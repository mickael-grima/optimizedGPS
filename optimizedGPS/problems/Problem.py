# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import sys
import time
from collections import defaultdict

try:
    import gurobipy as gb
    from gurobipy import GurobiError
except ImportError:
    gb, GurobiError = None, None

from simulator import FromEdgeDescriptionSimulator
from optimizedGPS import options
from optimizedGPS.structure import DriversStructure

__all__ = []

log = logging.getLogger(__name__)


class SolvinType:
    SOLVER = 0
    HEURISTIC = 1


class Problem(object):
    """ Initialize the problems' classes
    """
    def __init__(self, graph, drivers_graph, drivers_structure=None, horizon=sys.maxint,
                 timeout=sys.maxint, solving_type=SolvinType.SOLVER,):
        self.graph = graph
        self.drivers_graph = drivers_graph
        self.drivers_structure = drivers_structure or DriversStructure(graph, drivers_graph, horizon=horizon)

        self.value = 0  # final value of the problem
        self.running_time = 0  # running time
        self.timeout = timeout  # After this time we stop the algorithms
        self.solving_type = solving_type
        self.status = options.NOT_RUN  # status
        self.horizon = horizon

        self.opt_solution = {}  # On wich path are each driver
        self.opt_simulator = None
        """
        Given a driver, if an edge is not in the associated set, the driver will never use it in the optimal solution
        """
        self.unreachable_edges_for_driver = defaultdict(set)

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def solve_with_solver(self):
        """
        Implement this method when using Gurobi
        """
        message = "Solution with solver not implemented yet"
        log.error(message)
        raise NotImplementedError(message)

    def solve_with_heuristic(self):
        """
        Implement this method when solving with another algorithm (For example polynomial one)
        """
        message = "No heuristics available yet"
        log.error(message)
        raise NotImplementedError(message)

    def solve(self):
        """
        Solve the current problem.
        The optimal solution has to be set during the solving
        """
        if self.solving_type == SolvinType.HEURISTIC:
            self.solve_with_heuristic()
        elif self.solving_type == SolvinType.SOLVER:
            self.solve_with_solver()
        self.opt_simulator = FromEdgeDescriptionSimulator(
            self.get_graph(), self.get_drivers_graph(), self.opt_solution)
        self.opt_simulator.simulate()
        self.set_optimal_value()

    def set_optimal_solution(self):
        """
        Set the optimal solution. Should be used after solving
        """
        message = "Not implemented yet"
        log.error(message)
        raise NotImplementedError(message)

    def get_optimal_driver_path(self, driver):
        """
        Return the optimal path set to driver

        :param driver: Driver object
        :return: tuple of nodes
        """
        return self.opt_solution.get(driver, ())

    def set_optimal_path_to_driver(self, driver, path):
        """
        Assign a path to driver

        :param driver: Driver object
        :param path: nodes' tuple
        :return:
        """
        if not isinstance(path, tuple):
            message = "Path should be a tuple of nodes"
            log.error(message)
            raise TypeError(message)
        self.opt_solution[driver] = path

    def get_edges_for_driver(self, driver):
        """
        return the set of edges on which the driver can drive
        """
        if self.drivers_structure is not None:
            return self.drivers_structure.get_possible_edges_for_driver(driver)

    def get_time_interval(self, driver, edge):
        if self.drivers_structure is not None:
            start, end = self.drivers_structure.get_safety_interval(driver, edge)
            return start if start is not None else 0, end if end is not None else 0
        else:
            return 0, self.drivers_structure.horizon

    def iter_optimal_solution(self):
        """ yield for each driver his assigned path
        """
        for driver, path in self.opt_solution.iteritems():
            yield driver, path

    def iter_complete_optimal_solution(self):
        """
        return for each driver his optimal path and the starting time on each edge
        """
        for driver in self.get_drivers_graph().get_all_drivers():
            optimal_path = self.opt_solution[driver]
            starting_times = self.opt_simulator.get_starting_times(driver)
            yield driver, ((edge, starting_times[edge]) for edge in self.graph.iter_edges_in_path(optimal_path))

    def get_graph(self):
        """
        return the graph (GPSGraph instance)
        """
        return self.graph

    def get_drivers_graph(self):
        """
        return the drivers' graph (DriversGraph instance)
        """
        return self.drivers_graph

    def get_drivers_structure(self):
        return self.drivers_structure

    def get_optimal_value(self):
        """
        Using the self.optimal_solution, we simulate with FromEdgeDescriptionSimulator the optimal value.
        """
        return self.value

    def get_partial_optimal_value(self, drivers=()):
        """
        Compute the optimal value only for the given set of drivers

        :param drivers: set of drivers
        :return:
        """
        if len(drivers) == 0:
            return 0
        simulator = FromEdgeDescriptionSimulator(
            self.get_graph(),
            self.get_drivers_graph(),
            {driver: self.opt_solution[driver] for driver in drivers}
        )
        simulator.simulate()
        return simulator.get_value()

    def set_optimal_value(self):
        """
        After solving, we set self.value using a simulator
        """
        self.value = self.opt_simulator.get_value()

    def get_value(self):
        """
        Return the value obtained with the algorithm we used to solve the problem.

        ** IMPORTANT **: In order to compare different problem the method get_optimal_value should be used.
        """
        return self.value

    def get_running_time(self):
        return self.running_time

    def get_driver_driving_time(self, driver):
        """
        Return the driving time of driver considering the optimal solution

        :param driver: Driver object
        :return: Integer
        """
        value = 0
        waiting_times = {driver: self.opt_simulator.get_driver_waiting_times(driver)
                         for driver in self.get_drivers_graph().get_all_drivers()}
        for edge in self.get_graph().iter_edges_in_path(self.get_optimal_driver_path(driver)):
            value += waiting_times[driver][edge]
        return value

    def is_edge_reachable_for_driver(self, driver, edge):
        return edge not in self.unreachable_edges_for_driver.get(driver, set())


class SimulatorProblem(Problem):
    """ Initialize algorithm which use a simulator.
    The attribute simulator  should be instantiate in each subclass.
    The simulator should inherits from the super class Simulator
    """
    def set_optimal_solution(self):
        self.opt_solution = {}
        for driver, path in self.simulator.iter_edge_description():
            self.set_optimal_path_to_driver(driver, path)

    def simulate(self):
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    def solve_with_heuristic(self):
        ct = time.time()

        # simulate
        self.simulate()

        self.running_time = time.time() - ct


class Model(Problem):
    """ Initialize the models' classes
    """
    def __init__(self, graph, drivers_graph, drivers_structure=None, timeout=sys.maxint, horizon=sys.maxint,
                 solving_type=SolvinType.SOLVER, **params):
        super(Model, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure, horizon=horizon,
                                    timeout=timeout, solving_type=solving_type)
        self.model = gb.Model()
        params['TimeLimit'] = timeout
        params['LogToConsole'] = 0
        self.set_parameters(**params)

        self.count = {}

        self.initialize(**params)

    def initialize(self, *args, **kwargs):
        """
        We initialize here every attributes before building the model
        """
        pass

    def set_parameters(self, **kwargs):
        """
        Set Gurobi parameters
        """
        for key, value in kwargs.iteritems():
            if key != "horizon":
                self.model.setParam(key, value)

    def build_constants(self):
        """
        Set the constants of the problem
        """
        pass

    def build_variables(self):
        """
        Set the variables of the problem
        """
        pass

    def add_constraint(self, constraint, name=None):
        """ constraint: constraint to add
            name: name of the constraint. For counting we split this name wrt ":".
            after ":" the words are here only to make the constraint unique inside Gurobipy
        """
        if name is None:
            name = 0
            while str(name) in self.count:
                name += 1

        name = str(name)
        self.count.setdefault(name.split(':')[0], 0)
        self.model.addConstr(constraint, name)
        self.count[name.split(':')[0]] += 1

    def build_constraints(self):
        """
        Set the constraints of the problem
        """
        pass

    def set_objective(self):
        """
        Set the constants of the problem
        """
        pass

    def build_model(self):
        log.info("** Model building STARTED **")
        self.build_constants()
        self.build_variables()
        self.model.update()
        self.build_constraints()
        self.set_objective()
        log.info("** Model building FINISHED **")

    def optimize(self):
        self.model.optimize()

    def solve_with_solver(self):
        t = time.time()
        self.optimize()
        self.running_time = time.time() - t
        self.set_optimal_solution()
        self.set_status(options.SUCCESS)

    def get_graph(self):
        return self.graph

    def get_drivers_graph(self):
        return self.drivers_graph

    def get_objectif(self):
        try:
            return self.model.ObjVal
        except GurobiError:
            log.warning("problem has not been solved yet")
            return sys.maxint
