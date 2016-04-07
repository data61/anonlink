#!/usr/bin/env python3.4


from timeit import default_timer as timer


from randomnames import NameList
from entitymatch import calculate_bloom_filters, python_filter_similarity, c_filter_similarity


def compare_python_c(ntotal=8000, nsubset=4000, frac=0.8):
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

    # C++ Version
    start = timer()
    result2 = c_filter_similarity(filters1, filters2)
    end = timer()
    c_time = end - start

    assert result == result2, "Results are different"

    # Results are the same
    return {
        "c": c_time,
        "python": python_time
    }


if __name__ == '__main__':
    results = compare_python_c()
    print("Python time:{python:8.3f}\n{sep}\nC++ time:   {c:8.3f}".format(sep="="*20, **results))

    print("Speedup: {:.1f}x".format(results['python']/results['c']))


