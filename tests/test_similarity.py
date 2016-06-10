

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

    def test_cffi_manual(self):
        nl = randomnames.NameList(30)
        s1, s2 = nl.generate_subsets(5, 1.0)
        keys = ('test1', 'test2')
        f1 = entitymatch.calculate_bloom_filters(s1, nl.schema, keys)
        f2 = entitymatch.calculate_bloom_filters(s2, nl.schema, keys)

        ps = entitymatch.python_filter_similarity(f1, f2)
        cs = entitymatch.cffi_filter_similarity(f1, f2)

        python_scores = [p[1] for p in ps]
        c_scores = [c[1] for c in cs]

        self.assertEqual(python_scores, c_scores)

    def test_cffi_k(self):
        nl = randomnames.NameList(30)
        s1, s2 = nl.generate_subsets(10, 1.0)
        keys = ('test1', 'test2')
        f1 = entitymatch.calculate_bloom_filters(s1, nl.schema, keys)
        f2 = entitymatch.calculate_bloom_filters(s2, nl.schema, keys)

        cs = entitymatch.cffi_filter_similarity(f1, f2)
        csk = entitymatch.cffi_filter_similarity_k(f1, f2, 4)

        top_k_scores = [p[1] for p in csk]
        top_k_indices = [p[-1] for p in csk]

        for scores in top_k_scores:
            self.assertGreaterEqual(scores[0], scores[1])
            self.assertGreaterEqual(scores[1], scores[2])
            self.assertGreaterEqual(scores[2], scores[3])

        top_score_only =[s[0] for s in top_k_scores]
        c_scores = [c[1] for c in cs]

        self.assertEqual(top_score_only, c_scores)


    def test_cffi(self):
        similarity = entitymatch.cffi_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity)

    def test_python(self):
        similarity = entitymatch.python_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity)

    def test_default(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity)

    def test_same_score(self):
        cffi_score = entitymatch.cffi_filter_similarity(self.filters1, self.filters2)
        python_score = entitymatch.python_filter_similarity(self.filters1, self.filters2)
        for i in range(len(cffi_score)):
            self.assertEqual(cffi_score[i][1], python_score[i][1])

    def test_empty_input_a(self):
        with self.assertRaises(ValueError):
            entitymatch.calculate_filter_similarity([], self.filters2)

    def test_empty_input_b(self):
        with self.assertRaises(ValueError):
            entitymatch.calculate_filter_similarity(self.filters1, [])

    def test_small_input_a(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1[:10], self.filters2, use_python=True)
        similarity = entitymatch.calculate_filter_similarity(self.filters1[:10], self.filters2, use_python=False)

    def test_small_input_b(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2[:10], use_python=True)
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2[:10], use_python=False)


if __name__ == "__main__":
    unittest.main()