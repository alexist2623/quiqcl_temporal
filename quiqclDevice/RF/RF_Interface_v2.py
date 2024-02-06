# -*- coding: utf-8 -*-
"""
@author: Junho Jeong
@Tel: 010-9600-3392
@email1: jhjeong32@snu.ac.kr
@mail2: bugbear128@gmail.com
"""

import os
from PyQt5.QtCore import QThread
from queue import Queue

from RF_Controller_v2 import RF_Controller

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
import time
debug = True

class RFInterface(QThread):
    
    """
    This is an interface class that controls multiple RF devices.
    """
    
    _status = "standby"
    # Available rf device model list
    rf_device_model_list = ['synthnv', 'synthhd', 'sg384', 'apsyn420', 'dummy_rf']
    
    def logger_decorator(func):
        """
        It writes logs when an exception happens.
        """
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as err:
                if debug: print(err)
                if not self.logger == None:
                    self.logger.error("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
                else:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return wrapper
    
    def __init__(self, parent=None, config=None, logger=None, device="RF"):
        super().__init__()
        self.parent = parent
        self.cp = config
        self.logger = logger
        self.device = device
        
        self.device_dict = {}
        self._readRFconfig()
        self._client_list = []
        
        self.queue = Queue()
        

    def __call__(self):
        return self.device_dict
    
    @property
    def description(self):
        return "RF_Interface"
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, status):
        self._status = status

    @logger_decorator
    def _readRFconfig(self):
        rf_device_str = self.cp.get("rf", "device_list")
        rf_device_list = "".join(rf_device_str.split()).split(",")
        

        for device_idx, device in enumerate(rf_device_list):
            print("Opening an RF device '%s'.... (%d/%d)" % (device, device_idx+1, len(rf_device_list)))

            device_class = RF_Controller(parent=self, 
                                         config=self.cp,
                                         logger=self.logger.getChild("%s" % device),
                                         device=device,
                                         device_type=self.cp.get(device, "type")
                                         )
            device_class._dev_signal.connect(self.changedDeviceStatus)
            device_class._timer_signal.connect(device_class.startTimer)
            self.device_dict[device] = device_class
            
            
    @logger_decorator    
    def toWorkList(self, cmd): 
        client = cmd[-1]
        if not client in self._client_list:
            self._client_list.append(client)
            
        self.queue.put(cmd)
        if not self.isRunning():
            self.status = "running"
            self.start()
    
    # @logger_decorator
    def run(self):
        while self.queue.qsize():
            work = self.queue.get()
            work_type, rf_device = work[:2]
            operation = work[2]
            client = work[-1]
                        
            self.status = ":".join([rf_device, ":".join([str(op) for op in operation])])
            
            if work_type == "C":
                        
                if rf_device == "ALL":
                    sub_cmd = operation[0]
                    if sub_cmd == "ON":
                        self.openDevices()
                    elif sub_cmd == "OFF":
                        self.closeDevices()
                    else:
                        self.toLog("error", "An unknown all RF control command (%s)" % operation)
                        continue
                    msg = ["D", "RF", "ALL", [sub_cmd]]
                    self.AnnounceToClients(msg, self._client_list)
                
                # A new connection
                elif rf_device == "HELO":
                    data = []
                    for rf_handler in self.device_dict.values():
                        data += [rf_handler.device, rf_handler.device_type, rf_handler.isConnected]
                    msg = ["D", "RF", "HELO", data]
                    self.AnnounceToClients(msg, client)
                    
                # A disconnection request. The RF devices will be closed for the safety if there are no clients.
                elif rf_device == "DCN": # disconnect
                    self._client_list.remove(client)
                    if not len(self._client_list):
                        self.toLog("info", "No clients, turning off the RF devices.")
                        self.closeDevices()
                    
                # Let each device class do their jobs.
                elif rf_device in self.device_dict.keys():                    
                    sub_cmd = operation[0]
                    sub_oper = operation[1:]
                    sub_dev = self.device_dict[rf_device]
                    
                    if sub_cmd == "ON":

                        if not sub_dev.isConnected:  # It is already connected
                            con_flag = sub_dev.openDevice()
                            if con_flag == -1:
                                msg = ["E", "RF", rf_device, ["CON"]]
                                self.AnnounceToClients(msg, client)
                            else:
                                msg = ["D", "RF", rf_device, ["ON"]]
                                self.AnnounceToClients(msg, self._client_list)
                        else:
                            msg = ["D", "RF", rf_device, ["ON"]]
                            self.AnnounceToClients(msg, client)
                            
                        
                    elif sub_cmd == "OFF":
                        msg = ["D", "RF", rf_device, ["OFF"]]
                        
                        if sub_dev.isConnected:
                            sub_dev.closeDevice()
                            self.AnnounceToClients(msg, self._client_list)
                        else:
                            self.AnnounceToClients(msg, client)
                        
                    elif sub_cmd == "SETO": # power on
                        for channel, flag in zip(sub_oper[0::2], sub_oper[1::2]):
                            return_power_data = ["SETP"]
                            if flag:
                                sub_dev.setToMinPower(channel)
                                power = sub_dev.readSettings("power", channel)
                                return_power_data += [channel, power]
                            else:
                                while sub_dev.isUpdating:
                                    time.sleep(0.2)
                            sub_dev.setOutput(channel, flag)
                        msg = ["D", "RF", rf_device, ["SETO"] + sub_oper]
                        self.AnnounceToClients(msg, self._client_list)
                        
                        if len(return_power_data) > 1:
                            msg = ["D", "RF", rf_device, return_power_data]
                            self.AnnounceToClients(msg, self._client_list)

                    elif sub_cmd == "SETP": # power, channel
                        msg = ["D", "RF", rf_device, ["SETP", 'g', True]]
                        out_flag = False
                        if not sub_dev.isUpdating:
                            for channel, power in zip(sub_oper[0::2], sub_oper[1::2]):
                                sub_out_flag = sub_dev.settings[channel]["out"]
                                out_flag += sub_out_flag
                                if sub_out_flag:
                                    sub_dev.setPowerList(power, channel)
                            if not out_flag: # ignore when the power is off
                                continue
                            sub_dev.isUpdating = True
                            sub_dev._timer_signal.emit()
                            self.AnnounceToClients(msg, self._client_list)
                        else:
                            self.AnnounceToClients(msg, client)
                        
                    elif sub_cmd == "SETF": # freq, channel
                        data = [sub_cmd]
                        for channel, freq in zip(sub_oper[0::2], sub_oper[1::2]):
                            sub_dev.setFrequency(freq, channel)
                            freq = sub_dev.readSettings("freq", channel)
                            data += [channel, freq]
                        operation = data
                        self.AnnounceToClients(["D", "RF", rf_device, operation], self._client_list)
                        
                    elif sub_cmd == "SETPH": # phase, channel
                        data = [sub_cmd]
                        for channel, phase in zip(sub_oper[0::2], sub_oper[1::2]):
                            sub_dev.setPhase(phase, channel)
                            phase = sub_dev.readSettings("phase", channel)
                            data += [channel, phase]
                        operation = data
                        self.AnnounceToClients(["D", "RF", rf_device, operation], self._client_list)

                        
                    elif sub_cmd == "LOCK":
                        lock_flag, lock_freq = sub_oper
                        sub_dev.setFrequencyLock(lock_flag, lock_freq)                        
                        flag = int(sub_dev.isLocked)
                        operation = ["LOCK", flag]
                        self.AnnounceToClients(["D", "RF", rf_device, operation], self._client_list)
                        
                    else:
                        msg = ["E", "RF", rf_device, operation]
                        self.toLog("error", "An unknown operation of the device (%s, %s)" % (rf_device, "".join([str(op) for op in operation])))
                        self.AnnounceToClients(msg, client)
                        continue
                        
                    # msg = ["D", "RF", rf_device, operation]
                    # self.AnnounceToClients(msg, self._client_list)
                    
                # What did the client want to operate?
                else:
                    msg = ["E", "RF", "DEV", [rf_device]]
                    self.toLog("error", "An unkown rf device. (%s)" % rf_device)
                    self.AnnounceToClients(msg, client)
                    
            elif work_type == "Q":
                sub_cmd = operation[0]
                sub_oper = operation[1:]
                
                if rf_device == "STAT":
                    if sub_cmd == "ALL":
                        for rf_device in self.device_dict.keys():
                            msg = ["D", "RF", rf_device, ["STAT"] + self.device_dict[rf_device].getCurrentSettings()]
                            self.AnnounceToClients(msg, client)
                            msg = ["D", "RF", rf_device, ["LOCK", self.device_dict[rf_device].isLocked]]
                            self.AnnounceToClients(msg, client)
                    else:
                        for rf_device in sub_oper:
                            msg = ["D", "RF", rf_device, ["STAT"] + self.device_dict[rf_device].getCurrentSettings()]
                            self.AnnounceToClients(msg, client)

                elif rf_device in self.device_dict.keys():                    

                    sub_dev = self.device_dict[rf_device]
                    data_list = []
                    
                    if sub_cmd == "GETP":
                        data_list.append("SETP")
                        for channel in sub_oper:
                            power = sub_dev.readSettings("power", channel)
                            data_list += [channel, power]
                        msg = ["D", "RF", rf_device, data_list]
                        
                    elif sub_cmd == "GETF":
                        data_list.append("SETF")
                        for channel in sub_oper:
                            freq = sub_dev.readSettings("freq", channel)
                            data_list += [channel, power]
                        msg = ["D", "RF", rf_device, data_list]
                        
                    elif sub_cmd == "GETO":
                        data_list.append("SETO")
                        for channel in sub_oper:
                            out = sub_dev.readSettings("out", channel)
                            data_list += [channel, out]
                        msg = ["D", "RF", rf_device, data_list]
                        
                    elif sub_cmd == "GETPH":
                        data_list.append("SETPH")
                        for channel in sub_oper:
                            phase = sub_dev.readSettings("phase", channel)
                            data_list += [channel, phase]
                        msg = ["D", "RF", rf_device, data_list]                        
                                            
                    elif sub_cmd == "MAXP":
                        data_list.append("MAXP")
                        for channel in sub_oper:
                            max_power = sub_dev.readSettings("max_power", channel)
                            data_list += [channel, max_power]
                        msg = ["D", "RF", rf_device, data_list]
                        
                    elif sub_cmd == "MINP":
                        data_list.append("MINP")
                        for channel in sub_oper:
                            max_power = sub_dev.readSettings("min_power", channel)
                            data_list += [channel, max_power]
                        msg = ["D", "RF", rf_device, data_list]      
                        
                    elif sub_cmd == "MINF":
                        data_list.append("MINF")
                        for channel in sub_oper:
                            max_power = sub_dev.readSettings("min_frequency", channel)
                            data_list += [channel, max_power]
                        msg = ["D", "RF", rf_device, data_list]      
                        
                    elif sub_cmd == "MAXF":
                        data_list.append("MAXF")
                        for channel in sub_oper:
                            max_power = sub_dev.readSettings("max_frequency", channel)
                            data_list += [channel, max_power]
                        msg = ["D", "RF", rf_device, data_list]      
                        
                        
                    elif sub_cmd == "LOCK":
                        flag = int(sub_dev.isLocked)
                        msg = ["D", "RF", rf_device, ["LOCK", flag]]
                        
                    else:
                        msg = ["E", "RF", rf_device, ["CMD", sub_cmd]]
                        self.toLog("error", "An Unknown sub_cmd (%s)" % sub_cmd)
                    
                    self.AnnounceToClients(msg, client)
                    
            else:
                msg = ["E", "RF", "CMD", [work_type]]
                self.AnnounceToClients(msg, client)
                self.toLog("error", "An Unknown work_type (%s)" % work_type)

    @logger_decorator
    def openDevices(self):
        for device in self.device_dict.values():
            device.openDevice()
        
    @logger_decorator
    def closeDevices(self):
        for device in self.device_dict.values():
            device.closeDevice()
        
        
    def toLog(self, log_type, log_content):
        """
        log_type: debug, info, warning, error
        log_conetent: any error messages
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
    
    @logger_decorator
    def AnnounceToClients(self, msg, client_list):
        if not type(client_list) == list:
            client_list = [client_list]
        
        for client in client_list:
            client.toMessageList(msg)
            
    @logger_decorator
    def changedDeviceStatus(self, device, cmd, data):
        if cmd == "p":
            operation = ["SETP"] + data
            msg = ["D", "RF", device, operation]
            
        elif cmd == "gf": # gradual finished
            operation = ["SETP", "g", False]
            msg = ["D", "RF", device, operation]
            
        elif cmd == "f": # Initial frequency
            operation = ["SETF"] + data
            msg = ["D", "RF", device, operation]
            
        elif cmd == "e":
            if data[0] == "con": # connection failed
                msg = ["E", "RF", device, ["con"]]
            
        else:
            self.toLog("error", "A wrong command of data from signal. (%s)" % cmd)
            
        self.AnnounceToClients(msg, self._client_list)
    

        
"""
if __name__ == "__main__":
    class DummyClient():
        
        def __init__(self):
            pass
        
        def sendMessage(self, msg):
            print(msg)
            
        def toMessageList(self, msg):
            print(msg)
            
    def test_operation(device, operation):
        srv.device_dict["RF"].toWorkList(["C", device, [*operation], dummy])
    
    dummy = DummyClient()
    
    
    test_operation("HELO", [])
    test_operation("ALL", ["ON"])
    test_operation("ea_rf", ["ON"])
    test_operation("ea_rf", ["PWUP", 0, 1])
    test_operation("ec_rf", ["PWUP", 0, 1])
    test_operation("ea_rf", ["SETP", 0, -8, 1, -16])
    test_operation("ec_rf", ["SETP", 0, -8, 1, -16])
    test_operation("ea_mw", ["SETP", 0, -11])

    
    def test_query(device, operation):
        srv.device_dict["RF"].toWorkList(["Q", device, [*operation], dummy])
    
    test_query("ALL", ["STAT"])
    test_query("ea_rf", ["GETP", 0, 1])

    
    
    
    srv.device_dict["RF"].device_dict["ea_rf"]._getHardSetting("out", 0)


"""