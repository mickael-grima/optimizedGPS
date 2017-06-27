from collections import defaultdict

from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers
from optimizedGPS.problems.PreSolver import GlobalPreSolver
from optimizedGPS.problems.Solver import Solver


def get_percentage(part, total, trunc=2):
    return int(float(part) / total * (10 ** (trunc + 2))) / float((10 ** trunc))


def get_simple_stats():
    graph = generate_grid_data(7, 7)
    drivers_graph = generate_random_drivers(graph, 15)

    p = GlobalPreSolver(graph, drivers_graph)
    m = p.map_reachable_edges_for_drivers()
    stats = {
        "drivers": {
            id(driver): {
                "info": (driver.start, driver.end, driver.time),
                "stats": {
                    "edge_ratio": "%s%%" % get_percentage(len(m[driver]), graph.number_of_edges())
                }
            } for driver in drivers_graph.get_all_drivers()
        },
        "edges": {
            edge: {
                "stats": {
                    "drivers_ratio": "%s%%" % get_percentage(len(filter(lambda d: edge in m[d], m.keys())),
                                                             drivers_graph.number_of_drivers())
                }
            } for edge in graph.edges()
        },
        "general": {
            "unused_edges": len(filter(
                lambda edge: len(filter(lambda d: edge in m[d], m.keys())) == 0,
                graph.edges()
            )),
            "full_used_edges": len(filter(
                lambda edge: len(filter(lambda d: edge in m[d], m.keys())) == drivers_graph.number_of_drivers(),
                graph.edges()
            )),
            "edges_uses_repartition": defaultdict(lambda: 0)
        }
    }
    for edge, data in stats["edges"].iteritems():
        stats["general"]["edges_uses_repartition"][data["stats"]["drivers_ratio"]] += 1
    for ratio in stats["general"]["edges_uses_repartition"].iterkeys():
        stats["general"]["edges_uses_repartition"][ratio] = "%s%%" % get_percentage(
            stats["general"]["edges_uses_repartition"][ratio],
            graph.number_of_edges()
        )

    return stats


def get_average_unused_edges(length=5, width=5, number_of_drivers=10, niter=10):
    """
    iterate niter times on grid graph with given parameters, and return the average number of unused edges.

    :param length:
    :param width:
    :param number_of_drivers:
    :param niter:
    :return:
    """
    ratios = []
    for i in range(niter):
        graph = generate_grid_data(length=length, width=width)
        drivers_graph = generate_random_drivers(graph, total_drivers=number_of_drivers)
        presolver = GlobalPreSolver(graph, drivers_graph)
        ratios.append(get_percentage(len(list(presolver.iter_unused_edges())), graph.number_of_edges()))
    return sum(ratios) / float(len(ratios))


def test_running_time():
    pass


def compute_driver_influence_on_prersolving(length=3, width=3, niter=10):
    unused_edges = {}
    for n in range(1, length * width + 1, length):
        for _ in range(niter):
            graph = generate_grid_data(length=length, width=width)
            drivers_graph = generate_random_drivers(graph)
            presolver = GlobalPreSolver(graph, drivers_graph)
            unused_edges[n] = get_percentage(len(list(presolver.iter_unused_edges())), graph.number_of_edges())
    return unused_edges


def compute_variables_reduction(horizon=1000):
    """
    Check the reduction for a variable like x_{e,d,t}
    """
    graph = generate_grid_data(10, 10)
    drivers_graph = generate_random_drivers(graph, 15)
    max_nb_var = drivers_graph.number_of_drivers() * graph.number_of_edges() * horizon

    solver = Solver(graph, drivers_graph, None, None)
    solver.presolve()
    value = 0
    for driver in drivers_graph.get_all_drivers():
        for edge in solver.drivers_structure.get_possible_edges_for_driver(driver):
            start, end = solver.drivers_structure.get_safety_interval(driver, edge)
            if start >= horizon:
                continue
            elif end >= horizon:
                end = horizon
            value += end - start + 1

    return 100 - get_percentage(value, max_nb_var, trunc=10)


if __name__ == "__main__":
    # stats = get_simple_stats()
    # average_unused_edges = get_average_unused_edges(number_of_drivers=50, niter=1)
    # unused_edges = compute_driver_influence_on_prersolving(10, 10, 100)
    ratio = compute_variables_reduction()
    print ratio
