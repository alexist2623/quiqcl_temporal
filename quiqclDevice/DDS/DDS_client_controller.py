# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 18:03:23 2021

@author: QCP32

v1.2: the callback is now emitted from the controller, not from the gui.

"""
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
from configparser import ConfigParser
import os, sys

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

class DDS_ClientInterface(QThread):
    
    device_type = "DDS"
    sweep_parameter_dict = {"BRD": [1, 2], "CH": [1, 2]}
    sig_update_callback = pyqtSignal()
    
    _status = "standby"
    _is_opened = False
    _num_boards = 2
    _gui_opened = False
    _current_settings = {1: {"current": [0, 0], "freq_in_MHz": [0, 0], "power": [0, 0]},
                         2: {"current": [0, 0], "freq_in_MHz": [0, 0], "power": [0, 0]}}
    _board_nickname = ["EA", "EC"]

    def __init__(self, socket=None):
        super().__init__()
        
        self.sck = socket
        self.gui = None
        self.que = Queue()
        
        self.config_file = ""
        
        
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
        
    def openGui(self):
        sys.path.append(dirname + '/../')
        from DDS_client_GUI import MainWindow
        self.gui = MainWindow(controller=self)
        self._gui_opened = True
        
    def openDevice(self):
        if self._is_opened:
            raise RuntimeError ("The device is alrady open!")
        else:
            self.toSocket(["C", "DDS", "ON", []])
        
    @requires_device_open
    def closeDevice(self):
        self.toSocket(["C", "DDS", "OFF", []])
        self._is_opened = False
        self.sig_update_callback.emit()
        
    @requires_device_open
    def powerUp(self, board, ch1, ch2):
        msg = ["C", "DDS", "PWUP", [board, ch1, ch2]]
        self.toSocket(msg)
        
    @requires_device_open
    def powerDown(self, board, ch1, ch2):
        msg = ["C", "DDS", "PWDN", [board, ch1, ch2]]
        self.toSocket(msg)
    
    @requires_device_open
    def setCurrent(self, board, ch1, ch2, current):
        msg = ["C", "DDS", "SETC", [board, ch1, ch2, current]]
        self.toSocket(msg)
        
    @requires_device_open
    def setFrequency(self, board, ch1, ch2, freq_in_MHz):
        msg = ["C", "DDS", "SETF", [board, ch1, ch2, freq_in_MHz]]
        self.toSocket(msg)

    def toWorkList(self, cmd):         
        self.que.put(cmd)
        if not self.isRunning():
            self.start()

    def run(self):
        while True:
            work = self.que.get()
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
                
                elif command == "STAT":
                    data_list = work[2]
                    for board_idx, data in enumerate(data_list):
                        while len(data):
                            param = data.pop(0)
                            if param == "C":
                                self._current_settings[board_idx+1]["current"] = data.pop(0)
                            elif param == "F":
                                self._current_settings[board_idx+1]["freq_in_MHz"] = data.pop(0)
                            elif param == "P":
                                self._current_settings[board_idx+1]["power"] = data.pop(0)
                                
                elif command == "SETC":
                    board_idx, channel_1, channel_2, current = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["current"][0] = current
                    if channel_2:
                        self._current_settings[board_idx]["current"][1] = current
                    self.toGUI("Current values of Board_%d board have been changed." % (board_idx))
                    
                elif command == "SETF":
                    board_idx, channel_1, channel_2, frequency_in_MHz = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["freq_in_MHz"][0] = frequency_in_MHz
                    if channel_2:
                        self._current_settings[board_idx]["freq_in_MHz"][1] = frequency_in_MHz
                    self.toGUI("Frequency values of Board_%d board have been changed." % (board_idx))
                    
                elif command == "PWUP":
                    board_idx, channel_1, channel_2 = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["power"][0] = 1
                        self._current_settings[board_idx]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_idx]["power"][1] = 1
                        self._current_settings[board_idx]["current"][1] = 0
                    self.toGUI("Board_%d has been powered up." % (board_idx))

                elif command == "PWDN":
                    board_idx, channel_1, channel_2 = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["power"][0] = 0
                        self._current_settings[board_idx]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_idx]["power"][1] = 0
                        self._current_settings[board_idx]["current"][1] = 0
                    self.toGUI("Board_%d has been powered off." % (board_idx))

            self.sig_update_callback.emit()
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
            
    def readConfig(self, config_file):
        self.cp = ConfigParser()
        if not os.path.isfile(config_file):
            raise FileNotFoundError ("Couldn't find the config file")
            return
        
        self.config_file = config_file
        print("found the config")
        self.cp.read(config_file)
        
        self._num_boards = int(self.cp.get("dds", "number_of_boards"))
        self._ip = self.cp.get("server", "ip")
        self._port = int(self.cp.get("server", "port"))
        
        for board_idx in range(self._num_boards):
            self._current_settings[board_idx+1] = {"current": [0, 0], "freq_in_MHz": [0, 0], "power": [0, 0]}
    