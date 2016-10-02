# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.FiniteHorizonSimulator import FiniteHorizonSimulator
from utils.tools import splitObjectsInBoxes, assert_paths_in_graph
import sys
import logging

log = logging.getLogger(__name__)


class BacktrackingSearch():
    """ class to run a backtracking algorithm using a "finite horizon" simulator

        WARNING: we always handle minimum optimization problem
    """

    def __init__(self, graph, allowed_paths=[], initial_value=sys.maxint):
        assert_paths_in_graph(graph, *allowed_paths)
        self.simulator = FiniteHorizonSimulator(graph)
        # allowed paths: each driver should use one of these paths
        # if for a driver (start, end, time) we don't have any paths associated to (start, end)
        # then the driver can take any paths
        # here is stored the edges that are allowed in one path at least.
        self.allowed_edges = {}
        for path in allowed_paths:
            for edge in graph.getAllEdges():
                i = 0
                while i < len(path) and path[i] != edge[0]:
                    i += 1
                if i + 1 < len(path) and path[i + 1] == edge[1]:
                    self.allowed_edges.setdefault(edge, {})
                    self.allowed_edges[edge].setdefault((path[0], path[-1]), set())
                    self.allowed_edges[edge][(path[0], path[-1])].add(path[i + 1:])
        # initial value
        self.current_value = initial_value
        # we store the previous simulator states: we always follow one path in the possibilities tree
        self.previous_states = []

    def getAllowedEdges(self, driver, path):
        """ return the allowed edge for driver in graph.
            Furthermore the returned edges belong to an allowed path

            WARNING: `path` is the current path of driver, not completed !!
            IMPORTANT: an iterator here is needed, for the cutting strategy
        """
        edge = (path[-2], path[-1])
        for p in (self.allowed_edges.get(edge) or {}).get((driver[0], driver[1])) or []:
            yield p[0], p[1]

    def possibilities_iterator(self, driver, path, n):
        """ IMPORTANT: we need here an iterator to optimize the cutting strategy
        """
        for edges in splitObjectsInBoxes(self.getAllowedEdges(driver, path), n):
            yield driver, path, n, edges

    def iter_possibilities(self):
        """ compute every possibilities for given drivers

            IMPORTANT: this function has to be an iterator, in order to optimize the running time
                       if not the cutting strategy is useless !!!
        """
        # initialize the iterators
        iterators, possibility = [], {}
        for driver, paths in self.simulator.getMovedDrivers():
            for path, n in paths.iteritems():
                iterator = self.possibilities_iterator(driver, path, n)
                try:
                    possibility[driver] = iterator.next()[3]
                except StopIteration:
                    log.error("Drivers %s on path %s have no further possibilities to drive", str(driver), str(path))
                    raise StopIteration("Drivers %s on path %s have no further possibilities to drive"
                                        % (str(driver), str(path)))
                iterators.append(iterator)
        yield possibility

        # explore each possibility
        i = len(iterators) - 1
        while i >= 0:
            try:
                driver, path, n, edges = iterators[i].next()
            except StopIteration:
                i -= 1
                iterators[i] = self.possibilities_iterator(driver, path, n)
                continue
            possibility[driver] = edges
            if i < len(iterators) - 1:
                i += 1
                continue
            yield possibility

    def save_current_simulator_state(self):
        self.previous_states.append(self.simulator.getCurrentState())

    def has_previous_state(self):
        if self.previous_states:
            return True
        return False

    def backtrack(self):
        if self.has_previous_state:
            self.simulator.reinitialize(self.previous_states[-1])
            del self.previous_states[-1]
        else:
            log.error("No previous state found")
            raise Exception("No previous state found")

    def simulate(self, value=0):
        if self.simulator.has_next():
            if value < self.current_value:
                for possibility in self.iter_possibilities():
                    self.save_current_simulator_state()
                    self.simulator.updateNextEdges(possibility)
                    self.simulator.next()
                    value = self.simulator.get_total_time()
                    self.simulate(value=value)
            else:
                self.backtrack()
        else:
            if value < self.current_value:
                self.current_value = value
                self.backtrack()
