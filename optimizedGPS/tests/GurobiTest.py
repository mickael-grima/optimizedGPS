# -*- coding: utf-8 -*-
# !/bin/env python

import unittest


class GurobiTest(unittest.TestCase):
    """
    Test if gurobipy package is install
    """
    def test(self):
        def _import():
            try:
                import gurobipy
                return True
            except ImportError:
                return False
        self.assertTrue(_import())


if __name__ == "__main__":
    unittest.main()
