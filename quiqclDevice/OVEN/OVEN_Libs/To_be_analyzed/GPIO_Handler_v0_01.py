#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 27 16:21:15 2021

@author: pi
"""

import RPi.GPIO as G
import threading
import configparser
import os
import platform
import time

conf_dir = os.path.dirname(__file__) + '/Libs/'
conf_file = platform.node() + '.conf'

class GPIO_Handler():
    
    def __init__(self, logger=None):
        super().__init__()
        self._G = G
        self._G.setwarnings(False)
        self._logger = logger
        
        try: 
            self._G.cleanup()
            self._to_log("GPOI pins are reseted.", "info")
        except: pass
        self._G.setmode(self._G.BCM)
        self.INPUT = {}
        self.OUTPUT = {}
        self._queue = []
        self._thread = threading.Thread()
        
        self._read_config()
        
        for output in self.OUTPUT.values():
            self._G.setup(output, self._G.OUT)
        for input in self.INPUT.values():
            self._G.setup(input, self._G.IN)
            
    def _read_config(self):
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(conf_dir + conf_file)
        
        if "GPIO.INPUT" in cp.sections():
            self.INPUT = dict(cp.items("GPIO.INPUT"))
            for key, val in self.INPUT.items():
                try: self.INPUT[key] = int(val)
                except: 
                    if "GPIO" in val:
                        self.INPUT[key] = int(val[4:])
                    else: self._to_log("Invalid input pin(%s) is declared. Check the config file." % val, 'warning')                        
                
        if "GPIO.OUTPUT" in cp.sections():
            self.OUTPUT = dict(cp.items("GPIO.OUTPUT"))
            for key, val in self.OUTPUT.items():
                try: self.OUTPUT[key] = int(val)
                except: 
                    if "GPIO" in val:
                        self.OUTPUT[key] = int(val[4:])
                    else: self._to_log("Invalid output pin(%s) is declared. Check the config file." % val, 'warning')
                        
    def to_worker(self, item: list):
        self._queue.append(item)
        if not self._thread.isAlive():
            self._thread = threading.Thread(target=self._thread_run)
            self._thread.start()
        
        
    def _thread_run(self):
        while len(self._queue):
           queue = self._queue.pop(0)
           
           operation, client = queue
           
           if ("OVEN" in operation):
               _, ch, _ = operation.split(':')
               for idx, val in enumerate(ch[::-1]):
                   self._oven_control('OVEN%d' % (idx+1), int(val))
               
               try: self._to_client("OVEN:%s:CHAN\n" % ch, client)
               except: self._to_log("The client (%s, %d) is disconnected while controlling (%s)." % (client.getpeername()[0], client.getpeername()[1], ch), 'warning')
               
           elif "MIRROR" in operation:
               _, ch, _ = operation.split(':')
               self._mirror_flip("FLIP%s" % ch, client)
               
           elif "SHUTTER" in operation:
               _, ch, val = operation.split(':')
               if isinstance(val, str):
                   if val == "OPEN": val = 1
                   elif val == "CLOSE": val = 0
               self._shutter_control("SHUT%s" % ch, int(val), client)
           
           else:
               self.to_log("Unknown command has been requested (%s from %s)." % (operation, client.getpeername()[0]), 'error')
               
           
    def _mirror_flip(self, mirror, client):
        if not mirror in self.OUTPUT.keys():
            self._to_log("No such mirror found (%s)." % mirror, 'warning')
        else:
            self._G.output(self.OUTPUT[mirror], 1)
            time.sleep(0.1)
            self._G.output(self.OUTPUT[mirror], 0)
            try: self._to_client("%s:FLIPPED" % mirror, client)
            except: self.to_log("The client (%s) is disconnected while flipping mirror (%s)." % (client.getpeername()[0], mirror), 'warning')
            
    def _shutter_control(self, shutter, status, client):
        if not shutter in self.OUTPUT.keys():
            self._to_log("No such shutter found (%s)." % shutter, 'warning')
        else:
            self._G.output(self.OUTPUT[shutter], status)
            try: self._to_client("%s:SET:%s." % (shutter, 'OPEN' if status else 'CLOSE'), client)
            except: self.to_log("The client (%s) is disconnected while controlling shutter (%s)." % (client.getpeername()[0], shutter), 'warning')
    
    def _oven_control(self, oven, status):
        if not oven in self.OUTPUT.keys():
            self._to_log("No such oven found (%s)." % oven, 'warning')
        else:
            self._G.output(self.OUTPUT[oven], status)
            
    def _to_client(self, msg, client):
        if isinstance(client, list):
            for cli in client:
                cli.sendall(bytes(msg + '\n', 'latin-1'))    
        else:
            client.sendall(bytes(msg + '\n', 'latin-1'))
                        
    def _to_log(self, log_msg, log_type):
        if not self._logger == None:
            if log_type == 'info':
                self._logger.info(log_msg)
            elif log_type == 'warning':
                self._logger.warning(log_msg)
            elif log_type == 'error':
                self._logger.error(log_msg)
        
#    !def _
        
if __name__ == '__main__':
    GH = GPIO_Handler()