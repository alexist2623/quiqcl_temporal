# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 22:43:44 2022

@author: QCP32
"""
from PyQt5.QtCore import QObject
import time, os
import numpy as np
from scipy.optimize import curve_fit

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)


def corr_func(x, a, b, c):
    return a*np.cos(x+b)+c

class PMT_measure(QObject):
    
    ccd_cnt = 0
    ccd_data_list = []
    ccd_buffer = None
    
    rf_row = 0.22
    rf_high = 0.26
    
    def __init__(self, SEQUENCER, MIRROR, SCANNER, status_signal, parent):
        super().__init__()
        
        self.sequencer = SEQUENCER
        self.mirror = MIRROR
        self.scanner = SCANNER
        self.parent = parent

        
        self._status_signal = status_signal
        
        self._direction = "RIGHT"
        self.sequencer.sig_seq_complete.connect(self._completedSequencer)

        
        self.status = "standby"
        self.rf_status= "low"
        
        self.ccd_image_fit_img = [None, None]
        self.ccd_image_fit_data = [None, None]
        self.ccd_delta = None

        self.scanner.sig_update_plot.connect(self._completedScanner)
        
        self.rf_freq = 34000
        
        self.ion_threashold = 5
        
    def setRF_freq(self, freq_in_kHz):
        self.rf_freq = freq_in_kHz
        
    #%% Sequencer: Measure RF-Photon
    def measure(self):
        try:
            self.mirror.sendall(bytes("MIRROR:%d:TURN:%s\n" % (self._mirror_number, self._mirror_direction), "latin-1"))
            time.sleep(0.2)
            response =  self.mirror.recv(1024).decode('latin-1')
            time.sleep(0.5)
        except:
            self._status_signal.emit("PMT:BROKEN:MIRROR")
            return
        
        # self.toStatusBar("")
        self.scanner.BTN_start_scanning.click()
        
    def _setSequencerFile(self):
        # CHECK FOR SYNTAX
        self.sequencer.loadSequencerFile(seq_file= dirname + "/RF_phase_correlation.py",
                                         replace_dict={13:{"param": "RF_FREQ", "value": int(self.rf_freq)}})
        
    def _completedSequencer(self):
        if self.sequencer.occupant == "mm_runner":
            pmt_data = np.asarray(self.sequencer.data[0])
            arrival_time, minmax_normalization = self._sortSequencerData(pmt_data)
            
            self.corr_raw_x_data = np.arange(len(arrival_time))*1.25
            self.corr_raw_y_data = arrival_time
            
            self.corr_fit_x_data, self.corr_fit_y_data = self._fitVisibility()
            
            self.sequencer.sig_occupied.emit(False)
            self.status_signal.emit("PMT:DONE")
            
    
    def _completedScanner(self):
        if (self.scaner.scanning_flag == False and self.scanner.user_run_flag == False):
            time.sleep(0.2)
            
            if np.sum(self.scanner.image > self.ion_threashold):
                
                self._setSequencerFile()
                self.sequencer.occupant = "mm_runner"
                self.sequencer.sig_occupied.emit(True)
                self.sequencer.runSequencerFile()
            else:
                self._status_signal.emit("PMT:BROKEN:IONLOSS")

            
            
    def _sortSequencerData(self, data):
        arrival_time = []
        
        for each in data:
            arrival_time += each[0:3]
            
        min_val = min(arrival_time[1:])
        max_val= max(arrival_time[1:])
        
        minmax_normalization = (max_val-min_val)/(max_val+min_val+0.000000001)
                
        return [arrival_time, minmax_normalization]
                
    def _fitVisibility(self):
        x_fit = np.arange(1, len(self.corr_raw_y_data))/len(self.corr_raw_y_data)*2*np.pi
        popt, pcov = curve_fit(corr_func, x_fit, self.corr_raw_y_data[1:len(self.corr_raw_y_data)])
        
        corr_fit_x_data = np.arange(len(self.corr_raw_y_data))[1:len(self.corr_raw_y_data)]*1.25
        corr_fit_y_data = corr_func(x_fit, *popt)
        
        return corr_fit_x_data, corr_fit_y_data
    
    # def toStatusBar(self, msg):
    #     if self.parent == None:
    #         print(msg)
    #     else:
    #         self.parent.toStautsBar(msg)