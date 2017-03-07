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

        # add drivers
        if isinstance(graph, GPSGraph):
            for start, end, time, nb in graph.get_all_drivers():
                TEG.add_driver(start, end, time, nb=nb, force=True)

        return TEG
