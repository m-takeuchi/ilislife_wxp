
# import serial
from prologix import GPIBUSB
import time
import numpy as np
import sys

#portname = '/dev/ttyS0'
#BAUDRATE = 9600


class E3640A(GPIBUSB):

    def __init__(self, portNum, addr, reset=False):
        GPIBUSB.__init__(self, portNum, reset=False)
        self.setProAuto() #Set prologix to auto mode
        self.addr = addr

    #=============== basic functions ========================
    def Scan(self):
        return self.Read(self.addr)

    def Instruct(self, buffer):
        self.Write(self.addr, buffer)

    def Query(self, buffer):
        return self.Ask(self.addr, buffer)


    def Clear(self):
        return self.Query(':system:error?')

    def VoltZero(self):
        self.Write(self.addr, "voltage 0")
        self.Clear()

    def AskVolt(self):
        volt_raw = self.Query("voltage?")
        # print(volt_raw, type(volt_raw))
        if volt_raw == '+0,"No error"\n':
            #再度読み込む
            volt_raw = self.Query("voltage?")
        return float(volt_raw)

    def VoltStep(self, step):
        """
        """
        step_raw = step/1000.0 #Convert from HVPS voltage step to E3640A voltage step
        if step_raw < 0.01:
            print("Voltage step too small. Specify Vstep >= 10 V.")
            sys.exit()
        elif step_raw > 0.2:
            print("Voltage step too big. Specify Vstep <= 200 V.")
            sys.exit()
        else:
            print(("Voltage step " + str(step) + " is OK."))
        self.Instruct("voltage:step " + str(step_raw))
        return step_raw

    def OutOn(self):
        self.Instruct('OUTPUT On')

    def OutOff(self):
        self.Instruct('OUTPUT OFF')

    def ShutDown(self):
        self.VoltZero()
        self.OutOff()

    def SweepUp(self, start, end, step, tps):
        """
        Function of voltage sweep operation for BHVPS with Agilent E3460A
        Arguments:
        start : starting voltage. Default value is 0.00V
        end   : end voltage. Voltage unit must be specified in V.
        step  :
        tps   : time per step. The time is allowed to be in msec, e.g. 100 ms.

        Return:
        None
        """
        start_raw = start/1000
        end_raw = end/1000
        step_raw = self.VoltStep(step)
        volt_raw_now = start_raw

        self.Instruct('volt ' + str(start_raw))
        self.OutOn()
        while volt_raw_now <= end_raw:
            # print(str(volt_raw_now * 1000) + " V")
            # V_raw = float(self.Ask(self.addr, 'voltage?'))
            V_raw = self.AskVolt()
            print( str(V_raw*1000)+ " V")
            time.sleep(tps/1000.0)
            self.Instruct('voltage up')
            volt_raw_now += step_raw

    def SweepDown(self, start, end, step, tps):
        """
        Function of voltage sweep operation for BHVPS with Agilent E3460A
        Arguments:
        start : starting voltage. Default value is 0.00V
        end   : end voltage. Voltage unit must be specified in V.
        step  :
        tps   : time per step. The time is allowed to be in msec, e.g. 100 ms.

        Return:
        None
        """
        start_raw = start/1000
        end_raw = end/1000
        step_raw = self.VoltStep(step)
        volt_raw_now = start_raw

        V_raw = float(self.Query( 'voltage?'))
        # print( str(V_raw*1000)+ " V")

        self.Instruct('volt ' + str(start_raw))
        self.OutOn()
        # print( str(V_raw*1000)+ " V")
        while volt_raw_now > end_raw:
            # V_raw = float(self.Ask(self.addr, 'voltage?'))
            V_raw = self.AskVolt()

            if volt_raw_now >= step_raw + end_raw: # This prevents that next time volt_raw_now will be negative.
                time.sleep(tps/1000.0)
                self.Instruct('voltage down')
                volt_raw_now -= step_raw
                print(( str(V_raw*1000)+ " V"))
            else:
                time.sleep(tps/1000.0)
                # print( str(V_raw*1000)+ " V")
                self.Instruct('voltage ' + str(end_raw))
                volt_raw_now = end_raw
                time.sleep(tps/1000.0)
                # V_raw = float(self.Ask(self.addr, 'voltage?'))
                V_raw = self.AskVolt()
                # print( str(V_raw*1000)+ " V")
