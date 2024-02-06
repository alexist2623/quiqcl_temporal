# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 18:03:23 2021

@author: QCP32
"""
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue

def requires_device_open(func):
    """Decorator that checks if the device is open.

    Raises:
        RuntimeError - the func is called before the device is open.
    """

    def wrapper(self, *args):
        if self._is_opened:
            return func(self, *args)
        else:
            raise RuntimeError('{} is called before the device is opened.'
                               .format(func.__name__))
    return wrapper
    

class DAC_ClientInterface(QThread):
    
    device_type = "DAC"
    sig_update_callback = pyqtSignal()

    _status = "standby"
    _is_opened = False
    _voltage_list = []
    _num_channel = 16

        
    def __init__(self, socket=None, gui=None):
        self.sck = socket
        self.gui = gui
        self.que = Queue()
        
    def openDevice(self):
        if self._is_opened:
            raise RuntimeError ("The device is alrady open!")
        else:
            self.toSocket(["C", "DAC", "ON", []])
        
    @requires_device_open
    def closeDevice(self):
        self.toSocket(["C", "DAC", "OFF", []])
        self._is_opened = False
        self.sig_update_callback.emit()
        
    @requires_device_open
    def resetDevice(self):
        msg = ["C", "DAC", "RST", []]
        self.toSocket(msg)
    
    @requires_device_open
    def setVoltage(self, channel, voltage):
        if not type(channel) == list:
            channel = [channel]
        if not type(voltage) == list:
            voltage = [voltage]
        
        if not len(channel) == len(voltage):
            raise ValueError ("The number of channels and the number of voltages are different!")
            return
        
        msg = []
        for idx in range(len(channel)):
            msg.append(channel[idx])
            msg.append(voltage[idx])
            
        self.toSocket(["C", "DAC", "SETV", msg])

    @requires_device_open
    def readVoltage(self, channel):
        if channel >= self._num_channel:
            raise ValueError ("The number of channel that can be contrlled is (%d)" % self._num_channel)
        self.toSocket(["Q", "DAC", "SETV", channel])
        
    @requires_device_open
    def updateVoltages(self, data):
        channel_list = data[0::2]
        voltage_list = data[1::2]
        
        for idx, channel in enumerate(channel_list):
            self._voltage_list[channel] = voltage_list(idx)
            
            
    def toWorkList(self, cmd):         
        self.queue.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started")

    def run(self):
        while True:
            work = self.queue.get()
            self._status  = "running"
            # decompose the job
            work_type, command = work[:2]
    
            if work_type == "D":
                if command == "HELO":
                    """
                    Successfully received a response from the server
                    """
                    self.toGUI("Successfully connected to the server.")
                    self._is_opened = True
                
                elif command == "SETV":
                    data = work[2]
                    self.updateVoltages(data)
                    
                elif command == "RST":
                    channel_list = range(self._num_channel)
                    voltage_list = [0]*self._num_channel
                    
                    data = [0]*2*self._num_channel
                    data[0::2] = channel_list
                    data[1::2] = voltage_list
                    
                    self.updateVoltages(data)
            
            self.sig_update_callback.emit()
                    
    
    def toSocket(self, msg):
        if not self.sck == None:
            self.sck.toMessageList(msg)
        else:
            print(msg)
            
    def toGUI(self, msg):
        if not self.gui == None:
            self.gui.toStatus(msg)
        else:
            print(msg)