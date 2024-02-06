from fiberSW_v1_0 import fiberSW
import numpy as np
import time
import ctypes

from configparser import ConfigParser
from DummyLaser import DummyLaser

class connector:
    def __init__(self, wm, dac, sw):
        self.wm = wm
        self.dac = dac
        self.sw = sw
        
class wavemeter:
    # Instantiating Constants for 'RFC' parameter
    cInstCheckForWLM = -1;
    cInstResetCalc = 0;
    cInstReturnMode = cInstResetCalc;
    cInstNotification = 1;
    cInstCopyPattern = 2;
    cInstCopyAnalysis = cInstCopyPattern;
    cInstControlWLM = 3;
    cInstControlDelay = 4;
    cInstControlPriority = 5;
    
    # Operation
    cCtrlStopAll = 0
    cCtrlStartAdjustment = 1
    cCtrlStartMeasurement = 2
    
    # Amplitude Constants
    cMin1 = 0;
    cMin2 = 1;
    cMax1 = 2;
    cMax2 = 3;
    cAvg1 = 4;
    cAvg2 = 5;
    
    # Notification Constants for 'Mode' parameter
    cNotifyInstallCallback = 0;
    cNotifyRemoveCallback = 1;
    cNotifyInstallWaitEvent = 2;
    cNotifyRemoveWaitEvent = 3;
    cNotifyInstallCallbackEx = 4;
    cNotifyInstallWaitEventEx = 5;

    # Return errorvalues of GetFrequency, GetWavelength and GetWLMVersion
    ErrNoValue = 0;
    ErrNoSignal = -1.0;
    ErrBadSignal = -2.0;
    ErrLowSignal = -3.0;
    ErrBigSignal = -4.0;
    ErrWlmMissing = -5.0;
    ErrNotAvailable = -6.0;
    InfNothingChanged = -7.0;
    ErrNoPulse = -8.0;
    ErrDiv0 = -13.0;
    ErrOutOfRange = -14.0;
    ErrUnitNotAvailable = -15.0;
    ErrMaxErr = ErrUnitNotAvailable;

    # cmi Mode Constants for Callback-Export and WaitForWLMEvent-function
    cmiResultMode = 1;
    cmiRange = 2;
    cmiPulse = 3;
    cmiPulseMode = cmiPulse;
    cmiWideLine = 4;
    cmiWideMode = cmiWideLine;
    cmiFast = 5;
    cmiFastMode = cmiFast;
    cmiExposureMode = 6;
    cmiExposureValue1 = 7;
    cmiExposureValue2 = 8;
    cmiDelay = 9;
    cmiShift = 10;
    cmiShift2 = 11;
    cmiReduce = 12;
    cmiReduced = cmiReduce;
    cmiScale = 13;
    cmiTemperature = 14;
    cmiLink = 15;
    cmiOperation = 16;
    cmiDisplayMode = 17;
    cmiPattern1a = 18;
    cmiPattern1b = 19;
    cmiPattern2a = 20;
    cmiPattern2b = 21;
    cmiMin1 = 22;
    cmiMax1 = 23;
    cmiMin2 = 24;
    cmiMax2 = 25;
    cmiNowTick = 26;
    cmiCallback = 27;
    cmiFrequency1 = 28;
    cmiFrequency2 = 29;
    cmiDLLDetach = 30;
    cmiVersion = 31;
    cmiAnalysisMode = 32;
    cmiDeviationMode = 33;
    cmiDeviationReference = 34;
    cmiDeviationSensitivity = 35;
    cmiAppearance = 36;
    cmiAutoCalMode = 37;
    cmiWavelength1 = 42;
    cPatternDisable = 0;
    cPatternEnable = 1;
    cAnalysisDisable = cPatternDisable;
    cAnalysisEnable = cPatternEnable;
    cSignal1Interferometers = 0;
    cSignal1WideInterferometer = 1;
    cSignal1Grating = 1;
    cSignal2Interferometers = 2;
    cSignal2WideInterferometer = 3;
    cSignalAnalysis = 4;
    cSignalAnalysisX = cSignalAnalysis;
    cSignalAnalysisY = cSignalAnalysis + 1;
    cExposureMax = 2000
    cExposureMin = 1

    def __init__(self):
        parser = ConfigParser()
        parser.read('DummyLaser Config.ini')
        self.laserNum = parser.getint('laser', 'laser_number')
        self.fiberSWCh = [] 
        self.DACchannel = {}
        self.laser = {}
        self.isON = {}
        #self.pidON = {}
        self.exposureTime = {}
        self.amplitude = {}
        self.frequency = {}
        for i in range(self.laserNum):
            sectionName = "laser" + str(i+1)
            fb = parser.getint(sectionName, "fiber_switch")
            laserName = parser.get(sectionName, "name")
            initFreq = parser.getfloat(sectionName, "initial_frequency")
            self.fiberSWCh.append(fb)
            self.DACchannel[fb] = parser.getint(sectionName, "DAC_channel")
            self.laser[fb] = DummyLaser(laserName, initFreq)
            self.isON[fb] = False
            self.exposureTime[fb] = 0.0
            self.amplitude[fb] = 0.0
            self.frequency[fb] = 0.0
        self.currentSWCh = self.fiberSWCh[0]
        self.switchDelay = 100
        """
        for i in range(self.laserNum):
            swtch = self.fiberSWCh[i]
            print("fiber switch :", swtch)
            print("DAC channel :", self.DACchannel[swtch])
            print("laser info :", self.laser[swtch].laser_name)
            print("-------------------------------------------")
        """
        self.initConfig()

    def Instantiate(self, RFC = -1, Mode = 0, P1 = 0, P2 = 0):
        if(RFC != self.cInstCheckForWLM):
            print("This mode is not supported for dummy wavemeter")
            print("Should be Instantiate(-1, 0, 0, 0)")
    
    def Operation(self, op):
        ### starts the usual measurement mode
        if op == self.cCtrlStartMeasurement:
            # do sth
            pass

        ### stops all measurement activities as well as adjustment,
        ### recording, and replaying
        elif op == self.cCtrlStopAll:
            # do sth
            pass

        else:
            print("Operation code", str(op), "is not supported for dummy wavemeter")

    def Calibration(self, type, unit, value, channel):
        print("calibration called with [type] ", str(type), " / [unit] ", str(unit), " / [value] ", str(value), " / [channel] ", str(channel))

    def SetSwitcherChannel(self, fiberSWCh):
        if fiberSWCh not in self.fiberSWCh:
            print("No such switch")
            return
        self.currentSWCh = fiberSWCh

    ### Set the interferometers exposure values of a specific signal
    def SetExposureNum(self, fiberSWCh, arr, exposure):
        # arr = 1 in 1376 in multiple_window.py
        self.exposureTime[fiberSWCh] = exposure

    def GetFrequencyNum(self, fiberSWCh, F=0):
        return self.laser[fiberSWCh].getFrequency()

    ### Returns the extremum points of the interferometer pattern,
    ### the absolute minium and maximum as well as the fringes average amplitudes
    def GetAmplitudeNum(self, fiberSWCh, index, amplitude):
        # return min1 max1 min2 max2 depending on index
        # but not currently used in multiple_windows.py
        return 10

    def initConfig(self):
        pass


class dummyDAC:
    def __init__(self, com_port, wm):
        self.wm = wm
        # wm.fiberSWCh is list and wm.DACchannel is {fiberswitch : DACchannel} dict
        # make self.fiberSWCh with {DACchannel : fiberswitch}
        self.DACchannel = wm.DACchannel.values()
        self.fiberSWCh = {}
        for k, v in wm.DACchannel.items():
            self.fiberSWCh[v] = k
        #for k, v in self.fiberSWCh.items():
        #    print(k, v)
        #    print("---------------")
        
    def close(self):
        print("DAC close called")

    def voltage_register_update(self, dac_number, ch, voltage, bipolar=False, v_ref=2.5):
        if voltage > 2.5: 
            raise ValueError('Error in voltage_out: voltage is out of range')
        elif voltage < 0.0:
            raise ValueError('Error in voltage_out: voltage is out of range')

        # print("voltage update :", str(self.fiberSWCh[ch]), "with voltage", str(voltage))
        self.wm.laser[self.fiberSWCh[ch]].set_by_DAC_voltage(voltage)
    
    def load_dac(self):
        pass

class dumbFiberSW:
    def __init__(self, com, controller):
        self.controller = controller
        self.writebuffer = bytearray()
        self.com = com
        self.ch = -1
        
    def switchChannel(self, ch):
        chString = 'ch%1d\r\n' % ch
        self.frontport = ch
        self.write(chString.encode())
        self.controller.connector.wm.setChannel(ch)
        #self.com.write(chString.encode())
       # print chString
       
    def write(self, www):
        self.writebuffer = www
        
    def read(self):
        return self.writebuffer

def main():
    wm = wavemeter()

if __name__ == "__main__":
    main()