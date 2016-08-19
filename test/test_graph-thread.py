#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import wx

from threading import Thread
from wx.lib.pubsub import pub

########################################################################
class TestThread(Thread):
    """Test Worker Thread Class."""

    #----------------------------------------------------------------------
    def __init__(self):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.start()    # start the thread

    #----------------------------------------------------------------------
    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread.
        for i in range(6):
            time.sleep(1)
            wx.CallAfter(self.postTime, amt=i)
        time.sleep(1)
        wx.CallAfter(pub.sendMessage, "update", msg="Thread finished!")

    #----------------------------------------------------------------------
    def postTime(self, amt):
        """
        Send time to GUI
        """
        amtOfTime = (amt + 1) * 10
        pub.sendMessage("update", msg=amtOfTime)

########################################################################
class MyPanel(wx.Panel):
    # Add a panel so it looks the correct on all platforms
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.displayLbl = wx.StaticText(self.panel, label="Amount of time since thread started goes here")
        self.btn = btn = wx.Button(self.panel, label="Start Thread")

        self.btn.Bind(wx.EVT_BUTTON, self.onButton)

        self.box = wx.BoxSizer(wx.VERTICAL)
        # self.box = wx.BoxSizer(wx.HORIZONTAL)
        # self.box.Add(self.displayLbl, 0, wx.ALL|wx.CENTER, 5)
        self.box.Add(self.displayLbl, 0, wx.TOP|wx.CENTER, 5)
        # self.box.Add(self.btn, 0, wx.ALL|wx.CENTER, 5)
        self.box.Add(self.btn, 0, wx.BOTTOM|wx.CENTER, 5)
        self.panel.SetSizer(self.box)

    def onButton(self, event):
        """
        Runs the thread
        """
        TestThread()
        self.displayLbl.SetLabel("Thread started!")
        self.btn = event.GetEventObject()
        self.btn.Disable()

    def updateDisplay(self, msg):
        """
        Receives data from thread and updates the display
        """
        # t = msg.data
        t = msg
        if isinstance(t, int):
            self.displayLbl.SetLabel("Time since thread started: %s seconds" % t)
        else:
            self.displayLbl.SetLabel("%s" % t)
            self.btn.Enable()

class MyForm(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Tutorial")
        panel = MyPanel(self)
        # box = wx.BoxSizer(wx.VERTICAL)
        # box.Add(panel, 0, wx.ALL|wx.CENTER, 5)
        # panel.SetSizer(box)

        # create a pubsub receiver
        # pub.subscribe(self.updateDisplay, "update")
        pub.subscribe(panel.updateDisplay, "update")


#----------------------------------------------------------------------
# Run the program
if __name__ == "__main__":
    app = wx.App()
    frame = MyForm().Show()
    app.MainLoop()
