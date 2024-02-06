# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 13:48:03 2022

@author: QCP32
@author: pi
"""
import os, time
from PyQt5.QtCore import QThread, pyqtSignal
import platform
if platform.system() == "Windows":
    from termcolor import colored
    print(colored("You are running this script on 'Winows'. \nThe GPIO pins are autumatically set to simulated dummies.", 'magenta'))
    from GPIO_Libs.WindowsGPIO import GPIO_Dummy
    G = GPIO_Dummy()
else:
    import RPi.GPIO as G
from queue import Queue

conf_dir = os.path.dirname(__file__) + '/Libs/'
conf_file = platform.node() + '.conf'

class GPIO_Controller(QThread):
    
    _pin_assignment = {"IN": {}, "OUT": {}}
    _pin_value = {"IN": {}, "OUT": {}}
    _mode = "BCM"
    _sig_GPIO_updated = pyqtSignal()
    _connection = False
    
    def __init__(self, parent=None, config=None, logger=None, device="GPIO"):
        super().__init__()
        self.parent = parent
        self.cp = config
        self.logger = logger
        self.device = device

        self._G = G
        self._G.setwarnings(False)
        self.queue = Queue()
        self._client_list = []
        
        self.conf_dir = conf_dir
        self.conf_file = conf_file
        
        self._checkIfConfigExist()
        self.isOpened = self._connection
        
        
    def __call__(self):
        return self._pin_assignment, self._pin_out
    
    def _checkIfConfigExist(self):
        if self.cp == None:
            try:
                self.readConfig(self.conf_dir, self.conf_file)
                self.toLog("error", "No inherited config file. Loaded the local config.")
                
                for key in self.pin_assignment["IN"].keys():
                    self.setPinIn(key)
                for key in self.pin_assignment["OUT"].keys():
                    self.setPinOut(key, 0)
                
            except Exception as err:
                self.toLog("error", "No config file has been found (%s)." % err)
    
    def logger_decorator(func):
        """
        It writes logs when an exception happens.
        """
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except Exception as err:
                if not self.logger == None:
                    self.logger.error("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
                else:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return wrapper
    
    
    @logger_decorator
    def openDevice(self, initial_dict=None):
        if not initial_dict == None:
            for in_n_out in ["IN", "OUT"]:
                config_dict = initial_dict[in_n_out]
                
                for pin_num, pin_nick in config_dict.items():
                    self._pin_assignment[in_n_out][pin_num] = pin_nick
            
        self.isOpened = True
        
    @logger_decorator
    def closeDevice(self):
        if self.connection:
            self._G.cleanup()
        self.isOpened = False
            
            
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
                    if not self.isOpened:
                        self.openDevice()
                        
                    if not client in self._client_list:
                        self._client_list.append(client)
                    
                    data = self._pinDictToList(self._pin_value)
                    
                    message = ["D", "GPIO", "STAT", data]
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
    
                elif command == "SETI": # Set input
                    pin_num = work[2][0]
                    try:
                        self.setPinIn(pin_num)
                        self.informClients(["D", "GPIO", command, work[2]], self._client_list)
                    except Exception as err:
                        self.informClinets(["E", "GPIO", command, work[2]], client)
                        self.toLog("error", "An error (%s) of the command (%s) from the client(%s)" % (err, command, client._address))
                        return
                    
                    if len(work[2]) > 1:
                        nickname = work[2][1]
                        self.assignPinNick("IN", pin_num, nickname)
                        
                elif command == "SETO": # Set output
                    pin_num, pin_value = work[2][:2]
                    try:
                        self.setPinOut(pin_num, pin_value)
                        self.informClients(["D", "GPIO", command, work[2]], self._client_list)
                    except Exception as err:
                        self.informClinets(["E", "GPIO", command, work[2]], client)
                        self.toLog("error", "An error (%s) of the command (%s) from the client(%s)" % (err, command, client._address))
                        return
                        
                    if len(work[2]) > 2:
                        nickname = work[2][-1]
                        self.assignPinNick("OUT", pin_num, nickname)
                        
                elif command == "SETN": # Set nickname of the pin
                    pin_type, pin_num, pin_nick = work[2]
                    self.assignPinNick(pin_type, pin_num, pin_nick)
                    self.informClients(["D", "GPIO", command, work[2]], self._client_list)
                    
                    
                elif command == "UPTC": # update config
                    section, option, value = work[2]
                    self.updateConfig(section, option, value)
                    self.saveConfig()
                    self.toLog("info", "The config file has been updated by (%s)" % client._address)
                    
                    self.informClients(["D", "GPIO", command, work[2]], self._client_list)
                    
                else:
                    self.toLog("critical", "Unknown command (\"%s\") has been detected." % command)
                
                
            elif work_type == "Q":
                if command == "STAT":
                    data = self._pinDictToList(self._pin_value)
                    message = ["A", "GPIO", "STAT", data]
                    self.informClients(message, client)
                    
                elif command == "SETI":
                    if not len(work[2]): # all pin values
                        data = list(self._pin_value["IN"].itmes())
                    else:
                        data = []
                        for pin_num in work[2]:
                            data.append(self._pin_value["IN"][pin_num])
                        
                    self.informClients(["A", "GPIO", "SETI", data], client)
                    
                elif command == "SETO":
                    if not len(work[2]): # all pin values
                        data = list(self._pin_value["OUT"].itmes())
                    else:
                        data = []
                        for pin_num in work[2]:
                            data.append(self._pin_value["OUT"][pin_num])
                        
                    self.informClients(["A", "GPIO", "SETO", data], client)
                    
                elif command == "SETN":
                    if not len(work[2]): # all pin values
                        data = self._pinDictToList(self._pin_assignment)
                    else:
                        data = []
                        
                        for pin_type in ["IN", "OUT"]:
                            data.append(pin_type)
                            for pin_num in work[2]:
                                for key, val in self._pin_assignment[pin_type].items():
                                    if key == pin_num:
                                        data.append(val)
                                    if val == pin_num:
                                        data.append(key)
                            
                    self.informClients(["A", "GPIO", "SETN", data], client)
                    
                else:
                    self.toLog("critical", "Unknown command (\"%s\") has been detected." % command)
                        
            else:
                self.toLog("critical", "Unknown work type (\"%s\") has been detected." % work_type)
            self._status = "standby"
            
    @logger_decorator
    def readPinValue(self, pin_num):
        pin_value = self._G.input(pin_num)
        self._pin_value["IN"][pin_num] = pin_value
        
        return pin_value
        
    @logger_decorator
    def assignPinNick(self, pin_type, pin_num, pin_nick):
        if not pin_num in self._pin_assignment[pin_type].keys():
            self.toLog('warning', "The pin (%d) has never been set." % (pin_num))
        self._pin_assignment[pin_type][pin_num] = pin_nick
        
    @logger_decorator
    def setPinIn(self, pin_num):
        self._G.setup(pin_num, self._G.IN)
        if not pin_num in self._pin_assignment["IN"].keys():
            self._pin_assignment["IN"][pin_num] = "temporary"
            self.toLog('warning', "The input pin(%d) is set to temporary." % (pin_num))
        self._pin_value["IN"][pin_num] = 0
                
    @logger_decorator
    def setPinOut(self, pin_num, value):
        self._G.setup(pin_num, self._G.OUT)
        if not pin_num in self._pin_assignment["OUT"].keys():
            self._pin_assignment["OUT"][pin_num] = "temporary"
            self.toLog('warning', "The output pin(%d) is set to temporary." % (pin_num))
        self._pin_value["OUT"][pin_num] = value
        self._sig_GPIO_updated.emit(pin_num)
                      
    @logger_decorator
    def pullUpPin(self, pin_num, up_flag, verbose=True):
        if up_flag:
            self._G.setup(pin_num, self._G.IN, pull_up_down=self._G.PUD_UP)
        else:
            self._G.setup(pin_num, self._G.IN, pull_up_down=self._G.PUD_DOWN)
            
        if verbose:
            print("The pin(%d) is forced to be %s." % (pin_num, "up" if up_flag else "down"))
            
    
    @property
    def mode(self):  
        return self._mode
    
    @mode.setter
    def mode(self, g_mode):
        if not (g_mode == "BCM" or g_mode == "BOARD"):
            raise ValueError("The pin mode should be either 'BCM' or 'BOARD'.")
            return
        if self.g_mode == "BCM":
            self._G.setmode(self._G.BCM)
        else:
            self._G.setmode(self._G.BOARD)
            
        self._mode = g_mode
        
    @property
    def pin_assignment(self):
        return self._pin_assignment
    
    @property
    def pin_value(self):
        return self._pin_value
        
    @property
    def isOpened(self):
        return self._connection_flag
    
    @isOpened.setter
    def isOpened(self, flag):
        self._connection_flag = flag
        
    @logger_decorator
    def informClients(self, msg, client):
        if not type(client) == list:
            client = [client]
        
        for client in client:
            client.toMessageList(msg)
            while client.status == "sending":
                time.sleep(0.01)
              
    def toLog(self, log_type, log_content):
        """
        Available log_types: 'debug', 'info', 'warning', 'error'
        """
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
            print(log_type.upper(), log_content)
            
             
    def _pinDictToList(self, dictionary):
        listed_dict = []
        for pin_type in ["IN", "OUT"]:
            listed_dict.append(pin_type)
            listed_dict += list(dictionary[pin_type].items())
            
        return listed_dict
    
    @logger_decorator
    def updateConfig(self, section, option, value, verbose=True):
        if self.parent == None:
            self.cp.set(section, str(option), str(value))
        else:
            self.parent._updateConfig(section, option, value, verbose)
            
    @logger_decorator
    def saveConfig(self, file_path="", file_name="", verbose=True):
        if file_path == "":
            file_path = self.conf_dir
        if file_name == "":
            file_name = self.conf_file
        with open(file_path + "/" + file_name, "w") as fp:
            self.cp.write(fp)
        
        if verbose:
            print("The config file has been saved.")
            
    @logger_decorator
    def readConfig(self, file_path, file_name):
        from configparser import ConfigParser
        self.cp = ConfigParser()
        self.cp.read(file_path + "/" + file_name)

        try:
            for in_n_out in ["IN", "OUT"]:
                config_dict = dict(self.cp.items("GPIO.%sPUT" % in_n_out))
                
                for pin_num, pin_nick in config_dict.items():
                    self._pin_assignment[in_n_out][int(pin_num)] = pin_nick
                    
        except Exception as ee:
            print("An error has been occured when read the config (%s)" % ee)
    
class DummyClient():
    
    def __init__(self):
        self.status = "standby"
        self._address = "127.0.0.1"
    
    def toMessageList(self, msg):
        print(msg)
    
    
if __name__ == '__main__':
    GC = GPIO_Controller()
    client = DummyClient()
