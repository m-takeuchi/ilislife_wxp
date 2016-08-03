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
        self.Write(self.addr, buffer)

    def Query(self, buffer):
        return self.Ask(self.addr, buffer)

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
        d = self.Query(':read?')
        return float(d)
        # print(self.Query(':MEAS:VOLT?'))
        # return float(self.Query(':MEAS:VOLT?'))
        # data_str = self.Query(':read?')
        # if data_str[:1] == '--':
            # data_str.replace('--','-')
        # print(data_str)
        # return float(data_str.rstrip('\n'))

    def SampleRate(self, rate='fast'):
        if rate == 'fast' or rate == 'medium' or rate == 'slow':
            # self.Write(self.addr, ':sample:rate ' + rate)
            self.Instruct(':sample:rate ' + rate)
            print("Sampling rate changed to \"%s\"." %(rate))
        else:
            # self.Write(self.addr, ':sample:rate ' + 'slow')
            self.Instruct(':sample:rate ' + 'slow')
            print("\"%s\" is wrong representation. Use fast or medium or slow." %(rate))
