# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from datetime import datetime

from Heuristics import ShortestPathTrafficFree, ShortestPathHeuristic
from optimizedGPS import options
from utils.utils import SafeOpen

__all__ = ["Comparator", "MultipleGraphComparator", "LowerBound", "UpperBound", "BoundsHandler", "ResultsHandler"]

log = logging.getLogger(__name__)


def around(number):
    if number is not None:
        return int(number * 1000) / 1000.
    else:
        return None


class Comparator(object):
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
        if algo.__class__.__name__ in options.KNOWN_PROBLEMS + options.KNOWN_HEURISTICS:
            self.algorithms.append(options.ALGO(algo, arguments, kwards))
        else:
            log.warning("Algorithm %s not known. To allow it, modifu your options.py file", algo.__class__.__name__)

    def solve(self):
        """ solve algo stored
        """
        for algo in self.algorithms:
            log.info("algorithm %s is being solved" % algo.algo.__name__)
            a = algo.algo(self.graph, *algo.args, **algo.kwards)
            try:
                a.solve()
                self.values.setdefault(algo.algo.__name__, a.getOptimalValue())
                self.running_times.setdefault(algo.algo.__name__, a.getRunningTime())
                if a.isTimedOut():
                    self.status.setdefault(algo.algo.__name__, options.TIMEOUT)
                else:
                    self.status.setdefault(algo.algo.__name__, options.SUCCESS)
            except:
                self.values.setdefault(algo.algo.__name__, None)
                self.running_times.setdefault(algo.algo.__name__, None)
                self.status.setdefault(algo.algo.__name__, options.FAILED)

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
                    options.STATUS[self.status[algo.algo.__name__]]
                )
            )
        return res


class MultipleGraphComparator(Comparator):
    def __init__(self):
        super(MultipleGraphComparator, self).__init__()
        self.graphs = []
        self.__file = 'output/results/%s-%s.csv' % (self.__class__.__name__, datetime.now().strftime('%Y%m%d-%H%M%S'))

    def appendGraphs(self, *graphs):
        for graph in graphs:
            self.graphs.append(graph)

    def deleteGraphs(self):
        self.graphs = []

    def compare(self):
        res = []
        for graph in self.graphs:
            self.setGraph(graph)
            res.append(super(MultipleGraphComparator, self).compare())
            self.reinitialize()
        return res

    def getAlgorithms(self):
        return map(lambda el: el.algo.__name__, self.algorithms)

    def writeIntoFile(self, results):
        with SafeOpen(self.__file, 'w') as f:
            algos = self.getAlgorithms()
            f.write('%s\n' % '\t\t'.join(['\t'.join([''] + algos) for _ in range(3)]))
            for i in range(len(results)):
                g, res = self.graphs[i].name, results[i]
                f.write('%s\n' % '\t\t'.join(['\t'.join([g] + map(lambda a: str(res[a][i]), algos)) for i in range(3)]))
            f.write('%s\n' % '\t\t'.join(['\t'.join(['' for _ in range(len(algos) + 1)]) for _ in range(3)]))


class Bound(Comparator):
    DEFAULT_BOUND = None

    def __init__(self, default=True):
        super(Bound, self).__init__()
        self.best_algo = None
        if default is True:
            self.appendDefaultBound()

    def reinitialize(self):
        super(Bound, self).reinitialize()
        self.best_algo = None

    def setBestBound(self):
        pass

    def appendBound(self, algorithm, *args, **kwards):
        self.algorithms.append(options.ALGO(algorithm, args, kwards))

    def appendDefaultBound(self):
        if self.DEFAULT_BOUND is None:
            log.error("Default bound is None")
            raise Exception("Default bound is None")
        self.appendBound(self.DEFAULT_BOUND)

    # Bounds values
    def getBound(self):
        return self.values.get(self.best_algo)

    # Bounds running times
    def getBoundRunningTime(self):
        return self.running_times.get(self.best_algo)

    # bounds status
    def getBoundStatus(self):
        return options.STATUS.get(self.status.get(self.best_algo))

    def getBestAlgo(self):
        return self.best_algo


class LowerBound(Bound):
    DEFAULT_BOUND = ShortestPathTrafficFree

    def setBestBound(self):
        try:
            self.best_algo = min(
                filter(lambda a: self.status[a] in [options.TIMEOUT, options.SUCCESS], self.values.iterkeys()),
                key=lambda a: self.values[a]
            )
        except ValueError:
            log.warning("No problems has been solved successfully yet")


class UpperBound(Bound):
    DEFAULT_BOUND = ShortestPathHeuristic

    def setBestBound(self):
        try:
            self.best_algo = max(
                filter(lambda a: self.status[a] in [options.TIMEOUT, options.SUCCESS], self.values.iterkeys()),
                key=lambda a: self.values[a]
            )
        except ValueError:
            log.warning("No problems has been solved successfully yet")


class BoundsHandler(object):
    def __init__(self, default=True):
        self.lower = LowerBound(default=default)
        self.upper = UpperBound(default=default)

    def setGraph(self, graph):
        self.lower.setGraph(graph)
        self.upper.setGraph(graph)

    def reinitialize(self):
        self.lower.reinitialize()
        self.upper.reinitialize()

    def appendLowerBound(self, algorithm, *args, **kwards):
        self.lower.appendBound(algorithm, *args, **kwards)

    def appendUpperBound(self, algorithm, *args, **kwards):
        self.upper.appendBound(algorithm, *args, **kwards)

    def computeBounds(self):
        for a in [self.lower, self.upper]:
            a.solve()
            a.setBestBound()

    def getLowerBound(self):
        return self.lower.getBound()

    def getUpperBound(self):
        return self.upper.getBound()

    # Bounds running times
    def getLowerBoundRunningTime(self):
        return self.lower.getBoundRunningTime()

    def getUpperBoundRunningTime(self):
        return self.upper.getBoundRunningTime()

    # bounds status
    def getLowerBoundStatus(self):
        return self.lower.getBoundStatus()

    def getUpperBoundStatus(self):
        return self.upper.getBoundStatus()


class ResultsHandler(MultipleGraphComparator, BoundsHandler):
    def __init__(self, default=True):
        MultipleGraphComparator.__init__(self)
        BoundsHandler.__init__(self, default=default)

    def setGraph(self, graph):
        MultipleGraphComparator.setGraph(self, graph)
        BoundsHandler.setGraph(self, graph)

    def reinitialize(self):
        MultipleGraphComparator.reinitialize(self)
        BoundsHandler.reinitialize(self)

    def compare(self):
        res = []
        for graph in self.graphs:
            self.setGraph(graph)
            r = super(MultipleGraphComparator, self).compare()
            self.computeBounds()
            r.setdefault(
                options.LOWER_BOUND_LABEL,
                (around(self.getLowerBound()), around(self.getLowerBoundRunningTime()), self.getLowerBoundStatus())
            )
            r.setdefault(
                options.UPPER_BOUND_LABEL,
                (around(self.getUpperBound()), around(self.getUpperBoundRunningTime()), self.getUpperBoundStatus())
            )
            res.append(r)
            self.reinitialize()
        return res

    def getAlgorithms(self):
        return [options.LOWER_BOUND_LABEL] + super(ResultsHandler, self).getAlgorithms() + [options.UPPER_BOUND_LABEL]
