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
        self.nb_driver = 0  # == number of drivers in graph if there are still drivers in graph
        # for each path's index and for each edge in the path, we store a list of clocks
        self.clocks = [{i: [] for i in range(len(path) - 1)} for path in self.paths]
        for s, e, t, _ in self.graph.getAllDrivers():
            for i, n in (self.graph.getDriversProperty(s, e, 'paths', starting_time=t) or {}).iteritems():
                self.clocks[i].setdefault(-1, [])
                j = 0
                while j < len(self.clocks[i][-1]) and self.clocks[i][-1][j] < t:
                    j += 1
                for k in range(n):
                    self.clocks[i][-1].insert(j, t)
                self.nb_driver += n
        # how long has the driver been on the road
        self.times = {e: 0 for e in self.graph.getAllEdges()}

    def reinitialize(self):
        self.initialize()

    def computeClock(self, edge):
        return self.graph.getCongestionFunction(*edge)(self.graph.getEdgeProperty(edge[0], edge[1], 'traffic') or 0.0)

    def moveToNextEdge(self):
        """ simulate the move of drivers to the next edges
        """
        for i in range(len(self.clocks)):
            for e, clocks in self.clocks[i].iteritems():
                j = 0
                while j < len(clocks) and clocks[j] == 0:
                    # if we are not on the last edge of path
                    if e < len(self.paths[i]) - 2:
                        nxt_edge = (self.paths[i][e + 1], self.paths[i][e + 2])
                        # compute how long we stay on next edge
                        clock, k = self.computeClock(nxt_edge), 0
                        while k < len(clocks) and self.clocks[i][e][k] < clock:
                            k += 1
                        self.clocks[i][e + 1].insert(k, clock)
                        self.times[nxt_edge] += clock
                        traffic = self.graph.getEdgeProperty(nxt_edge[0], nxt_edge[1], 'traffic') or 0
                        self.graph.setEdgeProperty(nxt_edge[0], nxt_edge[1], 'traffic', traffic + 1)
                    else:  # we kill the driver
                        self.nb_driver -= 1
                    j += 1
                # we delete the 0
                self.clocks[i][e] = self.clocks[i][e][j:]

    def updateTime(self):
        """ define the minimum clock and remove this minimum to every clock
            After this step, the minimum clock is 0.0
        """
        min_clock = min(c[0] for p in self.clocks for c in p.itervalues() if len(c) > 0)
        for path in self.clocks:
            for clocks in path.itervalues():
                for ind in range(len(clocks)):
                    clocks[ind] -= min_clock
        print self.nb_driver

    def has_next(self):
        """ Check if there is a next step
        """
        return self.nb_driver > 0

    def next(self):
        """ Next step of the simulation
        """
        if self.has_next():
            self.updateTime()  # update the time to have 0.0 as minimum clock
            self.moveToNextEdge()  # move every 0.0 clocks to the next edge
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
