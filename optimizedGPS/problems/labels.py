# -*- coding: utf-8 -*-
# !/bin/env python

VARIABLES = 'variables'

STARTING_EDGES = 'starting-edges'
ENDING_EDGES = 'ending-edges'
INITIAL_CONDITIONS = 'initial-conditions'
NON_VISITED_EDGES = 'non-visited-edges-constraints'
VISITED_EDGES = 'visited-edges-constraints'
STARTING_ENDING = 'starting-ending'
TRANSFERT = 'transfert'
ENDING_TIME = 'ending-time'
NO_CYCLE = 'no-cycle'

ONE_DRIVER_PER_EDGE = "one-driver-per-edge"
TIME_TRANSFERT = "time-transfert"
LOWER_WAITING_TIME = "lower-waiting-time"
UPPER_WAITING_TIME = "upper-waiting-time"
EDGE_TIME_UNICITY = "edge_time_unicity"
FUTURE_AFTER_PAST = "future-after-past"
NO_INTERSECTION = "no_intersection"

DIFFERENCE_TO_SHORTEST_PATH = 'difference-to-shortest-path'
DIFFERENCE_TO_BEST_TRAFFIC = 'difference-to-best-traffic'

CONSTRAINTS = [STARTING_EDGES, ENDING_EDGES, INITIAL_CONDITIONS, NON_VISITED_EDGES, VISITED_EDGES, STARTING_ENDING,
               TRANSFERT, ENDING_TIME, NO_CYCLE, DIFFERENCE_TO_SHORTEST_PATH, DIFFERENCE_TO_BEST_TRAFFIC]
