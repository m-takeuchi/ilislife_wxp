#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division

import os

import e3640a_prologix as BPHV
import hioki, gid7 ### for dmm and ion guage
import numpy as np

import datetime as dtm
import time, random
import threading

class VeOperation():
    is_active = False
    is_sequence = False
    is_connected = False
    time_now = 0
    dt = 1.0
    # left_time = NumericProperty()
    Ig_status = 'Ig'
    Ic_status = 'Ic'
    P_status = 'P'
    Ig_value = 0
    Ic_value = 0
    P_value = 0


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = threading.Event()
        self.lock = threading.Lock()

    def connect_device(self, ttyport, IcAddr, IgAddr):
        """Connect to hioki dmm and gid7 RS232
        """
        self.Ic_obj = hioki.dmm3239gpib(tty, IcAddr)
        self.Ig_obj = hioki.dmm3239gpib(tty, IgAddr)
        self.P_obj  = gid7.RS232(ttyRS232)
        self.P_obj.RE() # Set GI-D7 into Remote control mode
        self.is_connected = True
        self.Ic_status = Ic_obj.Query('*IDN?')
        self.Ig_status = Ig_obj.Query('*IDN?')
        self.P_status = P_obj.GS() # Ask device
        self.Ic_obj.Mode()
        self.Ic_obj.SampleRate(rate='medium')
        self.Ig_obj.Mode()
        self.Ig_obj.SampleRate(rate='medium')
        self.P_obj.F1() # Turn filament on
        return Ic_obj, Ig_obj, P_obj

    def disconnect_device(self):
        """Disconnect BPHV
        """
        self.Ic_obj.Rst()
        self.Ig_obj.Rst()
        self.P_obj.F0()
        self.P_obj.LO()
        self.Ic_status = 'Disconnected'
        self.Ig_status = 'Disconnected'
        self.P_status  = 'Disconnected'
        self.is_connected = False
