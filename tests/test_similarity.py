

import unittest
from anonlink import randomnames

from anonlink import entitymatch

__author__ = 'Brian Thorne'


class TestBloomFilterComparison(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.proportion = 0.8
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(200, cls.proportion)

        keys = ('test1', 'test2')
        cls.filters1 = entitymatch.calculate_bloom_filters(s1, nl.schema, keys)
        cls.filters2 = entitymatch.calculate_bloom_filters(s2, nl.schema, keys)

    def _check_proportion(self, similarity):
        exact_matches = 0.0
        for (idx1, score, orig1, orig2, idx2) in similarity:
            if score == 1.0:
                exact_matches += 1

        self.assertAlmostEqual(exact_matches/len(similarity), self.proportion)

    def test_cffi(self):
        similarity = entitymatch.cffi_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity),

    # def test_manual_c(self):
    #     similarity = entitymatch.c_filter_similarity(self.filters1, self.filters2)
    #     self._check_proportion(similarity)

    def test_python(self):
        similarity = entitymatch.python_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity)

    def test_default(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity)


if __name__ == "__main__":
    unittest.main()