# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 20:29:03 2021

@author: QCP32
"""
from PyQt5.QtCore import QThread
from queue import Queue
from configparser import ConfigParser

import sys, os, time

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)


class DDS_Controller(QThread):
    """
    A dummy/test class to give a guide for making a script.
    The controller class inherits QThread class and handles commands in a separated thread.
    This avoids being delayed by the main thread's tasks.
    
    The logger decorator automatically records the exception when a bug happens.
    """
    _num_boards = 2
    _serial_number = ""
    _current_settings = {}
    _client_list = []
    _status = "standby"
    
    def __init__(self, parent=None, config=None, logger=None, device="dds"):
        super().__init__()
        self.parent = parent
        self.cp = config
        self.logger = logger
        self.device = device
        self.queue = Queue()
        self._readDeviceConfig(device)
        
    @property
    def description(self):
        return "DDS"
        
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
        
    @logger_decorator
    def openDevice(self):
        self.dds.openDevice()
    
    @logger_decorator
    def closeDevice(self):
        self.dds.closeDevice()

    @logger_decorator    
    def toWorkList(self, cmd):            
        self.queue.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started of the device (%s)" % self.device)

    @logger_decorator          
    def run(self):
        while True:
            work = self.queue.get()
            self._status  = "running"
            # decompose the job
            work_type, command = work[:2]
            client = work[-1]    
            
            if work_type == "C":
                if command == "ON":
                    """
                    When a client is connected, opens the devcie and send voltage data to the client.
                    """
                    print("opening the device (%s)" % self.device)
                    if not self.dds._connected:
                        self.openDevice()
                        
                    if not client in self._client_list:
                        self._client_list.append(client)
                    client.toMessageList(["D", "DDS", "HELO", [True]])
                    data = self.getCurrentSettings()
                    message = ["D", "DDS", "STAT", data]
                    self.informClients(message, client)
                    
                elif command == "OFF":
                    """
                    When a client is disconnected, terminate the client and close the device if no client left.
                    """
                    if client in self._client_list:
                        self._client_list.remove(client)
                    # When there's no clients connected to the server. close the device.
                    if not len(self._client_list):
                        self.closeDevice()
                        self.toLog("info", "No client is being connected. closing the device.")
    
                elif command == "SETC": # Set current
                    board_num, channel_1, channel_2, current = work[2]
                    self.dds.setCurrent(board_num, channel_1, channel_2, current)
                    if channel_1:
                        self._current_settings[board_num]["current"][0] = current
                    if channel_2:
                        self._current_settings[board_num]["current"][1] = current
                    # Let all clients know that the currents are updated.
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                    
                elif command == "SETF": # Set frequency
                    board_num, channel_1, channel_2, freq_in_MHz = work[2]
                    self.dds.setFrequency(board_num, channel_1, channel_2, freq_in_MHz)
                    if channel_1:
                        self._current_settings[board_num]["freq_in_MHz"][0] = freq_in_MHz
                    if channel_2:
                        self._current_settings[board_num]["freq_in_MHz"][1] = freq_in_MHz
                    # Let all clients know that the frequencies are updated.
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                    
                elif command == "PWUP": # power up
                    board_num, channel_1, channel_2, = work[2]
                    self.dds.powerUp(board_num, channel_1, channel_2)
                    if channel_1:
                        self._current_settings[board_num]["power"][0] = 1
                        self._current_settings[board_num]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_num]["power"][1] = 1
                        self._current_settings[board_num]["current"][1] = 0
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                        
                elif command == "PWDN": # power down
                    board_num, channel_1, channel_2, = work[2]
                    self.dds.powerUp(board_num, channel_1, channel_2)
                    if channel_1:
                        self._current_settings[board_num]["power"][0] = 0
                        self._current_settings[board_num]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_num]["power"][1] = 0
                        self._current_settings[board_num]["current"][1] = 0
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                    

                
            elif work_type == "Q":
                if command == "STAT":
                    data = self.getCurrentSettings()
                    message = ["D", "DDS", "STAT", [data]]
                    self.informClients(message, client)
                        
            else:
                self.toLog("critical", "Unknown work type (\"%s\") has been detected." % work_type)
            self._status = "standby"
            
            
    @logger_decorator
    def getCurrentSettings(self):
        """
        This functions returnes current settings data as list.
        """
        print("getting")
        data = []
        for board_idx in self._current_settings.keys():
            data.append(["C", self._current_settings[board_idx]["current"],
                         "F", self._current_settings[board_idx]["freq_in_MHz"],
                         "P", self._current_settings[board_idx]["power"]])
        print("there", data)
        return data
                    
    @logger_decorator
    def informClients(self, msg, client):
        if not type(client) == list:
            client = [client]
        
        for client in client:
            client.toMessageList(msg)
        print(msg)
        
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


    def _readDeviceConfig(self, device):
        device_type = self.cp.get("device", device)
        
        if device_type == "Dummy":
            sys.path.append(dirname + "/Dummy_DDS")
            from Dummy import DummyDDS as DDS
        else:
            sys.path.append(dirname + "/DDS_w_VVA")
            from DDS_n_VVA import AD9912_w_VVA as DDS
            
        self._getSerialNumber_from_Config()
        
        self.dds = DDS(self._serial_number)
        
    def _getSerialNumber_from_Config(self):
        self._serial_number = self.cp.get('dds', 'serial_number')
        self._num_boards = int(self.cp.get('dds', 'num_boards'))
        
        for board_idx in range(self._num_boards):
            self._current_settings[board_idx+1] = {"current": [0, 0], "freq_in_MHz": [0, 0], "power": [0, 0]}
    
    
        
class DummyClient():
    
    def __init__(self):
        pass
    
    def toMessageList(self, msg):
        print(msg)
    