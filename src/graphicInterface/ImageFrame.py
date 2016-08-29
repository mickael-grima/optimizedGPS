# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import Tkinter
import Constants


class ImageFrame(Tkinter.Frame):
    """ This frame contains the image
    """
    def __init__(self, parent, **kwards):
        Tkinter.Frame.__init__(self, parent, **kwards)
        self.parent = parent

        self.onCreate()

    def onCreate(self):
        """ initialize the image
        """
        self.imageCanvas = Tkinter.Canvas(self)
        self.image = Tkinter.PhotoImage(file=Constants.START_FILE)
        self.imageCanvas.create_image(125, 125, image=self.image)
        self.imageCanvas.pack()

    def load(self, image_loc):
        self.image = Tkinter.PhotoImage(file=image_loc)
