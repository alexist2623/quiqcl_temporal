#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 10:10:15 2021

@author: pi
"""
# INSTrument:NSELect {1 | 2 | 3}
# This command selects the output to be programmed among three outputs by a numeric value instead of the output identifier used in the INSTrument [:SELect] command. “1” selects +6V output, “2” selects +25V output, and
# "1" selects P6V", "2" selects "P25V", “3” selects "N25V" output.

import serial
import time

class DC_Power_Supply_E3631A():
    def __init__(self, port, stopbits=2, timeout=2, device=None):
        self.DC_ser = None
        if device == None: self.DC_ser = self.connect(port, stopbits, timeout)
        else: self.DC_ser = device
        self.WriteDev('SYST:REM')
        self.Channels = {1: "P6V", 2: "P25V", 3: "N25V"}
        self.Limits = {'1': {'vol':   5, 'cur': 4},
                       '2': {'vol':  15, 'cur': 2},
                       '3': {'vol': -15, 'cur': 2}}
                
        time.sleep(0.3)
        self.WriteDev('INST:NSEL 1')
        time.sleep(0.3)
        self.WriteDev('VOLT 5')
        
    def connect(self, port, stopbits, timeout):
        try:
            device = serial.Serial(port=port, stopbits=2, timeout=timeout)
            return device
        except Exception as err:
            print("An error while connecting the device. (%s)" % err)
        
    def close(self):
        self.DC_ser.close()
        
    def WriteDev(self, line):
        self.DC_ser.write((line + '\n').encode())
        
    def ReadDev(self):
        line = self.DC_ser.readline().decode()
        return line.rstrip('\r\n')
        
    def SetLimit(self, ch, vol, cur):
        self.Limits[str(ch)] = {'vol': vol, 'cur': cur}
        
    def VoltageOn(self, ch, targetV):
        self.WriteDev('INST:NSEL %d' % ch)
        time.sleep(0.2)
        self.WriteDev('OUTP ON')
        if targetV > self.Limits[str(ch)]['vol']:
            self.WriteDev('VOLT %f' % self.Limits[str(ch)]['vol'])
        elif targetV < 0:
            self.WriteDev('VOLT 0')
        else:
            self.WriteDev('VOLT %f' % targetV)
        time.sleep(0.2)

    def CurrentOn(self, ch, targetA):
        if targetA > self.Limits[str(ch)]['cur']:
            targetA = self.Limits[str(ch)]['cur']
        elif targetA < 0:
            targetA = 0
        self.WriteDev('APPL %s, 5.0, %.3f' % (self.Channels[ch], targetA))

    def TurnOff(self):
        self.WriteDev('OUTP OFF')
    
    def SetManual(self, flag):
        if flag == True:
            self.WriteDev('SYST:LOC')
        else:
            self.WriteDev('SYST:REM')
            
    def ReadValue_V(self, ch):
        self.WriteDev('MEAS:VOLT? %s' % self.Channels[ch])
        value = float(self.ReadDev())
        return value
        
    def ReadValue_I(self, ch):
        self.WriteDev('MEAS:CURR? %s' % self.Channels[ch])
        value = float(self.ReadDev())
        return value


    

if __name__ == "__main__":

    oven = DC_Power_Supply_E3631A("/dev/ttyUSB0") 