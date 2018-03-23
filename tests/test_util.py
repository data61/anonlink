#!/usr/bin/env python3.4

import unittest
import pytest
import itertools
from anonlink import util
from anonlink import bloommatcher as bm
from tests import bitarray_utils

class TestUtilDataGeneration(unittest.TestCase):

    def test_generate_bitarray(self):
        for i in range(100):
            ba = util.generate_bitarray(1024)
            self.assertEquals(len(ba), 1024)

    def test_generate_clks(self):

        clks = util.generate_clks(100)

        for clk in clks:
            self.assertEqual(len(clk), 3)
            self.assertEqual(len(clk[0]), 1024)
            self.assertEqual(clk[0].count(), clk[2])

@pytest.mark.parametrize("L", bitarray_utils.key_lengths)
def test_popcount_vector(L):
    bas = bitarray_utils.bitarrays_of_length(L)
    bas_counts = [b.count() for b in bas]

    popcounts, _ = util.popcount_vector(bas, use_python=True)
    assert(popcounts == bas_counts)
    popcounts, _ = util.popcount_vector(bas, use_python=False)
    assert(popcounts == bas_counts)


def popcount_offset_vector(bitarrays, offset):
    """Like the native version of util.popcount_vector() but where the
    pointers are all offset by offset bytes before sending them to the
    native library. This is used to check that the library is robust
    wrt to pointer misalignment.
    """
    from anonlink._entitymatcher import ffi, lib
    from bitarray import bitarray
    n = len(bitarrays)
    arr_bytes = bitarrays[0].length() // 8
    offset %= arr_bytes # make sure offset isn't too big
    c_popcounts = ffi.new("uint32_t[{}]".format(n))
    bas_as_bytes = bytes([b for f in bitarrays for b in f.tobytes()])
    many = ffi.new("char[{}]".format(arr_bytes * n), bas_as_bytes)

    # Note that we're sending n-1 elements here instead of n, dropping
    # the last array, because we've (effectively) shifted all the
    # arrays offsets forward by offset bytes.
    misaligned_addr = int(ffi.cast('uintptr_t', many)) + offset
    misaligned_many = ffi.cast('char *', misaligned_addr)
    lib.popcount_arrays(c_popcounts, misaligned_many, n - 1, arr_bytes)

    # restrict to the offset bytes
    bas_as_bytes = bas_as_bytes[offset : (n-1)*arr_bytes + offset]
    # split into chunks corresponding to clks
    chunks = [c for c in util.chunks(bas_as_bytes, arr_bytes)]
    # Can Hamish count?
    assert(len(chunks) == n - 1)
    for c in chunks:
        assert(len(c) == arr_bytes)

    # popcount from Python
    bas_counts = []
    for chunk in chunks:
        ba = bitarray()
        ba.frombytes(chunk)
        bas_counts.append(ba.count())

    # Return the popcounts calculated in the native library and those
    # from Python
    return [c_popcounts[i] for i in range(n-1)], bas_counts

@pytest.mark.parametrize("L, offset", itertools.product(bitarray_utils.key_lengths, [1, 3, 8]))
def test_popcount_offset_vector(L, offset):
    """Test the popcount_vector method but with input pointers that aren't
    aligned to a word boundary."""
    bas = bitarray_utils.bitarrays_of_length(L)

    popcounts, bas_counts = popcount_offset_vector(bas, offset)
    assert(popcounts == bas_counts)
