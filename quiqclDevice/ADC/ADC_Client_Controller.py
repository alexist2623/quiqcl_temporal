# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 18:38:33 2021

@author: User
"""

from PyQt5.QtCore import QThread
from queue import Queue
import os, sys

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

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
    return 

class ADC_ClientInterface(QThread):
    
    device_type = "ADC"
    _status = "standby"
    _is_opened = False
    _gui_opened = False
    channelNumber = 0
    
    def __init__(self, socket = None):
        
        self.sck = socket
        self.queue = Queue()
        self.gui = None
        self.voltData = {0:[], 1:[], 2:[], 3:[]}
      
    def openDevice(self):
        if self._is_opened:
            raise RuntimeError ("The device is alrady open!")
        else:
            self.toSocket(["C", "ADC", "ON", []])
                
    @requires_device_open
    def closeDevice(self):
        self.toSocket(["C", "ADC", "OFF", []])
        self._is_opened = False

    @requires_device_open
    def startMeasure(self, channelNumber):
        msg = ["Q", "VOLT_ON", [channelNumber]]
        self.toSocket(msg)
    
    @requires_device_open
    def stopMeasure(self, channelNumber):
        msg = ["Q", "VOLT_OFF", [channelNumber]]
        self.toSocket(msg)        
        
    @requires_device_open
    def switchChannel(self, channelNumber):
        self.channelNumber = channelNumber
        msg = ["Q", "SWITCH_CHANNEL", [self.channelNumber]]
        self.toSocket(msg)
        
    def closeGui(self):
        self._gui_opened = False
        self.closeDevice()

    def openGui(self):
        sys.path.append(dirname + '/../')
        from ADC_GUI_ex5 import Ui_MainWindow
        self.gui = Ui_MainWindow(self)
        self._gui_opened = True
        
    def toWorkList(self, cmd):         
        self.queue.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started")

    def run(self):
        while True:
            work = self.queue.get()
            self._status  = "running"
            #decompose the job
            work_type, command = work[:2]
            if work_type == "D":
                if command == "HELO":
                    """
                    Successfully received a response from the server
                    """
                    self.toGUI("Successfully connected to the server.")
                    self.gui.connect_button.setText("disconnect")
                    self._is_opened = True 
                
                elif command == "ON":
                    self.toGUI("Successfully opened ADC.")
                    
                elif command == "OFF":
                    self.toGUI("Successfully closed ADC.")
                    
                elif command == "SWIT":
                    channelNumber = work[2][0]
                    self.toGUI("Successfully swithced to channel %d." % channelNumber)
                    self.gui.switchChannel(channelNumber)
                    
                elif command == "VOLT":
                    channelNumber = work[2][0]
                    voltage = work[2][1]
                    self.voltData[channelNumber].append(voltage)
                    if len(self.voltData[channelNumber]) > 10:
                        self.voltData[channelNumber].pop(0)
                    self.gui._update_signal.emit(self.voltData[channelNumber])
                else:
                    pass
            self._status = "standby"

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
