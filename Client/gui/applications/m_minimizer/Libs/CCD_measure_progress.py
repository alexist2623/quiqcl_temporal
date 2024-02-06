# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 19:40:03 2022

@author: QCP32
"""
from PyQt5.QtCore import QObject
import time
import numpy as np
from scipy.optimize import curve_fit

def Gaussian_2D_elliptic(idx_arr, x_0, y_0, A, B, a, b, c):
    x, y = idx_arr
    result = A*np.exp(-(a*(x-x_0)**2 + 2*b*(x-x_0)*(y-y_0) + c*(y-y_0)**2)) + B
    return result.flatten()


class CCD_measure(QObject):
    
    ccd_cnt = 0
    ccd_data_list = []
    ccd_buffer = None
    
    rf_row = -9.17
    rf_high = -8.06
    
    def __init__(self, CCD, MIRROR, RF, status_signal, parent):
        super().__init__()
        
        self.ccd = CCD
        self.mirror = MIRROR
        self.rf_socket = RF
        self.parent = parent
        
        self._status_signal = status_signal
        
        self._direction = "LEFT"
        self.ccd.image_thread._img_recv_signal.connect(self._recievedCCD_Data)
        self.status = "standby"
        self.rf_status= "low"
        
        self.ccd_image_fit_img = [None, None]
        self.ccd_image_fit_data = [None, None]
        self.ccd_delta = None
        
    def changeRFVoltage(self, output_port=0, voltage=0):
        if output_port == 0 or output_port == "BNC":
            port = "AMPL"
        elif output_port == 1 or output_port == "N-Type":
            port = "AMPR"
        # else:
        #     self.toStatusBar("Couldn't match the output port (%s)." % str(output_port))
            return
        #VPP?
        if voltage < self.rf_low:
            voltage = self.rf_low
            # self.toStatusBar("The setted voltage is lower than the minimum. set to minimum.")
        if voltage > self.rf_high:
            voltage = self.rf_high
            # self.toStatusBar("The setted voltage is higher than the maxmimum. set to maximum.")    
            
        self.rf_socket.send("%s %.2f\r\n".encode() % (port, voltage))
            

    def setRFvalue(self, key, value):
        if key == "low":
            self.rf_low = value
        elif key == "high":
            self.rf_high = value
        # else:
        #     self.toStatusBar("Couldn't set the RF value. (key=%s)" % key)
        
    def setTurnDirection(self, direction):
        self._mirror_direction = direction
        
    def setMirrorNum(self, number):
        self._mirror_number = number
        
    def measure(self, scan_length=10, exposure_time=300):

        try:
            self.mirror.sendall(bytes("MIRROR:%d:TURN:%s\n" % (self._mirror_number, self._mirror_direction), "latin-1"))
            time.sleep(0.2)
            response =  self.mirror.recv(1024).decode('latin-1')
            time.sleep(0.2)
        except:
            self._status_signal.emit("CCD:BROKEN:MIRROR")
            return
        self._status_signal.emit("CCD:SET:MIRROR")
        time.sleep(0.5)
        
        self.rf_status = "low"
        self._measureCCD(scan_length=10, exposure_time=3000)
        

    def _measureCCD(self,  scan_length=10, exposure_time=3000):
        if self.rf_status == "low":
            rf_value = self.rf_low
        else:
            rf_value = self.rf_high
            
        try:
            self.changeRFVoltage(0, rf_value)
        except:
            self._status_signal.emit("CCD:BROKEN:RF")
            return
        self._status_signal.emit("CCD:SET:MIRROR")
        time.sleep(0.1)
        
        # reset ccd settings
        self.ccd_cnt = 0
        self.ccd_data_list = []
        
        self.ccd.setTriggerCount(scan_length)
        self.ccd.setExposureTime(exposure_time)
        
        self.status = "waiting_ccd"
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
        self._status_signal.emit("CCD:MEASURING")
    

    def _recievedCCD_Data(self, raw_min, raw_max):
        if self.status == "waiting_ccd":
            
            self.ccd_cnt += 1
            self.ccd_data_list.append(self.ccd.image_thread.image_buffer)
            
            if self.ccd_cnt == 10:
                self.ccd_buffer = np.average(self.ccd_data_list, 0)
                if not self.ccd.gui == None:
                    if self.ccd.gui.BTN_acquisition.isChecked():
                        self.ccd.gui.BTN_acquisition.setChecked(False)
                
                self.status = "standby"
                
                if self.rf_status == "low":
                    self.rf_status = "high"
                    
                    low_popt = self._fit2D_Image(im_array=self.ccd_buffer)
                    self.ccd_image_fit_data[0] = low_popt
                    self.ccd_image_fit_img[0]  = self._getFitImage(np.shape(self.ccd_buffer), *low_popt)
                    
                    self._measureCCD()
                
                else:
                    high_popt = self._fit2D_Image(im_array=self.ccd_buffer)
                    self.ccd_image_fit_data[1] = high_popt
                    self.ccd_image_fit_img[1]  = self._getFitImage(np.shape(self.ccd_buffer), *high_popt)
                    
                    self.ccd_delta = np.sqrt( np.diff(self.ccd_image_fit_data[0][0],  self.ccd_image_fit_data[1][0])**2  + np.diff(self.ccd_image_fit_data[0][1],  self.ccd_image_fit_data[1][1])**2)
                    
                    
                    self._status_signal.emit("CCD:DONE")
                
    def _fit2D_Image(self, im_array, guess_a = 0.3, guess_b = 0.001, guess_c = 0.3):
        
        guess_y, guess_x = np.unravel_index(np.argmax(im_array), im_array.shape)
        
        guess_B = np.min(im_array)
        guess_A = np.max(im_array) - guess_B
            
        arr_x = np.arange(im_array.shape[0])
        arr_y = np.arange(im_array.shape[1])
        
        
        popt, pcov = curve_fit(Gaussian_2D_elliptic, 
                               np.meshgrid(arr_x, arr_y),
                               im_array.flatten(),
                               p0 = [guess_x, guess_y, guess_A, guess_B, guess_a, guess_b, guess_c])
        
        
        return popt, pcov
        
    def _getFitImage(self, array_shape, *popt):
        x, y = np.arange(array_shape[0]), np.arange(array_shape[1])
        im_array = np.meshgrid(x, y)
        fit_image = Gaussian_2D_elliptic(im_array, *popt)
        return fit_image
    
    # def toStatusBar(self, msg):
    #     if self.parent == None:
    #         print(msg)
    #     else:
    #         self.parent.toStautsBar(msg)
