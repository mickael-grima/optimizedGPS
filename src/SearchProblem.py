# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.FiniteHorizonSimulator import FiniteHorizonSimulator
import sys
import logging

log = logging.getLogger(__name__)


class BacktrackingSearch():
    """ class to run a backtracking algorithm using a "finite horizon" simulator

        WARNING: we always handle minimum optimization problem
    """

    def __init__(self, graph, allowed_paths=[], initial_value=sys.maxint):
        self.simulator = FiniteHorizonSimulator(graph)
        # initial value
        self.current_value = initial_value
        self.step = 0
        self.cut = 0

    def backtrack(self):
        self.simulator.previous()

    def simulate(self):
        self.step += 1
        self.cut += 1
        if self.simulator.has_next():
            for possibility in self.simulator.iter_possibilities():
                # save state and update next edges
                self.simulator.save_current_state()
                self.simulator.updateNextEdges(possibility)

                # next and then previous
                self.simulator.next()
                value = self.simulator.get_total_time()
                if value < self.current_value:
                    self.simulate()
                    self.cut -= 1
                self.backtrack()
        else:
            value = self.simulator.get_total_time()
            self.current_value = min(value, self.current_value)
