import unittest
from anonlink import randomnames
from anonlink import network_flow
from anonlink import entitymatch

__author__ = 'Brian Thorne'


class EntityHelper(object):


    @staticmethod
    def generate_data(samples, proportion=0.75):

        nl = randomnames.NameList(samples * 2)
        s1, s2 = nl.generate_subsets(samples, proportion)

        keys = ('test1', 'test2')
        filters1 = entitymatch.calculate_bloom_filters(s1, nl.schema, keys)
        filters2 = entitymatch.calculate_bloom_filters(s2, nl.schema, keys)

        return (s1, s2, filters1, filters2)

    def check_accuracy(self, mapping):
        # Assert that there are no false matches
        for indx1 in mapping:
            indx2 = mapping[indx1]
            self.assertEqual(self.s1[indx1], self.s2[indx2])

        # Check that there were approximately the expected number of matches
        self.assertLessEqual(abs((self.sample * self.proportion) - len(mapping)), 3)

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


class TestEntityMatchingE2ESmall(EntityHelper, unittest.TestCase):

    sample = 5
    proportion = 0.8

    @classmethod
    def setUpClass(cls):
        cls.s1, cls.s2, cls.filters1, cls.filters2 = EntityHelper.generate_data(cls.sample, cls.proportion)


class TestEntityMatchingE2EMedium(EntityHelper, unittest.TestCase):

    sample = 100
    proportion = 0.9

    @classmethod
    def setUpClass(cls):
        cls.s1, cls.s2, cls.filters1, cls.filters2 = EntityHelper.generate_data(cls.sample, cls.proportion)


class TestEntityMatchingE2ELarge(EntityHelper, unittest.TestCase):

    sample = 500
    proportion = 0.7

    @classmethod
    def setUpClass(cls):
        cls.s1, cls.s2, cls.filters1, cls.filters2 = EntityHelper.generate_data(cls.sample, cls.proportion)


class TestEntityMatchTopK(unittest.TestCase):
    def test_cffi_k(self):
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(150, 0.8)
        keys = ('test1', 'test2')
        f1 = entitymatch.calculate_bloom_filters(s1, nl.schema, keys)
        f2 = entitymatch.calculate_bloom_filters(s2, nl.schema, keys)

        similarity = entitymatch.cffi_filter_similarity_k(f1, f2, 4)
        mapping = network_flow.map_entities(similarity, threshold=0.8, method=None)

        for indexA in mapping:
            self.assertEqual(s1[indexA], s2[mapping[indexA]])


if __name__ == '__main__':
    unittest.main()
