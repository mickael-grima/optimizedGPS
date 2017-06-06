
"""
In this file, we introduce some algorithm in order to simplify the problem before solving it
"""
from collections import defaultdict
import sys

from optimizedGPS.structure.DriversStructure import DriversStructure


class PreSolver(object):
    def __init__(self, graph, drivers_graph, drivers_structure=None, horizon=sys.maxint):
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.drivers_structure = drivers_structure or DriversStructure(graph, drivers_graph, horizon=horizon)

    def get_graph(self):
        return self.graph

    def get_drivers_graph(self):
        return self.drivers_graph

    def solve(self):
        raise NotImplementedError("Not implemented yet")

    def set_unreachable_edge_to_driver(self, driver, edge):
        self.drivers_structure.set_unreachable_edge_to_driver(driver, edge)

    def is_edge_reachable_by_driver(self, driver, edge):
        return self.drivers_structure.is_edge_reachable_by_driver(driver, edge)

    def iter_reachable_edges_for_driver(self, driver):
        for edge in self.graph.edges_iter():
            if self.is_edge_reachable_by_driver(driver, edge):
                yield edge

    def map_reachable_edges_for_drivers(self):
        """
        to each driver we associate the reachable edges

        :return: dict
        """
        return {
            driver: list(self.iter_reachable_edges_for_driver(driver))
            for driver in self.drivers_graph.get_all_drivers()
        }


class ShortestPathPreSolver(PreSolver):
    def __init__(self, graph, drivers_graph, drivers_structure=None, horizon=sys.maxint, heuristic=None):
        super(ShortestPathPreSolver, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure,
                                                    horizon=horizon)
        from optimizedGPS.problems.Heuristics import RealGPS
        self.heuristic = heuristic(graph, drivers_graph) if heuristic is not None else RealGPS(graph, drivers_graph)

        # solve the heuristic
        self.heuristic.solve()

    def iter_unused_edges(self):
        """
        Iterate the edges on which no drivers will driver

        :return:
        """
        drivers_map = self.map_reachable_edges_for_drivers()
        for edge in self.graph.edges():
            is_used = False
            for driver, edges in drivers_map.iteritems():
                if edge in edges:
                    is_used = True
                    break
            if is_used is False:
                yield edge

    def get_horizon(self):
        """
        return the value of the heuristic (max ending time)
        """
        return self.heuristic.opt_simulator.get_maximum_ending_time()


class DriverPreSolver(ShortestPathPreSolver):
    """
    This Heuristic will be used in some methods. It should provide a feasible solution.
    """
    def is_edge_reachable_by_driver(self, driver, edge):
        """
        We compute first a lower bound time for driver to reach edge and then to reach his ending node from edge.
        If this time is greater than the time provided by the heuristic for this driver to drive from start to end,
        we return False, otherwise True.

        :param driver: Driver object
        :param edge: Edge, should belong to self.graph
        :return: Boolean
        """
        try:
            path = self.graph.get_shortest_path(driver.start, edge[0]) if edge[0] != driver.start else (edge[0],)
            path += self.graph.get_shortest_path(edge[1], driver.end) if edge[1] != driver.end else (edge[1],)
        except StopIteration:  # Not path reaching edge
            return False
        d_time = sum(map(lambda e: self.graph.get_minimum_waiting_time(*e), self.graph.iter_edges_in_path(path)))
        return d_time <= self.heuristic.get_driver_driving_time(driver)


class GlobalPreSolver(ShortestPathPreSolver):
    """
    This Heuristic will be used in some methods. It should provide a feasible solution.
    """
    def is_edge_reachable_by_driver(self, driver, edge):
        """
        We compute first a lower bound time for driver to reach edge and then to reach his ending node from edge.
        If this time is greater than the time provided by the heuristic for this driver to drive from start to end,
        we return False, otherwise True.

        :param driver: Driver object
        :param edge: Edge, should belong to self.graph
        :return: Boolean
        """
        path = self.graph.get_shortest_path_through_edge(driver, edge)
        d_time = sum(map(lambda e: self.graph.get_minimum_waiting_time(*e), self.graph.iter_edges_in_path(path)))

        other_drivers = [d for d in self.drivers_graph.get_all_drivers() if d != driver]
        partial = self.heuristic.get_partial_optimal_value(other_drivers)
        return partial + d_time + driver.time <= self.heuristic.get_optimal_value()

    def iter_reachable_edges_for_driver(self, driver):
        """
        Iterate every reachable edge for driver.
        Since the partial solution shouldn't be computed for each edge, we rewrite the code done in
        `is_edge_reachable_for_driver`.

        :param driver: Driver instance
        :return:
        """
        partial = self.heuristic.get_partial_optimal_value(
            [d for d in self.drivers_graph.get_all_drivers() if d != driver])
        opt_value = self.heuristic.get_optimal_value()
        for edge in self.graph.edges_iter():
            path = self.graph.get_shortest_path_through_edge(
                driver, edge, key=self.graph.get_minimum_waiting_time)
            if path is not None:
                d_time = sum(map(
                    lambda e: self.graph.get_minimum_waiting_time(*e),
                    self.graph.iter_edges_in_path(path)
                ))
                if partial + d_time + driver.time <= opt_value:
                    yield edge


class LowerUpperBoundsPresolver(PreSolver):
    def __init__(self, graph, drivers_graph, drivers_structure=None, horizon=sys.maxint,
                 lower_bound=None, upper_bound=None):
        super(LowerUpperBoundsPresolver, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure,
                                                        horizon=horizon)

        if lower_bound is None:
            from optimizedGPS.problems.Heuristics import ShortestPathTrafficFree
            self.lower_bound = ShortestPathTrafficFree(graph, drivers_graph, drivers_structure=drivers_structure,
                                                       horizon=horizon)
        else:
            self.lower_bound = lower_bound(graph, drivers_graph, drivers_structure=drivers_structure, horizon=horizon)

        if upper_bound is None:
            from optimizedGPS.problems.Heuristics import RealGPS
            self.upper_bound = RealGPS(graph, drivers_graph, drivers_structure=drivers_structure, horizon=horizon)
        else:
            self.upper_bound = upper_bound(graph, drivers_graph, drivers_structure=drivers_structure, horizon=horizon)

    def solve(self):
        self.lower_bound.solve()
        self.upper_bound.solve()

        def get_starting_times(algo):
            res = {}
            for driver, times in algo.iter_complete_optimal_solution():
                res[driver], i = {}, 0
                while i < len(times) - 1:
                    res[driver][times[i][0]] = (times[i][1], times[i + 1][1])
                    i += 1
                res[driver][times[i][0]] = (times[i][1], algo.get_driver_driving_time(driver) + driver.time)

            return res

        lower_interval, upper_interval = map(get_starting_times, [self.lower_bound, self.upper_bound])

        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.graph.edges_iter():
                start = lower_interval[driver].get(edge, (0, 0))[0]
                end = upper_interval[driver].get(edge, (sys.maxint, sys.maxint))[1]
                self.drivers_structure.set_presence_interval_to_driver(driver, edge, (start, end))

    def get_horizon(self):
        """
        return the value of the heuristic (max ending time)
        """
        return self.upper_bound.opt_simulator.get_maximum_ending_time()
