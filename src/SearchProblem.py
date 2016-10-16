# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.FiniteHorizonSimulator import FiniteHorizonSimulator
from problems.Problem import Problem
import sys
import logging
import time

log = logging.getLogger(__name__)


class BacktrackingSearch(Problem):
    """ class to run a backtracking algorithm using a "finite horizon" simulator

        WARNING: we always handle minimum optimization problem
    """

    def __init__(self, graph, name='', allowed_paths=[], initial_value=sys.maxint, timeout=sys.maxint):
        super(BacktrackingSearch, self).__init__(name=name or self.__class__.__name__, timeout=timeout)
        self.simulator = FiniteHorizonSimulator(graph, allowed_paths=allowed_paths)
        # initial value
        self.value = initial_value
        self.step = 0
        self.cut = 0

    def backtrack(self):
        self.simulator.previous()

    def simulate(self, timeout=sys.maxint):
        self.step += 1
        self.cut += 1
        t = time.time()
        if timeout > 0:
            if self.simulator.has_next():
                for possibility in self.simulator.iter_possibilities():
                    if timeout <= 0:
                        break
                    # save state and update next edges
                    self.simulator.save_current_state()
                    self.simulator.updateNextEdges(possibility)

                    # next and then previous
                    self.simulator.next()
                    value = self.simulator.get_value()
                    if value < self.value:
                        dt = time.time() - t
                        self.simulate(timeout=timeout - dt)
                        self.cut -= 1
                    self.backtrack()
            else:
                value = self.simulator.get_value()
                if value < self.value:
                    self.value = value
                    self.opt_solution = self.simulator.get_current_solution()

    def solve(self):
        super(BacktrackingSearch, self).solve()
        t = time.time()
        self.simulate(timeout=self.timeout)
        self.running_time = time.time() - t
        log.info("-------------- %s: Solve TERMINATED --------------" % self.name)
