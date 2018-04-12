import os
import unittest
import random
from operator import itemgetter

from clkhash import bloomfilter, randomnames, schema
from clkhash.key_derivation import generate_key_lists

from anonlink import network_flow
from anonlink import entitymatch
from anonlink import distributed_processing
from anonlink.util import *

__author__ = 'Brian Thorne'


def generate_data(samples, proportion=0.75):
    nl = randomnames.NameList(samples * 2)
    s1, s2 = nl.generate_subsets(samples, proportion)

    keys = generate_key_lists(('test1', 'test2'), len(nl.schema))
    filters1 = bloomfilter.calculate_bloom_filters(s1, schema.get_schema_types(nl.schema), keys)
    filters2 = bloomfilter.calculate_bloom_filters(s2, schema.get_schema_types(nl.schema), keys)

    return (s1, s2, filters1, filters2)


class EntityHelperMixin(object):

    def check_accuracy(self, mapping):
        # Assert that there are no false matches
        for indx1 in mapping:
            indx2 = mapping[indx1]
            self.assertLess(indx1, len(self.s1))
            self.assertLess(indx2, len(self.s2))

            entityA = self.s1[indx1]
            entityB = self.s2[indx2]

            self.assertEqual(entityA, entityB)

        # Check that there were approximately the expected number of matches
        self.assertLessEqual(abs((self.sample * self.proportion) - len(mapping)), 3)


class EntityHelperTestMixin(EntityHelperMixin):
    default_similarity_k = 10
    default_similarity_threshold = 0.5
    default_greedy_k = 5
    default_greedy_threshold = 0.95

    def test_default(self):
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2, self.default_similarity_k, self.default_similarity_threshold)
        mapping = network_flow.map_entities(similarity, threshold=0.95)
        self.check_accuracy(mapping)

    def test_bipartite(self):
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2, self.default_similarity_k, self.default_similarity_threshold)
        mapping = network_flow.map_entities(similarity, threshold=0.95, method='bipartite')
        self.check_accuracy(mapping)

    def test_weighted(self):
        similarity = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2, self.default_similarity_k, self.default_similarity_threshold)
        mapping = network_flow.map_entities(similarity, threshold=0.95, method='weighted')
        self.check_accuracy(mapping)

    def test_greedy(self):
        mapping = entitymatch.calculate_mapping_greedy(
            self.filters1, self.filters2, self.default_greedy_threshold, self.default_greedy_k)
        self.check_accuracy(mapping)


class TestEntityMatchingE2E_Tiny(EntityHelperTestMixin, unittest.TestCase):

    sample = 5
    proportion = 0.8

    @classmethod
    def setUpClass(cls):
        cls.s1, cls.s2, cls.filters1, cls.filters2 = generate_data(cls.sample, cls.proportion)


class TestEntityMatchingE2E_100(EntityHelperTestMixin, unittest.TestCase):

    sample = 100
    proportion = 0.9

    @classmethod
    def setUpClass(cls):
        cls.s1, cls.s2, cls.filters1, cls.filters2 = generate_data(cls.sample, cls.proportion)


    def test_extra(self):
        a = bitarray('11111100011101100100100111110110001100110101101111011101011100110111111110010100101110001100111101000110111101111101111100101110010111101110001101010100010110000101100101011111011101001011101000010111010100000110111111110011100010110000001111101111000010101100000100000010000100111111010011011010001000100110010001110001010010110011110101100111110110100001000111111010001110001111111111101000011010100001001100001110011001010110101010000011010010100111111001100011011011100100011101111011111111010001110010011111110100010110111001001010001010000110000101100010010100100000011001001101010111111110011100100001001101001100100100000000011111110100010100110111111110011010001110101000000001011000100101111000100001100100111011110100001000100110111011000010000001010111001110100111001111011111110101000011111110001111010000101000011110000010011010110110011100000001111101101000001100100101001010010101000100101110100010001111000000110111010100100110001111001101011000111000011111100110000100001100110101101100111101110010')
        b = bitarray('11101000011110000101001110000110010100001000100111101000111111001001001110110000001011110011101000001000100011000110111100001010101111001001100000111000010010000100110100011000101001100110110011000111111011111100110111010111001000010100010110001111000010001011110000111101111011011110001111001011110010000111110100110010000010101100111100000100111010000010001100111010100010001111000101100001101010001010101110011101101010101010100010010100100010101000100111011001101001101100101010001110110110001000100010111101100110011100011011010100010011100110110011101101110110100010001011101000001010011110000010000111100110001011100010101001100000101000011111010001011010001011010010011000101111101001100001001001101111101010111000001011000000011011101010110111010110001111111000110001001011101011101010010001100110011100010010111001100011000001101100011010000110101011110110001101011111110100010111100111110101100101110110001001001110100110100011101010010111110101100000001101100111101001110010001000101110011000101111101010')

        self.filters1[-1] = (a, 100, a.count())
        self.filters2[-1] = (a, 100, a.count())

        self.filters2[-2] = (b, 101, b.count())

        sparse_scores = entitymatch.calculate_filter_similarity(
            self.filters1, self.filters2, k=20, threshold=0.8, use_python=False)
        ordered_by_score = sorted(sparse_scores, key=itemgetter(1), reverse=True)

        ordered_scores = sorted(ordered_by_score, key=itemgetter(0))

        mapping = entitymatch.greedy_solver(ordered_scores)
        self.check_accuracy(mapping)


class TestEntityMatchingE2E_1K(EntityHelperTestMixin, unittest.TestCase):

    sample = 1000
    proportion = 0.7

    @classmethod
    def setUpClass(cls):
        cls.s1, cls.s2, cls.filters1, cls.filters2 = generate_data(cls.sample, cls.proportion)

# Larger tests only using the Greedy solver

@unittest.skipUnless("INCLUDE_10K" in os.environ,
                     "Set envvar INCLUDE_10K to run")
class TestEntityMatchingE2E_10k(EntityHelperMixin, unittest.TestCase):

    sample = 10000
    proportion = 0.7

    def setUp(self):
        self.s1, self.s2, self.filters1, self.filters2 = generate_data(self.sample, self.proportion)

    def test_greedy(self):
        mapping = entitymatch.calculate_mapping_greedy(
            self.filters1, self.filters2, self.default_greedy_threshold, self.default_greedy_k)
        self.check_accuracy(mapping)


@unittest.skipUnless("INCLUDE_100K" in os.environ,
                     "Set envvar INCLUDE_100K to run")
class TestEntityMatchingE2E_100k(EntityHelperMixin, unittest.TestCase):

    sample = 100000
    proportion = 0.9

    def setUp(self):
        self.s1, self.s2, self.filters1, self.filters2 = generate_data(self.sample, self.proportion)

    def test_greedy(self):
        mapping = entitymatch.calculate_mapping_greedy(
            self.filters1, self.filters2, self.default_greedy_threshold, self.default_greedy_k)
        self.check_accuracy(mapping)


class TestEntityMatchTopK(unittest.TestCase):
    def test_cffi_k(self):
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(150, 0.8)
        keys = ('test1', 'test2')
        key_lists = generate_key_lists(keys, len(nl.schema))
        f1 = bloomfilter.calculate_bloom_filters(s1, schema.get_schema_types(nl.schema), key_lists)
        f2 = bloomfilter.calculate_bloom_filters(s2, schema.get_schema_types(nl.schema), key_lists)

        threshold = 0.8
        similarity = entitymatch.cffi_filter_similarity_k(f1, f2, 4, threshold)
        mapping = network_flow.map_entities(similarity, threshold, method=None)

        for indexA in mapping:
            self.assertEqual(s1[indexA], s2[mapping[indexA]])

    def test_concurrent(self):
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(150, 0.8)
        keys = ('test1', 'test2')
        key_lists = generate_key_lists(keys, len(nl.schema))
        f1 = bloomfilter.calculate_bloom_filters(s1, schema.get_schema_types(nl.schema), key_lists)
        f2 = bloomfilter.calculate_bloom_filters(s2, schema.get_schema_types(nl.schema), key_lists)

        threshold = 0.8
        similarity = distributed_processing.calculate_filter_similarity(f1, f2, 4, threshold)
        mapping = network_flow.map_entities(similarity, threshold, method=None)

        for indexA in mapping:
            self.assertEqual(s1[indexA], s2[mapping[indexA]])


class TestGreedy(unittest.TestCase):
    default_greedy_k = 5
    default_greedy_threshold = 0.95

    some_filters = generate_clks(1000)

    def test_greedy_matching_works(self):
        filters1 = [self.some_filters[random.randrange(0, 800)] for _ in range(1000)]
        filters2 = [self.some_filters[random.randrange(200, 1000)] for _ in range(1500)]
        result = entitymatch.calculate_mapping_greedy(
            filters1, filters2, self.default_greedy_threshold, self.default_greedy_k)

    def test_greedy_chunked_matching_works(self):
        filters1 = [self.some_filters[random.randrange(0, 800)] for _ in range(1000)]
        filters2 = [self.some_filters[random.randrange(200, 1000)] for _ in range(1500)]

        all_in_one_mapping = entitymatch.calculate_mapping_greedy(
            filters1, filters2, self.default_greedy_threshold, self.default_greedy_k)

        filters1_chunk1, filters1_chunk2 = filters1[:500],  filters1[500:]
        assert len(filters1_chunk1) == 500

        chunk_1 = entitymatch.calculate_filter_similarity(filters1_chunk1, filters2, threshold=0.95, k=5)

        chunk_2 = distributed_processing.calc_chunk_result(1, filters1_chunk2, filters2, k=5, threshold=0.95)

        full_similarity_scores = entitymatch.calculate_filter_similarity(filters1, filters2, threshold=0.95, k=5)

        sparse_matrix = chunk_1
        sparse_matrix.extend(chunk_2)

        self.assertEqual(len(full_similarity_scores), len(sparse_matrix))

        partial_mapping = entitymatch.greedy_solver(sparse_matrix)

        for entityA in all_in_one_mapping:
            assert entityA in partial_mapping
            self.assertEqual(all_in_one_mapping[entityA], partial_mapping[entityA])

if __name__ == '__main__':
    unittest.main()
