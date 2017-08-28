# -*- coding: utf-8 -*-
# !/bin/env python

from optimizedGPS.logger import configure
configure()

import unittest
from collections import defaultdict

try:
    from gurobipy import Var, GRB
except ImportError:
    Var, GRB = None, None

from optimizedGPS import labels
from optimizedGPS.problems import labels as mlabels
from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers, generate_bad_heuristic_graphs
from optimizedGPS.problems.Heuristics import RealGPS
from optimizedGPS.problems.Models import TEGModel
from optimizedGPS.problems.Algorithms import TEGColumnGenerationAlgorithm
from optimizedGPS.problems.simulator import FromEdgeDescriptionSimulator
from optimizedGPS.problems.Solver import Solver
from optimizedGPS.structure import Driver, DriversGraph, GPSGraph


class ProblemsTest(unittest.TestCase):
    def test_problems_main_functionnalities(self):
        """
        We test here global method in main classes Problem, Model
        """
        graph = GPSGraph()
        graph.add_edge(1, 2, congestion_func=lambda x: 4 * x + 3)
        graph.add_edge(1, 3, congestion_func=lambda x: 2)
        graph.add_edge(3, 2, congestion_func=lambda x: 2)

        driver0, driver1 = Driver(1, 2, 0), Driver(1, 2, 1)
        drivers_graph = DriversGraph()
        drivers_graph.add_driver(driver0)
        drivers_graph.add_driver(driver1)

        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()
        variable_indexes = [(driver0, (1, 2), 0, 3), (driver1, (1, 3), 1, 3), (driver1, (3, 2), 3, 5)]
        self.assertEqual(set(heuristic.iter_variable_indexes_from_optimal_solution()), set(variable_indexes))
        self.assertEqual(len(list(heuristic.iter_variable_indexes_from_optimal_solution())), 3)

    @unittest.skipIf(Var is None, "gurobipy dependency not satisfied")
    def testTEGModel(self):
        # 1 driver
        graph = GPSGraph()
        graph.add_edge("0", "1", **{labels.CONGESTION_FUNC: lambda x: x + 2})
        graph.add_edge("0", "2", **{labels.CONGESTION_FUNC: lambda x: 2 * x + 2})
        graph.add_edge("1", "2", **{labels.CONGESTION_FUNC: lambda x: x + 1})

        drivers_graph = DriversGraph()
        driver = Driver("0", "2", 0)
        drivers_graph.add_driver(driver)

        model = TEGModel(graph, drivers_graph, horizon=2)
        model.build_model()

        self.assertEqual(len(model.x), 9)  # number of variables

        model.solve()

        self.assertEqual(model.opt_solution[driver], ('0', '2'))
        self.assertEqual(model.value, 2)

        # 3 drivers
        driver2 = Driver("0", "2", 0)
        driver3 = Driver("0", "2", 1)
        drivers_graph.add_driver(driver2)
        drivers_graph.add_driver(driver3)

        model = TEGModel(graph, drivers_graph, horizon=4)
        model.build_model()

        self.assertEqual(len(model.x), 90)

        model.solve()

        # test big M: is big M greater than the greatest waiting time ?
        for i in range(4):
            max_traffic = max(
                graph.get_congestion_function(*edge)(
                    sum(
                        sum(
                            model.x[model.TEGgraph.build_edge(edge, i, j), d].X
                            for j in model.drivers_structure.iter_ending_times(driver, edge, starting_time=i)
                            if isinstance(model.x[model.TEGgraph.build_edge(edge, i, j), d], Var)
                        )
                        for d in drivers_graph.get_all_drivers()
                    )
                )
                for edge in graph.edges_iter())
            self.assertGreaterEqual(model.bigM(), max_traffic)

        # Check feasibility
        x = defaultdict(lambda: 0)
        x[model.TEGgraph.build_edge(("0", "1"), 1, 3), driver3] = 1
        x[model.TEGgraph.build_edge(("1", "2"), 3, 4), driver3] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver2] = 1
        self.assertTrue(model.check_feasibility(x))
        self.assertEqual(model.get_objective_from_solution(x), 8)

        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver2] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 1, 7), driver3] = 1
        self.assertTrue(model.check_feasibility(x))
        self.assertEqual(model.get_objective_from_solution(x), 11)

        x = defaultdict(lambda: 0)
        for key, var in model.x.iteritems():
            if isinstance(var, Var):
                x[key] = var.X
        self.assertTrue(model.check_feasibility(x))

        # Check optimality
        self.assertEqual(model.opt_solution[driver], ('0', '2'))
        self.assertEqual(model.opt_solution[driver2], ('0', '2'))
        self.assertEqual(model.opt_solution[driver3], ('0', '1', '2'))
        self.assertEqual(model.value, 8)

    def test_real_GPS(self):
        graph = GPSGraph()
        graph.add_edge(0, 1, congestion_func=lambda x: 3 * x + 3)
        graph.add_edge(0, 2, congestion_func=lambda x: 4)
        graph.add_edge(1, 3, congestion_func=lambda x: 1)
        graph.add_edge(2, 3, congestion_func=lambda x: 4)
        graph.add_edge(3, 1, congestion_func=lambda x: 13)

        driver1 = Driver(0, 3, 0)
        driver2 = Driver(0, 3, 1)
        driver3 = Driver(0, 1, 2)
        drivers_graph = DriversGraph()
        drivers_graph.add_driver(driver1)
        drivers_graph.add_driver(driver2)
        drivers_graph.add_driver(driver3)

        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()

        self.assertEqual(heuristic.get_optimal_driver_path(driver1), (0, 1, 3))
        self.assertEqual(heuristic.get_optimal_driver_path(driver2), (0, 1, 3))
        self.assertEqual(heuristic.get_optimal_driver_path(driver3), (0, 1))
        self.assertEqual(heuristic.get_optimal_value(), 23)

    def test_opt_solution_for_real_GPS(self):
        graph = generate_grid_data(10, 10)
        graph.set_global_congestion_function(lambda x: 3 * x + 4)
        for _ in xrange(10):
            drivers_graph = generate_random_drivers(graph, 10)
            heuristic = RealGPS(graph, drivers_graph)
            heuristic.solve()
            for driver, path in heuristic.opt_solution.iteritems():
                self.assertEqual(path[0], driver.start)
                self.assertEqual(path[-1], driver.end)

    def test_heuristic_optimality(self):
        """
        On a given graph, heuristic is always bad
        """
        traffic_influence, annex_road_congestion = 2, 1
        graph, drivers_graph = generate_bad_heuristic_graphs(traffic_influence, annex_road_congestion)
        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()
        drivers = sorted(drivers_graph.get_all_drivers(), key=lambda d: d.time)

        # Check the optimal solution of heuristic
        self.assertEqual(
            ((("0", "2"), 0), (("2", "3"), 2)),
            filter(lambda o: o[0] == drivers[0], heuristic.iter_complete_optimal_solution())[0][1]
        )
        self.assertEqual(
            ((("0", "2"), 0), (("2", "3"), 2)),
            filter(lambda o: o[0] == drivers[1], heuristic.iter_complete_optimal_solution())[0][1]
        )
        self.assertEqual(
            ((("0", "1"), 1), (("1", "3"), 1 + traffic_influence), (("3", "2"), 3 + traffic_influence)),
            filter(lambda o: o[0] == drivers[2], heuristic.iter_complete_optimal_solution())[0][1]
        )
        self.assertEqual(heuristic.value, 2 * traffic_influence + annex_road_congestion + 9)

        # Check the real optimal solution
        edge_description = {
            drivers[0]: ("0", "1", "3"),
            drivers[1]: ("0", "1", "3"),
            drivers[2]: ("0", "2")
        }
        simulator = FromEdgeDescriptionSimulator(graph, drivers_graph, edge_description)
        simulator.simulate()

        starting_times = simulator.get_starting_times(drivers[0])
        self.assertEqual(
            [0, traffic_influence],
            map(lambda e: starting_times[e], graph.iter_edges_in_path(edge_description[drivers[0]]))
        )
        self.assertEqual(traffic_influence + 2, simulator.get_ending_time(drivers[0]))
        starting_times = simulator.get_starting_times(drivers[1])
        self.assertEqual(
            [0, traffic_influence],
            map(lambda e: starting_times[e], graph.iter_edges_in_path(edge_description[drivers[1]]))
        )
        self.assertEqual(traffic_influence + 2, simulator.get_ending_time(drivers[1]))
        starting_times = simulator.get_starting_times(drivers[2])
        self.assertEqual(
            [1],
            map(lambda e: starting_times[e], graph.iter_edges_in_path(edge_description[drivers[2]]))
        )
        self.assertEqual(3, simulator.get_ending_time(drivers[2]))

        self.assertEqual(2 * traffic_influence + 7, simulator.get_sum_ending_time())

    def test_solver_shared_memory(self):
        """
        Some data are shared with the algorithm inside solver (e.g. drivers_structure)
        Check whether this sharing is really working
        """
        graph, drivers_graph = generate_bad_heuristic_graphs()
        solver = Solver(graph, drivers_graph, TEGModel)

        # check the adresses
        self.assertEqual(id(solver.drivers_structure), id(solver.algorithm.drivers_structure))
        self.assertEqual(id(solver.graph), id(solver.algorithm.graph))
        self.assertEqual(id(solver.drivers_graph), id(solver.algorithm.drivers_graph))

        # if we update the drivers_structure, are the changes updated everywhere ?
        driver = solver.drivers_graph.get_all_drivers().next()
        edge = solver.graph.edges()[0]
        solver.drivers_structure.add_starting_times(driver, edge, 0, 1, 4)
        self.assertEqual(
            list(solver.drivers_structure.get_starting_times(driver, edge)),
            list(solver.algorithm.drivers_structure.get_starting_times(driver, edge))
        )

        solver.drivers_structure.set_unreachable_edge_to_driver(driver, edge)
        self.assertEqual(
            list(solver.drivers_structure.get_possible_edges_for_driver(driver)),
            list(solver.algorithm.drivers_structure.get_possible_edges_for_driver(driver))
        )

    @unittest.skipIf(Var is None, "gurobipy dependency not satisfied")
    def test_TEGModel_vs_RealGPS(self):
        traffic_influence, annex_road_congestion = 2, 10
        graph, drivers_graph = generate_bad_heuristic_graphs(traffic_influence, annex_road_congestion)

        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()

        algorithm = TEGModel(graph, drivers_graph, horizon=11)
        algorithm.build_model()
        algorithm.solve()

        self.assertEqual(heuristic.value - algorithm.value, annex_road_congestion + 2)

    @unittest.skipIf(Var is None, "gurobipy dependency not satisfied")
    def test_TEGModel_feasibility(self):
        graph, drivers_graph = generate_bad_heuristic_graphs()
        algorithm = TEGModel(graph, drivers_graph, horizon=12, binary=False)
        algorithm.build_model()
        algorithm.solve()

        for edge_, driver in algorithm.x.iterkeys():
            edge = algorithm.TEGgraph.get_original_edge(edge_)
            start = algorithm.TEGgraph.get_node_layer(edge_[0])
            end = algorithm.TEGgraph.get_node_layer(edge_[1])

            var_value = algorithm.x[edge_, driver].X if isinstance(algorithm.x[edge_, driver], Var) else 0
            self.assertIn(var_value, [0, 1])

            # Test the mu constraint: for one given edge and driver, there is at most one variable which is equal to 1
            if var_value == 1:
                for s, e in algorithm.drivers_structure.iter_time_intervals(driver, edge):
                    if (s, e) != (start, end):
                        v = algorithm.x[algorithm.TEGgraph.build_edge(edge, s, e), driver]
                        v = v.X if isinstance(v, Var) else 0
                        self.assertEqual(v, 0)

    @unittest.skipIf(Var is None, "gurobipy dependency not satisfied")
    def test_column_generation_algorithm(self):
        graph, drivers_graph = generate_bad_heuristic_graphs()

        algo = TEGColumnGenerationAlgorithm(graph, drivers_graph, horizon=7)
        algo.master.presolve()
        algo.master.algorithm.build_model()

        # Check number of initial variables
        number_vars = len(filter(lambda v: isinstance(v, Var), algo.master.algorithm.x.itervalues()))
        self.assertEqual(number_vars, 5)

        # Check the number of new variables: is the drivers_structure of algo different from the one used by algo.master
        count = sum([1 for driver in algo.drivers_graph.get_all_drivers() for edge in algo.graph.edges_iter()
                     for _, _ in algo.drivers_structure.iter_time_intervals(driver, edge)])
        self.assertEqual(count, 104)
        count_master = sum([1 for driver in algo.master.drivers_graph.get_all_drivers()
                            for edge in algo.master.drivers_structure.get_possible_edges_for_driver(driver)
                            for _, _ in algo.master.drivers_structure.iter_time_intervals(driver, edge)])
        self.assertEqual(count_master, 5)

        # Is the heuristic solution transform into variables for master ?
        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()
        for column in heuristic.iter_variable_indexes_from_optimal_solution():
            self.assertTrue(algo.master.algorithm.has_variable(*column))

        algo = TEGColumnGenerationAlgorithm(graph, drivers_graph, horizon=7)
        algo.solve()

        # Are the heuristic's initial variables still in the master problem ?
        x = defaultdict(lambda: 0)
        for column in heuristic.iter_variable_indexes_from_optimal_solution():
            self.assertTrue(algo.master.algorithm.has_variable(*column))
            x[algo.master.algorithm.TEGgraph.build_edge(*column[1:]), column[0]] = 1
        # self.assertEqual(list(heuristic.iter_variable_indexes_from_optimal_solution()), 0)
        self.assertTrue(algo.master.algorithm.check_feasibility(x))

        # The solution should always be better than the heuristic
        self.assertLessEqual(algo.value, heuristic.value)

        # Is the solution optimal
        opt_algo = TEGModel(graph, drivers_graph, horizon=10)
        opt_algo.build_model()
        opt_algo.solve()

        self.assertEqual(opt_algo.value, algo.value)


if __name__ == '__main__':
    unittest.main()
