import unittest
import random
from bitarray import bitarray

from anonlink import bloommatcher as bm

__author__ = 'shardy'


class TestBloomMatcher(unittest.TestCase):

    def generate_bitarray(self, length):
        return bitarray(
            ''.join('1' if random.random() > 0.5 else '0' for _ in range(length))
        )

    def test_tanimoto_1(self):
        self.assertEqual(bm.tanimoto(bitarray('1111011'), bitarray('1111011')), 1.0)

    def test_tanimoto_2(self):
        self.assertEqual(bm.tanimoto(bitarray('0000100'), bitarray('1111011')), 0.0)

    def test_tanimoto_3(self):
        self.assertEqual(bm.tanimoto(bitarray('1000011'), bitarray('1111011')), 0.5)

    def test_tanimoto_precount_1(self):
        self.assertEqual(bm.tanimoto_precount(bitarray('1000011'), bitarray('1111011'), 9.0), 0.5)

    def test_dice_1(self):
        self.assertEqual(bm.dicecoeff_pure_python(bitarray('1111011'), bitarray('1111011')), 1.0)

    def test_dice_2(self):
        self.assertEqual(bm.dicecoeff_pure_python(bitarray('0000100'), bitarray('1111011')), 0.0)

    def test_dice_3(self):
        self.assertEqual(bm.dicecoeff_pure_python(bitarray('1000001'), bitarray('1111011')), 0.5)

    def test_dice_precount_1(self):
        self.assertEqual(bm.dicecoeff_precount(bitarray('1000001'), bitarray('1111011'), 8.0), 0.5)

    def test_unigram_1(self):
        self.assertEqual(bm.unigramlist("1/2/93", '/'), ['1', '2', '9', '3'])

    def test_unigram_2(self):
        self.assertEqual(bm.unigramlist("1*2*93", '*'), ['1', '2', '9', '3'])

    def test_unigram_duplicate(self):
        self.assertEqual(bm.unigramlist("1212"), ['1', '2', '1', '2'])

    def test_positional_unigram_1(self):
        self.assertEqual(bm.positional_unigrams("123"), ['1 1', '2 2', '3 3'])

    def test_positional_unigram_2(self):
        self.assertEqual(bm.positional_unigrams("1*2*"), ['1 1', '2 *', '3 2', '4 *'])

    def test_positional_unigram_duplicate(self):
        self.assertEqual(bm.positional_unigrams("111"), ['1 1', '2 1', '3 1'])

    def test_bigram_1(self):
        self.assertEqual(bm.bigramlist("steve"), [' s', 'st', 'te', 'ev', 've', 'e '])

    def test_bigram_2(self):
        self.assertEqual(bm.bigramlist("steve", 'e'), [' s', 'st', 'tv', 'v '])

    def test_bigram_duplicate(self):
        self.assertEqual(bm.bigramlist("abab"), [' a', 'ab', 'ba', 'ab', 'b '])

    def test_dice_1_c(self):
        ba = self.generate_bitarray(1024)
        self.assertEqual(bm.dicecoeff(ba, ba), 1.0)

    def test_dice_2_c(self):
        ba = self.generate_bitarray(1024)
        bb = ba.copy()
        bb.invert()
        self.assertEqual(bm.dicecoeff(ba, bb), 0.0)

    def test_dice_3_c(self):
        ba = self.generate_bitarray(1024)
        bb = self.generate_bitarray(1024)
        result = bm.dicecoeff(ba, bb)

        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)


if __name__ == '__main__':
    unittest.main()
