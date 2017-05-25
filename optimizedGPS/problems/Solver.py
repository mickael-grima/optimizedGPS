"""
We merge here every steps of the solving procedure:
   1. Presolve the problem
   2. Separate the problem considering the drivers' graph
   3. Use an algorithm
"""
import sys

from optimizedGPS.problems.PreSolver import GlobalPreSolver, DrivingTimeIntervalPresolver
from optimizedGPS.problems.Problem import Problem
from optimizedGPS import options


class Solver(Problem):
    def __init__(self, graph, drivers_graph, algorithm, drivers_structure=None, presolving=True, timeout=sys.maxint,
                 horizon=options.HORIZON, **kwargs):
        super(Solver, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure, timeout=timeout,
                                     horizon=horizon)
        self.presolving = presolving
        self.algorithm = algorithm(graph=graph, drivers_graph=drivers_graph, drivers_structure=drivers_structure,
                                   horizon=horizon, timeout=timeout, **kwargs)

    def presolve(self):
        """
        Goal:
            1- reduce the number of nodes and edges which are useless in graph
            2- determine safety and presence intervals for each driver
            3- separate drivers into smaller independent sets of drivers if possible
        """
        # Clean the graph
        presolver = GlobalPreSolver(self.graph, self.drivers_graph, horizon=self.horizon)
        for edge in presolver.iter_unused_edges():
            if self.graph.has_edge(*edge):
                self.graph.remove_edge(*edge)
                if not self.graph.neighbors(edge[0]):
                    self.graph.remove_node(edge[0])
                if not self.graph.neighbors(edge[1]):
                    self.graph.remove_node(edge[1])
        self.set_horizon(presolver.get_horizon())

        # Clean the drivers
        # TODO: add a initial drivers_structure
        presolver = DrivingTimeIntervalPresolver(
            self.graph, self.drivers_graph, drivers_structure=self.drivers_structure, horizon=self.horizon)
        presolver.solve()

        self.drivers_structure.horizon = self.horizon
        self.algorithm.drivers_structure = self.drivers_structure
        self.algorithm.set_horizon(self.horizon)
        self.algorithm.update()

    def solve(self):
        if self.presolving is True:
            self.presolve()

        self.algorithm.build_model()
        self.algorithm.solve()
        for driver, path in self.algorithm.iter_optimal_solution():
            self.set_optimal_path_to_driver(driver, path)
        self.value = self.algorithm.get_optimal_value()
