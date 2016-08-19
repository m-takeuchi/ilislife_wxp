#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division  # 少数点以下表示のためのモジュール

import os

import e3640a_prologix as BPHV
import hioki, gid7
import datetime as dtm
import time, random
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler


class Operation():
    is_sequence = False
    is_connected = False
    is_changevolt = False
    is_holdvolt = False
    is_output = False
    time_now = 0
    time_start = 0
    volt_now = 0.0
    volt_target = 0.0
    dV = 50
    dt = 1.0
    seq = []
    seq_now = 0
    left_time = 0
    Ve_status = 'Ve'
    Ig_status = 'Ig'
    Ic_status = 'Ic'
    P_status = 'P'
    Ve_value =  0
    Ig_value =  0
    Ic_value =  0
    P_value =  0
    portGPIB = '/dev/tty.usbserial-PXWV0AMC' ### For mac
    portRS232 = '/dev/tty.usbserial-FTAJM1O6' ### For mac
    VeAddr = 5
    IgAddr = 2
    IcAddr = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sched = BackgroundScheduler()
        # self.sched_cv = BlockingScheduler()
        # self.sched_hv = BlockingScheduler()

    def ConnectDevice(self):
        """Connect to BPHV and initialize gid7
        """
        self.Ve_obj = BPHV.E3640A(self.portGPIB, self.VeAddr)
        self.Ig_obj = hioki.dmm3239gpib(self.portGPIB, self.IgAddr)
        self.Ic_obj = hioki.dmm3239gpib(self.portGPIB, self.IcAddr)
        self.P_obj  = gid7.RS232(self.portRS232)
        self.P_obj.RE() # Set GI-D7 into Remote control mode

        self.Ve_status = self.Ve_obj.Query('*IDN?')
        msg = self.Ve_obj.Clear()
        self.Ve_obj.OutOn()
        self.is_output = True
        self.Ic_status = self.Ic_obj.Query('*IDN?')
        self.Ig_status = self.Ig_obj.Query('*IDN?')
        self.P_status = self.P_obj.GS() # Ask device
        self.Ic_obj.Mode()
        self.Ic_obj.SampleRate(rate='medium')
        self.Ic_obj.ContTrig()
        self.Ic_obj.TrigInt(trig=True)
        self.Ig_obj.Mode()
        self.Ig_obj.SampleRate(rate='medium')
        self.Ig_obj.ContTrig()
        self.Ig_obj.TrigInt(trig=True)
        self.P_obj.F1() # Turn filament on

        self.is_connected = True
        return {'Ve_obj':self.Ve_obj, 'Ic_obj':self.Ic_obj, 'Ig_obj':self.Ig_obj, 'P_obj':self.P_obj} ### Is this needed?

    def DisconnectDevice(self):
        """Disconnect BPHV
        """
        self.Ve_obj.VoltZero()
        self.Ve_obj.ShutDown()
        self.Ic_obj.Rst()
        self.Ig_obj.Rst()
        self.P_obj.F0()
        self.P_obj.LO()

        self.Ve_status = 'Disconnected'
        self.Ic_status = 'Disconnected'
        self.Ig_status = 'Disconnected'
        self.P_status  = 'Disconnected'

        self.is_connected = False
        self.is_active = False
        self.is_holdvolt = False
        self.is_changevolt = False
        self.is_sequence = False



    def _IncrementVolt(self):
        """Callback for increasing voltage
        """
        volt_raw_now = self.volt_now/1000
        deltaV_raw = self.dV/1000
        next_raw = '{0:.2f}'.format(volt_raw_now + deltaV_raw)
        # print('self.volt_now, next_raw are ', self.volt_now, next_raw)
        if self.volt_now >= self.volt_target:
            self.Ve_obj.Instruct('volt ' + str(self.volt_target/1000))
            self.is_changevolt = False
            return False
        else:
            self.Ve_obj.Instruct('volt ' + str(next_raw))
            if self.is_output == False:
                self.Ve_obj.OutOn()
            return True


    def _DecreamentVolt(self):
        """Callback for decreasing voltage
        """
        volt_raw_now = self.volt_now/1000
        deltaV_raw = self.dV/1000
        next_raw = '{0:.2f}'.format(volt_raw_now - deltaV_raw)
        if self.volt_now <= self.volt_target:
            self.Ve_obj.Instruct('volt ' + str(self.volt_target/1000))
            self.is_changevolt = False
            return False
        else:
            self.Ve_obj.Instruct('volt ' + str(next_raw))
            if self.is_output == False:
                self.Ve_obj.OutOn()
            return True

    def ChangeVolt(self):#, volt_target, *largs):
        """Callback for change voltage
        """
        self.volt_now = self.Ve_obj.AskVolt()*1000
        if self.volt_now == self.volt_target:
            self.is_changevolt = False
            return False
        elif self.volt_now < self.volt_target:
            self.is_changevolt = True
            self._IncrementVolt()#self.volt_target)#, *largs)
            self.is_changevolt = False
            return True
        elif self.volt_now > self.volt_target:
            self.is_changevolt = True
            self._DecreamentVolt()#self.volt_target, *largs)
            self.is_changevolt = False
            return True
        else:
            print('End ChangeVolt')
            return False


    def HoldVolt(self):#, left_time, *largs):
        """Hold voltage output by left_time == 0
        """
        self.volt_now = self.Ve_obj.AskVolt()*1000
        volt_raw_now = self.volt_now/1000
        self.AquireParam()
        self.Ve_status = str(self.volt_now)
        if self.left_time <= 0:
            self.seq_now += 1 # Step 1 sequence forward
            self.is_holdvolt = False
            return False
        self.left_time -= self.dt


    def AquireParam(self):
        """Callback function for fetching measured values
        """
        ### Update instance variables
        # try:
        # self.Ig_value = self.Ig_obj.Measure()
        self.Ig_value = self.Ig_obj.Fetch()
        # self.Ic_value = self.Ic_obj.Measure()
        self.Ic_value = self.Ic_obj.Fetch()
        start = time.time()
        self.P_value  = self.P_obj.RP()
        self.time_now = time.time() - self.time_start
        self.Ve_value = self.volt_now
        self.Ve_status = str(self.Ve_value)
        self.Ic_status = str(self.Ic_value)
        self.Ig_status = str(self.Ig_value)
        self.P_status  = "{0:1.2e}".format(self.P_value)

    def IvMeasure(self):
        """Auto I-V measurement up to the current Ve value with dV/dt rate
        """
        self.volt_last = round(self.Ve_obj.AskVolt()*1000)
        self.is_changevolt = True
        self.Ve_obj.VoltZero()
        result = []
        for i in range(0, self.volt_last+self.dV, self.dV):
            # volt_raw_now = self.volt_now/1000
            # deltaV_raw = self.dV/1000
            next_raw = '{0:.2f}'.format(float(i)/1000)
            self.Ve_obj.Instruct('volt ' + str(next_raw))
            time.sleep(self.dt)
            self.volt_now = self.Ve_obj.AskVolt()*1000
            self.AquireParam()
            tmp = [self.Ve_value, self.Ig_value, self.Ic_value, self.P_value]
            result.append(tmp)
            print(tmp)
        self.is_changevolt = False
        return result


    def StartSequence(self):
        """Start voltage sequence
        """
        if self.is_sequence is False:
            self.is_sequence = True
            self.sched.add_job(self.OnSequence, 'interval', seconds=self.dt)
            self.sched.start()
            self.time_start = time.time()
            print('Start Sequence')

    def StopSequence(self):
        """Stop running voltage sequence
        """
        self.sched.remove_all_jobs()
        self.sched.state = 0
        self.is_sequence =False

    def OnSequence(self):
        """Callback for voltage sequence
        """
        if self.seq_now <= len(self.seq) -1:
            # print('I am in on_countdonw'+str(self.seq_now))
            self.volt_target = self.seq[self.seq_now][0]
            if self.volt_now != self.volt_target:
                ### 電圧変更中でない場合
                if not self.is_changevolt:
                    # イベントループに投入
                    self.is_changevolt = True
                    print('Now on change voltage')
                    self.ChangeVolt()


            ### 現在電圧が現在シーケンス設定電圧と等しく, 電圧変更中でなく, HoldVolt中でない場合
            else:
                if not self.is_changevolt and not self.is_holdvolt: ### 1st cycle to hold volt on the seq number
                    self.is_holdvolt = True
                    self.left_time = self.seq[self.seq_now][1] #left_timeにシーケンスリスト
                    # イベントループに投入
                    print('Now on hold voltage')
                    self.HoldVolt()
                elif not self.is_changevolt and self.is_holdvolt == True:  ### other than 1st cycle to hold volt on the seq number
                    self.HoldVolt()

        elif self.seq_now > len(self.seq) -1:
            print('All sequences are finished. Measurement is now stopped.')
            self.StopSequence()
        else:
            print('Where I am')


    def LapseTime(self, t):
        """Retrun lapse time (hh:mm:ss format)
        """
        rh = (t-t%3600)/3600
        rm = (t-rh*3600-((t-rh*3600)%60))/60
        rs = t%60
        return "{0:2.0f} H {1:2.0f} M {2:2.0f} ".format(rh,rm,rs)

    def CalcTotTime(self):
        l = len(self.seq)
        total=0
        for i in range(l):
            if i == 0:
                total += (self.seq[i][0]/self.dV)*self.dt
            else:
                total += ((self.seq[i][0]-self.seq[i-1][0])/self.dV)*self.dt
            total += self.seq[i][1]
        return total

    def CalcRestTime(self,t):
        total = self.CalcTottime()
        rt = total - t
        return self.LapseTime(rt)

### Need to make abort_sequence
