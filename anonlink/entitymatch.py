from _entitymatcher import ffi, lib
from . import bloommatcher as bm
from .identifier_types import basic_types
import logging
logging.basicConfig(level=logging.WARNING)


def cryptoBloomFilter(record, tokenizers, key1="test1", key2="test2"):
    """
    Make a bloom filter from a record with given tokenizers

    Using the method from
    http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf

    :param record: record tuple. E.g. (index, name, dob, gender)
    :param tokenizers: A list of IdentifierType tokenizers (one for each record element)
    :param key1: key for first hash function
    :param key2: key for second hash function

    :return: 3-tuple - bitarray with bloom filter for record, index of record, bitcount
    """

    mlist = []
    for (entry, tokenizer) in zip(record, tokenizers):
        for token in tokenizer(entry):
            mlist.append(token)

    bf = bm.hbloom(mlist, keysha1=key1, keymd5=key2)

    return bf, record[0], bf.count()


def calculate_bloom_filters(dataset, schema, keys):
    """
    :param dataset: A list of indexable records.
    :param schema: An iterable of identifier type names.
    :param keys: A tuple of two secret keys used in the HMAC.
    :return: List of bloom filters
    """
    schema_types = [basic_types[column] for column in schema]
    bloom_filters = [cryptoBloomFilter(s, schema_types, key1=keys[0], key2=keys[1])
                     for s in dataset]
    return bloom_filters


def python_filter_similarity(filters1, filters2):
    """Pure python method for determining Bloom Filter similarity

    Both arguments are 3-tuples - bitarray with bloom filter for record, index of record, bitcount

    :return: A list of tuples *one* for each entity in filters1.
    The tuple comprises:
        - the index in filters1
        - the similarity score between 0 and 1 of the best match
        - The original index in entity A
        - The original index in entity B
        - The index in filters2 of the best match
    """
    result = []
    for i, f1 in enumerate(filters1):
        coeffs = [bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2])) for x in filters2]
        # argmax
        best = max(enumerate(coeffs), key=lambda x: x[1])[0]
        assert coeffs[best] <= 1.0
        result.append((i, coeffs[best], f1[1], filters2[best][1], best))
    return result


def cffi_filter_similarity_k(filters1, filters2, k=3):
    """Accelerated method for determining Bloom Filter similarity.

    Computes a sparse similarity matrix with:
        - size of k * len(filters1)
        - order of len(filters1) + len(filters2)

    :param filters1: A list of cryptoBloomFilters
    :param filters2: A list of cryptoBloomFilters
    :param k: The top k edges will be included in the result.
    :return: A sparse matrix as a list of tuples, *k* for each entity
        in filters1.

        The tuple comprises:
            - the index in filters1
            - the similarity score between 0 and 1 of the best match
            - The original index in entity A
            - The original index in entity B
            - The index in filters2 of the best match
    """
    length_f1 = len(filters1)
    length_f2 = len(filters2)

    # We assume the length is 1024 bit = 128 Bytes
    match_one_against_many_dice_1024_k_top = lib.match_one_against_many_dice_1024_k_top

    clist1 = [ffi.new("char[128]",
                      bytes(f[0].tobytes())) for f in filters1]
    carr2 = ffi.new("char[{}]".format(128 * length_f2),
                    bytes([b for f in filters2 for b in f[0].tobytes()]))

    result = []
    for i, f1 in enumerate(filters1):
        # easier to do all buffer allocations in Python and pass them to C,
        # even for output-only arguments
        c_scores = ffi.new("double[]", k)
        c_indices = ffi.new("int[]", k)
        assert len(clist1[i]) == 128
        assert len(carr2) % 64 == 0
        match_one_against_many_dice_1024_k_top(
            clist1[i],
            carr2,
            length_f2,
            k,
            c_indices,
            c_scores)

        scores = [v for v in c_scores]
        indices = [v for v in c_indices]

        original_index_a = f1[1]

        for j in range(k):
            ind = indices[j]
            assert ind < len(filters2)
            original_index_b = filters2[ind][1]
            result.append((i, scores[j], original_index_a, original_index_b, ind))

    return result


def python_calculate_mapping_greedy(filters1, filters2, threshold=0.95):
    """
    Brute force pure python solver.

    A bitset for each entry in the set we are matching to (filters2)
    and a search per entry in the matching set over the top k matches for
    the first unmatched entry.

    We don't calculate/store the graph at all, and process each record in turn.

    Memory requirements are:
        - to store the bloom filter arrays
        - the mapping and a bit per target

    """

    logging.info('Solving with greedy solver')
    mappings = {}
    # original indicies of filters which have been claimed
    matched_entries_a = set()
    matched_entries_b = set()

    for i, f1 in enumerate(filters1):
        index_a = i
        if index_a not in matched_entries_a:
            # A list of 2-tuples containing (elements' index in b, and the score)
            coeffs = [(j, bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2]))) for j, x in enumerate(filters2)]
            # naive k-argmax, TODO replace with the C version
            for possible_index_b, score in reversed(sorted(coeffs, key=lambda x: x[1])):
                if possible_index_b not in matched_entries_b and score > threshold:
                    mappings[index_a] = possible_index_b

                    matched_entries_a.add(index_a)
                    matched_entries_b.add(possible_index_b)
                    break

    return mappings


def calculate_filter_similarity(filters1, filters2, use_python=False):
    MIN_LENGTH = 5
    if len(filters1) < MIN_LENGTH or len(filters2) < MIN_LENGTH:
        raise ValueError("Didn't meet minimum number of entities")
    # use C++ version by default
    if use_python:
        return python_filter_similarity(filters1, filters2)
    else:
        return cffi_filter_similarity_k(filters1, filters2, k=10)

