import unittest

from clkhash import bloomfilter, randomnames, schema
from clkhash.key_derivation import generate_key_lists

from anonlink import similarities

__author__ = 'Brian Thorne'

FLOAT_ARRAY_TYPES = 'fd'
UINT_ARRAY_TYPES = 'BHILQ'


class TestBloomFilterComparison(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.proportion = 0.8
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(200, cls.proportion)

        keys = generate_key_lists(('test1', 'test2'), len(nl.schema_types))
        cls.filters1 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s1, keys, nl.SCHEMA))
        cls.filters2 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s2, keys, nl.SCHEMA))
        cls.filters = cls.filters1, cls.filters2

        cls.default_k = 10
        cls.default_threshold = 0.5

    def _check_proportion(self, candidate_pairs):
        sims, _ = candidate_pairs
        exact_matches = sum(sim == 1 for sim in sims)

        self.assertAlmostEqual(exact_matches / len(self.filters1),
                               self.proportion)
        self.assertAlmostEqual(exact_matches / len(self.filters2),
                               self.proportion)

    def assert_similarity_matrices_equal(self, M, N):
        M_sims, (M_indices0, M_indices1) = M
        N_sims, (N_indices0, N_indices1) = N
        assert (set(zip(M_sims, M_indices0, M_indices1))
                == set(zip(N_sims, N_indices0, N_indices1)))

    def test_cffi_manual(self):
        nl = randomnames.NameList(30)
        s1, s2 = nl.generate_subsets(5, 1.0)
        keys = generate_key_lists(('test1', 'test2'), len(nl.schema_types))
        f1 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s1, keys, nl.SCHEMA))
        f2 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s2, keys, nl.SCHEMA))

        py_similarity = similarities.dice_coefficient_python(
            (f1, f2), self.default_threshold, self.default_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (f1, f2), self.default_threshold, self.default_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_cffi(self):
        similarity = similarities.dice_coefficient_accelerated(
            self.filters, self.default_threshold, self.default_k)
        self._check_proportion(similarity)

    def test_python(self):
        similarity = similarities.dice_coefficient_python(
            self.filters, self.default_threshold, self.default_k)
        self._check_proportion(similarity)

    def test_default(self):
        similarity = similarities.dice_coefficient(
            self.filters, self.default_threshold, self.default_k)
        self._check_proportion(similarity)

    def test_same_score(self):
        cffi_cands = similarities.dice_coefficient_accelerated(
            self.filters, self.default_threshold, self.default_k)
        cffi_scores, _ = cffi_cands
        python_cands = similarities.dice_coefficient_python(
            self.filters, self.default_threshold, self.default_k)
        python_scores, _ = python_cands
        assert cffi_scores == python_scores

    def test_same_score_k_none(self):
        cffi_cands = similarities.dice_coefficient_accelerated(
            self.filters, self.default_threshold, None)
        cffi_scores, _ = cffi_cands
        python_cands = similarities.dice_coefficient_python(
            self.filters, self.default_threshold, None)
        python_scores, _ = python_cands
        assert cffi_scores == python_scores

    def test_empty_input_a(self):
        candidate_pairs = similarities.dice_coefficient(
            ((), self.filters2), self.default_threshold, self.default_k)
        sims, (indices0, indices1) = candidate_pairs
        assert len(sims) == len(indices0) == len(indices1) == 0
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert indices0.typecode in UINT_ARRAY_TYPES
        assert indices1.typecode in UINT_ARRAY_TYPES


    def test_empty_input_b(self):
        candidate_pairs = similarities.dice_coefficient(
            (self.filters1, ()), self.default_threshold, self.default_k)
        sims, (indices0, indices1) = candidate_pairs
        assert len(sims) == len(indices0) == len(indices1) == 0
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert indices0.typecode in UINT_ARRAY_TYPES
        assert indices1.typecode in UINT_ARRAY_TYPES

    def test_small_input_a(self):
        py_similarity = similarities.dice_coefficient_python(
            (self.filters1[:10], self.filters2),
            self.default_threshold, self.default_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (self.filters1[:10], self.filters2),
            self.default_threshold, self.default_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_small_input_b(self):
        py_similarity = similarities.dice_coefficient_python(
            (self.filters1, self.filters2[:10]),
            self.default_threshold, self.default_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (self.filters1, self.filters2[:10]),
            self.default_threshold, self.default_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_memory_use(self):
        n = 10
        f1 = self.filters1[:n]
        f2 = self.filters2[:n]
        # If memory is not handled correctly, then this would allocate
        # several terabytes of RAM.
        big_k = 1 << 50
        py_similarity = similarities.dice_coefficient_python(
            (f1, f2), self.default_threshold, big_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (f1, f2), self.default_threshold, big_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)


if __name__ == "__main__":
    unittest.main()
