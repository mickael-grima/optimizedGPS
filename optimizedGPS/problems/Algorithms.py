from Models import FixedWaitingTimeModel
from Problem import Problem, SolvinType


class ConstantModelAlgorithm(Problem):
    def __init__(self, graph, **kwargs):
        self.model = FixedWaitingTimeModel(graph, **kwargs)
        for driver in self.model.drivers:
            for edge in self.getGraph().edges():
                self.model.setWaitingTime(driver, edge, self.getGraph().get_congestion_function(*edge)(0))

        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(ConstantModelAlgorithm, self).__init__(**kwargs)

    def getGraph(self):
        return self.model.getGraph()

    def solve_with_heuristic(self):
        for i in range(10):
            self.model.solve()
            better_solution = self.value > self.model.value
            for driver in self.model.drivers:
                path = self.model.getOptimalDriverPath(driver)
                waiting_times = self.model.getOptimalDriverWaitingTimes(driver)
                for edge in self.getGraph().iter_edges_in_path(path):
                    self.model.setWaitingTime(driver, edge, waiting_times[edge])
                if better_solution:
                    self.addOptimalPathToDriver(driver, path)
            if better_solution:
                self.value = self.model.value
