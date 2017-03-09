# -*- coding: utf-8 -*-
# !/bin/env python

import logging

from Driver import Driver
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
        super(GPSGraph, self).__init__(name=name, data=None, **attr)
        # drivers
        """
        set of drivers
        """
        self.__drivers = {}

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
        super(Graph, self).add_edge(u, v, distance=distance, lanes=lanes, attr_dict=props, **attr)

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

    def has_driver(self, start, end):
        """
        return True if graph contains at least one driver from start to end

        :param start: source node
        :param end: target node

        :return: boolean
        """
        return self.has_node(start) and self.has_node(end) and self.__drivers.get(start, {}).get(end) is not None

    def has_starting_time(self, start, end, starting_time):
        """
        returns True if there exists at least one driver from start to end with the given starting time

        :param start: source node
        :param end: target node
        :param starting_time: starting time
        :type starting_time: int

        :return: boolean
        """
        return self.has_driver(start, end) and self.__drivers[start][end].get(starting_time) is not None

    def add_driver(self, start, end, starting_time=0, nb=1, force=False):
        """
        add `nb` drivers starting at `start` and ending at `end` with starting tim `starting_time`

        :param start: source node
        :param end: target node

        * options:

            * ``starting_time=0``: starting time for the driver
            * ``nb=1``: number of drivers to add
        """
        if force or self.has_node(start) and self.has_node(end):
            if isinstance(nb, int) and nb > 0:
                self.__drivers.setdefault(start, {})
                self.__drivers[start].setdefault(end, {})
                self.__drivers[start][end].setdefault(starting_time, {})
                self.__drivers[start][end][starting_time].setdefault('nb', 0)
                self.__drivers[start][end][starting_time]['nb'] += nb
                log.info("Driver from %s to %s added to graph %s", start, end, self.name)
                return True
            else:
                log.warning("Impossible to add either non-int number of drivers or 0 driver. nb=%s" % nb)
        log.warning("Node %s or %s doesn't exist in graph %s", start, end, self.name)
        return False

    def set_drivers_property(self, start, end, prop, value, starting_time=None):
        """
        set properties to the given drivers and returns True if successful, else returns False

        :param start: source node
        :param end: target node
        :param prop: property keyword
        :param value: property value

        * options:

            * ``starting_time=None``: if integer we add the given property only to drivers starting at `starting_time`,
                                      else we add it to every drivers (only from `start` to `end`)
        """
        if self.has_driver(start, end):
            if starting_time is not None:
                if self.has_starting_time(start, end, starting_time):
                    self.__drivers[start][end][starting_time][prop] = value
                    return True
                log.warning("Drivers from node %s to node %s doesn't start at %s in graph %s",
                            start, end, starting_time, self.name)
                return False
            self.__drivers[start][end][prop] = value
            return True
        log.warning('No drivers from node %s to node %s in graph %s', start, end, self.name)
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
        if self.has_driver(start, end):
            if starting_time is not None:
                if self.has_starting_time(start, end, starting_time):
                    return self.__drivers[start][end][starting_time]['nb']
                log.warning("Drivers from node %s to node %s doesn't start at %s in graph %s",
                            start, end, starting_time, self.name)
                return 0
            else:
                return self.__drivers[start][end]
        log.warning('No drivers from node %s to node %s in graph %s', start, end, self.name)
        return 0

    def get_drivers_property(self, start, end, prop, starting_time=None):
        """
        return the wanted property about the given driver

        :param start: source node
        :param end: target node
        :param prop: property to return (keyword)

        * options:

            * ``starting_time=None``: if not None, return the wanted property considering only the drivers starting at
                                      `starting_time`, else considering every drivers

        :return: the wanted property
        """
        if self.has_driver(start, end):
            if starting_time is not None:
                if self.has_starting_time(start, end, starting_time):
                    return self.__drivers[start][end][starting_time].get(prop)
                log.warning("Drivers from node %s to node %s doesn't start at %s in graph %s",
                            start, end, starting_time, self.name)
                return None
            return self.__drivers[start][end].get(prop)
        log.warning('No drivers from node %s to node %s in graph %s', start, end, self.name)
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
        for start, dct in self.__drivers.iteritems():
            for end, d in dct.iteritems():
                for time, props in d.iteritems():
                    yield start, end, time, props['nb']

    def get_all_unique_drivers(self):
        """
        return the drivers making them unique if they are more than one for same starting, ending nodes and
        starting time.

        :return: list of :class:``Driver <Driver.Driver>``
        """
        for start, dct in self.__drivers.iteritems():
            for end, d in dct.iteritems():
                for time, props in d.iteritems():
                    for _ in range(props['nb']):
                        yield Driver(start, end, time)

    def get_all_drivers_from_starting_node(self, start):
        """
        Iterate every drivers starting at node `start`. A yielded driver is (start, end, starting_time, nb).

        :param start: source node

        :return: iterator
        """
        for end, dct in self.__drivers.get(start, {}).iteritems():
            for time, props in dct.iteritems():
                yield start, end, time, props['nb']

    def get_all_drivers_to_ending_node(self, end):
        """
        Iterate every drivers ending at node `end`. A yielded driver is (start, end, starting_time, nb).

        :param end: target node

        :return: iterator
        """
        for start, dct in self.__drivers.iteritems():
            for e, d in dct.iteritems():
                if e == end:
                    for time, props in d.iteritems():
                        yield start, end, time, props['nb']

    def remove_driver(self, start, end, starting_time, nb=1):
        """
        Remove `nb` drivers starting at `start`, ending at `end` and starting at `starting_time`.

        :param start: source node
        :param end: target node
        :param starting_time: starting time

        * options:

            * ``nb=1``: number of drivers to delete

        :return: a boolean
        """
        if self.has_starting_time(start, end, starting_time):
            self.__drivers[start][end][starting_time]['nb'] -= nb
            if self.__drivers[start][end][starting_time]['nb'] <= 0:
                del self.__drivers[start][end][starting_time]
            if not self.__drivers[start][end]:
                del self.__drivers[start][end]
            if not self.__drivers[start]:
                del self.__drivers[start]
            log.info("driver removed from %s to %s with starting time %s in graph %s",
                     start, end, starting_time, self.name)
            return True
        log.warning("No driver from %s to %s with starting time %s in graph %s", start, end, starting_time, self.name)
        return False

    def number_of_drivers(self):
        """
        Returns the number of drivers in graph

        :return: int
        """
        res = 0
        for _, _, _, nb in self.get_all_drivers():
            res += nb
        return res

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
