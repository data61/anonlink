import itertools
import random
import operator
import os
from timeit import default_timer as timer

import bitarray
from clkhash.key_derivation import generate_key_lists
from clkhash.bloomfilter import stream_bloom_filters
from clkhash.randomnames import NameList

import anonlink


def generate_random_bitarrays(length=1024):
    while True:
        a = bitarray.bitarray()
        a.frombytes(os.urandom(length//8))
        yield a


def generate_random_clks(count, length=1024):
    return tuple(itertools.islice(generate_random_bitarrays(length), count))


some_filters = generate_random_clks(10000)


def print_comparison_header(threshold):
    print("\nThreshold:", threshold)
    print("Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput")
    print("       |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)")
    print("-------+--------+------------------+-------------------------+-------------")


def compute_comparison_speed(n1, n2, threshold):
    """
    Using the greedy solver, how fast can hashes be computed using one core.
    """

    assert n1 != 0 and n2 != 0
    filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
    filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]

    start = timer()
    sparse_matrix = anonlink.candidate_generation.find_candidate_pairs(
        (filters1, filters2),
        anonlink.similarities.dice_coefficient,
        threshold)
    t1 = timer()
    anonlink.solving.greedy_solve(sparse_matrix)
    end = timer()

    similarity_time = t1 - start
    solver_time = end - t1
    elapsed_time = end - start

    inv_similarity_time = 1 / similarity_time if similarity_time > 0 else float('inf')
    inv_elapsed_time = 1 / elapsed_time if elapsed_time > 0 else float('inf')

    print("{:6d} | {:6d} | {:4d}e6  ({:5.2f}%) | {:6.3f}  ({:4.1f}% / {:4.1f}%) |  {:8.3f}".format(
        n1, n2, n1*n2 // 1000000,
        100.0*len(sparse_matrix)/(n1*n2),
        elapsed_time,
        100.0*similarity_time * inv_elapsed_time,
        100.0*solver_time * inv_elapsed_time,
        (n1*n2 / 1e6) * inv_similarity_time))
    return elapsed_time


def compare_python_c(ntotal=10000, nsubset=6000, frac=0.8):
    """Compare results and running time of python and C++ versions.

    :param ntotal: Total number of data points to generate
    :param nsubset: Number of points for each database
    :param frac: Fraction of overlap between subsets

    :raises: AssertionError if the results differ
    :return: dict with 'c' and 'python' keys with values of the total time taken
             for each implementation
    """

    nml = NameList(ntotal)
    sl1, sl2 = nml.generate_subsets(nsubset, frac)

    keys = generate_key_lists(('test1', 'test2'), len(nml.schema_types))
    filters1 = tuple(map(operator.itemgetter(0),
                         stream_bloom_filters(sl1, keys, nml.SCHEMA)))
    filters2 = tuple(map(operator.itemgetter(0),
                         stream_bloom_filters(sl2, keys, nml.SCHEMA)))

    # Pure Python version
    start = timer()
    result = anonlink.candidate_generation.find_candidate_pairs(
        (filters1, filters2),
        anonlink.similarities.dice_coefficient_python,
        0.0,
        k=1)
    end = timer()
    python_time = end - start

    # C++ accelerated version
    start = timer()
    result3 = anonlink.candidate_generation.find_candidate_pairs(
        (filters1, filters2),
        anonlink.similarities.dice_coefficient_accelerated,
        0.0,
        k=1)
    end = timer()
    cffi_time = end - start

    assert result == result3, "Results are different between C++ cffi and Python"

    # Results are the same
    return {
        "c": cffi_time,
        "python": python_time
    }


def benchmark(size, compare):

    print("Anonlink benchmark -- see README for explanation")
    print("------------------------------------------------")
    if compare:
        print(compare_python_c(ntotal=1000, nsubset=600))

    possible_test_sizes = [
        1000, 2000, 3000, 4000,
        5000, 6000, 7000, 8000, 9000,
        10000,
        20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
        1000000,
        2000000
    ]

    thld = 0.5
    print_comparison_header(thld)
    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed(test_size, test_size, thld)

    thld = 0.7
    print_comparison_header(thld)
    size *= 5
    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed(test_size, test_size, thld)


if __name__ == '__main__':
    benchmark(4000, False)
    # benchmark(20000, False)
