"""
Solves pairwise matches for the entire network at once.

Given a sparse, weighted, bipartite graph determine the matching.
"""

import logging
import networkx as nx
from networkx.algorithms import bipartite

log = logging.getLogger('anonlink.networkflow')


def calculate_network(similarity, cutoff):
    """Given an adjacency matrix of edge weights, apply a
    threshold to the connections and construct a graph.

    :param similarity: The list of tuples including n-gram similarity scores
    :param cutoff: The threshold for including a connection
    :return: The resulting networkx graph.
    """
    G = nx.DiGraph()
    logging.debug('Applying threshold to network')
    for (idx1, score, idx2) in similarity:
        if score > cutoff:
            G.add_edge('row'+str(idx1), 'col'+str(idx2), weight=score, capacity=1.0)

    return G


def _to_int_map(network, find_pair):
    """Given a dictionary of edges {'rowN': 'colM', ...}, and a
    function to find the mate node.
    Return a dictionary of {N: M, ...}
    """
    entityMap = {}
    for node in network:
        if node.startswith("row") and len(network[node]):
            paired_node = find_pair(network, node)
            if paired_node is not None:
                entityMap[int(node[3:])] = int(paired_node[3:])
    return entityMap


def calculate_entity_mapping(G, method=None):
    """Given the networkx graph, calculate a dictionary mapping
    each row node to the most highly similar column node.

    :param G: A `networkx.Graph` comprising of nodes from two entities,
    connected by equally weighted edges if the similarity was above a
    threshold.

    :param method: The method to use to solve the entity mapping.
    Options are
        - 'flow' or None (default) - `networkx.maximum_flow` method.
        - 'bipartite' - the `networkx.bipartite.maximum_matching` algorithm (fastest)
        - 'weighted' - the `networkx.max_weight_matching` (slowest but most accurate
          with close matches)

    :return: A dictionary mapping of row index to column index. If no mate
    is found, the node isn't included.
    """

    if method == 'bipartite':
        log.info('Solving entity matches with bipartite maximum matching solver')
        network = bipartite.maximum_matching(G)
        entity_map = _to_int_map(network, lambda network, node: network[node])

    elif method == 'weighted':
        log.info('Solving entity matches with networkx maximum weight matching solver')
        network = nx.max_weight_matching(G)
        entity_map = _to_int_map(network, lambda network, node: network[node])

    elif method == 'flow' or method is None:
        log.info('Solving entity matches with networkx maximum flow solver')
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
            log.info('Matching not perfect - {:.3f}'.format(flow_value))
        else:
            log.info('Matching complete. (perfect matching)')

        def find_pair(network, node):
            # Make sure to deal with unconnected nodes

            possible_nodes = [n for n in network[node] if n != 'start']
            if len(possible_nodes) > 0:
                def get_score(node_name):
                    return network[node][node_name]
                return max(possible_nodes, key=get_score)
            else:
                return None

        entity_map = _to_int_map(network, find_pair)

    else:
        raise NotImplementedError("Haven't implemented that matching method")

    return entity_map


def map_entities(weights, threshold=0.8, method=None):
    """Calculate a dictionary mapping using similarity scores.

    :param weights: The list of tuples including n-gram similarity scores
    :param threshold: The threshold for including a connection
    :param method: The method to use to solve the entity mapping.
    Options are
        - 'flow' or None (default for datasets under 100K records) - `networkx.maximum_flow` method.
        - 'bipartite' - the `networkx.bipartite.maximum_matching` algorithm
        - 'weighted' - the `networkx.max_weight_matching` (slowest but most accurate
          with close matches)
    """

    network = calculate_network(weights, threshold)
    return calculate_entity_mapping(network, method)


if __name__ == "__main__":
    import numpy as np
    A = [[4.0, 3.0, 2.0, 1.0],
         [1.0, 4.0, 3.0, 2.0],
         [2.0, 1.0, 4.0, 3.0],
         [2.5, 3.5, 4.5, 1.5]]

    print("Threshold | Match | Entity Mapping")
    for threshold in np.linspace(2.5, 3.5, 11):
        entity_map = map_entities(A, threshold)
        perfect_match = len(entity_map) == len(A)
        print("{:9.3f} | {:5} | {:26s} ".format(threshold, perfect_match, entity_map))
