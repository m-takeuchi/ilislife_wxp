#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import serial
import time
import re

#RS232_PORT = '/dev/ttyS0'
#UNIT_NUM = 1
BAUDRATE = 9600

class RS232():
# At first, get initialized
    def __init__(self, portname, unitnum=1):
        self._portname_ = portname
        self.raw = serial.Serial(self._portname_, BAUDRATE, timeout=0.05, rtscts=True)
        time.sleep(0.2)

    ### Basic I/O
    # Simply write buffer to RS232
    def _read(self):
        """read buffer to RS232 with CR delimiter
        """
        # return self.raw.write(buffer + '\r')
        return self.raw.readline()

    def _write(self, buffer):
        """Wite buffer to RS232 with CR delimiter
        """
        # return self.raw.write(buffer + '\r')
        return self.raw.write(bytes(buffer + '\r', encoding='utf-8'))

    # Write buffer to RS232 and recieve buffer
    def _ask(self, buffer):
        """Wite and read buffer to RS232 with uint number and CR delimiter
        """
        self._write(buffer)
        ans = self.raw.readline().decode('utf-8')
        return ans.replace("\r","",1) # delete the last delimiter character

    def okngbool(self, buffer):
        res = self._ask(buffer)
        if res == 'OK' or res == 'ON':
            return True
        elif res == 'NG' or res == 'OF':
            return False

    def intpParam(self, buffer):
        """ Interpretation buffer str as formatted number
        """
        res = self._ask(buffer)
        str_l = re.split('[Ee]', res)[0]
        str_r = re.split('[Ee]', res)[1]
        num_l = float(str_l)
        num_r = float(str_r)
        ans = num_l*10**num_r
        return ans

    def putParam(self, buffer, param, dig):
        """ Transration from float to GI-D7's format
        """
        s = "{0:.3e}".format(param)
        str_l_dig = len(re.split('[Ee]', s)[0])-1
        str_l = re.split('[Ee]', s)[0][:-(str_l_dig - dig)]
        str_r = re.split('[Ee]', s)[1]
        trans = str_l+'E'+str_r
        print(buffer+trans)
        return self._ask(buffer+trans)

    ## Basic commands for GI_D7
    def RE(self):
        """Go into remote control mode
        """
        return self.okngbool('RE')
    def LO(self):
        """Go into local control mode
        """
        return self.okngbool('LO')
    def E0(self):
        """Set emission current to 0.5 mA
        """
        return self.okngbool('E0')
    def E1(self):
        """Set emission current to 5.0 mA
        """
        return self.okngbool('E1')
    def EM(self):
        """Ask emission valid
        """
        return self.okngbool('EM')
    def ES(self):
        """Ask emission current settings
        """
        return self._ask('ES')
    def F0(self):
        """Turn filament off
        """
        return self.okngbool('F0')
    def F1(self):
        """Turn filament on
        """
        return self.okngbool('F1')
    def FA(self):
        """Select filament 1
        """
        return self.okngbool('FA')
    def FB(self):
        """Select filament 2
        """
        return self.okngbool('FB')
    def D0(self):
        """Turn degass off
        """
        return self.okngbool('D0')
    def D1(self):
        """Turn degass on
        """
        return self.okngbool('D1')
    def M0(self):
        """Set Xray off
        """
        return self.okngbool('M0')
    def M1(self):
        """Set Xray on
        """
        return self.okngbool('M1')
    def GS(self):
        """Ask current device connected to
        """
        return self._ask('GS')
    def SA(self):
        """Set sensitivity factor for N2
        """
        return self.okngbool('SA')
    def SB(self):
        """Set sensitivity factor for H2
        """
        return self.okngbool('SB')
    def SE(self, param):
        """Set sensitivity factor arbitrarily
        """
        return self.putParam('SE', param, 2)
    def R1(self):
        """Ask set point 1 data
        """
        return self.intpParam('R1')
    def R2(self):
        """Ask set point 2 data
        """
        return self.intpParam('R2')
    def S1(self, param):
        """Input set point 1
        """
        return self.putParam('S1', param, 3)
    def S2(self, param):
        """Input set point 2
        """
        return self.putParam('S2', param, 3)
    def SP(self):
        """Ask set point 1 and 2 data
        """
        return self._ask('SP')
    def RR(self):
        """Ask range hold data
        """
        res = '1'+self._ask('RR')
        return float(res)
    def RH(self, param):
        """Input range hold
        """
        return self.putParam('RH', param, -1)
    def RP(self):
        """Read measured pressure
        If under not mesurement, return float 0 value.
        """
        return self.intpParam('RP')
    def PR(self):
        """Ask Ext protect status
        """
        return self.okngbool('PR')
