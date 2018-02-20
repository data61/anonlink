#!/usr/bin/env python3.4

import unittest
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

# Generate bit arrays that are combinations of words 0, 1, 2^63, 2^64 - 1
# of various lengths between 1 and 65 words.
def test_popcount_vector():
    for L in bitarray_utils.key_lengths:
        yield check_popcount_vector, bitarray_utils.bitarrays_of_length(L)

def check_popcount_vector(bas):
    bas_counts = [b.count() for b in bas]

    popcounts, _ = util.popcount_vector(bas, use_python=True)
    assert(popcounts == bas_counts)
    popcounts, _ = util.popcount_vector(bas, use_python=False)
    assert(popcounts == bas_counts)

