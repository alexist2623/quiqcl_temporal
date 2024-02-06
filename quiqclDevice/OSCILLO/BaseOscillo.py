#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 00:35:12 2021

@author: pi
"""

import numpy
import matplotlib.pyplot as plt
import sys
import pyvisa as visa
import math
import time

class OscilloBase:
    """
    This class is an interface for interacting with Oscilloscopes.
    
    - Every class implemetning Oscilloscope device should inherit this class.
    - Note that expections may occur in each method depending on devices
    """
    
    def __init__(self, num_channels):
        self.__num_channels = num_channels
        
    def connect(self):
        """Connects to the device."""
        not_implemented('connect', self)
    
    def disconnect(self):
        """Disconnects to the device."""
        not_implemented('disconnect', self)
        
    def is_connected(self) -> bool:
        """
        Returns:
            whether the device is currently connected.
        """
        not_implemented('is_connected', self)
    


class VisaOscilloscope(OscilloBase):
    """
    This is a base class that handles oscilloscopes through pyvisa
    
    Package 'pyvisa' is required.
    
    it controls devices using Visa interface which support both socket and serial.
    To initiate this class, you need to know the device_id first
    """

    def __init__(self, num_channels, device_id = None, **visa_kwargs):
        """
        scope is None until you open the device
        
        The timeout is set to 100 s for large data transfer.
        """
        super().__init__(num_channels)
        self.__connected = False
        self.__scope = None
        
        self.__rm = visa.ResourceManager()
        self.__rm.timeout = 100
        self.__device_id = device_id
        
    def connect(self):
        if not self.__device_id in self.rm.list_resources():
            raise ValueError ('Wrong Device ID - {}'.format(self.__device_id))
        else:
            self.__scope = self.__rm.open_resource(self.__device_id)
            self.__connected = True

    def disconnect(self):
        self.__scope.write(":STOP")
        self.__scope.close()
        self.__connected = False
        
    def is_connected(self) -> bool:
        return self.__connected

    @property       
    def device_id(self):
        return self.__device_id
    
    @device_id.setter
    def device_id(self, device_id):
        self.__device_id = device_id
       
    @property
    def time_scale(self):
        return self.__time_base
    
    @time_scale.setter
    def time_scale(self, time_base):
        self.__time_base = time_base

    @property
    def sample_rate0(self):
        return self.__sample_rate0
    
    @property
    def sample_rate1(self):
        return self.__sample_rate1
       
    @sample_rate0.setter
    def sample_rate0(self, sample_rate):
        self.__sample_rate0 = sample_rate
       
    @sample_rate1.setter
    def sample_rate1(self, sample_rate):
        self.__sample_rate1 = sample_rate
        
    @property
    def data_scale0(self):
        return self.__data_scale0
    
    @property
    def data_scale1(self):
        return self.__data_scale1
    
    @data_scale0.setter
    def data_scale0(self, data_scale):
        self.__data_scale0 = data_scale
        
    @data_scale1.setter
    def data_scale1(self, data_scale):
        self.__data_scale1 = data_scale
        
    @property
    def memory_depth0(self):
        return self.__memory_depth0
    
    @property
    def memory_depth1(self):
        return self.__memory_depth1
    
    @memory_depth0.setter
    def memory_depth0(self, mem_depth):
        self.__memory_depth0 = mem_depth
        
    @memory_depth1.setter
    def memory_depth1(self, mem_depth):
        self.__memory_depth1 = mem_depth
        
    @property
    def data_offset0(self):
        return self.__data_offset0
    
    @property
    def data_offset1(self):
        return self.__data_offset1
        
    @data_offset0.setter
    def data_offset0(self, data_offset):
        self.__data_offset0 = data_offset

    @data_offset1.setter
    def data_offset1(self, data_offset):
        self.__data_offset1 = data_offset        
    
    def __send_command(self, )
    
    def __query_command(self, cmd):
        return (self.scope.query_ascii_values(cmd)[0])


def not_implemented(func, obj):
    """Raises NotImplementedError with the given function name.

    This is a helper function, which is NOT included in RFSource class.
    """
    raise NotImplementedError("method '{}' is not supported on device '{}'"
                              .format(func, obj.__class__.__name__))