#!/usr/bin/env python3.4

import os
import random
from bitarray import bitarray


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


def popcount_vector(bitarrays):
    """
    Note, due to the overhead of converting bitarrays into
    bytes, it is more expensive to call our C implementation
    than just calling bitarray.count()

    """
    return [clk.count() for clk in bitarrays]

    # n = len(clks)
    # c_popcounts = ffi.new("uint32_t[{}]".format(n))
    # many = ffi.new("char[{}]".format(128 * n),
    #                 bytes([b for f in clks for b in f.tobytes()]))
    # lib.popcount_1024_array(many, n, c_popcounts)
    #
    # return [c_popcounts[i] for i in range(n)]


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]