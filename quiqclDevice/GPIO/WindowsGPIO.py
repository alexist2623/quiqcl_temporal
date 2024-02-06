# -*- coding: utf-8 -*-
"""
Created on Thu Nov 10 11:06:41 2022

@author: QCP32
"""

class GPIO_Dummy(object):
    
    _pin_out_dict = {"IN": {}, "OUT": {}}
    _mode = "BCM"
    _verbose = False
    
    
    def __init__(self):
        pass
        
    def setwarnings(self, mode):
        self._verbose = mode
    
    @property
    def BCM(self):
        return "BCM"
    
    @property
    def BOARD(self):
        return "BOARD"
    
    @property
    def IN(self):
        return "IN"
    
    @property
    def OUT(self):
        return "OUT"
    
    @property
    def PUD_UP(self):
        return "PUD_UP"
    
    @property
    def PUD_DOWN(self):
        return "PUD_DOWN"
    
    def setmode(self, mode):
        self._mode = mode
        
    def setup(self, pin_num, pin_mode, pull_up_down=None):
        self._pin_out_dict[pin_mode][pin_num] = None
        
    def input(self, pin_num):
        return True
    
    def output(self, pin_num, value):
        if not pin_num in self._pin_out_dict["OUT"].keys():
            if self._verbose:
                raise RuntimeError ("The output pin should be assigned beforehand.")
                return
        self._pin_out_dict["OUT"][pin_num] = value
    
    def cleanup(self):
        self._pin_out_dict = {"IN": {}, "OUT": {}}
        if self._verbose:
            print("All GPIO pins are cleared out.")
                
    
if __name__ == "__main__":
    G = GPIO_Dummy()