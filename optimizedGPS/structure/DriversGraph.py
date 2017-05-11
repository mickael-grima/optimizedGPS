"""
Class representing the drivers inside a graph
"""
import networkx as nx

from Driver import Driver


class DriversGraph(nx.Graph):
    def __init__(self, *args, **kwargs):
        super(DriversGraph, self).__init__(*args, **kwargs)

    def add_node(self, driver, attr_dict=None, **kwargs):
        if isinstance(driver, Driver):
            super(DriversGraph, self).add_node(driver, attr_dict=attr_dict, **kwargs)
        else:
            raise TypeError("Only drivers are accepted as node")

    def has_driver(self, driver):
        return self.has_node(driver)

    def add_driver(self, driver, attr_dict=None, **kwargs):
        self.add_node(driver, attr_dict=attr_dict, **kwargs)

    def get_drivers(self, start, end, starting_time=None):
        """
        return the drivers from start to end with starting time if given
        """
        for driver in self.get_all_drivers():
            if driver.start == start and driver.end == end and (starting_time is None or driver.time == starting_time):
                yield driver

    def get_driver_property(self, driver, prop):
        """
        return the wanted property about the given driver

        :param driver: object driver
        :param prop: property to return
        :return: the wanted property
        """
        return self.node.get(driver, {}).get(prop)

    def get_all_drivers_from_starting_node(self, start):
        """
        Iterate every drivers starting at node `start`. A yielded driver is (start, end, starting_time, nb).
        """
        for driver in self.get_all_drivers():
            if driver.start == start:
                yield driver

    def get_all_drivers_to_ending_node(self, end):
        """
        Iterate every drivers ending at node `end`. A yielded driver is (start, end, starting_time, nb).
        """
        for driver in self.get_all_drivers():
            if driver.end == end:
                yield driver

    def remove_driver(self, driver):
        """
        Remove given driver.
        """
        self.remove_node(driver)

    def number_of_drivers(self):
        """
        Returns the number of drivers in graph
        """
        return self.number_of_nodes()

    def get_time_ordered_drivers(self):
        """
        Return a list of drivers sorted by starting time
        """
        return sorted(self.get_all_drivers(), key=lambda d: d.time)

    def get_all_drivers(self):
        return self.nodes_iter()
