#!/usr/bin/env python3.4

import unittest
import os
from itertools import combinations_with_replacement
from collections import deque
from anonlink import util
from bitarray import bitarray
from anonlink import bloommatcher as bm

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

# Return a bit array of length L*64 whose contents are combinations of
# the words 0, 2^64-1, 1 or 2^63 (ie. all zeros, all ones, or a one in
# the least or most significant position).
def bitarrays_of_length(L):
    special_words = [64*bitarray('0'),
                     63*bitarray('0') + bitarray('1'),
                     bitarray('1') + 63*bitarray('0'),
                     64*bitarray('1')]
    # '+' on bitarrays is concatenation
    return [sum(word, bitarray())
            for word in combinations_with_replacement(special_words, L)]

# Interesting key lengths (usually around 2^something +/-1).
key_lengths = [1, 2, 3, 4, 8, 9, 10, 15, 16, 17,
               23, 24, 25, 30, 31, 32, 33, 63, 64, 65]

# Generate bit arrays that are combinations of words 0, 1, 2^63, 2^64 - 1
# of various lengths between 1 and 65 words.
def test_popcount_vector():
    for L in key_lengths:
        yield check_popcount_vector, bitarrays_of_length(L)

def check_popcount_vector(bas):
    bas_counts = [b.count() for b in bas]

    popcounts, _ = util.popcount_vector(bas, use_python=True)
    assert(popcounts == bas_counts)
    popcounts, _ = util.popcount_vector(bas, use_python=False)
    assert(popcounts == bas_counts)

def test_dicecoeff():
    for L in key_lengths:
        yield check_dicecoeff, bitarrays_of_length(L)

def check_dicecoeff(bas):
    # Test the Dice coefficient of bitarrays in bas with other
    # bitarrays of bas.  rotations is the number of times we rotate
    # bas to generate pairs to test the Dice coefficient; 10 takes
    # around 10s, 100 around 60s.
    rotations = 100 if "INCLUDE_10K" in os.environ else 10;

    # We check that the native code and Python versions of dicecoeff
    # don't ever differ by more than 10^{-6}.
    eps = 0.000001
    d = deque(bas)
    for _ in range(min(rotations, len(bas))):
        for a, b in zip(bas, d):
            diff = bm.dicecoeff_pure_python(a, b) - bm.dicecoeff_native(a, b)
            assert(abs(diff) < eps)
        d.rotate(1)
