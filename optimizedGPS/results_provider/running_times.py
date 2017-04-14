from optimizedGPS.problems.Models import TEGLinearCongestionModel
from optimizedGPS.problems.Comparator import ResultsHandler
from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers


def get_running_times():
    widths = range(2, 6)
    lengths = range(2, 6)

    result_handler = ResultsHandler()
    result_handler.append_algorithm(TEGLinearCongestionModel)
    for width in widths:
        for length in lengths:
            graph = generate_grid_data(length, width)
            generate_random_drivers(graph, seed=0)
            result_handler.append_graphs(graph)

    res = result_handler.compare()
    return result_handler.algorithms


if __name__ == "__main__":
    print get_running_times()
