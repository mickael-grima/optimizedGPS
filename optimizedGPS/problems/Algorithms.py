import sys

from Heuristics import RealGPS
from Models import FixedWaitingTimeModel, TEGModel
from Problem import Problem, SolvinType
from Solver import Solver
from optimizedGPS.structure.DriversStructure import DriversStructure
from optimizedGPS.structure.Graph import Graph


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
        self.master = Solver(self.graph, drivers_graph, TEGModel, drivers_structure=sub_drivers_structure, binary=False)

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
                except (KeyError, IndexError):
                    pass
                i += 1
            drivers_structure.add_ending_times(
                driver, edge, driver.time + self.heuristic.get_driver_driving_time(driver))

        return drivers_structure

    def get_TEGgraph(self):
        return self.master.algorithm.TEGgraph

    def set_optimal_solution(self):
        for driver, path in self.master.iter_optimal_solution():
            self.set_optimal_path_to_driver(driver, path)

    def get_next_columns(self):
        """
        We minimize the reduced cost (see master) over a specified set of paths for each driver.
        """
        # TODO: add a limit to the paths iteration
        best_driver, best_path, best_value = None, None, sys.maxint
        teg = self.get_TEGgraph()
        for driver in self.drivers_graph.get_all_drivers():
            traffic = self.master.get_optimal_traffic()
            n_org = 0
            for extended_path in self.graph.get_sorted_paths_with_traffic(
                    driver.start, driver.end, driver.time, traffic, delta=10):
                if n_org == self.graph.number_of_edges():
                    break
                path = tuple(map(lambda e: e[0], extended_path))
                n = 0
                for path_ in teg.iter_time_paths_from_path(path):
                    if n == self.graph.number_of_edges():
                        break
                    value = 0
                    for edge_ in Graph.iter_edges_in_path(path_):
                        edge = teg.get_original_edge(edge_)
                        start = teg.get_node_layer(edge_[0])
                        end = teg.get_node_layer(edge_[1])
                        value += self.master.algorithm.get_reduced_cost(driver, edge, start, end)
                    if value < best_value:
                        best_driver, best_path = driver, path_
                        best_value = value
                    n += 1
                n_org += 1
        return map(
            lambda e_: (best_driver, teg.get_original_edge(e_), teg.get_node_layer(e_[0]), teg.get_node_layer(e_[1])),
            Graph.iter_edges_in_path(best_path)
        )

    def add_column_to_master(self, column):
        driver, edge, start, end = column
        self.master.drivers_structure.add_starting_times(driver, edge, start)
        self.master.drivers_structure.add_ending_times(driver, edge, end)
        update = self.master.algorithm.generate_variables(driver, edge, [(start, end)])
        self.master.algorithm.generate_constraints(driver, edge, [(start, end)])
        return update

    def solve_master_as_integer(self):
        """
        Solve the master problem with integer variables
        """
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
            print self.master.algorithm.model.objVal
            next_columns = self.get_next_columns()
            if not next_columns:
                break  # Optimality reached
            update = False
            for column in next_columns:
                update = update or self.add_column_to_master(column)
            if update is False:
                break
        self.solve_master_as_integer()
        self.set_optimal_solution()
