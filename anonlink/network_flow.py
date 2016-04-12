import logging
import networkx as nx
from networkx.algorithms import bipartite

logging.basicConfig(level=logging.WARNING)


def calculate_network(similarity, cutoff):
    """Given a adjacency matrix of edge weights, apply a
    threshold to the connections and construct a graph.

    :param similarity: The tuple including n-gram similarity scores
    :param cutoff: The threshold for including a connection
    :return: The resulting networkx graph.
    """
    G = nx.DiGraph()
    for (idx1, score, orig1, orig2, idx2) in similarity:

        if score > cutoff:
            logging.debug('adding ({}, {})'.format(idx1, idx2))
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
        - None (default) - `networkx.maximum_flow` method.
        - 'bipartite' - the `networkx.bipartite.maximum_matching` algorithm (fastest)
        - 'weighted' - the `networkx.max_weight_matching` (slowest but most accurate
          with close matches)

    :return: A dictionary mapping of row index to column index. If no mate
    is found, the node isn't included.
    """

    if method == 'bipartite':
        network = bipartite.maximum_matching(G)
        entity_map = _to_int_map(network, lambda network, node: network[node])

    elif method == 'weighted':
        network = nx.max_weight_matching(G)
        entity_map = _to_int_map(network, lambda network, node: network[node])

    elif method is None:
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

        entity_map = _to_int_map(network, lambda network, node: max(network[node], key=network[node].get))

    else:
        raise NotImplementedError("Haven't implemented that matching method")

    return entity_map


def map_entities(weights, threshold=0.8, method=None):
    network = calculate_network(weights, threshold)
    return calculate_entity_mapping(network, method)


def solve_entity_mapping(weights, method=None):
    """use a binary search tree to find the largest
    threshold that will give a perfect match"""

    # all_weights = np.array(weights).flatten()
    # min_weight, max_weight, mean_weight = all_weights.min(), all_weights.max(), all_weights.mean()
    #
    # threshold = mean_weight

    # TODO binary search...
    entity_map = map_entities(A, threshold)
    raise NotImplementedError("TODO binary search here")


if __name__ == "__main__":
    A = [[4.0, 3.0, 2.0, 1.0],
         [1.0, 4.0, 3.0, 2.0],
         [2.0, 1.0, 4.0, 3.0],
         [2.5, 3.5, 4.5, 1.5]]

    print "Threshold | Match | Entity Mapping"
    for threshold in np.linspace(2.5, 3.5, 11):
        entity_map = map_entities(A, threshold)
        perfect_match = len(entity_map) == len(A)
        print "{:9.3f} | {:5} | {:26s} ".format(threshold, perfect_match, entity_map)

    solve_entity_mapping(A)