import unittest

from bitarray import bitarray

from anonlink import bloommatcher as bm

__author__ = 'shardy'


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
        self.assertEqual(bm.unigramlist("1/2/93", '/'), ['1', '2', '9', '3'])

    def test_unigram_2(self):
        self.assertEqual(bm.unigramlist("1*2*93", '*'), ['1', '2', '9', '3'])

    def test_unigram_duplicate(self):
        self.assertEqual(bm.unigramlist("1212"), ['1', '2', '1', '2'])

    def test_bigram_1(self):
        self.assertEqual(bm.bigramlist("steve"), [' s', 'st', 'te', 'ev', 've', 'e '])

    def test_bigram_2(self):
        self.assertEqual(bm.bigramlist("steve", 'e'), [' s', 'st', 'tv', 'v '])

    def test_bigram_duplicate(self):
        self.assertEqual(bm.bigramlist("abab"), [' a', 'ab', 'ba', 'ab', 'b '])

if __name__ == '__main__':
    unittest.main()
