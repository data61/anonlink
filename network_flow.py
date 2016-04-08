import logging
import networkx as nx
from networkx.algorithms import bipartite
import numpy as np

logging.basicConfig(level=logging.WARNING)


def calculate_network(similarity_matrix, cutoff):
    """Given a adjacency matrix of edge weights, apply a
    threshold to the connections and construct a graph.

    and solve the maximum flow problem.

    :param similarity_matrix: The n-gram similarity scores
    :param cutoff: The threshold for including a connection
    :return: The resulting networkx graph.
    """
    G = nx.DiGraph()
    for i, row in enumerate(similarity_matrix):
        for j, e in enumerate(row):
            if e > cutoff:
                logging.debug('adding ({}, {})'.format(i, j))
                G.add_edge('row'+str(i), 'col'+str(j), weight=e, capacity=1.0)

    return G


def calculate_entity_mapping(G, altmethod=False):
    """Given the networkx graph, calculate a dictionary mapping
    each row node to the most connected column node.

    There are two possible methods for achieving this:

        nx.maximum_flow(G, 'start', 'end')
        nx.bipartite.maximum_matching(G)

    :param G: A `networkx.Graph` comprising of nodes from two entities,
    connected by equally weighted edges if the similarity was above a
    threshold.

    :return: A dictionary mapping of row index to column index. If no mate
    is found, the node isn't included.
    """

    def to_int_map(network, find_pair):
        """Given a dictionary of edges {'rowN': 'colM', ...}, and a
        function to find the mate node
        Return a dictionary of {N: M, ...}
        """
        entityMap = {}
        for node in network:
            if node.startswith("row") and len(network[node]):
                paired_node = find_pair(network, node)
                entityMap[int(node[3:])] = int(paired_node[3:])
        return entityMap

    if altmethod:
        network = nx.max_weight_matching(G)
        #network = bipartite.maximum_matching(G)
        entity_map = to_int_map(network, lambda network, node: network[node])

    else:
        # The maximum flow solver requires a SOURCE and SINK
        num_rows, num_cols = 0, 0
        for i, node in enumerate(G.nodes()):
            if node.startswith("row"):
                G.add_edge('start', node, capacity=1.0)
                num_rows += 1
            if node.startswith("col"):
                G.add_edge(node, 'end', capacity=1.0)
                num_cols += 1
        flow_value, network = nx.maximum_flow(G, 'start', 'end')

        # This method produces a quality metric `flow`, however
        # it needs to be compared to the number of entities
        if flow_value < num_rows:
            logging.info('Matching not perfect - {:.3f}'.format(flow_value))
        else:
            logging.info('Matching complete. (perfect matching)')

        entity_map = to_int_map(network, lambda network, node: max(network[node], key=network[node].get))

    return entity_map


def map_entities(weights, threshold=0.8, altmethod=False):
    network = calculate_network(weights, threshold)
    return calculate_entity_mapping(network, altmethod)


def solve_entity_mapping(weights, altmethod=False):
    """use a binary search tree to find the largest
    threshold that will give a perfect match"""

    all_weights = np.array(weights).flatten()
    min_weight, max_weight, mean_weight = all_weights.min(), all_weights.max(), all_weights.mean()

    threshold = mean_weight

    # TODO
    entity_map = map_entities(A, threshold, False)

if __name__ == "__main__":
    A = [[4.0, 3.0, 2.0, 1.0],
         [1.0, 4.0, 3.0, 2.0],
         [2.0, 1.0, 4.0, 3.0],
         [2.5, 3.5, 4.5, 1.5]]

    print "Threshold | Match | Entity Mapping"
    for threshold in np.linspace(2.5, 3.5, 11):
        entity_map = map_entities(A, threshold, True)
        perfect_match = len(entity_map) == len(A)
        print "{:9.3f} | {:5} | {:26s} ".format(threshold, perfect_match, entity_map)

    solve_entity_mapping(A, )