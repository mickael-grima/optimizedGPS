# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.GPSSimulator import GPSSimulator


class Heuristics(object):
    """ We handle here the heuristics
        They will written as classmethod
        Each class variable should be a global variable
    """
    @classmethod
    def shortest_path(cls, graph):
        # Initialize the paths
        paths = {}
        for start, end, time, nb in graph.getAllDrivers():
            paths[graph.getPathsFromTo(start, end).next()] = {time: nb}
        simulator = GPSSimulator(graph, paths)

        # simulate
        while simulator.has_next():
            simulator.next()

        return simulator.get_total_time()
