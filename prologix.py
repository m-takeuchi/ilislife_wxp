import serial, re
## from visa import instrument
from time import sleep
## import numpy as np
#import string

"""
--------------------------------------------------------------------
 Class to change the settings of the Prologix GPIB/USB Adapter vers. 6.0

 The commands implemented are not comprehensive.

 Note: Not all functions have been tested.

 My general convention (some based on Python convention...):

   .__function__()  built-in/reserved methods
   ._variable_      variables that are not callable...i.e. no '()' at end
   .InternalFunc()  initial capital letter indicates the function is called internally only
   .someCommand()   perform instrument commands/queries
   .MACRO_FUNC()    "macro" functions that do a whole bunch of things, like set up the instrument
   'SCRIPT: ...'     indicates the script is outputting information (as opposed to an instrument)

Revision History:
10 Aug 2010 (LNT)
 - Initial revision
 2013
 - Modified by me (M. Takeuchi)

USAGE EXAMPLE
        import prologix
        proctrl = prologix.GPIBUSB(4,12)
        #...
        print proctrl.ask('*idn?')
--------------------------------------------------------------------
"""

class GPIBUSB(object):
###########################################################################
## Initialization
###########################################################################
    def __init__(self, portNum, reset=False):
#                self._serPort_ = portNum-1
# Changed above line into this
            self._serPort_ = portNum

            ## Port setup
            self.raw = serial.Serial(self._serPort_,9600,timeout=1,rtscts=True) #open the serial on COM n+1
            if reset:
                self.resetPro() # Reset prologix
            else:
                pass

            self.setProController()         # set up as a controller
            self.read()

    def openport(self):
            self.raw=serial.Serial(self._serPort_,9600,timeout=1) #open the serial on COM n+1

    def closeport(self):
            self.raw.close()

###########################################################################
## Basic I/O
###########################################################################
    def write(self,buffer):
        # return self.raw.write(buffer + '\n')
        self.raw.write(bytes(buffer + '\r\n', 'utf-8'))

    def read(self):
            ans = self.raw.readline()
            return ans

    def ask(self,buffer):
            self.write(buffer)
            return self.read()

###########################################################################
## Usefull I/O
###########################################################################

    def Test(self, addr):
        self.setProAddr(addr)
        return self.ProAsk("*IDN?")

    def Read(self, addr):
        self.setProAddr(addr)
        return self.read()

    def Write(self, addr, buffer):
        self.setProAddr(addr)
        self.write(buffer)

    def Ask(self, addr, buffer):
        self.setProAddr(addr)
        ans = self.ask(buffer).decode('utf-8')
        return ans.replace("\r","",1)
#=========================================================

    def Initialize(self, addr):
        """
        Initialize device
        """
        # res = self.Ask(addr, '*IDN?')
        # self.raw.write('*CLS') #Device clear
        return self.Ask(addr, '*CLS')


    def CheckDevice(self, addr):
        self.setProAddr(addr)
        if self.raw.isOpen() == True:
            ans = "Port check OK\r\n"
            pass
        else:
            ans = "No device port\r\n"
        return ans

    def ClosePort(self):
        """
        Close dev file / com port
        """
        self.raw.close()



###########################################################################
## Settings (Pro is short for Prologix Unit)
###########################################################################
    def resetPro(self):
            print('Reset Prologix.')
            self.write('++rst')
            sleep(5)

    def setProCIC(self):
            #assert GPIB IFC signal for 150 microseconds making Prologix GPIB- USB controller the Controller-In-Charge on the GPIB bus.
            self.write('++ifc')

    def ProAutoAsk(self,buffer):
            self.setProAuto()
            return self.ask(buffer)

    def ProAsk(self,buffer,eoi='\n'):
            self.clrProAuto()
            self.write(buffer)
            self.write('++read ' + eoi)
            return self.read()

    def setProAddr(self,newaddress):
            self.write('++addr'+str(newaddress))
            # return self.ask('++addr')

    # Set the Prologix unit as a bus controller (master)
    def setProController(self):
            self.write('++mode 1')
            mode = int(self.ask('++mode'))
            if mode == 1:
                    print('Prologix is now controller mode.')
            else:
                    print('SCRIPT: mode changing failed')
                    mode = 0
            return mode

    # Set the Prologix unit as a bus device (slave)
    def setProDevice(self):
            self.write('++mode 0')
            mode = int(self.ask('++mode'))
            if mode == 0:
                    print('Prologix is now device mode.')
            else:
                    print('SCRIPT: mode changing failed')
                    mode = 1
            return mode

    # Automatically set to read after writing
    def setProAuto(self):
            # self.raw.write('++auto 1\n')
            self.write('++auto 1')

    def clrProAuto(self):
            # self.raw.write('++auto 0\n')
            self.write('++auto 0')

    def getProAddr(self):
            addr = self.ask('++addr')
            return addr
