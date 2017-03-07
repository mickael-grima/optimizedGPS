"""
Class to create Time Expanded Graphs from a given graph
"""

from GPSGraph import GPSGraph


class TimeExpandedGraph(object):
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
    def create_time_expanded_graph_from_linear_congestion(cls, graph, horizon):
        """
        We create a TEG considering a linear congestion function as following:
          - the set of nodes is a union of graph's nodes' sets (horizon time)
          - For each edge in graph, we build a new edge in the TEG from the starting node at every ending node to a
            greater level (i -> j where j > i)

        :param graph: Graph object from which we want to create a TEG
        :param horizon: Number of level (time slots) in the new created TEG
        :return: A GPSGraph object
        """
        TEG = GPSGraph(name="TEG-%s" % graph.name)
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
