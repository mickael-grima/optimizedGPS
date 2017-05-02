
"""
In this file, we introduce some algorithm in order to simplify the problem before solving it
"""
from collections import defaultdict

from networkx import Graph


class PreSolver(object):
    def __init__(self, graph, heuristic=None):
        from optimizedGPS.problems.Heuristics import RealGPS
        self.heuristic = heuristic(graph) if heuristic is not None else RealGPS(graph)
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


class DrivingTimeIntervalPresolver(object):
    """
    The principle of this algorithm is to compute at each step two driving time interval for each driver and each edge.
    One is an interval for which we are sure that the driver can't drive on the given edge outside from this interval.
    The second one ensure that the driver will be on the edge during this interval.

    At each step we compute theoretical maximal and minimal traffics on each edge for each driver, and from these
    traffics we ae able to compute the intervals into the next steps.
    """
    def __init__(self, graph, niter=-1):
        self.graph = graph
        self.niter = niter
        self.unreachable_edges_for_driver = defaultdict(set)
        # Traffics for each driver on each edge
        self.min_traffics = defaultdict(lambda: defaultdict(lambda: 0))
        self.max_traffics = defaultdict(lambda: defaultdict(lambda: self.get_graph().number_of_drivers()))
        # minimal and maximal starting and ending times for each driver on each edge
        self.min_starting_times = defaultdict(lambda: defaultdict(lambda: None))
        self.max_starting_times = defaultdict(lambda: defaultdict(lambda: None))
        self.min_ending_times = defaultdict(lambda: defaultdict(lambda: None))
        self.max_ending_times = defaultdict(lambda: defaultdict(lambda: None))

    def get_graph(self):
        return self.graph

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
        min_starting_time = self.min_starting_times[edge][driver]
        max_starting_time = self.max_starting_times[edge][driver]
        congestion = self.get_graph().get_congestion_function
        if min_starting_time is None:
            return None
        else:
            return max(max_starting_time, min_starting_time + congestion(*edge)(self.min_traffics[edge][driver]))

    def compute_maximum_ending_time(self, driver, edge):
        """
        Considering the traffic, we get the maximum ending time after which the driver has crossed the edge.
        """
        max_starting_time = self.max_starting_times[edge][driver]
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
        for d in self.get_graph().get_all_drivers():
            if d != driver and self.min_starting_times[edge][driver] <= self.min_ending_times[edge][d] and \
                            self.max_starting_times[edge][driver] >= self.max_starting_times[edge][d]:
                traffic += 1
        return traffic

    def compute_maximal_traffic(self, driver, edge):
        """
        Considering the starting and ending times, get the maximal possible traffic for driver on edge
        """
        traffic = 0
        for d in self.get_graph().get_all_drivers():
            if d != driver and self.min_starting_times[edge][driver] <= self.max_ending_times[edge][d] and \
                            self.max_starting_times[edge][driver] >= self.min_starting_times[edge][d]:
                traffic += 1
        return traffic

    def add_unreachable_edge_for_driver(self, driver, edge):
        self.unreachable_edges_for_driver[driver].add(edge)
        self.min_starting_times[edge][driver] = None
        self.max_starting_times[edge][driver] = None
        self.min_ending_times[edge][driver] = None
        self.max_ending_times[edge][driver] = None

    def is_edge_reachable_for_driver(self, driver, edge):
        return edge not in self.unreachable_edges_for_driver[driver]

    def get_safety_interval(self, driver, edge):
        """
        return the interval of time (as a tuple) in which we are sure that the driver is.
        """
        return self.min_starting_times[edge][driver], self.max_ending_times[edge][driver]

    def get_safety_interval_length(self, driver, edge):
        safety_interval = self.get_safety_interval(driver, edge)
        if safety_interval[0] is None or safety_interval[1] is None:
            return None
        return safety_interval[1] - safety_interval[0]

    def get_presence_interval(self, driver, edge):
        """
        return the interval of time (as tuple) in which we are sure that the driver will be.
        """
        return self.max_starting_times[edge][driver], self.min_ending_times[edge][driver]

    def are_edges_connected_for_driver(self, driver, edge_source, edge_target):
        """
        Return True if the safety interval for edge source intersect the safety interval for edge target,
        and if the safety interval for edge source starts and ends before the one for edge target.
        Otherwise return False.

        Indeed if the intersection is empty, driver can't driver from edge source to edge target
        """
        source_interval = self.get_safety_interval(driver, edge_source)
        target_interval = self.get_safety_interval(driver, edge_target)
        if any(map(lambda i: i is None, source_interval + target_interval)):
            return False
        return source_interval[0] <= target_interval[0] <= source_interval[1] <= target_interval[1]

    def get_possible_edges_for_driver(self, driver):
        """
        Considering the safety intervals of every edges reachable for driver, determine iteratively starting at
        driver.start if the edge can be used by driver.
        """
        visited = set()
        nexts = set(map(lambda s: (driver.start, s), self.get_graph().successors_iter(driver.start)))
        accepted = set(map(lambda s: (driver.start, s), self.get_graph().successors_iter(driver.start)))
        while len(nexts) > 0:
            edge = nexts.pop()
            visited.add(edge)
            for succ in self.get_graph().successors_iter(edge[1]):
                next_edge = (edge[1], succ)
                if next_edge in visited:
                    continue
                if self.are_edges_connected_for_driver(driver, edge, next_edge):
                    nexts.add(next_edge)
                    accepted.add(next_edge)
        return accepted

    def are_drivers_dependent(self, driver1, driver2):
        """
        Return True if both drivers can be on the same edge at the same time
        """
        for edge in self.get_graph().edges_iter():
            if self.min_starting_times[edge][driver1] <= self.min_starting_times[edge][driver2]:
                if self.max_ending_times[edge][driver1] <= self.max_ending_times[edge][driver2]:
                    return True
            else:
                if self.max_ending_times[edge][driver2] <= self.max_ending_times[edge][driver1]:
                    return True
        return False

    def get_drivers_graph(self):
        """
        Compute the drivers graph.
        If optimal is set to true, we consider the optimal drivers as well. Otherwise no.
        """
        graph = Graph()
        for driver in self.get_graph().get_all_drivers():
            graph.add_node(driver)
            for d in self.get_graph().get_all_drivers():
                if not graph.has_edge(driver, d) and self.are_drivers_dependent(driver, d):
                    graph.add_edge(driver, d)
        return graph

    def next(self):
        """
        First we compute minimum and maximum starting and ending times for each driver on each edge.
        If we find an unreachable edge for driver, we store it.
        Then we update the traffics on each edge for each driver.
        """
        has_new_value = False
        for edge in self.get_graph().edges_iter():
            for driver in self.get_graph().get_all_drivers():
                if self.is_edge_reachable_for_driver(driver, edge):
                    min_starting_time = self.compute_minimum_starting_time(driver, edge)
                    if self.min_starting_times[edge][driver] != min_starting_time:
                        has_new_value = True
                    self.min_starting_times[edge][driver] = min_starting_time
                    max_starting_time = self.compute_maximum_starting_time(driver, edge)
                    if self.max_starting_times[edge][driver] != max_starting_time:
                        has_new_value = True
                    self.max_starting_times[edge][driver] = max_starting_time
                    self.min_ending_times[edge][driver] = self.compute_minimum_ending_time(driver, edge)
                    self.max_ending_times[edge][driver] = self.compute_maximum_ending_time(driver, edge)
                    if self.min_starting_times[edge][driver] is None:
                        self.add_unreachable_edge_for_driver(driver, edge)

        for edge in self.get_graph().edges_iter():
            for driver in self.get_graph().get_all_drivers():
                if self.is_edge_reachable_for_driver(driver, edge):
                    self.min_traffics[edge][driver] = self.compute_minimum_traffic(driver, edge)
                    self.max_traffics[edge][driver] = self.compute_maximal_traffic(driver, edge)
        return has_new_value

    def optimize_intervals(self):
        has_next_step, n = True, 0
        while (self.niter < 0 or n <= self.niter) and has_next_step:
            has_next_step = self.next()
