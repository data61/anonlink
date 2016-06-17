
import unittest
import networkx as nx

from anonlink import network_flow

__author__ = 'Brian Thorne'


class TestNetworkMatching(unittest.TestCase):
    """Network tests on following graph:

    [row0]  ----   [col0]
    [row1]  ----   [col1]
    [row2]  \__-   [col2]
    [row3]  __|    [col3]

    A much weaker connection exists between row1 and col2.

    The desired behaviour is to ignore this lower rated connection
    """

    def setUp(self):
        self.G = nx.Graph()

        score = 0.9

        self.G.add_edge('row0', 'col0', weight=score, capacity=1.0)
        self.G.add_edge('row1', 'col1', weight=score, capacity=1.0)
        self.G.add_edge('row1', 'col2', weight=score / 3, capacity=1.0)
        self.G.add_edge('row3', 'col2', weight=score, capacity=1.0)

        self.expected_map = {
            0: 0,
            1: 1,
            3: 2
        }

    def tearDown(self):
        del self.G

    def test_default(self):
        mapping = network_flow.calculate_entity_mapping(self.G)
        self.assertDictEqual(self.expected_map, mapping)

    def test_bipartite(self):
        mapping = network_flow.calculate_entity_mapping(self.G, method='bipartite')
        self.assertDictEqual(self.expected_map, mapping)

    def test_weighted(self):
        mapping = network_flow.calculate_entity_mapping(self.G, method='weighted')
        self.assertDictEqual(self.expected_map, mapping)

    def test_invalid(self):
        args = (self.G, 'random')
        self.assertRaises(NotImplementedError, network_flow.calculate_entity_mapping, *args)


class TestNetworkMatchingDuplicates(unittest.TestCase):
    """Tests network matching on following graph:

    [row0]  ----   [col0]
    [row1]  ----   [col1]
    [row2]  ----   [col2]
    [row3]  __|    [col3]
    [row4]

    A slightly weaker connection exists between row2 and col2.

    The expected output will not include a matching between these, as
    col2 is strongly connected to row3.
    """

    def setUp(self):
        self.G = nx.Graph()

        score = 0.9

        self.G.add_edge('row0', 'col0', weight=score, capacity=1.0)
        self.G.add_edge('row1', 'col1', weight=score, capacity=1.0)
        self.G.add_edge('row1', 'col2', weight=score / 3, capacity=1.0)
        self.G.add_edge('row3', 'col2', weight=score, capacity=1.0)
        self.G.add_node('row4')

        self.expected_map = {
            0: 0,
            1: 1,
            3: 2
        }

    def test_default(self):
        mapping = network_flow.calculate_entity_mapping(self.G)
        self.assertDictEqual(self.expected_map, mapping)

    def test_bipartite(self):
        mapping = network_flow.calculate_entity_mapping(self.G, method='bipartite')
        self.assertDictEqual(self.expected_map, mapping)

    def test_weighted(self):
        mapping = network_flow.calculate_entity_mapping(self.G, method='weighted')
        self.assertDictEqual(self.expected_map, mapping)

    def test_invalid(self):
        args = (self.G, 'random')
        self.assertRaises(NotImplementedError, network_flow.calculate_entity_mapping, *args)


if __name__ == "__main__":
    unittest.main()
