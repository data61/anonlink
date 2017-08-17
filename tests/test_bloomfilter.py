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

    def test_dice_4(self):
        self.assertEqual(bm.dicecoeff_pure_python(bitarray('00000000'), bitarray('00000000')), 0.0)

    def test_dice_precount_1(self):
        self.assertEqual(bm.dicecoeff_precount(bitarray('1000001'), bitarray('1111011'), 8.0), 0.5)

    def test_unigram_1(self):
        self.assertEqual(bm.unigramlist("1/2/93", '/'), ['1', '2', '9', '3'])

    def test_unigram_2(self):
        self.assertEqual(bm.unigramlist("1*2*93", '*'), ['1', '2', '9', '3'])

    def test_unigram_duplicate(self):
        self.assertEqual(bm.unigramlist("1212"), ['1', '2', '1', '2'])

    def test_unigram_1_positional(self):
        self.assertEqual(bm.unigramlist("1/2/93", '/', positional=True), ['1 1', '2 2', '3 9', '4 3'])

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

    def test_dice_small(self):
        ba = self.generate_bitarray(64)
        self.assertEqual(bm.dicecoeff(ba, ba), 1.0)

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

    def test_dice_4_c(self):
        ba = bitarray('0' * 1024)
        bb = bitarray('0' * 1024)
        result = bm.dicecoeff(ba, bb)

        self.assertEqual(result, 0.0)

    def test_manual(self):
        a = bitarray('11111100011101100100100111110110001100110101101111011101011100110111111110010100101110001100111101000110111101111101111100101110010111101110001101010100010110000101100101011111011101001011101000010111010100000110111111110011100010110000001111101111000010101100000100000010000100111111010011011010001000100110010001110001010010110011110101100111110110100001000111111010001110001111111111101000011010100001001100001110011001010110101010000011010010100111111001100011011011100100011101111011111111010001110010011111110100010110111001001010001010000110000101100010010100100000011001001101010111111110011100100001001101001100100100000000011111110100010100110111111110011010001110101000000001011000100101111000100001100100111011110100001000100110111011000010000001010111001110100111001111011111110101000011111110001111010000101000011110000010011010110110011100000001111101101000001100100101001010010101000100101110100010001111000000110111010100100110001111001101011000111000011111100110000100001100110101101100111101110010')
        b = bitarray('11101000011110000101001110000110010100001000100111101000111111001001001110110000001011110011101000001000100011000110111100001010101111001001100000111000010010000100110100011000101001100110110011000111111011111100110111010111001000010100010110001111000010001011110000111101111011011110001111001011110010000111110100110010000010101100111100000100111010000010001100111010100010001111000101100001101010001010101110011101101010101010100010010100100010101000100111011001101001101100101010001110110110001000100010111101100110011100011011010100010011100110110011101101110110100010001011101000001010011110000010000111100110001011100010101001100000101000011111010001011010001011010010011000101111101001100001001001101111101010111000001011000000011011101010110111010110001111111000110001001011101011101010010001100110011100010010111001100011000001101100011010000110101011110110001101011111110100010111100111110101100101110110001001001110100110100011101010010111110101100000001101100111101001110010001000101110011000101111101010')

        self.assertLess(bm.dicecoeff(a, b), 1.0)


if __name__ == '__main__':
    unittest.main()
