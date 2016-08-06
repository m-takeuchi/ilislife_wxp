# -*- coding: utf-8 -*-
import wx
import numpy as np
import matplotlib.figure as mfigure
import matplotlib.animation as manim

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

class MyFrame(wx.Frame):
    def __init__(self):
        super(MyFrame,self).__init__(None, wx.ID_ANY, size=(800, 600))
        self.fig = mfigure.Figure()
        self.ax = self.fig.add_subplot(111)
        self.canv = FigureCanvasWxAgg(self, wx.ID_ANY, self.fig)
        self.values = []
        # self.animator = manim.FuncAnimation(self.fig,self.anim, interval=1000)
        self.animator = manim.FuncAnimation(self.fig,self.anim, interval=250)

    def anim(self,i):
        # if i%10 == 0:
        if i%100 == 0:
            self.values = []
        else:
            self.values.append(np.random.rand())
        self.ax.clear()
        # self.ax.set_xlim([0,10])
        self.ax.set_xlim([0,100])
        self.ax.set_ylim([0,1])
        # return self.ax.plot(np.arange(1,i%10+1),self.values,'d-')
        return self.ax.plot(np.arange(1,i%100+1),self.values,'d-')


app = wx.App()
w = MyFrame()
w.Show(True)
app.MainLoop()
