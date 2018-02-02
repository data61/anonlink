#!/usr/bin/env python3.4

import os
import random
from bitarray import bitarray

from anonlink._entitymatcher import ffi, lib

def generate_bitarray(length):
    a = bitarray(endian=['little', 'big'][random.randint(0, 1)])
    a.frombytes(os.urandom(length//8))
    return a


def generate_clks(n):
    res = []
    for i in range(n):
        ba = generate_bitarray(1024)
        res.append((ba, i, ba.count()))
    return res


def popcount_vector(bitarrays, use_native=False):
    """Return an array containing the popcounts of the elements of
    bitarrays. If use_native is True, use the native code
    implementation and return the time spent (in milliseconds) in the
    native code as a second return value.

    Note, due to the overhead of converting bitarrays into bytes,
    it is currently more expensive to call our C implementation
    than just calling bitarray.count()

    """
    # Use Python
    if not use_native:
        return [clk.count() for clk in bitarrays]

    # Use native code
    n = len(bitarrays)
    c_popcounts = ffi.new("uint32_t[{}]".format(n))
    many = ffi.new("char[{}]".format(128 * n),
                    bytes([b for f in bitarrays for b in f.tobytes()]))
    ms = lib.popcount_1024_array(many, n, c_popcounts)

    return [c_popcounts[i] for i in range(n)], ms


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
