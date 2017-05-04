"""
We merge here every steps of the solving procedure:
   1. Presolve the problem
   2. Separate the problem considering the drivers' graph
   3. Use an algorithm
"""
import sys

from optimizedGPS.problems.PreSolver import GlobalPreSolver, DrivingTimeIntervalPresolver
from optimizedGPS.problems.Problem import Problem

HORIZON = 1000


class Solver(Problem):
    def __init__(self, graph, drivers_graph, algorithm, drivers_structure=None, presolving=True, timeout=sys.maxint,
                 horizon=HORIZON, **kwargs):
        super(Solver, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure, timeout=timeout,
                                     horizon=horizon)
        self.drivers_graphs = {drivers_graph}

        self.presolving = presolving
        self.algorithm = algorithm
        self.parameters = kwargs

    def presolve(self):
        """
        Goal:
            1- reduce the number of nodes and edges which are useless in graph
            2- determine safety and presence intervals for each driver
            3- separate drivers into smaller independent sets of drivers if possible
        """
        # Clean the graph
        drivers_graph = self.drivers_graphs.pop()
        presolver = GlobalPreSolver(self.graph, drivers_graph, horizon=self.horizon)
        for edge in presolver.iter_unused_edges():
            if self.graph.has_edge(*edge):
                self.graph.remove_edge(*edge)
                if not self.graph.neighbors(edge[0]):
                    self.graph.remove_node(edge[0])
                if not self.graph.neighbors(edge[1]):
                    self.graph.remove_node(edge[1])
        self.horizon = presolver.get_horizon()

        # Clean the drivers
        presolver = DrivingTimeIntervalPresolver(self.graph, drivers_graph, horizon=self.horizon)
        presolver.solve()
        self.drivers_structure = presolver.drivers_structure
        self.drivers_structure.set_edges_to_drivers_graph()
        self.drivers_graphs = set(self.drivers_structure.split_drivers_graph())

    def solve(self):
        if self.presolving is True:
            self.presolve()
        self.value = 0
        for drivers_graph in self.drivers_graphs:
            algo = self.algorithm(self.graph, drivers_graph, drivers_structure=self.drivers_structure,
                                  horizon=self.horizon, timeout=self.timeout, **self.parameters)
            algo.solve()
            for driver, path in algo.iter_optimal_solution():
                self.set_optimal_path_to_driver(driver, path)
            self.value += algo.get_optimal_value()
