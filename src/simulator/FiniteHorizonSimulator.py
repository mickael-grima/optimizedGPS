# -*- coding: utf-8 -*-
# !/bin/env python

from Simulator import Simulator
from utils.tools import get_id, splitObjectsInBoxes, assert_paths_in_graph
import logging

log = logging.getLogger(__name__)


class FiniteHorizonSimulator(Simulator):
    """ how to use the simulator:
        while there are drivers on the road:
            1) update the next edges for each drivers in self.moved.
                next_edges is {driver: [(next_edge)]}
            2) simulate one step

        A group of drivers is a tuple (starting node, ending node, starting time)
    """

    def __init__(self, graph, allowed_paths=[]):
        """ paths = {path: {time: nb_drivers}}
            for each path we associate pairs of time, nb of drivers starting at this time
        """
        super(Simulator, self).__init__()
        assert_paths_in_graph(allowed_paths, graph, simulator_type=1)
        self.graph = graph
        # allowed paths: each driver should use one of these paths
        # if for a driver (start, end, time) we don't have any paths associated to (start, end)
        # then the driver can take any paths
        # here is stored the edges that are allowed in one path at least.
        self.allowed_edges = {}  # TODO to modify completely: doesn't work
        for path in allowed_paths:
            for edge in graph.getAllEdges():
                i = 0
                while i < len(path) and path[i] != edge[0]:
                    i += 1
                if i + 2 < len(path) and path[i + 1] == edge[1]:
                    self.allowed_edges.setdefault(edge, {})
                    self.allowed_edges[edge].setdefault((path[0], path[-1]), set())
                    self.allowed_edges[edge][path[0], path[-1]].add(path[i + 1:])
        self.initialize()

    def initialize(self, initial_time=0):
        """ we declare here every variable which will be modified during the simulation
        """
        self.previous_states = []
        # we use ids which we store here
        self.ids = {}
        self.drivers = {}  # how many drivers with given idd still on road
        # the drivers for whom we don't know the next edge
        self.moved = {}
        # the next edge where drivers will move
        self.next_moves = set()
        # for each edge we store the clocks of drivers on this edge
        # the list has to be always sorted
        # to each edge we associate a dictionnary where for a ending node we store the list of drivers' clocks
        # who wants to finish at the ending point
        self.clocks = {(): []}
        # how long have drivers been on the road
        self.time = 0
        # traffic
        self.traffics = {}
        # for the key out, we store the list of driver's clocks who didn't start yet (sorted)
        for s, e, t, n in self.graph.getAllDrivers():
            idd, ind = get_id(((s, e, t), ())), None
            self.ids[idd] = ((s, e, t), ())
            for _ in range(n):
                ind = self.insert_new_clock(idd, ind=ind)
            self.drivers[idd] = n
            self.moved[idd] = n
        # for each driver we store the next_edges
        self.next_edges = {}

    def reinitialize(self, state={}):
        """ if state is not empty, it describes a previous step of the simulator.
            We restore the current state to this previous one
        """
        if not state:
            self.initialize()
        else:
            self.drivers = state.get('drivers', self.drivers)
            self.moved = state.get('moved', self.moved)
            self.clocks = state.get('clocks', self.clocks)
            self.time = state.get('time', self.time)
            self.next_edges = state.get('next_edges', self.next_edges)
            self.traffics = state.get('traffics', self.traffics)
            self.next_moves = state.get('next_moves', self.next_moves)
            self.ids = state.get('ids', self.ids)

    def getCurrentState(self):
        drivers = {}
        for idd, n in self.drivers.iteritems():
            drivers[idd] = n
        moved = {}
        for idd, n in self.moved.iteritems():
            moved[idd] = n
        clocks = {}
        for e, lst in self.clocks.iteritems():
            clocks[e] = []
            for el in lst:
                clocks[e].append(el)
        time = self.time
        next_edges = {}
        for idd, dct in self.next_edges.iteritems():
            next_edges[idd] = {}
            for edge, value in dct.iteritems():
                next_edges[idd][edge] = value
        traffics = {}
        for e, traffic in self.traffics.iteritems():
            traffics[e] = traffic
        next_moves = set()
        for edge in self.next_moves:
            next_moves.add(edge)
        ids = {}
        for idd, el in self.ids.iteritems():
            ids[idd] = el

        return {
            'drivers': drivers,
            'moved': moved,
            'clocks': clocks,
            'time': time,
            'next_edges': next_edges,
            'traffics': traffics,
            'next_moves': next_moves,
            'ids': ids
        }

    def getMovedDrivers(self):
        return self.moved.iteritems()

    def get_total_time(self):
        return self.time

    def has_previous_state(self):
        return len(self.previous_states) > 0

    def save_current_state(self):
        self.previous_states.append(self.getCurrentState())

    def previous(self, state=None):
        if state is not None:
            self.reinitialize(state=state)
        elif self.has_previous_state():
            self.reinitialize(state=self.previous_states[-1])
            del self.previous_states[-1]
        else:
            log.error("No previous state found")
            raise Exception("No previous state found")

    # --------------------------------------------------------------------------------------------------------------
    # ------------------------------------- UPDATE EDGES ----------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------

    def getAllowedEdges(self, idd):
        """ return the allowed edge for driver in graph.
            Furthermore the returned edges belong to an allowed path (if given)

            IMPORTANT: an iterator here is needed, for the cutting strategy
        """
        # if driver didn't reach his end node
        driver, path = self.ids[idd]
        if path == () or path[-1] != driver[1]:
            node = path[-1] if path else driver[0]
            for n in self.graph.getSuccessors(node):
                if n not in path:
                    yield node, n

    def possibilities_iterator(self, idd, n):
        """ IMPORTANT: we need here an iterator to optimize the cutting strategy
        """
        # nxt_edges is a dictionnary where we associate to each edge a number
        # See splitObjectsInBoxes() function for further explanation
        nxt_edges = list(self.getAllowedEdges(idd))
        for sol in splitObjectsInBoxes(len(nxt_edges), n):
            yield {nxt_edges[i]: sol[i] for i in range(len(nxt_edges)) if sol[i] > 0}

    def iter_possibilities(self):
        """ compute every possibilities for given drivers

            IMPORTANT: this function has to be an iterator, in order to optimize the running time
                       if not the cutting strategy is useless !!!
        """
        # initialize the iterators
        iterators, possibility, ids = [], {}, []
        for idd, n in self.getMovedDrivers():
            iterator = self.possibilities_iterator(idd, n)
            try:
                possibility[idd] = iterator.next()
                iterators.append(iterator)
                ids.append((idd, n))
            except StopIteration:  # without possibility means driver is done
                continue
        yield possibility

        # explore each possibility
        i = len(iterators) - 1
        while i >= 0:
            idd, n = ids[i]
            try:
                nxt_edges = iterators[i].next()
            except StopIteration:
                iterators[i] = self.possibilities_iterator(idd, n)
                i -= 1
                continue
            possibility[idd] = nxt_edges
            if i < len(iterators) - 1:
                i += 1
                continue
            yield possibility

    def updateNextEdges(self, next_edges):
        """ we update here the next_edges for each drivers.
            Each driver should have a next_edge, except if he reached his end node

            WARNING: to be used in an other script after each step !!!
        """
        for idd, dct in next_edges.iteritems():
            if idd not in self.ids:
                driver, path = self.ids[idd]
                log.error("Driver %s missing in simulator's data for given path %s", str(driver), str(path))
                raise KeyError("Driver %s missing in simulator's data for given path %s" % (str(driver), str(path)))
            self.next_edges.setdefault(idd, {})
            self.next_edges[idd].update(dct)
        self.moved = {}

    # --------------------------------------------------------------------------------------------------------------
    # ---------------------------------- SIMULATION FUNCTIONS ------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------

    def insert_new_clock(self, idd, ind=None):
        driver, path = self.ids[idd]
        edge = (path[-2], path[-1]) if path else ()
        clock = self.compute_clock(edge) if edge != () else driver[2]
        self.clocks.setdefault(edge, [])
        if ind is None:
            k = 0
            while k < len(self.clocks[edge]) and self.clocks[edge][k][1] < clock:
                k += 1
        else:
            k = ind
        self.clocks[edge].insert(k, (idd, clock))
        if edge != ():
            self.time += clock
        return k

    def compute_clock(self, edge):
        return self.graph.getCongestionFunction(*edge)(self.traffics.get(edge) or 0.0)

    def update_traffics(self, edge, nb=1):
        if nb > 0:
            self.traffics.setdefault(edge, 0)
            self.traffics[edge] += nb
        elif nb < 0 and edge != ():
            try:
                self.traffics[edge] += nb
                if self.traffics[edge] == 0:
                    del self.traffics[edge]
                elif self.traffics[edge] < 0:
                    log.warning("We removed more drivers on edge %s than possible", str(edge))
                    del self.traffics[edge]
            except KeyError:
                log.error("We try to remove %s drivers from edge %s without traffic", nb, str(edge))
                raise KeyError("We try to remove %s drivers from edge %s without traffic" % (nb, str(edge)))

    def update_next_edges(self, idd, next_edge, n, nb=1):
        # reduce nxt_edge
        if n - nb > 0:
            self.next_edges[idd][next_edge] = n - nb
        elif n - nb < 0:
            log.error("We can't remove %s drivers among %s", nb, n)
            raise ValueError("We can't remove %s drivers among %s" % (nb, n))
        if not self.next_edges[idd]:
            del self.next_edges[idd]

    def update_moved(self, idd, edge, nb=1):
        # we remember that this driver has no next_edges
        if self.ids[idd][0][1] != edge[1]:
            self.moved.setdefault(idd, 0)
            self.moved[idd] += nb

    def update_ids(self, idd, nb=1):
        self.drivers.setdefault(idd, 0)
        self.drivers[idd] += nb
        if self.drivers[idd] == 0:
            del self.drivers[idd]
            del self.ids[idd]
        elif self.drivers[idd] < 0:
            log.error("We removed more drivers %s on path %s than possible",
                      str(self.ids[idd][0]), str(self.ids[idd][1]))
            raise ValueError("We removed more drivers %s on path %s than possible"
                             % (str(self.ids[idd][0]), str(self.ids[idd][1])))

    def moveToNextEdge(self):
        """ simulate the move of drivers to the next edges
        """
        for edge in self.next_moves:
            clocks = self.clocks[edge]
            j = 0
            while j < len(clocks) and clocks[j][1] == 0:
                idd = clocks[j][0]
                driver, path = self.ids[idd]
                if len(self.next_edges.get(idd) or {}) > 0:
                    nxt_edge, n = self.next_edges[idd].popitem()

                    # Check if nxt_edge in graph and if we follow an existing path
                    self.graph.assertIsAdjacentEdgeTo(edge, nxt_edge)

                    # handle previous idd
                    self.update_next_edges(idd, nxt_edge, n)
                    self.update_ids(idd, nb=-1)

                    # create new path and change the id
                    path = path + (nxt_edge[1],) if path else nxt_edge
                    idd = get_id((driver, path))
                    self.ids[idd] = (driver, path)
                    self.update_ids(idd)
                    self.insert_new_clock(idd)
                    self.update_traffics(nxt_edge)
                    self.update_moved(idd, nxt_edge)
                else:
                    self.update_ids(idd, nb=-1)

                self.update_traffics(edge, nb=-1)
                j += 1
            # remove the 0 (handled drivers) from clocks
            if j == len(clocks):
                del self.clocks[edge]
            else:
                self.clocks[edge] = clocks[j:]
        self.next_moves = set()

    def updateTime(self):
        """ define the minimum clock and remove this minimum to every clock
            After this step, the minimum clock is 0.0
        """
        # compute min_clock
        min_clock = min(map(lambda c: c[0][1], filter(bool, self.clocks.itervalues())))

        # update other clocks
        for edge, clocks in self.clocks.iteritems():
            for ind in range(len(clocks)):
                clocks[ind] = (clocks[ind][0], clocks[ind][1] - min_clock)
            if clocks[0][1] == 0:
                self.next_moves.add(edge)

    def has_next(self):
        """ Check if there is a next step
        """
        return len(self.drivers) > 0

    def next(self):
        """ Next step of the simulation
        """
        if self.has_next():
            self.updateTime()  # update the time to have 0.0 as minimum clock
            self.moveToNextEdge()  # move every 0.0 clocks to the next edge
        else:
            log.error("StopIteration: No drivers on graph")
            raise StopIteration("No drivers on graph")

    # --------------------------------------------------------------------------------------------------------------
    # ---------------------------------- PRINT FUNCTIONS FOR TEST --------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------

    def print_state(self):
        """ we print for each driver, path how many drivers we have, and how long they will wait (clocks)
        """
        state = {}
        for idd in self.ids:
            state.setdefault(idd, {'clocks': []})
            for e, cs in self.clocks.iteritems():
                for i, clock in cs:
                    if i == idd:
                        state[idd]['clocks'].append(str(float(clock)))
            state[idd]['next_edges'] = {e: n for e, n in self.next_edges.get(idd, {}).iteritems()}
            state[idd]['moved'] = self.moved.get(idd)

        txt = ''
        for idd in sorted(state.iterkeys(), key=lambda i: self.ids[i]):
            driver, path = self.ids[idd]
            clocks = ', '.join(clock for clock in state[idd]['clocks'])
            txt += "Drivers %s are on path %s and move in %s time's unit(s). " % (str(driver), str(path), clocks)
            if state[idd]['next_edges'] or state[idd]['moved']:
                if state[idd]['next_edges']:
                    txt += ', '.join("%s will move on edge %s" % (n, str(e))
                                     for e, n in sorted(state[idd]['next_edges'].iteritems(), key=lambda el: el[0]))
                    txt += '. '
                if state[idd]['moved']:
                    txt += "%s of them are waiting for next edges." % state[idd]['moved']
                else:
                    txt = txt[:-1]
            else:
                txt += 'They have reached the ending node.'
            txt += '\n'
        return txt

    def assert_consistency(self):
        """ check if the drivers' number in clocks is the same as in next_edges or ids, etc ...
        """
        for idd, (driver, path) in self.ids.iteritems():
            # Check if next_edges are consistent with path
            for e in self.next_edges.get(idd, {}).iterkeys():
                if path and e[0] != path[-1]:
                    log.error("Driver %s on path %s can't go on edge %s", str(driver), str(path), str(e))
                    raise Exception("Driver %s on path %s can't go on edge %s" % (str(driver), str(path), str(e)))

            # Check drivers number
            count = {'nb_clock': 0, 'next_edge': 0, 'moved': 0}
            for e, clocks in self.clocks.iteritems():
                for i, _ in clocks:
                    if i == idd:
                        count['nb_clock'] += 1
            count['next_edges'] = sum([n for n in self.next_edges.get(idd, {}).itervalues()])
            count['moved'] = self.moved.get(idd, 0)

            if path and driver[1] != path[-1] and count['nb_clock'] != count['moved'] + count['next_edges']:
                log.error('Structure error for driver %s on path %s',
                          str(self.ids[idd][0]), str(self.ids[idd][1]))
                raise Exception('Structure error for driver %s on path %s' %
                                (str(self.ids[idd][0]), str(self.ids[idd][1])))
            elif path and driver[1] == path[-1] and count['nb_clock'] < count['moved'] + count['next_edges']:
                log.error('Structure error for driver %s on path %s',
                          str(self.ids[idd][0]), str(self.ids[idd][1]))
                raise Exception('Structure error for driver %s on path %s' %
                                (str(self.ids[idd][0]), str(self.ids[idd][1])))
            elif path and driver[1] == path[-1] and count['next_edges'] > 0:
                log.error('Structure error for driver %s on path %s',
                          str(self.ids[idd][0]), str(self.ids[idd][1]))
                raise Exception('Structure error for driver %s on path %s' %
                                (str(self.ids[idd][0]), str(self.ids[idd][1])))
