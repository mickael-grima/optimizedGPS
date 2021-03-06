# -*- coding: utf-8 -*-
# !/bin/env python

import os


class SafeOpen(object):
    """
    A safe opening: if the directory doesn't exist, create it, and then open
    """
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def makeDir(self, directory):
        """ Check if the file directory exists, otherwise create the directory
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __enter__(self):
        self.makeDir('/'.join(self.filename.split('/')[:-1]))
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()


def around(number):
    """
    Truncate a float to the third decimal
    """
    if number is not None:
        return int(number * 1000) / 1000.
    else:
        return None
