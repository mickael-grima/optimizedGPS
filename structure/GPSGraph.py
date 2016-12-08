# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from Graph import Graph
from Driver import Driver
from utils.tools import congestion_function

import options

log = logging.getLogger(__name__)


class GPSGraph(Graph):
    """ This class contains every instances and methods describing a Graph for our problem
        It inherits from Graph, and contains the drivers

        drivers are stored as a tuple (starting node, ending node, starting time) to which we associate a number
        which represents how many drivers for these informations we have
    """
    def __init__(self, name='graph'):
        super(GPSGraph, self).__init__(name=name)
        # drivers
        self.__drivers = {}

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- EDGES -----------------------------------------------
    # ----------------------------------------------------------------------------------------

    def add_edge(self, source, target, attr_dict=None, **attr):
        attr.setdefault(options.TRAFFIC_LIMIT, self.compute_traffic_limit(source, target))
        super(GPSGraph, self).add_edge(source, target, attr_dict, **attr)

    def compute_traffic_limit(self, source, target, **data):
        # TODO
        return 1

    def getCongestionFunction(self, source, target):
        if self.has_edge(source, target):
            return congestion_function(**self.get_edge_data(source, target))

    def getMinimumWaitingTime(self, source, target):
        if self.has_edge(source, target):
            return congestion_function(**self.get_edge_data(source, target))(0)

    def getTrafficLimit(self, source, target):
        return self.get_edge_property(source, target, options.TRAFFIC_LIMIT)

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- DRIVERS ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def hasDriver(self, start, end):
        """ return True if graph contains at least one driver from start to end
        """
        return self.has_node(start) and self.has_node(end) and self.__drivers.get(start, {}).get(end) is not None

    def hasStartingTime(self, start, end, starting_time):
        """ returns True if there exists at least one driver from start to end with the given starting time
        """
        return self.hasDriver(start, end) and self.__drivers[start][end].get(starting_time) is not None

    def addDriver(self, start, end, starting_time=0, nb=1):
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

    def setDriversProperty(self, start, end, prop, value, starting_time=None):
        """ set properties to the given drivers and returns True if driver exists
            else return False

            if starting_time == None, add a property to every drivers from start to end
        """
        if self.hasDriver(start, end):
            if starting_time is not None:
                if self.hasStartingTime(start, end, starting_time):
                    self.__drivers[start][end][starting_time][prop] = value
                    return True
                log.warning("Drivers from node %s to node %s doesn't start at %s in graph %s",
                            start, end, starting_time, self.name)
                return False
            self.__drivers[start][end][prop] = value
            return True
        log.warning('No drivers from node %s to node %s in graph %s', start, end, self.name)
        return False

    def getDrivers(self, start, end, starting_time=None):
        """ return the drivers from start to end, and with the given starting_time if not None
        """
        if self.hasDriver(start, end):
            if starting_time is not None:
                if self.hasStartingTime(start, end, starting_time):
                    return self.__drivers[start][end][starting_time]['nb']
                log.warning("Drivers from node %s to node %s doesn't start at %s in graph %s",
                            start, end, starting_time, self.name)
                return 0
            else:
                return self.__drivers[start][end]
        log.warning('No drivers from node %s to node %s in graph %s', start, end, self.name)
        return 0

    def getDriversProperty(self, start, end, prop, starting_time=None):
        if self.hasDriver(start, end):
            if starting_time is not None:
                if self.hasStartingTime(start, end, starting_time):
                    return self.__drivers[start][end][starting_time].get(prop)
                log.warning("Drivers from node %s to node %s doesn't start at %s in graph %s",
                            start, end, starting_time, self.name)
                return None
            return self.__drivers[start][end].get(prop)
        log.warning('No drivers from node %s to node %s in graph %s', start, end, self.name)
        return None

    def getAllDrivers(self):
        for start, dct in self.__drivers.iteritems():
            for end, d in dct.iteritems():
                for time, props in d.iteritems():
                    yield start, end, time, props['nb']

    def getAllUniqueDrivers(self):
        """ return the drivers making them unique if more than one for same starting, ending nodes and starting time
        """
        for start, dct in self.__drivers.iteritems():
            for end, d in dct.iteritems():
                for time, props in d.iteritems():
                    for _ in range(props['nb']):
                        yield Driver(start, end, time)

    def getAllDriversFromStartingNode(self, start):
        for end, dct in self.__drivers.get(start, {}).iteritems():
            for time, props in dct.iteritems():
                yield start, end, time, props['nb']

    def getAllDriversToEndingNode(self, end):
        for start, dct in self.__drivers.iteritems():
            for e, d in dct.iteritems():
                if e == end:
                    for time, props in d.iteritems():
                        yield start, end, time, props['nb']

    def removeDriver(self, start, end, starting_time, nb=1):
        if self.hasStartingTime(start, end, starting_time):
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
        for _, _, _, nb in self.getAllDrivers():
            res += nb
        return res

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------
