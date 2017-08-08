# -*- coding: utf-8 -*-
# !/bin/env python

from optimizedGPS import labels

"""
Constants for structure classes.
Would be use later for computing the congestion functions.
"""

constants = {
    # Default distance of a road
    labels.DISTANCE: 100.0,
    # Default number of lanes for a road
    labels.LANES: 1,
    # default traffic after which a congestion appears
    labels.TRAFFIC_LIMIT: 1,
    # default car length
    labels.CAR_LENGTH: 2,
    # default max speed
    labels.MAX_SPEED: 50,
    # default longitude
    labels.LONGITUDE: None,
    # default latitude
    labels.LATITUDE: None
}
