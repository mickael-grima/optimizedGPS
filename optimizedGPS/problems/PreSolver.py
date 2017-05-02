
"""
In this file, we introduce some algorithm in order to simplify the problem before solving it
"""
from collections import defaultdict

from optimizedGPS.structure.DriversStructure import DriversStructure


class PreSolver(object):
    def __init__(self, graph, drivers_graph):
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.drivers_structure = DriversStructure(graph, drivers_graph)

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
    def __init__(self, graph, drivers_graph, heuristic=None):
        super(ShortestPathPreSolver, self).__init__(graph, drivers_graph)
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
        d_time = sum(map(lambda e: self.graph.get_congestion_function(*e)(0), self.graph.iter_edges_in_path(path)))
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
        d_time = sum(map(lambda e: self.graph.get_congestion_function(*e)(0), self.graph.iter_edges_in_path(path)))

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
        other_drivers = [d for d in self.drivers_graph.get_all_drivers() if d != driver]
        partial = self.heuristic.get_partial_optimal_value(other_drivers)
        for edge in self.graph.edges_iter():
            path = self.graph.get_shortest_path_through_edge(driver, edge)
            if path is not None:
                d_time = sum(map(lambda e: self.graph.get_congestion_function(*e)(0), self.graph.iter_edges_in_path(path)))
                if partial + d_time + driver.time <= self.heuristic.get_optimal_value():
                    yield edge


class DrivingTimeIntervalPresolver(PreSolver):
    """
    The principle of this algorithm is to compute at each step two driving time interval for each driver and each edge.
    One is an interval for which we are sure that the driver can't drive on the given edge outside from this interval.
    The second one ensure that the driver will be on the edge during this interval.

    At each step we compute theoretical maximal and minimal traffics on each edge for each driver, and from these
    traffics we ae able to compute the intervals into the next steps.
    """
    def __init__(self, graph, drivers_graph, niter=-1):
        super(DrivingTimeIntervalPresolver, self).__init__(graph, drivers_graph)
        self.niter = niter
        # Traffics for each driver on each edge
        self.min_traffics = defaultdict(lambda: defaultdict(lambda: 0))
        self.max_traffics = defaultdict(lambda: defaultdict(lambda: self.drivers_graph.number_of_drivers()))

    def compute_minimum_starting_time(self, driver, edge):
        """
        Considering the traffic, we get the minimum time before which the driver can't arrive on edge
        """
        try:
            congestion = self.get_graph().get_congestion_function
            path = self.get_graph().get_shortest_path(
                driver.start,
                edge[0],
                key=lambda u, v: congestion(u, v)(self.min_traffics[u, v][driver])
            ) if edge[0] != driver.start else ()
            return driver.time + sum(map(
                lambda (u, v): congestion(u, v)(self.min_traffics[u, v][driver]),
                self.get_graph().iter_edges_in_path(path)
            ))
        except StopIteration:
            return None

    def compute_maximum_starting_time(self, driver, edge):
        """
        Considering the traffic, we get the maximum time after which the driver has already been on edge
        """
        try:
            congestion = self.get_graph().get_congestion_function
            path = self.get_graph().get_shortest_path(
                driver.start,
                edge[0],
                key=lambda u, v: 1 / float(congestion(u, v)(self.max_traffics[u, v][driver]))
            ) if edge[0] != driver.start else ()
            return driver.time + sum(map(
                lambda (u, v): congestion(u, v)(self.max_traffics[u, v][driver]),
                self.get_graph().iter_edges_in_path(path)
            ))
        except StopIteration:
            return None

    def compute_minimum_ending_time(self, driver, edge):
        """
        Considering the traffic, we get the minimum ending time before which the driver hasn't crossed the edge.
        """
        min_starting_time = self.drivers_structure.get_safety_interval(driver, edge).lower
        max_starting_time = self.drivers_structure.get_presence_interval(driver, edge).lower
        congestion = self.get_graph().get_congestion_function
        if min_starting_time is None:
            return None
        else:
            return max(max_starting_time, min_starting_time + congestion(*edge)(self.min_traffics[edge][driver]))

    def compute_maximum_ending_time(self, driver, edge):
        """
        Considering the traffic, we get the maximum ending time after which the driver has crossed the edge.
        """
        max_starting_time = self.drivers_structure.get_presence_interval(driver, edge).lower
        congestion = self.get_graph().get_congestion_function
        if max_starting_time is None:
            return None
        else:
            return max_starting_time + congestion(*edge)(self.max_traffics[edge][driver])

    def compute_minimum_traffic(self, driver, edge):
        """
        Considering the starting and ending times, get the minimal possible traffic for driver on edge
        """
        traffic = 0
        for d in self.get_drivers_graph().get_all_drivers():
            if d != driver:
                presence_interval = self.drivers_structure.get_presence_interval(d, edge)
                min_starting_time = self.drivers_structure.get_safety_interval(driver, edge).lower
                max_starting_time = self.drivers_structure.get_presence_interval(driver, edge).lower
                if min_starting_time <= presence_interval.upper and max_starting_time >= presence_interval.lower:
                    traffic += 1
        return traffic

    def compute_maximal_traffic(self, driver, edge):
        """
        Considering the starting and ending times, get the maximal possible traffic for driver on edge
        """
        traffic = 0
        for d in self.get_drivers_graph().get_all_drivers():
            if d != driver:
                safety_interval = self.drivers_structure.get_presence_interval(d, edge)
                min_starting_time = self.drivers_structure.get_safety_interval(driver, edge).lower
                max_starting_time = self.drivers_structure.get_presence_interval(driver, edge).lower
                if min_starting_time <= safety_interval.upper and max_starting_time >= safety_interval.lower:
                    traffic += 1
        return traffic

    def set_unreachable_edge_to_driver(self, driver, edge):
        super(DrivingTimeIntervalPresolver, self).set_unreachable_edge_to_driver(driver, edge)
        self.drivers_structure.set_safety_interval_to_driver(driver, edge, (None, None))
        self.drivers_structure.set_presence_interval_to_driver(driver, edge, (None, None))

    def next(self):
        """
        First we compute minimum and maximum starting and ending times for each driver on each edge.
        If we find an unreachable edge for driver, we store it.
        Then we update the traffics on each edge for each driver.
        """
        has_new_value = False
        for edge in self.get_graph().edges_iter():
            for driver in self.get_drivers_graph().get_all_drivers():
                if self.is_edge_reachable_by_driver(driver, edge):
                    # Safety interval
                    edge_update = False
                    min_starting_time = self.compute_minimum_starting_time(driver, edge)
                    if min_starting_time > self.drivers_structure.get_safety_interval(driver, edge).lower:
                        edge_update = True

                    # Presence interval
                    max_starting_time = self.compute_maximum_starting_time(driver, edge)
                    if max_starting_time < self.drivers_structure.get_presence_interval(driver, edge).lower:
                        edge_update = True

                    if min_starting_time is None:
                        self.set_unreachable_edge_to_driver(driver, edge)
                    elif edge_update:  # compute the ending time since we updated the starting time
                        max_ending_time = self.compute_maximum_ending_time(driver, edge)
                        min_ending_time = self.compute_maximum_ending_time(driver, edge)
                        self.drivers_structure.set_safety_interval_to_driver(
                            driver, edge, (min_starting_time, max_ending_time)
                        )
                        self.drivers_structure.set_presence_interval_to_driver(
                            driver, edge, (max_starting_time, min_ending_time)
                        )
                    has_new_value = has_new_value or edge_update

        for edge in self.get_graph().edges_iter():
            for driver in self.get_drivers_graph().get_all_drivers():
                if self.is_edge_reachable_by_driver(driver, edge):
                    self.min_traffics[edge][driver] = self.compute_minimum_traffic(driver, edge)
                    self.max_traffics[edge][driver] = self.compute_maximal_traffic(driver, edge)
        return has_new_value

    def solve(self):
        has_next_step, n = True, 0
        while (self.niter < 0 or n <= self.niter) and has_next_step:
            has_next_step = self.next()
