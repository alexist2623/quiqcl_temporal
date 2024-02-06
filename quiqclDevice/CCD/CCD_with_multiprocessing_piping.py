# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 20:24:45 2022

@author: QCP32
"""
import numpy as np
from multiprocessing import Process, Pipe
from threading import Thread
from PIL import Image
import os, sys

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

class CameraHandler(Process):
    
    def __init__(self, result_p=None, data_p=None, ccd_type="Dummy"):
        super().__init__()
        self.result_p = result_p # gives the result to it
        self.data_p = data_p # It handles image data only
                
        self.roi_dict = {"x": [0, 1040], "y": [0, 1392]}
        self.flip_dict = {"v": False, "h": False}
        self.pooling_step = 2
        
        self.cam = None
        self.ccd_type = ccd_type
        
        self.device_running = False
        self.loop_flag = True
        self.record_full_image = True
        self.max_buffer_length = 50
        
        self.dirname = dirname
        
        
    def openDevice(self, ccd_type="CCD"):
        try:
            sys.path.append(self.dirname)
            if ccd_type == "Thorcam":
                sys.path.append(self.dirname + '/Thorcam/') 
                from Thorcam_controller import CCD_controller
                
            elif ccd_type == "EMCCD":
                pass
                
            elif ccd_type == "Dummy":
                sys.path.append(self.dirname + '/Dummy/') 
                from Dummy_CCD_w_pipe import CCD_controller
                
            else:
                raise ValueError ("You should specify the ccd type which is one of 'CCD', 'EMCCD' or 'DUMMY'.")
                self.result_p.send(["E", "OPEN", ["You should specify the ccd type which is one of 'CCD' or 'EMCCD.'"]])
            self.cam = CCD_controller(data_p=self.data_p, parent=self)
            
            self.cam.openDevice()
            self._device_opened = True
            self.result_p.send(["D", "OPEN", []])
        except Exception as err:
            print(err)
            self.result_p.send(["E", "OPEN", [err]])
        
        
    def setROI(self, roi_axis:list, roi_range:list):
        if not isinstance(roi_axis, list):
            raise ValueError ("The roi_axis must be a list.")
        if not isinstance(roi_range, list):
            raise ValueError ("The roi_range must be a list.")
            
        for idx, axis in enumerate(roi_axis):
            if not axis in ["x", "y"]:
                raise ValueError ("The roi_axis must be 'x' or 'y'.")
                
            self.roi_dict[axis] = roi_range[idx]
        
    def setPoolingStep(self, step):
        if not step in [2, 4]:
            raise ValueError ("The pooling step must be bettwen 2 or 4.")
        else:
            self.pooling_step = step
            
    def setFlip(self, flip_axis:list, flip_flag:list):
        if not isinstance(flip_axis, list):
            flip_axis = [flip_axis]
        if not isinstance(flip_flag, list):
            flip_flag = [flip_flag]
            
        temp_zip = zip(flip_axis, flip_flag)
        
        for axis, flag in temp_zip:
            if not axis in ["x", "y", "h", "v"]:
                raise ValueError ("The flip axis must be one of 'h', 'v', 'x', and 'y'.")
                return 
            
            if axis == "x":
                axis = "h"
            if axis == "y":
                axis = "v"
            self.flip_dict[axis] = flag
        
    def processData(self, data):
        processed_image = data[self.roi_dict["y"][0]:self.roi_dict["y"][1], 
                               self.roi_dict["x"][0]:self.roi_dict["x"][1]]
        if self.flip_dict["h"]:
            processed_image = np.flip(processed_image, 1)
        if self.flip_dict["v"]:
            processed_image = np.flip(processed_image, 0)
        
        return processed_image
    
    
    def saveImage(self, save_name="default", tif_flag=True, full_flag=True):
        if os.path.exists(save_name):
            extention = save_name[-3:]
            file_name = save_name[:-4]
            
            file_name += "_%03d"
            idx = 0
            save_name = file_name + "." + extention
            while os.path.exists(save_name % idx):
                idx += 1
            save_name = save_name % idx
    
        if tif_flag:
            save_thread = Thread(target=self._saveTIF, args=(save_name, full_flag, ))
            save_thread.start()
        
        else:
            save_thread = Thread(target=self._savePNG, args=(save_name, full_flag, ))
            save_thread.start()
        
        
    def _savePNG(self, save_name, full_flag):
        png_arr = np.uint16(65535*((self.cam.ccd_image - np.min(self.cam.ccd_image))/np.ptp(self.cam.ccd_image)))
        if not full_flag:
            png_arr = png_arr[self.roi_dict["y"][0]:self.roi_dict["y"][1],
                              self.roi_dict["x"][0]:self.roi_dict["x"][1]]
        
        img = Image.fromarray(png_arr)
        img.save(save_name, format="PNG")
        print("Saved %s" % save_name)
        
    def _saveTIF(self, save_name, full_flag):
        if self.cam.trigger_count == 1:
            if not full_flag:
                ccd_image = self.cam.ccd_image[self.roi_dict["y"][0]:self.roi_dict["y"][1],
                                               self.roi_dict["x"][0]:self.roi_dict["x"][1]]
            else:
                ccd_image = self.cam.ccd_image
            
            im = Image.fromarray(ccd_image)
            
            im.save(save_name, format='tiff')
        
        else:
           
            cam_image = np.asarray(self.cam._buffer_list).astype(np.int16)
            
            if not full_flag:
                cam_image = cam_image[:, 
                                   self.roi_dict["y"][0]:self.roi_dict["y"][1],
                                   self.roi_dict["x"][0]:self.roi_dict["x"][1]]
            im_arr = []

            for arr in cam_image:
                im_arr.append( Image.fromarray(arr) )
                
            im_arr[0].save(save_name, format="tiff", save_all=True, append_images=im_arr[1:])

    def run(self):
        while self.loop_flag:
            work = self.result_p.recv()
            work_type, cmd, data = work
            
            if work_type == "C":
                if cmd == "OPEN":
                    self.openDevice(self.ccd_type)
                
                elif cmd == "ROI":
                    roi_axis, roi_range = data
                    self.setROI(roi_axis, roi_range)
                    self.result_p.send(["D", "ROI", self.dictToList(self.roi_dict)])
                    
                elif cmd == "FLIP":
                    flip_axis, flip_flag = data
                    self.setFlip(flip_axis, flip_flag)
                    self.result_p.send(["D", "FLIP", self.dictToList(self.flip_dict)])
                    
                elif cmd == "GAIN":
                    self.cam.gain = data[0]
                    self.result_p.send(["D", "GAIN", [self.cam.gain]])
                    
                elif cmd == "EXPT": # exposure_time
                    self.cam.exposure_time = data[0]
                    self.result_p.send(["D", "EXPT", [self.cam.exposure_time]])
                    
                elif cmd == "ACQM": # acqusition_mode
                    self.cam.acquisition_mode = data[0]
                    self.result_p.send(["D", "ACQM", [self.cam.acquisition_mode]])
                    
                elif cmd == "NTRG": # number of trigger
                    self.cam.trigger_count = data[0]
                    self.result_p.send(["D", "NTRG", [self.cam.trigger_count]])
    
                elif cmd == "RUN":
                    self.cam.startAcquisition()
                    self.result_p.send(["D", "RUN", [self.cam._running_flag]])
                    
                elif cmd == "STOP":
                    self.cam.stopAcquisition()
                    self.result_p.send(["D", "RUN", [self.cam._running_flag]])
                    
                elif cmd == "BUFF": # changes the buffer size
                    self.cam.buffer_size = data[0]
                    self.result_p.send(["D", "BUFF", [self.cam.buffer_size]])
                    
                elif cmd == "FULL":
                    self.cam.store_full_image = data[0]
                    self.result_p.send(["D", "FULL", [self.cam.store_full_image]])
                    
                elif cmd == "SAVE":
                    file_name, tif_flag, full_flag = data
                    print("file_name", file_name)
                    self.saveImage(file_name, tif_flag, full_flag)
                    self.result_p.send(["D", "SAVE", [filename, tif_flag, full_flag]])

                else:
                    self.result_p.send(["E", "CMD", ["An unknown command (%s)" % cmd]])
            
            elif work_type == "Q":
                if cmd == "ROI":
                    self.result_p.send(["A", "ROI", self.dictToList(self.roi_dict)])
                    
                elif cmd == "FLIP":
                    self.result_p.send(["A", "FLIP", self.dictToList(self.flip_dict)])
                    
                elif cmd == "GAIN":
                    self.result_p.send(["A", "GAIN", [self.cam.gain]])
                    
                elif cmd == "EXPT":
                    self.result_p.send(["A", "EXPT", [self.cam.exposure_time]])
                    
                elif cmd == "ACQM":
                    self.result_p.send(["A", "ACQM", [self.cam.acqusition_mode]])
                    
                elif cmd == "NTRG":
                    self.result_p.send(["A", "NTRG", [self.cam.trigger_count]])
                    
                elif cmd == "RUN":
                    self.result_p.send(["A", "RUN", [self.cam._running_flag]])
                    
                elif cmd == "BUFF":
                    self.result_p.send(["A", "BUFF", [self.cam.buffer_size]])
                    
                elif cmd == "FULL":
                    self.result_p.send(["A", "FULL", [self.cam.store_full_image]])
                    
                elif cmd == "PARAM":
                    self.result_p.send(["A", "PARAM", self.cam._getAllParams()])
                    
                else:
                    self.result_p.send(["E", "CMD", ["An unknown command (%s)" % cmd]])
            
            else:
                self.result_p.send(["E", "TYPE", ["An unknown command type (%s)" % work_type]])
                
                    
    def dictToList(self, dict):
        return_list = []
        for key, val in dict.items():
            return_list.append(key)
            return_list.append(val)
        return return_list
            
            
    def average_pooling(self, array):
        x, y = array.shape
        new_x, new_y = x//self.pooling_step, y//self.pooling_step
        array = np.mean(array.reshape(new_x, self.pooling_step, new_y, self.pooling_step), axis = (1, 3))
        return array.astype(np.uint16)
    
    def maximum_pooling(self, array):
        x, y = array.shape
        new_x, new_y = x//self.pooling_step, y//self.pooling_step
        array = np.max(array.reshape(new_x, self.pooling_step, new_y, self.pooling_step), axis = (1, 3))
        return array.astype(np.uint16)
        
    
if __name__ == "__main__":
    user_cmd_p, ccd_cmd_p = Pipe()
    user_data_p, ccd_data_p = Pipe()
    # redundant_p.close() # It reads data only
    ch = CameraHandler(ccd_cmd_p, ccd_data_p, "Thorcam")
    ch.start()
    print(dirname)
    
    # user_cmd_p.send(["C", "OPEN", []])
    # user_cmd_p.send(["C", "RUN", []])
    # user_cmd_p.send(["C", "STOP", []])