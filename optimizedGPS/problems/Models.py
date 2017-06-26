# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from collections import defaultdict

try:
    from gurobipy import GRB, quicksum, Var
except:
    pass

import labels
from optimizedGPS import options
from Problem import Model
from optimizedGPS.structure import ReducedTimeExpandedGraph as TEG
from optimizedGPS.structure import Graph, Driver

__all__ = ["MainContinuousTimeModel", "BestPathTrafficModel", "FixedWaitingTimeModel", "TEGModel"]

log = logging.getLogger(__name__)


class EdgeCharacterizationModel(Model):
    def initialize(self, **kwards):
        self.vtype = GRB.BINARY if self.binary else GRB.CONTINUOUS

    def change_variables_type(self, vtype):
        self.binary = vtype == GRB.BINARY
        self.vtype = vtype

    def build_variables(self):
        self.x = defaultdict(lambda: 0)
        for edge in self.graph.edges_iter():
            for driver in self.drivers_graph.get_all_drivers():
                self.x[edge, driver] = self.model.addVar(0.0, name='x[%s,%s]' % (str(edge), repr(driver)),
                                                         vtype=self.vtype)

    def set_optimal_solution(self):
        paths = {}
        for (edge, driver), var in self.x.iteritems():
            paths.setdefault(driver, [])
            if isinstance(var, Var) and var.X == 1.0:
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
            for driver in self.drivers_graph.get_all_drivers():
                self.S[edge, driver] = self.model.addVar(0.0, name='S[%s,%s]' % (str(edge), repr(driver)))
                self.E[edge, driver] = self.model.addVar(0.0, name='E[%s,%s]' % (str(edge), repr(driver)))

    def get_traffic(self, edge, time):
        raise NotImplementedError("Not implemented yet")

    def build_constraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for driver in self.drivers_graph.get_all_drivers():
            # starting edges constraints
            self.add_constraint(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                name="%s:%s" % (labels.STARTING_EDGES, repr(driver))
            )
            # ending edges constraints
            self.add_constraint(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                name="%s:%s" % (labels.ENDING_EDGES, repr(driver))
            )
            # initial conditions
            self.add_constraint(
                quicksum(self.S[(driver.start, t), driver]
                         for t in self.graph.successors_iter(driver.start)) == driver.time + 1,
                name="%s:%s" % (labels.INITIAL_CONDITIONS, repr(driver))
            )
            for node in self.graph.nodes_iter():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.add_constraint(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.NO_CYCLE, repr(driver), str(node))
                    )
                    # ending time constraints
                    self.add_constraint(
                        quicksum(self.E[(n, node), driver] for n in self.graph.predecessors_iter(node)) <=
                        quicksum(self.S[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.ENDING_TIME, repr(driver), str(node))
                    )
            for edge in self.graph.edges_iter():
                # non visited edges constraint
                self.add_constraint(
                    self.S[edge, driver] <= self.horizon * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.NON_VISITED_EDGES, repr(driver), str(edge))
                )
                # visited edges constraint
                self.add_constraint(
                    self.S[edge, driver] >= self.x[edge, driver],
                    name="%s:%s:%s" % (labels.VISITED_EDGES, repr(driver), str(edge))
                )
                # starting ending constraints
                self.model.addConstr(
                    self.E[edge, driver] <= self.horizon * self.x[edge, driver],
                    name="%s:%s:%s" % (labels.STARTING_ENDING, repr(driver), str(edge))
                )
                # transfert equation
                self.model.addConstr(
                    self.E[edge, driver] - self.S[edge, driver] + self.horizon * (1 - self.x[edge, driver]) >=
                    self.get_traffic(edge, driver),
                    name="%s:%s:%s" % (labels.TRANSFERT, repr(driver), str(edge))
                )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def set_objective(self):
        self.model.setObjective(
            quicksum(self.E[edge, driver] for edge in self.graph.edges_iter()
                     for driver in self.drivers_graph.get_all_drivers()
                     if edge[1] == driver.end),
            GRB.MINIMIZE
        )


class BestPathTrafficModel(EdgeCharacterizationModel):
    def build_constants(self):
        """ For each driver we find the edges belonging to his shortest path
        """
        self.X = {}
        for driver in self.drivers_graph.get_all_drivers():
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
                quicksum(self.x[edge, driver] - self.graph.get_traffic_limit(*edge)
                         for driver in self.drivers_graph.get_all_drivers()) <=
                self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_BEST_TRAFFIC, str(edge))
            )
        for driver in self.drivers_graph.get_all_drivers():
            self.add_constraint(
                quicksum(self.graph.get_minimum_waiting_time(*edge) *
                         (self.x[edge, driver] - self.X[driver.start, driver.end].get(edge, 0))
                         for edge in self.graph.edges_iter()) <= self.z,
                name="%s:%s" % (labels.DIFFERENCE_TO_SHORTEST_PATH, repr(driver))
            )
            # starting edges constraints
            self.add_constraint(
                quicksum(self.x[(n, driver.end), driver] for n in self.graph.predecessors_iter(driver.end)) == 1,
                name="%s:%s" % (labels.STARTING_EDGES, repr(driver))
            )
            # ending edges constraints
            self.add_constraint(
                quicksum(self.x[(driver.start, n), driver] for n in self.graph.successors_iter(driver.start)) == 1,
                name="%s:%s" % (labels.ENDING_EDGES, repr(driver))
            )
            for node in self.graph.nodes_iter():
                if node not in [driver.start, driver.end]:
                    # on one node, driver comes from only one node and goes to only one node
                    self.add_constraint(
                        quicksum(self.x[(n, node), driver] for n in self.graph.predecessors_iter(node)) ==
                        quicksum(self.x[(node, n), driver] for n in self.graph.successors_iter(node)),
                        name="%s:%s:%s" % (labels.NO_CYCLE, repr(driver), str(node))
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
        for driver in self.drivers_graph.get_all_drivers():
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
        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.graph.edges_iter():
                self.graph.set_edge_property(edge[0], edge[1], 'waiting_time', self.C[edge, driver])
            path = self.graph.get_shortest_path(driver.start, driver.end, edge_property='waiting_time')
            self.set_optimal_path_to_driver(driver, path)
        self.set_status(options.SUCCESS)


class TEGModel(EdgeCharacterizationModel):
    def initialize(self, **kwargs):
        self.TEGgraph = TEG(self.graph, self.horizon)
        super(TEGModel, self).initialize(**kwargs)

    def bigM(self):
        return max([self.graph.get_congestion_function(*edge)(self.drivers_graph.number_of_drivers())
                    for edge in self.graph.edges_iter()])

    def has_variable(self, driver, edge, start, end):
        return isinstance(self.x[self.TEGgraph.build_edge(edge, start, end), driver], Var)

    def number_of_variables(self):
        value = 0
        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.get_edges_for_driver(driver):
                value += len(set(self.iter_start_end_times_for_driver(driver, edge)))
        return value

    def number_of_constraints(self):
        value = 0
        for driver in self.drivers_graph.get_all_drivers():
            value += 1
            value += self.TEGgraph.number_of_nodes()
            value -= len(self.drivers_structure.get_possible_ending_times_on_node(driver, driver.end))
            for edge in self.graph.edges_iter():
                value += 1 + 2 * len(set(self.drivers_structure.iter_starting_times(driver, edge)))
        return value

    def generate_variables(self, driver, edge, times):
        for i, j in times:
            _edge = self.TEGgraph.build_edge(edge, i, j)
            if not isinstance(self.x[_edge, driver], Var):
                self.x[_edge, driver] = \
                    self.model.addVar(0.0, name='x[%s,%s]' % (str(_edge), repr(driver)), vtype=self.vtype)
        self.model.update()

    def generate_constraints(self, driver, edge, times):
        for i, _ in times:
            constr_name = "%s:%s:%s:%s" % (labels.UPPER_WAITING_TIME, repr(driver), str(edge), i)
            if not self.has_constraint(constr_name):
                self.add_constraint(
                    quicksum(self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i)
                             for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i)) <=
                    self.graph.get_congestion_function(*edge)(
                        quicksum(
                            quicksum(self.x[self.TEGgraph.build_edge(edge, ii, jj), d]
                                     for ii, jj in self.iter_start_end_times_for_driver(d, edge) if ii < i <= jj)
                            for d in self.drivers_graph.get_all_drivers()
                        )
                    ),
                    name=constr_name
                )
            constr_name = "%s:%s:%s:%s" % (labels.LOWER_WAITING_TIME, repr(driver), str(edge), i)
            if not self.has_constraint(constr_name):
                self.add_constraint(
                    quicksum(self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i)
                             for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i)) +
                    self.bigM() * (1 - quicksum(
                        self.x[self.TEGgraph.build_edge(edge, i, j), driver]
                        for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i))) >=
                    self.graph.get_congestion_function(*edge)(
                        quicksum(
                            quicksum(self.x[self.TEGgraph.build_edge(edge, ii, jj), d]
                                     for ii, jj in self.iter_start_end_times_for_driver(d, edge) if ii < i <= jj)
                            for d in self.drivers_graph.get_all_drivers()
                        )
                    ),
                    name=constr_name
                )
            constr_name = "%s:%s:%s" % (labels.EDGE_TIME_UNICITY, repr(driver), str(edge))
            if not self.has_constraint(constr_name):
                self.add_constraint(
                    quicksum(self.x[self.TEGgraph.build_edge(edge, i, j), driver]
                             for i, j in self.iter_start_end_times_for_driver(driver, edge)) <= 1,
                    name=constr_name
                )
            for node in self.graph.nodes_iter():
                if node != driver.end:
                    constr_name = "%s:%s:%s:%s" % (labels.TRANSFERT, repr(driver), str(node), i)
                    if not self.has_constraint(constr_name):
                        node_ = self.TEGgraph.build_node(node, i)
                        self.add_constraint(
                            quicksum(
                                self.x[(node_, succ), driver] for succ in self.TEGgraph.successors_iter(node_)) -
                            quicksum(
                                self.x[(pred, node_), driver] for pred in self.TEGgraph.predecessors_iter(node_)) ==
                            1 * (node == driver.start and i == driver.time),
                            name=constr_name
                        )
            constr_name = "%s:%s" % (labels.ENDING_TIME, repr(driver))
            if not self.has_constraint(constr_name):
                self.add_constraint(
                    quicksum(
                        quicksum(
                            self.x[(s, self.TEGgraph.build_node(driver.end, time)), driver]
                            for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
                        )
                        for time in self.drivers_structure.get_possible_ending_times_on_node(driver, driver.end)
                    ) == 1,
                    name=constr_name
                )

    def check_feasibility(self, x):
        for driver in self.drivers_graph.get_all_drivers():
            res = sum(
                sum(
                    x[(s, self.TEGgraph.build_node(driver.end, time)), driver]
                    for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
                )
                for time in self.drivers_structure.get_possible_ending_times_on_node(driver, driver.end)
            ) == 1
            if res is False:
                return False
            for node in self.graph.nodes_iter():
                if node != driver.end:
                    for i in self.drivers_structure.iter_possible_time_on_node(driver, node):
                        node_ = self.TEGgraph.build_node(node, i)
                        res = sum(x[(node_, succ), driver] for succ in self.TEGgraph.successors_iter(node_)) - \
                              sum(x[(pred, node_), driver] for pred in self.TEGgraph.predecessors_iter(node_)) == \
                              1 * (node == driver.start and i == driver.time)
                        if res is False:
                            return False
            for edge in self.graph.edges_iter():
                res = sum(x[self.TEGgraph.build_edge(edge, i, j), driver]
                          for i, j in self.iter_start_end_times_for_driver(driver, edge)) <= 1
                if res is False:
                    return False
                for i in self.drivers_structure.iter_starting_times(driver, edge):
                    res = sum(x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i)
                             for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i)) <= \
                          self.graph.get_congestion_function(*edge)(
                              sum(
                                  sum(x[self.TEGgraph.build_edge(edge, ii, jj), d]
                                      for ii, jj in self.iter_start_end_times_for_driver(d, edge) if ii < i <= jj)
                                      for d in self.drivers_graph.get_all_drivers()
                              )
                          )
                    if res is False:
                        return False
                    res = sum(x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i)
                        for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i)) + \
                    self.bigM() * (1 - quicksum(
                        x[self.TEGgraph.build_edge(edge, i, j), driver]
                        for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i))) >= \
                    self.graph.get_congestion_function(*edge)(
                        sum(
                            sum(x[self.TEGgraph.build_edge(edge, ii, jj), d]
                                for ii, jj in self.iter_start_end_times_for_driver(d, edge) if ii < i <= jj)
                            for d in self.drivers_graph.get_all_drivers()
                        )
                    )
                    if res is False:
                        return False
        return True

    def get_reduced_cost(self, driver, edge, start, end):
        """
        If the problem has already been solved, and it is a continuous model, then return the reduced cost associated
        to the given variable index.
        """
        var = self.x[self.TEGgraph.build_edge(edge, start, end), driver]
        if isinstance(var, Var):
            return var.getAttr(GRB.Attr.RC)
        lambda_plus = {
            (d, i): self.get_dual_variable_from_constraint(
                "%s:%s:%s:%s" % (labels.UPPER_WAITING_TIME, repr(d), str(edge), i)) or 0
            for d in self.drivers_graph.get_all_drivers()
            for i in self.drivers_structure.get_starting_times(d, edge)
        }
        lambda_minus = {
            (d, i): self.get_dual_variable_from_constraint(
                "%s:%s:%s:%s" % (labels.LOWER_WAITING_TIME, repr(d), str(edge), i)) or 0
            for d in self.drivers_graph.get_all_drivers()
            for i in self.drivers_structure.get_starting_times(d, edge)
        }

        mu = self.get_dual_variable_from_constraint(
            "%s:%s:%s" % (labels.EDGE_TIME_UNICITY, repr(driver), str(edge))) or 0
        tau_start = - self.get_dual_variable_from_constraint(
            "%s:%s:%s:%s" % (labels.TRANSFERT, repr(driver), str(edge[0]), start)) or 0
        tau_end = - self.get_dual_variable_from_constraint(
            "%s:%s:%s:%s" % (labels.TRANSFERT, repr(driver), str(edge[1]), start)) or 0
        omega = self.get_dual_variable_from_constraint("%s:%s" % (labels.ENDING_TIME, repr(driver))) or 0

        func = self.graph.get_congestion_function(*edge)
        alpha = func(1) - func(0)

        reduced_cost = (end - start) * (lambda_minus.get((driver, start), 0) - lambda_plus.get((driver, start), 0)) + \
            self.bigM() * lambda_plus.get((driver, start), 0) + \
            alpha * sum(lambda_plus.get((d, i), 0) - lambda_minus.get((d, i), 0)
                        for d in self.drivers_graph.get_all_drivers()
                        for i in self.drivers_structure.get_starting_times(d, edge)
                        if start < i <= end) + \
            mu + (driver.end != edge[0]) * tau_start - (driver.end != edge[1]) * tau_end + \
            (driver.end == edge[1]) * (omega + start)

        return reduced_cost

    def build_variables(self):
        self.x = defaultdict(lambda: 0)
        for driver in self.drivers_graph.get_all_drivers():
            for edge in self.get_edges_for_driver(driver):
                self.generate_variables(driver, edge, self.iter_start_end_times_for_driver(driver, edge))

    def build_constraints(self, notify=True):
        if notify:
            log.info("ADDING Constraints ...")

        for driver in self.drivers_graph.get_all_drivers():
            self.add_constraint(
                quicksum(
                    quicksum(
                        self.x[(s, self.TEGgraph.build_node(driver.end, time)), driver]
                        for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
                    )
                    for time in self.drivers_structure.get_possible_ending_times_on_node(driver, driver.end)
                ) == 1,
                name="%s:%s" % (labels.ENDING_TIME, repr(driver))
            )
            for node in self.graph.nodes_iter():
                if node != driver.end:
                    for i in self.drivers_structure.iter_possible_time_on_node(driver, node):
                        node_ = self.TEGgraph.build_node(node, i)
                        self.add_constraint(
                            quicksum(
                                self.x[(node_, succ), driver] for succ in self.TEGgraph.successors_iter(node_)) -
                            quicksum(
                                self.x[(pred, node_), driver] for pred in self.TEGgraph.predecessors_iter(node_)) ==
                            1 * (node == driver.start and i == driver.time),
                            name="%s:%s:%s:%s" % (labels.TRANSFERT, repr(driver), str(node), i)
                        )
            for edge in self.graph.edges_iter():
                self.add_constraint(
                    quicksum(self.x[self.TEGgraph.build_edge(edge, i, j), driver]
                             for i, j in self.iter_start_end_times_for_driver(driver, edge)) <= 1,
                    name="%s:%s:%s" % (labels.EDGE_TIME_UNICITY, repr(driver), str(edge))
                )
                for i in self.drivers_structure.iter_starting_times(driver, edge):
                    self.add_constraint(
                        quicksum(self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i)
                                 for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i)) <=
                        self.graph.get_congestion_function(*edge)(
                            quicksum(
                                quicksum(self.x[self.TEGgraph.build_edge(edge, ii, jj), d]
                                         for ii, jj in self.iter_start_end_times_for_driver(d, edge) if ii < i <= jj)
                                for d in self.drivers_graph.get_all_drivers()
                            )
                        ),
                        name="%s:%s:%s:%s" % (labels.LOWER_WAITING_TIME, repr(driver), str(edge), i)
                    )
                    self.add_constraint(
                        quicksum(self.x[self.TEGgraph.build_edge(edge, i, j), driver] * (j - i)
                                 for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i)) +
                        self.bigM() * (1 - quicksum(
                            self.x[self.TEGgraph.build_edge(edge, i, j), driver]
                            for j in self.drivers_structure.iter_ending_times(driver, edge, starting_time=i))) >=
                        self.graph.get_congestion_function(*edge)(
                            quicksum(
                                quicksum(self.x[self.TEGgraph.build_edge(edge, ii, jj), d]
                                         for ii, jj in self.iter_start_end_times_for_driver(d, edge) if ii < i <= jj)
                                for d in self.drivers_graph.get_all_drivers()
                            )
                        ),
                        name="%s:%s:%s:%s" % (labels.UPPER_WAITING_TIME, repr(driver), str(edge), i)
                    )

        if notify:
            log.info("Constraints ADDED: %s" % ",".join("%s: %s added" % (n, c) for n, c in self.count.iteritems()
                                                        if n in labels.CONSTRAINTS))

    def set_objective(self):
        self.model.setObjective(
            quicksum(
                time * self.x[(s, self.TEGgraph.build_node(driver.end, time)), driver]
                for driver in self.drivers_graph.get_all_drivers()
                for time in self.drivers_structure.get_possible_ending_times_on_node(driver, driver.end)
                for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
            ),
            GRB.MINIMIZE
        )

    def get_objective_from_solution(self, x):
        return quicksum(
            time * x[(s, self.TEGgraph.build_node(driver.end, time)), driver]
            for driver in self.drivers_graph.get_all_drivers()
            for time in self.drivers_structure.get_possible_ending_times_on_node(driver, driver.end)
            for s in self.TEGgraph.predecessors_iter(self.TEGgraph.build_node(driver.end, time))
        )

    def set_optimal_solution(self):
        self.opt_solution = {}
        paths = {}
        for (edge, driver), var in self.x.iteritems():
            paths.setdefault(driver, {})
            if isinstance(var, Var) and var.X > 0:
                paths[driver][self.TEGgraph.get_original_edge(edge)] = var.X

        # If the solution is continuous, we split the drivers into smaller drivers
        if self.binary is False:
            paths_ = {}
            for driver in paths.iterkeys():
                cont_paths = Graph.get_paths_from_continuous_edge_description(driver.start, driver.end, paths[driver])
                for path, coeff in cont_paths.iteritems():
                    paths_[Driver(driver.start, driver.end, driver.time, coeff)] = \
                        list(self.graph.iter_edges_in_path(path))
            paths = paths_

        for driver, edges in paths.iteritems():
            self.set_optimal_path_to_driver(
                driver,
                self.graph.generate_path_from_edges(driver.start, driver.end, edges)
            )

    def set_horizon(self, horizon):
        super(TEGModel, self).set_horizon(horizon)
        self.TEGgraph.horizon = horizon
