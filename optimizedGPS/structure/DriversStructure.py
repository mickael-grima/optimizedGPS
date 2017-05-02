"""
If an edge is unreachable by driver, this information should be stored in this class.
For each edge and each driver, the time interval in which the driver can be on the edge should be stored here as well.
"""
import sys
from collections import defaultdict, namedtuple

import networkx as nx

Interval = namedtuple("Interval", ["lower", "upper"])


class DriversStructure(object):
    def __init__(self, graph, drivers_graph):
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.unreachable_edges = defaultdict(lambda: defaultdict(lambda: 0))
        self.safety_intervals = defaultdict(lambda: defaultdict(lambda: Interval(0, sys.maxint)))
        self.presence_intervals = defaultdict(lambda: defaultdict(lambda: Interval(0, sys.maxint)))

    def set_unreachable_edge_to_driver(self, driver, edge):
        self.unreachable_edges[driver][edge] = 1

    def set_safety_interval_to_driver(self, driver, edge, interval):
        self.safety_intervals[driver][edge] = Interval(*interval)

    def set_presence_interval_to_driver(self, driver, edge, interval):
        self.presence_intervals[driver][edge] = Interval(*interval)

    def is_edge_reachable_by_driver(self, driver, edge):
        return self.unreachable_edges[driver][edge] != 1

    def get_safety_interval(self, driver, edge):
        return self.safety_intervals[driver][edge]

    def get_presence_interval(self, driver, edge):
        return self.presence_intervals[driver][edge]

    def are_edges_time_connected_for_driver(self, driver, edge_source, edge_target):
        """
        Return True if the safety interval for edge source intersect the safety interval for edge target,
        and if the safety interval for edge source starts and ends before the one for edge target.
        Otherwise return False.

        Indeed if the intersection is empty, driver can't driver from edge source to edge target
        """
        source_interval = self.get_safety_interval(driver, edge_source)
        target_interval = self.get_safety_interval(driver, edge_target)
        if not self.graph.has_edge(edge_source) or not self.graph.has_edge(edge_target):
            return False
        if edge_source[0] != edge_target[0]:
            return False
        if any(map(lambda i: i is None, source_interval + target_interval)):
            return False
        return source_interval.lower <= target_interval.lower <= source_interval.upper <= target_interval.upper

    def get_possible_edges_for_driver(self, driver):
        """
        Considering the safety intervals of every edges reachable for driver, determine iteratively starting at
        driver.start if the edge can be used by driver.
        """
        visited = set()
        nexts = set(map(lambda s: (driver.start, s), self.graph.successors_iter(driver.start)))
        accepted = set(map(lambda s: (driver.start, s), self.graph.successors_iter(driver.start)))
        while len(nexts) > 0:
            edge = nexts.pop()
            visited.add(edge)
            for succ in self.graph.successors_iter(edge[1]):
                next_edge = (edge[1], succ)
                if next_edge in visited:
                    continue
                if self.are_edges_time_connected_for_driver(driver, edge, next_edge):
                    nexts.add(next_edge)
                    accepted.add(next_edge)
        return accepted

    def are_drivers_dependent(self, driver1, driver2):
        """
        Return True if both drivers can be on the same edge at the same time
        """
        for edge in self.graph.edges_iter():
            if self.is_edge_reachable_by_driver(driver1, edge) and self.is_edge_reachable_by_driver(driver2, edge):
                safety_interval1 = self.get_safety_interval(driver1, edge)
                safety_interval2 = self.get_safety_interval(driver2, edge)
                if safety_interval1.lower <= safety_interval2.lower:
                    if safety_interval2.lower < safety_interval1.upper:
                        return True
                else:
                    if safety_interval1.lower < safety_interval2.upper:
                        return True
        return False

    def set_edges_to_drivers_graph(self):
        """
        Compute the drivers graph.
        If optimal is set to true, we consider the optimal drivers as well. Otherwise no.
        """
        for driver in self.drivers_graph.get_all_drivers():
            for d in self.drivers_graph.get_all_drivers():
                if not self.drivers_graph.has_edge(driver, d) and self.are_drivers_dependent(driver, d):
                    self.drivers_graph.add_edge(driver, d)
