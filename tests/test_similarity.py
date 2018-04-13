

import unittest

from clkhash import bloomfilter, randomnames, schema
from clkhash.key_derivation import generate_key_lists

from anonlink import entitymatch

__author__ = 'Brian Thorne'


class TestBloomFilterComparison(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.proportion = 0.8
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(200, cls.proportion)

        keys = generate_key_lists(('test1', 'test2'), len(nl.schema))
        cls.filters1 = bloomfilter.calculate_bloom_filters(s1, schema.get_schema_types(nl.schema), keys)
        cls.filters2 = bloomfilter.calculate_bloom_filters(s2, schema.get_schema_types(nl.schema), keys)

        cls.default_k = 10
        cls.default_threshold = 0.5

    def _check_proportion(self, similarity):
        exact_matches = 0.0
        for (idx1, score, idx2) in similarity:
            if score == 1.0:
                exact_matches += 1

        self.assertAlmostEqual(exact_matches/len(self.filters1), self.proportion)
        self.assertAlmostEqual(exact_matches/len(self.filters2), self.proportion)

    def test_cffi_manual(self):
        nl = randomnames.NameList(30)
        s1, s2 = nl.generate_subsets(5, 1.0)
        keys = generate_key_lists(('test1', 'test2'), len(nl.schema))
        f1 = bloomfilter.calculate_bloom_filters(s1, schema.get_schema_types(nl.schema), keys)
        f2 = bloomfilter.calculate_bloom_filters(s2, schema.get_schema_types(nl.schema), keys)

        ps = entitymatch.python_filter_similarity(f1, f2)
        cs = entitymatch.cffi_filter_similarity_k(f1, f2, 1, 0.0)

        python_scores = [p[1] for p in ps]
        c_scores = [c[1] for c in cs]

        self.assertAlmostEqual(python_scores, c_scores)

    def test_cffi(self):
        similarity = entitymatch.cffi_filter_similarity_k(self.filters1, self.filters2, 1, 0.0)
        self._check_proportion(similarity)

    def test_python(self):
        similarity = entitymatch.python_filter_similarity(self.filters1, self.filters2)
        self._check_proportion(similarity)

    def test_default(self):
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2, self.default_k, self.default_threshold)
        self._check_proportion(similarity)

    def test_same_score(self):
        cffi_score = entitymatch.cffi_filter_similarity_k(self.filters1, self.filters2, 1, 0.0)
        python_score = entitymatch.python_filter_similarity(self.filters1, self.filters2)
        for i in range(len(cffi_score)):
            self.assertEqual(cffi_score[i][1], python_score[i][1])

    def test_empty_input_a(self):
        with self.assertRaises(ValueError):
            entitymatch.calculate_filter_similarity(
                [], self.filters2, self.default_k, self.default_threshold)

    def test_empty_input_b(self):
        with self.assertRaises(ValueError):
            entitymatch.calculate_filter_similarity(
                self.filters1, [], self.default_k, self.default_threshold)

    def test_small_input_a(self):
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1[:10], self.filters2, self.default_k, self.default_threshold, use_python=True)
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1[:10], self.filters2, self.default_k, self.default_threshold, use_python=False)

    def test_small_input_b(self):
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2[:10], self.default_k, self.default_threshold, use_python=True)
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2[:10], self.default_k, self.default_threshold, use_python=False)


if __name__ == "__main__":
    unittest.main()
