#!/usr/bin/env python3.4

import unittest
from itertools import combinations_with_replacement
from anonlink import util
from bitarray import bitarray

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

def concat_bitarrays(products):
    for p in products:
        yield sum(p, bitarray())

# Generate bit arrays that are combinations of words 0, 1, 2^63, 2^64 - 1
# of various lengths between 1 and 65 words.
def test_generator():
    key_lengths = [1, 2, 3, 4, 8, 9, 10, 15, 16, 17,
                   23, 24, 25, 30, 31, 32, 33, 63, 64, 65]
    special_words = [64*bitarray('0'),
                     63*bitarray('0') + bitarray('1'),
                     bitarray('1') + 63*bitarray('0'),
                     64*bitarray('1')]
    for L in key_lengths:
        words = combinations_with_replacement(special_words, L)
        # '+' on bitarrays is concatenation
        bas = [sum(w, bitarray()) for w in words]
        yield check_popcount_vector, bas

def check_popcount_vector(bas):
    bas_counts = [b.count() for b in bas]

    popcounts, _ = util.popcount_vector(bas, use_python=True)
    assert(popcounts == bas_counts)
    popcounts, _ = util.popcount_vector(bas, use_python=False)
    assert(popcounts == bas_counts)
