import random
from timeit import default_timer as timer

from clkhash.key_derivation import generate_key_lists
from clkhash.schema import get_schema_types
from clkhash.bloomfilter import calculate_bloom_filters
from clkhash.randomnames import NameList

from anonlink.entitymatch import *
from anonlink.util import popcount_vector, generate_clks, generate_bitarray


some_filters = generate_clks(10000)


def compute_popcount_speed(n):
    """
    Just do as much counting of bits.
    """
    clk_bits = 1024
    clk_bytes = clk_bits / 8
    clks_MiB = n * clk_bytes * 1.0 / (1 << 20)

    clks = [generate_bitarray(clk_bits) for _ in range(n)]

    print("{:6d} x {:d} bit popcounts".format(n, clk_bits))
    print("Implementation              | Time (ms) | Bandwidth (MiB/s)")
    start = timer()
    popcounts = popcount_vector(clks, use_native=False)
    end = timer()
    elapsed_time = end - start
    speed_in_MiB = clks_MiB / elapsed_time
    print("Python (bitarray.count()):  |  {:7.2f}  |  {:9.2f} "
          .format(elapsed_time * 1e3, speed_in_MiB))

    # Native
    start = timer()
    popcounts, ms = popcount_vector(clks, use_native=True)
    end = timer()
    elapsed_time = end - start
    elapsed_nocopy = ms / 1e3
    copy_percent = 100*(elapsed_time - elapsed_nocopy) / elapsed_time
    speed_in_MiB = clks_MiB / elapsed_time
    speed_in_MiB_nocopy = clks_MiB / elapsed_nocopy
    print("Native code (no copy):      |  {:7.2f}  |  {:9.2f} "
          .format(ms, speed_in_MiB_nocopy))
    print("Native code (w/ copy):      |  {:7.2f}  |  {:9.2f}   ({:.1f}% copying)"
          .format(elapsed_time * 1e3, speed_in_MiB, copy_percent))

    return speed_in_MiB


def print_comparison_header(threshold):
    print("Threshold = ", threshold)
    print("Size 1 | Size 2 | Comparisons  | Total Time (simat/solv) | Million Comparisons per second")


def compute_comparison_speed(n1=100, n2=100, threshold=0.75):
    """
    Using the greedy solver, how fast can hashes be computed using one core.
    """

    filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
    filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]

    start = timer()
    sparse_matrix = calculate_filter_similarity(filters1, filters2, k=len(filters2), threshold=threshold)
    t1 = timer()
    res = greedy_solver(sparse_matrix)
    end = timer()

    #print("mat size = ", len(sparse_matrix))
    similarity_time = t1 - start
    solver_time = end - t1
    elapsed_time = end - start
    print("{:6d} | {:6d} | {:12d} | {:7.3f}s ({:3.1f}% / {:3.1f}%) |  {:12.3f}  -- {:8d} = {:2.1f}%".format(
        n1, n2, n1*n2, elapsed_time,
        100.0*similarity_time/elapsed_time,
        100.0*solver_time/elapsed_time,
        (n1*n2)/(1e6*similarity_time), len(sparse_matrix), 100.0*len(sparse_matrix)/(n1*n2)))
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

    keys = generate_key_lists(('test1', 'test2'), len(nml.schema))
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

    possible_test_sizes = [
        1000, 2000, 3000, 4000,
        5000, 6000, 7000, 8000, 9000,
        10000,
        20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
        1000000,
        2000000
    ]

    #for thld in [0.95, 0.85, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5]:
    for thld in [0.22, 0.25, 0.27, 0.48, 0.49, 0.5, 0.51, 0.52, 0.54, 0.56, 0.58, 0.6, 0.62, 0.64]:
        #print_comparison_header(thld)
        print("threshold = ", thld)
        for test_size in possible_test_sizes:
            if test_size <= size:
                compute_comparison_speed(test_size, test_size, thld)

if __name__ == '__main__':
    benchmark(1000, False)
    #benchmark(20000, False)
