#!/usr/bin/env python3.4

import os
import platform
from timeit import default_timer as timer
import sys as sys
from ctypes import cdll, c_double, byref
import numpy as np

import bloommatcher as bm
from randomnames import NameList, cryptoBloomFilter

library_name = "dice_one_against_many"
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), library_name))

if platform.system() == "Darwin":
    c_dice = cdll.LoadLibrary(libpath + '.dll')
else:
    c_dice = cdll.LoadLibrary(libpath + '.so')

match_one_against_many_dice_c = c_dice.match_one_against_many_dice_c
match_one_against_many_dice_1024_c = c_dice.match_one_against_many_dice_1024_c


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
    filters1 = [cryptoBloomFilter(s, key1="test1", key2="test2") for s in sl1]
    filters2 = [cryptoBloomFilter(s, key1="test1", key2="test2") for s in sl2]

    # Pure Python version
    start = timer()

    result = []
    for i, f1 in enumerate(filters1):
        coeffs = map(lambda x:  bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2])), filters2)
        best = np.argmax(coeffs)
        result.append((i, coeffs[best], f1[1], filters2[best][1], best))

    end = timer()

    python_time = end - start

    # C++ Version

    carr1 = "".join([f[0].tobytes() for f in filters1])
    clist1 = [f[0].tobytes() for f in filters1]
    carr2 = "".join([f[0].tobytes() for f in filters2])

    start = timer()

    result2 = []
    for i, f1 in enumerate(filters1):
        coeff = c_double()
        ind = match_one_against_many_dice_1024_c(clist1[i], carr2, nsubset, byref(coeff))
        result2.append((i, coeff.value, f1[1], filters2[ind][1], ind))

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
    print("Python time:{python:8.3f}\n{sep}\nC++ time:   {c:8.3f}".format(sep="="*24, **results))



