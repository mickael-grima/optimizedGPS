from collections import defaultdict
import time

from networkx import Graph

from Models import FixedWaitingTimeModel
from Problem import Problem, SolvinType


class ConstantModelAlgorithm(Problem):
    def __init__(self, graph, drivers_graph, **kwargs):
        self.model = FixedWaitingTimeModel(graph, drivers_graph, **kwargs)
        for driver in self.model.drivers:
            for edge in self.get_graph().edges():
                self.model.set_waiting_time(driver, edge, self.get_graph().get_congestion_function(*edge)(0))

        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(ConstantModelAlgorithm, self).__init__(**kwargs)

    def get_graph(self):
        return self.model.get_graph()

    def get_drivers_graph(self):
        return self.model.get_drivers_graph()

    def solve_with_heuristic(self):
        for i in range(10):
            self.model.solve()
            better_solution = self.value > self.model.value
            for driver in self.model.drivers:
                path = self.model.get_optimal_driver_path(driver)
                waiting_times = self.model.get_optimal_driver_waiting_times(driver)
                for edge in self.get_graph().iter_edges_in_path(path):
                    self.model.set_waiting_time(driver, edge, waiting_times[edge])
                if better_solution:
                    self.set_optimal_path_to_driver(driver, path)
            if better_solution:
                self.value = self.model.value


class DrivingTimeIntervalAlgorithm(Problem):
    """
    The principle of this algorithm is to compute at each step two driving time interval for each driver and each edge.
    One is an interval for which we are sure that the driver can't drive on the given edge outside from this interval.
    The second one ensure that the driver will be on the edge during this interval.

    At each step we compute theoretical maximal and minimal traffics on each edge for each driver, and from these
    traffics we ae able to compute the intervals into the next steps.
    """
    def __init__(self, graph, drivers_graph, solving_type=SolvinType.HEURISTIC, niter=-1, **kwargs):
        super(DrivingTimeIntervalAlgorithm, self).__init__(solving_type=solving_type, **kwargs)
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.has_next = True
        self.niter = niter
        self.optimal_drivers = set()
        # Traffics for each driver on each edge
        self.min_traffics = defaultdict(lambda: defaultdict(lambda: 0))
        self.max_traffics = defaultdict(lambda: defaultdict(lambda: self.get_drivers_graph().number_of_drivers()))
        # minimal and maximal starting and ending times for each driver on each edge
        self.min_starting_times = defaultdict(lambda: defaultdict(lambda: None))
        self.max_starting_times = defaultdict(lambda: defaultdict(lambda: None))
        self.min_ending_times = defaultdict(lambda: defaultdict(lambda: None))
        self.max_ending_times = defaultdict(lambda: defaultdict(lambda: None))

    def get_graph(self):
        return self.graph

    def get_drivers_graph(self):
        return self.drivers_graph

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
        for d in self.get_drivers_graph().get_all_drivers():
            if d != driver and self.min_starting_times[edge][driver] <= self.min_ending_times[edge][d] and \
                            self.max_starting_times[edge][driver] >= self.max_starting_times[edge][d]:
                traffic += 1
        return traffic

    def compute_maximal_traffic(self, driver, edge):
        """
        Considering the starting and ending times, get the maximal possible traffic for driver on edge
        """
        traffic = 0
        for d in self.get_drivers_graph().get_all_drivers():
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

    def get_best_driver_path(self, driver):
        """
        Considering the safety interval of every possible edges for driver, return the shortest path.
        """
        try:
            return self.get_graph().get_shortest_path(
                driver.start,
                driver.end,
                key=lambda u, v: self.get_safety_interval_length(driver, (u, v)),
                next_choice=lambda u, v: (u, v) in self.get_possible_edges_for_driver(driver)
            )
        except StopIteration:
            return None

    def has_reached_optimality_for_driver(self, driver):
        """
        Return if the found path can't be better
        """
        path = self.opt_solution.get(driver, None) or self.get_best_driver_path(driver)
        edge = list(self.get_graph().iter_edges_in_path(path))[-1]
        best_pred = min(
            self.get_graph().predecessors_iter(driver.end),
            key=lambda n: self.min_ending_times[n, driver.end][driver]
        )
        if self.max_ending_times[edge][driver] <= self.min_ending_times[(best_pred, driver.end)][driver]:
            self.set_optimal_path_to_driver(driver, path)
            return True
        return False

    def has_reached_optimality(self):
        for driver in self.get_drivers_graph().get_all_drivers():
            if not self.has_reached_optimality_for_driver(driver):
                return False
        return True

    def set_optimality_for_driver(self, driver):
        """
        If the driver has reached the optimality, we set his optimal path, and we set to the other edges that
        they are unreachable.

        Return True if at least one path has been setted to one driver
        """
        if driver not in self.optimal_drivers and self.has_reached_optimality_for_driver(driver):
            path = self.opt_solution[driver]
            path_edges = set(self.get_graph().iter_edges_in_path(path))
            for edge in self.get_graph().edges_iter():
                if edge not in path_edges:
                    self.add_unreachable_edge_for_driver(driver, edge)
            self.optimal_drivers.add(driver)
            return True
        return False

    def set_optimality(self):
        change = False
        for driver in self.get_drivers_graph().get_all_drivers():
            change = self.set_optimality_for_driver(driver) or change
        return change

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

    def next(self):
        """
        First we compute minimum and maximum starting and ending times for each driver on each edge.
        If we find an unreachable edge for driver, we store it.
        Then we update the traffics on each edge for each driver.
        """
        has_new_value = False
        for edge in self.get_graph().edges_iter():
            for driver in self.get_drivers_graph().get_all_drivers():
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
            for driver in self.get_drivers_graph().get_all_drivers():
                if self.is_edge_reachable_for_driver(driver, edge):
                    self.min_traffics[edge][driver] = self.compute_minimum_traffic(driver, edge)
                    self.max_traffics[edge][driver] = self.compute_maximal_traffic(driver, edge)
        self.has_next = has_new_value

    def solve_with_heuristic(self):
        n = 0
        starting_time = time.time()
        while True:
            while (self.niter < 0 or n <= self.niter) and self.has_next:
                self.next()
                if time.time() - starting_time > self.timeout:
                    break
            if not self.set_optimality() or time.time() - starting_time > self.timeout:
                break
            else:
                self.has_next = True
        for driver in self.get_drivers_graph().get_all_drivers():
            if self.opt_solution.get(driver) is None:
                self.set_optimal_path_to_driver(driver, self.get_best_driver_path(driver))
        self.running_time = time.time() - starting_time

    def __str__(self):
        to_print = ""
        for driver in self.get_drivers_graph().get_all_drivers():
            line = "%s: \n" % str(driver)
            for edge in self.get_graph().edges_iter():
                safe_interval = self.get_safety_interval(driver, edge)
                presence_interval = self.get_presence_interval(driver, edge)
                line += "  %s: [%s, [%s, %s], %s]\n" % (
                    str(edge),
                    safe_interval[0],
                    presence_interval[0],
                    presence_interval[1],
                    safe_interval[1]
                )
            line += "\n"
            to_print += line
        return to_print
