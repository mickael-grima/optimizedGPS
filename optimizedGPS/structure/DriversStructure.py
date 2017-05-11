"""
If an edge is unreachable by driver, this information should be stored in this class.
For each edge and each driver, the time interval in which the driver can be on the edge should be stored here as well.
"""
import sys
from collections import defaultdict, namedtuple

import networkx as nx

Interval = namedtuple("Interval", ["lower", "upper"])


class DriversStructure(object):
    def __init__(self, graph, drivers_graph, horizon=sys.maxint):
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.horizon = horizon

        self.unreachable_edges = defaultdict(lambda: defaultdict(lambda: 0))
        self.safety_intervals = defaultdict(lambda: defaultdict(lambda: Interval(0, horizon)))
        self.presence_intervals = defaultdict(lambda: defaultdict(lambda: Interval(horizon, horizon)))

    def set_unreachable_edge_to_driver(self, driver, edge):
        self.unreachable_edges[driver][edge] = 1
        if driver in self.safety_intervals and edge in self.safety_intervals[driver]:
            del self.safety_intervals[driver][edge]
        if driver in self.presence_intervals and edge in self.presence_intervals[driver]:
            del self.presence_intervals[driver][edge]

    def set_safety_interval_to_driver(self, driver, edge, interval):
        """
        Add a safety interval to driver for edge.
        Only reachable edge should be added.

        A safety interval is a time interval outside which we are sure the driver can't be present on edge.
        """
        assert(all(map(lambda i: isinstance(i, int), interval)))
        self.safety_intervals[driver][edge] = Interval(min(interval[0], self.horizon), min(interval[1], self.horizon))

    def set_presence_interval_to_driver(self, driver, edge, interval):
        """
        Add a presence interval to driver for edge.
        Only reachable edge should be added.

        A presence interval is a time interval in which we are sure the driver is present on edge.
        """
        assert(all(map(lambda i: isinstance(i, int), interval)))
        self.presence_intervals[driver][edge] = Interval(min(interval[0], self.horizon), min(interval[1], self.horizon))

    def is_edge_reachable_by_driver(self, driver, edge):
        return self.unreachable_edges[driver][edge] != 1

    def get_safety_interval(self, driver, edge):
        start, end = self.safety_intervals[driver][edge]
        if start >= self.horizon:
            return Interval(self.horizon, self.horizon)
        elif end >= self.horizon:
            return Interval(start, self.horizon)
        else:
            return Interval(start, end)

    def get_presence_interval(self, driver, edge):
        start, end = self.presence_intervals[driver][edge]
        if start >= self.horizon:
            return Interval(self.horizon, self.horizon)
        elif end >= self.horizon:
            return Interval(start, self.horizon)
        else:
            return Interval(start, end)

    def get_largest_safety_interval_before_end(self, driver):
        """
        Considering every edge before the end and we return the minimal starting time and the maximum ending time
        """
        start, end = None, None
        for pred in self.graph.predecessors_iter(driver.end):
            s, e = self.get_safety_interval(driver, (pred, driver.end))
            start = min(start if start is not None else self.horizon, s) if s is not None else None
            end = max(end if end is not None else 0, e) if e is not None else None
        return start, end

    def get_largest_safety_interval_after_start(self, driver):
        """
        Considering every edge after the start and we return the minimal starting time and the maximum ending time
        """
        start, end = None, None
        for succ in self.graph.successors_iter(driver.start):
            s, e = self.get_safety_interval(driver, (driver.start, succ))
            start = min(start if start is not None else self.horizon, s) if s is not None else None
            end = max(end if end is not None else 0, e) if e is not None else None
        return start, end

    def are_edges_time_connected_for_driver(self, driver, edge_source, edge_target):
        """
        Return True if the safety interval for edge source intersect the safety interval for edge target,
        and if the safety interval for edge source starts and ends before the one for edge target.
        Otherwise return False.

        Indeed if the intersection is empty, driver can't driver from edge source to edge target
        """
        source_interval = self.get_safety_interval(driver, edge_source)
        target_interval = self.get_safety_interval(driver, edge_target)
        if not self.graph.has_edge(*edge_source) or not self.graph.has_edge(*edge_target):
            return False
        if edge_source[1] != edge_target[0]:
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
        nexts = set(
            filter(
                lambda e: self.is_edge_reachable_by_driver(driver, e),
                map(lambda s: (driver.start, s), self.graph.successors_iter(driver.start))
            )
        )
        while len(nexts) > 0:
            edge = nexts.pop()
            yield edge
            visited.add(edge)
            for succ in self.graph.successors_iter(edge[1]):
                next_edge = (edge[1], succ)
                if next_edge in visited:
                    continue
                if self.are_edges_time_connected_for_driver(driver, edge, next_edge):
                    nexts.add(next_edge)

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

    def split_drivers_graph(self):
        return nx.connected_component_subgraphs(self.drivers_graph)
