# -*- coding: utf-8 -*-
# !/bin/env python

CONSTRAINTS = 'constraints'
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
EXACT_WAITING_TIME = "exact-waiting-time"
FUTURE_AFTER_PAST = "future-after-past"

DIFFERENCE_TO_SHORTEST_PATH = 'difference-to-shortest-path'
DIFFERENCE_TO_BEST_TRAFFIC = 'difference-to-best-traffic'

CONSTRAINTS = [STARTING_EDGES, ENDING_EDGES, INITIAL_CONDITIONS, NON_VISITED_EDGES, VISITED_EDGES, STARTING_ENDING,
               TRANSFERT, ENDING_TIME, NO_CYCLE, DIFFERENCE_TO_SHORTEST_PATH, DIFFERENCE_TO_BEST_TRAFFIC]
