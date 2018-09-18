import unittest
import pytest
import random
import os
from collections import deque
from bitarray import bitarray

from anonlink import bloommatcher as bm
from tests import bitarray_utils

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

@pytest.mark.skip
@pytest.mark.parametrize("L", bitarray_utils.key_lengths)
def test_dicecoeff(L):
    """
    Test the Dice coefficient of bitarrays in bas with other
    bitarrays of bas.  rotations is the number of times we rotate
    bas to generate pairs to test the Dice coefficient; 10 takes
    around 10s, 100 around 60s.
    """
    rotations = 100 if "INCLUDE_10K" in os.environ else 10;
    bas = bitarray_utils.bitarrays_of_length(L)

    # We check that the native code and Python versions of dicecoeff
    # don't ever differ by more than 10^{-6}.
    eps = 0.000001
    d = deque(bas)
    for _ in range(min(rotations, len(bas))):
        for a, b in zip(bas, d):
            diff = bm.dicecoeff_pure_python(a, b) - bm.dicecoeff_native(a, b)
            assert(abs(diff) < eps)
        d.rotate(1)

if __name__ == '__main__':
    unittest.main()
