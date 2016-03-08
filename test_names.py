__author__ = 'shardy'

import unittest
from bitarray import bitarray
import bloommatcher as bm
import randomnames as rn
from datetime import datetime

class TestBloomMatcher(unittest.TestCase):

    def test_tanimoto_1(self):
        self.assertEqual(bm.tanimoto(bitarray('1111011'), bitarray('1111011')), 1.0)

    def test_tanimoto_2(self):
        self.assertEqual(bm.tanimoto(bitarray('0000100'), bitarray('1111011')), 0.0)

    def test_tanimoto_3(self):
        self.assertEqual(bm.tanimoto(bitarray('1000011'), bitarray('1111011')), 0.5)

    def test_tanimoto_precount_1(self):
        self.assertEqual(bm.tanimoto_precount(bitarray('1000011'), bitarray('1111011'), 9.0), 0.5)

    def test_dice_1(self):
        self.assertEqual(bm.dicecoeff(bitarray('1111011'), bitarray('1111011')), 1.0)

    def test_dice_2(self):
        self.assertEqual(bm.dicecoeff(bitarray('0000100'), bitarray('1111011')), 0.0)

    def test_dice_3(self):
        self.assertEqual(bm.dicecoeff(bitarray('1000001'), bitarray('1111011')), 0.5)

    def test_dice_precount_1(self):
        self.assertEqual(bm.dicecoeff_precount(bitarray('1000001'), bitarray('1111011'), 8.0), 0.5)

    def test_unigram_1(self):
        self.assertEqual(bm.unigramlist("1/2/93"), ['1', '2', '9', '3'])

    def test_unigram_2(self):
        self.assertEqual(bm.unigramlist("1*2*93", '*'), ['1', '2', '9', '3'])

    def test_bigram_1(self):
        self.assertEqual(bm.bigramlist("steve"), [' s', 'st', 'te', 'ev', 've', 'e '])

    def test_random_date(self):
        start = datetime(1980, 1, 1)
        end = datetime(1990, 1, 1)

        for i in range(1000):
            self.assertGreaterEqual((rn.random_date(start, end)-start).days, 0)
            self.assertLess((rn.random_date(start, end)-end).days, 0)

    def test_generate_subsets(self):
        nl = rn.NameList(20)
        s1, s2 = nl.generate_subsets(10, 0.8)
        counteq = 0
        for s in s1:
            for t in s2:
                if s == t:
                    counteq += 1
        self.assertEqual(counteq, 8)

if __name__ == '__main__':
    unittest.main()
