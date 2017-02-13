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

DIFFERENCE_TO_SHORTEST_PATH = 'difference-to-shortest-path'
DIFFERENCE_TO_BEST_TRAFFIC = 'difference-to-best-traffic'

CONSTRAINTS = [STARTING_EDGES, ENDING_EDGES, INITIAL_CONDITIONS, NON_VISITED_EDGES, VISITED_EDGES, STARTING_ENDING,
               TRANSFERT, ENDING_TIME, NO_CYCLE, DIFFERENCE_TO_SHORTEST_PATH, DIFFERENCE_TO_BEST_TRAFFIC]

STATS = {
    'running_time': None,
    'value': None,
    'gap_opt_value': None,
    'av_gap_per_driver': None,
    'var_gap_per_driver': None,
    'best_gap_per_driver': None,
    'worst_gap_per_driver': None,
    'status': None
}
