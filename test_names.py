import unittest
from datetime import datetime

import randomnames as rn

__author__ = 'shardy'



class TestRandomNames(unittest.TestCase):

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
