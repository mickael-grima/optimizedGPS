# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import sys
import time
from collections import defaultdict

from Problem import SimulatorProblem, Problem
from Problem import SolvinType
from simulator import FromEdgeDescriptionSimulator
from optimizedGPS import options

__all__ = ["ShortestPathHeuristic", "ShortestPathTrafficFree", "RealGPS"]

log = logging.getLogger(__name__)


class ShortestPathHeuristic(SimulatorProblem):
    """ We handle here the heuristics
    """
    def __init__(self, graph, timeout=sys.maxint):
        super(ShortestPathHeuristic, self).__init__(timeout=timeout, solving_type=SolvinType.HEURISTIC)
        edges_description = {}  # fro each driver we assign him a path
        for driver in graph.get_all_drivers():
            try:
                path = graph.get_shortest_path(driver.start, driver.end)
            except StopIteration:
                message = "Imposible to find shortest path from node %s to node %s in graph %s"\
                          % (driver.start, driver.end, graph.name)
                log.error(message)
                raise Exception(message)
            edges_description[driver] = path
        self.simulator = FromEdgeDescriptionSimulator(graph, edges_description, timeout=self.timeout)

    def simulate(self):
        self.simulator.simulate()
        self.status = self.simulator.status
        self.set_optimal_solution()


class ShortestPathTrafficFree(Problem):
    """ We give each drivers his shortest path, and we simulate considering no interaction between drivers
        Return a lower bound of our problem
    """
    def __init__(self, graph, **kwargs):
        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(ShortestPathTrafficFree, self).__init__(**kwargs)
        self.graph = graph

    def get_graph(self):
        return self.graph

    def get_optimal_value(self):
        return self.get_value()

    def solve(self):
        ct = time.time()
        status = None

        for driver in self.graph.get_all_drivers():
            self.value += driver.time
            path = self.graph.get_shortest_path(driver.start, driver.end)
            for edge in self.graph.iter_edges_in_path(path):
                self.value += self.graph.get_minimum_waiting_time(*edge)
            if time.time() - ct > self.timeout:
                status = options.TIMEOUT

        self.status = status if status is not None else options.SUCCESS
        self.running_time = time.time() - ct


class RealGPS(Problem):
    def __init__(self, graph, **kwargs):
        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(RealGPS, self).__init__(**kwargs)
        self.graph = graph

    def get_graph(self):
        return self.graph

    def solve_with_heuristic(self):
        drivers = self.graph.get_time_ordered_drivers()
        # we here iteratively the drivers who already has a path
        # for each driver and each visited edge, we also store here when driver has enter and leave the given edge
        traffic = defaultdict(lambda: defaultdict(lambda: 0))
        for driver in drivers:
            driver_history = self.graph.get_shortest_path_with_traffic(driver.start, driver.end, driver.time, traffic)
            path = ()
            for i in range(len(driver_history) - 1):
                node, t = driver_history[i]
                nxt = driver_history[i + 1][0]
                path += (node,)
                traffic[node, nxt][t] += 1
            path += (driver_history[-1][0],)
            self.set_optimal_path_to_driver(driver, path)
        self.set_status(options.SUCCESS)
