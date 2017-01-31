# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import Tkinter
import time

import Constants
from ImageFrame import ImageFrame
from OptionsFrame import OptionsFrame


class PetrinetInterface(Tkinter.Tk):
    """ this class implement the main window of the interface
    """
    def __init__(self, parent, simulator, **kwards):
        """ simulator is an object of class Simulator
        """
        Tkinter.Tk.__init__(self, parent)
        self.parent = parent
        self.simulator = simulator
        self.speed = Constants.SPEED
        self.status = Constants.STOPPED

        self.width = kwards.get('width', Constants.WINDOW['MAIN']['WIDTH'])
        self.length = kwards.get('length', Constants.WINDOW['MAIN']['LENGTH'])

        self.onCreate()

    def onCreate(self):
        """ After the first call of the interface, we create the window
            To this window we associate some variables
        """
        # Create the frame in which we put the buttons
        self.optionsFrame = OptionsFrame(self, borderwidth=2, relief=Tkinter.GROOVE)
        self.optionsFrame.pack(side=Tkinter.LEFT)

        # Create the frame in which we put the image
        self.imageFrame = ImageFrame(self, borderwidth=2)
        self.imageFrame.pack(side=Tkinter.LEFT)

    def onQuit(self):
        """ reinitialize the simulator
        """
        self.simulator.reinitialize()

    def startSimulation(self):
        """ start the simulation
        """
        self.status = Constants.RUNNING
        while self.status and self.simulator.has_next():
            # One step simulation
            self.simulator.next()

            # Generate the image of the simulation and update imageFrame
            image_loc = self.simulator.to_image()
            self.imageFrame.load(image_loc)

            # Sleep function of speed
            self.speed = self.optionsFrame.speedScale.get()
            time.sleep(self.speed)

    def stopSimulation(self):
        """ stop simulation
        """
        self.status = Constants.STOPPED
