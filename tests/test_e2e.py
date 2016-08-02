import os
import unittest
import random
from bitarray import bitarray

import anonlink.bloomfilter
from anonlink import randomnames
from anonlink import network_flow
from anonlink import entitymatch
from anonlink import concurrent
from anonlink.util import *

__author__ = 'Brian Thorne'


def generate_data(samples, proportion=0.75):
    nl = randomnames.NameList(samples * 2)
    s1, s2 = nl.generate_subsets(samples, proportion)

    keys = ('test1', 'test2')
    filters1 = anonlink.bloomfilter.calculate_bloom_filters(s1, nl.schema, keys)
    filters2 = anonlink.bloomfilter.calculate_bloom_filters(s2, nl.schema, keys)

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
    def test_default(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2)
        mapping = network_flow.map_entities(similarity, threshold=0.95)
        self.check_accuracy(mapping)

    def test_bipartite(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2)
        mapping = network_flow.map_entities(similarity, threshold=0.95, method='bipartite')
        self.check_accuracy(mapping)

    def test_weighted(self):
        similarity = entitymatch.calculate_filter_similarity(self.filters1, self.filters2)
        mapping = network_flow.map_entities(similarity, threshold=0.95, method='weighted')
        self.check_accuracy(mapping)

    def test_greedy(self):
        mapping = entitymatch.calculate_mapping_greedy(self.filters1, self.filters2)
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
        mapping = entitymatch.calculate_mapping_greedy(self.filters1, self.filters2)
        self.check_accuracy(mapping)


@unittest.skipUnless("INCLUDE_100K" in os.environ,
                     "Set envvar INCLUDE_100K to run")
class TestEntityMatchingE2E_100k(EntityHelperMixin, unittest.TestCase):

    sample = 100000
    proportion = 0.9

    def setUp(self):
        self.s1, self.s2, self.filters1, self.filters2 = generate_data(self.sample, self.proportion)

    def test_greedy(self):
        mapping = entitymatch.calculate_mapping_greedy(self.filters1, self.filters2)
        self.check_accuracy(mapping)


class TestEntityMatchTopK(unittest.TestCase):
    def test_cffi_k(self):
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(150, 0.8)
        keys = ('test1', 'test2')
        f1 = anonlink.bloomfilter.calculate_bloom_filters(s1, nl.schema, keys)
        f2 = anonlink.bloomfilter.calculate_bloom_filters(s2, nl.schema, keys)

        threshold = 0.8
        similarity = entitymatch.cffi_filter_similarity_k(f1, f2, 4, threshold)
        mapping = network_flow.map_entities(similarity, threshold=threshold, method=None)

        for indexA in mapping:
            self.assertEqual(s1[indexA], s2[mapping[indexA]])

    def test_concurrent(self):
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(150, 0.8)
        keys = ('test1', 'test2')
        f1 = anonlink.bloomfilter.calculate_bloom_filters(s1, nl.schema, keys)
        f2 = anonlink.bloomfilter.calculate_bloom_filters(s2, nl.schema, keys)

        threshold = 0.8
        similarity = concurrent.calculate_filter_similarity(f1, f2, 4, threshold)
        mapping = network_flow.map_entities(similarity, threshold=threshold, method=None)

        for indexA in mapping:
            self.assertEqual(s1[indexA], s2[mapping[indexA]])


class TestGreedy(unittest.TestCase):

    some_filters = generate_clks(1000)

    def test_greedy_matching_works(self):
        filters1 = [self.some_filters[random.randrange(0, 800)] for _ in range(1000)]
        filters2 = [self.some_filters[random.randrange(200, 1000)] for _ in range(1500)]
        result = entitymatch.calculate_mapping_greedy(filters1, filters2)

    def test_greedy_chunked_matching_works(self):
        filters1 = [self.some_filters[random.randrange(0, 800)] for _ in range(1000)]
        filters2 = [self.some_filters[random.randrange(200, 1000)] for _ in range(1500)]

        all_in_one_mapping = entitymatch.calculate_mapping_greedy(filters1, filters2, threshold=0.95, k=5)

        filters1_chunk1, filters1_chunk2 = filters1[:500],  filters1[500:]
        assert len(filters1_chunk1) == 500

        chunk_1 = entitymatch.calculate_filter_similarity(filters1_chunk1, filters2, threshold=0.95, k=5)
        chunk_2_orig = entitymatch.calculate_filter_similarity(filters1_chunk2, filters2, threshold=0.95, k=5)
        chunk_2 = []
        # offset chunk2's index by 500
        for (ia, score, ib) in chunk_2_orig:
            chunk_2.append((ia + 500, score, ib))

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
