# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple
import logging
log = logging.getLogger(__name__)

ALGO = namedtuple('algo', ['algo', 'args', 'kwards'])


class Comparator(object):
    def __init__(self):
        self.optimal = None  # optimal algorithm
        self.algorithms = []  # other algorithm

        self.values = []
        self.running_times = []

    def setGraph(self, graph):
        self.graph = graph

    def reinitialize(self):
        self.values = []
        self.running_times = []

    def setOptimalAlgorithm(self, algo, *arguments, **kwards):
        self.optimal = ALGO(algo, arguments, kwards)

    def appendAlgorithm(self, algo, *arguments, **kwards):
        self.algorithms.append(ALGO(algo, arguments, kwards))

    def solve(self):
        """ solve algo stored
        """
        if self.optimal is not None:
            log.info("Optimal algorithm is being solved")
            opt = self.optimal.algo(self.graph, *self.optimal.args, **self.optimal.kwards)
            opt.solve()
            self.values.append(opt.value)
            self.running_times.append(opt.running_time)
        i = 0
        for algo in self.algorithms:
            log.info("%sth algorithm is being solved" % i)
            a = algo.algo(self.graph, *algo.args, **algo.kwards)
            a.solve()
            self.values.append(a.value)
            self.running_times.append(a.running_time)
            i += 1

    def compare(self):
        """ Compute some results about the given algorithms
            value, running time
        """
        self.solve()
        res = {}  # 'optimal' for optimal algo, else index in the list
        if self.optimal is not None:
            res.setdefault('optimal', (self.values[0], self.running_times[0]))
        i = 1
        for algo in self.algorithms:
            res.setdefault(i, (self.values[i], self.running_times[i]))
            i += 1
        return res


class MultipleGraphComparator(Comparator):
    def __init__(self):
        super(MultipleGraphComparator, self).__init__()
        self.graphs = []
        self.optimal = None
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
