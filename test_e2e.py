import unittest
import randomnames
import network_flow
import entitymatch

__author__ = 'Brian Thorne'


class TestEntityMatchingE2E(unittest.TestCase):

    def test_small(self):
        nl = randomnames.NameList(100)
        s1, s2 = nl.generate_subsets(50, 0.75)

        keys = ('test1', 'test2')
        filters1 = entitymatch.calculate_bloom_filters(s1, nl.schema, keys)
        filters2 = entitymatch.calculate_bloom_filters(s2, nl.schema, keys)

        similarity = entitymatch.calculate_filter_similarity(filters1, filters2)

        flow, mapping = network_flow.map_entities(similarity)

        print(flow)
        print(mapping)


if __name__ == '__main__':
    unittest.main()
