import io
import math
import os
import unittest
import random
from operator import itemgetter

from bitarray import bitarray
from clkhash import bloomfilter, randomnames, schema
from clkhash.key_derivation import generate_key_lists

import anonlink
import anonlink.benchmark


def generate_data(samples, proportion=0.75):
    nl = randomnames.NameList(samples * 2)
    s1, s2 = nl.generate_subsets(samples, proportion)

    keys = generate_key_lists('secret', len(nl.schema_types))
    filters1 = list(map(itemgetter(0),
                    bloomfilter.stream_bloom_filters(s1, keys, nl.SCHEMA)))
    filters2 = list(map(itemgetter(0),
                    bloomfilter.stream_bloom_filters(s2, keys, nl.SCHEMA)))

    return (s1, s2, filters1, filters2)


class EntityHelperMixin(object):

    default_similarity_k = 10
    default_similarity_threshold = 0.5
    default_greedy_k = 5
    default_greedy_threshold = 0.95

    def check_accuracy(self, mapping, max_false_positives=0.02):
        # Assert that there are _almost_ no false matches
        false_matches, true_matches = 0, 0
        for indx1 in mapping:
            indx2 = mapping[indx1]
            self.assertLess(indx1, len(self.s1))
            self.assertLess(indx2, len(self.s2))

            entityA = self.s1[indx1]
            entityB = self.s2[indx2]

            if entityA != entityB:
                false_matches += 1
            else:
                true_matches += 1

        num_matches = len(mapping)
        allowed_false_matches = math.ceil(num_matches * max_false_positives)
        assert num_matches <= true_matches + allowed_false_matches

        # Check that there were approximately the expected number of matches
        self.assertLessEqual(abs((self.sample * self.proportion) - num_matches), allowed_false_matches)


class EntityHelperTestMixin(EntityHelperMixin):

    def test_greedy(self):
        candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
            (self.filters1, self.filters2),
            anonlink.similarities.dice_coefficient,
            self.default_greedy_threshold,
            k=self.default_greedy_k)
        groups = anonlink.solving.greedy_solve(candidate_pairs)
        mapping = dict(anonlink.solving.pairs_from_groups(groups))

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
        a = bitarray('1111110001110110010010011111011000110011010110111101110101110011011111111001010010111000110011110100011011110111110111110010111001011110111000110101010001011000010110010101111101110100101110100001011101010000011011111111001110001011000000111110111100001010110000010000001000010011111101001101101000100010011001000111000101001011001111010110011111011010000100011111101000111000111111111110100001101010000100110000111001100101011010101000001101001010011111100110001101101110010001110111101111111101000111001001111111010001011011100100101000101000011000010110001001010010000001100100110101011111111001110010000100110100110010010000000001111111010001010011011111111001101000111010100000000101100010010111100010000110010011101111010000100010011011101100001000000101011100111010011100111101111111010100001111111000111101000010100001111000001001101011011001110000000111110110100000110010010100101001010100010010111010001000111100000011011101010010011000111100110101100011100001111110011000010000110011010110110011110111001001110010')
        b = bitarray('1110100001111000010100111000011001010000100010011110100011111100100100111011000000101111001110100000100010001100011011110000101010111100100110000011100001001000010011010001100010100110011011001100011111101111110011011101011100100001010001011000111100001000101111000011110111101101111000111100101111001000011111010011001000001010110011110000010011101000001000110011101010001000111100010110000110101000101010111001110110101010101010001001010010001010100010011101100110100110110010101000111011011000100010001011110110011001110001101101010001001110011011001110110111011010001000101110100000101001111000001000011110011000101110001010100110000010100001111101000101101000101101001001100010111110100110000100100110111110101011100000101100000001101110101011011101011000111111100011000100101110101110101001000110011001110001001011100110001100000110110001101000011010101111011000110101111111010001011110011111010110010111011000100100111010011010001110101001011111010110000000110110011110100111001000100010111001100010111110101011101010')
        assert len(self.filters1[0]) == len(a)
        assert len(self.filters2[0]) == len(a)
        assert len(self.filters1[0]) == len(b)
        assert len(self.filters2[0]) == len(b)

        self.filters1[-1] = a
        self.filters2[-1] = a

        self.filters2[-2] = b

        candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
            (self.filters1, self.filters2),
            anonlink.similarities.dice_coefficient_python,
            0.8,
            k=20)
        groups = anonlink.solving.greedy_solve(candidate_pairs)
        mapping = dict(anonlink.solving.pairs_from_groups(groups))

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
class TestEntityMatchingE2E_10k(EntityHelperTestMixin, unittest.TestCase):

    sample = 10000
    proportion = 0.7

    def setUp(self):
        self.s1, self.s2, self.filters1, self.filters2 = generate_data(self.sample, self.proportion)


@unittest.skipUnless("INCLUDE_100K" in os.environ,
                     "Set envvar INCLUDE_100K to run")
class TestEntityMatchingE2E_100k(EntityHelperTestMixin, unittest.TestCase):

    sample = 100000
    proportion = 0.9

    def setUp(self):
        self.s1, self.s2, self.filters1, self.filters2 = generate_data(self.sample, self.proportion)


class TestEntityMatchTopK(EntityHelperMixin, unittest.TestCase):

    proportion = 0.8
    sample = 150

    def setUp(self):
        self.nl = randomnames.NameList(300)
        self.s1, self.s2 = self.nl.generate_subsets(self.sample, self.proportion)
        self.key_lists = generate_key_lists('secret', len(self.nl.schema_types))

    def test_accelerated_k(self):

        f1 = tuple(map(itemgetter(0),
                       bloomfilter.stream_bloom_filters(
                           self.s1, self.key_lists, self.nl.SCHEMA)))
        f2 = tuple(map(itemgetter(0),
                       bloomfilter.stream_bloom_filters(
                           self.s2, self.key_lists, self.nl.SCHEMA)))

        threshold = 0.9
        candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
            (f1, f2),
            anonlink.similarities.dice_coefficient_accelerated,
            threshold,
            k=4)
        groups = anonlink.solving.greedy_solve(candidate_pairs)
        mapping = dict(anonlink.solving.pairs_from_groups(groups))

        self.check_accuracy(mapping)

    def test_concurrent(self):
        f1 = tuple(map(itemgetter(0),
                       bloomfilter.stream_bloom_filters(
                           self.s1, self.key_lists, self.nl.SCHEMA)))
        f2 = tuple(map(itemgetter(0),
                       bloomfilter.stream_bloom_filters(
                           self.s2, self.key_lists, self.nl.SCHEMA)))

        threshold = 0.9
        candidate_pairs = anonlink.concurrency.process_chunk(
            [
                {"datasetIndex": 0, "range": [0, len(f1)]},
                {"datasetIndex": 1, "range": [0, len(f2)]}
            ],
            (f1, f2),
            anonlink.similarities.dice_coefficient,
            threshold,
            k=4)
        groups = anonlink.solving.greedy_solve(candidate_pairs)
        mapping = dict(anonlink.solving.pairs_from_groups(groups))

        self.check_accuracy(mapping)


class TestGreedy(unittest.TestCase):
    default_greedy_k = 5
    default_greedy_threshold = 0.95

    some_filters = anonlink.benchmark.generate_random_clks(1000)

    def test_greedy_matching_works(self):
        filters1 = [self.some_filters[random.randrange(0, 800)] for _ in range(1000)]
        filters2 = [self.some_filters[random.randrange(200, 1000)] for _ in range(1500)]
        candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
            (filters1, filters2),
            anonlink.similarities.dice_coefficient_accelerated,
            self.default_greedy_threshold,
            k=self.default_greedy_k)
        anonlink.solving.greedy_solve(candidate_pairs)

    def test_greedy_chunked_matching_works(self):
        filters1 = [self.some_filters[random.randrange(0, 800)] for _ in range(1000)]
        filters2 = [self.some_filters[random.randrange(200, 1000)] for _ in range(1500)]

        candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
            (filters1, filters2),
            anonlink.similarities.dice_coefficient_accelerated,
            self.default_greedy_threshold)
        groups = anonlink.solving.greedy_solve(candidate_pairs)
        mapping = dict(anonlink.solving.pairs_from_groups(groups))

        chunk_size = len(filters1) // 2
        filters1_chunk1, filters1_chunk2 \
            = filters1[:chunk_size], filters1[chunk_size:]
        assert len(filters1_chunk1) == len(filters1_chunk2) == chunk_size

        chunk_1 = anonlink.concurrency.process_chunk(
            [
                {"datasetIndex": 0, "range": [0, chunk_size]},
                {"datasetIndex": 1, "range": [0, len(filters2)]}
            ],
            (filters1_chunk1, filters2),
            anonlink.similarities.dice_coefficient,
            .95)
        chunk_2 = anonlink.concurrency.process_chunk(
            [
                {"datasetIndex": 0, "range": [chunk_size, len(filters1)]},
                {"datasetIndex": 1, "range": [0, len(filters2)]}
            ],
            (filters1_chunk2, filters2),
            anonlink.similarities.dice_coefficient,
            .95)

        chunk_1_f = io.BytesIO()
        anonlink.serialization.dump_candidate_pairs(chunk_1, chunk_1_f)
        chunk_1_f.seek(0)
        
        chunk_2_f = io.BytesIO()
        anonlink.serialization.dump_candidate_pairs(chunk_2, chunk_2_f)
        chunk_2_f.seek(0)

        merged_f = io.BytesIO()
        anonlink.serialization.merge_streams((chunk_1_f, chunk_2_f), merged_f)
        merged_f.seek(0)

        full_candidate_pairs = anonlink.serialization.load_candidate_pairs(
            merged_f)

        assert candidate_pairs == full_candidate_pairs
        merged_groups = anonlink.solving.greedy_solve(full_candidate_pairs)
        merged_mapping = dict(
            anonlink.solving.pairs_from_groups(merged_groups))

        assert mapping == merged_mapping



class TestSimilarityStream(EntityHelperMixin, unittest.TestCase):

    proportion = 0.8
    sample = 150

    def setUp(self):
        self.nl = randomnames.NameList(300)
        self.s1, self.s2 = self.nl.generate_subsets(self.sample, self.proportion)
        self.key_lists = generate_key_lists('secret', len(self.nl.schema_types))
        self.f1 = tuple(map(itemgetter(0),
                       bloomfilter.stream_bloom_filters(
                           self.s1, self.key_lists, self.nl.SCHEMA)))
        self.f2 = tuple(map(itemgetter(0),
                       bloomfilter.stream_bloom_filters(
                           self.s2, self.key_lists, self.nl.SCHEMA)))

    def test_similarity_stream(self):
        candidate_pairs = []
        for f1 in self.f1:
            for f2 in self.f2:
                candidate_pairs.append((f1, f2))

        similarity_stream = anonlink.similarities.dice_coefficient_pairs_python(
            candidate_pairs
        )

        assert len(similarity_stream) == len(self.f1) * len(self.f2)

        candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
            (self.f1, self.f2),
            anonlink.similarities.dice_coefficient_accelerated,
            threshold=0.0,
        )

        scores, _, (l_indicies, r_indicies) = candidate_pairs

        for score, l_index, r_index in zip(scores, l_indicies, r_indicies):
            # Calculate the index in the streamed candidate pairs list
            index = l_index * len(self.f2) + r_index
            assert similarity_stream[index] == score


if __name__ == '__main__':
    unittest.main()
