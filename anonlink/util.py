#!/usr/bin/env python3.4

import inspect
import os
import random
import warnings
from bitarray import bitarray
from timeit import default_timer as timer

from anonlink._entitymatcher import ffi, lib

def _fname():
    return inspect.currentframe().f_back.f_back.f_code.co_name
def _deprecation(use_instead=None):
    msg = (f'anonlink.util.{_fname()} has been '
           f'deprecated ')
    if use_instead is not None:
        msg += f'(use anonlink.{use_instead} instead)'
    else:
        msg += 'without replacement'
    warnings.warn(msg, DeprecationWarning, stacklevel=2)


def generate_bitarray(length):
    _deprecation()
    a = bitarray(endian=['little', 'big'][random.randint(0, 1)])
    a.frombytes(os.urandom(length//8))
    return a


def generate_clks(n):
    _deprecation()
    res = []
    for i in range(n):
        ba = generate_bitarray(1024)
        res.append((ba, i, ba.count()))
    return res


def popcount_vector(bitarrays, use_python=True):
    """Return a list containing the popcounts of the elements of
    bitarrays, and the time (in seconds) it took. If use_python is
    False, use the native code implementation instead of Python; in
    this case the returned time is the time spent in the native code,
    NOT including copying to and from the Python runtime.

    Note, due to the overhead of converting bitarrays into bytes,
    it is currently more expensive to call our C implementation
    than just calling bitarray.count()
    """
    _deprecation()
    # Use Python
    if use_python:
        start = timer()
        counts = [clk.count() for clk in bitarrays]
        elapsed = timer() - start
        return counts, elapsed

    # Use native code
    n = len(bitarrays)
    arr_bytes = bitarrays[0].length() // 8
    c_popcounts = ffi.new("uint32_t[{}]".format(n))
    many = ffi.new("char[{}]".format(arr_bytes * n),
                    bytes([b for f in bitarrays for b in f.tobytes()]))
    ms = lib.popcount_arrays(c_popcounts, many, n, arr_bytes)

    return [c_popcounts[i] for i in range(n)], ms * 1e-3


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    _deprecation('concurrency.split_to_chunks')
    for i in range(0, len(l), n):
        yield l[i:i + n]
