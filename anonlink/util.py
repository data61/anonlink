#!/usr/bin/env python3.4

#from _entitymatcher import ffi, lib


def popcount_vector(clks):
    """
    Note, due to the overhead of converting bitarrays into
    bytes, it is more expensive to call our C implementation
    than just calling bitarray.count()

    """
    return [clk.count() for clk in clks]

    # n = len(clks)
    # c_popcounts = ffi.new("uint32_t[{}]".format(n))
    # many = ffi.new("char[{}]".format(128 * n),
    #                 bytes([b for f in clks for b in f.tobytes()]))
    # lib.popcount_1024_array(many, n, c_popcounts)
    #
    # return [c_popcounts[i] for i in range(n)]