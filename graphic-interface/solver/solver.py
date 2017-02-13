
from optimizedGPS.problems.Comparator import ResultsHandler
from optimizedGPS.problems.SearchProblem import BacktrackingSearch
from optimizedGPS.problems.Models import BestPathTrafficModel, FixedWaitingTimeModel
from optimizedGPS.problems.Heuristics import (
    ShortestPathTrafficFree,
    ShortestPathHeuristic,
    AllowedPathsHeuristic,
    UpdatedBySortingShortestPath
)


class GraphHandler(object):
    @classmethod
    def build_graph(cls, data):
        pass


class Solver(object):
    PROBLEMS = [BacktrackingSearch, BestPathTrafficModel, FixedWaitingTimeModel, ShortestPathTrafficFree,
                ShortestPathHeuristic, AllowedPathsHeuristic, UpdatedBySortingShortestPath]

    def __init__(self, data, parameters, problems, heuristics):
        self.results_handler = ResultsHandler()
        self.results_handler.setGraph(GraphHandler.build_graph(data))
        for problem in self.PROBLEMS:
            if problem.__name__ in problems or problem.__name__ in heuristics:
                self.results_handler.appendAlgorithm(problem, **parameters)

    def solve(self):
        self.results_handler.solve()

    def get_stats(self):
        stats = {}
        lower_value = self.results_handler.lower.getBestAlgo().getOptimalValue()
        for problem in self.results_handler.iterAlgorithms():
            opt_value = problem.getOptimalValue()
            stats[problem.__name__] = dict(
                status=self.results_handler.getStatus(problem.__name__),
                running_time=problem.getRunningTime(),
                value=opt_value,
                gap_opt_value=int((opt_value - lower_value) / lower_value * 100) / 10000.,
                av_gap_per_driver=problem.getAverageDrivingTimeGap(),
                var_gap_per_driver=problem.getVarianceDrivingTimeGap(),
                best_gap_per_driver=problem.getBestDrivingTimeGap(),
                worst_gap_per_driver=problem.getWorstDrivingTimeGap()
            )
        return stats

    def getProblems(self):
        return self.results_handler.getAlgorithmNames()
