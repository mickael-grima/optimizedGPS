# -*- coding: utf-8 -*-
# !/bin/env python


class Driver(object):
    def __init__(self, start, end, time):
        self.start = start
        self.end = end
        self.time = time

    def to_tuple(self):
        return self.start, self.end, self.time
