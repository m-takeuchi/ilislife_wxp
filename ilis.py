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
    is_sequence = False # boolen for sequence is active or not
    is_connected = False # boolen for device is connected or not
    is_changevolt = False # boolen for program is changing volt or not
    is_holdvolt = False # boolen for program is on holding volt or not
    is_output = False # boolen for voltage is active or not
    is_iv = False # boolen for iv measurement is active or not
    count = 0 # Counter for sequence interval
    count_iv = 1 # Counter for number of iv measuremnt
    # period = 3600 # Specific time period for i-v measurment to interupt
    period = 60 # Specific time period for i-v measurment to interupt
    time_now = 0 # timer
    time_start = 0 # t0
    volt_now = 0.0 # current voltage setting
    volt_target = 0.0 # next voltage setting
    dV = 50 # minimux voltage step
    dt = 1.0 # time step for
    dtiv = 2.0 # time step for i-v measurement
    seq = [] # list container of sequence
    seq_now = 0 # current sequence number
    left_time = 0 # left time in the current sequence number
    Ve_status = 'Ve' # initial status for Ve
    Ig_status = 'Ig' # initial status for Ig
    Ic_status = 'Ic' # initial status for Ic
    P_status = 'P' # initial status for P
    Ve_value =  0 # initial value for Ve
    Ig_value =  0 # initial value for Ig
    Ic_value =  0 # initial value for Ic
    P_value =  0 # initial value for P
    portGPIB = '/dev/tty.usbserial-PXWV0AMC' ### For mac
    portRS232 = '/dev/tty.usbserial-FTAJM1O6' ### For mac
    VeAddr = 5 # GPIB address of Ve instrument
    IgAddr = 2 # GPIB address of Ig instrument
    IcAddr = 1 # GPIB address of Ic instrument

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sched = BackgroundScheduler() ###
        # self.sched = BlockingScheduler()

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
        self.AquireParam()
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
        # volt_raw_now = self.volt_now/1000
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
        # self.Ig_value = self.Ig_obj.Measure()
        self.Ig_value = self.Ig_obj.Fetch()
        # self.Ic_value = self.Ic_obj.Measure()
        self.Ic_value = self.Ic_obj.Fetch()

        self.P_value  = self.P_obj.RP()
        self.time_now = float( "{0:.2f}".format(time.time() - self.time_start) )
        self.Ve_value = self.volt_now
        self.Ve_status = str(self.Ve_value)
        self.Ic_status = str(self.Ic_value)
        self.Ig_status = str(self.Ig_value)
        self.P_status  = "{0:1.2e}".format(self.P_value)


    # def IvMeasure(self, targetvolt):
    #     """Auto I-V measurement up to the current Ve value with dV/0.5*dt rate
    #     """
    #     # self.volt_last = round(self.Ve_obj.AskVolt()*1000)
    #     # target = self.volt_last+self.dV


    #     self.is_iv = True
    #     target = int(targetvolt+self.dV)
    #     step = int(self.dV)
    #     self.is_changevolt = True
    #     self.Ve_obj.VoltZero()
    #     result = []
    #     for i in range(0, target, step):
    #         next_raw = '{0:.2f}'.format(float(i)/1000)
    #         self.Ve_obj.Instruct('volt ' + str(next_raw))
    #         time.sleep(self.dtiv)
    #         self.volt_now = self.Ve_obj.AskVolt()*1000
    #         self.AquireParam()
    #         tmp = [self.Ve_value, self.Ig_value, self.Ic_value, self.P_value]
    #         result.append(tmp)
    #         print(tmp, 'count_iv: '+str(self.count_iv))
    #     self.is_changevolt = False
    #     self.is_iv = False
    #     return result


    def IvMeasure(self):
        """Auto I-V measurement up to the current Ve value
        """
        print('IvMeasure: volt_target is ', self.volt_target)
        self.volt_now = self.Ve_obj.AskVolt()*1000

        self.AquireParam()
        if self.volt_now == self.volt_target:
            self.is_iv = False
            self.count_iv += 1
            print('End I-V')
            return False
        elif self.volt_now < self.volt_target:
            self.is_iv = True
            self._IncrementVolt()#self.volt_target)#, *largs)
            return True
        else:
            self.is_iv = False            
            self.count_iv += 1
            print('End I-V')
            return False

    def tIMeasure(self):
        ### Change voltage
        if self.volt_now != self.volt_target:
           print('Now on change voltage')
           self.ChangeVolt()

        ### Hold voltage
        else:
        ### 1st cycle to hold volt on the seq number
            if not self.is_changevolt and not self.is_holdvolt:
                self.is_holdvolt = True
                self.left_time = self.seq[self.seq_now][1] # Read left_time from sequence list
                print('Now on hold voltage')
                self.HoldVolt()
                 ### other than 1st cycle to hold volt on the seq number
            elif not self.is_changevolt and self.is_holdvolt == True:
                self.HoldVolt()
        self.count += 1
       
    def StartSequence(self):
        """Start voltage sequence
        """
        if self.is_sequence is False:
            self.is_sequence = True
            self.job_seq = self.sched.add_job(self.OnSequence, 'interval', seconds=self.dt, id='seq')#, max_instances=2)
            self.sched.start()
            self.time_start = time.time()
            print('Start Sequence')

    def StopSequence(self):
        """Stop running voltage sequence
        """
        self.sched.shutdown(wait=False)
        self.is_sequence =False


        
    def OnSequence(self):
        """Callback for voltage sequence
        """
        # print('COUNT: ', self.count)
        # print(self.sched.print_jobs())

        ### Sequence continue check
        if self.seq_now <= len(self.seq) -1:
            
            self.volt_target = self.seq[self.seq_now][0]

            ### Insert I-V measurement
            if self.count % round(self.period/self.dt) == 0:
                try:
                    self.job_tI.pause() ### Pause self.sched until IvMeasure finished
                except:
                    pass

                if self.is_iv == False:
                    self.is_iv = True
                    print('Starting I-V No. ', self.count_iv)
                    # print('Volt_target : ', self.volt_target)
                    self.Ve_obj.VoltZero()
                    self.job_iv = self.sched.add_job(self.IvMeasure, 'interval',\
                                                 seconds=self.dtiv, id='iv',\
                                                 replace_existing=True)
                else:
                    self.count += 1 

           ### Insert t-I job
            else:
                if self.is_iv == False:
                    try:
                        self.job_iv.pause()
                        self.job_iv.remove()
                    except:
                        pass
                    
                    try:
                        self.job_tI.resume()    ### Normal time-dependent measuremt
                        # print('Resuming sequence' , time.ctime())
                    except AttributeError:
                        self.job_tI = self.sched.add_job(self.tIMeasure, 'interval',\
                                            seconds=self.dt, id='ti', replace_existing=True)
                        print('Start sequence' , time.ctime())
                    # self.count += 1
                    
        ### Finish all sequences
        elif self.seq_now > len(self.seq) -1:
            print('All sequences are finished. Measurement is now stopped.')
            self.StopSequence()




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
