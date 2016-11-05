# -*- coding: utf-8 -*-
# !/bin/env python

from Problem import Model, ColumnGenerationModel
from gurobipy import GRB, quicksum, GurobiError
import logging
import sys
from utils.tools import isclose

log = logging.getLogger(__name__)


class ContinuousTimeModel(Model):
    def __init__(self, graph, timeout=sys.maxint, horizon=1000, binary=True):
        super(ContinuousTimeModel, self).__init__(graph, timeout=timeout, NumericFocus=3)
        self.initialize_drivers()
        self.hor = horizon
        self.vtype = GRB.BINARY if binary else GRB.CONTINUOUS

        self.buildModel()

    def initialize_drivers(self):
        self.drivers = {driver: set(list(self.graph.get_all_paths_without_cycle(driver.start, driver.end)))
                        for driver in self.graph.getAllUniqueDrivers()}

    def buildVariables(self):
        # add here variables
        log.info("ADDING variables ...")
        self.z = {}  # paths' variables
        self.x = {}  # edges's variables
        self.S = {}  # starting time variables
        self.E = {}  # ending time variables

        count = {'z': 0, 'x': 0, 'S': 0, 'E': 0}
        for driver in self.drivers:
            for path in self.drivers[driver]:
                self.z[path, driver] = self.model.addVar(0.0, name='z[%s,%s]' % (str(path), str(driver)),
                                                         vtype=self.vtype)
                count['z'] += 1
            for edge in self.graph.edges():
                self.x[edge, driver] = self.model.addVar(0.0, name='x[%s,%s' % (str(edge), str(driver)))
                count['x'] += 1
                self.S[edge, driver] = self.model.addVar(0.0, name='S[%s,%s]' % (str(edge), str(driver)))
                count['S'] += 1
                self.E[edge, driver] = self.model.addVar(0.0, name='E[%s,%s]' % (str(edge), str(driver)))
                count['E'] += 1

        self.model.update()
        log.info("Variables ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in count.iteritems()))

    def horizon(self):
        return self.hor

    def buildConstraints(self):
        log.info("ADDING Constraints ...")

        count = {'one-path-constraint': 0, 'initial-conditions': 0, 'non-visited-edges-constraints': 0,
                 'visited-edges-constraints': 0, 'transfert-constraints': 0, 'ending-time-constraints': 0,
                 'edge-path-constraint': 0}
        for driver in self.drivers:
            # add one path constraint
            self.model.addConstr(
                quicksum(self.z[path, driver] for path in self.drivers[driver]) == 1,
                "One-path constraint for driver %s" % str(driver)
            )
            count['one-path-constraint'] += 1
            # initial conditions
            self.model.addConstr(
                quicksum(self.S[(driver.start, t), driver]
                         for t in self.graph.successors_iter(driver.start)) == driver.time + 1,
                "Initial conditions for driver %s" % str(driver)
            )
            count['initial-conditions'] += 1
            for edge in self.graph.edges():
                # edge path constraint
                self.model.addConstr(
                    self.x[edge, driver] ==
                    quicksum(self.z[path, driver] for path in self.drivers[driver]
                             if self.graph.is_edge_in_path(edge, path)),
                    "Relation edge-path for driver %s and edge %s" % (str(driver), str(edge))
                )
                count['edge-path-constraint'] += 1
                # non visited edges constraint
                self.model.addConstr(
                    self.S[edge, driver] <= self.horizon() * self.x[edge, driver]
                )
                count['non-visited-edges-constraints'] += 1
                # visited edges constraint
                self.model.addConstr(
                    self.S[edge, driver] >= self.x[edge, driver]
                )
                count['visited-edges-constraints'] += 1
                # ending time constraints
                self.model.addConstr(
                    self.E[edge, driver] + self.horizon() * (1 - self.x[edge, driver]) >=
                    quicksum(self.S[(edge[1], n), driver]
                             for n in self.graph.successors_iter(edge[1])),
                    "Ending time equation for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['ending-time-constraints'] += 1
                # transfert equation
                self.model.addConstr(
                    self.E[edge, driver] - self.S[edge, driver] + self.horizon() * (1 - self.x[edge, driver]) >=
                    quicksum(self.x[edge, driver] *
                             self.graph.getTimeCongestionFunction(*edge)(self.S[edge, driver] - self.S[edge, d])
                             for d in self.drivers),
                    "Transfert equation for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['transfert-constraints'] += 1

        log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in count.iteritems()))

    def setObjective(self):
        self.model.setObjective(
            quicksum(self.E[(n, driver.end), driver]
                     for driver in self.drivers for n in self.graph.predecessors(driver.end)),
            GRB.MINIMIZE
        )
        log.info("Objective SETTED")

    def setOptimalSolution(self):
        # TODO: what to do if not binary ?
        if self.vtype == GRB.BINARY:
            for (path, driver), var in self.z.iteritems():
                try:
                    if var.X == 1.0:
                        self.addOptimalPathToDriver(driver.to_tuple(), path)
                except:
                    continue
        else:
            return {}


class ColumnGenerationAroundShortestPath(ContinuousTimeModel, ColumnGenerationModel):
    def __init__(self, graph, timeout=sys.maxint, horizon=1000, binary=True):
        if not binary:
            log.error("Not implemented yet")
            raise NotImplementedError("Not implemented yet")
        super(ColumnGenerationAroundShortestPath, self).__init__(graph, timeout=timeout, horizon=horizon, binary=binary)

    def initialize_drivers(self):
        self.drivers = {}
        self.paths_iterator = {}
        for driver in self.graph.getAllUniqueDrivers():
            self.drivers[driver] = set()
            self.paths_iterator[driver] = self.graph.get_all_paths_without_cycle(driver.start, driver.end)
            self.drivers[driver].add(self.paths_iterator[driver].next())

    def generateNewColumn(self, driver, path):
        try:
            self.drivers[driver].add(path)
        except KeyError:
            log.error("Driver %s doesn't exist in model %s", str(driver.to_tuple()), self.__class__.__name__)
            raise KeyError("Driver %s doesn't exist in model %s" % (str(driver.to_tuple()), self.__class__.__name__))
        self.addVariable(driver, path)
        self.addConstraint(driver, path)

    def addInstance(self, driver, path):
        try:
            self.drivers[driver].add(path)
        except KeyError:
            log.error("Driver %s doesn't exist in model %s", str(driver.to_tuple()), self.__class__.__name__)
            raise KeyError("Driver %s doesn't exist in model %s" % (str(driver.to_tuple()), self.__class__.__name__))

    def addVariable(self, driver, path):
        self.z[path, driver] = self.model.addVar(0.0, name='z[%s,%s]' % (str(path), str(driver)),
                                                 vtype=self.vtype)
        self.model.update()

    def addConstraint(self, driver, path):
        log.info("ADDING new Constraints ...")

        # remove the constraint
        try:
            self.model.remove(self.model.getConstrByName("One-path constraint for driver %s" % str(driver)))
        except GurobiError:
            log.error("No one-path constraint for driver %s", str(driver))
            raise
        # add one path constraint
        self.model.addConstr(
            quicksum(self.z[path, driver] for path in self.drivers[driver]) == 1,
            "One-path constraint for driver %s" % str(driver)
        )
        for edge in self.graph.edges():
            # first remove constraint
            try:
                self.model.remove(self.model.getConstrByName("Relation edge-path for driver %s and edge %s"
                                                             % (str(driver), str(edge))))
            except GurobiError:
                log.error("No relation edge-path constraint for driver %s and edge %s", str(driver), str(edge))
                raise

            # edge path constraint
            self.model.addConstr(
                self.x[edge, driver] ==
                quicksum(self.z[path, driver] for path in self.drivers[driver]
                         if self.graph.is_edge_in_path(edge, path)),
                "Relation edge-path for driver %s and edge %s" % (str(driver), str(edge))
            )

        log.info("New Constraints ADDED for driver %s and path %s", str(driver.to_tuple()), str(path))

    def isComplete(self):
        """ True if every path have been added in the problem
        """
        return len(self.paths_iterator) == 0

    def driverHasBeenOnEdge(self, driver, edge):
        return isclose(self.x[edge, driver].X, 1.0)

    def getEdgeTrafficAt(self, edge, time):
        traffic = 0
        for d in filter(lambda d: self.driverHasBeenOnEdge(d, edge), self.drivers):
            if self.S[edge, d].X <= time and self.E[edge, d].X >= time:
                traffic += 1
        return traffic

    def getWorstDriver(self):
        worst_traffic, worst_driver = 0, None
        for driver in filter(lambda d: d in self.paths_iterator, self.drivers):
            for edge in self.graph.edges():
                if self.S[edge, driver].X > 0:
                    traffic = self.getEdgeTrafficAt(edge, self.S[edge, driver].X)
                    if traffic > worst_traffic:
                        worst_traffic = traffic
                        worst_driver = driver
        return worst_driver

    def getBestGapConstraintIndex(self):
        """ find worst driver on worst path
        """
        driver, path = None, None
        while all([not self.isComplete(), driver is None, path is None]):
            try:
                driver = self.getWorstDriver()
                path = self.paths_iterator[driver].next()
            except StopIteration:
                del self.paths_iterator[driver]
                continue
        return driver, path
