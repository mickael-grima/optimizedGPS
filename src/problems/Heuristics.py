# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.GPSSimulator import GPSSimulator
from Problem import SimulatorProblem, Problem
from SearchProblem import BacktrackingSearch
import time
import sys

import logging
log = logging.getLogger(__name__)


class ShortestPathHeuristic(SimulatorProblem):
    """ We handle here the heuristics
    """
    def __init__(self, graph, timeout=sys.maxint):
        super(ShortestPathHeuristic, self).__init__(timeout=timeout)
        paths = {}
        for start, end, t, nb in graph.getAllDrivers():
            try:
                path = graph.get_paths_from_to(start, end).next()
            except StopIteration:
                log.error("Imposible to find shortest path from node %s to node %s in graph %s",
                          start, end, graph.name)
                raise Exception("Imposible to find shortest path from node %s to node %s in graph %s"
                                % (start, end, graph.name))
            paths.setdefault(path, {})
            paths[path][t] = nb
        self.simulator = GPSSimulator(graph, paths)

    def simulate(self):
        ct = time.time()

        # simulate
        while self.simulator.has_next():
            if time.time() - ct >= self.timeout:
                log.warning("Problem %s timed out", self.__class__.__name__)
                self.__timed_out = True
                break
            self.simulator.next()

        self.setOptimalSolution()


class AllowedPathsHeuristic(BacktrackingSearch):
    def __init__(self, graph, initial_value=sys.maxint, diff_length=0, timeout=sys.maxint):
        allowed_paths = []
        for s, t, _, _ in graph.getAllDrivers():
            allowed_paths.extend(graph.get_paths_from_to(s, t, length=diff_length))
        super(AllowedPathsHeuristic, self).__init__(graph, initial_value=initial_value, allowed_paths=allowed_paths,
                                                    timeout=timeout)


class UpdatedBySortingShortestPath(Problem):
    def __init__(self, graph, **kwards):
        super(UpdatedBySortingShortestPath, self).__init__(**kwards)
        self.graph = graph
        self.traffics = {}

    def solve(self):
        drivers = sorted(self.graph.getAllUniqueDrivers(), key=lambda d: d.time)
        for driver in drivers:
            self.addOptimalPathToDriver(driver.to_tuple(), ())


class ShortestPathTrafficFree(Problem):
    """ We give each drivers his shortest path, and we simulate considering no interaction between drivers
        Return a lower bound of our problem
    """
    def __init__(self, graph, **kwards):
        super(ShortestPathTrafficFree, self).__init__(**kwards)
        self.graph = graph

    def getOptimalValue(self):
        return self.getValue()

    def solve(self):
        ct = time.time()

        for driver in self.graph.getAllUniqueDrivers():
            path = self.graph.get_shortest_path(driver.start, driver.end)
            for edge in self.graph.iter_edges_in_path(path):
                self.value += self.graph.getMinimumWaitingTime(*edge)

        self.running_time = time.time() - ct
