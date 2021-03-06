"""
We merge here every steps of the solving procedure:
   1. Presolve the problem
   2. Separate the problem considering the drivers' graph
   3. Use an algorithm
"""
import sys

from optimizedGPS.problems.PreSolver import HorizonPresolver, SafetyIntervalsPresolver
from optimizedGPS.problems.Problem import Problem
from optimizedGPS import options


class Solver(Problem):
    DEFAULT_PRESOLVERS = {"HorizonPresolver"}

    def __init__(self, graph, drivers_graph, algorithm, drivers_structure=None, presolvers=None, timeout=sys.maxint,
                 horizon=options.HORIZON, **kwargs):
        super(Solver, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure, timeout=timeout,
                                     horizon=horizon)
        self.presolvers = presolvers if presolvers is not None else self.DEFAULT_PRESOLVERS
        self.algorithm = algorithm(graph=graph, drivers_graph=drivers_graph, drivers_structure=self.drivers_structure,
                                   horizon=horizon, timeout=timeout, **kwargs)

    def presolve(self):
        """
        Goal:
            1- reduce the number of nodes and edges which are useless in graph
            2- determine safety and presence intervals for each driver
            3- separate drivers into smaller independent sets of drivers if possible
        """
        if HorizonPresolver.__name__ in self.presolvers:
            presolver = HorizonPresolver(self.graph, self.drivers_graph, self.drivers_structure,
                                         horizon=self.horizon)
            presolver.solve()
            self.set_horizon(min(presolver.get_horizon(), self.horizon))

        self.algorithm.set_horizon(self.horizon)

        if SafetyIntervalsPresolver.__name__ in self.presolvers:
            presolver = SafetyIntervalsPresolver(self.graph, self.drivers_graph, self.drivers_structure,
                                                 horizon=self.horizon)
            presolver.solve()

    def solve_with_solver(self):
        self.presolve()
        self.algorithm.build_model()
        self.algorithm.solve_with_solver()
        self.opt_solution = {}
        for driver, path in self.algorithm.iter_optimal_solution():
            self.set_optimal_path_to_driver(driver, path)
        self.set_status(options.SUCCESS)
