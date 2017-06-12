# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from collections import defaultdict

from Graph import Graph
from constants import constants
from optimizedGPS import labels
from utils.tools import congestion_function

__all__ = ["GPSGraph"]

log = logging.getLogger(__name__)


class GPSGraph(Graph):
    """
    This class allows to add drivers on the graph
    It inherits from :class:``Graph <optimizedGPS.Graph>``, and contains the drivers

    drivers are stored as a tuple (starting node, ending node, starting time) to which we associate a number
    which represents how many drivers we have
    """
    PROPERTIES = Graph.PROPERTIES
    PROPERTIES['edges'].update({
        labels.TRAFFIC_LIMIT: constants[labels.TRAFFIC_LIMIT],
        labels.MAX_SPEED: constants[labels.MAX_SPEED]
    })

    def __init__(self, name='graph', data=None, **attr):
        super(GPSGraph, self).__init__(name=name, data=data, **attr)
        """
        set of drivers
        """
        self.__drivers = defaultdict(lambda: defaultdict())

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- EDGES -----------------------------------------------
    # ----------------------------------------------------------------------------------------

    def add_edge(self, u, v, distance=None, lanes=None, traffic_limit=None, max_speed=None, attr_dict=None,
                 **attr):
        """
        Call the super-method :func:``add_node <Graph.add_node>`` with some more parameters.

        :param u: source node
        :param v: target node

        * options:

            * ``distance=None``: distance of the added edge. If None, we add the default value.
            * ``lanes=None``: number of lanes of the added edge. If None, we add the default value.
            * ``traffic_limit=None``: maximal traffic before the beginning of a congestion.
                                      If None, we add the default value.
            * ``max_speed=None``: max speed allowed. If None, we add the default value.
            * ``attr_dict=None``: Other attributes to add.
            * ``**attr``: Other attributes to add.
        """
        props = {
            # labels.TRAFFIC_LIMIT: self.compute_traffic_limit(u, v),
            labels.TRAFFIC_LIMIT: self.PROPERTIES['edges'][labels.TRAFFIC_LIMIT],
            labels.MAX_SPEED: self.PROPERTIES['edges'][labels.MAX_SPEED]
        }
        if attr_dict is not None:
            props.update(attr_dict)
        props[labels.TRAFFIC_LIMIT] = traffic_limit if traffic_limit is not None else props[labels.TRAFFIC_LIMIT]
        props[labels.MAX_SPEED] = max_speed if max_speed is not None else props[labels.MAX_SPEED]
        super(GPSGraph, self).add_edge(u, v, distance=distance, lanes=lanes, attr_dict=props, **attr)

    def compute_traffic_limit(self, source, target, **data):
        """
        Considering the length of the edge (see :func:``get_edge_length <Graph.get_edge_length>``) and
        the number of lanes we return the limit traffic which represents a limit before a congestion traffic
        appears on it.

        :param source: node source
        :param target: node target
        :param data: some data about the edges. As a dictionary
        :return: an integer representing the limit traffic on the given edge
        """
        length = self.get_edge_length(source, target)
        return float(length) / constants[labels.CAR_LENGTH] * data.get(constants[labels.LANES], 1)

    def get_congestion_function(self, source, target):
        """
        return the congestion function concerning the edge (`source`, `target`).
        See also :func:``congestion_function <utils.tools.congestion_function>``

        :param source: source node
        :param target: target node

        :return: func
        """
        if self.has_edge(source, target):
            congestion = self.get_edge_property(source, target, labels.CONGESTION_FUNC)
            return congestion or congestion_function(**self.get_edge_data(source, target))

    def set_congestion_function(self, source, target, congestion_func):
        """
        Set given congestion function to edge

        :param source: source node
        :param target: target node
        :param congestion_func: function taking traffic as argument
        :return:
        """
        if self.has_edge(source, target):
            self.set_edge_property(source, target, labels.CONGESTION_FUNC, congestion_func)

    def set_global_congestion_function(self, congestion_func):
        """
        Set the given congestion function to every edges

        :param congestion_func: function taking traffic as argument
        :return:
        """
        for source, target in self.edges_iter():
            self.set_congestion_function(source, target, congestion_func)

    def get_minimum_waiting_time(self, source, target):
        """
        Computes and returns the time needed to cross the edge without traffic.

        :param source: source node
        :param target: target node

        :return: integer
        """
        if self.has_edge(source, target):
            return self.get_congestion_function(source, target)(0)

    def get_traffic_limit(self, source, target):
        """
        Computes and returns the traffic limit: the traffic after which we observe a congestion.

        :param source: source node
        :param target: target node

        :return: int
        """
        return self.get_edge_property(source, target, labels.TRAFFIC_LIMIT)

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- DRIVERS ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def get_shortest_path_through_edge(self, driver, edge, edge_property=labels.DISTANCE, key=None):
        """
        compute the shortest path for driver containing edge.
        If edge is unreachable for driver, we return None.

        :param driver:
        :param edge:
        :param edge_property: value on edge to consider for computing the shortest path
        :param key:
        :return: path (tuple of nodes)
        """
        try:
            if edge[0] == driver.start:
                path = (edge[0],)
            else:
                path = self.get_shortest_path(driver.start, edge[0], edge_property=edge_property, key=key)
            if edge[1] == driver.end:
                path += (edge[1],)
            else:
                path += self.get_shortest_path(edge[1], driver.end, edge_property=edge_property, key=key)
            return path
        except StopIteration:  # Not path reaching edge
            return None

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def belong_to_same_road(self, u0, v0, u1, v1):
        """
        We check the number of lanes, the name, the max_speed and the traffic limit of both edges.
        If It is the same, we return True

        :return: boolean
        """
        params0 = self.get_edge_data(u0, v0)
        params1 = self.get_edge_data(u1, v1)
        if super(GPSGraph, self).belong_to_same_road(u0, v0, u1, v1) \
                and params0[labels.MAX_SPEED] == params1[labels.MAX_SPEED] \
                and params0[labels.TRAFFIC_LIMIT] == params1[labels.MAX_SPEED]:
            return True
        return False

    def get_shortest_path_with_traffic(self, start, end, time, traffic_history):
        """
        Then considering the traffic_history we compute the fastest path from start to end starting at time

        :param start: starting node
        :param end: ending node
        :param time: starting time
        :param traffic_history: for each edge, we associate a dictionnary of time, traffic.
        :return: the traffic history of this shortest path, as if a driver would have driven on it
        """
        if not self.has_node(start):
            log.error("Node %s not in graph %s", start, self.name)
            raise KeyError("Node %s not in graph %s" % (start, self.name))
        # paths: to each node we associate path used to rech this node
        # each path is a tuple of (node, current_time)
        paths = {start: {((start, time),)}}

        # Set the time for the start node to zero
        next_nodes = {time: {start}}
        times = [time]

        # Unvisited nodes
        visited = set()
        current = None

        while len(times) > 0 and current != end:
            # Pops a vertex with the smallest distance
            t = times[0]
            current = next_nodes[t].pop()

            # remove nodes from nexts and distances
            if len(next_nodes[t]) == 0:
                del next_nodes[t]
                del times[0]

            # Check if already visited
            if current in visited:
                continue
            visited.add(current)

            for n in self.successors(current):
                # get traffic at t
                current_traffic = 0
                for i in sorted(traffic_history.get((current, n), {}).keys()):
                    if i >= t:
                        break
                    current_traffic = traffic_history[current, n][i]

                # compute new time
                new_time = t + self.get_congestion_function(current, n)(current_traffic)

                # add new node in next_nodes
                next_nodes.setdefault(new_time, set())
                next_nodes[new_time].add(n)

                # add new time in the sorted list times
                i = 0
                while i < len(times):
                    if times[i] == new_time:
                        i = -1
                        break
                    elif times[i] > new_time:
                        break
                    i += 1
                if i >= 0:
                    times.insert(i, new_time)

                # update paths
                paths.setdefault(n, set())
                for path in paths[current]:
                    if path[-1][1] == t:
                        paths[n].add(path + ((n, new_time),))

        return min(paths[end], key=lambda p: p[-1][1])

    def get_lowest_driving_time(self, driver):
        """
        Compute the minimum driving time on graph for driver
        """
        path = self.get_shortest_path(driver.start, driver.end, key=self.get_minimum_waiting_time)
        return sum(map(lambda e: self.get_minimum_waiting_time(*e), self.iter_edges_in_path(path)))

    def get_lowest_driving_time_with_traffic(self, driver, traffic):
        """
        Compute the minimum driving time on graph for driver with traffic
        """
        driver_history = self.get_shortest_path_with_traffic(driver.start, driver.end, driver.time, traffic)
        return driver_history[-1][1] - driver_history[0][1]

    @classmethod
    def enrich_traffic_with_driver_history(cls, traffic, driver_history):
        """
        Add the driver's history into the traffic
        """
        for i in range(len(driver_history) - 1):
            node, t = driver_history[i]
            nxt, t_nxt = driver_history[i + 1]
            traffic[node, nxt][t] += 1
            traffic[node, nxt][t_nxt] = max(traffic[node, nxt][t_nxt] - 1, 0)
