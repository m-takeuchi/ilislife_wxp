#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, os, json, importlib, tempfile
from importlib import machinery
import wx
import mygraph
import numpy as np
import datetime as dtm
import ilis_noiv
#import ilis_dummy as ilis

from wx.lib.pubsub import pub

import types
# from pympler import muppy
# from pympler import summary
# from pympler import tracker
# tr = tracker.SummaryTracker()

# import gc
# from collections import defaultdict
# def output_memory():
#     d = defaultdict(int)
#     for o in gc.get_objects():
#         name = type(o).__name__
#         d[name] += 1

#     items = d.items()
#     items.sort(key=lambda x:x[1])
#     for key, value in items:
#         print(key, value)



class ConfigPanel(wx.Panel):
    cfg_param = {} ### config parameters to be used for another classes
    var_param = {} ### current status
    var_arr = [] ### current data to be saveed to file

    def __init__(self, parent):
        super(ConfigPanel, self).__init__(parent, wx.ID_ANY)
        # self.SetBackgroundColour("#00FF00")


        self.elt1 = ("Determin from date-time", "Chose from file")
        ### Save file name
        self.cbx_file = wx.ComboBox(self, wx.ID_ANY, "Save to ...", choices=self.elt1, style=wx.CB_DROPDOWN)
        self.cbx_file.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        ### Set comment to the file
        self.txt_cmt = wx.TextCtrl(self, wx.ID_ANY, "Comment")
        ### Config botton
        self.btn_cfg = wx.Button(self, wx.ID_ANY, "Config", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_cfg.Bind(wx.EVT_BUTTON, self.open_cfg)
        ### Set sequence
        self.btn_seq = wx.Button(self, wx.ID_ANY, "Sequence", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_seq.Bind(wx.EVT_BUTTON, self.open_seq)
        ### Connect botton
        self.btn_cnt = wx.Button(self, wx.ID_ANY, "Connect", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_cnt.Bind(wx.EVT_BUTTON, self.OnConnect)
        ### Start measurement botton
        self.btn_sta = wx.Button(self, wx.ID_ANY, "Start", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_sta.Bind(wx.EVT_BUTTON, self.OnStart)
        ### Reset measurement botton
        self.btn_rst = wx.Button(self, wx.ID_ANY, "Reset", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_rst.Bind(wx.EVT_BUTTON, self.OnReset)
        ### Sequence view
        self.seq_view = SeqList(self)

        ### Static lines
        self.stl_1 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.stl_2 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)


        ### Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.cbx_file, flag=wx.GROW)
        layout.Add(self.txt_cmt, flag=wx.GROW)
        layout.AddSpacer(10)
        layout.Add(self.stl_1, flag=wx.GROW)
        layout.Add(self.btn_cfg, flag=wx.GROW)
        layout.Add(self.btn_seq, flag=wx.GROW)
        layout.AddSpacer(10)
        layout.Add(self.stl_2, flag=wx.GROW)
        layout.AddSpacer(10)
        layout.Add(self.btn_cnt, flag=wx.GROW)
        layout.Add(self.btn_sta, flag=wx.GROW)
        layout.Add(self.btn_rst, flag=wx.GROW)
        layout.AddSpacer(10)
        layout.Add(self.seq_view, proportion=1, flag=wx.EXPAND )
        self.SetSizer(layout)

        ### Prepare wx.Timer
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_timer, self.update_timer)
        # self.update_timer.Start(1000) #ms

        ### Subscribe config informations from ConfigDialog class
        pub.subscribe(self.cfg_listen, "cfgListner")
        ### Subscribe sequence information from SequenceSetting class
        pub.subscribe(self.seq_listen, "seqListner")

    def OnSelect(self, event):
        self.fileopt = event.GetSelection()
        print(self.fileopt)
        if self.fileopt == 0 or None:
            self.dirName = os.path.dirname(os.path.abspath(__file__))+'/data/'
            self.fileName = "{0:%y%m%d-%H%M%S}.dat".format(dtm.datetime.now())
            self.datafilepath = os.path.join(self.dirName, self.fileName)
        if self.fileopt == 1:
            self.dirName = os.path.dirname(os.path.abspath(__file__))
            ### Show file dialog to load file
            dialog = wx.FileDialog(self, "Save data file to", self.dirName, "", "*.dat", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            ### Show until pushing OK button
            if dialog.ShowModal() == wx.ID_OK:
                self.fileName = dialog.GetFilename()
                self.dirName = dialog.GetDirectory()
                self.datafilepath = os.path.join(self.dirName, self.fileName)
            ### Destroy dialog
            dialog.Destroy()

    def SaveHeader(self):
        if self.fileopt == 0 or None:
            self.dirName = os.path.dirname(os.path.abspath(__file__))+'/data/'
            self.fileName = "{0:%y%m%d-%H%M%S}.dat".format(dtm.datetime.now())
            self.datafilepath = os.path.join(self.dirName, self.fileName)
        with open(self.datafilepath, 'w') as f:
            f.write('#'+self.txt_cmt.GetValue()+'\n')
            f.write('#date\ttime(s)\tVe(V)\tIg(V)\tIc(V)\tP(Pa)\tIV_No\n')

    def open_cfg(self, event):
        dialog = ConfigDialog(self, self.cfg_param)
        try:
            # dialog.ShowModal()
            dialog.Show()
        finally:
            # dialog.Destroy()
            self.cfg_param = dialog.cfg_param
            # print(self.cfg_param)
            # dialog.Destroy()
            # print('Destroied')
        # self.cfg_param = dialog.cfg_param
        return True
        # return self.cfg_param

    def cfg_listen(self, message):
        """ pub listner to get config dict from ConfigPanel class
        """
        self.cfg_param = message

    def open_seq(self, event):
        seqSet = SequenceSetting(self)
        seqSet.Show()

    def seq_listen(self, message):
        """ pub listner to get sequence list from SequenceSetting class
        """
        # self.SEQ = message
        self.seq_var = message

    def OnConnect(self, event):
        lbl = self.btn_cnt.GetLabel()
        if lbl == 'Connect':
            self.dev = ilis.Operation()
            self.dev.portGPIB = self.cfg_param['pgx_port']
            self.dev.VeAddr = int(self.cfg_param['VeAddr'])
            self.dev.IgAddr = int(self.cfg_param['IgAddr'])
            self.dev.IcAddr = int(self.cfg_param['IcAddr'])
            self.dev.portRS232 = self.cfg_param['gid7_port']
            self.dev.dt = float(self.cfg_param['sampling'])
            self.dev.dV = float(self.seq_var.dV)
            self.dev.seq = self.seq_var.SEQ
            self.dev.left_time = self.dev.seq[self.dev.seq_now] ### Set left time for 1st sequence to hold voltage
            # dev.P_abt = float(self.cfg_param['pressure_abort'])
            # dev.P_pst = float(self.cfg_param['pressure_postpone'])

            ### Message dialog for comfirmation
            yesno_dialog = wx.MessageDialog(self, "Sure to turn on ion guage filament?", "CAUTION", wx.YES_NO | wx.ICON_QUESTION)
            try:
                if yesno_dialog.ShowModal() == wx.ID_YES:
                    self.dev.ConnectDevice()
                    self.btn_cnt.SetLabel('Disconnect')
                    self.Close()
                    return True
            except Exception as e:
                print('Error object:\n' + str(e))
            finally:
                yesno_dialog.Destroy()

        elif lbl == 'Disconnect':
            yesno_dialog = wx.MessageDialog(self, "Sure to Disconnect?", "CAUTION", wx.YES_NO | wx.ICON_QUESTION)
            try:
                if yesno_dialog.ShowModal() == wx.ID_YES:
                    self.dev.StopSequence()
                    self.dev.DisconnectDevice()
                    self.btn_cnt.SetLabel('Connect')
                    self.Close()
            finally:
                yesno_dialog.Destroy()
                return False
        else:
            return False

    def OnStart(self, event):
        lbl = self.btn_sta.GetLabel()
        if not self.dev:
            return False
        if self.dev.is_connected == True:
            if lbl == 'Start':
                self.btn_sta.SetLabel('Stop')
                self.SaveHeader() # Make datafile only with header
                # self.update_timer.Start(1000) #ms, Should is this self.dev.dt?
                self.update_timer.Start(self.dev.dt*1000) #ms, Should is this self.dev.dt?
                self.dev.StartSequence()
                return True
            elif lbl == 'Stop':
                self.btn_sta.SetLabel('Start')
                self.update_timer.Stop()
                self.dev.StopSequence()
                return False
        elif self.dev.is_connected == False:
            return False
    def OnReset(self, event):
        if not self.dev:
            return False
        elif self.dev.is_connected == True:
            self.dev.Ve_obj.VoltZero()

    def on_update_timer(self, event):
        self.seq_now  = self.dev.seq_now
        self.Ve_status = self.dev.Ve_status
        self.Ig_status = self.dev.Ig_status
        self.Ic_status = self.dev.Ic_status
        self.P_status  = self.dev.P_status
        self.Ve_value  = self.dev.Ve_value
        self.Ig_value  = self.dev.Ig_value
        self.Ic_value  = self.dev.Ic_value
        self.P_value  = self.dev.P_value

        ###
        self.var_param = {'dt':self.dev.dt, 'seq_now':self.dev.seq_now, 'time_now':self.dev.time_now, 'Ve_status':self.dev.Ve_status, 'Ig_status':self.dev.Ig_status, 'Ic_status':self.dev.Ic_status, 'P_status':self.dev.P_status, 'Ve_value':self.dev.Ve_value, 'Ig_value':self.dev.Ig_value, 'Ic_value':self.dev.Ic_value, 'P_value':self.dev.P_value}
        # print(self.var_param)
        if self.dev.is_iv == True:
            self.var_arr = [round(self.dev.time_now), self.dev.Ve_value, self.dev.Ig_value, self.dev.Ic_value, self.dev.P_value, self.dev.count_iv]
        else:
            self.var_arr = [round(self.dev.time_now), self.dev.Ve_value, self.dev.Ig_value, self.dev.Ic_value, self.dev.P_value, 0]
        # print('count_iv = ', self.var_arr[-1])

        ### Normal data append for time-dependent measuremt
        self.append_to_file()
        ### I-V data save
        # if self.dev.is_iv == True:
        #     if

        wx.CallAfter(pub.sendMessage, "varListner", message=self.var_param)
        # print([self.Ve_value, self.Ig_value, self.Ic_value, self.P_value])

        #####output_memory()
        # all_objects = muppy.get_objects()
        # sum1 = summary.summarize(all_objects)
        # summary.print_(sum1)
        # tr.print_diff()
        # print(len(all_objects))

    def prepare_ivdatafile(self):
        self.ivfileName = self.fileName.rsplit('.dat')[0]+'_iv'+'{0:03d}'.format(self.dev.count_iv)+'.dat'
        self.ivdatafilepath = os.path.join(self.dirName, self.ivfileName)
        with open(self.ivdatafilepath, 'w') as f:
            f.write('#'+self.ivfileName+'\n')
            f.write('#date\ttime(s)\tVe(kV)\tIg(V)\tIc(V)\tP(Pa)\n')
    def append_ivdatafile(self):
        datastr = ''
        for data in self.var_arr:
            datastr += '\t'+str(data)
        with open(self.ivdatafilepath, 'a') as fh:
            fh.write(str(self.get_ctime()) + datastr + '\n')

    def append_to_file(self):
        ## Append data to specific file
        datastr = ''
        for data in self.var_arr:
            datastr += '\t'+str(data)
        with open(self.datafilepath, mode = 'a', encoding = 'utf-8') as fh:
            fh.write(str(self.get_ctime()) + datastr + '\n')

    def get_ctime(self):
        self.t = dtm.datetime.now()
        self.point = (self.t.microsecond - self.t.microsecond%10000)/10000
        self.app_time = "{0:%y%m%d-%H:%M:%S}.{1:.0f}".format(self.t, self.point)
        return self.app_time

class SequenceSetting(wx.Frame):
    seq_str = ""
    def __init__(self, parent):
        super(SequenceSetting, self).__init__(parent, wx.ID_ANY, title="Sequence Setting")

        ### Text area to display email.json file
        self.txt_seq = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_MULTILINE)

        ### Load, Save and Apply botton
        btn_load = wx.Button(self, wx.ID_ANY, "Load")
        btn_load.Bind(wx.EVT_BUTTON, self.button_load_click)
        btn_save = wx.Button(self, wx.ID_ANY, "Save")
        btn_save.Bind(wx.EVT_BUTTON, self.button_save_click)
        btn_apply = wx.Button(self, wx.ID_ANY, "Apply")
        btn_apply.Bind(wx.EVT_BUTTON, self.button_apply_click)
        hbox_btn = wx.BoxSizer(wx.HORIZONTAL)
        hbox_btn.Add(btn_load, proportion=1, flag=wx.GROW | wx.ALL, border=10)
        hbox_btn.Add(btn_save, proportion=1,  flag=wx.GROW | wx.ALL, border=10)
        hbox_btn.Add(btn_apply,  proportion=1, flag=wx.GROW | wx.ALL, border=10)

        layout = wx.BoxSizer(wx.VERTICAL)
        # layout.Add(pnl_dtl, flag=wx.GROW)
        layout.Add(self.txt_seq, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        layout.AddSpacer(10)
        layout.Add(hbox_btn, flag=wx.GROW|wx.ALL, border=10)
        self.SetSizer(layout)

    def update_seq(self):
        self.txt_seq.SetValue(self.seq_str)
    def read_seq(self):
        self.seq_str = self.txt_seq.GetValue()

    def check_seq(self, module):
        """Check sequence syntax
        """
        pass
        # if not module.dV:
        #     if type(module.dV) is not int:
        #         if module.dV < 1:
        #             return False
        #         return False
        #     return False
        # elif not module.dt_meas:

    def button_load_click(self, event):
        self.dirName = os.path.dirname(os.path.abspath(__file__))
        ### Show file dialog to load file
        dialog = wx.FileDialog(self, "Load sequence file", self.dirName, "", "*.py", wx.FD_OPEN  | wx.FD_FILE_MUST_EXIST)
        ### Show until pushing OK button
        if dialog.ShowModal() == wx.ID_OK:
            self.fileName = dialog.GetFilename()
            self.dirName = dialog.GetDirectory()
            with open(os.path.join(self.dirName, self.fileName), 'r') as f:
                self.seq_str = "".join(f.readlines())
            self.update_seq()
        ### Destroy dialog
        dialog.Destroy()

    def button_save_click(self, event):
        self.read_seq()
        self.dirName = os.path.dirname(os.path.abspath(__file__))
        ### Show file dialog to load file
        dialog = wx.FileDialog(self, "Save sequence file", self.dirName, "", "*.py", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        ### Show until pushing OK button
        if dialog.ShowModal() == wx.ID_OK:
            self.fileName = dialog.GetFilename()
            self.dirName = dialog.GetDirectory()
            with open(os.path.join(self.dirName, self.fileName), 'w') as f:
                f.writelines(self.seq_str)
        ### Destroy dialog
        dialog.Destroy()

    def button_apply_click(self, event):
        yesno_dialog = wx.MessageDialog(self, "Apply now?",
            "CAUTION", wx.YES_NO | wx.ICON_QUESTION)

        try:
            if yesno_dialog.ShowModal() == wx.ID_YES:
                self.read_seq()
                ### Save seq_str as a temporary file
                fd, path = tempfile.mkstemp()
                # print(path)
                os.write(fd, self.seq_str.encode("utf-8"))
                ### Dinamically import py module
                # seq_var = importlib.import_module('sequence')
                self.seq_var = machinery.SourceFileLoader("seq_var", path).load_module()
                self.check_seq(self.seq_var)
                ### Send arg over class
                # pub.sendMessage("seqListner", message=self.seq_var.SEQ)
                pub.sendMessage("seqListner", message=self.seq_var)
                self.Close()
        finally:
            yesno_dialog.Destroy()
        return True

class SeqList(wx.ListCtrl):
    """Prepare sequence list on the top frame
    """
    SEQ = []
    seq_var = {}
    def __init__(self, parent):
        super(SeqList, self).__init__(parent, wx.ID_ANY, style=wx.LC_REPORT
                         |wx.BORDER_SUNKEN)

        pub.subscribe(self.seq_listen, "seqListner")
        pub.subscribe(self.var_listen, "varListner")

        # self.list = wx.ListCtrl(panel, -1, style = wx.LC_REPORT)
        self.InsertColumn(0, "#", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, "Ve (V)", wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, "Time (s)", wx.LIST_FORMAT_RIGHT)

        self.SetColumnWidth(0, 20)
        self.SetColumnWidth(1, 60)
        self.SetColumnWidth(2, 60)


    def seq_listen(self, message):
        """ pub listner to get sequence list from SequenceSetting class
        """
        # self.SEQ = message
        self.seq_var = message
        self.SEQ = self.seq_var.SEQ

        for i,v in enumerate(self.SEQ):
            self.InsertItem(i, str(i))
            self.SetItem(i, 1, str(v[0]))
            self.SetItem(i, 2, str(v[1]))

    def get_seq(self, d):
        self.seq_now = d['seq_now']

    def var_listen(self, message):
        self.get_seq(message)
        self.HLTcolour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        if self.seq_now == 0: ### First sequence
            self.SetItemBackgroundColour(self.seq_now, col=self.HLTcolour)
        elif self.seq_now == len(self.SEQ): ### After sequence
            self.SetItemBackgroundColour(self.seq_now -1 , col='#FFFFFF')
        else: ### on sequence
            self.SetItemBackgroundColour(self.seq_now -1 , col='#FFFFFF')
            self.SetItemBackgroundColour(self.seq_now, col=self.HLTcolour)
        pass


# class ConfigDialog(wx.Dialog):
class ConfigDialog(wx.Frame):
    # cfg_param = {} ### config parameters to be going to read from config.json
    def __init__(self, parent, cfg):
        super(ConfigDialog, self).__init__(parent, wx.ID_ANY, title="Config")
        # if self.cfg_param == {}:
        if cfg == {}:
            self.load_default() # This input default params into self.cfg_param
            print('Loaded default config')
        elif cfg != {}:
            self.cfg_param = cfg
            # self.load_default()
            print('Loaded dafault2 config')
            print(cfg)
            # print(self.cfg_param)

        ### Sampling period
        self.lbl_sampling = wx.StaticText(self, wx.ID_ANY, "Sampling period (s)")
        self.txt_sampling = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['sampling'])
        ### Prologix serial port
        self.lbl_pgx = wx.StaticText(self, wx.ID_ANY, "Prologix port")
        self.txt_pgx = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['pgx_port'])
        ### GPIB channel
        self.lbl_gpib = wx.StaticText(self, wx.ID_ANY, "GPIB (Ve, Ig, Ic)")
        self.txt_gpib_Ve = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['VeAddr'])
        self.txt_gpib_Ig = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['IgAddr'])
        self.txt_gpib_Ic = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['IcAddr'])
        hbox_gpib = wx.BoxSizer(wx.HORIZONTAL)
        hbox_gpib.Add(self.txt_gpib_Ve, proportion=1, flag=wx.GROW)
        hbox_gpib.Add(self.txt_gpib_Ig, proportion=1, flag=wx.GROW)
        hbox_gpib.Add(self.txt_gpib_Ic, proportion=1, flag=wx.GROW)
        ### Serial port for GI-D7
        self.lbl_gi = wx.StaticText(self, wx.ID_ANY, "Port for GI-D7")
        self.txt_gi = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['gid7_port'])
        ### Pressure limit to abort
        self.chb_pla = wx.CheckBox(self, wx.ID_ANY, "P limit to abort")
        self.txt_pla = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['pressure_abort'])
        ### Pressure limit to postpone
        self.chb_plp = wx.CheckBox(self, wx.ID_ANY, "P limit to postpone")
        self.txt_plp = wx.TextCtrl(self, wx.ID_ANY, self.cfg_param['pressure_postpone'])
        ### Email Notifyer
        self.chb_emn = wx.CheckBox(self, wx.ID_ANY, "Email notifyer")
        self.btn_emn = wx.Button(self, wx.ID_ANY, "Detail")
        self.btn_emn.Bind(wx.EVT_BUTTON, self.open_emn_detail)

        ### Layout ConfigDaialog
        fgs_layout = wx.FlexGridSizer(2,4,1)
        fgs_layout.Add(self.lbl_sampling, flag=wx.GROW)
        fgs_layout.Add(self.txt_sampling, flag=wx.GROW)
        fgs_layout.Add(self.lbl_pgx, flag=wx.GROW)
        fgs_layout.Add(self.txt_pgx, flag=wx.GROW)
        fgs_layout.Add(self.lbl_gpib, flag=wx.GROW)
        fgs_layout.Add(hbox_gpib, flag=wx.GROW)
        fgs_layout.Add(self.lbl_gi, flag=wx.GROW)
        fgs_layout.Add(self.txt_gi, flag=wx.GROW)
        fgs_layout.Add(self.chb_pla, flag=wx.GROW)
        fgs_layout.Add(self.txt_pla, flag=wx.GROW)
        fgs_layout.Add(self.chb_plp, flag=wx.GROW)
        fgs_layout.Add(self.txt_plp, flag=wx.GROW)
        fgs_layout.Add(self.chb_emn, flag=wx.GROW)
        fgs_layout.Add(self.btn_emn, flag=wx.GROW)

        ### Load, Save and Apply botton
        btn_load = wx.Button(self, wx.ID_ANY, "Load")
        btn_load.Bind(wx.EVT_BUTTON, self.button_load_click)
        btn_save = wx.Button(self, wx.ID_ANY, "Save")
        btn_save.Bind(wx.EVT_BUTTON, self.button_save_click)
        btn_apply = wx.Button(self, wx.ID_ANY, "Apply")
        btn_apply.Bind(wx.EVT_BUTTON, self.button_apply_click)
        hbox_btn = wx.BoxSizer(wx.HORIZONTAL)
        hbox_btn.Add(btn_load, proportion=1, flag=wx.GROW, border=10)
        hbox_btn.Add(btn_save, proportion=1,  flag=wx.GROW, border=10)
        hbox_btn.Add(btn_apply,  proportion=1, flag=wx.GROW, border=10)

        layout = wx.BoxSizer(wx.VERTICAL)
        # layout.Add(pnl_dtl, flag=wx.GROW)
        layout.Add(fgs_layout, proportion=1, flag=wx.GROW|wx.RIGHT|wx.LEFT|wx.TOP, border=10)
        # layout.AddSpacer(10)
        layout.Add(hbox_btn, proportion=1,flag=wx.GROW|wx.RIGHT|wx.LEFT|wx.BOTTOM, border=10)
        self.SetSizer(layout)

    def load_default(self):
        self.dirName = os.path.dirname(os.path.abspath(__file__))
        self.fileName = 'config.json'
        try:
            with open(os.path.join(self.dirName, self.fileName), 'r') as f:
                self.cfg_param = json.load(f)
        except:
            print('Please set config.json')

    def update_config(self):
        self.txt_sampling.SetValue(self.cfg_param['sampling'])
        self.txt_pgx.SetValue(self.cfg_param['pgx_port'])
        self.txt_gpib_Ve.SetValue(self.cfg_param['VeAddr'])
        self.txt_gpib_Ig.SetValue(self.cfg_param['IgAddr'])
        self.txt_gpib_Ic.SetValue(self.cfg_param['IcAddr'])
        self.txt_gi.SetValue(self.cfg_param['gid7_port'])
        self.txt_pla.SetValue(self.cfg_param['pressure_abort'])
        self.txt_plp.SetValue(self.cfg_param['pressure_postpone'])

    def read_config(self):
        self.cfg_param['sampling'] = self.txt_sampling.GetValue()
        self.cfg_param['pgx_port'] = self.txt_pgx.GetValue()
        self.cfg_param['VeAddr'] = self.txt_gpib_Ve.GetValue()
        self.cfg_param['IgAddr'] = self.txt_gpib_Ig.GetValue()
        self.cfg_param['IcAddr'] = self.txt_gpib_Ic.GetValue()
        self.cfg_param['gid7_port'] = self.txt_gi.GetValue()
        self.cfg_param['pressure_abort'] = self.txt_pla.GetValue()
        self.cfg_param['pressure_postpone'] = self.txt_plp.GetValue()


    def button_load_click(self, event):
        self.dirName = os.path.dirname(os.path.abspath(__file__))
        ### Show file dialog to load file
        dialog = wx.FileDialog(self, "Load configuration file", self.dirName, "", "*.json", wx.FD_OPEN  | wx.FD_FILE_MUST_EXIST)
        ### Show until pushing OK button
        if dialog.ShowModal() == wx.ID_OK:
            self.fileName = dialog.GetFilename()
            self.dirName = dialog.GetDirectory()
            with open(os.path.join(self.dirName, self.fileName), 'r') as f:
                self.cfg_param = json.load(f)
            self.update_config()
        ### Destroy dialog
        dialog.Destroy()
        # print(self.cfg_param)

    def button_save_click(self, event):
        self.read_config()
        self.dirName = os.path.dirname(os.path.abspath(__file__))
        ### Show file dialog to load file
        dialog = wx.FileDialog(self, "Save configuration file", self.dirName, "", "*.json", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        ### Show until pushing OK button
        if dialog.ShowModal() == wx.ID_OK:
            self.fileName = dialog.GetFilename()
            self.dirName = dialog.GetDirectory()
            with open(os.path.join(self.dirName, self.fileName), 'w') as f:
                json.dump(self.cfg_param, f, sort_keys=True, indent=4)
            # print(self.cfg_param)
        ### Destroy dialog
        dialog.Destroy()

    def button_apply_click(self, event):
        yesno_dialog = wx.MessageDialog(self, "Apply now?",
            "CAUTION", wx.YES_NO | wx.ICON_QUESTION)

        try:
            if yesno_dialog.ShowModal() == wx.ID_YES:
                self.read_config()
                # self.update_config()
                # print(self.cfg_param)
                self.Close()
                pub.sendMessage("cfgListner", message=self.cfg_param)
        finally:
            yesno_dialog.Destroy()
        return True

    def open_emn_detail(self, event):
        dialog = EmailDetail(self)
        try:
            dialog.ShowModal()
        finally:
            dialog.Destroy()
        return True


class EmailDetail(wx.Dialog):
    def __init__(self, parent):
        super(EmailDetail, self).__init__(parent, wx.ID_ANY)
        jsonfile = os.path.dirname(os.path.abspath(__file__))+'/email.json'
        if jsonfile:
            with open('email.json', 'r') as f:
                lines = f.readlines()
                jsondata = ''.join(lines)
        else:
            jsondata = ''

        ### Text area to display email.json file
        self.txt_eml = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_MULTILINE)
        self.txt_eml.AppendText(jsondata)
        ### Load, Save and Apply buttons
        self.btn_load = wx.Button(self, wx.ID_ANY, 'Load')
        self.btn_save = wx.Button(self, wx.ID_ANY, 'Save')
        self.btn_apply = wx.Button(self, wx.ID_ANY, 'apply')
        hbox_btn = wx.BoxSizer(wx.HORIZONTAL)
        hbox_btn.Add(self.btn_load, proportion=1, flag=wx.GROW | wx.ALL, border=10)
        hbox_btn.Add(self.btn_save, proportion=1, flag=wx.GROW | wx.ALL, border=10)
        hbox_btn.Add(self.btn_apply, proportion=1, flag=wx.GROW | wx.ALL, border=10)

        ### Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.txt_eml, proportion=1, flag=wx.EXPAND)
        layout.Add(hbox_btn, proportion=1, flag=wx.GROW)
        self.SetSizer(layout)



# class MyGraphPanel(mygraph.GraphPanel):
#     def __init__(self, parent):
#         super(MyGraphPanel, self).__init__(parent, wx.ID_ANY)
#         # self.SetBackgroundColour("#FF0000")
#         pub.subscribe(self.var_listen, "varListner")

#     def var_listen(self, message):
#         """ pub listner to get var list from SequenceSetting class
#         """
#         # print(message)
#         self.dt = message['dt']
#         self.val_arr[0,1:] = np.array([message['Ve_value'], message['Ig_value'], message['Ic_value'], message['P_value']])
#         # print(self.val_arr[0:1,:])

#         self.val_arr = np.roll(self.val_arr, 1, axis=0) # Roll 1 element forward
#         self.t += self.dt
#         # self.val_arr[0,0] = self.t
#         self.val_arr[:,0] = np.arange(0, -self.BUFFSIZE*self.dt, -self.dt)

#         ### Put values by self.datagen.next
#         # self.val_arr[0,1:] = [self.datagen.read() for i in range(self.COLS-1)]

#         self.draw_plot()


class TopForm(wx.Frame):
    """MainFrame of this app
    """
    def __init__(self):
        # wx.Frame.__init__(self, None, wx.ID_ANY, "Tutorial")
        # super().__init__(None, wx.ID_ANY, "ILISlife", size=(800,600))
        super().__init__(None, wx.ID_ANY, "ILISlife", size=(200,600))
        # self.mgp = MyGraphPanel(self)
        self.cfp = ConfigPanel(self)
        self.stb = self.CreateStatusBar()
        self.stb.SetStatusText( "Welcome to ILISlife" )
        pub.subscribe(self.var_listen, "varListner")

        layout = wx.BoxSizer(wx.HORIZONTAL)
        # layout.Add(self.cfp, proportion=0.1,flag=wx.GROW | wx.ALL, border=10)
        layout.Add(self.cfp, proportion=1,flag=wx.GROW | wx.ALL, border=10)        
        layout.Add(wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL), flag=wx.GROW)
        # layout.Add(self.mgp, proportion=3, flag=wx.EXPAND | wx.RIGHT)
        self.SetSizer(layout)

    def format_info(self, d):
        self.fmt_txt = ""
        self.var_list = [d['time_now'], d['seq_now'], d['Ve_status'], d['Ig_status'], d['Ic_status'], d['P_status']]
        self.lab_list = ['Time(s)', 'Seq.No','Ve','Ig','Ic','P']
        for i,v in enumerate(self.var_list):
            self.fmt_txt += self.lab_list[i]+': '+str(v) + ' '
        return self.fmt_txt

    def var_listen(self, message):
        self.info_txt = self.format_info(message)
        self.stb.SetStatusText(self.info_txt)
        pass

class MyApp(wx.App):
    def __init__(self):
        wx.App.__init__(self,False) #//ココ


if __name__ == "__main__":
    # app = wx.App()
    # app = wx.App(redirect=True)
    # app = wx.App(redirect=True,filename="mylogfile.txt")
    app = MyApp()
    frame = TopForm().Show()
    app.MainLoop()
