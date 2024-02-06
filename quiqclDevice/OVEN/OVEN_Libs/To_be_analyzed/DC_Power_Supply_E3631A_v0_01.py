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

class DC_Power_Supply_E3631A():
    def __init__(self, port, device=None):
        if device == None: self.DC_ser = serial.Serial(port=port, stopbits=2, timeout=1)
        else: self.DC_ser = device
        self.WriteDev('SYST:REM')
        self.Limits = {'1': {'vol':   5, 'cur': 2},
                       '2': {'vol':  15, 'cur': 2},
                       '3': {'vol': -15, 'cur': 2}}
        
    def WriteDev(self, line):
        self.DC_ser.write(bytes(line + '\n'))
        
    def ReadDev(self):
        line = self.DC_ser.readline().decode()
        return line.rstrip('\r\n')
        
    def SetLimit(self, ch, vol, cur):
        self.Limits[str(ch)] = {'vol': vol, 'cur': cur}
        
    def VoltageOn(self, ch, targetV):
        self.WriteDev('INST:NSEL %d' % ch)
        self.WriteDev('OUTP ON')
        if targetV > self.Limits[str(ch)]['vol']:
            self.WriteDev('VOLT %f' % self.Limits[str(ch)]['vol'])
        else:
            self.WriteDev('VOLT %f' % targetV)

    def CurrentOn(self, ch, targetA):
        self.WriteDev('INST:NSEL %d' % ch)
        self.WriteDev('OUTP ON')
        if targetA > self.Limits[str(ch)]['cur']:
            self.WriteDev('CURR %f' % self.Limits[str(ch)]['cur'])
        else:
            self.WriteDev('CURR %f' % targetA)

    def TurnOff(self):
        self.WriteDev('OUTP OFF')
    
    def SetManual(self, flag):
        if flag == True:
            self.WriteDev('SYST:LOC')
        else:
            self.WriteDev('SYST:REM')
            
    def ReadValue_V(self):
        self.WriteDev('SOUR:VOLT?')
        value = float(self.ReadDev)
        return value
        
    def ReadValue_A(self):
        self.WriteDev('SOUR:CURR?')
        value = float(self.ReadDev)
        return value


    

if __name__ == "__main__":

    oven = DC_Power_Supply_E3631A() 