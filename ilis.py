#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division  # 少数点以下表示のためのモジュール

import os

import e3640a_prologix as BPHV
import datetime as dtm
import time, random
import threading


class VeOperation():
    is_active = False # Flag for multiple GPIB use
    is_countup = False
    is_sequence = False
    is_connected = False
    is_changevolt = False
    is_holdvolt = False
    time_now = 0
    volt_now = 0.0
    volt_target = 0.0
    dV = 50
    dt = 1.0
    seq = []
    seq_now = 0
    # left_time = NumericProperty()
    Ve_status = 'Ve'
    Ig_status = 'Ig'
    Ic_status = 'Ic'
    P_status = 'P'
    Ve_value =  0
    Ig_value =  0
    Ic_value =  0
    P_value =  0
    portGPIB = ''
    portRS232 = ''
    VeAddr = 5
    IgAddr = 2
    IcAddr = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = threading.Event()
        self.lock = threading.Lock()

    def connect_device(self):
        """Connect to BPHV and initialize gid7
        """
        self.Ve_obj = BPHV.E3640A(self.portGPIB, self.VeAddr)
        self.Ic_obj = hioki.dmm3239gpib(self.portGPIB, self.IcAddr)
        self.Ig_obj = hioki.dmm3239gpib(self.portGPIB, self.IgAddr)
        self.P_obj  = gid7.RS232(self.ttyRS232)
        self.P_obj.RE() # Set GI-D7 into Remote control mode

        self.Ve_status = self.Ve_obj.Query('*IDN?')
        msg = self.Ve_obj.Clear()
        self.Ic_status = self.Ic_obj.Query('*IDN?')
        self.Ig_status = self.Ig_obj.Query('*IDN?')
        self.P_status = self.P_obj.GS() # Ask device
        self.Ic_obj.Mode()
        self.Ic_obj.SampleRate(rate='medium')
        self.Ig_obj.Mode()
        self.Ig_obj.SampleRate(rate='medium')
        self.P_obj.F1() # Turn filament on

        self.is_connected = True
        return {'Ve_obj':self.Ve_obj, 'Ic_obj':self.Ic_obj, 'Ig_obj':self.Ig_obj, 'P_obj':self.P_obj} ### Is this needed?

    def disconnect_device(self):
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
    #
    # def run(self):
    #     self.thread = threading.Thread(target=self.countup)
    #     self.thread.start()

    def stop(self):
        """Stop running thread"""
        self.event.set()
        self.thread.join()    # Wait main thread for end subthread

# ### Need modify
#     def start_timer(self):
#         self.is_countup = True
#         Clock.schedule_interval(self.on_countup, dt_meas)
#         pass
# ### Need modify
#     def stop_timer(self):
#         self.is_countup = False
#         Clock.unschedule(self.on_countup)
#         pass


    def increment_Volt(self, volt_target, *largs):
        """Callback for increasing voltage
        """
        self.volt_now = self.Ve_obj.AskVolt()*1000
        volt_raw_now = self.volt_now/1000
        deltaV_raw = self.dV/1000
        next_raw = '{0:.2f}'.format(volt_raw_now + deltaV_raw)
        if self.volt_now >= volt_target:
            self.Ve_obj.Instruct('volt ' + str(volt_target/1000))
            self.volt_now = self.Ve_obj.AskVolt()*1000
            self.Ve_status = str(self.volt_now)
            self.is_changevolt = False
            return False
        else:
            self.Ve_obj.Instruct('volt ' + str(next_raw))
            self.Ve_obj.OutOn()
            # self.volt_now = '{0:.2f}'.format(Ve_obj.AskVolt())*1000
            self.volt_now = self.Ve_obj.AskVolt()*1000
            self.Ve_status = str(self.volt_now)
            return True


    def decrement_Volt(self, volt_target, *largs):
        """Callback for decreasing voltage
        """
        self.volt_now = self.Ve_obj.AskVolt()*1000
        volt_raw_now = self.volt_now/1000
        deltaV_raw = self.dV/1000
        next_raw = '{0:.2f}'.format(volt_raw_now - deltaV_raw)
        if self.volt_now <= volt_target:
            self.Ve_obj.Instruct('volt ' + str(volt_target/1000))
            self.volt_now = self.Ve_obj.AskVolt()*1000
            self.Ve_status = str(self.volt_now)
            self.is_changevolt = False
            return False
        else:
            self.Ve_obj.Instruct('volt ' + str(next_raw))
            self.Ve_obj.OutOn()
            self.volt_now = self.Ve_obj.AskVolt()*1000
            self.Ve_status = str(self.volt_now)
            return True

    def change_Volt(self, volt_target, *largs):
        """Callback for change voltage
        """
        self.volt_now = self.Ve_obj.AskVolt()*1000
        if self.volt_now == volt_target:
            self.is_changevolt = False
            return False
        elif self.volt_now < volt_target:
            self.increment_Volt(volt_target, *largs)
            self.is_changevolt = True
            return True
        elif self.volt_now > volt_target:
            self.decrement_Volt(volt_target, *largs)
            self.is_changevolt = True
            return True
        else:
            print('End change_Volt')
            return False


    def hold_Volt(self, left_time, *largs):
        """Hold voltage output by left_time == 0
        """
        self.volt_now = self.Ve_obj.AskVolt()*1000
        volt_raw_now = self.volt_now/1000
        self.Ve_status = str(self.volt_now)
        if self.left_time <= 0:
            self.seq_now += 1 #シーケンスを1進める
            self.is_holdvolt = False
            return False
        self.left_time -= 1


    def aquire_param(self):
        """Callback function for fetching measured values
        """
        ### Update instance variables
        try:
            self.Ig_value = self.Ig_obj.Measure()
            self.Ic_value = self.Ic_obj.Measure()
            start = time.time()
            self.P_value  = self.P_obj.RP()
            #elapsed_time = time.time() - start
            self.Ve_value = self.volt_now
            self.Ve_status = str(self.Ve_value)
            self.Ic_status = str(self.Ic_value)
            self.Ig_status = str(self.Ig_value)
            self.P_status  = "{0:1.2e}".format(self.P_value)

        except ValueError:
            self.Ig_value = 0
            self.Ic_value = 0
            self.P_value  = self.P_obj.RP()
            self.Ic_status = Ic_obj.ClearBuffer()
            self.Ig_status = Ig_obj.ClearBuffer()
            self.P_status  = "{0:1.2e}".format(self.P_value)


    def start_sequence(self):
        """Start voltage sequence
        """
        if self.is_sequence is False:
            self.is_sequence = True
            # self.thread = threading.Thread(target=self.on_sequence)
            self.thread = threading.Thread(target=self.test_sequence)
            self.thread.start()
            print('Start test_sequence')
    def stop_sequence(self):
        """Stop running voltage sequence
        """
        self.event.set()
        self.thread.join()

    def test_sequence(self):
        with self.lock: ### Prohibit multiple change_volt
            self.is_changevolt = True
            while self.is_changevolt is True:
                self.is_active = True
                self.change_Volt(volt_target=self.volt_target)
                self.is_active = False
                time.sleep(self.dt)
            self.is_sequence = False

    def on_sequence(self, dt):
        """Callback for voltage sequence
        """
        with self.lock: ### Prohibit multiple change_volt
            if self.seq_now <= len(self.seq) -1:
                # print('I am in on_countdonw'+str(self.seq_now))
                self.volt_target = self.seq[self.seq_now][0]
                if self.volt_now != self.volt_target:
                    ### 電圧変更中でない場合
                    if not self.is_changevolt:
                        # イベントループに投入
                        self.is_changevolt = True
                        print('Now on change voltage')
                        while self.is_changevolt is True:
                            self.is_active = True
                            self.change_Volt(volt_target=self.volt_target)
                            self.aquire_param()
                            self.is_active = False
                            time.sleep(self.dt)

                ### 現在電圧が現在シーケンス設定電圧と等しく, 電圧変更中でなく, hold_Volt中でない場合
                else:
                    if not self.is_changevolt and not self.is_holdvolt:
                        self.is_holdvolt = True
                        self.left_time = self.seq[self.seq_now][1] #left_timeにシーケンスリスト
                        # イベントループに投入
                        print('Now on hold voltage')
                        while self.is_holdvolt is True:
                            self.is_active = True
                            self.hold_Volt(left_time=self.left_time)
                            self.aquire_param()
                            self.is_active = False
                            time.sleep(self.dt)

            # except IndexError:
            elif self.seq_now > len(self.seq) -1:
                print('All sequences are finished. Measurement is now stopped.')
                self.stop_sequence()


    def lapse_time(self, t):
        """Retrun lapse time (hh:mm:ss format)
        """
        rh = (t-t%3600)/3600
        rm = (t-rh*3600-((t-rh*3600)%60))/60
        rs = t%60
        return "{0:2.0f} H {1:2.0f} M {2:2.0f} ".format(rh,rm,rs)

    def calc_Ttime(self):
        l = len(self.seq)
        total=0
        for i in range(l):
            if i == 0:
                total += (self.seq[i][0]/self.dV)*dt_op
            else:
                total += ((self.seq[i][0]-self.seq[i-1][0])/self.dV)*dt_op
            total += self.seq[i][1]
        return total

    def calc_Rtime(self,t):
        total = self.total_time()
        rt = total - t
        return self.lapse_time(rt)

### Need to make abort_sequence
