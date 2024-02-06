# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 13:48:03 2022

@author: QCP32
@author: pi
"""
import time, os
from PyQt5.QtCore import QThread, QObject, QTimer, pyqtSignal
import platform
from queue import Queue

conf_dir = os.path.dirname(__file__) + '/Libs/'
conf_file = platform.node() + '.conf'

class OVEN_HandlerQT(QThread):
    
    _connection_flag = False
    _operation = False
    _channel = 1
    _target = 0
    _status = "standby"
    _voltage = 0
    _current = 0
    _force_off = False
    
    sig_oven_control = pyqtSignal()
    
    def __init__(self, parent=None, config=None, logger=None, device="DC_Power_Supply_E3631A"):
        super().__init__()
        self.parent = parent
        self.cp = config
        self.model_name = device
        
        self.DC = None
        self.file_name = ""
        self.class_name = ""
        
        self.logger = logger
        self.que = Queue()
        
    def __call__(self):
        return self.device
        
        
    @property
    def connection(self):
        return self._connection_flag
    
    @connection.setter
    def connection(self, flag):
        self._connection_flag = flag
        
    @property
    def operation(self):
        return self._operation
    
    @operation.setter
    def operation(self, flag):
        self._operation = flag
        
    @property
    def channel(self):
        return self._channel
    
    @channel.setter
    def channel(self, ch):
        self._channel = ch
        
    @property
    def target_value(self):
        return self._target
    
    @target_value.setter
    def target_value(self, target):
        self._target = target
        
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, stat):
        self._status = stat
        
    @property
    def voltage(self):
        return self._voltage
    
    @voltage.setter
    def voltage(self, value):
        self._voltage = value
        
    @property
    def current(self):
        return self._current
    
    @current.setter
    def current(self, value):
        self._current = value
        
    
    def setDeviceFile(self, file_name, class_name, model_name="DC_Power_Supply_E3631A"):
        self.file_name = file_name
        self.class_name = class_name
        self.model_name = model_name
        
    def run(self):
        while self.operation:
            oven_status = self._oven_run()
            if not oven_status:
                self.operation = False
                
            time.sleep(0.2)
            
        self.sig_oven_control.emit()
            
    def openDevice(self, port=None, stopbits=2, timeout=2):
        """
        It opens the device moudule following the user's file and class name.
        **I believe there's a better design than this. but I was in a hurry.
        """
        if not (self.file_name == "" or self.file_name == ""):
            if port == None:
                port = self._discover_device()
        
        exec("from %s import %s as DC" % (self.file_name, self.class_name))
        
        try:
            exec("self.DC = DC(port, stopbits, timeout)")
            self.DC.WriteDev('*IDN?')
            line = self.DC.ReadDev()
            if self.model_name in line:
                print("Connected to", line)
                self.connection = True
                return 1
            else:
                self.toLog("No/Wrong response from the device.", "error")
                self.DC.close()
                self.DC = None
                return 0
        except Exception as err:
            self.toLog("An error while connecting to the device (%s)." % err, "error")
            return 0
        
    def closeDevice(self):
        if self.connection:
            self.DC.close()
            self.DC = None
        else:
            self.toLog("The device is not yet opened!", "warning")
            
    def _force_off(self):
        print("Forcing off")
        self.status = "off"
        self.operation = True
        if not self.isRunning():
            self.start()
            
    def stopRightNow(self):
        """
        This function is for emergency.
        It downs currents of every cheannels to 0.
        """
        print("Emergency Stopping")
        self.operation = False
        self.status = "off"
        for key in self.DC.Channels.keys():
            self.DC.VoltageOn(key, 0)
            
        print("Done an emergency stop.")
        
    def _oven_run(self):
        time.sleep(0.2)
        self.voltage = self.DC.ReadValue_V(1)
        time.sleep(0.2)
        self.current = self.DC.ReadValue_I(1)
        if self.status == "on":
            if ( (self.target - self.current) > 0.15):
                self.DC.CurrentOn(self.channel, self.current + 0.15)
            else:
                self.DC.CurrentOn(self.channel, self.target)
            return 1
            
        else:
            if not self.current < 0.15:
                self.DC.CurrentOn(self.channel, self.current - 0.15)
                print(self.current)
                return -1
            else:
                self.DC.CurrentOn(self.channel, 0)
                self.current = 0
                return 0
     
    def _discover_device(self, ser_num="A602B73U"):    
        from serial.tools.list_ports import comports
        for dev in comports():
            if dev.serial_number == ser_num:
                return dev.device
        
    

    
if __name__ == '__main__':
    OH = OVEN_HandlerQT()
