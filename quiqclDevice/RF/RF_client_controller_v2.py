# -*- coding: utf-8 -*-
"""
@author: Junho Jeong
@e-mail: jhjeong32@snu.ac.kr
@e-mail2: bugbear128@gmail.com
"""

from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
import os
# from RFsettings import Device_list
from RF_device_client import RF_Device_Client

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

def requires_device_open(func):
    """Decorator that checks if the device is open.

    The error message will be printed on the GUI.
    If the GUI is not opened, then it will be printed.
    """

    def wrapper(self, *args):
        if self.isOpened:
            return func(self, *args)
        else:
            self.toGUI("%s is called before the device is opened." % func.__name__ )
    return wrapper

class RF_ClientInterface(QThread):
    
    device_type = "RF"
    _gui_update_signal = pyqtSignal(str, str, list)

    def closeEvent(self, e):
        self._gui_opened = False
        self.closeDevice()
    
    def __init__(self, socket=None):
        super().__init__()
        
        self.sck = socket
        self.gui = None
        self.que = Queue()
        
        self.RF_dict = {}
        
        self.isOpened = False
        self._status = "standby"
        self._gui_opened = False


    def __call__(self):
        return self.RF_dict
        
    def openGui(self):
        from RF_client_GUI_v2 import RF_ControllerGUI
        self.gui = RF_ControllerGUI(self)
        self._gui_opened = True
        self._gui_update_signal.connect(self.gui.updateGUI)
        
    def buildRF_Device(self, dev_nick, data_list):
        num_channels = len(data_list)
        RF_dev = RF_Device_Client(self, dev_nick, num_channels)
        
        for channel, data in enumerate(data_list):
            for param, value in zip(data[::2], data[1::2]):
                RF_dev.setValue(param, value, channel)
                    
        self.RF_dict[dev_nick] = RF_dev

    
    # When RF Controller is made, it automatically send the server a command to read info about rf devices connected to server
    def connectRF(self):
        if not self.isOpened:
            self.toSocket(["C", "RF", "HELO", []])
            self.toSocket(["Q", "RF", "STAT", ["ALL"]])
            
    def disconnectRF(self):
        self.toSocket(["C", "RF", "DCN", []])
        self.isOpened = False
                    
    def openDevice(self, dev_nick=""):
        if dev_nick in self.RF_dict.keys():
            self.toSocket(["C", "RF", dev_nick, ["ON"]])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
        
    def closeDevice(self, dev_nick=""):
        if dev_nick in self.RF_dict.keys():
            self.toSocket(["C", "RF", dev_nick, ["OFF"]])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)

    @requires_device_open
    def setOutput(self, dev_nick, channel, flag):
        if dev_nick in self.RF_dict.keys():
            msg = ["SETO", channel, flag]
            self.toSocket(["C", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
    
    @requires_device_open
    def setPower(self, dev_nick, channel, power):
        if dev_nick in self.RF_dict.keys():
            msg = ["SETP", channel, power]
            self.toSocket(["C", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
                
    @requires_device_open
    def setFrequency(self, dev_nick, channel, frequency):
        if dev_nick in self.RF_dict.keys():
            msg = ["SETF", channel, frequency]
            self.toSocket(["C", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
    
    @requires_device_open
    def setPhase(self, dev_nick, channel, phase):
        if dev_nick in self.RF_dict.keys():
            msg = ["SETPH", channel, phase]
            self.toSocket(["C", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)

    @requires_device_open
    def setLock(self, dev_nick, flag, freq=10e6):
        if dev_nick in self.RF_dict.keys():
            msg = ["LOCK", flag, freq]
            self.toSocket(["C", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
            
    @requires_device_open
    def getPower(self, dev_nick, channels=0):
        if dev_nick in self.RF_dict.keys():
            if not type(channels) == list:
                channels = list(channels)
            msg = ["SETP"] + channels
            self.toSocket(["Q", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
            
    @requires_device_open
    def getFrequency(self, dev_nick, channels=0):
        if dev_nick in self.RF_dict.keys():
            if not type(channels) == list:
                channels = list(channels)
            msg = ["SETF"] + channels
            self.toSocket(["Q", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
    
    @requires_device_open
    def getPhase(self, dev_nick, channels=0):
        if dev_nick in self.RF_dict.keys():
            if not type(channels) == list:
                channels = list(channels)
            msg = ["SETPH"] + channels
            self.toSocket(["Q", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)

    @requires_device_open
    def getOutput(self, dev_nick, channels=0):
        if dev_nick in self.RF_dict.keys():
            if not type(channels) == list:
                channels = list(channels)
            msg = ["SETO"] + channels
            self.toSocket(["Q", "RF", dev_nick, msg])
        else:
            self.toGUI("The device (%s) is missing!" % dev_nick)
            
    @requires_device_open
    def getDeviceStatus(self, device_list):
        if not type(device_list) == list:
            device_list = [device_list]
        msg = ["Q", "RF", "STAT", device_list]
        self.toSocket(msg)
        
    def toWorkList(self, cmd):
        # cmd = ['D', Command, Result Data List with rf device name] 
        # cmd goes to run
        self.que.put(cmd)
        if not self.isRunning():
            self.start()

    def run(self):
        while self.que.qsize():
            # Received Message has a form
            # ['D', Command, Result Data List with rf device name]
            work = self.que.get()
            self._status  = "running"
            # decompose the job
            work_type, cmd = work[:2]
            data_list = work[2] # list of data
            
            if work_type == "D":
                
                if cmd == "HELO":
                    """
                    Successfully received a response from the server
                    Got data of Server Device List
                    """
                    self._status  = "HELO"
                    self.isOpened = True
                    self._gui_update_signal.emit("RF", "CON", [])

                    dev_nick_list = data_list[0::3]
                    dev_type_list = data_list[1::3]
                    dev_conn_list = data_list[2::3]
                    
                    for dev_nick, dev_type, dev_conn in zip(dev_nick_list, dev_type_list, dev_conn_list):
                        self.buildRF_Device(dev_nick, dev_type)
                        self.RF_dict[dev_nick].isConnected = dev_conn
                        
                    
                elif cmd in self.RF_dict.keys():
                    
                    sub_cmd = data_list[0]
                    sub_data = data_list[1:]
                    
                    self._status  = cmd + ":" + sub_cmd
                    
                    if sub_cmd == "STAT":
                        self.RF_dict[cmd].setupDevice(len(sub_data))
                        for ch, parameters in enumerate(sub_data):
                            for param, value in zip(parameters[::2], parameters[1::2]):
                                if value:
                                    self.RF_dict[cmd].setValue(param, value, ch)
                        self._gui_update_signal.emit(cmd, "STAT", [])
                        
                    elif sub_cmd == "ON":
                        self.RF_dict[cmd].setValue("c", True)
                        self._gui_update_signal.emit(cmd, "c", [True])
                        
                    elif sub_cmd == "OFF":
                        self.RF_dict[cmd].setValue("c", False)
                        self._gui_update_signal.emit(cmd, "c", [False])
                        
                    elif sub_cmd == "LOCK":
                        flag = sub_data[0]
                        self.RF_dict[cmd].setLocked(flag) # sub_data[0] is flag
                        self._gui_update_signal.emit(cmd, "l", [flag])
                        
                    elif sub_cmd[:3] == "MAX" or sub_cmd[:3] == "MIN":
                        for ch, val in zip(sub_data[::2], sub_data[1::2]):
                            self.RF_dict[cmd].setValue(sub_cmd.lower(), val, ch)
                        # self.RF_dict[cmd].setValue(param, val, ch) # value update
                        
                    elif sub_cmd[:3] == "SET":
                        param = sub_cmd[3].lower()
                        
                        if sub_data[0] == "g":
                            self._gui_update_signal.emit(cmd, "g", [sub_data[1]])
                        else:
                            for ch, val in zip(sub_data[::2], sub_data[1::2]):
                                self.RF_dict[cmd].setValue(param, val, ch) # value update
                            self._gui_update_signal.emit(cmd, param, sub_data[::2]) # gui update, sub_data[::2] indicates the channels


            elif work_type == "E":
                if data_list[0] == "CON":
                    print("A connection error with device (RF:%s)" % cmd)
                    self._gui_update_signal.emit(cmd, "e", ["con"])
                    
            self._status = "standby"
    
    def toSocket(self, msg):
        if not self.sck == None:
            self.sck.toMessageList(msg)
        else:
            print(msg)
            
    def toGUI(self, msg):
        if not self.gui == None:
            self.gui.toStatusBar(msg)
        else:
            print(msg)
            
      
if __name__ == "__main__":
    rf = RF_ClientInterface()