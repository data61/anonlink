import logging
import networkx as nx
import numpy as np

logging.basicConfig(level=logging.WARNING)


def calculate_network(similarity_matrix, cutoff):
    """Given a matrix of edge weights, construct a networkx digraph
    and solve the maximum flow problem.

    :param similarity_matrix: The n-gram similarity scores
    :param cutoff: The threshold for including a connection
    :return: The resulting optimized network.
    """
    G = nx.DiGraph()
    for i, row in enumerate(similarity_matrix):

        G.add_edge('start', 'row'+str(i), capacity=1.0)
        G.add_edge('col'+str(i), 'end', capacity=1.0)

        for j, e in enumerate(row):
            if e > cutoff:
                logging.debug('adding ({}, {})'.format(i, j))
                G.add_edge('row'+str(i), 'col'+str(j), capacity=e)

    flow_value, network = nx.maximum_flow(G, 'start', 'end')

    if flow_value < len(similarity_matrix):
        logging.info('Matching not perfect - {:.3f}'.format(flow_value))
    else:
        logging.info('Matching complete. (perfect matching)')

    return flow_value, network


def calculate_entity_mapping(network):
    """Given the dictionary containing the value of the flow that went through
    each edge, calculate a dictionary mapping each row node to the most connected
    column node.

    :param network: As output from `networkx.maximum_flow`
    :return: A dictionary mapping of row index to column index.
    """
    entityMap = {}
    for node in network:
        if node.startswith("row") and len(network[node]):
            paired_node = max(network[node], key=network[node].get)
            entityMap[int(node[3:])] = int(paired_node[3:])
    return entityMap


def map_entities(weights, threshold=0.8):
    flow_value, network = calculate_network(weights, threshold)
    return flow_value, calculate_entity_mapping(network)


if __name__ == "__main__":
    A = [[4.0, 3.0, 2.0, 1.0],
         [1.0, 4.0, 3.0, 2.0],
         [2.0, 1.0, 4.0, 3.0],
         [2.5, 3.5, 4.5, 1.5]]

    # TODO Could use a binary search tree to find the largest
    # threshold that will give a perfect match
    print "Threshold |   Flow | Mapping"
    for threshold in np.linspace(0, 3, 12):
        flow_value, entity_map = map_entities(A, threshold)
        print "{:9.3f} | {:6.2f} | {}".format(threshold, flow_value, entity_map)
