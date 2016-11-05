# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple
import logging
log = logging.getLogger(__name__)

ALGO = namedtuple('algo', ['algo', 'args', 'kwards'])


def around(number):
    return int(number * 1000) / 1000.


class Comparator(object):
    __SUCCESS = 0
    __FAILED = 1
    __TIMEOUT = 2

    __STATUS = {0: 'SUCCESS', 1: 'FAILED', 2: 'TIMEOUT'}

    def __init__(self):
        self.algorithms = []  # algorithm

        self.values = {}
        self.running_times = {}
        self.status = {}

    def setGraph(self, graph):
        self.graph = graph

    def reinitialize(self):
        self.values = {}
        self.running_times = {}
        self.status = {}

    def appendAlgorithm(self, algo, *arguments, **kwards):
        self.algorithms.append(ALGO(algo, arguments, kwards))

    def solve(self):
        """ solve algo stored
        """
        for algo in self.algorithms:
            log.info("algorithm %s is being solved" % algo.algo.__name__)
            a = algo.algo(self.graph, *algo.args, **algo.kwards)
            try:
                a.solve()
                self.values.setdefault(algo.algo.__name__, a.value)
                self.running_times.setdefault(algo.algo.__name__, a.running_time)
                if a.isTimedOut():
                    self.status.setdefault(algo.algo.__name__, self.__TIMEOUT)
                else:
                    self.status.setdefault(algo.algo.__name__, self.__SUCCESS)
            except:
                self.values.setdefault(algo.algo.__name__, None)
                self.running_times.setdefault(algo.algo.__name__, None)
                self.status.setdefault(algo.algo.__name__, self.__FAILED)

    def compare(self):
        """ Compute some results about the given algorithms
            value, running time
        """
        self.solve()
        res = {}  # 'optimal' for optimal algo, else index in the list
        for algo in self.algorithms:
            res.setdefault(
                algo.algo.__name__,
                (
                    around(self.values[algo.algo.__name__]),
                    around(self.running_times[algo.algo.__name__]),
                    self.__STATUS[self.status[algo.algo.__name__]]
                )
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
        res = {}
        for graph in self.graphs:
            self.setGraph(graph)
            res.setdefault(graph.name, super(MultipleGraphComparator, self).compare())
            self.reinitialize()
        return res
