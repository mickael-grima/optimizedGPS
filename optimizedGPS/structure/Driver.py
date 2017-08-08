# -*- coding: utf-8 -*-
# !/bin/env python

__all__ = ['Driver']


"""
This script defines objects representing the drivers
"""


class Driver(object):
    """
    Represent a Driver. 3 properties are mandatory: starting time, starting and ending nodes.
    For continuous solution, a traffic weight can be specified: between 0 and 1
    """
    def __init__(self, start, end, time, traffic_weight=1):
        """
        starting node
        """
        self.start = start
        """
        ending node
        """
        self.end = end
        """
        starting time
        """
        self.time = time
        """
        Importance in the traffic computation
        """
        self.traffic_weight = traffic_weight

    def to_tuple(self):
        """
        Transform Driver to a tuple (starting node, ending node, starting time)

        :return: tuple
        """
        return self.start, self.end, self.time, self.traffic_weight

    def __str__(self):
        return str(self.to_tuple())
