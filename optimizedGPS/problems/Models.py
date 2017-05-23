# -*- coding: utf-8 -*-
# !/bin/env python

import logging

try:
    from gurobipy import GRB, quicksum
except:
    pass

import labels
from optimizedGPS import options
from Problem import Model
from optimizedGPS.structure import ReducedTimeExpandedGraph as TEG

__all__ = ["MainContinuousTimeModel", "BestPathTrafficModel", "FixedWaitingTimeModel", "TEGModel"]

log = logging.getLogger(__name__)


class EdgeCharacterizationModel(Model):
    def initialize(self, **kwards):
        binary = kwards.get("binary", True)
        self.vtype = GRB.BINARY if binary else GRB.CONTINUOUS
        self.initialize_drivers()

    def build_variables(self):
        self.x = {}
        for edge in self.graph.edges_iter():
            for driver in self.drivers:
                self.x[edge, driver] = self.model.addVar(0.0, name='x[%s,%s]' % (str(edge), str(driver)),
                                                         vtype=self.vtype)

    def initialize_drivers(self):
        """ Make drivers unique entities
        """
        self.drivers = set(self.drivers_graph.get_all_drivers())

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
    def build_variables(self):
        # add here variables
        super(MainContinuousTimeModel, self).build_variables()

        self.S = {}  # starting time variables
        self.E = {}  # ending time variables

        for edge in self.graph.edges_iter():
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
            for node in self.graph.nodes_iter():
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
            for edge in self.graph.edges_iter():
                # non visited edges constraint
                self.add_constraint(
                    self.S[edge, driver] <= self.horizon * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.NON_VISITED_EDGES, str(driver), str(edge))
                )
                # visited edges constraint
                self.add_constraint(
                    self.S[edge, driver] >= self.x[edge, driver],
                    name="%s:%s:%s" % (labels.VISITED_EDGES, str(driver), str(edge))
                )
                # starting ending constraints
                self.model.addConstr(
                    self.E[edge, driver] <= self.horizon * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.STARTING_ENDING, str(driver), str(edge))
                )
                # transfert equation
                self.model.addConstr(
                    self.E[edge, driver] - self.S[edge, driver] + self.horizon * (1 - self.x[edge, driver]) >=
                    self.get_traffic(edge, driver),
                    name="%s:%s:%s" % (labels.TRANSFERT, str(driver), str(edge))
                )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def set_objective(self):
        self.model.setObjective(
            quicksum(self.E[edge, driver] for edge in self.graph.edges_iter() for driver in self.drivers
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

    def build_variables(self):
        super(BestPathTrafficModel, self).build_variables()
        self.z = self.model.addVar(name="z")

    def build_constraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for edge in self.graph.edges_iter():
            self.add_constraint(
                quicksum(self.x[edge, driver] - self.graph.get_traffic_limit(*edge) for driver in self.drivers) <=
                self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_BEST_TRAFFIC, str(edge))
            )
        for driver in self.drivers:
            self.add_constraint(
                quicksum(self.graph.get_minimum_waiting_time(*edge) *
                         (self.x[edge, driver] - self.X[driver.start, driver.end].get(edge, 0))
                         for edge in self.graph.edges_iter()) <= self.z,
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
            for node in self.graph.nodes_iter():
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
            for edge in self.graph.edges_iter():
                self.set_waiting_time(driver, edge, value=C.get((driver, edge)))

    def set_waiting_time(self, driver, edge, value=None):
        if value is None:
            value = self.graph.get_minimum_waiting_time(*edge)
        self.C[edge, driver] = value

    def get_traffic(self, edge, driver):
        return self.C[edge, driver]

    def get_optimal_driver_waiting_times(self, driver):
        """
        Return the waiting times of driver

        :param driver: Driver object
        :return: dict with waiting time on each edge: {edge: waiting_time}
        """
        waiting_times = {driver: self.opt_simulator.get_driver_waiting_times(driver)
                         for driver in self.get_drivers_graph().get_all_drivers()}
        return waiting_times.get(driver, {})

    def solve_with_heuristic(self):
        for driver in self.drivers:
            for edge in self.graph.edges_iter():
                self.graph.set_edge_property(edge[0], edge[1], 'waiting_time', self.C[edge, driver])
            path = self.graph.get_shortest_path(driver.start, driver.end, edge_property='waiting_time')
            self.set_optimal_path_to_driver(driver, path)
        self.set_status(options.SUCCESS)


class TEGModel(EdgeCharacterizationModel):
    def initialize(self, **kwargs):
        self.TEGgraph = TEG(self.graph, self.horizon)
        super(TEGModel, self).initialize(**kwargs)

    def start_interval(self, driver):
        start, end = self.drivers_structure.get_largest_safety_interval_after_start(driver)
        return start if start is not None else 0, end + 1 if end is not None else 0

    def end_interval(self, driver):
        start, end = self.drivers_structure.get_largest_safety_interval_before_end(driver)
        return start if start is not None else 0, end + 1 if end is not None else 0

    def bigM(self):
        return max([self.graph.get_congestion_function(*edge)(self.drivers_graph.number_of_drivers())
                    for edge in self.graph.edges_iter()])

    def number_of_variables(self):
        value = 0
        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.get_edges_for_driver(driver):
                start, end = self.get_time_interval(driver, edge)
                for i in xrange(start, end + 1):
                    for j in xrange(i, end + 1):
                        value += 1
        return value

    def number_of_constraints(self):
        value = 0
        for driver in self.drivers:
            for edge in self.get_edges_for_driver(driver):
                start, end = self.get_time_interval(driver, edge)
                for i in xrange(start, end):
                    for j in xrange(i + 1, end + 1):
                        value += 2
        for driver in self.drivers:
            value += 1
            ending_nodes = set(map(lambda t: self.TEGgraph.build_node(driver.end, t), xrange(*self.end_interval(driver))))
            for node in self.TEGgraph.nodes_iter():
                if node not in ending_nodes:
                    value += 1
        return value

    def add_driver(self, driver, edges):
        self.drivers_graph.add_driver(driver)
        for edge in self.graph.edges_iter():
            if edge in edges:
                start, end = 0, self.horizon
                self.generate_variables(driver, edge, start, end, update=True)
                self.generate_constraints(driver, edge, start, end)
            else:
                self.drivers_structure.set_unreachable_edge_to_driver(driver, edge)

    def add_edges_for_driver(self, driver, edges):
        for edge in edges:
            self.drivers_structure.set_reachable_edge_for_driver(driver, edge)
            start, end = 0, self.horizon
            self.generate_variables(driver, edge, start, end, update=True)
            self.generate_constraints(driver, edge, start, end)

    def generate_variables(self, driver, edge, start, end, update=False):
        for i in xrange(start, end):
            for j in xrange(i + 1, end + 1):
                _edge = self.TEGgraph.build_edge(edge, i, j)
                self.x[_edge, driver] = \
                    self.model.addVar(0.0, name='x[%s,%s]' % (str(_edge), str(driver)), vtype=self.vtype)
        if update:
            self.model.update()

    def generate_constraints(self, driver, edge, start, end):
        for i in xrange(start, end):
            for j in xrange(i + 1, end + 1):
                self.add_constraint(
                    self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i) <=
                    self.graph.get_congestion_function(*edge)(
                        quicksum(self.x.get((self.TEGgraph.build_edge(edge, ii, jj), d), 0)
                                 for ii in xrange(0, i) for jj in xrange(i + 1, self.horizon + 1)
                                 for d in self.drivers)
                    ),
                    name="%s:%s:%s" % (
                        labels.LOWER_WAITING_TIME,
                        str(self.TEGgraph.build_edge(edge, i, j)),
                        str(driver)
                    )
                )
                self.add_constraint(
                    self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i) +
                    self.bigM() * (1 - self.x[self.TEGgraph.build_edge(edge, i, j), driver]) >=
                    self.graph.get_congestion_function(*edge)(
                        quicksum(self.x.get((self.TEGgraph.build_edge(edge, ii, jj), d), 0)
                                 for ii in xrange(0, i) for jj in xrange(i + 1, self.horizon + 1)
                                 for d in self.drivers)
                    ),
                    name="%s:%s:%s" % (
                        labels.UPPER_WAITING_TIME,
                        str(self.TEGgraph.build_edge(edge, i, j)),
                        str(driver)
                    )
                )
        self.add_constraint(
            quicksum(
                self.x.get(((s, self.TEGgraph.build_node(driver.end, time)), driver), 0)
                for time in xrange(*self.end_interval(driver))
                for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
            ) == 1,
            name="%s:%s" % (labels.ENDING_TIME, str(driver))
        )
        ending_nodes = set(map(lambda t: self.TEGgraph.build_node(driver.end, t), xrange(*self.end_interval(driver))))
        for node in self.TEGgraph.nodes_iter():
            if node not in ending_nodes:
                if self.TEGgraph.get_original_node(node) == driver.start and \
                                self.TEGgraph.get_node_layer(node) == driver.time:
                    res = 1
                else:
                    res = 0
                self.add_constraint(
                    quicksum(self.x.get(((node, succ), driver), 0) for succ in self.TEGgraph.successors_iter(node)) -
                    quicksum(self.x.get(((pred, node), driver), 0) for pred in self.TEGgraph.predecessors_iter(node)) ==
                    res,
                    name="%s:%s:%s" % (labels.TRANSFERT, str(driver), str(node))
                )

    def build_variables(self):
        self.x = {}
        for driver in self.drivers:
            for edge in self.get_edges_for_driver(driver):
                start, end = self.get_time_interval(driver, edge)
                self.generate_variables(driver, edge, start, end)

    def build_constraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for driver in self.drivers:
            for edge in self.get_edges_for_driver(driver):
                start, end = self.get_time_interval(driver, edge)
                for i in xrange(start, end):
                    for j in xrange(i + 1, end + 1):
                        self.add_constraint(
                            self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i) <=
                            self.graph.get_congestion_function(*edge)(
                                quicksum(self.x.get((self.TEGgraph.build_edge(edge, ii, jj), d), 0)
                                         for ii in xrange(0, i) for jj in xrange(i + 1, self.horizon + 1)
                                         for d in self.drivers)
                            ),
                            name="%s:%s:%s" % (
                                labels.LOWER_WAITING_TIME,
                                str(self.TEGgraph.build_edge(edge, i, j)),
                                str(driver)
                            )
                        )
                        self.add_constraint(
                            self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i) +
                            self.bigM() * (1 - self.x[self.TEGgraph.build_edge(edge, i, j), driver]) >=
                            self.graph.get_congestion_function(*edge)(
                                quicksum(self.x.get((self.TEGgraph.build_edge(edge, ii, jj), d), 0)
                                         for ii in xrange(0, i) for jj in xrange(i + 1, self.horizon + 1)
                                         for d in self.drivers)
                            ),
                            name="%s:%s:%s" % (
                                labels.UPPER_WAITING_TIME,
                                str(self.TEGgraph.build_edge(edge, i, j)),
                                str(driver)
                            )
                        )
        for driver in self.drivers:
            self.add_constraint(
                quicksum(
                    self.x.get(((s, self.TEGgraph.build_node(driver.end, time)), driver), 0)
                    for time in xrange(*self.end_interval(driver))
                    for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
                ) == 1,
                name="%s:%s" % (labels.ENDING_TIME, str(driver))
            )
            ending_nodes = set(map(lambda t: self.TEGgraph.build_node(driver.end, t), xrange(*self.end_interval(driver))))
            for node in self.TEGgraph.nodes_iter():
                if node not in ending_nodes:
                    if self.TEGgraph.get_original_node(node) == driver.start and \
                                    self.TEGgraph.get_node_layer(node) == driver.time:
                        res = 1
                    else:
                        res = 0
                    self.add_constraint(
                        quicksum(self.x.get(((node, succ), driver), 0) for succ in self.TEGgraph.successors_iter(node)) -
                        quicksum(self.x.get(((pred, node), driver), 0) for pred in self.TEGgraph.predecessors_iter(node)) ==
                        res,
                        name="%s:%s:%s" % (labels.TRANSFERT, str(driver), str(node))
                    )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def set_objective(self):
        self.model.setObjective(
            quicksum(
                time * self.x.get(((s, self.TEGgraph.build_node(driver.end, time)), driver), 0) for driver in self.drivers
                for time in xrange(*self.end_interval(driver))
                for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
            ),
            GRB.MINIMIZE
        )

    def set_optimal_solution(self):
        paths = {}
        for (edge, driver), var in self.x.iteritems():
            paths.setdefault(driver, [])
            if var.X == 1.0:
                paths[driver].append(self.TEGgraph.get_original_edge(edge))

        for driver, edges in paths.iteritems():
            self.set_optimal_path_to_driver(
                driver,
                self.graph.generate_path_from_edges(driver.start, driver.end, edges)
            )
