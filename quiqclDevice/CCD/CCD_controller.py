# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 22:52:01 2021

@author: CPO
v1.01: read a config file. compatible with EMCCD
v2.01: Multirprocessing handles the device.
"""
debug = True

import os
os.system('CLS')
import matplotlib.pyplot as plt

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
import time
import numpy as np
from datetime import datetime
from configparser import ConfigParser
from multiprocessing import Pipe

from CCD_with_multiprocessing_piping import CameraHandler

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

        
    
class CCD_Interface(QThread):
    
    _sig_closed = pyqtSignal()
    _sig_update_callback = pyqtSignal(str)
    _sig_im_size_changed = pyqtSignal(int, int)
    _device_opened = False
    _gui_opened = False
    _status = "standby"
    _param_dict = {}
    _camera_type = "Dummy"

    def __init__(self, socket=None, gui=None, debug=False):
        super().__init__()
        self.sc = socket
        self.gui = gui
        self.que = Queue()
        self.debug = debug
                
        # self._readConfig(os.getenv('COMPUTERNAME', 'defaultValue'))
        if not debug:
            self._camera_type = self.sc.cp.get("device", "ccd")
        self.toWorkList(["C", "OPEN", []])
                
    def closeDevice(self):
        if self._device_opened:
            resp = self._sendCommand_n_GetResponse("STOP", [])
            print(resp)
            self.oc.close_oven()
            self.cam._loop_flag = False
            while True:
                self.cam.join()
                
            self.cam.terminate()
            
        # self.cam = None
        self._device_opened = False
        self._sig_closed.emit()
        self.toStatusBar("Closed the device.")
        
    def openGui(self):
        from CCD_GUI_v2_02 import CCD_UI
        self.gui = CCD_UI(self, self.sc.gui._theme)
        self._gui_opened = True

    def openDevice(self):
        if not self._device_opened:
            
            self.user_cmd_p, self.ccd_cmd_p = Pipe()
            self.user_data_p, self.ccd_data_p = Pipe()
            
            self.cam = CameraHandler(self.ccd_cmd_p, self.ccd_data_p, self._camera_type)
            self.image_thread = CCD_ImageHandler(self, self.user_data_p)
            
            # self.oc = Oven_controller(self)
            self.cam.start()
            resp = self._sendCommand_n_GetResponse("OPEN", [])
            if (resp[1] == "OPEN"):
                self._device_opened = True
                self.toStatusBar("The CCD is successfully opened.")
                
                self._initParams()
                self.setROI(["x", "y"], [[0, self._param_dict["SIZE"][1]], [0, self._param_dict["SIZE"][0]]])
                print("initial parameters are set.")
                
            else:
                self.cam.terminate()
                self.toStatusBar("An error while opening the device. Try again in a few minutes.")
                
                
        else:
            self.toStatusBar("An error while opening the device. Try again in a few minutes.")
        
    def setROI(self, axes_list, value_list):
        self._sendCommand_n_GetResponse("ROI", [axes_list, value_list])
        
    def setGain(self, gain):
        self._sendCommand_n_GetResponse("GAIN", [gain])
        
    def setExposureTime(self, exposure_time):
        self._sendCommand_n_GetResponse("EXPT", [exposure_time])
        
    def setFlip(self, flip_list):
        flip_axes, flip_flags = flip_list
        self._sendCommand_n_GetResponse("FLIP", [flip_axes, flip_flags])
        
    def setAcquisitionMode(self, acq_mode):
        if not acq_mode in ["continuous_scan", "single_scan"]:
            raise ValueError ("The acquisition mode must be either 'continuous_scan' or 'single_scan'.")
        else:
            self._sendCommand_n_GetResponse("ACQM", [acq_mode])
            
    def setTriggerCount(self, trigger_count):
        trigger_count = int(trigger_count)
        self._sendCommand_n_GetResponse("NTRG", [trigger_count])
            
        
    def startAcquisition(self, acq_flag):
        if acq_flag:
            self._sendCommand_n_GetResponse("RUN", [])
            self.image_thread.running_flag = True
            if not self.image_thread.isRunning():    
                self.image_thread.start()
            
        else:
            self._sendCommand_n_GetResponse("STOP", [])
            self.image_thread.running_flag = False
            
    def saveImages(self, save_name, tif_flag = True, full_flag=True):
        self._sendCommand_n_GetResponse("SAVE", [save_name, tif_flag, full_flag])
        
    def toWorkList(self, cmd):         
        self.que.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started")

    def run(self):
        while True:
            work = self.que.get()
            self._status  = "running"
            # decompose the job
            work_type, command, data = work
    
            if work_type == "C":
                if command == "HELO":
                    """
                    Successfully received a response from the server
                    """
                    self._is_opened = True
                    
                elif command == "OPEN":
                    self.openDevice()
                    
                elif command == "CLOSE":
                    self.closeDevice()
                
                elif command == "ROI":
                    axes_list, value_list = data
                    self.setROI(axes_list, value_list)
                    
                elif command == "GAIN":
                    self.setGain(data[0])
                    
                elif command == "EXPT":
                    self.setExposureTime(data[0])
                    
                elif command == "RUN":
                    self.startAcquisition(True)
                    
                elif command == "STOP":
                    self.startAcquisition(False)
                    
                elif command == "FLIP":
                    self.setFlip(data)
                    
                elif command == "ACQM":
                    self.setAcquisitionMode(data[0])
                    
                elif command == "NTRG":
                    self.setTriggerCount(data[0])
                    
                elif command == "SAVE":
                    self.saveImages(data[0], data[1], data[2])
                    
                else:
                    self.toStatusBar("An unknown command has been detected (%s)." % command)
                    
            elif work_type == "Q":
                if command == "ROI":
                    self._sendQuery_n_GetResponse("ROI", [])
                    
                elif command == "GAIN":
                    self._sendQuery_n_GetResponse("GAIN", [])
                    
                elif command == "RUN":
                    self._sendQuery_n_GetResponse("RUN", [])
                    
                elif command == "EXPT":
                    self._sendQuery_n_GetResponse("EXPT", [])
                    
                elif command == "PARAM":
                    self._sendQuery_n_GetResponse("PARAM", [])
                    
                elif command == "ACQM":
                    self._sendQuery_n_GetResponse("ACQM", [])
                    
                elif command == "NTRG":
                    self._sendQuery_n_GetResponse("NTRG", [])
                
                else:
                    self.toStatusBar("An unknown command has been detected (%s)." % command)
                
            else:
                self.toStatusBar("An unknown command type has been detected (%s)." % work_type)
                
    def _initParams(self):
        response = self._sendQuery_n_GetResponse("PARAM", [])
        if not response[0] == "A":
            self.toStatusBar("An error occured while getting the initial parameters. (%s)")
        
        else:
            data = response[-1]
            
            options = data[0::2]
            values = data[1::2]
            
            self.updateParams(options, values)
                
    def _readConfig(self, pc_name):
        conf_file = dirname + '/config/%s.conf' % pc_name
        if not os.path.isfile(conf_file):
            print("No config file has been found.")
            return
        
        cp = ConfigParser()
        cp.read(conf_file)
        self._camera_type = cp.get('device', 'type')
        self._theme = cp.get('ui', 'theme')
        try:
            self._available_ccd = cp.get("server", 'avails').replace(' ', '').split(',')
        except:
            self._available_ccd = [pc_name]

    def _sendCommand_n_GetResponse(self, command, data):
        
        self.user_cmd_p.send(["C", command, data])
        
        response = self.user_cmd_p.recv()
        
        command, data = response[1:]

        if command == "OPEN":
            self._param_dict["OPEN"] = 1
        elif command == "CLOSE":
            self._param_dict["OPEN"] = 0
        elif command == "RUN":
            self._param_dict["RUN"] = 1
        elif command == "STOP":
            self._param_dict["RUN"] = 0
        elif command == "ROI":
            self._sig_im_size_changed.emit( (data[1][1] - data[1][0]), (data[3][1] - data[3][0]) )
        else:
            self._param_dict[command] = data[0]
        
        if self.debug:
            print(response)
            
        return response
        
    
    def _sendQuery_n_GetResponse(self, command, data):
        self.user_cmd_p.send(["Q", command, data])
        response = self.user_cmd_p.recv()
        if self.debug:
            print(response)
        
        _, command, data = response
        self.updateParams(command, data)
        return response
    
    def toStatusBar(self, msg):
        if self.gui == None:
            print(msg)
        else:
            self.gui.toStatusBar(msg)
            
    def updateParams(self, param_key, param_val):
        if not isinstance(param_key, list):
            param_key = [param_key]
        if not isinstance(param_val, list):
            param_val = [param_val]
            
        temp_zip = zip(param_key, param_val)
        for param_key, param_val in temp_zip:
            self._param_dict[param_key] = param_val
        
        self._sig_update_callback.emit(param_key)
            
            
        
class CCD_ImageHandler(QThread):
    
    _img_recv_signal = pyqtSignal(int, int)
    _status = "standby"
    
    def __init__(self, parent, data_p):
        super().__init__()
        self.controller = parent
        self.data_p = data_p
        
        self.running_flag = False
        
        self.image_buffer = np.random.random((1340, 1040))
        self.image_datetime = datetime.now()
        self.raw_min = 0
        self.raw_max = 0
               
        
    def run(self):
        while self.running_flag:
            self._status = "receieving"
            raw_min, raw_max, image_buffer = self.data_p.recv()
            
            self.raw_min, self.raw_max, self.image_buffer = raw_min, raw_max, image_buffer[::-1]

            self._img_recv_signal.emit(self.raw_min, self.raw_max)
            self._status = "standby"

                
class Cooling_Thread(QThread):
    
    def __init__(self, parent):
        super().__init__()
        self.GUI = parent
        self.cam = self.GUI.cam
        self.running_flag = False
        
    def run(self):
        while self.running_flag:
            if self.cam._cool_status == "cooling":
                self.GUI.LBL_temp.setStyleSheet(self.GUI._emccd_cooler_theme[self.GUI._theme]["red"])
            elif self.cam._cool_status == "stabilized":
                self.GUI.LBL_temp.setStyleSheet(self.GUI._emccd_cooler_theme[self.GUI._theme]["blue"])
                
            self.GUI.LBL_temp.setText(str(self.cam.temperature))
            time.sleep(3)
            if not self.GUI.BTN_acquisition.isChecked():
                self.GUI.update()


if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    CCD = CCD_Interface(debug=debug)
    CCD.start()
    
    time.sleep(0.2)
    # CCD.toWorkList(["C", "OPEN", []])

# CCD.openGui()
# CCD.gui.show()
# CCD.toWorkList(["C", "ROI", [["x", "y"], [[40, 80], [40, 80]]]])
# CCD.toWorkList(["C", "ROI", [["y"], [[40, 80]]]])
# CCD.toWorkList(["C", "RUN", []])
# CCD.toWorkList(["C", "STOP", []])