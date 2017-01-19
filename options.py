# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple


# Graph labels
DEFAULT_DISTANCE = 100.0
DEFAULT_CAR_LENGTH = 2 # given in meter

TRAFFIC_LIMIT = 'traffic_limit'
LANES = 'lanes'
MAX_SPEED = 'max_speed'
ONEWAY = 'oneway'

LATITUDE = 'lat'
LONGITUDE = 'lon'

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
