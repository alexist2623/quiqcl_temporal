#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 28 08:23:16 2021

@author: pi
"""

from DC_Power_Supply_E3631A_v0_01 import DC_Power_Supply_E3631A
from DB_ASRI133109_v0_01 import DB_ASRI133109

import threading, configparser, os, usb, serial, platform, time
from serial.tools.list_ports import comports

conf_dir = os.path.dirname(__file__)
conf_file = "OVEN.conf"

class OVEN_Handler():
    
    def __init__(self, logger=None, MODEL="E3631A"):
        self._logger = logger
        self._thread = threading.Thread()
        self._queue = []
        
        self.DC = DC_Power_Supply_E3631A(port=None, device=self._discover_device(MODEL))
        
        self.DB = DB_ASRI133109()
        
        # Internal variables
        self.CNT = 0
        self.CHANNEL = "00"
        self.STATUS = "OFF"
        
        self._VOL = 0
        self._CUR = 0
        
        self._oven_flag = False
        self._timer = None
        self._oven = None
        
    def _read_config(self):
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(conf_dir + conf_file)
        
        conf_dict = dict(cp.items("OVEN"))
        
        self._settings = {}
        for idx, (key, val) in enumerate(conf_dict.items()):
            binary_key = "{0:02b}".format(idx)
            self._settings[binary_key] = {"CH_ID": key.split('_')[0],
                                            "ION": key.split('_')[1] + "yb",
                                            "CUR": float(val[:val.find('A')])}
            
        
    def _discover_device(self, IDN):        
        serial_ports = [(x[0], x[1], dict(y.split('=', 1) for y in x[2].split(' ') if '=' in y)) for x in comports()]
        port_candidates = []
        
        for dev in usb.core.find(find_all=True, custom_match= lambda x: x.bDeviceClass != 9):
            if platform.system() == 'Linux':
                port_candidates = [x[0] for x in serial_ports if x[2].get('SER') != None]
            else:
                raise NotImplementedError("Implement for platform.system()=={0}".format(platform.system()))
            
        if not len(port_candidates):
            self._to_log("No devices are found.", 'error')
            return
            
        for port in port_candidates:
            device = serial.Serial(port=port, stopbits=2, timeout=2)
            device.write(b'*IDN?\n')
            line = device.readline().decode()
            if IDN in line:
                print("Connected to", line)
                return device
            
    def to_worker(self, item: list):
        self._queue.append(item)
        if not self._thread.isAlive():
            self._thread = threading.Thread(target=self._thread_run)
            self._thread.start()
            
    def set_target(self, item: list):
        operation, client = item
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(conf_dir + conf_file)
        
        _, ch, _, which, value = operation.split(':')
        value = float(value)
        
        self._settings[ch]["CUR"] = value
        
        if which == "CUR":
            self._value_dict[ch]['CUR'] = value
        else:
            self._to_log("Unknown command (%s), from (%s, %d)" % (operation, client.getpeername()[0], client.getpeername()[1]), 'error')
            return
        
        cp_key = "_".join([self._settings[ch]["CH_ID"], self._settings[ch]["ION"][:-2]])
        cp.set("OVEN", cp_key, "%.3fA" % (value))
        with open (conf_dir + conf_file, 'w') as cw:
            cp.write(cw)
            
        self._to_client("OVEN:%s:%s:%.3f" % (ch, which, value), client)
        self._to_log("%s of %s is set to %.3f by (%s, %d)" % (which, cp_key, value, client.getpeername()[0], client.getpeername()[1]), 'info')
        
    def _thread_run(self):
        while len(self._queue):
           queue =  self._queue.pop(0)
           operation, client = queue
           print("Current operation:", operation)
           if "ON" in operation:
               _, channel, _ = operation.split(':')
               self.CNT = int(8*60)
               self.CHANNEL = channel
               self._TAR_VOL = self._value_dict[self.CHANNEL]['VOL']
               self._TAR_CUR = self._value_dict[self.CHANNEL]['CUR']
               self._oven_flag = True
               self.STATUS = "ON"
               
               self._timer = threading.Thread(target=self._timer_run, args=(client, ))
               self._oven = threading.Thread(target=self._oven_run, args=(client, ))
               self._oven.start()
               self._timer.start()
               
               
           elif "OFF" in operation:
               print("getting off")
               _, channel, _ = operation.split(':')
               db_dict = self._value_dict[self.CHANNEL]
               self.DB.asri_oven(db_dict["CH_ID"],
                                 db_dict["ION"],
                                 (self._VOL/self._CUR),
                                 self._VOL,
                                 self._CUR)
               self.CNT = 0
               self.STATUS = "OFF"
               
    def _timer_run(self, client):
        while self.CNT > 0:
            time.sleep(1)
            self.CNT -= 1
            self._to_client("OVEN:%s:CNT:%03d" % (self.CHANNEL, self.CNT), client)
            
            if self.CNT <= 0:
                if self.STATUS == "ON":
                    self.to_worker(["OVEN:%s:OFF" % self.CHANNEL, client])
               
    def _oven_run(self, client):
        start_flag = 0
        while self._oven_flag:
            time.sleep(0.2)
            self._VOL = self.DC.ReadValue_V(1)
            time.sleep(0.2)
            self._CUR = self.DC.ReadValue_I(1)

            if self.STATUS == "ON":
                if not start_flag:
                    if (self._TAR_CUR - self._CUR > 0.15):
                        self.DC.CurrentOn(1, self._CUR + 0.15)
                    else:
                        self.DC.CurrentOn(1, self._TAR_CUR)
                        start_flag = True
                
            else:
                if not self._CUR < 0.15:
                    self.DC.CurrentOn(1, self._CUR - 0.15)
                else:
                    self.DC.CurrentOn(1, 0)
                    self._oven_flag = False
                    self._to_client("OVEN:%s:OFF" % self.CHANNEL, client)
            self._to_client("OVEN:%s:VOL:%.3f" % (self.CHANNEL, self._VOL), client)
            self._to_client("OVEN:%s:CUR:%.3f" % (self.CHANNEL, self._CUR), client)                
                
    def _to_client(self, msg, client):
        if isinstance(client, list):
            for cli in client:
                cli.sendall(bytes(msg + '\n', 'latin-1'))
                
        else: client.sendall(bytes(msg + '\n', 'latin-1'))
                      
            
    def _to_log(self, log_msg, log_type):
        if not self._logger == None:
            if log_type == 'info':
                self._logger.info(log_msg)
            elif log_type == 'warning':
                self._logger.warning(log_msg)
            elif log_type == 'error':
                self._logger.error(log_msg)
        
if __name__ == '__main__':
    OH = OVEN_Handler()