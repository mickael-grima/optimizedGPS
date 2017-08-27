"""
If an edge is unreachable by driver, this information should be stored in this class.
For each edge and each driver, the time interval in which the driver can be on the edge should be stored here as well.

This script is useful to specify the structure of drivers inside the graph:
   - when do they reach an edge, when do they leave an edge
   - can an edge be reached by drivers

We specify the safety and presence interval here as well:
   - A presence interval is specified for each driver and edge. It ensures that, if driver takes a path containing this
   edge, then driver will drive on this edge during an interval which contains this presence interval.
   - A safety interval is specified for each driver and edge. It ensures that, if driver takes a path containing this
   edge, then driver will drive on this edge during an interval which is contained in this safety interval.
"""
import sys
from collections import defaultdict

from sortedcontainers import SortedSet


class DriversStructure(object):
    def __init__(self, graph, drivers_graph, horizon=sys.maxint):
        self.graph = graph  # road network structure
        self.drivers_graph = drivers_graph  # drivers graph
        self.horizon = horizon  # no possible time greater than this value

        # set of edges unreachable for driver
        self.unreachable_edges = defaultdict(lambda: defaultdict(lambda: 0))
        # for every driver and edge, if the value is not None, it represents the only possible starting times
        self.starting_times = defaultdict(lambda: defaultdict(lambda: None))
        # for every driver and edge, if the value is not None, it represents the only possible ending times
        self.ending_times = defaultdict(lambda: defaultdict(lambda: None))

        # For every driver and edge, we specify a pair of int
        self.presence_interval = defaultdict(lambda: defaultdict(lambda: (None, None)))
        self.safety_interval = defaultdict(lambda: defaultdict(lambda: (None, None)))

    def set_unreachable_edge_to_driver(self, driver, *edges):
        """
        Set an edge as unreachable for a driver
        """
        for edge in edges:
            self.unreachable_edges[driver][edge] = 1
            if driver in self.starting_times and edge in self.starting_times[driver]:
                del self.starting_times[driver][edge]
            if driver in self.ending_times and edge in self.ending_times[driver]:
                del self.ending_times[driver][edge]

    def set_reachable_edge_to_driver(self, driver, *edges):
        """ Set an edge as reachable for a driver """
        for edge in edges:
            self.unreachable_edges[driver][edge] = 0

    def is_edge_reachable_by_driver(self, driver, edge):
        """ return True if the edge is reachable by the driver """
        return self.unreachable_edges[driver][edge] != 1

    def add_starting_times(self, driver, edge, *starting_times):
        """ Add the given starting times to the set of possible starting times for driver """
        if self.starting_times[driver][edge] is None:
            self.starting_times[driver][edge] = SortedSet()
        self.starting_times[driver][edge].update(starting_times)

    def add_ending_times(self, driver, edge, *ending_times):
        """ Add the given ending times to the set of possible ending times for driver """
        if self.ending_times[driver][edge] is None:
            self.ending_times[driver][edge] = SortedSet()
        self.ending_times[driver][edge].update(ending_times)

    def add_safety_interval(self, driver, edge, start=None, end=None):
        """
        If start or end is None, we don't modify the actual value
        """
        safety_interval = (
            self.safety_interval[driver][edge][0] if start is None else start,
            self.safety_interval[driver][edge][1] if end is None else end
        )
        self.safety_interval[driver][edge] = safety_interval

    def add_presence_interval(self, driver, edge, start=None, end=None):
        """
        If start or end is None, we don't modify the actual value
        """
        presence_interval = (
            self.presence_interval[driver][edge][0] if start is None else start,
            self.presence_interval[driver][edge][1] if end is None else end
        )
        self.presence_interval[driver][edge] = presence_interval

    def get_starting_times(self, driver, edge):
        """ Return the possible starting times for driver on edge. If None return every integer up to horizon """
        if self.starting_times[driver][edge] is None:
            return range(self.horizon + 1)
        return self.starting_times[driver][edge]

    def get_ending_times(self, driver, edge):
        """ Return the possible ending times for driver on edge. If None return every integer up to horizon """
        if self.ending_times[driver][edge] is None:
            return range(self.horizon + 1)
        return self.ending_times[driver][edge]

    def get_safety_interval(self, driver, edge):
        """ return the safety interval for driver and edge """
        return self.safety_interval[driver][edge]

    def get_presence_interval(self, driver, edge):
        """ return the presence interval for driver and edge """
        return self.presence_interval[driver][edge]

    def get_safety_starting_time(self, driver, edge):
        """ return the starting time of the safety interval for driver and edge """
        return self.get_safety_interval(driver, edge)[0] or 0

    def get_safety_ending_time(self, driver, edge):
        """ return the ending time of the safety interval for driver and edge """
        ending_time = self.get_safety_interval(driver, edge)[1]
        return ending_time if ending_time is not None else self.horizon

    def get_presence_starting_time(self, driver, edge):
        """ return the starting time of the presence interval for driver and edge """
        starting_time = self.get_safety_interval(driver, edge)[0]
        return starting_time if starting_time is not None else self.horizon

    def get_presence_ending_time(self, driver, edge):
        """ return the ending time of the presence interval for driver and edge """
        return self.get_safety_interval(driver, edge)[1] or 0

    def iter_starting_times(self, driver, edge):
        """ iterator version of get_starting_times """
        min_starting_time = self.safety_interval[driver][edge][0] or 0
        times = self.starting_times[driver][edge]
        times = times if times is not None else xrange(driver.time, self.horizon + 1)
        for starting_time in times:
            if starting_time >= min_starting_time:
                yield starting_time

    def iter_ending_times(self, driver, edge, starting_time=-1):
        """ iterator version of get_ending_times """
        max_ending_time = self.safety_interval[driver][edge][1] or self.horizon
        times = self.ending_times[driver][edge]
        times = times if times is not None else xrange(self.horizon + 1)
        for ending_time in times:
            if starting_time < ending_time <= max_ending_time:
                yield ending_time

    def iter_time_intervals(self, driver, edge):
        """ Return the possible times interval on which driver could be on edge """
        ending_times = self.ending_times[driver][edge]
        ending_times = set(ending_times) if ending_times is not None else None
        for starting_time in self.iter_starting_times(driver, edge):
            for wtime in self.graph.iter_possible_waiting_time(edge, max_waiting_time=self.horizon - starting_time):
                if ending_times is None or starting_time + wtime in ending_times:
                    yield starting_time, starting_time + wtime

    def get_possible_ending_times_on_node(self, driver, node):
        """ Return the union of every possible ending times of every edges whith node as target """
        times, has_predecessors = set(), False
        for pred in self.graph.predecessors_iter(node):
            has_predecessors = True
            for ending_time in self.iter_ending_times(driver, (pred, node)):
                times.add(ending_time)
        return times if has_predecessors is True else None

    def iter_possible_time_on_node(self, driver, node):
        """
        Iterate every time which are possible for ending on node and for starting on node
        """
        times = self.get_possible_ending_times_on_node(driver, node)
        for succ in self.graph.successors_iter(node):
            for starting_time in self.iter_starting_times(driver, (node, succ)):
                if times is None or starting_time in times:
                    yield starting_time

    def get_possible_edges_for_driver(self, driver):
        """
        Considering the safety intervals of every edges reachable for driver, determine iteratively starting at
        driver.start if the edge can be used by driver.
        """
        for edge in self.graph.edges_iter():
            if self.is_edge_reachable_by_driver(driver, edge):
                yield edge

    def compute_minimum_traffics(self):
        """
        Considering the presence and safety interval of every driver, we compute for a driver and an edge the minimum
        traffic that this driver could see on this edge
        """
        min_traffics = defaultdict(lambda: defaultdict(lambda: 0))
        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.graph.edges_iter():
                if not self.is_edge_reachable_by_driver(driver, edge):
                    continue
                min_traffics[driver][edge] = min(
                    [
                        sum([
                            1 * (self.get_presence_starting_time(d, edge) < s <= self.get_presence_ending_time(d, edge))
                            for d in self.drivers_graph.get_all_drivers() if d != driver
                        ])
                        for s in xrange(
                            self.get_safety_starting_time(driver, edge),
                            self.get_presence_starting_time(driver, edge) + 1
                        )
                    ]
                )
        return min_traffics

    def compute_maximum_traffics(self):
        """
        Considering the presence and safety interval of every driver, we compute for a driver and an edge the maximum
        traffic that this driver could see on this edge
        """
        max_traffics = defaultdict(lambda: defaultdict(lambda: 0))
        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.graph.edges_iter():
                if not self.is_edge_reachable_by_driver(driver, edge):
                    continue
                max_traffics[driver][edge] = max(
                    [
                        sum([
                            1 * (self.get_safety_starting_time(d, edge) < s <= self.get_safety_ending_time(d, edge))
                            for d in self.drivers_graph.get_all_drivers() if d != driver
                        ])
                        for s in xrange(
                            self.get_safety_starting_time(driver, edge),
                            self.get_presence_starting_time(driver, edge) + 1
                        )
                    ]
                )
        return max_traffics

    def compute_minimum_starting_time(self, driver, edge, min_traffics):
        """
        Compute the shortest path from starting node of driver to edge, and return the driving time on this path
        considering the minimal traffic
        """
        return driver.time + sum(
            map(
                lambda e: self.graph.get_congestion_function(*e)(min_traffics[driver][e]),
                self.graph.iter_edges_in_path(self.graph.get_shortest_path(
                    driver.start, edge[0],
                    key=lambda *x: self.graph.get_congestion_function(*x)(min_traffics[driver][x]),
                    next_choice=lambda *x: self.is_edge_reachable_by_driver(driver, x)
                ))
            )
        )

    def compute_maximum_starting_time(self, driver, edge, max_traffics):
        """
        Compute the longest path from starting node of driver to edge, and return the driving time on this path
        considering the maximal traffic
        """
        return driver.time + sum(
            map(
                lambda e: self.graph.get_congestion_function(*e)(max_traffics[driver][e]),
                self.graph.iter_edges_in_path(self.graph.get_shortest_path(
                    driver.start, edge[0],
                    key=lambda *x: - self.graph.get_congestion_function(*x)(max_traffics[driver][x]),
                    next_choice=lambda *x: self.is_edge_reachable_by_driver(driver, x)
                ))
            )
        )

    def update_intervals(self, driver, edge, min_traffics, max_traffics):
        """
        Given the minimum and maximum traffics, compute the minimum/maximum starting/ending time for driver on edge.
        Then replace the old presence and safety intervals by the new values.

        return True if the new values are different to the old ones.
        """
        cong_function = self.graph.get_congestion_function(*edge)
        min_starting_time = self.compute_minimum_starting_time(driver, edge, min_traffics)
        max_starting_time = self.compute_maximum_starting_time(driver, edge, max_traffics)
        min_ending_time = min_starting_time + cong_function(min_traffics[driver][edge])
        max_ending_time = max_starting_time + cong_function(max_traffics[driver][edge])

        safety_interval = self.get_safety_interval(driver, edge)
        presence_interval = self.get_presence_interval(driver, edge)
        self.add_safety_interval(driver, edge, min_starting_time, max_ending_time)
        self.add_presence_interval(driver, edge, max_starting_time, min_ending_time)

        return safety_interval != self.get_safety_interval(driver, edge) or \
               presence_interval != self.get_presence_interval(driver, edge)

    def compute_optimal_safety_intervals(self):
        """
        The objective is to reduce the safety_interval as much as possible.
        In a time iterations loop, considering the actual presence and safety intervals,
        we compute the minimal and maximal possible traffic on a given edge for a given driver.
        From these traffics, we can update the safety and presence intervals.
        """
        is_update_possible = True  # Boolean to know if we can still run the update
        while is_update_possible is True:
            is_update_possible = False
            min_traffics = self.compute_minimum_traffics()
            max_traffics = self.compute_maximum_traffics()
            for driver in self.drivers_graph.get_all_drivers():
                for edge in self.graph.edges_iter():
                    is_update_possible = self.update_intervals(
                        driver, edge, min_traffics, max_traffics) or is_update_possible
