
"""
In this file, we introduce some algorithm in order to simplify the problem before solving it
"""

from Heuristics import RealGPS


class PreSolver(object):
    """
    This Heuristic will be used in some methods. It should provide a feasible solution.
    """
    HEURISTIC = RealGPS

    def __init__(self, graph):
        self.heuristic = self.HEURISTIC(graph)
        self.graph = self.heuristic.get_graph()

        # solve the heuristic
        self.heuristic.solve()

    def is_edge_reachable_for_driver(self, driver, edge):
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
        d_time = sum(map(lambda e: self.graph.get_congestion_function(*e)(0), self.graph.iter_edges_in_path(path)))
        return d_time <= self.heuristic.get_driver_driving_time(driver)

    def iter_reachable_edges_for_driver(self, driver):
        for edge in self.graph.edges():
            if self.is_edge_reachable_for_driver(driver, edge):
                yield edge

    def map_reachable_edges_for_drivers(self):
        """
        to each driver we associate the reachable edges

        :return: dict
        """
        return {
            driver: list(self.iter_reachable_edges_for_driver(driver))
            for driver in self.graph.get_all_drivers()
        }
