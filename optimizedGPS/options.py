# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple
import os

def _import():
    try:
        import gurobipy
        return True
    except ImportError:
        return False


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

ALGO = namedtuple('algo', ['algo', 'args', 'kwargs'])
PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))

if _import() is True:
    KNOWN_PROBLEMS = ["BestPathTrafficModel", "FixedWaitingTimeModel", "TEGLinearCongestionModel"]
    KNOWN_HEURISTICS = ["ShortestPathHeuristic", "ShortestPathTrafficFree", "RealGPS"]
else:
    KNOWN_PROBLEMS = []
    KNOWN_HEURISTICS = ["ShortestPathHeuristic", "ShortestPathTrafficFree", "RealGPS"]

HORIZON = 1000
EXIT = "@@EXIT@@"
