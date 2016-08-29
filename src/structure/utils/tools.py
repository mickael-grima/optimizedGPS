# -*- coding: utf-8 -*-
# !/bin/env python


def congestion_function(**parameters):
    if 'a' in parameters:
        if 'b' in parameters:
            return lambda x: parameters['a'] * x * x * x * x + parameters['b']
        else:
            return lambda x: parameters[0] * x * x * x * x + 1
    else:
        return lambda x: x * x * x * x + 1
