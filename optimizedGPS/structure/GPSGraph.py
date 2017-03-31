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
    """ This class contains every instances and methods describing a Graph for our problem
        It inherits from Graph, and contains the drivers

        drivers are stored as a tuple (starting node, ending node, starting time) to which we associate a number
        which represents how many drivers for these informations we have
    """
    PROPERTIES = Graph.PROPERTIES
    PROPERTIES['edges'].update({
        labels.TRAFFIC_LIMIT: constants[labels.TRAFFIC_LIMIT],
        labels.MAX_SPEED: constants[labels.MAX_SPEED]
    })

    def __init__(self, name='graph', data=None, **attr):
        super(GPSGraph, self).__init__(name=name, data=data, **attr)
        # drivers
        self.__drivers = defaultdict(lambda: defaultdict())

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- EDGES -----------------------------------------------
    # ----------------------------------------------------------------------------------------

    def add_edge(self, u, v, distance=None, lanes=None, traffic_limit=None, max_speed=None, attr_dict=None,
                 **attr):
        props = {
            labels.TRAFFIC_LIMIT: self.compute_traffic_limit(u, v),
            labels.MAX_SPEED: self.PROPERTIES['edges'][labels.MAX_SPEED]
        }
        if attr_dict is not None:
            props.update(attr_dict)
        props[labels.TRAFFIC_LIMIT] = traffic_limit if traffic_limit is not None else props[labels.TRAFFIC_LIMIT]
        props[labels.MAX_SPEED] = max_speed if max_speed is not None else props[labels.MAX_SPEED]
        super(Graph, self).add_edge(u, v, distance=distance, lanes=lanes, attr_dict=props, **attr)

    def compute_traffic_limit(self, source, target, **data):
        """
        Considering the the length of the edge (see Graph.get_edge_length) and the number of lanes
        we return the limit traffic which represents a limit before a congestion traffic appears on it

        :param source: node source
        :param target: node target
        :param data: some data about the edges. As a dictionary
        :return: an integer representing the limit traffic on the given edge
        """
        length = self.get_edge_length(source, target)
        return float(length) / constants[labels.CAR_LENGTH] * data.get(constants[labels.LANES], 1)

    def get_congestion_function(self, source, target):
        if self.has_edge(source, target):
            return congestion_function(**self.get_edge_data(source, target))

    def get_minimum_waiting_time(self, source, target):
        if self.has_edge(source, target):
            return congestion_function(**self.get_edge_data(source, target))(0)

    def get_traffic_limit(self, source, target):
        return self.get_edge_property(source, target, labels.TRAFFIC_LIMIT)

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- DRIVERS ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def has_driver(self, driver):
        """ return True if graph contains at least one driver from start to end
        """
        return driver in self.__drivers

    def add_driver(self, driver, force=False):
        """ add nb drivers with the given properties
        """
        if force or self.has_node(driver.start) and self.has_node(driver.end):
            self.__drivers[driver] = {}
            return True
        log.warning("Node %s or %s doesn't exist in graph %s", driver.start, driver.end, self.name)
        return False

    def set_drivers_property(self, driver, prop, value):
        """ set properties to the given drivers and returns True if driver exists
            else return False

            if starting_time == None, add a property to every drivers from start to end
        """
        if self.has_driver(driver):
            self.__drivers[driver][prop] = value
            return True
        log.warning('Driver %s doesn\'t exist in graph %s', driver, self.name)
        return False

    def get_drivers(self, start, end, starting_time=None):
        """ return the drivers from start to end, and with the given starting_time if not None
        """
        for driver in self.__drivers:
            if driver.start == start and driver.end == end and (starting_time is None or driver.time == starting_time):
                yield driver

    def get_drivers_property(self, driver, prop):
        if self.has_driver(driver):
            return self.__drivers[driver].get(prop)
        log.warning('Driver %s doesn\'t exist in graph %s', driver, self.name)
        return None

    def get_all_drivers(self):
        for driver in self.__drivers:
            yield driver

    def get_all_drivers_from_starting_node(self, start):
        for driver in self.__drivers:
            if driver.start == start:
                yield driver

    def get_all_drivers_to_ending_node(self, end):
        for driver in self.__drivers:
            if driver.end == end:
                yield driver

    def remove_driver(self, driver):
        if self.has_driver(driver):
            del self.__drivers[driver]
            return True
        log.warning('Driver %s doesn\'t exist in graph %s', driver, self.name)
        return False

    def number_of_drivers(self):
        return len(self.__drivers)

    def get_time_ordered_drivers(self):
        """
        Return a list of drivers sorted by starting time

        :return: list
        """
        return sorted(self.get_all_drivers(), key=lambda d: d.time)

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
