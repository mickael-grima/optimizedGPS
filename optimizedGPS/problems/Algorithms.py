from Models import FixedWaitingTimeModel, TEGModel
from Problem import Problem, SolvinType
from Solver import Solver
from optimizedGPS.structure.DriversGraph import DriversGraph
from optimizedGPS.structure.DriversStructure import DriversStructure


class ConstantModelAlgorithm(Problem):
    def __init__(self, graph, drivers_graph, **kwargs):
        self.model = FixedWaitingTimeModel(graph, drivers_graph, **kwargs)
        for driver in self.model.drivers:
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
            for driver in self.model.drivers:
                path = self.model.get_optimal_driver_path(driver)
                waiting_times = self.model.get_optimal_driver_waiting_times(driver)
                for edge in self.get_graph().iter_edges_in_path(path):
                    self.model.set_waiting_time(driver, edge, waiting_times[edge])
                if better_solution:
                    self.set_optimal_path_to_driver(driver, path)
            if better_solution:
                self.value = self.model.value


class TEGColumnGenerationAlgorithm(Problem):
    def __init__(self, graph, drivers_graph, drivers_structure=None, **kwargs):
        super(TEGColumnGenerationAlgorithm, self).__init__(graph, drivers_graph, drivers_structure=drivers_structure,
                                                           **kwargs)
        sub_drivers_graph, sub_drivers_structure = self.get_initial_structures()
        self.solver = Solver(self.graph, sub_drivers_graph, TEGModel, drivers_structure=sub_drivers_structure,
                             presolvers={'LowerUpperBoundsPresolver'})

    def get_initial_structures(self):
        """
        1. Find the driver with the minimum ending time
        2. create a drivers graph containing only this driver
        3. Set every edges not on shortest path as unreachable
        4. Set presence interval for every reachable edges
        5. create the model with appropriate horizon
        """
        driver = min(
            self.drivers_graph.get_all_drivers(),
            key=lambda d: d.time + self.graph.get_lowest_driving_time(d)
        )
        path = self.graph.get_shortest_path(
            driver.start, driver.end, key=self.graph.get_minimum_waiting_time)

        sub_drivers_graph = DriversGraph()
        sub_drivers_graph.add_driver(driver)

        sub_drivers_structure = DriversStructure(self.graph, sub_drivers_graph)
        edges = set(self.graph.iter_edges_in_path(path))
        for edge in self.graph.edges_iter():
            if edge not in edges:
                sub_drivers_structure.set_unreachable_edge_to_driver(driver, edge)

        return sub_drivers_graph, sub_drivers_structure

    def iter_next_edges_for_generation(self):
        """
        iterate each driver and edges we want to generate as next step
        """
        driver = max(
            self.solver.drivers_graph.get_all_drivers(),
            key=self.solver.compute_difference_driving_time
        )
        traffic = self.solver.get_optimal_traffic()
        path = self.graph.get_shortest_path_with_traffic(driver.start, driver.end, driver.time, traffic)
        yield driver, self.graph.iter_edges_in_path(path)

    def solve_with_solver(self):
        """
        Solve the model and compare the values:
           - if we don't improve the value, add a new driver into the model, and compute his best path
           - else add a new path for the worst driver
        """
        self.solver.solve()
        if self.value == self.solver.value:  # Optimality reached for this set of drivers: add 1 driver
            traffic = self.solver.get_optimal_traffic()
            try:
                driver = min(
                    [driver for driver in self.drivers_graph
                     if driver not in set(self.solver.drivers_graph.get_all_drivers())],
                    key=lambda d: d.time + self.graph.get_lowest_driving_time_with_traffic(d, traffic)
                )
            except ValueError:  # Every drivers have already been added. Global optimality reached
                return
            path = map(
                lambda e: e[0],
                self.graph.get_shortest_path_with_traffic(driver.start, driver.end, driver.time, traffic)
            )
            unreachable_edges = [edge for edge in self.graph.edges_iter()
                                 if edge not in set(self.graph.iter_edges_in_path(path))]
            self.solver.add_driver(driver, unreachable_edges=unreachable_edges)
        else:  # Find a bad driver and generate variables
            for driver, edges in self.iter_next_edges_for_generation():
                self.solver.add_edges_for_driver(driver, edges)
                break
        self.value = self.solver.value
