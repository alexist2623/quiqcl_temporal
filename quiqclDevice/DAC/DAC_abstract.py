# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 11:22:41 2021

@author: QCP32
"""

class DAC_AbstractBase:
    
    channel_num = 16
    voltage_range = [-15, 15]
    
    def openDevice(self):
        """
        """
        
    def closeDevice(self):
        """
        """
        
    def reset(self):
        """
        Set all the channel to 0V.
        """
        
    def setVoltage(self, channel, value):
        """
        Set the output voltage of the given channel.
        """
        
    def readVoltage(self, channel, value):
        """
        Read the output voltage of the given channel.
        """
        
    
        