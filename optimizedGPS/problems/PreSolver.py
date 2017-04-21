
"""
In this file, we introduce some algorithm in order to simplify the problem before solving it
"""


class PreSolver(object):
    def __init__(self, graph, heuristic=None):
        from optimizedGPS.problems.Heuristics import RealGPS
        self.heuristic = heuristic(graph, presolving=False) if heuristic is not None else RealGPS(graph, presolving=False)
        self.graph = self.heuristic.get_graph()

        # solve the heuristic
        self.heuristic.solve()

    def is_edge_reachable_for_driver(self, driver, edge):
        raise NotImplementedError("Not implemented yet")

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


class DriverPreSolver(PreSolver):
    """
    This Heuristic will be used in some methods. It should provide a feasible solution.
    """
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


class GlobalPreSolver(PreSolver):
    """
    This Heuristic will be used in some methods. It should provide a feasible solution.
    """
    def is_edge_reachable_for_driver(self, driver, edge):
        """
        We compute first a lower bound time for driver to reach edge and then to reach his ending node from edge.
        If this time is greater than the time provided by the heuristic for this driver to drive from start to end,
        we return False, otherwise True.

        :param driver: Driver object
        :param edge: Edge, should belong to self.graph
        :return: Boolean
        """
        path = self.graph.get_shortest_path_through_edge(driver, edge)
        d_time = sum(map(lambda e: self.graph.get_congestion_function(*e)(0), self.graph.iter_edges_in_path(path)))

        other_drivers = [d for d in self.graph.get_all_drivers() if d != driver]
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
        other_drivers = [d for d in self.graph.get_all_drivers() if d != driver]
        partial = self.heuristic.get_partial_optimal_value(other_drivers)
        for edge in self.graph.edges():
            path = self.graph.get_shortest_path_through_edge(driver, edge)
            if path is not None:
                d_time = sum(map(lambda e: self.graph.get_congestion_function(*e)(0), self.graph.iter_edges_in_path(path)))
                if partial + d_time + driver.time <= self.heuristic.get_optimal_value():
                    yield edge
