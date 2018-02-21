import logging

from anonlink._entitymatcher import ffi, lib

import sys

from . import bloommatcher as bm
from . import util

log = logging.getLogger('anonlink.entitymatch')


def python_filter_similarity(filters1, filters2):
    """Pure python method for determining Bloom Filter similarity

    Both arguments are 3-tuples - bitarray with bloom filter for record, index of record, bitcount

    :return: A list of tuples *one* for each entity in filters1.
    The tuple comprises:
        - the index in filters1
        - the similarity score between 0 and 1 of the best match
        - The index in filters2 of the best match
    """
    result = []
    for i, f1 in enumerate(filters1):
        coeffs = [bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2])) for x in filters2]
        # argmax
        best = max(enumerate(coeffs), key=lambda x: x[1])[0]
        assert coeffs[best] <= 1.0
        result.append((i, coeffs[best], best))
    return result


def cffi_filter_similarity_k(filters1, filters2, k, threshold):
    """Accelerated method for determining Bloom Filter similarity.

    Assumes all filters are the same length, being a multiple of 64
    bits.

    """
    length_f1 = len(filters1)
    length_f2 = len(filters2)

    if length_f1 == 0:
        return []

    filter_bits = len(filters1[0][0])
    assert(filter_bits % 64 == 0, 'Filter length must be a multple of 64 bits.')
    filter_bytes = filter_bits // 8

    match_one_against_many_dice_k_top = lib.match_one_against_many_dice_k_top

    # An array of the *one* filter
    clist1 = [ffi.new("char[{}]".format(filter_bytes), bytes(f[0].tobytes()))
              for f in filters1]

    if sys.version_info < (3, 0):
        # Python 2 version
        data = []
        for f in filters2:
            for b in f[0].tobytes():
                data.append(b)

        carr2 = ffi.new("char[{}]".format(filter_bytes * length_f2), ''.join(data))
    else:
        # Works in Python 3+
        carr2 = ffi.new("char[{}]".format(filter_bytes * length_f2),
                        bytes([b for f in filters2 for b in f[0].tobytes()]))

    c_popcounts = ffi.new("uint32_t[{}]".format(length_f2), [f[2] for f in filters2])

    # easier to do all buffer allocations in Python and pass them to C,
    # even for output-only arguments
    c_scores = ffi.new("double[]", k)
    c_indices = ffi.new("int[]", k)

    result = []
    for i, f1 in enumerate(filters1):
        assert len(clist1[i]) == filter_bytes
        matches = match_one_against_many_dice_k_top(
            clist1[i],
            carr2,
            c_popcounts,
            length_f2,
            filter_bytes,
            k,
            threshold,
            c_indices,
            c_scores)

        if matches < 0:
            raise ValueError('Internel error: Bad key length')
        for j in range(matches):
            ind = c_indices[j]
            assert ind < len(filters2)
            result.append((i, c_scores[j], ind))

    return result


def greedy_solver(sparse_similarity_matrix):
    """
    For optimal results consider sorting input by score for each row.

    :param sparse_similarity_matrix: Iterable of tuples: (indx_a, similarity_score, indx_b)
    """
    mappings = {}

    # original indicies of filters which have been claimed
    matched_entries_b = set()

    for result in sparse_similarity_matrix:
        index_a, score, possible_index_b = result
        if possible_index_b not in matched_entries_b:
            mappings[index_a] = possible_index_b
            matched_entries_b.add(possible_index_b)

    return mappings


def calculate_mapping_greedy(filters1, filters2, threshold=0.95, k=5):
    """
    Brute-force one-shot solver.

    :param filters1: A list of cryptoBloomFilters from first organization
    :param filters2: A list of cryptoBloomFilters from second organization
    :param float threshold: The score above which to consider
    :param int k: Consider up to the top k matches.

    :returns A mapping dictionary of index in filters1 to index in filters2.
    """

    log.info('Solving with greedy solver')

    sparse_matrix = calculate_filter_similarity(filters1, filters2, k, threshold)
    return greedy_solver(sparse_matrix)


def calculate_filter_similarity(filters1, filters2, k=10, threshold=0.5, use_python=False):
    """Computes a sparse similarity matrix with:
        - size no larger than k * len(filters1)
        - order of len(filters1) + len(filters2)

    This method is used as part of the all in one function `calculate_mapping_greedy`
    however you may wish to call it yourself in order to break a large mapping into
    more sizable chunks. These partial similarity results can be reduced into one
    list and passed to the `greedy_solver` function. Note the returned index for
    filters1 will need to be offset, see anonlink.concurrent for an example.

    :param filters1: A list of cryptoBloomFilters from first organization
    :param filters2: A list of cryptoBloomFilters from second organization
    :param k: The top k edges will be included in the result.
    :param threshold: Only scores greater than this threshold will be considered
        (between 0 and 1)
    :param use_python: Use the slower pure python method instead of C++ implementation

    :return: A sparse matrix as a list of tuples, up to *k* for each entity
        in filters1. Will be shorter if there are no qualifying matches.

        The tuple comprises:
            - the index in filters1
            - the similarity score between 0 and 1 of the best match
            - The index in filters2 of the best match
    """
    MIN_LENGTH = 5
    if len(filters1) < MIN_LENGTH or len(filters2) < MIN_LENGTH:
        raise ValueError("Didn't meet minimum number of entities")
    # use C++ version by default
    if use_python:
        return python_filter_similarity(filters1, filters2)
    else:
        return cffi_filter_similarity_k(filters1, filters2, k=k, threshold=threshold)

