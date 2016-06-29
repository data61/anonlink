import random
from bitarray import bitarray
from timeit import default_timer as timer
from anonlink.randomnames import NameList
from anonlink.entitymatch import *


def generate_bitarray(length):
    return bitarray(
        ''.join('1' if random.random() > 0.5 else '0' for _ in range(length))
    )

some_filters = [(generate_bitarray(1024),) for _ in range(10000)]


def compute_comparison_speed(n1=100, n2=100):
    """
    Using the greedy solver, how fast can hashes be computed.


    """


    filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
    filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]


    # Greedy C++ cffi version
    start = timer()
    result3 = calculate_mapping_greedy(filters1, filters2)
    end = timer()
    elapsed_time = end - start
    print("{:6d} | {:6d} | {:12d} | {:8.3f}s    |  {:12.3f}".format(
        n1, n1, n1*n2, elapsed_time, (n1*n2)/(1e6*elapsed_time)))
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
    filters1 = calculate_bloom_filters(sl1, nml.schema, keys)
    filters2 = calculate_bloom_filters(sl2, nml.schema, keys)

    # Pure Python version
    start = timer()
    result = python_filter_similarity(filters1, filters2)
    end = timer()
    python_time = end - start

    # C++ cffi version
    start = timer()
    result3 = cffi_filter_similarity(filters1, filters2)
    end = timer()
    cffi_time = end - start

    assert result == result3, "Results are different between C++ cffi and Python"

    # Results are the same
    return {
        "c": cffi_time,
        "python": python_time
    }


if __name__ == '__main__':
    print("Size 1 | Size 2 | Comparisons  | Compute Time | Million Comparisons per second")

    for size in [
        10, 50, 100, 500,
        1000, 2000, 3000,
        4000,
        5000, 6000, 7000, 8000,
        10000,
        #50000,
        #100000,
        #20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000
        #1000000
    ]:
        elapsed = compute_comparison_speed(size, size)


#
#     results = compare_python_c()
#     print("""
# Python:       {python:8.3f}
# C++ (cffi):   {c:8.3f}
# """.format(**results))
#
#     print("Speedup: {:.1f}x".format(results['python']/results['c']))
#
#
