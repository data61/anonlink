import os
import platform
from ctypes import cdll, c_double, byref
import numpy as np
import bloommatcher as bm
from identifier_types import basic_types


def cryptoBloomFilter(record, tokenizers, key1="test1", key2="test2"):
    """
    Make a bloom filter from a record with given tokenizers

    Using the method from
    http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf

    :param record: record of index, name, dob, gender (M/F)
    :param tokenizers: A list of IdentifierType tokenizers
    :param key1: key for first hash function
    :param key2: key for second hash function
    :return: 2-tuple - bitarray with bloom filter for record, index of record
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


def python_filter_similarity_matrix(filters1, filters2):
    result = []
    for i, f1 in enumerate(filters1):
        coeffs = map(lambda x:  bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2])), filters2)
        result.append(coeffs)
    return result


def python_filter_similarity(filters1, filters2):
    result = []
    for i, f1 in enumerate(filters1):
        coeffs = map(lambda x:  bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2])), filters2)
        best = np.argmax(coeffs)
        result.append((i, coeffs[best], f1[1], filters2[best][1], best))
    return result


def c_filter_similarity(filters1, filters2):
    length = len(filters1)
    library_name = "dice_one_against_many"
    libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), library_name))

    if platform.system() == "Darwin":
        c_dice = cdll.LoadLibrary(libpath + '.dll')
    else:
        c_dice = cdll.LoadLibrary(libpath + '.so')

    match_one_against_many_dice_1024_c = c_dice.match_one_against_many_dice_1024_c

    clist1 = [f[0].tobytes() for f in filters1]
    carr2 = "".join([f[0].tobytes() for f in filters2])

    result = []
    for i, f1 in enumerate(filters1):
        coeff = c_double()
        ind = match_one_against_many_dice_1024_c(clist1[i], carr2, length, byref(coeff))
        result.append((i, coeff.value, f1[1], filters2[ind][1], ind))

    return result


def calculate_filter_similarity(filters1, filters2):
    # TODO use C++ version by default
    return python_filter_similarity_matrix(filters1, filters2)

