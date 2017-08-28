# -*- coding: utf-8 -*-
# !/bin/env python
"""
Comparator classes are found here.
"""

import logging
from datetime import datetime
from collections import namedtuple
import time

from Heuristics import ShortestPathTrafficFree, RealGPS
from optimizedGPS import options
from utils.utils import SafeOpen, around

__all__ = ["Comparator", "MultipleGraphComparator", "LowerBound", "UpperBound", "BoundsHandler", "ResultsHandler"]

log = logging.getLogger(__name__)

Graphs = namedtuple("Graphs", ["graph", "drivers_graph"])


class Comparator(object):
    """
    Object for comparing several algorithms
    """
    def __init__(self):
        self.algorithms = []  # algorithms

        self.values = {}
        self.running_times = {}
        self.status = {}
        self.graphs = Graphs(None, None)

    def set_graphs(self, graph, drivers_graph):
        self.graphs = Graphs(graph, drivers_graph)

    def reinitialize(self):
        self.values = {}
        self.running_times = {}
        self.status = {}

    def append_algorithm(self, algorithm, *arguments, **kwargs):
        if algorithm.__name__ in options.KNOWN_PROBLEMS + options.KNOWN_HEURISTICS:
            self.algorithms.append(options.ALGO(algorithm, arguments, kwargs))
        else:
            log.warning("Algorithm %s not known. To allow it, modify your options.py file",
                        algorithm.__name__)

    def solve(self):
        """ solve the stored algorithms on the set input
        """
        for algo in self.algorithms:
            log.info("algorithm %s is being solved" % algo.algo.__name__)
            a = algo.algo(self.graphs.graph, self.graphs.drivers_graph, *algo.args, **algo.kwargs)
            try:
                start = time.time()
                a.solve()
                running_time = time.time() - start
                self.values.setdefault(algo.algo.__name__, a.get_optimal_value())
                self.running_times.setdefault(algo.algo.__name__, running_time)
                self.status.setdefault(algo.algo.__name__, a.get_status())
            except Exception:
                self.values.setdefault(algo.algo.__name__, None)
                self.running_times.setdefault(algo.algo.__name__, None)
                self.status.setdefault(algo.algo.__name__, options.FAILED)

    def compare(self):
        """ Compute some results about the given algorithms:
            value, running time, status
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
    """
    Compare different algorithms on several inputs
    """
    def __init__(self):
        super(MultipleGraphComparator, self).__init__()
        self.graphs_list = []
        self.__file = 'output/results/%s-%s.csv' % (self.__class__.__name__, datetime.now().strftime('%Y%m%d-%H%M%S'))

    def append_graphs(self, *graphs):
        """
        Graphs parameters should be tuple of one graph and one drivers' graph
        """
        for graph in graphs:
            self.graphs_list.append(Graphs(graph[0], graph[1]))

    def delete_graphs(self):
        self.graphs_list = []

    def compare(self):
        """
        Compare on every inputs
        """
        res = []
        for graph in self.graphs_list:
            self.set_graphs(graph.graph, graph.drivers_graph)
            res.append(super(MultipleGraphComparator, self).compare())
            self.reinitialize()
        return res

    def get_algorithms(self):
        return map(lambda el: el.algo.__name__, self.algorithms)

    def write_into_file(self, results):
        """
        Write the obtained results into a file
        """
        with SafeOpen(self.__file, 'w') as f:
            algos = self.get_algorithms()
            f.write('%s\n' % '\t\t'.join(['\t'.join([''] + algos) for _ in range(3)]))
            for i in range(len(results)):
                g, res = self.graphs_list[i].graph.name, results[i]
                f.write('%s\n' % '\t\t'.join(['\t'.join([g] + map(lambda a: str(res[a][i]), algos)) for i in range(3)]))
            f.write('%s\n' % '\t\t'.join(['\t'.join(['' for _ in range(len(algos) + 1)]) for _ in range(3)]))


class Bound(Comparator):
    """
    Bound handler
    """
    DEFAULT_BOUND = None

    def __init__(self, default=True):
        super(Bound, self).__init__()
        self.best_algo = None
        if default is True:
            self.append_default_bound()

    def reinitialize(self):
        super(Bound, self).reinitialize()
        self.best_algo = None

    def set_best_bound(self):
        pass

    def append_bound(self, algorithm, *args, **kwards):
        self.algorithms.append(options.ALGO(algorithm, args, kwards))

    def append_default_bound(self):
        if self.DEFAULT_BOUND is None:
            log.error("Default bound is None")
            raise Exception("Default bound is None")
        self.append_bound(self.DEFAULT_BOUND)

    # Bounds values
    def get_bound(self):
        return self.values.get(self.best_algo)

    # Bounds running times
    def get_bound_running_time(self):
        return self.running_times.get(self.best_algo)

    # bounds status
    def get_bound_status(self):
        return options.STATUS.get(self.status.get(self.best_algo))

    def get_best_algo(self):
        return self.best_algo


class LowerBound(Bound):
    """
    For lower bound
    """
    DEFAULT_BOUND = ShortestPathTrafficFree

    def set_best_bound(self):
        try:
            self.best_algo = min(
                filter(lambda a: self.status[a] in [options.TIMEOUT, options.SUCCESS], self.values.iterkeys()),
                key=lambda a: self.values[a]
            )
        except ValueError:
            log.warning("No problems has been solved successfully yet")


class UpperBound(Bound):
    """
    For upper bound
    """
    DEFAULT_BOUND = RealGPS

    def set_best_bound(self):
        try:
            self.best_algo = max(
                filter(lambda a: self.status[a] in [options.TIMEOUT, options.SUCCESS], self.values.iterkeys()),
                key=lambda a: self.values[a]
            )
        except ValueError:
            log.warning("No problems has been solved successfully yet")


class BoundsHandler(object):
    """
    Handle the upper and lower bounds
    """
    def __init__(self, default=True):
        self.lower = LowerBound(default=default)
        self.upper = UpperBound(default=default)

    def set_graphs(self, graph, drivers_graph):
        self.lower.set_graphs(graph, drivers_graph)
        self.upper.set_graphs(graph, drivers_graph)

    def reinitialize(self):
        self.lower.reinitialize()
        self.upper.reinitialize()

    def append_lower_bound(self, algorithm, *args, **kwargs):
        self.lower.append_bound(algorithm, *args, **kwargs)

    def append_upper_bound(self, algorithm, *args, **kwargs):
        self.upper.append_bound(algorithm, *args, **kwargs)

    def compute_bounds(self):
        for a in [self.lower, self.upper]:
            a.solve()
            a.set_best_bound()

    def get_lower_bound(self):
        return self.lower.get_bound()

    def get_upper_bound(self):
        return self.upper.get_bound()

    # Bounds running times
    def get_lower_bound_running_time(self):
        return self.lower.get_bound_running_time()

    def get_upper_bound_running_time(self):
        return self.upper.get_bound_running_time()

    # bounds status
    def get_lower_bound_status(self):
        return self.lower.get_bound_status()

    def get_upper_bound_status(self):
        return self.upper.get_bound_status()


class ResultsHandler(MultipleGraphComparator, BoundsHandler):
    """
    Compare several algorithm to lower and upper bounds on different inputs
    """
    def __init__(self, default=True):
        MultipleGraphComparator.__init__(self)
        BoundsHandler.__init__(self, default=default)

    def set_graphs(self, graph, drivers_graph):
        MultipleGraphComparator.set_graphs(self, graph, drivers_graph)
        BoundsHandler.set_graphs(self, graph, drivers_graph)

    def reinitialize(self):
        MultipleGraphComparator.reinitialize(self)
        BoundsHandler.reinitialize(self)

    def compare(self):
        res = []
        for graph in self.graphs_list:
            self.set_graphs(graph.graph, graph.drivers_graph)
            r = super(MultipleGraphComparator, self).compare()
            self.compute_bounds()
            r.setdefault(
                options.LOWER_BOUND_LABEL,
                (
                    around(self.get_lower_bound()),
                    around(self.get_lower_bound_running_time()),
                    self.get_lower_bound_status()
                )
            )
            r.setdefault(
                options.UPPER_BOUND_LABEL,
                (
                    around(self.get_upper_bound()),
                    around(self.get_upper_bound_running_time()),
                    self.get_upper_bound_status()
                )
            )
            res.append(r)
            self.reinitialize()
        return res

    def get_algorithms(self):
        return [options.LOWER_BOUND_LABEL] + super(ResultsHandler, self).get_algorithms() + [options.UPPER_BOUND_LABEL]
