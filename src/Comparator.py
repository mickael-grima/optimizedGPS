# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple
import logging
log = logging.getLogger(__name__)

ALGO = namedtuple('algo', ['algo', 'args', 'kwards'])


class Comparator(object):
    def __init__(self):
        self.algorithms = []  # algorithm

        self.values = {}
        self.running_times = {}

    def setGraph(self, graph):
        self.graph = graph

    def reinitialize(self):
        self.values = {}
        self.running_times = {}

    def appendAlgorithm(self, algo, *arguments, **kwards):
        self.algorithms.append(ALGO(algo, arguments, kwards))

    def solve(self):
        """ solve algo stored
        """
        for algo in self.algorithms:
            log.info("algorithm %s is being solved" % algo.algo.__name__)
            a = algo.algo(self.graph, *algo.args, **algo.kwards)
            a.solve()
            self.values.setdefault(algo.algo.__name__, a.value)
            self.running_times.setdefault(algo.algo.__name__, a.running_time)

    def compare(self):
        """ Compute some results about the given algorithms
            value, running time
        """
        self.solve()
        res = {}  # 'optimal' for optimal algo, else index in the list
        for algo in self.algorithms:
            res.setdefault(
                algo.algo.__name__,
                (self.values[algo.algo.__name__], self.running_times[algo.algo.__name__])
            )
        return res


class MultipleGraphComparator(Comparator):
    def __init__(self):
        super(MultipleGraphComparator, self).__init__()
        self.graphs = []
        self.algorithms = []

    def appendGraphs(self, *graphs):
        for graph in graphs:
            self.graphs.append(graph)

    def compare(self):
        res = []
        for graph in self.graphs:
            self.setGraph(graph)
            res.append(super(MultipleGraphComparator, self).compare())
            self.reinitialize()
        return res
