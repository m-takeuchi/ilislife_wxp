#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
# import pprint
import random
import sys
# import threading
import wx
from wx.lib import plot as wxplot

import numpy as np
import time

class DataGen(object):
    """ A silly class that generates pseudo-random data for
        display in the plot.
    """
    def __init__(self, init=50):
        self.data = self.init = init
        # print(self.data)

    def next(self):
        self._recalc_data()
        return self.data

    def _recalc_data(self):
        delta = random.uniform(-0.5, 0.5)
        r = random.random()

        if r > 0.9:
            self.data += delta * 15
        elif r > 0.8:
            # attraction to the initial value
            delta += (0.5 if self.init > self.data else -0.5)
            self.data += delta
        else:
            self.data += delta

class PlotExample(wx.Frame):
    BUFFSIZE = 100 # 12 hours = 12*3600 sec = 43200
    COLS = 2 # Number of param you deal with (include time col)
    val_arr = np.zeros((BUFFSIZE, COLS)) ### Prepare zero array
    dt = 1
    t = 0

    def __init__(self):
        wx.Frame.__init__(self, None, title="Example of wx.lib.plot")

        # self.datagen = DataGen()

        # Generate some Data
        # x_data = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        # y_data = [2, 4, 6, 4, 2, 5, 6, 7, 1]

        # most items require data as a list of (x, y) pairs:
        #    [[1x, y1], [x2, y2], [x3, y3], ..., [xn, yn]]
        # xy_data = list(zip(x_data, y_data))

        self.val_arr[:,0] = np.arange(0, -self.BUFFSIZE*self.dt, -self.dt)
        self.val_arr[:,1] = [random.random() for i in range(self.BUFFSIZE)]
        # self.setGraphics(self.val_arr)

        ### Prepare wx.Timer
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_timer, self.update_timer)
        self.update_timer.Start(1000) #ms, Should is this self.dev.dt?


    def setGraphics(self, xyarray):
        # Create your Poly object(s).
        # Use keyword args to set display properties.
        self.line = wxplot.PolySpline(
            # xy_data,
            xyarray,
            colour=wx.Colour(128, 128, 0),   # Color: olive
            width=3,
        )

        # create your graphics object
        self.graphics = wxplot.PlotGraphics([self.line])

        # create your canvas
        self.panel = wxplot.PlotCanvas(self)

        # Edit panel-wide settings
        # axes_pen = wx.Pen(wx.BLUE, 1, wx.PENSTYLE_LONG_DASH)
        self.panel.axesPen = wx.Pen(wx.BLUE, 1, wx.PENSTYLE_LONG_DASH)

        # draw the graphics object on the canvas
        print('Update')
        self.panel.Draw(self.graphics)


    def on_update_timer(self, event):
        # wx.CallAfter(pub.sendMessage, "varListner", message=self.var_param)

        self.val_arr = np.roll(self.val_arr, 1, axis=0) # Roll 1 element forward
        self.t += self.dt
        # self.val_arr[0,0] = self.t
        self.val_arr[:,0] = np.arange(0, -self.BUFFSIZE*self.dt, -self.dt)

        ### Put values by self.datagen.next
        # self.val_arr[0,1:] = [self.datagen.read() for i in range(self.COLS-1)]
        self.val_arr[0,1:] = [random.random() for i in range(self.COLS-1)]

        print(self.val_arr[0])
        # self.panel.Clear()
        self.setGraphics(self.val_arr)
        self.panel.Redraw()


if __name__ == '__main__':
    app = wx.App()
    frame = PlotExample()
    frame.Show()
    app.MainLoop()
