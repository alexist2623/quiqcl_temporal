# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 09:44:33 2022

@author: QCP32
"""
# INSTrument:NSELect {1 | 2 | 3}
# This command selects the output to be programmed among three outputs by a numeric value instead of the output identifier used in the INSTrument [:SELect] command. “1” selects +6V output, “2” selects +25V output, and
# "1" selects P6V", "2" selects "P25V", “3” selects "N25V" output.

import time


class DC_Power_Supply_Dummy():
    
    _connection = False
    
    def __init__(self, port="", stopbits=2, timeout=2, device=None):
        self.DC_ser = self.connect(port, stopbits, timeout)
        self.Channels = {1: "P6V", 2: "P25V", 3: "N25V"}
        self.Limits = {'1': {'vol':   5, 'cur': 4},
                       '2': {'vol':  15, 'cur': 2},
                       '3': {'vol': -15, 'cur': 2}}
        self.Voltages = {"1": 0, "2": 0, "3": 0}
        self.Currents = {"1": 0, "2": 0, "3": 0}
                
        time.sleep(0.6)
        self._connection = True
        
    def connect(self, port, stopbits, timeout):
        if self._connection:
            raise RuntimeError("The device is already occupied.")
        else:
            self._connection = True
        
    def close(self):
        self._connection = False
        
    def WriteDev(self, line):
        pass
        
    def ReadDev(self):
        return "Dummy"
        
    def SetLimit(self, ch, vol, cur):
        self.Limits[str(ch)] = {'vol': vol, 'cur': cur}
        
    def VoltageOn(self, ch, targetV):
        time.sleep(0.2)
        if targetV > self.Limits[str(ch)]['vol']:
            self.Voltages[str(ch)] = self.Limits[str(ch)]['vol']
        elif targetV < 0:
            self.Voltages[str(ch)] = 0
        else:
            self.Voltages[str(ch)] = targetV
        time.sleep(0.2)

    def CurrentOn(self, ch, targetA):
        if targetA > self.Limits[str(ch)]['cur']:
            targetA = self.Limits[str(ch)]['cur']
        elif targetA < 0:
            targetA = 0
        self.Currents[str(ch)] = targetA

    def TurnOff(self):
        for key in self.Voltages.keys():
            self.Voltages[key] = 0
            self.Currents[key] = 0
              
    def ReadValue_V(self, ch):
        return self.Voltages[str(ch)]
        
    def ReadValue_I(self, ch):
        return self.Currents[str(ch)]


    

if __name__ == "__main__":

    oven = DC_Power_Supply_Dummy("test_port")