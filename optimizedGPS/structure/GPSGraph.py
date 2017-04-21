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

    **Example:**

    >>> from optimizedGPS import GPSGraph
    >>>
    >>> graph = GPSGraph(name='test')
    >>> graph.add_node('node0', 0, 1)
    >>> graph.add_node('node1', 1, 1)
    >>> graph.add_edge('node0', 'node1', 3, 2)
    >>>
    >>> graph.add_driver('node0', 'node1', 3)  # Add a driver starting at node 'node0', ending at node 'node1' and starting after 3 units of time
    >>>
    >>> n = graph.number_of_drivers()
    >>> print "number of drivers: %s" % n  #doctest: +NORMALIZE_WHITESPACE
    # number of drivers: 3 #
    >>> drivers = graph.get_all_drivers()
    >>> print str(drivers.next())  #doctest: +NORMALIZE_WHITESPACE
    # ('node0', 'node1', 3)
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
            labels.TRAFFIC_LIMIT: self.compute_traffic_limit(u, v),
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
            return congestion_function(**self.get_edge_data(source, target))

    def get_minimum_waiting_time(self, source, target):
        """
        Computes and returns the time needed to cross the edge without traffic.

        :param source: source node
        :param target: target node

        :return: integer
        """
        if self.has_edge(source, target):
            return congestion_function(**self.get_edge_data(source, target))(0)

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

    def has_driver(self, driver):
        """
        return True if graph contains at least one driver from start to end

        :param start: source node
        :param end: target node

        :return: boolean
        """
        return driver in self.__drivers

    def add_driver(self, driver, force=False):
        """
        add a driver.

        :param driver: Instance Driver

        * options:

            * ``force=False``: If True we add the driver even if the starting and ending node don't exist in graph
        """
        if force or self.has_node(driver.start) and self.has_node(driver.end):
            self.__drivers[driver] = {}
            return True
        log.warning("Node %s or %s doesn't exist in graph %s", driver.start, driver.end, self.name)
        return False

    def set_drivers_property(self, driver, prop, value):
        """
        set properties to the given drivers and returns True if successful, else returns False

        :param driver: object Driver
        :param prop: property keyword
        :param value: property value
        """
        if self.has_driver(driver):
            self.__drivers[driver][prop] = value
            return True
        log.warning('Driver %s doesn\'t exist in graph %s', driver, self.name)
        return False

    def get_drivers(self, start, end, starting_time=None):
        """
        return the drivers from start to end

        :param start: source node
        :param end: target node

        * options:

            * ``starting_time=None``: returns only drivers starting at `starting_time`

        :return: set of drivers
        """
        for driver in self.__drivers:
            if driver.start == start and driver.end == end and (starting_time is None or driver.time == starting_time):
                yield driver

    def get_drivers_property(self, driver, prop):
        """
        return the wanted property about the given driver

        :param driver: object driver
        :param prop: property to return
        :return: the wanted property
        """
        if self.has_driver(driver):
            return self.__drivers[driver].get(prop)
        log.warning('Driver %s doesn\'t exist in graph %s', driver, self.name)
        return None

    def get_all_drivers(self):
        """
        Iterate every drivers as tuple (start, end, starting_time, nb) where:
            - start is the source node
            - end is the target node
            - starting_time is the starting time
            - nb is the number of drivers

        :return: iterator
        """
        for driver in self.__drivers:
            yield driver

    def get_all_drivers_from_starting_node(self, start):
        """
        Iterate every drivers starting at node `start`. A yielded driver is (start, end, starting_time, nb).

        :param start: source node

        :return: iterator
        """
        for driver in self.__drivers:
            if driver.start == start:
                yield driver

    def get_all_drivers_to_ending_node(self, end):
        """
        Iterate every drivers ending at node `end`. A yielded driver is (start, end, starting_time, nb).

        :param end: target node

        :return: iterator
        """
        for driver in self.__drivers:
            if driver.end == end:
                yield driver

    def remove_driver(self, driver):
        """
        Remove given driver.

        :return: a boolean
        """
        if self.has_driver(driver):
            del self.__drivers[driver]
            return True
        log.warning('Driver %s doesn\'t exist in graph %s', driver, self.name)
        return False

    def number_of_drivers(self):
        """
        Returns the number of drivers in graph

        :return: int
        """
        return len(self.__drivers)

    def get_time_ordered_drivers(self):
        """
        Return a list of drivers sorted by starting time

        :return: list
        """
        return sorted(self.get_all_drivers(), key=lambda d: d.time)

    def get_shortest_path_through_edge(self, driver, edge, edge_property=labels.DISTANCE):
        """
        compute the shortest path for driver containing edge.
        If edge is unreachable for driver, we return None.

        :param driver:
        :param edge:
        :param edge_property: value on edge to consider for computing the shortest path
        :return: path (tuple of nodes)
        """
        try:
            if edge[0] == driver.start:
                path = (edge[0],)
            else:
                path = self.get_shortest_path(driver.start, edge[0], edge_property=edge_property)
            if edge[1] == driver.end:
                path += (edge[1],)
            else:
                path += self.get_shortest_path(edge[1], driver.end, edge_property=edge_property)
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

            for n in self.successors(current):
                # if visited, skip
                if n in visited:
                    continue

                # else add t in visited
                visited.add(n)

                # get traffic at t
                current_traffic = 0
                for i in sorted(traffic_history.get((current, n), {}).keys()):
                    if i > t:
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
