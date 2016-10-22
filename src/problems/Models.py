# -*- coding: utf-8 -*-
# !/bin/env python

from Problem import Model
from gurobipy import GRB, quicksum
import logging
import sys

log = logging.getLogger(__name__)


class ContinuousTimeModel(Model):
    def __init__(self, graph, timeout=sys.maxint):
        super(ContinuousTimeModel, self).__init__(graph, timeout=timeout, NumericFocus=3)
        self.drivers = list(self.graph.getAllUniqueDrivers())

        self.buildModel()

    def buildVariables(self):
        # add here variables
        log.info("ADDING variables ...")
        self.z = {}  # paths' variables
        self.S = {}  # starting time variables
        self.E = {}  # ending time variables

        count = {'z': 0, 'S': 0, 'E': 0}
        for driver in self.drivers:
            for path in self.graph.getAllPathsWithoutCycle(driver.start, driver.end):
                self.z[path, driver] = self.model.addVar(name='z[%s,%s]' % (str(path), str(driver)),
                                                         vtype=GRB.BINARY)
                count['z'] += 1
            for edge in self.graph.getAllEdges():
                self.S[edge, driver] = self.model.addVar(0.0, name='S[%s,%s]' % (str(edge), str(driver)))
                count['S'] += 1
                self.E[edge, driver] = self.model.addVar(0.0, name='E[%s,%s]' % (str(edge), str(driver)))
                count['E'] += 1

        super(ContinuousTimeModel, self).buildVariables()
        log.info("Variables ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in count.iteritems()))

    def big_M(self):
        # TODO
        return 1000

    def horizon(self):
        return 1000

    def buildConstraints(self):
        log.info("ADDING Constraints ...")

        count = {'one-path-constraint': 0, 'initial-conditions': 0, 'non-visited-edges-constraints': 0,
                 'visited-edges-constraints': 0, 'transfert-constraints': 0, 'ending-time-constraints': 0}
        for driver in self.drivers:
            # add one path constraint
            self.model.addConstr(
                quicksum(self.z[path, driver]
                         for path in self.graph.getAllPathsWithoutCycle(driver.start, driver.end)) == 1,
                "One-path constraint for driver %s" % str(driver)
            )
            count['one-path-constraint'] += 1
            # initial conditions
            self.model.addConstr(
                quicksum(self.S[(driver.start, t), driver]
                         for t in self.graph.getSuccessors(driver.start)) == driver.time + 1,
                "Initial conditions for driver %s" % str(driver)
            )
            count['initial-conditions'] += 1
            for edge in self.graph.getAllEdges():
                # non visited edges constraint
                self.model.addConstr(
                    self.S[edge, driver] <= self.horizon() *
                    quicksum(self.z[path, driver]
                             for path in self.graph.getAllPathsWithoutCycle(driver.start, driver.end)
                             if self.graph.isEdgeInPath(edge, path))
                )
                count['non-visited-edges-constraints'] += 1
                # visited edges constraint
                self.model.addConstr(
                    self.S[edge, driver] >=
                    quicksum(self.z[path, driver]
                             for path in self.graph.getAllPathsWithoutCycle(driver.start, driver.end)
                             if self.graph.isEdgeInPath(edge, path))
                )
                count['visited-edges-constraints'] += 1
                # ending time constraints
                self.model.addConstr(
                    self.E[edge, driver] + self.big_M() *
                    (1 - quicksum(self.z[path, driver]
                                  for path in self.graph.getAllPathsWithoutCycle(driver.start, driver.end)
                                  if self.graph.isEdgeInPath(edge, path))) >=
                    quicksum(self.S[(edge[1], n), driver]
                             for n in self.graph.getSuccessors(edge[1])),
                    "Ending time equation for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['ending-time-constraints'] += 1
                # transfert equation
                self.model.addConstr(
                    self.E[edge, driver] - self.S[edge, driver] +
                    self.big_M() *
                    (1 - quicksum(self.z[path, driver]
                                  for path in self.graph.getAllPathsWithoutCycle(driver.start, driver.end)
                                  if self.graph.isEdgeInPath(edge, path))) >=
                    quicksum(self.graph.getTimeCongestionFunction(*edge)(self.S[edge, driver] - self.S[edge, d])
                             for d in self.drivers),
                    "Transfert equation for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['transfert-constraints'] += 1

        log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in count.iteritems()))

    def setObjective(self):
        self.model.setObjective(
            quicksum(self.E[(n, driver.end), driver]
                     for driver in self.drivers for n in self.graph.getPredecessors(driver.end)),
            GRB.MINIMIZE
        )
        log.info("Objective SETTED")

    def setOptimalSolution(self):
        for (path, driver), var in self.z.iteritems():
            if var.X == 1.0:
                self.addOptimalPathToDriver(driver.to_tuple(), path)
