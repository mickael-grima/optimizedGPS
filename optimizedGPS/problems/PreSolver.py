
"""
In this file, we introduce some algorithm in order to simplify the problem before solving it
"""
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


class HorizonPresolver(PreSolver):
    """
    Compute the minimum horizon
    """
    def solve(self):
        from optimizedGPS.problems.Heuristics import RealGPS
        problem = RealGPS(self.graph, self.drivers_graph)
        problem.solve()
        self.drivers_structure.horizon = problem.opt_simulator.get_maximum_ending_time()

    def get_horizon(self):
        return self.drivers_structure.horizon
