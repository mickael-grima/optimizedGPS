# -*- coding: utf-8 -*-
# !/bin/env python

import logging

try:
    from gurobipy import GRB, quicksum
except:
    pass

import labels
from Problem import Model

__all__ = ["MainContinuousTimeModel", "BestPathTrafficModel", "FixedWaitingTimeModel"]

log = logging.getLogger(__name__)


HORIZON = 1000


class EdgeCharacterizationModel(Model):
    def initialize(self, **kwards):
        binary = kwards.get("binary", True)
        self.vtype = GRB.BINARY if binary else GRB.CONTINUOUS
        self.initialize_drivers()

    def build_variables(self):
        self.x = {}
        for edge in self.graph.edges():
            for driver in self.drivers:
                self.x[edge, driver] = self.model.addVar(0.0, name='x[%s,%s]' % (str(edge), str(driver)),
                                                         vtype=self.vtype)

    def initialize_drivers(self):
        """ Make drivers unique entities
        """
        self.drivers = set(self.graph.get_all_drivers())

    def set_optimal_solution(self):
        paths = {}
        for (edge, driver), var in self.x.iteritems():
            paths.setdefault(driver, [])
            if var.X == 1.0:
                paths[driver].append(edge)

        for driver, edges in paths.iteritems():
            self.set_optimal_path_to_driver(
                driver,
                self.graph.generate_path_from_edges(driver.start, driver.end, edges)
            )


class MainContinuousTimeModel(EdgeCharacterizationModel):
    """ Main Model: do not try to solve, one constraint is neither linear nor convex nor continuous
    """
    def initialize(self, **kwards):
        super(MainContinuousTimeModel, self).initialize(**kwards)
        self.hor = kwards.get("horizon", 1000)

    def horizon(self):
        return self.hor

    def build_variables(self):
        # add here variables
        super(MainContinuousTimeModel, self).build_variables()

        self.S = {}  # starting time variables
        self.E = {}  # ending time variables

        for edge in self.graph.edges():
            for driver in self.drivers:
                self.S[edge, driver] = self.model.addVar(0.0, name='S[%s,%s]' % (str(edge), str(driver)))
                self.E[edge, driver] = self.model.addVar(0.0, name='E[%s,%s]' % (str(edge), str(driver)))

    def get_traffic(self, edge, time):
        raise NotImplementedError("Not implemented yet")

    def build_constraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for driver in self.drivers:
            # starting edges constraints
            self.add_constraint(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                name="%s:%s" % (labels.STARTING_EDGES, str(driver))
            )
            # ending edges constraints
            self.add_constraint(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                name="%s:%s" % (labels.ENDING_EDGES, str(driver))
            )
            # initial conditions
            self.add_constraint(
                quicksum(self.S[(driver.start, t), driver]
                         for t in self.graph.successors_iter(driver.start)) == driver.time + 1,
                name="%s:%s" % (labels.INITIAL_CONDITIONS, str(driver))
            )
            for node in self.graph.nodes():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.add_constraint(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.NO_CYCLE, str(driver), str(node))
                    )
                    # ending time constraints
                    self.add_constraint(
                        quicksum(self.E[(n, node), driver] for n in self.graph.predecessors_iter(node)) <=
                        quicksum(self.S[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.ENDING_TIME, str(driver), str(node))
                    )
            for edge in self.graph.edges():
                # non visited edges constraint
                self.add_constraint(
                    self.S[edge, driver] <= self.horizon() * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.NON_VISITED_EDGES, str(driver), str(edge))
                )
                # visited edges constraint
                self.add_constraint(
                    self.S[edge, driver] >= self.x[edge, driver],
                    name="%s:%s:%s" % (labels.VISITED_EDGES, str(driver), str(edge))
                )
                # starting ending constraints
                self.model.addConstr(
                    self.E[edge, driver] <= self.horizon() * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.STARTING_ENDING, str(driver), str(edge))
                )
                # transfert equation
                self.model.addConstr(
                    self.E[edge, driver] - self.S[edge, driver] + self.horizon() * (1 - self.x[edge, driver]) >=
                    self.get_traffic(edge, driver),
                    name="%s:%s:%s" % (labels.TRANSFERT, str(driver), str(edge))
                )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def set_objective(self):
        self.model.setObjective(
            quicksum(self.E[edge, driver] for edge in self.graph.edges() for driver in self.drivers
                     if edge[1] == driver.end),
            GRB.MINIMIZE
        )


class BestPathTrafficModel(EdgeCharacterizationModel):
    def build_constants(self):
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
        super(BestPathTrafficModel, self).build_variables()
        self.z = self.model.addVar(name="z")

    def build_constraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for edge in self.graph.edges():
            self.add_constraint(
                quicksum(self.x[edge, driver] - self.graph.get_traffic_limit(*edge) for driver in self.drivers) <=
                self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_BEST_TRAFFIC, str(edge))
            )
        for driver in self.drivers:
            self.add_constraint(
                quicksum(self.graph.get_minimum_waiting_time(*edge) *
                         (self.x[edge, driver] - self.X[driver.start, driver.end].get(edge, 0))
                         for edge in self.graph.edges()) <= self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_SHORTEST_PATH, str(driver))
            )
            # starting edges constraints
            self.add_constraint(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                name="%s:%s" % (labels.STARTING_EDGES, str(driver))
            )
            # ending edges constraints
            self.add_constraint(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                name="%s:%s" % (labels.ENDING_EDGES, str(driver))
            )
            for node in self.graph.nodes():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.add_constraint(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.NO_CYCLE, str(driver), str(node))
                    )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def set_objective(self):
        self.model.setObjective(self.z, GRB.MINIMIZE)


class FixedWaitingTimeModel(MainContinuousTimeModel):
    def initialize(self, **kwargs):
        super(FixedWaitingTimeModel, self).initialize()
        C, self.C = kwargs.get('waiting_times', {}), {}
        for driver in self.drivers:
            for edge in self.graph.edges():
                self.set_waiting_time(driver, edge, value=C.get((driver, edge)))

    def set_waiting_time(self, driver, edge, value=None):
        if value is None:
            value = self.graph.get_minimum_waiting_time(*edge)
        self.C[edge, driver] = value

    def get_traffic(self, edge, driver):
        return self.C[edge, driver]
