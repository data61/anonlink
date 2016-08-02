#!/usr/bin/env python3.4

import unittest
from anonlink import util

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

    def test_popcount_vector(self):
        bas = [util.generate_bitarray(1024) for i in range(100)]
        popcounts = util.popcount_vector(bas)

        self.assertEquals(len(popcounts), 100)
        for i, cnt in enumerate(popcounts):
            self.assertEquals(cnt, bas[i].count())
