from prologix import *
import re,time



class dmm3239gpib(GPIBUSB):
# At first, get initialized
    def __init__(self, portNum, addr):
        GPIBUSB.__init__(self, portNum)
        self.setProAuto() #Set prologix to auto mode
        self.addr = addr

    def Scan(self):
        return self.Read(self.addr)

    def Instruct(self, buffer):
        self.clrProAuto()
        self.Write(self.addr, buffer)

    def Query(self, buffer):
        return self.ProAutoAsk(self.addr, buffer)

    def Rst(self):
        """Reset
        """
        self.Instruct('*RST')

    def Cls(self):
        """Clear register
        """
        self.Instruct('*CLS')

    def ClearBuffer(self):
        """Force to clear buffer
        """
        return self.Query(':read?')

    def DataHeader(self, onoff='off'):
        if onoff == 'on':
            bit = '1'
        elif onoff == 'off':
            bit = '0'
        else:
            bit = '0'
        # self.Write(self.addr, ':system:header '+bit)
        self.Instruct(':system:header '+bit)

    def Mode(self,prop='voltage',acdc='dc',range=''):
        # meas=self.Write(self.addr, 'measure:' + prop + ':' + acdc + '? ' + str(range))
        meas=self.Instruct('measure:' + prop + ':' + acdc + '? ' + str(range))
        # return meas

    def Measure(self):
        # d = self.Query(':read?')
        d = self.Query(':MEAS:VOLT?')
        # d = self.ProAsk(self.addr, ':read?')
        return float(d)

        # print(self.Query(':MEAS:VOLT?'))
        # return float(self.Query(':MEAS:VOLT?'))
        # data_str = self.Query(':read?')
        # if data_str[:1] == '--':
            # data_str.replace('--','-')
        # print(data_str)
        # return float(data_str.rstrip('\n'))
    def TrigInt(self, trig=True):
        if trig == False:
            source = 'EXTERNAL'
        elif trig == True:
            source = 'IMMEDIATE'
        else:
            source = 'IMMEDIATE'
        self.Instruct(':TRIG:SOUR ' +source)

    def Fetch(self):
        d = self.Query('FETCH?')
        return float(d)

    def ContTrig(self):
        self.Instruct(':INIT:CONT 1') ## 1: On, 0:OFF

    def SingleTrig(self):
        self.Instruct(':INIT:CONT 0') ## 1: On, 0:OFF


    def SampleRate(self, rate='fast'):
        if rate == 'fast' or rate == 'medium' or rate == 'slow':
            # self.Write(self.addr, ':sample:rate ' + rate)
            self.Instruct(':sample:rate ' + rate)
            print("Sampling rate changed to \"%s\"." %(rate))
        else:
            # self.Write(self.addr, ':sample:rate ' + 'slow')
            self.Instruct(':sample:rate ' + 'slow')
            print("\"%s\" is wrong representation. Use fast or medium or slow." %(rate))
