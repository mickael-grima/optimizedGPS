
from utils import tools
from optimizedGPS.data.data_generator import generate_random_drivers, generate_grid_data
from optimizedGPS.problems.Models import TEGModel
from optimizedGPS.problems.Solver import Solver


def compare_rows_and_columns_number(graph, drivers_numbers=iter([])):
    """
    Considering a graph, we compute number of variables and constraints for several drivers_graph (number of driver
    up to drivers_number). We return the ratio number_contraints / number_variables
    """
    res = {}
    for nb_drivers in drivers_numbers:
        ratios = []
        for _ in range(50):  # we take the average over 50 tries
            drivers_graph = generate_random_drivers(graph, nb_drivers)
            solver = Solver(graph, drivers_graph, TEGModel)
            solver.presolve()
            ratios.append(tools.get_percentage(
                solver.algorithm.number_of_constraints(), solver.algorithm.number_of_variables()))
        res[nb_drivers] = sum(ratios) / float(len(ratios))
    return res


def get_maximum_ratio_non_zero_variables(graph, drivers_numbers=iter([])):
    """
    Compute the worst number of non-zero variable: we assume that each driver has taken the longest path
    """
    res = {}
    for nb_drivers in drivers_numbers:
        ratios = []
        for _ in range(50):  # we take the average over 50 tries
            value = 0
            drivers_graph = generate_random_drivers(graph, nb_drivers)
            solver = Solver(graph, drivers_graph, TEGModel)
            solver.presolve()
            for driver in drivers_graph.get_all_drivers():
                value += len(graph.get_shortest_path(driver.start, driver.end, key=lambda u, v: - 1))
            ratios.append(tools.get_percentage(value, solver.algorithm.number_of_variables()))
        res[nb_drivers] = sum(ratios) / float(len(ratios))
    return res


if __name__ == "__main__":
    graph = generate_grid_data()
    graph.set_global_congestion_function(lambda x: 3 * x + 4)
    # print compare_rows_and_columns_number(graph, drivers_numbers=(20,))
    print get_maximum_ratio_non_zero_variables(graph, drivers_numbers=xrange(1, 10))
