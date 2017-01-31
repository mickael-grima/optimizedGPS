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

    def __init__(self, name='graph'):
        super(GPSGraph, self).__init__(name=name)
        # drivers
        self.__drivers = {}

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

    def has_driver(self, start, end):
        """ return True if graph contains at least one driver from start to end
        """
        return self.has_node(start) and self.has_node(end) and self.__drivers.get(start, {}).get(end) is not None

    def has_starting_time(self, start, end, starting_time):
        """ returns True if there exists at least one driver from start to end with the given starting time
        """
        return self.has_driver(start, end) and self.__drivers[start][end].get(starting_time) is not None

    def add_driver(self, start, end, starting_time=0, nb=1):
        """ add nb drivers with the given properties
        """
        if self.has_node(start) and self.has_node(end):
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
        """ set properties to the given drivers and returns True if driver exists
            else return False

            if starting_time == None, add a property to every drivers from start to end
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
        """ return the drivers from start to end, and with the given starting_time if not None
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
        for start, dct in self.__drivers.iteritems():
            for end, d in dct.iteritems():
                for time, props in d.iteritems():
                    yield start, end, time, props['nb']

    def get_all_unique_drivers(self):
        """ return the drivers making them unique if more than one for same starting, ending nodes and starting time
        """
        for start, dct in self.__drivers.iteritems():
            for end, d in dct.iteritems():
                for time, props in d.iteritems():
                    for _ in range(props['nb']):
                        yield Driver(start, end, time)

    def get_all_drivers_from_starting_node(self, start):
        for end, dct in self.__drivers.get(start, {}).iteritems():
            for time, props in dct.iteritems():
                yield start, end, time, props['nb']

    def get_all_drivers_to_ending_node(self, end):
        for start, dct in self.__drivers.iteritems():
            for e, d in dct.iteritems():
                if e == end:
                    for time, props in d.iteritems():
                        yield start, end, time, props['nb']

    def remove_driver(self, start, end, starting_time, nb=1):
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
        res = 0
        for _, _, _, nb in self.get_all_drivers():
            res += nb
        return res

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------
