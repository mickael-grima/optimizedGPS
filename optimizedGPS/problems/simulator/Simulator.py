# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""
import logging
import sys
import time
from collections import defaultdict, namedtuple

from sortedcontainers import SortedListWithKey

from optimizedGPS import options

__all__ = []

log = logging.getLogger(__name__)


class Simulator(object):
    """
    A simulator object return an edge-description and the starting time on each edge for each driver (+ a special
    starting time on a fake edge representing the fact that a driver leaves the edge)

    Every Subclasses have to implement the `get_next_edge()` method.
    This method moves the next driver to the next edge.
    How to obtain the next edge should be implemented in the subclass as well.
    """

    EXIT = '@@EXIT@@'
    Time = namedtuple('Time', ['object', 'time'])

    def __init__(self, graph, timeout=sys.maxint):
        """graph instance, containing drivers"""
        self.graph = graph
        """Maximum time allowed for simulating"""
        self.timeout = timeout
        """Status"""
        self.status = options.NOT_RUN
        """Which driver is entered in which edge at which time"""
        self.events = defaultdict(lambda: SortedListWithKey(key=lambda c: c.time))
        """Sorted list of tuple (driver, clock)"""
        self.clocks = SortedListWithKey(key=lambda c: c.time)
        self.initialize_clocks()

    def initialize_clocks(self):
        for driver in self.graph.get_all_drivers():
            self.add_clock(driver, driver.time)

    def add_clock(self, driver, time):
        """
        Add a clock for driver.
        This method should be preferred each time one wants to add a clock for a driver.

        :param driver: Driver object
        :param time: Current time in the simulation
        :return:
        """
        self.clocks.add(self.Time(object=driver, time=time))

    def add_event(self, driver, edge, time):
        """
        Save the event for driver on edge at time

        :param driver: driver object
        :param edge: edge in graph
        :param time: current time in the simulation
        :return:
        """
        self.events[driver].add(self.Time(object=edge, time=time))

    def get_current_edge(self, driver):
        """
        Return the edge which driver is currently

        :param driver: driver object
        """
        return self.events[driver][-1].object if len(self.events[driver]) > 0 else None

    def get_next_edge(self, driver):
        """
        Return the next edge for driver.
        Should be implemented in subclasses.

        :param driver: Driver object
        """
        message = "Not implemented yet"
        log.error(message)
        raise NotImplementedError(message)

    def get_next_driver(self):
        """
        Return the next driver respecting the clocks order
        """
        return self.clocks[0].object

    def get_waiting_time(self, edge, traffic):
        """
        Compute and return the current waiting time on this edge.

        :param edge: edge in graph
        :param traffic: traffic supposed on this edge
        """
        return self.graph.get_congestion_function(*edge)(traffic)

    def move_driver(self, driver, current_time, current_edge=None, next_edge=None):
        """
        Move driver from current_edge to next edge at time current_time.
        Update every simulator's instances:
          - add event for driver on next edge at time current time
          - compute new time when the driver should leave the next edge
          - delete the previous time we have for driver in self.clocks instance

        :param driver: driver object
        :param current_edge: current edge for driver
        :param current_time: current time in the simulation
        :param next_edge: next edge for driver
        """
        if self.clocks[0].object != driver:
            raise KeyError("driver %s shouldn't be next" % str(driver))
        if next_edge is None:
            if current_edge is None:
                message = "Driver %s has no current edge and no next edge. He should be deleted from data" % str(driver)
                log.warning(message)
                self.add_event(driver, (driver.start, self.EXIT), current_time)
            else:
                self.add_event(driver, (current_edge[1], self.EXIT), current_time)
        else:
            if current_edge is not None and current_edge[1] != next_edge[0]:
                raise Exception("current edge %s and next edge %s are not connected"
                                % (str(current_edge), str(next_edge)))
            self.add_event(driver, next_edge, current_time)
            waiting_time = self.get_waiting_time(next_edge, self.get_traffic(next_edge, current_time))
            self.add_clock(driver, current_time + waiting_time)
        del self.clocks[0]

    def has_next(self):
        """
        Return True if at least one driver is still driving on graph
        """
        return len(self.clocks) > 0

    def next(self):
        """
        Find the next driver to move and move him to his next edge
        """
        driver, current_time = self.clocks[0]
        self.move_driver(
            driver,
            current_time,
            self.get_current_edge(driver),
            self.get_next_edge(driver)
        )

    def simulate(self):
        """
        From the input, we simulate everything to obtain an edge-description and starting time on every visited edges
        for each driver.
        """
        ct = time.time()
        while self.has_next():
            self.next()
            if time.time() - ct >= self.timeout:
                self.status = options.TIMEOUT
                return
        self.status = options.SUCCESS

    def get_maximum_driving_time(self, drivers=None):
        """
        Return the worst driving time
        If drivers is not None, we just consider the drivers inside drivers
        """
        if drivers is None:
            return max(self.events.itervalues(), key=lambda e: e[-1].time if len(e) > 0 else 0)[-1].time
        else:
            return max(
                map(lambda d: self.events[d], filter(lambda d: d in drivers, self.events.iterkeys())),
                key=lambda e: e[-1].time if len(e) > 0 else 0
            )[-1].time

    def get_sum_driving_time(self, drivers=None):
        """
        Return the sum of every driving time
        """
        if drivers is None:
            return sum(map(lambda e: e[-1].time - e[0].time, self.events.itervalues()))
        else:
            return sum(map(
                lambda d: self.events[d][-1].time - self.events[d][0].time,
                filter(lambda d: d in drivers, self.events.iterkeys())
            ))

    def get_sum_ending_time(self, drivers=None):
        """
        Return the sum of ending times
        """
        if drivers is None:
            return sum(map(lambda e: e[-1].time, self.events.itervalues()))
        else:
            return sum(map(
                lambda d: self.events[d][-1].time,
                filter(lambda d: d in drivers, self.events.iterkeys())
            ))

    def get_value(self):
        """
        return the default value, here the maximum of ending time
        """
        return self.get_sum_ending_time()

    def get_edge_description(self):
        """
        Return the current edge description
        """
        return {driver: tuple(map(lambda e: e.object[0], path_clocks))
                for driver, path_clocks in self.events.iteritems()}

    def iter_edge_description(self):
        """
        Iterate the current edge description
        """
        for driver, path_clocks in self.events.iteritems():
            yield driver, tuple(map(lambda e: e.object[0], path_clocks))

    def iter_edge_in_driver_path(self, driver):
        path = [edge for d, edge in self.iter_edge_description() if d == driver][0]
        for e in self.graph.iter_edges_in_path(path):
            yield e

    def get_starting_times(self, driver):
        """
        Return the dictionary of starting times on each visited edge by drivers

        :param driver: driver object
        """
        if driver not in self.events:
            message = "driver %s has not been simulated" % str(driver)
            log.error(message)
            raise KeyError(message)
        return {p.object: p.time for p in self.events[driver]}

    def get_ending_time(self, driver):
        """
        Return the time at which the driver reach @@EXIT@@

        :param driver: driver object
        :return:
        """
        for p in self.events[driver]:
            if p.object[-1] == self.EXIT:
                return p.time

    def get_driver_waiting_times(self, driver):
        """
        For each edge, compute the associated waiting time of driver

        :param driver: Driver object
        :return: dict
        """
        previous_edge = None
        waiting_times = {}
        starting_times = self.get_starting_times(driver)
        for edge in self.iter_edge_in_driver_path(driver):
            starting_time = starting_times[edge]
            waiting_times[edge] = starting_time
            if previous_edge is not None:
                waiting_times[previous_edge] = starting_time - waiting_times[previous_edge]
            previous_edge = edge
        if previous_edge in waiting_times:
            waiting_times[previous_edge] = self.get_ending_time(driver) - waiting_times[previous_edge]
        return waiting_times

    def get_traffic(self, edge, time):
        """
        Return the traffic on edge at time
        """
        traffic = 0
        for path_clocks in self.events.itervalues():
            i, visited = 0, False
            while i < len(path_clocks) - 1:
                if path_clocks[i].object == edge and path_clocks[i].time < time <= path_clocks[i + 1].time:
                    visited = True
                    break
                i += 1
            if path_clocks[i].object == edge and path_clocks[i].time < time:
                visited = True
            traffic += visited
        return traffic


class FromEdgeDescriptionSimulator(Simulator):
    """
    This Simulator simulate the edge-description and starting times from an edge_description
    """
    def __init__(self, graph, edge_description, timeout=sys.maxint):
        """For each driver, the path he has to follow"""
        self.edge_description = edge_description
        super(FromEdgeDescriptionSimulator, self).__init__(graph, timeout=timeout)

    def initialize_clocks(self):
        for driver in self.edge_description.iterkeys():
            self.add_clock(driver, driver.time)

    def get_next_edge(self, driver):
        if driver not in self.edge_description:
            message = "Driver %s doesn't have associated path" % str(driver)
            log.error(message)
            raise KeyError(message)
        current_edge = self.get_current_edge(driver)
        edge_iterator = self.graph.iter_edges_in_path(self.edge_description[driver])
        if current_edge is None:
            try:
                return edge_iterator.next()
            except StopIteration:
                return None
        while True:
            try:
                if edge_iterator.next() == current_edge:
                    try:
                        return edge_iterator.next()
                    except StopIteration:
                        return None
            except StopIteration:
                message = "Driver %s on edge %s which doesn't appear in given edge_description"\
                          % (str(driver), str(current_edge))
                log.error(message)
                raise StopIteration(message)
