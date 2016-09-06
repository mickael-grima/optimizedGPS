# -*- coding: utf-8 -*-
# !/bin/env python

""" data should be created with data tools in folder data/
"""

from gurobipy import Model, GRB
import logging
from logger import configure
from data_generator import generate_graph_from_file

configure()
log = logging.getLogger(__name__)


def staticOptimalRouting(file_loc):
    prob = Model()
    g = generate_graph_from_file(file_loc)

    # Define the constants of the problem
    starting_flow = {n: sum(map(lambda el: el[1], g.getAllDriversFromStartingNode(n)))
                     for n in g.getAllStartingNodes()}
    ending_flow = {n: sum(map(lambda el: el[1], g.getAllDriversToEndingNode(n)))
                     for n in g.getAllStartingNodes()}

    # add variables
    x = {}
    for edge in g.getAllEdges():
        x[edge] = prob.addVar(0.0, name='x[%s]' % str(edge))
    prob.update()

    # add constraints
    for n in g.getAllNodes():
        prob.addConstr(sum(x[e] for e in g.getAllEdgesIncidentTo(n)) == sum(x[e] for e in g.getAllEdgesOutfrom(n)),
                       "flow_conservation_on_node_%s" % n)
    for n in g.getAllStartingNodes():
        prob.addConstr(sum(x[e] for e in g.getAllEdgesOutfrom(n)) == starting_flow[n],
                       "indoming_flow_on_node_%s" % n)
    for n in g.getAllEndingNodes():
        prob.addConstr(sum(x[e] for e in g.getAllEdgesIncidentTo(n)) == ending_flow[n],
                       "outcoming_flow_on_node_%s" % n)

    # add objective
    prob.setObjective(sum(g.getCongestionFunction(e[0], e[1])(x[e]) for e in g.getAllEdges()), GRB.MINIMIZE)
    return prob
