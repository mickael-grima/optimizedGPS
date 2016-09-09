# -*- coding: utf-8 -*-
# !/bin/env python


def get_id(obj):
    return hash(obj)


def congestion_function(size, length, *parameters):
    if len(parameters) >= 2:
        return lambda x: parameters[0] * x * x * x * x + parameters[1]
    elif len(parameters) == 1:
        return lambda x: parameters[0] * x * x * x * x
    else:
        return lambda x: x * x * x * x
