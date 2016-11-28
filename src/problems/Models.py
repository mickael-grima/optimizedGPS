# -*- coding: utf-8 -*-
# !/bin/env python

from Problem import Model
from gurobipy import GRB, quicksum
import logging
import sys

log = logging.getLogger(__name__)


class BestPathTrafficModel(Model):
    def __init__(self, graph, timeout=sys.maxint, horizon=1000, binary=True):
        if not binary:
            log.error("Not implemented yet")
            raise NotImplementedError("Not implemented yet")
        super(BestPathTrafficModel, self).__init__(graph, timeout=timeout, NumericFocus=3)
        self.initialize_drivers()
        self.hor = horizon
        self.vtype = GRB.BINARY if binary else GRB.CONTINUOUS

        self.buildModel()

    def initialize_drivers(self):
        self.drivers = set(self.graph.getAllUniqueDrivers())

    def buildConstants(self):
        """ For each driver we find the edges belonging to his shortest path
        """
        self.X = {}
        for driver in self.drivers:
            if (driver.start, driver.end) not in self.X:
                self.X[driver.start, driver.end] = {}
                path = self.graph.get_shortest_path(driver.start, driver.end)
                for edge in self.graph.iter_edges_in_path(path):
                    self.X[driver.start, driver.end][edge] = 1

    def buildVariables(self):
        # add here variables
        log.info("ADDING variables ...")
        self.x = {}  # edges's variables
        self.S = {}  # starting time variables
        self.E = {}  # ending time variables
        self.y = {}
        self.z = None

        count = {'x': 0, 'S': 0, 'E': 0, 'z': 0}
        self.z = self.model.addVar(name='z')
        count['z'] += 1
        for edge in self.graph.edges():
            for driver in self.drivers:
                self.x[edge, driver] = self.model.addVar(0.0, name='x[%s,%s]' % (str(edge), str(driver)),
                                                         vtype=self.vtype)
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

        count = {'starting-edges': 0, 'ending-edges': 0, 'initial-conditions': 0, 'non-visited-edges-constraints': 0,
                 'visited-edges-constraints': 0, 'starting-ending-constraints': 0, 'transfert-constraints': 0,
                 'ending-time-constraints': 0, 'no-cycle-constraints': 0, 'difference-to-shortest-path': 0,
                 'difference-to-best-traffic': 0}

        for edge in self.graph.edges():
            self.model.addConstr(
                quicksum(self.x[edge, driver] - self.graph.getTrafficLimit(*edge) for driver in self.drivers) <=
                self.z,
                "difference to best traffic on edge %s" % str(edge)
            )
            count['difference-to-best-traffic'] += 1
        for driver in self.drivers:
            self.model.addConstr(
                quicksum(self.graph.getMinimumWaitingTime(*edge) *
                         (self.x[edge, driver] - self.X[driver.start, driver.end].get(edge, 0))
                         for edge in self.graph.edges()) <= self.z,
                "difference to shortest path"
            )
            count['difference-to-shortest-path'] += 1
            # starting edges constraints
            self.model.addConstr(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                "starting edges constraint for driver %s" % str(driver)
            )
            count['starting-edges'] += 1
            # ending edges constraints
            self.model.addConstr(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                "ending edges constraint for driver %s" % str(driver)
            )
            count['ending-edges'] += 1
            # initial conditions
            self.model.addConstr(
                quicksum(self.S[(driver.start, t), driver]
                         for t in self.graph.successors_iter(driver.start)) == driver.time + 1,
                "Initial conditions for driver %s" % str(driver)
            )
            count['initial-conditions'] += 1
            for node in self.graph.nodes():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.model.addConstr(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        "path constraint for driver %s on node %s" % (str(driver), str(node))
                    )
                    count['no-cycle-constraints'] += 1
                    # ending time constraints
                    self.model.addConstr(
                        quicksum(self.E[(n, node), driver] for n in self.graph.predecessors_iter(node)) <=
                        quicksum(self.S[(node, n), driver] for n in self.graph.successors_iter(node)),
                        "Ending time equation for driver %s on node %s" % (str(driver), str(node))
                    )
                    count['ending-time-constraints'] += 1
            for edge in self.graph.edges():
                # non visited edges constraint
                self.model.addConstr(
                    self.S[edge, driver] <= self.horizon() * self.x[edge, driver],
                    "Non visited edges constraint for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['non-visited-edges-constraints'] += 1
                # visited edges constraint
                self.model.addConstr(
                    self.S[edge, driver] >= self.x[edge, driver],
                    "Visited edges constraint for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['visited-edges-constraints'] += 1
                # starting ending constraints
                self.model.addConstr(
                    self.E[edge, driver] <= self.horizon() * self.x[edge, driver],
                    "Starting-ending constraint for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['starting-ending-constraints'] += 1
                # transfert equation
                self.model.addConstr(
                    self.E[edge, driver] - self.S[edge, driver] + self.horizon() * (1 - self.x[edge, driver]) >=
                    quicksum(self.x[edge, driver] for d in self.drivers),
                    "Transfert equation for driver %s on edge %s" % (str(driver), str(edge))
                )
                count['transfert-constraints'] += 1

        log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in count.iteritems()))

    def setObjective(self):
        self.model.setObjective(self.z, GRB.MINIMIZE)
        log.info("Objective SETTED")

    def setOptimalSolution(self):
        paths = {}
        for (edge, driver), var in self.x.iteritems():
            paths.setdefault(driver, [])
            if var.X == 1.0:
                paths[driver].append((edge, self.S[edge, driver].X))

        for driver, lst in paths.iteritems():
            path = None
            for edge in map(lambda (e, v): e, sorted(lst, key=lambda (e, v): v)):
                path = edge if path is None else path + (edge[1],)
            self.addOptimalPathToDriver(driver.to_tuple(), tuple(path))

    def assert_objective_is_valid(self):
        """ the objective value of this problem is bounded
        """
        M = max(self.graph.getCongestionFunction(*edge)(0) for edge in self.graph.edges())
        E, D = self.graph.number_of_edges(), self.graph.number_of_drivers()
        if self.getObj() > max(E * M, D):
            log.error("Solving problem %s has failes", self.__class__.__name__)
            raise Exception("Solving problem %s has failes" % self.__class__.__name__)

    def getUpperBoundToOptimal(self):
        """ If the problem has been solved, compute the bound using the formula in report 3
        """
        self.assert_objective_is_valid()
        alpha = self.getObj()

        # Compute first the shortest path withour traffic lower bound
        lower = 0
        for driver in self.drivers:
            path = self.get_shortest_path(driver.start, driver.end)
            for edge in self.graph.iter_edges_in_path(path):
                lower += self.graph.getCongestionFunction(driver.start, driver.end)(0)

        # compute the maximum waiting time
        M = max(self.graph.getCongestionFunction(*edge)(alpha) for edge in self.graph.edges())

        # compute the minimum waiting time
        m = min(self.graph.getCongestionFunction(*edge)(0) for edge in self.graph.edges())

        return (1 + len(self.drivers()) * alpha / lower) * M / m
