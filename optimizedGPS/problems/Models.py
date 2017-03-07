# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import sys

try:
    from gurobipy import GRB, quicksum
except:
    pass

import labels
from Problem import Model
from optimizedGPS.structure import TimeExpandedGraph as TEG

__all__ = ["MainContinuousTimeModel", "BestPathTrafficModel", "FixedWaitingTimeModel"]

log = logging.getLogger(__name__)


HORIZON = 1000


class EdgeCharacterizationModel(Model):
    def initialize(self, **kwards):
        binary = kwards.get("binary", True)
        self.vtype = GRB.BINARY if binary else GRB.CONTINUOUS
        self.initialize_drivers()

    def buildVariables(self):
        self.x = {}
        for edge in self.graph.edges():
            for driver in self.drivers:
                self.x[edge, driver] = self.model.addVar(0.0, name='x[%s,%s]' % (str(edge), str(driver)),
                                                         vtype=self.vtype)

    def initialize_drivers(self):
        """ Make drivers unique entities
        """
        self.drivers = set(self.graph.get_all_unique_drivers())

    def setOptimalSolution(self):
        paths = {}
        for (edge, driver), var in self.x.iteritems():
            paths.setdefault(driver, [])
            if var.X == 1.0:
                paths[driver].append(edge)

        for driver, edges in paths.iteritems():
            self.addOptimalPathToDriver(
                driver.to_tuple(),
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

    def buildVariables(self):
        # add here variables
        super(MainContinuousTimeModel, self).buildVariables()

        self.S = {}  # starting time variables
        self.E = {}  # ending time variables

        for edge in self.graph.edges():
            for driver in self.drivers:
                self.S[edge, driver] = self.model.addVar(0.0, name='S[%s,%s]' % (str(edge), str(driver)))
                self.E[edge, driver] = self.model.addVar(0.0, name='E[%s,%s]' % (str(edge), str(driver)))

    def getTraffic(self, edge, time):
        raise NotImplementedError("Not implemented yet")

    def buildConstraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for driver in self.drivers:
            # starting edges constraints
            self.addConstraint(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                name="%s:%s" % (labels.STARTING_EDGES, str(driver))
            )
            # ending edges constraints
            self.addConstraint(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                name="%s:%s" % (labels.ENDING_EDGES, str(driver))
            )
            # initial conditions
            self.addConstraint(
                quicksum(self.S[(driver.start, t), driver]
                         for t in self.graph.successors_iter(driver.start)) == driver.time + 1,
                name="%s:%s" % (labels.INITIAL_CONDITIONS, str(driver))
            )
            for node in self.graph.nodes():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.addConstraint(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.NO_CYCLE, str(driver), str(node))
                    )
                    # ending time constraints
                    self.addConstraint(
                        quicksum(self.E[(n, node), driver] for n in self.graph.predecessors_iter(node)) <=
                        quicksum(self.S[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.ENDING_TIME, str(driver), str(node))
                    )
            for edge in self.graph.edges():
                # non visited edges constraint
                self.addConstraint(
                    self.S[edge, driver] <= self.horizon() * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.NON_VISITED_EDGES, str(driver), str(edge))
                )
                # visited edges constraint
                self.addConstraint(
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
                    self.getTraffic(edge, driver),
                    name="%s:%s:%s" % (labels.TRANSFERT, str(driver), str(edge))
                )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def setObjective(self):
        self.model.setObjective(
            quicksum(self.E[edge, driver] for edge in self.graph.edges() for driver in self.drivers
                     if edge[1] == driver.end),
            GRB.MINIMIZE
        )


class BestPathTrafficModel(EdgeCharacterizationModel):
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
        super(BestPathTrafficModel, self).buildVariables()
        self.z = self.model.addVar(name="z")

    def buildConstraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for edge in self.graph.edges():
            self.addConstraint(
                quicksum(self.x[edge, driver] - self.graph.get_traffic_limit(*edge) for driver in self.drivers) <=
                self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_BEST_TRAFFIC, str(edge))
            )
        for driver in self.drivers:
            self.model.addConstr(
                quicksum(self.graph.get_minimum_waiting_time(*edge) *
                         (self.x[edge, driver] - self.X[driver.start, driver.end].get(edge, 0))
                         for edge in self.graph.edges()) <= self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_SHORTEST_PATH, str(driver))
            )
            # starting edges constraints
            self.model.addConstr(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                name="%s:%s" % (labels.STARTING_EDGES, str(driver))
            )
            # ending edges constraints
            self.model.addConstr(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                name="%s:%s" % (labels.ENDING_EDGES, str(driver))
            )
            for node in self.graph.nodes():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.model.addConstr(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.NO_CYCLE, str(driver), str(node))
                    )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def setObjective(self):
        self.model.setObjective(self.z, GRB.MINIMIZE)


class FixedWaitingTimeModel(MainContinuousTimeModel):
    def initialize(self, **kwards):
        super(FixedWaitingTimeModel, self).initialize()
        C, self.C = kwards.get('waiting_times', {}), {}
        for driver in self.drivers:
            for edge in self.graph.edges():
                self.setWaitingTime(driver, edge, value=C.get((driver, edge)))

    def setWaitingTime(self, driver, edge, value=None):
        if value is None:
            value = self.graph.get_minimum_waiting_time(*edge)
        self.C[edge, driver] = value

    def getTraffic(self, edge, driver):
        return self.C[edge, driver]


class TEGLinearCongestionModel(EdgeCharacterizationModel):
    def __init__(self, graph, timeout=sys.maxint, horizon=1000):
        super(TEGLinearCongestionModel, self).__init__(graph, timeout=timeout, horizon=horizon)

    def initialize(self, horizon=HORIZON, **kwargs):
        self.TEG_graph = TEG.create_time_expanded_graph_from_linear_congestion(self.graph, horizon)
        self.hor = horizon
        super(TEGLinearCongestionModel, self).initialize(**kwargs)

    def horizon(self):
        return self.hor

    def buildConstraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for edge in self.TEG_graph.edges():
            self.addConstraint(
                quicksum(self.x[edge, driver] for driver in self.drivers) <= 1,
                name="%s:%s" % (labels.ONE_DRIVER_PER_EDGE, str(edge))
            )
        for driver in self.drivers:
            self.addConstraint(
                quicksum(
                    self.x[(s, TEG.get_time_node_name(driver.end, time)), driver]
                    for time in range(self.horizon())
                    for s in self.TEG_graph.predecessors_iter(TEG.get_time_node_name(driver.end, time))
                ) == 1,
                name="%s:%s" % (labels.ENDING_TIME, str(driver))
            )
            for node in self.TEG_graph.nodes():
                if node not in map(lambda t: TEG.get_time_node_name(driver.end, t), range(self.horizon())):
                    self.addConstraint(
                        quicksum(self.x[(node, succ), driver] for succ in self.TEG_graph.successors_iter(node)) -
                        quicksum(self.x[(pred, node), driver] for pred in self.TEG_graph.predecessors_iter(node)) ==
                        sum(
                            1 for time in range(self.horizon())
                            if TEG.get_time_node_name(driver.start, time) == node
                        ),
                        name="%s:%s:%s" % (labels.TRANSFERT, str(driver), str(node))
                    )
        for edge in self.graph.edges():
            for i in range(self.horizon()):
                for j in range(i + 1, self.horizon()):
                    self.addConstraint(
                        quicksum(
                            self.x[TEG.get_edge(edge, i, j), driver] -
                            quicksum(
                                self.x[TEG.get_edge(edge, ii, j)]
                                for ii in range(i)
                            )
                            for driver in self.drivers
                        ) <= 0,
                        name="%s:%s:%s:%s" % (labels.TIME_TRANSFERT, str(edge), i, j)
                    )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def setObjective(self):
        self.model.setObjective(
            quicksum(
                self.x[(s, TEG.get_time_node_name(driver.end, time)), driver] for driver in self.drivers
                for time in range(self.horizon())
                for s in self.TEG_graph.predecessors_iter(TEG.get_time_node_name(driver.end, time))
            )
        )
