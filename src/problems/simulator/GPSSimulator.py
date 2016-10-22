# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

from Simulator import Simulator
from utils.tools import assert_paths_in_graph
import logging
import time

log = logging.getLogger(__name__)


class GPSSimulator(Simulator):
    """ this simulator consider groups of drivers: a group is entirely characterized by a starting node, an ending node,
        a starting time and a path
    """
    def __init__(self, graph, paths):
        """ paths = {path: {time: nb_drivers}}
            for each path we associate pairs of time, nb of drivers starting at this time
        """
        assert_paths_in_graph(paths, graph)
        super(GPSSimulator, self).__init__(graph)
        self.paths = list(paths.iterkeys())
        self.drivers = {}
        for i in range(len(self.paths)):
            path = self.paths[i]
            for t, nb in paths[path].iteritems():
                self.drivers.setdefault((path[0], path[-1], t), {})
                self.drivers[path[0], path[-1], t][i] = nb
        self.initialize()

    def initialize(self, initial_time=0):
        super(GPSSimulator, self).initialize()
        self.nb_driver = 0  # == number of drivers in graph if there are still drivers in graph
        # for each path's index and for each edge in the path, we store a list of clocks
        self.clocks = [{i: [] for i in range(len(path) - 1)} for path in self.paths]
        self.traffics = {}
        for s, e, t, _ in self.graph.getAllDrivers():
            for i, n in self.drivers[s, e, t].iteritems():
                self.clocks[i].setdefault(-1, [])
                j = 0
                while j < len(self.clocks[i][-1]) and self.clocks[i][-1][j] < t:
                    j += 1
                for k in range(n):
                    self.clocks[i][-1].insert(j, t)
                self.nb_driver += n

    def reinitialize(self, state=None):
        super(GPSSimulator, self).reinitialize(state=state)

    def get_current_state(self):
        state = super(GPSSimulator, self).get_current_state()

        state['nb_driver'] = self.nb_driver
        state['clocks'] = {}
        for dct in self.clocks:
            state['clocks'].append({idd: [c for c in l] for idd, l in dct.iteritems()})
        state['traffic'] = {}
        for edge, value in self.traffics.iteritems():
            state['traffic'][edge] = value

        return state

    def get_running_time(self):
        t = time.time()
        while self.has_next():
            self.next()
        return time.time() - t

    # --------------------------------------------------------------------------------------------------------------
    # ---------------------------------- SIMULATION FUNCTIONS ------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------

    def computeClock(self, edge):
        return self.graph.getCongestionFunction(*edge)(self.traffics.get(edge, 0.0))

    def update_traffic(self, edge, traffic=1):
        if traffic > 0:
            self.traffics.setdefault(edge, 0)
            self.traffics[edge] += traffic
        elif traffic < 0:
            try:
                self.traffics[edge] += traffic
            except KeyError:
                log.error("Try to remove traffic on edge %s without traffic", str(edge))
                raise KeyError("Try to remove traffic on edge %s without traffic" % str(edge))
            if self.traffics[edge] < 0:
                log.error("Remove more traffic on edge %s than possible", str(edge))
                raise ValueError("Remove more traffic on edge %s than possible" % str(edge))
            if self.traffics[edge] == 0:
                del self.traffics[edge]

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
                        while k < len(self.clocks[i][e + 1]) and self.clocks[i][e + 1][k] < clock:
                            k += 1
                        self.clocks[i][e + 1].insert(k, clock)
                        self.time += clock
                        self.update_traffic(nxt_edge)
                    else:  # we kill the driver
                        self.nb_driver -= 1
                    if e >= 0:
                        self.update_traffic((self.paths[i][e], self.paths[i][e + 1]), traffic=-1)
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

    def get_current_solution(self):
        for s, e, t, n in self.graph.getAllDrivers():
            for i, nb in self.drivers[s, e, t].iteritems():
                for _ in range(nb):
                    yield (s, e, t), self.paths[i]
