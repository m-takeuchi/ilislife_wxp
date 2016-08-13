#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import division  # 少数点以下表示のためのモジュール

### For logging to current dir/log_dir
import os
from sys import platform as _platform
from kivy.config import Config
Config.set('kivy', 'log_name', _platform+'_kivy_%y-%m-%d_%_.txt')
Config.set('kivy', 'log_level', 'debug')
Config.set('kivy', 'log_dir', os.path.dirname(os.path.abspath(__file__))+'/logs/')

from functools import partial
# from kivy.lang import Builder
from kivy.uix.widget import Widget
# from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
from kivy.app import App

# Importing my modules
import e3640a_prologix as BPHV
import hioki
import gid7 ### for ion guage
from kivy.properties import StringProperty
import datetime as dtm
import time
import random
import numpy as np
import plot_tdepend as tdep
import email_pdf as epdf

# Device settings
VeAddr = 5
IcAddr = 1
IgAddr = 2

if _platform == "linux" or _platform == "linux2":
    # linux
    tty = '/dev/ttyUSB0'
    ttyRS232 = '/dev/ttyUSB1'
elif _platform == "darwin":
    # OS X
    tty = '/dev/tty.usbserial-PXWV0AMC'
    ttyRS232 = '/dev/tty.usbserial-FTAJM1O6'
elif _platform == "win32":
    # Windows...
    # tty =
    pass

# Load sequence configuration
from config import *

# Prepare file
directory = 'data/'
filename = directory+"{0:%y%m%d-%H%M%S}.dat".format(dtm.datetime.now())
with open(filename, mode = 'w', encoding = 'utf-8') as fh:
    # fh.write('#date\ttime(s)\tVe(kV)\tIg(V)\tIc(V)\n')
    fh.write('#date\ttime(s)\tVe(kV)\tIg(V)\tIc(V)\tP(Pa)\n')

# Time to make summary graph wih matplotlib
time_mkgraph = 6*3600# sec

class MyRoot(TabbedPanel):
    pass

class MainView(BoxLayout):
    is_countup = BooleanProperty(False)
    is_sequence = BooleanProperty(False)
    is_connected = BooleanProperty(False)
    is_changevolt = BooleanProperty(False)
    is_holdvolt = BooleanProperty(False)
    time_now = NumericProperty(0)
    volt_now = NumericProperty(0.0)
    volt_target = NumericProperty(0.0)
    seq = ListProperty(SEQ)
    seq_now = NumericProperty(0)
    left_time = NumericProperty()
    Ve_status = StringProperty('Ve')
    Ic_status = StringProperty('Ic')
    Ig_status = StringProperty('Ig')
    P_status = StringProperty('P')
    Ve_value =  NumericProperty()
    Ig_value =  NumericProperty()
    Ic_value =  NumericProperty()
    P_value =  NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def on_command(self, command):
        # global Ve_obj, Ic_obj, Ig_obj
        global Ve_obj, Ic_obj, Ig_obj, P_obj

        if command == 'connect/disconnect':
            if self.is_connected:
                self.disconnect_device()#Ve_obj, Ic_obj, Ig_obj)
            else:
                self.time_now = 0
                # Ve_obj, Ic_obj, Ig_obj = self.connect_device()
                Ve_obj, Ic_obj, Ig_obj, P_obj = self.connect_device()

        elif command == 'start/stop':
            if self.is_countup:
                self.stop_timer()
                # self.Stop_IncVolt()
                self.abort_sequence()
            else:
                # if self.is_connected:
                if Ve_obj:
                    msg = Ve_obj.Clear()
                ### for simple test ###
                # self.Start_IncVolt(1000, dt)
                self.start_timer()
                self.start_sequence(self.seq)
                # MyGraph.do_toggle()
                # MyGraph.do_toggle()
                #######################
                # else:
                    # print('Connect first')
        elif command == 'reset':
            self.abort_sequence()

    def on_countup(self, dt):
        """Callback function for fetching measured values
        """
        try:
            self.Ig_value = Ig_obj.Measure()
            self.Ic_value = Ic_obj.Measure()
            start = time.time()
            self.P_value  = P_obj.RP()
            #elapsed_time = time.time() - start
            #print('elapsed_time: '+str(elapsed_time))
            self.Ic_status = str(self.Ic_value)
            self.Ig_status = str(self.Ig_value)
            self.P_status  = "{0:1.2e}".format(self.P_value)

        except ValueError:
            self.Ig_value = 0
            self.Ic_value = 0
            self.Ic_status = Ic_obj.ClearBuffer()
            self.Ig_status = Ig_obj.ClearBuffer()
        self.Ve_value = self.volt_now

        ### データをファイルに追記
        StoreValue.append_to_file(filename, [self.time_now, self.Ve_value, self.Ig_value, self.Ic_value, "{0:1.2e}".format(self.P_value)])
        ### 経過時間がtime_mkgraphの整数倍の時、グラフｐｄｆを作成 & Send email
        if self.time_now != 0 and self.time_now%time_mkgraph == 0:
            tot_dose = tdep.generate_plot(filename)
            pdffile = filename.rsplit('.dat')[0]+'.pdf'
            print(tot_dose)
            sbj = "[ILISLIFE] Summary Report for the last {0} hours".format(self.time_now/3600)
            msg = "Total dose is {0} (C), {1} (C) and {2} (C) for Ig, Ic and Ig+Ic, repectively.".format(tot_dose[0], tot_dose[1], tot_dose[2])
            epdf.push_email('email.json', sbj, msg, pdffile)

        ### データをMyGraphに送る
        MyGraph.to_val = [self.time_now, self.Ve_value, self.Ig_value, self.Ic_value, self.P_value]

        self.time_now += 1

    def start_timer(self):
        self.is_countup = True
        Clock.schedule_interval(self.on_countup, dt_meas)
        pass

    def stop_timer(self):
        self.is_countup = False
        Clock.unschedule(self.on_countup)
        pass

    def connect_device(self):#, tty, VeAddr, IcAddr, IgAddr):
        """各GPIB機器およびRS232機器を設定する
        """
        Ve_obj = BPHV.E3640A(tty, VeAddr)
        Ic_obj = hioki.dmm3239gpib(tty, IcAddr)
        Ig_obj = hioki.dmm3239gpib(tty, IgAddr)
        P_obj  = gid7.RS232(ttyRS232)
        P_obj.RE() # Set GI-D7 into Remote control mode
        self.Ve_status = Ve_obj.Query('*IDN?')
        self.Ic_status = Ic_obj.Query('*IDN?')
        self.Ig_status = Ig_obj.Query('*IDN?')
        self.P_status = P_obj.GS() # Ask device
        msg = Ve_obj.Clear()
        Ic_obj.Mode()
        Ic_obj.SampleRate(rate='medium')
        Ig_obj.Mode()
        Ig_obj.SampleRate(rate='medium')
        P_obj.F1() # Turn filament on
        self.is_connected = True
        return Ve_obj, Ic_obj, Ig_obj, P_obj

    def disconnect_device(self):#, Ve_obj, Ic_obj, Ig_obj):
        """設定したGPIB機器を初期状態に戻し, ポートを開放する
        """
        Ve_obj.VoltZero()
        Ve_obj.ShutDown()
        Ve_obj.Clear()
        Ic_obj.Rst()
        Ig_obj.Rst()
        P_obj.F0()
        P_obj.LO()
        self.Ve_status = 'Disconnected'
        self.Ic_status = 'Disconnected'
        self.Ig_status = 'Disconnected'
        self.P_status  = 'Disconnected'
        # Ve_obj.ClosePort()
        self.is_connected = False

    # def increment_Volt(self, dt):
    def increment_Volt(self, volt_target, *largs):
        """Callback for increasing voltage
        """
        # print('I am in increment_Volt')
        self.volt_now = Ve_obj.AskVolt()*1000
        volt_raw_now = self.volt_now/1000
        deltaV_raw = dV/1000
        next_raw = '{0:.2f}'.format(volt_raw_now + deltaV_raw)
        Ve_obj.Instruct('volt ' + str(next_raw))
        Ve_obj.OutOn()
        # self.volt_now = '{0:.2f}'.format(Ve_obj.AskVolt())*1000
        self.volt_now = Ve_obj.AskVolt()*1000
        self.Ve_status = str(self.volt_now)
        if self.volt_now >= volt_target:
            self.is_changevolt = False
            return False

    # def decrement_Volt(self, dt):
    def decrement_Volt(self, volt_target, *largs):
        """Callback for decreasing voltage
        """
        # step_raw = Ve_obj.VoltStep(dV)
        self.volt_now = Ve_obj.AskVolt()*1000
        # print(type(self.volt_now))
        volt_raw_now = self.volt_now/1000
        deltaV_raw = dV/1000
        next_raw = '{0:.2f}'.format(volt_raw_now - deltaV_raw)
        Ve_obj.Instruct('volt ' + str(next_raw))
        Ve_obj.OutOn()
        # self.volt_now = '{0:.2f}'.format(Ve_obj.AskVolt())*1000
        self.volt_now = Ve_obj.AskVolt()*1000
        self.Ve_status = str(self.volt_now)
        if self.volt_now <= volt_target:
            self.is_changevolt = False
            return False

    def change_Volt(self, volt_target, *largs):
        """Callback for change voltage
        """
        self.volt_now = Ve_obj.AskVolt()*1000
        if self.volt_now == volt_target:
            self.is_changevolt = False
            return False
        elif self.volt_now < volt_target:
            self.increment_Volt(volt_target, *largs)
        elif self.volt_now > volt_target:
            self.decrement_Volt(volt_target, *largs)
        else:
            print('End change_Volt')
            return False


    def hold_Volt(self, left_time, *largs):
        """Hold voltage output by left_time == 0
        """
        self.volt_now = Ve_obj.AskVolt()*1000
        # print(type(self.volt_now))
        volt_raw_now = self.volt_now/1000
        # Ve_obj.Instruct('volt ' + str(volt_raw_now))
        # Ve_obj.OutOn()
        self.Ve_status = str(self.volt_now)
        if self.left_time <= 0:
            self.seq_now += 1 #シーケンスを1進める
            self.is_holdvolt = False
            return False
        self.left_time -= 1

    def start_sequence(self, seqlist):
        """Start voltage sequence
        """
        if not self.is_sequence:
            self.is_sequence = True
            # trigger = Clock.create_trigger(self.on_countdown, dt_meas)
            # trigger()
            Clock.schedule_interval(self.on_countdown, dt_meas/5)
            print('created on_countdown trigger')

    def on_countdown(self, dt):
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
                    Clock.schedule_interval(partial(self.change_Volt, self.volt_target), dt_op)
                    print('Now on change voltage')


            ### 現在電圧が現在シーケンス設定電圧と等しく, 電圧変更中でなく, hold_Volt中でない場合
            else:
                if not self.is_changevolt and not self.is_holdvolt:
                    self.is_holdvolt = True
                    self.left_time = self.seq[self.seq_now][1] #left_timeにシーケンスリスト
                    # イベントループに投入
                    Clock.schedule_interval(partial(self.hold_Volt, self.left_time), dt_op)
                    print('Now on hold voltage')
        # except IndexError:
        elif self.seq_now > len(self.seq) -1:
            print('All sequences are finished. Measurement is now stopped.')
            self.abort_sequence()

    def get_seq(self):
        """Read sequence status
        """
        try:
            out = str(self.seq[self.seq_now])
        except IndexError:
            out = 'Sequence is over!'
        return out

    def format_seq(self, cur_seq):
        if cur_seq <= len(self.seq) -1:
            output = str(cur_seq)+' [sub]th[/sub]   '+str(self.seq[cur_seq][0])+' [sub]V[/sub]  '+str(self.seq[cur_seq][1])+' [sub]s[/sub]'
        else:
            output = str(cur_seq-1)+' [sub]th[/sub]   '+str(self.seq[cur_seq-1][0])+' [sub]V[/sub]  '+str(self.seq[cur_seq-1][1])+' [sub]s[/sub]'
        return output

    def lapse_time(self, t):
        """Retrun lapse time (hh:mm:ss format)
        """
        rh = (t-t%3600)/3600
        rm = (t-rh*3600-((t-rh*3600)%60))/60
        rs = t%60
        return "{0:2.0f} [sub][i]H[/i][/sub] {1:2.0f} [sub][i]M[/i][/sub] {2:2.0f} [sub][i]S[/i][/sub]".format(rh,rm,rs)

    def total_time(self):
        l = len(self.seq)
        total=0
        for i in range(l):
            if i == 0:
                total += (self.seq[i][0]/dV)*dt_op
            else:
                total += ((self.seq[i][0]-self.seq[i-1][0])/dV)*dt_op
            total += self.seq[i][1]
        return total

    def remaining_time(self,t):
        total = self.total_time()
        rt = total - t
        return self.lapse_time(rt)

    def abort_sequence(self):
        """Force to abort measurement immediately
        """
        self.is_countup = False
        self.is_changevolt = False
        self.is_sequence = False
        self.is_holdvolt = False
        # events = Clock.get_events()
        # for ev in events:
        #    # Clock.unschedule(ev)
        #    ev.cancel()
        try:
            Clock.unschedule(self.change_Volt)
        except:
            print('abort_sequence error 3')
            pass
        try:
            Clock.unschedule(self.on_countdown)
        except:
            print('abort_sequence error 2')
            pass
        try:
            Clock.unschedule(self.on_countup)
        except:
            print('abort_sequence error 1')
            pass
        try:
            Clock.unschedule(self.hold_Volt)
        except:
            print('abort_sequence error 4')
            pass

        if self.is_connected:
            msg = Ve_obj.Clear()
            Ve_obj.VoltZero()
            Ve_obj.OutOff()
            self.seq_now = 0
            self.time_now = 0
            self.volt_now = Ve_obj.AskVolt()*1000
            # Ve_obj.ShutDown()
            # Ig_obj.Cls()
            # Ic_obj.Cls()
            P_obj.F0()
            P_obj.LO()
        pass

    def Start_IncVolt(self, volt_target, dt):
        Clock.schedule_interval(partial(self.increment_Volt, volt_target), dt)
        self.is_changevolt = True
        pass

    def Stop_IncVolt(self):
        Clock.unschedule(self.increment_Volt)
        self.is_countup = False
        pass

class MyGraph(BoxLayout):
    graph_plot = ObjectProperty(None)
    sensorEnabled = BooleanProperty(False)
    graph_y_upl = NumericProperty(2)
    graph_y_lwl = NumericProperty(-1)
    graph_x_range = NumericProperty(600)
    graph_x_hist = NumericProperty(0)
    graph_x_step = NumericProperty(600)
    data_buffer = ListProperty([[],[],[]])
    BUFFSIZE = 43200 # 12 hours = 12*3600 sec
    to_val = ListProperty([0,0,0,0])#, force_dispatch=True)
    Ve_value =  NumericProperty()
    Ig_value =  NumericProperty()
    Ic_value =  NumericProperty()
    P_value  =  NumericProperty()
    # val = np.zeros((BUFFSIZE, 4))
    val = np.zeros((BUFFSIZE, 5))
    t_lapse = np.arange(0,BUFFSIZE)



    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.prepare_graph,0)

    def prepare_graph(self, dt):
        self.graph = self.graph_plot
        # self.graph = self.ids.graph_plot
        print('**************************')
        print(self.graph)
        print('**************************')
        self.plot = []
        self.plot.append(MeshLinePlot(color=[1, 0, 0, 1]))  # X - Red
        self.plot.append(MeshLinePlot(color=[0, 1, 0, 1]))  # Y - Green
        self.plot.append(MeshLinePlot(color=[0, 0.5, 1, 1]))  # Z - Blue
        self.plot.append(MeshLinePlot(color=[0.5, 0.5, 1, 1]))  # pressure log
        self.reset_plots()
        for plot in self.plot:
            self.graph.add_plot(plot) # Add MeshLinePlot object of garden.graph into Graph()
            # graph.add_plot(plot) # Add MeshLinePlot object of garden.graph into Graph()

    def ymin_up(self):
        if (self.graph_y_upl -1 > self.graph_y_lwl):
            self.graph_y_lwl += 1
    def ymax_down(self):
        if (self.graph_y_upl -1 > self.graph_y_lwl):
            self.graph_y_upl -= 1
    def reset_plots(self):
        for plot in self.plot:
            # plot.points = [(0, 0),(1,0.5)]
            plot.points = [(0, 0)]
        # self.counter = 1

    def do_toggle(self):
        try:
            if not self.sensorEnabled:
                print('excuted do_toggle()',dt_meas)
                # Clock.schedule_interval(StoreValue.make_random_data, dt_meas)
                Clock.schedule_interval(self.get_mydata,dt_meas)
                self.sensorEnabled = True
            else:
                # Clock.unschedule(StoreValue.make_random_data)
                Clock.unschedule(self.get_mydata)
                self.sensorEnabled = False
        except NotImplementedError:
                popup = ErrorPopup()
                popup.open()



    # def read_file(self, filename):
    #     last = os.popen('tail -1 '+filename).read().rsplit('\n')[0].split('\t')[2:] ### Implement
    #     # print(last)
    #     # with open(filename, mode = 'r', encoding = 'utf-8') as fh:
    #         # last = fh.readlines()[-1].rsplit('\n')[0].split('\t')[2:]
    #     ve = float(last[0])/1000.
    #     ig = float(last[1])*1000
    #     ic = float(last[2])*1000
    #     return [ve,ig,ic]

    def get_mydata(self, dt):
        self.val[0] = self.to_val
        ### Modify values digits
        self.val[0, 1:] = self.val[0,1:] * (1e-3, 1e+3, 1e+3, 1)
        if self.val[0,4] != 0:
            self.val[0, 4] = np.log10(self.val[0, 4])
        else:
            self.val[0, 4] = -10#np.log10(self.val[0, 4])
        # Reset time
        self.val[:,0] = self.t_lapse

        output1 = self.val[:,(0,1)].tolist() # for (t, Ve)
        output2 = self.val[:,(0,2)].tolist()  # for (t, Ig)
        output3 = self.val[:,(0,3)].tolist()  # for (t, Ic)
        output4 = self.val[:,(0,4)].tolist()  # for (t, P)

        self.plot[0].points = output1
        self.plot[1].points = output2
        self.plot[2].points = output3
        self.plot[3].points = output4
        self.val = np.roll(self.val, 1, axis=0)

    def format_val(self, val):
        return '{0:.3f}'.format(val)
    def _make_random_data(self):
        ## valに値を代入する. 例では乱数を入れている.
        self.val = [random.random()+0.2, random.random(), random.random()-0.2]
        return self.val

class StoreValue(BoxLayout):
    """Store measured values to file
    """
    sv = ObjectProperty()
    Ve_value =  NumericProperty()
    Ig_value =  NumericProperty()
    Ic_value =  NumericProperty()
    P_value  =  NumericProperty()
    is_random = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def start_random(self):
        self.is_random = True
        print('start_random is pressed')
        Clock.schedule_interval(self.make_random_data, 1)

    def stop_random(self):
        self.is_random = False
        Clock.unschedule(self.make_random_data)

    # @classmethod
    def make_random_data(self, dt):
        ## valに値を代入する. 例では乱数を入れている.
        self.Ve_value, self.Ig_value, self.Ic_value = random.random()+0.2, random.random(), random.random()-0.2
        #### 値をMyGraphに渡す!
        MyGraph.to_val = [self.Ve_value, self.Ig_value, self.Ic_value]
        print(self.Ve_value, self.Ig_value, self.Ic_value)
        # return

    @classmethod
    def append_to_file(cls, filename, data1d):
        ## ファイルにデータ書き込み
        datastr = ''
        with open(filename, mode = 'a', encoding = 'utf-8') as fh:
            for data in data1d:
                datastr += '\t'+str(data)
            fh.write(str(cls.get_ctime()) + datastr + '\n')
    @classmethod
    def get_ctime(self):
        t = dtm.datetime.now()
        point = (t.microsecond - t.microsecond%10000)/10000
        app_time = "{0:%y%m%d-%H:%M:%S}.{1:.0f}".format(t, point)
        return app_time



class IlislifeApp(App):
    pass
    # def build(self):
    #     # self.screens["wordcomp"].bind(count_r=self.screens["score"].setter('score'))
    #     # self.MyGraph(app=self).bind(Ve_value=self.MainView(app=self).setter('Ve_value'))
    #     return MyRoot()


if __name__ == '__main__':
    IlislifeApp().run()
