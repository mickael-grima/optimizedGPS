"""
Class to create Time Expanded Graphs from a given graph
"""

from GPSGraph import GPSGraph


class TimeExpandedGraph(object):
    @classmethod
    def get_node_level(cls, node):
        """
        Extract the node's level (see get_time_node_name)

        :return: integer
        """
        return int(node.split(':')[-1])

    @classmethod
    def get_time_node_name(cls, node, time):
        """
        New timenode's name

        :param node: node
        :param time: timeslot
        :return: String
        """
        return "%s:%s" % (str(node), time)

    @classmethod
    def get_edge(cls, edge, i ,j):
        """
        Return the corresponding edge in TEG

        :param edge: edge in original graph
        :param i: timeslot for source node
        :param j: timeslot for target node
        :return:
        """
        return cls.get_time_node_name(edge[0], i), cls.get_time_node_name(edge[1], j)

    @classmethod
    def create_time_expanded_graph_from_linear_congestion(cls, graph, horizon):
        """
        We create a TEG considering a linear congestion function as following:
          - the set of nodes is a union of graph's nodes' sets (horizon time)
          - For each edge in graph, we build a new edge in the TEG from the starting node at every ending node to a
            greater level (i -> j where j > i)

        :param graph: GPSGraph object from which we want to create a TEG
        :param horizon: Number of level (time slots) in the new created TEG
        :return: A GPSGraph object
        """
        TEG = GPSGraph(name="TEG-%s" % graph.name, horizon=horizon)
        # We add the nodes
        for node in graph.nodes():
            for time in range(horizon):
                TEG.add_node(cls.get_time_node_name(node, time), **graph.node[node])

        # We add the edges
        for (source, target) in graph.edges():
            for time in range(horizon - 1):
                for t in range(time + 1, horizon):
                    TEG.add_edge(
                        cls.get_time_node_name(source, time),
                        cls.get_time_node_name(target, t),
                        graph.get_edge_data(source, target)
                    )

        return TEG


class ReducedTimeExpandedGraph(object):
    """
    This class represents a time expanded graph: given a graph, we provide methods to iterate the existing edges
    in the TEG given an edge.
    The main goal is to never build the TEG, this class only describe the TEG building what need when we call a
    specific method.
    """
    SEPARATOR = ":::"
    NODE_NAME_FORMAT = "%s" + SEPARATOR + "%s"

    def __init__(self, graph, horizon):
        """
        :param graph: Graph instance
        :param horizon: integer representing the number of layers
        """
        self.graph = graph
        self.horizon = horizon

    def number_of_layers(self):
        return self.horizon

    def build_node(self, node, layer):
        """
        build a node in the TEG from the orignal node belonging to the given layer.

        :param node: node from the original graph
        :param layer:
        :return:
        """
        return self.NODE_NAME_FORMAT % (str(node), layer)

    def get_node_layer(self, node):
        return int(node.split(self.SEPARATOR)[-1])

    def get_original_node(self, node):
        """
        Return the node from original graph from which we built the input node

        :param node: node in TEG
        :return: node in orignal Graph
        """
        return self.SEPARATOR.join(node.split(self.SEPARATOR)[:-1])

    def iter_nodes_from_node(self, node, layer=0):
        """
        Iterate every nodes in TEG built from node, starting at layer

        :param node: node from original graph
        :param layer: layer of built node
        """
        for i in xrange(layer, self.horizon + 1):
            yield self.build_node(node, i)

    def nodes_iter(self):
        """
        Iterate every nodes in TEG
        """
        for node in self.graph.nodes_iter():
            for n in self.iter_nodes_from_node(node):
                yield n

    def build_edge(self, edge, layer_source, layer_target):
        """
        Build an edge in the TEG.

        :param edge: edge in the original graph
        :param layer_source: layer for the source node
        :param layer_target: layer for the target node
        :return: tuple
        """
        return self.build_node(edge[0], layer_source), self.build_node(edge[1], layer_target)

    def get_original_edge(self, edge):
        """
        Return the edge in original graph from which we built the input edge

        :param edge: edge from TEG
        :return: tuple
        """
        return self.get_original_node(edge[0]), self.get_original_node(edge[1])

    def iter_edges_from_edge(self, source, target, layer=0):
        """
        Iterate the edges built from edge.
        We start from the given layer.
        """
        for s in self.iter_nodes_from_node(source, layer=layer):
            for t in self.iter_nodes_from_node(target, layer=self.get_node_layer(s) + 1):
                yield s, t

    def edges_iter(self):
        """
        Iterate the edges in the TEG.
        """
        for edge in self.graph.edges_iter():
            for e in self.iter_edges_from_edge(*edge):
                yield e

    def iter_original_edges(self):
        """
        Iterate edges in the original graph
        """
        for edge in self.graph.edges_iter():
            yield edge

    def predecessors_iter(self, node):
        """
        Iterate the predecessors of edge in the TEG

        :param node: Node in TEG
        """
        original_node = self.get_original_node(node)
        node_layer = self.get_node_layer(node)
        for n in self.graph.predecessors_iter(original_node):
            for l in xrange(0, node_layer):
                yield self.build_node(n, l)

    def successors_iter(self, node):
        """
        Iterate the successors of edge in the TEG

        :param node: Node in TEG
        """
        original_node = self.get_original_node(node)
        node_layer = self.get_node_layer(node)
        for n in self.graph.successors_iter(original_node):
            for l in xrange(node_layer + 1, self.horizon + 1):
                yield self.build_node(n, l)
