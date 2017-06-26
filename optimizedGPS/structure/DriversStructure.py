"""
If an edge is unreachable by driver, this information should be stored in this class.
For each edge and each driver, the time interval in which the driver can be on the edge should be stored here as well.
"""
import sys
from collections import defaultdict

from sortedcontainers import SortedList


class DriversStructure(object):
    def __init__(self, graph, drivers_graph, horizon=sys.maxint):
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.horizon = horizon

        self.unreachable_edges = defaultdict(lambda: defaultdict(lambda: 0))
        self.starting_times = defaultdict(lambda: defaultdict(lambda: None))
        self.ending_times = defaultdict(lambda: defaultdict(lambda: None))

    def set_unreachable_edge_to_driver(self, driver, *edges):
        for edge in edges:
            self.unreachable_edges[driver][edge] = 1
            if driver in self.starting_times and edge in self.starting_times[driver]:
                del self.starting_times[driver][edge]
            if driver in self.ending_times and edge in self.ending_times[driver]:
                del self.ending_times[driver][edge]

    def set_reachable_edge_to_driver(self, driver, *edges):
        for edge in edges:
            self.unreachable_edges[driver][edge] = 0

    def is_edge_reachable_by_driver(self, driver, edge):
        return self.unreachable_edges[driver][edge] != 1

    def add_starting_times(self, driver, edge, *starting_times):
        if self.starting_times[driver][edge] is None:
            self.starting_times[driver][edge] = SortedList()
        self.starting_times[driver][edge].update(starting_times)

    def add_ending_times(self, driver, edge, *ending_times):
        if self.ending_times[driver][edge] is None:
            self.ending_times[driver][edge] = SortedList()
        self.ending_times[driver][edge].update(ending_times)

    def get_starting_times(self, driver, edge):
        if self.starting_times[driver][edge] is None:
            return range(self.horizon + 1)
        return self.starting_times[driver][edge]

    def get_ending_times(self, driver, edge):
        if self.ending_times[driver][edge] is None:
            return range(self.horizon + 1)
        return self.ending_times[driver][edge]

    def iter_starting_times(self, driver, edge):
        times = self.starting_times[driver][edge]
        times = times if times is not None else xrange(driver.time, self.horizon + 1)
        for starting_time in times:
            yield starting_time

    def iter_ending_times(self, driver, edge, starting_time=-1):
        times = self.ending_times[driver][edge]
        times = times if times is not None else xrange(self.horizon + 1)
        for ending_time in times:
            if ending_time > starting_time:
                yield ending_time

    def iter_time_intervals(self, driver, edge):
        ending_times = self.ending_times[driver][edge]
        ending_times = set(ending_times) if ending_times is not None else None
        for starting_time in self.iter_starting_times(driver, edge):
            for wtime in self.graph.iter_possible_waiting_time(edge, max_waiting_time=self.horizon - starting_time):
                if ending_times is None or starting_time + wtime in ending_times:
                    yield starting_time, starting_time + wtime

    def get_possible_ending_times_on_node(self, driver, node):
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
