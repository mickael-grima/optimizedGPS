# -*- coding: utf-8 -*-
# !/bin/env python

__all__ = ['Driver']


class Driver(object):
    """
    Represent a Driver
    """
    def __init__(self, start, end, time):
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

    def to_tuple(self):
        """
        Transform Driver to a tuple (starting node, ending node, starting time)

        :return: tuple
        """
        return self.start, self.end, self.time

    def __str__(self):
        return str(self.to_tuple())
