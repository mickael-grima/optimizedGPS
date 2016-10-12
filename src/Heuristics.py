# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.GPSSimulator import GPSSimulator
from problems.Problem import Problem
from SearchProblem import BacktrackingSearch
import time
import sys

import logging
log = logging.getLogger(__name__)


class ShortestPathHeuristic(Problem):
    """ We handle here the heuristics
    """
    def __init__(self, graph, timeout=sys.maxint):
        super(ShortestPathHeuristic, self).__init__(timeout=timeout)
        self.graph = graph
        paths = {}
        for start, end, t, nb in self.graph.getAllDrivers():
            try:
                path = self.graph.getPathsFromTo(start, end).next()
            except StopIteration:
                log.error("Imposible to find shortest path from node %s to node %s in graph %s",
                          start, end, graph.name)
                raise Exception("Imposible to find shortest path from node %s to node %s in graph %s"
                                % (start, end, graph.name))
            paths.setdefault(path, {})
            paths[path][t] = nb
        self.simulator = GPSSimulator(self.graph, paths)

    def solve(self):
        ct = time.time()

        # simulate
        while self.simulator.has_next():
            if time.time() - ct >= self.timeout:
                break
            self.simulator.next()

        self.value = self.simulator.get_value()
        self.running_time = time.time() - ct
        self.opt_solution = self.simulator.get_current_solution()


class AllowedPathsHeuristic(BacktrackingSearch):
    def __init__(self, graph, initial_value=sys.maxint, diff_length=0, timeout=sys.maxint):
        allowed_paths = []
        for s, t, _, _ in graph.getAllDrivers():
            allowed_paths.extend(graph.getPathsFromTo(s, t, length=diff_length))
        super(AllowedPathsHeuristic, self).__init__(graph, initial_value=initial_value, allowed_paths=allowed_paths,
                                                    timeout=timeout)
