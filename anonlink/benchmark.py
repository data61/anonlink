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


def print_comparison_header(headline):
    print()
    print(headline)
    print("Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput")
    print("       |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)")
    print("-------+--------+------------------+-------------------------+-------------")


def compute_comparison_speed(n1, n2, threshold, k=None):
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
        threshold,
        k=k
    )
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
        100.0*len(sparse_matrix[0])/(n1*n2),
        elapsed_time,
        100.0*similarity_time * inv_elapsed_time,
        100.0*solver_time * inv_elapsed_time,
        (n1*n2 / 1e6) * inv_similarity_time))
    return elapsed_time


def benchmark(size):

    print("Anonlink benchmark -- see README for explanation")
    print("------------------------------------------------")

    print(f"using '{anonlink.solving.greedy_solve.__name__}' as solver and "
          f"'{anonlink.similarities.dice_coefficient.__name__}' as similarity metric")

    possible_test_sizes = [
        1000, 2000, 3000, 4000,
        5000, 6000, 7000, 8000, 9000,
        10000,
        20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
        1000000,
        2000000
    ]

    thld = 0.5
    print_comparison_header(f"Threshold: {thld}, All results returned")
    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed(test_size, test_size, thld, k=None)

    size *= 5
    thld = 0.5
    print_comparison_header(f"Threshold: {thld}, Top 100 matches per record returned")
    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed(test_size, test_size, thld, k=100)

    thld = 0.7
    print_comparison_header(f"Threshold: {thld}, All results returned")
    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed(test_size, test_size, thld, k=None)

    print_comparison_header(f"Threshold: {thld}, Top 100 matches per record returned")
    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed(test_size, test_size, thld, k=100)


if __name__ == '__main__':
    benchmark(4000)

