# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple


# Status
SUCCESS = 0
FAILED = 1
TIMEOUT = 2
NOT_RUN = -1
STATUS = {
    SUCCESS: 'SUCCESS',
    FAILED: 'FAILED',
    TIMEOUT: 'TIMEOUT',
    NOT_RUN: 'NOT RUN'
}

LOWER_BOUND_LABEL = 'lower_bound'
UPPER_BOUND_LABEL = 'upper_bound'

ALGO = namedtuple('algo', ['algo', 'args', 'kwards'])

KNOWN_PROBLEMS = ["BacktrackingSearch", "BestPathTrafficModel", "FixedWaitingTimeModel"]
KNOWN_HEURISTICS = ["ShortestPathHeuristic", "AllowedPathsHeuristic", "UpdatedBySortingShortestPath",
                    "ShortestPathTrafficFree"]
