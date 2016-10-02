# -*- coding: utf-8 -*-
# !/bin/env python

from Simulator import Simulator
from utils.tools import get_id
from copy import deepcopy
import logging
import sys

log = logging.getLogger(__name__)


class FiniteHorizonSimulator(Simulator):

    def __init__(self, graph):
        """ paths = {path: {time: nb_drivers}}
            for each path we associate pairs of time, nb of drivers starting at this time
        """
        super(Simulator, self).__init__()
        self.graph = graph
        # we store the drivers: for each idd, how many drivers
        self.drivers = {get_id((s, e, t)): (s, e, t) for s, e, t, _ in self.graph.getAllDrivers()}
        self.initialize()

    def initialize(self, initial_time=0):
        """ we declare here every variable which will be modified during the simulation
        """
        self.nb_drivers = 0  # nb of drivers
        # wich drivers on which paths
        self.paths = {idd: {} for idd in self.drivers}
        # the drivers for whom we don't know the next edge
        self.moved = set(self.drivers.iterkeys())
        # for each edge we store the clocks of drivers on this edge
        # the list has to be always sorted
        # to each edge we associate a dictionnary where for a ending node we store the list of drivers' clocks
        # who wants to finish at the ending point
        self.clocks = {e: [] for e in self.graph.getAllEdges()}
        # for the key out, we store the list of driver's clocks who didn't start yet (sorted)
        self.clocks['out'] = []
        for s, e, t, n in self.graph.getAllDrivers():
            idd = get_id((s, e, t))
            j = 0
            while j < len(self.clocks['out']) and t > self.clocks['out'][j][1]:
                j += 1
            for _ in range(n):
                self.clocks['out'].insert(j, (idd, t))
            self.paths[idd][()] = n
        # how long have drivers been on the road
        self.times = {e: 0 for e in self.graph.getAllEdges()}
        # for each driver we store the next_edges
        self.next_edges = {}

    def reinitialize(self, state={}):
        """ if state is not empty, it describes a previous step of the simulator.
            We restore the current state to this previous one
        """
        if state:
            for name, attr in state.iteritems():
                self.__dict__[name] = attr
        else:
            self.initialize()

    def getCurrentState(self):
        return {name: deepcopy(attr) for name, attr in self.__dict__.iteritems()
                if name.startswith('_%s_' % self.__class__.__name__) and not filter(lambda el: name.endswith(el),
                                                                                    ['graph', 'drivers'])}

    def getMovedDrivers(self):
        for idd, nb in self.moved.iteritems():
            yield self.drivers[idd], self.paths[idd]

    def get_total_time(self):
        return sum(self.times.itervalues())

    # --------------------------------------------------------------------------------------------------------------
    # ---------------------------------- SIMULATION FUNCTIONS ------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------

    def computeClock(self, edge):
        return self.graph.getCongestionFunction(*edge)(self.graph.getEdgeProperty(edge[0], edge[1], 'traffic') or 0.0)

    def moveToNextEdge(self):
        """ simulate the move of drivers to the next edges
        """
        for edge, clocks in self.clocks.iteritems():
            j = 0
            while j < len(clocks) and clocks[j][1] == 0:
                idd = self.clocks[j][0]
                if len(self.next_edges.get(idd) or []) > 0:
                    nxt_edge, n = (self.next_edges.get(idd) or [])[0]

                    # insert new clock
                    clock, k = self.computeClock(nxt_edge), 0
                    while k < len(self.clocks[nxt_edge]) and self.clocks[nxt_edge][k] < clock:
                        k += 1
                    self.clocks[nxt_edge].insert(k, (idd, clock))
                    self.times[nxt_edge] += clock
                    traffic = self.graph.getEdgeProperty(nxt_edge[0], nxt_edge[1], 'traffic') or 0
                    self.graph.setEdgeProperty(nxt_edge[0], nxt_edge[1], 'traffic', traffic + 1)

                    # reduce nxt_edge
                    if n - 1 > 0:
                        self.next_edges[idd][0] = (nxt_edge, n - 1)
                    else:
                        del self.next_edges[idd][0]

                    # update the path for this driver
                    current_path, nb = self.paths[idd].popitem()
                    new_path = current_path + (nxt_edge[1],)
                    self.paths[idd].setdefault(new_path, 0)
                    self.path[idd][new_path] += 1
                    if nb - 1 > 0:
                        self.paths[idd][current_path] = nb - 1

                    # we remember that this driver has no next_edges
                    self.moved.add(idd)
                else:
                    self.nb_drivers -= 1

            # remove the 0 (handled drivers) from clocks
            clocks = clocks[j:]

    def updateTime(self):
        """ define the minimum clock and remove this minimum to every clock
            After this step, the minimum clock is 0.0
        """
        # compute min_clock
        min_clock = sys.maxint
        for clocks in self.clocks.itervalues():
            try:
                min_clock = min(min_clock, min(map(lambda el: el[1], clocks)))
            except ValueError:
                continue

        # update other clocks
        for clocks in self.clocks.itervalues():
            for ind in range(len(clocks)):
                clocks[ind] = (clocks[ind][0], clocks[ind][1] - min_clock)

    def updateNextEdges(self, next_edges):
        """ we update here the next_edges for each drivers.
            Each driver should have a next_edge, except if he reached his end node

            WARNING: to be used in an other script after each step !!!
        """
        for driver, dct in next_edges.iteritems():
            self.next_edges[get_id(driver)].update(dct)
        self.moved = {}

    def has_next(self):
        """ Check if there is a next step
        """
        return self.nb_drivers > 0

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
