# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import Tkinter
import Constants


class OptionsFrame(Tkinter.Frame):
    """ This object represents the options frame
        We find here the start button and end button
    """
    def __init__(self, parent, **kwards):
        Tkinter.Frame.__init__(self, parent, **kwards)
        self.parent = parent
        self.onCreate()

    def onCreate(self):
        """ introduce the wanted buttons into the frame
        """
        # Button start
        self.startButton = Tkinter.Button(self, text=Constants.START, command=self.onStart)
        self.startButton.pack(side=Tkinter.TOP, padx=Constants.BUTTON_PADX)

        # Button Stop
        self.stopButton = Tkinter.Button(self, text=Constants.STOP, command=self.onStop)
        self.stopButton.pack(side=Tkinter.TOP, padx=Constants.BUTTON_PADX)

        # Scale bar to speed up or slow down the animation
        self.speedScale = Tkinter.Scale(self, from_=0, to=1000, orient=Tkinter.HORIZONTAL)
        self.speedScale.pack(side=Tkinter.TOP, padx=Constants.BUTTON_PADX)

        # Button quit
        self.quitButton = Tkinter.Button(self, text=Constants.QUIT, command=self.onQuit)
        self.quitButton.pack(side=Tkinter.BOTTOM, padx=Constants.BUTTON_PADX)

    def onStart(self):
        """ start the animation
        """
        self.parent.startSimulation()

    def onStop(self):
        """ stop the animation
        """
        self.parent.stopSimulation()

    def onQuit(self):
        """ quit the animation
        """
        self.parent.onQuit()
        self.quit()
