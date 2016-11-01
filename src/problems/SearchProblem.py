# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.FiniteHorizonSimulator import FiniteHorizonSimulator
from Problem import SimulatorProblem
import sys
import logging
import time

log = logging.getLogger(__name__)


class BacktrackingSearch(SimulatorProblem):
    """ class to run a backtracking algorithm using a "finite horizon" simulator

        WARNING: we always handle minimum optimization problem
    """

    def __init__(self, graph, allowed_paths=[], initial_value=sys.maxint, timeout=sys.maxint):
        super(BacktrackingSearch, self).__init__(timeout=timeout)
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
                        log.warning("Problem %s timed out", self.__class__.__name__)
                        self.__timed_out = True
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
                    self.setOptimalSolution()
