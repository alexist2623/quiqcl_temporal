# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 14:53:31 2022

@author: QCP32
"""
from PyQt5.QtCore import QObject, pyqtSignal, QWaitCondition, QMutex
from queue import Queue

from CCD_measure_progress import CCD_measure
from PMT_meausre_progress import PMT_measure

class env(QObject):
    
    measure_done = pyqtSignal(bool)
    status_signal = pyqtSignal(str)
    
    def __init__(self, device_dict={}, parent=None):
        super().__init__()
        
        self.parent = parent
        self.ccd = device_dict["ccd"]
        self.dac = device_dict["dac"]
        self.sequencer = device_dict["sequencer"]
        # self.rf = device_dict["rf"]
        
        self.MIRROR = self.device_dict["MIRROR"]
        self.SCAN = self.device_dict["SCAN"]
        self.user_name = self.device_dict["user_name"]
        
        
        self.ccd_measure = CCD_measure(self.ccd, self.MIRROR, self.status_signal)
        self.pmt_measure = PMT_measure(self.status_signal)
        
        
        self.status_signal.connect(self._receieved_status_signal)
        
        self.measurement_order = ["CCD", "PMT"]
        
        self._running_flag = False
        self._status = "standby"
        
        self.cond = QWaitCondition()
        self.mutex = QMutex()

    def observe(self):
        if not self.isRunning():
            self._running_flag = True
            self.start()
            
    def run(self):
        while self._running_flag:
            for device in self.measurement_order:
                if self._running_flag:
                    self.mutex.lock()
                    self.performMeasurement(device)
                    self.cond.wait(self.mutex)
                    self.mutex.unlock()
            
        self.measure_done.emit()
        
    def setDeviceMeasurements(self, device_list:list):
        self.measurement_order = device_list
        
    def performMeasurement(self, device):
        self._status = device
        
        if device == "CCD":
            self.ccd_measure.measure()
            
        elif device == "PMT":
            self.pmt_measure.measure()
        

    @property
    def status(self):
        return self._status
    
    def wakeupCondition(self, device):
        print(device)
        self.cond.wakeAll()

    def _receieved_status_signal(self, status):
        pass
      
    #%% DAC
    def shiftDC(self, axis, value):
        #axis 0 = asym, axis_1 = x, axis_2 = y, axis_3 = z
        self.sft_scroll_list[axis+1].setValue(-value)