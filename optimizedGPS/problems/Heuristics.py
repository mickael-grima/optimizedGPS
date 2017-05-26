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
    def __init__(self, graph, drivers_graph, drivers_structure=None, timeout=sys.maxint):
        super(ShortestPathHeuristic, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure,
                                                    timeout=timeout, solving_type=SolvinType.HEURISTIC)
        edges_description = {}  # for each driver we assign him a path
        for driver in drivers_graph.get_all_drivers():
            try:
                path = graph.get_shortest_path(
                    driver.start, driver.end,
                    key=self.graph.get_minimum_waiting_time
                )
            except StopIteration:
                message = "Imposible to find shortest path from node %s to node %s in graph %s"\
                          % (driver.start, driver.end, graph.name)
                log.error(message)
                raise Exception(message)
            edges_description[driver] = path
        self.simulator = FromEdgeDescriptionSimulator(graph, drivers_graph, edges_description, timeout=self.timeout)

    def simulate(self):
        self.simulator.simulate()
        self.status = self.simulator.status
        self.set_optimal_solution()


class ShortestPathTrafficFree(Problem):
    """ We give each drivers his shortest path, and we simulate considering no interaction between drivers
        Return a lower bound of our problem
    """
    def __init__(self, graph, drivers_graph, **kwargs):
        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(ShortestPathTrafficFree, self).__init__(graph, drivers_graph, **kwargs)

    def get_graph(self):
        return self.graph

    def get_drivers_graph(self):
        return self.drivers_graph

    def get_optimal_value(self):
        return self.get_value()

    def solve_with_heuristic(self):
        ct = time.time()
        status = None

        for driver in self.drivers_graph.get_all_drivers():
            self.value += driver.time
            path = self.graph.get_shortest_path(driver.start, driver.end)
            for edge in self.graph.iter_edges_in_path(path):
                self.value += self.graph.get_minimum_waiting_time(*edge)
            if time.time() - ct > self.timeout:
                status = options.TIMEOUT
            self.set_optimal_path_to_driver(driver, path)

        self.status = status if status is not None else options.SUCCESS
        self.running_time = time.time() - ct


class RealGPS(Problem):
    def __init__(self, graph, drivers_graph, **kwargs):
        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(RealGPS, self).__init__(graph, drivers_graph, **kwargs)

    def get_graph(self):
        return self.graph

    def get_drivers_graph(self):
        return self.drivers_graph

    def solve_with_heuristic(self):
        drivers = self.drivers_graph.get_time_ordered_drivers()
        # we here iteratively the drivers who already has a path
        # for each driver and each visited edge, we also store here when driver has enter and leave the given edge
        traffic = defaultdict(lambda: defaultdict(lambda: 0))
        for driver in drivers:
            driver_history = self.graph.get_shortest_path_with_traffic(driver.start, driver.end, driver.time, traffic)
            self.graph.enrich_traffic_with_driver_history(traffic, driver_history)
            path = tuple(map(lambda e: e[0], driver_history))
            self.set_optimal_path_to_driver(driver, path)
        self.set_status(options.SUCCESS)
