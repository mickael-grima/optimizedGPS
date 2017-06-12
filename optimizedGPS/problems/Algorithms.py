from Models import FixedWaitingTimeModel, TEGModel
from Heuristics import RealGPS, ReducedTEGModel
from Problem import Problem, SolvinType
from Solver import Solver
from optimizedGPS.structure.DriversStructure import DriversStructure


class ConstantModelAlgorithm(Problem):
    def __init__(self, graph, drivers_graph, **kwargs):
        self.model = FixedWaitingTimeModel(graph, drivers_graph, **kwargs)
        for driver in self.model.drivers_graph.get_all_drivers():
            for edge in self.get_graph().edges():
                self.model.set_waiting_time(driver, edge, self.get_graph().get_congestion_function(*edge)(0))

        kwargs["solving_type"] = SolvinType.HEURISTIC
        super(ConstantModelAlgorithm, self).__init__(**kwargs)

    def get_graph(self):
        return self.model.get_graph()

    def get_drivers_graph(self):
        return self.model.get_drivers_graph()

    def solve_with_heuristic(self):
        for i in range(10):
            self.model.solve()
            better_solution = self.value > self.model.value
            for driver in self.model.drivers_graph.get_all_drivers():
                path = self.model.get_optimal_driver_path(driver)
                waiting_times = self.model.get_optimal_driver_waiting_times(driver)
                for edge in self.get_graph().iter_edges_in_path(path):
                    self.model.set_waiting_time(driver, edge, waiting_times[edge])
                if better_solution:
                    self.set_optimal_path_to_driver(driver, path)
            if better_solution:
                self.value = self.model.value


class TEGColumnGenerationAlgorithm(Problem):
    def __init__(self, graph, drivers_graph, drivers_structure=None, heuristic=None, **kwargs):
        super(TEGColumnGenerationAlgorithm, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure,
                                                           **kwargs)
        self.heuristic = heuristic if heuristic is not None else RealGPS(graph, drivers_graph)
        sub_drivers_structure = self.get_initial_structures()
        self.master = Solver(self.graph, drivers_graph, TEGModel, drivers_structure=sub_drivers_structure)
        self.reducer = Solver(self.graph, drivers_graph, ReducedTEGModel, drivers_structure=sub_drivers_structure)

    def get_initial_structures(self):
        """
        1. Solve the heuristic
        2. Build structure taking the found optimal solution:
             - for each driver and each visited edge, add as starting (resp. ending) time the unique driver's starting
             (resp. ending) on the given edge
        """
        self.heuristic.solve()

        # Build the initial structure
        drivers_structure = DriversStructure(self.graph, self.drivers_graph)
        for driver, opt_solution in self.heuristic.iter_complete_optimal_solution():
            i, edge = 0, None
            while edge is None or edge[1] != driver.end:
                edge, starting_time = opt_solution[i]
                drivers_structure.add_starting_times(driver, edge, starting_time)
                try:
                    drivers_structure.add_ending_times(driver, edge, opt_solution[i + 1][1])
                except KeyError:
                    pass
                i += 1
            drivers_structure.add_ending_times(
                driver, edge, driver.time + self.heuristic.get_driver_driving_time(driver))

        return drivers_structure

    def set_optimal_solution(self):
        for driver, path in self.master.iter_optimal_solution():
            self.set_optimal_path_to_driver(driver, path)

    def update_reducer(self):
        raise NotImplementedError()

    def get_next_column(self):
        raise NotImplementedError()

    def add_column_to_master(self):
        raise NotImplementedError()

    def solve_with_solver(self):
        """
        Classical column generation algorithm:
          1. Solve the master problem
          2. Solve the reduced problem taking the dual solution of the master problem.
             This returns us the best next column to add
          3. If optimality, stop, else add the next column and restart from 1.
        """
        while True:
            self.master.solve()
            self.update_reducer()
            self.reducer.solve()
            next_column = self.get_next_column()
            if next_column is None:
                break  # Optimality reached
            else:
                self.add_column_to_master()
        self.set_optimal_solution()
