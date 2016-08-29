# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

from Simulator import Simulator
from utils.tools import assert_paths_in_graph
import logging

log = logging.getLogger(__name__)


class GPSSimulator(Simulator):
    """ this simulator consider groups of drivers: a group is entirely characterized by a starting node, an ending node,
        a starting time and a path
    """
    def __init__(self, graph, paths):
        """ paths = {path: {time: nb_drivers}}
            for each path we associate pairs of time, nb of drivers starting at this time
        """
        super(GPSSimulator, self).__init__()
        assert_paths_in_graph(paths, graph)
        self.graph = graph
        self.paths = list(paths.iterkeys())
        props, i = {}, 0
        for i in range(len(self.paths)):
            path = self.paths[i]
            dct = paths[path]
            for time, nb in dct.iteritems():
                props.setdefault((path[0], path[-1], time), {})
                props[path[0], path[-1], time][i] = nb
        for (s, e, t), dct in props.iteritems():
            self.graph.setDriversProperty(s, e, 'paths', dct, starting_time=t)
        self.initialize()

    def initialize(self, initial_time=0):
        # Initialize the instances
        self.time = initial_time
        self.state = {}  # which driver on which edge
        # drivers clocks: how long does he have to stay on the current edge
        # (s, e, t, p) characterize enterily a set of drivers
        self.clocks = {}
        # how long has the driver been on the road
        self.times = {}
        for s, e, t, _ in self.graph.getAllDrivers():
            for i, n in (self.graph.getDriversProperty(s, e, 'paths', starting_time=t) or {}).iteritems():
                self.clocks[i, t] = t
                self.times[i, t] = 0

    def reinitialize(self):
        self.initialize()

    def getNextMove(self):
        for driver, clock in self.clocks.iteritems():
            if clock == 0:
                return driver

    def getNextEdge(self, *driver):
        """ Define the edge where the driver has to move
        """
        edge = self.state.get(driver)
        path = self.paths[driver[0]]
        if edge is None:
            return (path[0], path[1])
        else:
            target = edge[1]
            i = 0
            while path[i] != target:
                i += 1
                if i >= len(path):
                    log.error("driver on edge %s not in path %s" % (str(edge), str(path)))
                    raise Exception("driver on edge %s not in path %s" % (str(edge), str(path)))
            if i < len(path) - 1:
                return (path[i], path[i + 1])
            else:
                return None

    def computeClock(self, edge):
        return self.graph.getCongestionFunction(*edge)(self.graph.getEdgeProperty(edge[0], edge[1], 'traffic') or 0.0)

    def killDriver(self, *driver):
        """ remove driver from the data
        """
        del self.state[driver]
        del self.clocks[driver]

    def moveToNextEdge(self, *driver):
        """ simulate the move of driver to the next edge
        """
        nxt_edge = self.getNextEdge(*driver)
        # remove driver of previous edge
        if driver in self.state:
            source, target = self.state[driver]
            traffic = self.graph.getEdgeProperty(source, target, 'traffic')
            self.graph.setEdgeProperty(source, target, 'traffic', traffic - 1)
        # if driver arrived we remove it from the graph
        if nxt_edge is None:
            self.killDriver(*driver)
        # else we move driver to the next edge
        else:
            self.clocks[driver] = self.computeClock(nxt_edge)
            self.state[driver] = nxt_edge
            traffic = self.graph.getEdgeProperty(nxt_edge[0], nxt_edge[1], 'traffic') or 0.0
            self.graph.setEdgeProperty(nxt_edge[0], nxt_edge[1], 'traffic', traffic + 1)
            self.times[driver] += self.clocks[driver]

    def updateTime(self):
        """ define the minimum clock and remove this minimum to every clock.
            if starting_time >= self.time we don't consider the related clock
        """

        min_clock = min(self.clocks.itervalues())
        for driver in self.clocks.iterkeys():
            self.clocks[driver] -= min_clock
        self.time += min_clock

    def has_next(self):
        """ Check if there is a next step
        """
        return len(self.clocks) > 0

    def next(self):
        """ Next step of the simulation
        """
        if self.has_next():
            self.updateTime()
            driver = self.getNextMove()
            self.moveToNextEdge(*driver)
        else:
            log.error("StopIteration: No drivers on graph")
            raise StopIteration("No drivers on graph")

    def previous(self):
        """ previous step in the simulation
        """
        pass

    def to_image(self):
        """ Produce an image describing the current step
        """
        raise NotImplementedError()
