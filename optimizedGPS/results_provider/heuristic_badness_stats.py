
from utils import tools
from optimizedGPS.data.data_generator import generate_bad_heuristic_graphs
from optimizedGPS.problems.Heuristics import RealGPS
from optimizedGPS.problems.simulator import FromEdgeDescriptionSimulator


def get_RealGPS_badness_stats(congestions=iter([])):
    res = []
    traffic_influence = 2
    for annex_congestion in congestions:
        graph, drivers_graph = generate_bad_heuristic_graphs(traffic_influence, annex_congestion)
        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()

        drivers = sorted(drivers_graph.get_all_drivers(), key=lambda d: d.time)
        edge_description = {
            drivers[0]: ("0", "1", "3"),
            drivers[1]: ("0", "1", "3"),
            drivers[2]: ("0", "2"),
        }
        simulator = FromEdgeDescriptionSimulator(graph, drivers_graph, edge_description)
        simulator.simulate()

        res.append(tools.get_percentage(simulator.get_sum_ending_time(), heuristic.value))
    return res


if __name__ == "__main__":
    print get_RealGPS_badness_stats([1, 10, 100, 1000, 10000])
