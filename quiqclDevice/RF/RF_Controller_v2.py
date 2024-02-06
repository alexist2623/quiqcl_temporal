# -*- coding: utf-8 -*-
"""
@author: Junho Jeong
@Tel: 010-9600-3392
@email1: jhjeong32@snu.ac.kr
@mail2: bugbear128@gmail.com
"""

import os
from PyQt5.QtCore import pyqtSignal, QTimer, QObject
import numpy as np
from queue import Queue
# from DummyRFdevice import *

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

from RFdevice import (SynthNV, SynthHD, SG384, APSYN420, Dummy_RF)


class RF_Controller(QObject):
    

    # Available rf device model list
    avail_device_list = {'synthnv':"SynthNV", 
                         'synthhd':"SynthHD", 
                         'sg384':"SG384", 
                         'apsyn420':"APSYN420",
                         "device_dummy": "Dummy_RF"}
    _config_options = ["curr_freq_hz",
                       "max_power"]
    _device_parameters = ["out",
                          "power",
                          "freq",
                          "phase",
                          "max_power"]  # This max power is a kind of a software interlock. The user cannot access to the max_power value
    _default_parameters = ["min_power",
                           "min_frequency",
                           "max_frequency",
                           "max_power"]
    
    _dev_signal = pyqtSignal(str, str, list)
    _timer_signal = pyqtSignal()
    
    def logger_decorator(func):
        """
        It writes logs when an exception happens.
        """
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as err:
                if not self.logger == None:
                    self.logger.error("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
                else:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return wrapper
    
    
    def __init__(self, parent=None, config=None, logger=None, device=None, device_type=None):
        super().__init__()
        self._client_list = []
        self._status = "standby"
        self.settings = {}
        
        self.parent = parent
        self.cp = config
        self.logger = logger
        self.device = device
        self.device_type = device_type
        self.isConnected = False
        self.isLocked = False
        self.voltage_step = 0.01 # vpp

        self.con = None
        self.rf = None
        self.queue = Queue()
        
        self._status = "off"
        self._generateDevice()

        self._readRFconfig()
        
        self.init_power = -50
        self.final_power = -50
        self.power_list_dict = {}
            
        self.power_timer = QTimer()
        self.power_timer.setSingleShot(True)
        self.power_timer.setInterval(250)
        self.power_timer.timeout.connect(self.setGradualPower)
        self.isUpdating = False
        
        self.openDevice()
        self.readHardSettings()
        
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, status):
        self._status = status
        
        # print(self._device_dict)
        # print("opened the device (%s)" % device)
        
    def startTimer(self):
        if not self.power_timer.isActive():
            self.power_timer.start()

    def __call__(self):
        return self._status
    
    def _generateDevice(self):
        if self.device_type == "synthnv":
            self.rf = SynthNV()
        elif self.device_type == "synthhd":
            self.rf = SynthHD()
        elif self.device_type == "sg384":
            self.rf = SG384()
        elif self.device_type == "apsyn420":
            self.rf = APSYN420()
        else:
            self.rf = Dummy_RF(device_type=self.device_type)

    @logger_decorator
    def _readRFconfig(self): 
        self._generateDevice()
        self.num_channels = self.rf._num_channels

        for channel_idx in range(self.num_channels):
            self.settings[channel_idx] = {key: None for key in self._device_parameters}
            self.settings[channel_idx]["out"] = False
        
        if "ip" in self.cp.options(self.device):
            ip = self.cp.get(self.device, "ip")
            self.con = self.rf.tcp_ip = ip
        elif "com" in self.cp.options(self.device):
            comport = self.cp.get(self.device, "com")
            self.con = self.rf.port = comport
        elif "serial_number" in self.cp.options(self.device):
            serial_number = self.cp.get(self.device, "serial_number")
            comport = self.rf._get_comport(serial_number) # This function returns the comport from the serial number.
            self.con = self.rf.port = comport
        else:
            raise ValueError ("A necessary information to connect to the device is missing!. Please provide any ip address or com port.")

            
        if "voltage_step" in self.cp.options(self.device):
            self.voltage_step = float(self.cp.get(self.device, "voltage_step"))
            print("voltage step of device (%s): %f" % (self.device, self.voltage_step))
            
        for param in self._default_parameters:
            for ch in range(len(self.settings)):
                self.settings[ch][param] = getattr(self.rf, param)
        
        for option in self._config_options:
            for cp_option in self.cp.options(self.device):
                if option in cp_option:
                    if cp_option[-4:-1] == "_ch":
                        for channel_index in range(self.num_channels):
                            self.settings[channel_index][option] = float(self.cp.get(self.device, option + "_ch%d" % (channel_index+1)))
                    else:
                        self.settings[0][option] = float(self.cp.get(self.device, cp_option))
                        
    @logger_decorator
    def openDevice(self):
        if not self.isConnected:
            con_flag = self.rf.connect()
            if con_flag == -1: # the connection failed. let the client know.
                print("Failed connecting to the device (%s)" % self.device)
                return -1
            else:
                self.isConnected = True
                print("Opened the device (%s)" % self.device)
    
            for channel in self.settings.keys():
                if "curr_freq_hz" in self.settings[channel].keys():
                    frequency = self.settings[channel]["curr_freq_hz"]
                    self.setFrequency(frequency, channel)
                                        
            self.readHardSettings()
        else:
            print("The device (%s) is aleady opened." % self.device)
                                

    @logger_decorator
    def closeDevice(self):
        for ch in range(self.num_channels):
            if self.settings[ch]["out"]:
                self.setPowerGradually(self.rf.min_power)
                self.setOutput(ch, False)
        self.rf.disconnect()
        self.isConnected = False
    
    
    @logger_decorator
    def readHardSettings(self, verbal=False):
        """
        This funtion quries parameters to the device.
        It updates the device dictionary.
        """
        for ch_idx in self.settings.keys():
            for parameter in self._device_parameters:
                if not parameter == "max_power":
                    try:    
                        self.settings[ch_idx][parameter] = self._getHardSetting(parameter, ch_idx)
                    except Exception:
                        raise ValueError ("The parameter (%s) is nt avalable for the device(%s, %s)." % (parameter, self._device_type, self.device))
           
        self.isLocked = self.checkIfLocked()
           
    @logger_decorator
    def setOutput(self, channel, out_flag):
        if out_flag:
            self.rf.enableOutput(channel)
        else:
            self.rf.disableOutput(channel)
        self.settings[channel]["out"] = out_flag
        
    @logger_decorator
    def setFrequency(self, frequency, channel):
        frequency = max( min(frequency, self.rf.max_frequency), self.rf.min_frequency )
            
        self.rf.setFrequency(frequency, channel)
        self.settings[channel]["freq"] = frequency
    
    @logger_decorator
    def setPhase(self, phase, channel):
        self.rf.setPhase(phase, channel)
        self.settings[channel]["phase"] = phase

    def dBm_to_vpp(self, dBm):
        volt = 2*np.sqrt((100)/1000)*10**(dBm/20)
        return volt
        
    def vpp_to_dBm(self, vpp):
        dBm = 20*np.log10(vpp/np.sqrt(8)/(0.001 * 50)**0.5)
        return dBm
    
    
    @logger_decorator
    def setPowerList(self, power, ch_idx=0):
        self.init_power = self.settings[ch_idx]["power"]
        if self.settings[ch_idx]["max_power"]: # if not the max_power is None
            max_power = self.settings[ch_idx]["max_power"]
        else:
            max_power = self.settings[ch_idx]["max_power"] = self.rf.max_power
            
        self.final_power = max( min(power, max_power), self.rf.min_power )
        
        init_vpp = self.dBm_to_vpp(self.init_power)
        final_vpp = self.dBm_to_vpp(self.final_power)
        
        power_list = np.arange(init_vpp, final_vpp, (-1)**(init_vpp > final_vpp)*self.voltage_step).tolist()
        power_list.append(final_vpp)
        
        self.power_list_dict[ch_idx] = self.vpp_to_dBm(power_list).tolist()

    @logger_decorator
    def setGradualPower(self):
        operation_list = []
        for channel in self.power_list_dict.keys():
            if len(self.power_list_dict[channel]):
                power = self.power_list_dict[channel].pop(0)
                self.setPower(power, channel)
                
                operation_list += [channel, power]
                
        self._dev_signal.emit(self.device, "p", operation_list)
        
        list_length = 0
        for power_list in self.power_list_dict.values():
            list_length += len(power_list)
            
        if list_length:
            self.power_timer.start()
        else:
            self._dev_signal.emit(self.device, 'gf', [])
            self.isUpdating = False

        
    @logger_decorator
    def setPower(self, power, ch_idx=0):
        if self.settings[ch_idx]["max_power"]:
            max_power = self.settings[ch_idx]["max_power"]
        else:
            max_power = self.rf.max_power
        power = max( min(power, max_power), self.rf.min_power )
        self.rf.setPower(power, ch_idx)
        self.settings[ch_idx]["power"] = power
        

    @logger_decorator
    def setToMinPower(self, channel=0):
        min_power = self.rf.min_power
        self.setPower(min_power, channel)
        
    def toLog(self, log_type, log_content):
        if not self.logger == None:
            if log_type == "debug":
                self.logger.debug(log_content)
            elif log_type == "info":
                self.logger.info(log_content)
            elif log_type == "warning":
                self.logger.warning(log_content)
            elif log_type == "error":
                self.logger.error(log_content)
            else:
                self.logger.critical(log_content)           
        else:
            print(log_type, log_content)
    

    @logger_decorator
    def _getHardSetting(self, parameter, ch_idx):
        if parameter == "out":
            return self.rf.is_output_enabled(ch_idx)
        elif parameter == "power":
            return self.rf.getPower(ch_idx)
        elif parameter == "freq":
            return self.rf.getFrequency(ch_idx)
        elif parameter == "phase":
            return self.rf.getPhase(ch_idx)
        elif parameter == "min_power":
            return self.rf.min_power
        elif parameter == "max_power":
            return self.rf.max_power
        elif parameter == "min_frequency":
            return self.rf.min_frequency
        elif parameter == "max_frequency":
            return self.rf.max_frequency
        else:
            return
            
    @logger_decorator
    def readSettings(self, parameter, ch_idx=0):
        """
        avail arameters: out, freq, power, phase, max_power 
        """
        if parameter in self._device_parameters:
            return self.settings[ch_idx][parameter]
        elif parameter in self._default_parameters:
            return self.settings[ch_idx][parameter]
        else:
            raise ValueError ("The parameter (%s) is not avalable for the device(%s, %s)." % (parameter, self.device_type, self.device))
        
    @logger_decorator
    def getCurrentSettings(self):
        """
        This functions returnes current settings data as list.
        """
        data = []
        for ch_idx in self.settings.keys():
            data.append(["o", self.readSettings("out", ch_idx),
                         "f", self.readSettings("freq", ch_idx),
                         "p", self.readSettings("power", ch_idx),
                         "ph", self.readSettings("phase", ch_idx),
                         "minp", self.readSettings("min_power", ch_idx),
                         "maxp", self.readSettings("max_power", ch_idx),
                         "minf", self.readSettings("min_frequency", ch_idx),
                         "maxf", self.readSettings("max_frequency", ch_idx)])
        return data
    
    def _getListFromDict(self, channel_list, parameter):
        if not type(channel_list) == list: # single parameter is acceptable
            channel_list = [channel_list]
        
        return_list = []
        for channel in channel_list:
            value =  self.settings[channel][parameter]
            temp_list = [channel, value]
            return_list += temp_list
        return return_list
    
    @logger_decorator
    def setFrequencyLock(self, lock_flag, lock_frequency=10e6):
        self.rf.lockFrequency(lock_flag, lock_frequency)
        self.isLocked = self.checkIfLocked()
        
    def checkIfLocked(self):
        return self.rf.is_locked()
    
    
            
class DummyClient():
    
    def __init__(self):
        pass
           
    def toMessageList(self, msg):
        print(msg)
        


if __name__ == "__main__":
    RF = RF_Controller(nickname="Dummy")
    RF.device_type = "dummy_rf"
    RF._generateDevice()
    
    client = DummyClient()
    
    RF.toWorkList(["C", "CON", [], client])
    RF.toWorkList(["C", "SETF", [0, 100], client])
    RF.toWorkList(["C", "ON", [0], client])
    RF.toWorkList(["C", "SETP", [0, 3], client])
    
    RF.toWorkList(["C", "OFF", [0], client])
