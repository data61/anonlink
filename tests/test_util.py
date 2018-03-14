#!/usr/bin/env python3.4

import unittest
import pytest
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
