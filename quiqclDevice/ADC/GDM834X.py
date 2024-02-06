# -*- coding: utf-8 -*-
"""
Created on Sat Oct  9 08:24:42 2021

v0.01: Primitive version that for ADC
"""
import serial
from serial.tools.list_ports import comports

def requires_device_open(func):
    """Decorator that checks if the device is open.

    Raises:
        RuntimeError - the func is called before the device is open.
    """

    def wrapper(self, *args):
        if self._is_opened:
            return func(self, *args)
        else:
            raise RuntimeError('{} is called before the device is opened.'
                               .format(func.__name__))
    return wrapper

class GDM834X(object):
    """
    This class provides a compliation of APIs of GDM8341A from GWINSTEK (Taiwanese)
    Note that some APIs that do not match with our purpose are missing.
    """
    adc = None
    _device_candidate = {}
    _is_opened = False
    
    def __init__(self):
        self.scanDevice()
        assert len(self._device_candidate), "No GDM8341A has been found."
                
    def scanDevice(self):
        for dev in comports():
            if "GDM834" in dev.description:
                serial_number = dev.serial_number
                com_port      = dev.device
                description   = dev.description
                
                self._device_candidate[serial_number] = {"desc": description, "com": com_port}
        
    def openDevice(self, com_port=None):
        if com_port == None:
            device_list = list(self._device_candidate.values())
            com_port = device_list[0]["com"]
        self.adc = serial.Serial(port=com_port, timeout=0.2)
        self._is_opened = True
        device_id = self.queryValue("*IDN?")
        if not len(device_id):
            self._is_opened = False
            raise RuntimeError ("The device is not responding! please check the device")
            return
        print("The device sucessfully opened!")
        
    @requires_device_open
    def closeDevice(self):
        self.adc.close()
        self.adc = None
               
    @requires_device_open
    def goRemote(self):
        "you should fill this out"
        
    @requires_device_open
    def goLocal(self):
        "you should fill this out"
        
    @requires_device_open
    def readVoltage(self, channel=1, vol_type="DC"):
        "you should fill this out"
        
    @requires_device_open
    def readCurrent(self, channel=1, cur_type = "DC"):
        "you should fill this out"
        
    @requires_device_open
    def readResistance(self, channel=1):
        "you should fill this out"
        
    @requires_device_open
    def readFrequency(self, channel=1):
        "you should fill this out"
                
    @requires_device_open
    def writeCommand(self, command):
        if command[-1] != '\n':
            command += '\n'
        self.adc.write(command.encode())
        
    @requires_device_open
    def queryValue(self, command):
        self.writeCommand(command)
        line = self.adc.readline().decode()[:-2] # drop EOL
        return line
        
    
if __name__ == "__main__":
    gdm = GDM834X()