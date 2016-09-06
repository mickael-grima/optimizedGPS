# -*- coding: utf-8 -*-
# !/bin/env python


def get_id(obj):
    return hash(obj)


def congestion_function(traffic, size, length, *parameters):
    if len(parameters) >= 2:
        return parameters[0] * traffic * traffic * traffic * traffic + parameters[1]
    elif len(parameters) == 1:
        return parameters[0] * traffic * traffic * traffic * traffic
    else:
        return traffic * traffic * traffic * traffic
