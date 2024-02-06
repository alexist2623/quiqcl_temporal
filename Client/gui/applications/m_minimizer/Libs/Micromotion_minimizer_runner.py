# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:10:25 2022

@author: QCP32
"""
from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
from queue import Queue
import time
import numpy as np
import socket, os
from scipy.optimize import curve_fit

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
version = "0.1"

def corr_func(x, a, b, c):
    return a*np.cos(x+b)+c

class MicromotionRunner(QThread):
    
    measure_done = pyqtSignal(str)
    stopped_run = pyqtSignal()
    
    _status = "standby"
    
    def __init__(self, device_dict={}, parent=None):
        super().__init__()
        
        # self.rf = socket.
        
        self.gui = parent
        self.ccd = device_dict["ccd"]
        self.dac = device_dict["dac"]
        self.sequencer = device_dict["sequencer"]
        
        self.rf_min = 0.22
        self.rf_max = 0.26
        
        # self.rf = device_dict["rf"]
        
        # This is a bad
        self.MIRROR = self.gui.parent.panel_dict["measure_panel"].MFF
        self.SCAN = self.gui.parent.application_dict["pmt_aligner"].pmt_aligner_gui.scanner
        self.user_name = self.gui.parent.parent.user_name
        
        # no need?
        self.queue = Queue()
        
        #Running
        self.running_flag = False
        
        self.ccd.image_thread._img_recv_signal.connect(self._recieved_CCD_data)
        self.ccd_data_list = []
        
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        
        self.measurement_order = ["CCD", "MIRROR:RIGHT", "SCAN", "RF-Photon", "MIRROR:LEFT"]
        self.measure_done.connect(self.wakeupCondition)
        
        # scan
        self.SCAN.sig_update_plot.connect(self._receieved_scanner_data)
        self.scan_ion_threshold = 5
        
        # sequencer
        self.sequencer.sig_seq_complete.connect(self._completedSequencer)
        
        
    #%% sg
    def connectRF(self, ip="172.22.22.220", port=5025):
        # This is gonna be deprecated
        rf_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rf_socket.connect((ip, port))
        
        self.rf_low = 0.22
        self.rf_high = 0.26
        
        return rf_socket
    
    def changeRFVoltage(self, output_port=0, voltage=0):
        if output_port == 0 or output_port == "BNC":
            port = "AMPL"
        elif output_port == 1 or output_port == "N-Type":
            port = "AMPR"
        else:
            self.toStatusBar("Couldn't match the output port (%s)." % str(output_port))
            return
        
        if voltage < self.rf_low:
            voltage = self.rf_low
            self.toStatusBar("The setted voltage is lower than the minimum. set to minimum.")
        if voltage > self.rf_high:
            voltage = self.rf_high
            self.toStatusBar("The setted voltage is higher than the maxmimum. set to maximum.")    
            
        self.rf_socket.send("%s %.2f\r\n".encode() % (port, voltage))
    
    def getRFFreq(self):
        self.rf_socket.send("FREQ?\r\n".encode())
        
        resp = self.rf_sock.recv(1024)
        rf_freq = float(resp.decode()[:-2])/1000  # convert to kHz
        
        return rf_freq
        

    def setRFvalue(self, key, value):
        if key == "low":
            self.rf_low = value
        elif key == "high":
            self.rf_high = value
        else:
            self.toStatusBar("Couldn't set the RF value. (key=%s)" % key)
            
        
    def setDeviceMeasurements(self, device_list:list):
        self.measurement_order = device_list
        
        
    def run(self):
        while self.running_flag:
            for device in self.measurement_order:
                if self.running_flag:
                    self.mutex.lock()
                    self.performMeasurement(device)
                    self.cond.wait(self.mutex)
                    self.mutex.unlock()
            
            self.agent.something()
                    
        self.stopped_run.emit()
    
    @property
    def status(self):
        return self._status
    
    def wakeupCondition(self, device):
        print(device)
        self.cond.wakeAll()
    
    def performMeasurement(self, device):
        if device == "CCD":
            self.measureCCD()
            
        elif device == "RF-Photon":
            self.measureRF_Photon()
            
        # elif device == "MIRROR:RIGHT":
        #     self.turnMirror("RIGHT")
            
        # elif device == "MIRROR:LEFT":
        #     self.turnMirror("LEFT")
            
        else:
            self.wakeupCondition(device)
    
    
    #%% Meausre CCD
    def measureCCD(self, scan_length=10, exposure_time=3000):
        # reset ccd settings
        self.ccd_cnt = 0        
        self.ccd_data_list = []
        
        self.ccd.setTriggerCount(scan_length)
        
        self.ccd.setExposureTime(exposure_time)
        
        self._status = "waiting_ccd"
        if not self.ccd.gui == None:
            self.ccd.gui.LBL_scan_length.setText("%d" % scan_length)
            self.ccd.gui.CBOX_single_scan.setChecked(True)
            self.ccd.gui.STATUS_exp_time.setText("%.2f" % (exposure_time))
            
            time.sleep(0.2)
            self.ccd.gui.BTN_acquisition.click()
            
        else:
            self.ccd.setAcquisitionMode("single_scan")
            
            time.sleep(0.2)
            self.ccd.startAcqusition(True)
            
        
    def _recieved_CCD_data(self, raw_min, raw_max):
        if self.status == "waiting_ccd":
            self.ccd_cnt += 1
            self.ccd_data_list.append(self.ccd.image_thread.image_buffer)
            
            if self.ccd_cnt == 10:
                self.ccd_buffer = np.average(self.ccd_data_list, 0)
                if not self.ccd.gui == None:
                    if self.ccd.gui.BTN_acquisition.isChecked():
                        self.ccd.gui.BTN_acquisition.setChecked(False)
                
                self.measure_done.emit("CCD")
                
    #%% Sequencer: Measure RF-Photon
    def measureRF_Photon(self):
        self._setSequencerFile()
        self.sequencer.occupant = "mm_runner"
        self.sequencer.sig_occupied.emit(True)
        self.sequencer.runSequencerFile()
        
        
    def _setSequencerFile(self):
        # CHECK FOR SYNTAX
        self.sequencer.loadSequencerFile(seq_file= dirname + "/RF_phase_correlation.py",
                                         replace_dict={13:{"param": "EXPOSURE_TIME_IN_100US", "value": int(self.exposure_time*10)},
                                                       14:{"param": "NUM_REPEAT", "value": self.avg_num}})
        
    def _completedSequencer(self):
        if self.sequencer.occupant == "mm_runner":
            pmt_data = np.asarray(self.sequencer.data[0])
            arrival_time, minmax_normalization = self._sortSequencerData(pmt_data)
            
            self.corr_raw_x_data = np.arange(len(arrival_time))*1.25
            self.corr_raw_y_data = arrival_time
            
            self.corr_fit_x_data, self.corr_fit_y_data = self._fitVisibility()
            
            self.measure_done.emit("RF-Photon")
        
    def _setInterlock(self, occupied_flag):
        if occupied_flag:
            if not self.sequencer.occupant == "mm_runner":
                self._setEnableObjects(False)
        else:
            self._setEnableObjects(True)
                
            
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
        
    #%% Mirror 
    def turnMirror(self, direction=""):
        if not self.MIRROR == None: # this for debuggin.
            if self.user_name == "EA":
                mirror_num = 4
            elif self.user_name == "EC":
                mirror_num = 3
            else:
                mirror_num = 1
                
            self.MIRROR.sendall(bytes("MIRROR:%d:TURN:%s\n" % (mirror_num, direction), "latin-1"))
            time.sleep(0.2)
            response =  self.MIRROR.recv(1024).decode('latin-1')
            time.sleep(0.2)
            
            self.measure_done.emit("MIRROR")
        
    #%% PMT scanner
    def gotoMax(self):
        self.SCAN.BTN_go_to_max.click()

    def _receieved_scanner_data(self):
        if not self.SCAN.scanning_flag == False:
            if np.sum(self.SCAN.image > self.scan_ion_threshold):
                self.measure_done.emit("SCAN")
            else:
                self.running_flag = False
                self.gui.toStatusBar("Ion lost. Stopped running.")
                self.measure_done.emit("SCAN")
                
                
    
        # while self.running_flag:
        #     for device in self.measurement_order:
        #         self.mutex.lock()
        #         self.performMeasurement(device)
        #         self.cond.wait(self.mutex)
        #         self.mutex.unlock()