import random
from timeit import default_timer as timer

from clkhash.schema import get_schema_types
from clkhash.bloomfilter import calculate_bloom_filters
from clkhash.randomnames import NameList

from anonlink.entitymatch import *
from anonlink.util import popcount_vector, generate_clks, generate_bitarray
from anonlink.distributed_processing import calculate_filter_similarity


some_filters = generate_clks(10000)


def compute_popcount_speed(n):
    """
    Just do as much counting of bits.
    """
    clks = [generate_bitarray(1024) for _ in range(n)]
    start = timer()
    popcounts = popcount_vector(clks)
    end = timer()
    elapsed_time = end - start
    print("{:6d} x 1024 bit popcounts in {:.6f} seconds".format(n, elapsed_time))
    speed_in_MiB = n / (1024 * 8 * elapsed_time)
    print("Popcount speed: {:.2f} MiB/s".format(speed_in_MiB))
    return speed_in_MiB


def print_comparison_header():
    print("Size 1 | Size 2 | Comparisons  | Compute Time | Million Comparisons per second")


def compute_comparison_speed(n1=100, n2=100):
    """
    Using the greedy solver, how fast can hashes be computed using one core.
    """

    filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
    filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]

    start = timer()
    result3 = calculate_mapping_greedy(filters1, filters2)
    end = timer()
    elapsed_time = end - start
    print("{:6d} | {:6d} | {:12d} | {:8.3f}s    |  {:12.3f}".format(
        n1, n2, n1*n2, elapsed_time, (n1*n2)/(1e6*elapsed_time)))
    return elapsed_time


def compute_comparison_speed_parallel(n1=100, n2=100):
    """
    Using the greedy solver in chunks, how fast can hashes be computed.
    """

    filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
    filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]


    start = timer()
    calculate_filter_similarity(filters1, filters2)

    end = timer()
    elapsed_time = end - start
    print("{:6d} | {:6d} | {:12d} | {:8.3f}s    |  {:12.3f}".format(
        n1, n2, n1*n2, elapsed_time, (n1*n2)/(1e6*elapsed_time)))
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

    keys = ('test1', 'test2')
    filters1 = calculate_bloom_filters(sl1, get_schema_types(nml.schema), keys)
    filters2 = calculate_bloom_filters(sl2, get_schema_types(nml.schema), keys)

    # Pure Python version
    start = timer()
    result = python_filter_similarity(filters1, filters2)
    end = timer()
    python_time = end - start

    # C++ cffi version
    start = timer()
    result3 = cffi_filter_similarity_k(filters1, filters2, 1, 0.0)
    end = timer()
    cffi_time = end - start

    assert result == result3, "Results are different between C++ cffi and Python"

    # Results are the same
    return {
        "c": cffi_time,
        "python": python_time
    }


def benchmark(size, compare):

    if compare:
        print(compare_python_c(ntotal=1000, nsubset=600))

    compute_popcount_speed(100000)

    print_comparison_header()

    possible_test_sizes = [
        1000, 2000, 3000, 4000,
        5000, 6000, 7000, 8000, 9000,
        10000,
        20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
        1000000,
        2000000
    ]

    for test_size in possible_test_sizes:
        if test_size <= size:
            compute_comparison_speed_parallel(
                test_size, test_size
            )

    print("Single Core:")
    compute_comparison_speed(5000, 5000)


if __name__ == '__main__':
    benchmark(20000, False)