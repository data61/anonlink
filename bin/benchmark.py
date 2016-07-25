import random
from timeit import default_timer as timer

import concurrent.futures
from bitarray import bitarray

from anonlink.bloomfilter import calculate_bloom_filters
from anonlink.entitymatch import *
from anonlink.randomnames import NameList


def generate_bitarray(length):
    return bitarray(
        ''.join('1' if random.random() > 0.5 else '0' for _ in range(length))
    )

some_filters = [(generate_bitarray(1024),) for _ in range(10000)]


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
        n1, n1, n1*n2, elapsed_time, (n1*n2)/(1e6*elapsed_time)))
    return elapsed_time


def calc_chunk_result(chunk_number, chunk, filters2):
    chunk_results = calculate_filter_similarity(chunk, filters2,
                                                threshold=0.95,
                                                k=5)

    partial_sparse_result = []
    # offset chunk's A index by chunk_size * chunk_number
    chunk_size = len(chunk)
    offset = chunk_size * chunk_number
    for (ia, score, ib) in chunk_results:
        partial_sparse_result.append((ia + offset, score, ib))

    return partial_sparse_result


def compute_comparison_speed_parallel(n1=100, n2=100):
    """
    Using the greedy solver in chunks, how fast can hashes be computed.
    """


    filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
    filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]

    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    start = timer()
    with concurrent.futures.ProcessPoolExecutor() as executor:

        futures = []
        chunk_size = int(20000000 / len(filters2))
        for i, chunk in enumerate(chunks(filters1, chunk_size)):
            future = executor.submit(calc_chunk_result, i, chunk, filters2)
            futures.append(future)


        for future in futures:
            future.result()

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
        500,
        1000, 2000, 3000,
        4000,
        5000, 6000, 7000, 8000,
        10000,
        #50000,
        #20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
        #1000000,
        #2000000
    ]:
        # Using just one core
        #elapsed = compute_comparison_speed(size, size)

        elapsed = compute_comparison_speed_parallel(size, size)


