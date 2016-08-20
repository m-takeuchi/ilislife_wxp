#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MyGraph.py, modified from demo python script by Eli Bendersky (eliben@gmail.com), is real time plotting with wxPython Phoenix

"""
import os
# import pprint
import random
import sys
# import threading
import wx

# The recommended way to use wx with mpl is with the WXAgg
# backend.
#
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np


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



class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval):
        wx.Panel.__init__(self, parent, ID)

        self.value = initval

        box = wx.StaticBox(self, wx.ID_ANY, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.radio_auto = wx.RadioButton(self, wx.ID_ANY,
            label="Auto", style=wx.RB_GROUP)
        self.radio_manual = wx.RadioButton(self, wx.ID_ANY,
            label="Manual")
        self.manual_text = wx.TextCtrl(self, wx.ID_ANY,
            size=(35,-1),
            value=str(initval),
            style=wx.TE_PROCESS_ENTER)

        ### Initial state for radio box of Auto range
        self.radio_auto.SetValue(True)

        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)

        manual_box = wx.BoxSizer(wx.HORIZONTAL)
        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(self.radio_auto, 0, wx.ALL, 10)
        sizer.Add(manual_box, 0, wx.ALL, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_update_manual_text(self, event):
        self.manual_text.Enable(self.radio_manual.GetValue())

    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()

    def is_auto(self):
        return self.radio_auto.GetValue()

    def manual_value(self):
        return self.value

class GraphPanel(wx.Panel):
    """ The main frame of the application
    """
    title = 'MyGraph Demo: dynamic matplotlib graph'
    t = t0 = 0
    dt = 1.0 #s
    dtms = dt*1000 #ms
    BUFFSIZE = 43200 # 12 hours = 12*3600 sec = 43200
    COLS = 5 # Number of param you deal with (include time col)
    val_arr = np.zeros((BUFFSIZE, COLS)) ### Prepare zero array


    def __init__(self, parent, id):
        # super().__init__(None, wx.ID_ANY, self.title)
        super().__init__(parent, id=wx.ID_ANY)

        # self.datagen = DataGen()
        # self.datagen = DataFetch()

        # self.val_arr[0,0] = self.t0 # Initialization time col's 1st element
        # self.val_arr[0,1:] = [self.datagen.next() for i in range(self.COLS-1)] # Initilaze param cols' 1st elements


        self.paused = False
        # self.paused = True

        ### Prepare matplotlib and widgets
        self.init_plot()
        self.canvas = FigCanvas(self, wx.ID_ANY, self.fig)

        self.xmin_control = BoundControlBox(self, wx.ID_ANY, "X min", -60)
        self.xmax_control = BoundControlBox(self, wx.ID_ANY, "X max", 0)
        self.ymin_control = BoundControlBox(self, wx.ID_ANY, "Y min", 0)
        self.ymax_control = BoundControlBox(self, wx.ID_ANY, "Y max", 100)

        self.pause_button = wx.Button(self, wx.ID_ANY, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.cb_grid = wx.CheckBox(self, wx.ID_ANY,
            "Show Grid",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)

        self.cb_xlab = wx.CheckBox(self, wx.ID_ANY,
            "Show X labels",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)
        self.cb_xlab.SetValue(True)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
        self.hbox2.AddSpacer(24)
        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

        ### Prepare wx.Timer
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(self.dtms)


    def init_plot(self):
        self.dpi = 100
        self.fig = plt.Figure((3.0, 3.0), dpi=self.dpi)
        self.gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 3])

        # self.axes = self.fig.add_subplot(111)
        # self.axes.set_axis_bgcolor((0.1,0.1,0.1,1))
        # self.axes.set_title('Description', size=12)
        self.ax1 = self.fig.add_subplot(self.gs[0]) # Voltage
        self.ax2 = self.fig.add_subplot(self.gs[1]) # Pressure
        self.ax3 = self.fig.add_subplot(self.gs[2]) # Current
        # self.ax1.set_title('Ve', size=12)
        # self.ax2.set_title('Pressure', size=12)
        # self.ax3.set_title('Current', size=12)

        plt.setp(self.ax1.get_xticklabels(), visible=False)
        plt.setp(self.ax2.get_xticklabels(), visible=False)
        plt.setp(self.ax3.get_xticklabels(), fontsize=8)
        plt.setp(self.ax1.get_yticklabels(), fontsize=8)
        plt.setp(self.ax2.get_yticklabels(), fontsize=8)
        # self.ax2.set_yscale('symlog')
        plt.setp(self.ax3.get_yticklabels(), fontsize=8)


        self.plot_data = []
        colors = ['red','cyan','green','blue']
        # for col in range(self.COLS-1):
            # self.plot_data.append(self.axes.plot(self.val_arr[:,0], self.val_arr[:,col+1], linewidth=1, color=colors[col])[0])
        # Ve
        self.plot_data.append(self.ax1.plot(self.val_arr[:,0], self.val_arr[:,1], linewidth=1, color=colors[0])[0])
        # Ig
        self.plot_data.append(self.ax3.plot(self.val_arr[:,0], self.val_arr[:,2], linewidth=1, color=colors[2])[0])
        # Ic
        self.plot_data.append(self.ax3.plot(self.val_arr[:,0], self.val_arr[:,3], linewidth=1, color=colors[3])[0])
        # P
        self.plot_data.append(self.ax2.plot(self.val_arr[:,0], self.val_arr[:,4], linewidth=1, color=colors[1])[0])


    def draw_plot(self):
        """ Redraws the plot
        """
        if self.xmax_control.is_auto():
            xmax = self.val_arr[0,0]
        else:
            xmax = int(self.xmax_control.manual_value())

        if self.xmin_control.is_auto():
            xmin = self.val_arr[-1,0]
        else:
            xmin = int(self.xmin_control.manual_value())


        ymin1 = round(self.val_arr[:,1].min()) - 1
        ymax1 = round(self.val_arr[:,1].max()) + 1
        ymin2 = self.val_arr[:,4].min()
        ymax2 = self.val_arr[:,4].max()

        if self.ymin_control.is_auto():
            # ymin = round(self.val_arr[:,1:].min()) - 1
            ymin3 = self.val_arr[:,2:4].min()
        else:
            ymin3 = self.ymin_control.manual_value()

        if self.ymax_control.is_auto():
            # ymax = round(self.val_arr[:,1:].max()) + 1
            ymax3 = self.val_arr[:,2:4].max()
        else:
            ymax3 = self.ymax_control.manual_value()

        # self.axes.set_xbound(lower=xmin, upper=xmax)
        # self.axes.set_ybound(lower=ymin, upper=ymax)
        self.ax1.set_xbound(lower=xmin, upper=xmax)
        self.ax1.set_ybound(lower=ymin1, upper=ymax1)
        self.ax2.set_xbound(lower=xmin, upper=xmax)
        self.ax2.set_ybound(lower=ymin2, upper=ymax2)
        self.ax3.set_xbound(lower=xmin, upper=xmax)
        self.ax3.set_ybound(lower=ymin3, upper=ymax3)

        if self.cb_grid.IsChecked():
            # self.axes.grid(True, color='gray')
            self.ax1.grid(True, color='gray')
            self.ax2.grid(True, color='gray')
            self.ax3.grid(True, color='gray')
        else:
            # self.axes.grid(False)
            self.ax1.grid(False)
            self.ax2.grid(False)
            self.ax3.grid(False)

        # plt.setp(self.axes.get_xticklabels(),          visible=self.cb_xlab.IsChecked())
        plt.setp(self.ax1.get_xticklabels(), visible=False)
        plt.setp(self.ax2.get_xticklabels(), visible=False)
        plt.setp(self.ax3.get_xticklabels(), visible=self.cb_xlab.IsChecked())


        ### Ve, Ig, Ic, P
        for col in range(self.COLS-1):
            self.plot_data[col].set_xdata(self.val_arr[:, 0])
            self.plot_data[col].set_ydata(self.val_arr[:, col+1])

        self.canvas.draw()

    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def on_cb_grid(self, event):
        self.draw_plot()

    def on_cb_xlab(self, event):
        self.draw_plot()

    def on_redraw_timer(self, event):
        if not self.paused:
            self.val_arr = np.roll(self.val_arr, 1, axis=0) # Roll 1 element forward
            self.t += self.dt
            # self.val_arr[0,0] = self.t
            self.val_arr[:,0] = np.arange(0, -self.BUFFSIZE*self.dt, -self.dt)

            ### Put values by self.datagen.next
            # self.val_arr[0,1:] = [self.datagen.read() for i in range(self.COLS-1)]

            self.draw_plot()


    # def flash_status_message(self, msg, flash_len_ms=1500):
    #     self.statusbar.SetStatusText(msg)
    #     self.timeroff = wx.Timer(self)
    #     self.Bind(
    #         wx.EVT_TIMER,
    #         self.on_flash_status_off,
    #         self.timeroff)
    #     self.timeroff.Start(flash_len_ms, oneShot=True)
    #
    # def on_flash_status_off(self, event):
    #     self.statusbar.SetStatusText('')


class TopFrame(wx.Frame):
    title = 'hoge'
    def __init__(self):
        super().__init__(None, wx.ID_ANY, self.title, size=(600,400))
        self.mygraph = GraphPanel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.mygraph, proportion=1, flag=wx.EXPAND|wx.ALL)
        self.SetSizer(layout)

if __name__ == '__main__':
    # app = wx.PySimpleApp()
    app = wx.App()
    app.frame = TopFrame()
    # print(app.frame.mygraph.val_arr)
    app.frame.Show()
    app.MainLoop()
