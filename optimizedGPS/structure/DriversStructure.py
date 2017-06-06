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
        self.starting_times.update(starting_times)

    def add_ending_times(self, driver, edge, *ending_times):
        if self.ending_times[driver][edge] is None:
            self.ending_times[driver][edge] = SortedList()
        self.ending_times.update(ending_times)

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
        times = times if times is not None else xrange(self.horizon + 1)
        for starting_time in times:
            yield starting_time

    def iter_ending_times(self, driver, edge):
        times = self.ending_times[driver][edge]
        times = times if times is not None else xrange(self.horizon + 1)
        for starting_time in times:
            yield starting_time

    def get_possible_ending_times_on_node(self, driver, node):
        times = set()
        for edge in self.graph.predecessors(node):
            for ending_time in self.iter_ending_times(driver, edge):
                times.add(ending_time)
        return times

    def get_possible_edges_for_driver(self, driver):
        """
        Considering the safety intervals of every edges reachable for driver, determine iteratively starting at
        driver.start if the edge can be used by driver.
        """
        for edge in self.graph.edges_iter():
            if self.is_edge_reachable_by_driver(driver, edge):
                yield edge
