# -*- coding: utf-8 -*-
# !/bin/env python

from Problem import Model
from gurobipy import GRB, quicksum, GurobiError
import logging
import sys

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
                    quicksum(self.graph.getTimeCongestionFunction(*edge)(self.S[edge, driver] - self.S[edge, d])
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
                if var.X == 1.0:
                    self.addOptimalPathToDriver(driver.to_tuple(), path)
        else:
            return {}


class ColumnGenerationAroundShortestPath(ContinuousTimeModel):
    def __init__(self, graph, timeout=sys.maxint, horizon=1000, binary=True):
        if not binary:
            log.error("Not implemented yet")
            raise NotImplementedError("Not implemented yet")
        self.values = []
        self.drivers = {}
        self.paths_iterator = {}
        super(ColumnGenerationAroundShortestPath, self).__init__(graph, timeout=timeout, horizon=horizon, binary=binary)

    def initialize_drivers(self):
        for driver in self.graph.getAllUniqueDrivers():
            self.drivers[driver] = set()
            self.paths_iterator[driver] = self.graph.get_all_paths_without_cycle(driver.start, driver.end)
            self.drivers[driver].add(self.paths_iterator[driver].next())

    def generateNewColumn(self, driver, path):
        try:
            self.drivers[driver].add(path)
            self.addVariable(driver, path)
            self.addConstraint(driver, path)
        except KeyError:
            log.error("Driver %s doesn't exist in model %s", str(driver.to_tuple()), self.__class__.__name__)
            raise KeyError("Driver %s doesn't exist in model %s" % (str(driver.to_tuple()), self.__class__.__name__))

    def addVariable(self, driver, path):
        self.z[driver, path] = self.model.addVar(0.0, name='z[%s,%s]' % (str(path), str(driver)),
                                                 vtype=self.vtype)
        self.model.update()

    def addConstraint(self, driver, path):
        log.info("ADDING new Constraints ...")

        # remove the constraint
        try:
            self.model.remove(self.model.getConstrByName("One-path constraint for driver %s" % str(driver)))
        except GurobiError as e:
            log.error("No one-path constraint for driver %s", str(driver))
            print e
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

    def stopIteration(self):
        return len(self.values) < 2 or self.values[-1] != self.values[-2]

    def getObj(self):
        try:
            self.model.ObjVal
        except GurobiError:
            log.warning("problem has not been solved yet")
            return sys.maxint

    def getDriverOptimalPath(self, driver):
        for path in self.drivers[driver]:
            if self.z[path, driver].X == 1.0:
                return path

    def driverHasBeenOnEdge(self, driver, edge):
        return self.x[edge, driver].X == 1.0

    def getEdgeWorstTraffic(self, edge):
        worst_traffic = 0
        for driver in filter(lambda d: self.driverHasBeenOnEdge(d, edge), self.drivers):
            starting_time, traffic = self.S[edge, driver].X, 1
            for d in filter(lambda d: self.driverHasBeenOnEdge(d, edge), self.drivers):
                if self.S[edge, d].X <= starting_time and self.E[edge, d].X >= starting_time:
                    traffic += 1
            worst_traffic = max(worst_traffic, traffic)
        return worst_traffic

    def getWorstTrafficEdge(self):
        value, edge = 0, None
        for e in self.graph.edges():
            traffic = self.getEdgeWorstTraffic(e)
            if traffic > value:
                value = traffic
                edge = e
        return edge

    def getDriversOnEdge(self, edge):
        for driver in self.drivers:
            if self.driverHasBeenOnEdge(driver, edge):
                yield driver

    def getDrivingTime(self, driver):
        for node in self.graph.predecessors(driver.end):
            edge = (node, driver.end)
            if self.E[edge, driver].X > 0:
                return self.E[edge, driver].X

    def getLowerBoundDrivingTime(self, driver):
        path = self.getDriverOptimalPath(driver)
        return sum(self.graph.getTimeCongestionFunction(path[i], path[i + 1])(0)
                   for i in range(len(path) - 1))

    def getWorstDriver(self):
        edge = self.getWorstTrafficEdge()
        wasted_time, driver = 0, None
        for d in self.getDriversOnEdge(edge):
            m = self.getLowerBoundDrivingTime(d)
            wt = (self.getDrivingTime(d) - m) / m
            if wt > wasted_time:
                wasted_time = wt
                driver = d
        return driver

    def getBestGapConstraint(self):
        """ find worst driver on worst path
        """
        driver = self.getWorstDriver()
        return driver, self.paths_iterator[driver].next()

    def optimizeOneStep(self):
        super(ColumnGenerationAroundShortestPath, self).optimize()
        self.values.append(self.getObj())

    def optimize(self):
        while not self.stopIteration():
            self.optimizeOneStep()
            self.generateNewColumn(*self.getBestGapConstraint())
