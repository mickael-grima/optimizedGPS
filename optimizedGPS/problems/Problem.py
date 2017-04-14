# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import sys
import time

try:
    import gurobipy as gb
    from gurobipy import GurobiError
except ImportError:
    gb, GurobiError = None, None

from simulator import FromEdgeDescriptionSimulator
from optimizedGPS import options

__all__ = []

log = logging.getLogger(__name__)


class SolvinType:
    SOLVER = 0
    HEURISTIC = 1


class Problem(object):
    """ Initialize the problems' classes
    """
    def __init__(self, timeout=sys.maxint, solving_type=SolvinType.SOLVER):
        self.value = 0  # final value of the problem
        self.running_time = 0  # running time
        self.opt_solution = {}  # On wich path are each driver
        self.waiting_times = {}  # Waiting times of each driver for opt solution
        self.timeout = timeout  # After this time we stop the algorithms
        self.solving_type = solving_type

        self.status = options.NOT_RUN  # status

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
        Solve the current problem
        """
        if self.solving_type == SolvinType.HEURISTIC:
            self.solve_with_heuristic()
        elif self.solving_type == SolvinType.SOLVER:
            self.solve_with_solver()

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

    def iter_optimal_solution(self):
        """ yield for each driver his assigned path
        """
        for driver, path in self.opt_solution.iteritems():
            yield driver, path

    def get_graph(self):
        """
        return the graph (GPSGraph instance)
        """
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    def get_optimal_value(self):
        """
        Using the self.optimal_solution, we simulate with FromEdgeDescriptionSimulator the optimal value.
        """
        simulator = FromEdgeDescriptionSimulator(self.get_graph(), self.opt_solution)
        simulator.simulate()
        self.waiting_times = {driver: simulator.get_driver_waiting_times(driver)
                              for driver in self.get_graph().get_all_drivers()}
        return simulator.get_value()

    def set_optimal_value(self):
        """
        After solving, we set self.value using a simulator
        """
        self.value = self.get_optimal_value()

    def get_value(self):
        """
        Return the value obtained with the algorithm we used to solve the problem.

        ** IMPORTANT **: In order to compare different problem the method get_optimal_value should be used.
        """
        return self.value

    def get_running_time(self):
        return self.running_time


class SimulatorProblem(Problem):
    """ Initialize algorithm which use a simulator.
    The attribute simulator  should be instantiate in each subclass.
    The simulator should inherits from the super class Simulator
    """
    def get_graph(self):
        return self.simulator.graph

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
        self.value = self.get_optimal_value()


class Model(Problem):
    """ Initialize the models' classes
    """
    def __init__(self, graph, timeout=sys.maxint, solving_type=SolvinType.SOLVER, **params):
        super(Model, self).__init__(timeout=timeout, solving_type=solving_type)
        self.model = gb.Model()
        self.graph = graph
        params['TimeLimit'] = timeout
        params['LogToConsole'] = 0
        self.set_parameters(**params)

        self.count = {}

        self.initialize(**params)
        self.build_model()

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
        self.value = self.get_optimal_value()
        self.set_status(options.SUCCESS)

    def get_graph(self):
        return self.graph

    def get_objectif(self):
        try:
            return self.model.ObjVal
        except GurobiError:
            log.warning("problem has not been solved yet")
            return sys.maxint
