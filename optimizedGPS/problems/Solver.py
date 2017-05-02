"""
We merge here every steps of the solving procedure:
   1. Presolve the problem
   2. Separate the problem considering the drivers' graph
   3. Use an algorithm
"""


class Solver(object):
    def __init__(self, graph, algorithm, presolver=None, **kwargs):
        self.graph = graph
        self.presolver = presolver
        self.algorithm = algorithm
        self.parameters = kwargs

    def presolve(self):
        if self.presolver is not None:
            self.presolver(self.graph).solve()
            # TODO: find reachable edges for each driver

    def solve(self):
        self.presolve()
        self.algorithm(self.graph, **self.parameters).solve()
