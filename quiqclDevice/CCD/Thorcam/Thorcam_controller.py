# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 00:30:47 2021

@author: CPO
"""
import os
import threading
import numpy as np
from datetime import datetime
from PIL import Image
from tifffile import tifffile
from QuIQCL_ThorCam import QuIQCL_ThorCam

class CCD_controller_Base:
    
    _image_buffer = None
    _buffer_size = 50
    _buffer_list = []
    
    _avail_acquisition_modes = ['single_scan', 'continuous_scan']
    
    _acquisition_mode = 'continuous_scan'
    _img_cnt = 0
    _running_flag = False
    _is_opened = False
    
    _store_full_image = False
    _half_period_flag = True
    

class CCD_controller(CCD_controller_Base):
    
    def __init__(self, data_p = None, parent=None):
        self._thor_cam = QuIQCL_ThorCam()
        self.parent = parent
        self.data_p = data_p
        
        self.openDevice()
        
        # Get all the initial parameters from the device
        self._read_settings()
               
        self.acquisition_mode = self._acquisition_mode
        
        self._running_thread = threading.Thread(target = self._get_ccd_image, daemon=True)
        
        print("Device standby.")
        
    def _read_settings(self):
        attr_list = self._thor_cam.__dir__()
        for  attr in attr_list:
            if "get_" in attr:
                func = getattr(self._thor_cam, attr)
                func()
    
    def openDevice(self):
        self._thor_cam.cam_serial = self._thor_cam.get_cam_list()[0]
        self._thor_cam.open_cam()
        
        print("Device opened!")
    
    def closeDevice(self):
        self._thor_cam.stop_camera()
        self._thor_cam.close_cam()
        if self._running_thread.is_alive():
            self._running_thread.join()
    
    def startAcquisition(self):
        self._img_cnt = 0
        self._buffer_list.clear()
        self._thor_cam.play_camera()
        if not self._running_thread.is_alive():
            self._running_thread = threading.Thread(target = self._get_ccd_image)
            self._running_thread.start()
        self._running_flag = True
    
    def stopAcquisition(self):
        self._thor_cam.stop_camera()
        if self._running_thread.is_alive():
            self._running_thread.join()
        self._running_flag = False
    
    @property
    def sensor_size(self):
        return self._thor_cam.sensor_size
    
    @property
    def gain(self):
        return self._thor_cam.gain
        
    @gain.setter
    def gain(self, value):
        self._thor_cam.set_gain(value)
        
    @property
    def exposure_time(self):
        return self._thor_cam.exposure_ms
    
    @exposure_time.setter
    def exposure_time(self, exp_time):
        self._thor_cam.set_exposure_ms(exp_time)
        
    @property
    def acquisition_mode(self):
        return self._acquisition_mode
    
    @acquisition_mode.setter
    def acquisition_mode(self, mode):
        assert isinstance(mode, str), "Acquisition mode should be a string."
        if not mode in self._avail_acquisition_modes:
            raise ValueError ("Acqusition mode should be either 'single_scan' or 'continuous_scan'.")
        self._acquisition_mode = mode
        
        if mode == "single_scan":
            self._thor_cam.set_trigger_count(self.trigger_count)
        else:
            self._thor_cam.set_trigger_count(0)
        
    @property
    def trigger_count(self):
        return self._thor_cam.trigger_count
    
    @trigger_count.setter
    def trigger_count(self, count):
        assert isinstance(count, int), "Trigger count should be an int."
        self._thor_cam.set_trigger_count(count)
        self._buffer_size = count
        
    @property
    def buffer_size(self):
        return self._buffer_size
    
    @buffer_size.setter
    def buffer_size(self, size:int):
        size = int(size)
        if size < 1:
            size = 50
        self._buffer_size = size
        
    @property
    def store_full_image(self):
        return self._store_full_image
    
    @store_full_image.setter
    def store_full_image(self, flag:bool):
        self._store_full_image = flag
    
    #%% CCD Image
    @property
    def ccd_image(self):
        return self._image_buffer
    
    @ccd_image.setter
    def ccd_image(self, image):
        self._image_buffer = image
        
    #%%
    def _getAllParams(self):
        param_list = ["BUFF", self.buffer_size,
                      "SIZE", self.sensor_size,
                      "EXPT", self.exposure_time,
                      "GAIN", self.gain,
                      "ACQM", self.acquisition_mode,
                      "NTRG", self.trigger_count]
        
        return param_list
    
    #%% Thread
    def _get_ccd_image(self):
        while self._thor_cam.is_running():
            raw_data = self._thor_cam.read_frame()
            if raw_data == None:
                continue
            self._img_cnt += 1
            data_int = raw_data[0].astype(np.int16)
            data_arr = data_int.reshape(raw_data[2], order='F')
            
            self.ccd_image = np.copy(data_arr)
            
            if not self.data_p == None:
                processed_data = self.parent.processData(data_arr) # This is a bad design.... 
                
                if ( ( (self.parent.roi_dict["x"][1] - self.parent.roi_dict["x"][0]) *
                      (self.parent.roi_dict["y"][1] - self.parent.roi_dict["y"][0]) ) > 696800):
                    self._half_period_flag = not self._half_period_flag
                else: self._half_period_flag = True
                
                if self._half_period_flag:
                
                    processed_data = self.parent.processData(data_arr) # This is a bad design.... 
                    raw_min = np.min(processed_data)
                    raw_max = np.max(processed_data)
                    
                    self.data_p.send([raw_min, raw_max, processed_data])
                    if not self._store_full_image:
                        data_arr = processed_data
            # print('list_len:{} / buffer size: {}'.format(len(self._buffer_list), self._buffer_size))
            if len(self._buffer_list) > self._buffer_size:
                while (len(self._buffer_list) >= self._buffer_size):
                    self._buffer_list.pop(0)
                    # print('popped')
            self._buffer_list.append(data_arr)
            
            if self._acquisition_mode == 'single_scan':
                if self._img_cnt == self.trigger_count:
                    self._thor_cam.stop_camera()
                    self._img_cnt = 0
                    # self.data_p.send([-1, -1, []])
            

if __name__ == "__main__":
    CCD = CCD_controller()