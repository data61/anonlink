
import unittest
import networkx as nx
from anonlink.entitymatch import greedy_solver

from anonlink import network_flow

__author__ = 'Brian Thorne'


def convert_graph_to_sparse(G):
    res = []
    for node in G.nodes():
        if node.startswith("col"):
            for linked_node in G[node]:
                res.append([int(linked_node[3:]), G[node][linked_node]['weight'], int(node[3:])])

    return res


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
        self.G.add_node('row2')
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

    @unittest.expectedFailure
    def test_greedy_badorder(self):
        #sparse_similarity_matrix = convert_graph_to_sparse(self.G)
        sparse_similarity_matrix = [[1, 0.3, 2], [3, 0.9, 2], [1, 0.9, 1], [0, 0.9, 0]]
        mapping = greedy_solver(sparse_similarity_matrix)
        self.assertDictEqual(self.expected_map, mapping)

    def test_greedy_presorted(self):
        #sparse_similarity_matrix = convert_graph_to_sparse(self.G)
        sparse_similarity_matrix = [[3, 0.9, 2], [1, 0.9, 1], [0, 0.9, 0], [1, 0.3, 2]]
        mapping = greedy_solver(sparse_similarity_matrix)
        self.assertDictEqual(self.expected_map, mapping)


class TestNetworkMatchingDuplicates(unittest.TestCase):
    """Tests network matching on following graph:

    [row0]  ----   [col0]
    [row1]  ----   [col1]
    [row2]    --   [col2]
    [row3]  __|    [col3]
    [row4]

    A slightly weaker connection exists between row1 and col2.

    The expected output will not include a matching between these, as
    col2 is strongly connected to row3.
    """

    def setUp(self):
        self.G = nx.Graph()

        score = 0.9

        self.G.add_edge('row0', 'col0', weight=score, capacity=1.0)
        self.G.add_edge('row1', 'col1', weight=score, capacity=1.0)
        self.G.add_edge('row1', 'col2', weight=score / 3, capacity=1.0)
        self.G.add_node('row2')
        self.G.add_edge('row3', 'col2', weight=score, capacity=1.0)

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

    @unittest.expectedFailure
    def test_greedy_badorder(self):
        #sparse_similarity_matrix = convert_graph_to_sparse(self.G)
        sparse_similarity_matrix = [[0, 0.9, 0], [1, 0.3, 2], [3, 0.9, 2], [1, 0.9, 1]]
        mapping = greedy_solver(sparse_similarity_matrix)
        self.assertDictEqual(self.expected_map, mapping)

    def test_greedy_presorted(self):
        #sparse_similarity_matrix = convert_graph_to_sparse(self.G)
        sparse_similarity_matrix = [[0, 0.9, 0], [3, 0.9, 2], [1, 0.9, 1], [1, 0.3, 2]]
        mapping = greedy_solver(sparse_similarity_matrix)
        self.assertDictEqual(self.expected_map, mapping)


class TestNetworkGreedyHard1(unittest.TestCase):
    """Tests network matching on following graph:

    [A]  ---- 0.9  [1]
    [A]  ---- 0.8  [2]

    [B]  ---- 0.9  [3]

    [C]  ---- 0.9  [1]

    The network methods should succeed, and if the greedy algorithm is too naive it might
    fail.

    Correct mapping is:

        {a: 2, b: 3, c: 1}
    """

    def setUp(self):
        self.G = nx.Graph()

        self.G.add_edge('row0', 'col0', weight=0.9, capacity=1.0)
        self.G.add_edge('row0', 'col1', weight=0.8, capacity=1.0)
        self.G.add_edge('row1', 'col2', weight=0.9, capacity=1.0)
        self.G.add_edge('row2', 'col0', weight=0.9, capacity=1.0)

        self.expected_map = {
            0: 1,
            1: 2,
            2: 0
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

    def test_greedy_presorted(self):
        #sparse_similarity_matrix = convert_graph_to_sparse(self.G)
        sparse_similarity_matrix = [[2, 0.9, 0], [1, 0.9, 2], [0, 0.9, 0], [0, 0.8, 1]]
        mapping = greedy_solver(sparse_similarity_matrix)

        self.assertDictEqual(self.expected_map, mapping)


    @unittest.expectedFailure
    def test_greedy_unsorted(self):
        sparse_similarity_matrix = [[0, 0.9, 0], [0, 0.8, 1], [1, 0.9, 2], [2, 0.9, 0]]
        mapping = greedy_solver(sparse_similarity_matrix)

        self.assertDictEqual(self.expected_map, mapping)


class TestNetworkGreedyHard2(unittest.TestCase):
    """Tests network matching on following graph:

    [A]  ---- 0.9  [1]
    [A]  ---- 0.0  [2]

    [B]  ---- 0.9  [3]

    [C]  ---- 0.8  [1]

    The network methods should succeed, and if the greedy algorithm is too naive it might
    fail.

    Correct mapping is:

        {a: 2, b: 3, c: 1}
    """

    def setUp(self):
        self.G = nx.Graph()

        self.G.add_edge('row0', 'col0', weight=0.9, capacity=1.0)
        self.G.add_edge('row0', 'col1', weight=0.9, capacity=1.0)
        self.G.add_edge('row1', 'col2', weight=0.9, capacity=1.0)
        self.G.add_edge('row2', 'col0', weight=0.8, capacity=1.0)

        self.expected_map = {
            0: 1,
            1: 2,
            2: 0
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

    @unittest.expectedFailure
    def test_greedy(self):
        # This will pass if the sparse similarity matrix is in a particular order
        #sparse_similarity_matrix = convert_graph_to_sparse(self.G)
        sparse_similarity_matrix = [[0, 0.9, 0], [0, 0.9, 1], [1, 0.9, 2], [2, 0.8, 0]]

        mapping = greedy_solver(sparse_similarity_matrix)
        self.assertDictEqual(self.expected_map, mapping)


if __name__ == "__main__":
    unittest.main()
