
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 12:21:02 2020

@author: Created by Jiyong Yu, QUIQCL, CSE department, Seoul Natioanl University, Korea

<Raman beam geometry list>
If you want to add beam geometry in configuration file (ini file), you should follow this rule
1. All geometry values should be seperated with string ', '. For example, beam geometry name list is Double Pass Single beam, 
Double Pass Double beam, ...
2. Feedback direction should be NORMAL or REVERSE (caution: should be uppercase!)
3. Geometry should be SINGLE PASS or DOUBLE PASS (caution: should be uppercase!)

detuning = hyperfine_energy[GHz] + offset[kHz] - N * repetition_rate[MHz]

Sinble beam equation: 2 * (freq_aom1 - freq_aom1') = detuning
Double beam equation: 2 * freq_aom1 - freq_aom2 = detuning

1. Single Pass Double beam
freq_aom2 = (2 * freq_aom1 - detuning)
Typical freq_aom1 is 143.8MHz
In this case, PID feedback direction is positive (NORMAL)
freq_aom1 is fixed frequency (freq_aom2 is feedbacked)

2. Double Pass Single beam
freq_aom1 = -detuning/2 + freq_aom1'
Typical freq_aom1' is 157.4MHz
In this case, PID feedback direction is positive (NORMAL)
freq_aom1' is fixed frequency (freq_aom1 is feedbacked)

3. Double Pass Double beam
freq_aom1 = (detuning + freq_aom2)/2
Typical freq_aom2 is 258MHz
In this case, PID feedback direction is negative (REVERSE)
freq_aom2 is fixed frequency (freq_aom1 is feedbacked)

"""
# Prerequisite module import
import os, sys
filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

new_path_list = []
new_path_list.append(dirname + '\\ui_resources') # For resources_rc.py
# More paths can be added here...
for each_path in new_path_list:
    if not (each_path in sys.path):
        sys.path.append(each_path)
        
import ImportForSpyderAndQt5
from Raman_PID_Controller import Raman_PID_Controller
from Arty_S7_v1_01 import ArtyS7

from PyQt5 import uic
qt_designer_file = dirname + '\\Raman_PID_Controller_GUI.ui'
Ui_QDialog, QtBaseClass = uic.loadUiType(qt_designer_file)
ICON_ON = ":/icons/Toggle_Switch_ON_64x34.png"
ICON_OFF = ":/icons/Toggle_Switch_OFF_64x34.png"

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox

import socket
from shutil import copyfile
import configparser
from code_editor.code_editor_v2_00 import TextEditor
from keyboard import press

import time
from datetime import datetime
import threading
from collections import deque
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
from pandas import DataFrame

class Raman_PID_Controller_GUI(QtWidgets.QDialog, Ui_QDialog):
    def __init__(self, parent=None, connection_callback=None):
        
        # FPGA connect and initialization
        self.fpga = ArtyS7('COM4') 
        self.fpga.print_idn()
        
        dna_string = self.fpga.read_DNA()
        print('FPGA DNA string:', dna_string)
        
        self.PID = Raman_PID_Controller(self.fpga)
    
        # GUI initialization
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.on_pixmap = QtGui.QPixmap(ICON_ON)
        self.on_icon = QtGui.QIcon(self.on_pixmap)

        self.off_pixmap = QtGui.QPixmap(ICON_OFF)
        self.off_icon = QtGui.QIcon(self.off_pixmap)
        
        # configuration setting
        self.config_editor = TextEditor(window_title = 'Config editor')
        config_dir = dirname + '\\config'
        self.config_filename = '%s\\%s.ini' % (config_dir, socket.gethostname())
        self.config_file_label.setText(self.config_filename)
        if not os.path.exists(self.config_filename):
            copyfile('%s\\default.ini' % config_dir, self.config_filename)
            
        self.initUi()    
        self.reload_config()    
        
    def initUi(self):
        # Configuration
        self.config = configparser.ConfigParser()
        self.config.read(self.config_filename)
        
        self.reload_config_button.clicked.connect(self.reload_config)
        self.edit_config_button.clicked.connect(self.edit_config)
        self.save_config_button.clicked.connect(self.save_config)
        
        # Lock Parameter setting        
        self.P_box.returnPressed.connect(lambda: self.PID.comp_set(int(self.P_box.text()), int(self.I_box.text()), int(self.D_box.text())))
        self.I_box.returnPressed.connect(lambda: self.PID.comp_set(int(self.P_box.text()), int(self.I_box.text()), int(self.D_box.text())))
        self.D_box.returnPressed.connect(lambda: self.PID.comp_set(int(self.P_box.text()), int(self.I_box.text()), int(self.D_box.text())))
        
        # Combobox setting
        self.beam_geometry_name_list = self.config['beam_geometry']['name_list'].split(', ')
        self.beam_geometry_fixed_aom_freq_list = self.config['beam_geometry']['fixed_aom_freq_list'].split(', ')
        self.beam_geometry_formula_list = self.config['beam_geometry']['formula_list'].split(', ')
        self.beam_geometry_feedback_direction_list = self.config['beam_geometry']['feedback_direction_list'].split(', ')
        self.beam_geometry_geometry_list = self.config['beam_geometry']['geometry_list'].split(', ')
        
        item_number = len(self.beam_geometry_name_list)
        for i in range(0, item_number): # Combobox initialization
            self.beam_geometry_combobox.insertItem(i, self.beam_geometry_name_list[i])
        
        self.beam_geometry_combobox.setCurrentIndex(item_number) # For detecting index change in reload_config
        self.beam_geometry_combobox.currentIndexChanged.connect(self.feedback_select)
        
        # Manual Lock setting
        self.ADC_read_button.clicked.connect(self.ADC_read)
        self.freq_add_button.clicked.connect(self.freq_add)
        self.freq_substract_button.clicked.connect(self.freq_substract)
        
        # Signal setting
        self.tracking_freq_box.returnPressed.connect(self.freq_apply)
        self.tracking_power_box.returnPressed.connect(lambda: self.PID.set_current(int(self.tracking_power_box.text()), 1, 0))
        self.tracking_phase_box.returnPressed.connect(lambda: self.PID.set_phase(float(self.tracking_phase_box.text()), 1, 0))
        
        self.aom_freq_box.returnPressed.connect(lambda: self.PID.set_frequency(float(self.aom_freq_box.text()), 0, 1))
        self.aom_power_box.returnPressed.connect(lambda: self.PID.set_current(int(self.aom_power_box.text()), 0, 1))
        self.aom_phase_box.returnPressed.connect(lambda: self.PID.set_phase(float(self.aom_phase_box.text()), 0, 1))
        self.tracking_signal_onoff_button.clicked.connect(self.tracking_signal_onoff)
        
        self.aom_signal_onoff_button.clicked.connect(self.aom_signal_onoff)
        
        self.tracking_freq_min = float(self.config['tracking_signal']['tracking_freq_min'])
        self.tracking_freq_max = float(self.config['tracking_signal']['tracking_freq_max'])
        
        # Locking setting
        self.lock_start_button.clicked.connect(self.lock_start)
        self.lock_stop_button.clicked.connect(self.lock_stop)
        self.isLockOn = False
        
        # Offset setting
        self.offset_unit_combobox.insertItem(0, 'Hz')
        self.offset_unit_combobox.insertItem(1, 'kHz')
        self.offset_unit_combobox.insertItem(2, 'MHz')
        
        self.offset_spinbox.valueChanged.connect(self.offset_apply)
        self.offset_step_size_box.returnPressed.connect(self.offset_step_size_apply)
        
        self.offset = self.offset_spinbox.value()
        
        # Data plot setting
        self.data_plot_button.clicked.connect(self.data_plot)
        self.tracking_signal_queue = deque([])
        self.aom_signal_queue = deque([])
        self.adc_queue = deque([])
        self.sampling_time = 0.2 # second
        self.measure_time = 1 # minute
        self.max_data_length = int((self.measure_time * 60) / self.sampling_time)
        
        # Default setting for PID controller
        self.PID.adc_range_select() # Vref = 4.096V, range is -2.5 * Vref ~ 2.5 * Vref
        self.PID.user_sampling() # user sampling frequency is 20kHz (Alterable in Verilog)

        self.tracking_signal_on = False
        self.aom_signal_on = False
        self.PID.power_down(1, 1) # initially all rf signal off for safety
        
        self.hyperfine_energy = float(self.config['Raman_parameter']['hyperfine_energy']) # ~12.6GHz
        self.offset_frequency = float(self.config['Raman_parameter']['offset_frequency']) # ~4.6kHz
        self.N = int(self.config['Raman_parameter']['N']) # typically 104 or 105
        
        # Color setting
        self.lock_start_button.setStyleSheet("background-color: #008000") # green
            

    #########################################################################################################################
    ## Configuration
    #########################################################################################################################
        
    def reload_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_filename)
        
        # PID configuration
        P_saved = int(self.config['PID']['P_saved'])
        I_saved = int(self.config['PID']['I_saved'])
        D_saved = int(self.config['PID']['D_saved'])
        
        self.P_box.setText("%d" % P_saved)
        self.I_box.setText("%d" % I_saved)
        self.D_box.setText("%d" % D_saved)
        
        self.PID.comp_set(P_saved, I_saved, D_saved)

        # Beam geometry configuration
        geometry_index_saved = int(self.config['beam_geometry']['index_saved'])
        self.beam_geometry_combobox.setCurrentIndex(geometry_index_saved)
                
        # Signal configuration
        # Tracking signal
        tracking_freq_saved = float(self.config['tracking_signal']['tracking_freq_saved'])
        tracking_power_saved = int(self.config['tracking_signal']['tracking_power_saved'])
        tracking_phase_saved = int(self.config['tracking_signal']['tracking_phase_saved'])
        
        self.tracking_freq_box.setText("%.6f" % tracking_freq_saved)
        self.tracking_power_box.setText("%d" % tracking_power_saved)
        self.tracking_phase_box.setText("%d" % tracking_phase_saved)
        
        # self.PID.set_frequency(tracking_freq_saved, 1, 0)
        aom_freq_saved = self.freq_apply()
        self.PID.set_current(tracking_power_saved, 1, 0)
        self.PID.set_phase(tracking_phase_saved, 1, 0)
        
        # AOM Signal
        aom_power_saved = int(self.config['aom_signal']['aom_power_saved'])
        aom_phase_saved = int(self.config['aom_signal']['aom_phase_saved'])
        
        self.aom_freq_box.setText("%.6f" % aom_freq_saved)
        self.aom_power_box.setText("%d" % aom_power_saved)
        self.aom_phase_box.setText("%d" % aom_phase_saved)
        
        # self.PID.set_frequency(aom_freq_saved, 0, 1)
        self.PID.set_current(aom_power_saved, 0, 1)
        self.PID.set_phase(aom_phase_saved, 0, 1)
        
        # Offset configuration
        offset_index_saved = int(self.config['offset']['index_saved'])
        self.offset_unit_combobox.setCurrentIndex(offset_index_saved)
        
        offset_saved = float(self.config['offset']['offset_saved'])
        offset_step_size_saved = float(self.config['offset']['offset_step_size_saved'])
        
        self.offset_spinbox.setValue(offset_saved)
        self.offset_step_size_box.setText("%.6f" % offset_step_size_saved)
        
        self.offset_step_size_apply()
        
        print('Configuration reloaded\n')
        
    def edit_config(self):
        self.config_editor.show()
        self.config_editor.open_document_by_external(self.config_filename)
        print('Configuration edited\n')
    
    def config_changed(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_filename)
        
        if(int(self.P_box.text()) != int(self.config['PID']['P_saved'])):
            return True
        if(int(self.I_box.text()) != int(self.config['PID']['I_saved'])):
            return True
        if(int(self.D_box.text()) != int(self.config['PID']['D_saved'])):
            return True
        if(self.beam_geometry_combobox.currentIndex() != int(self.config['beam_geometry']['index_saved'])):
            return True
        if(float(self.tracking_freq_box.text()) != float(self.config['tracking_signal']['tracking_freq_saved'])):
            return True
        if(float(self.tracking_power_box.text()) != float(self.config['tracking_signal']['tracking_power_saved'])):
            return True
        if(float(self.tracking_phase_box.text()) != float(self.config['tracking_signal']['tracking_phase_saved'])):
            return True
        #if(self.aom_freq_box.text() != self.config['aom_signal']['aom_freq_saved']):
            #return True
        if(int(self.aom_power_box.text()) != int(self.config['aom_signal']['aom_power_saved'])):
            return True
        if(float(self.aom_phase_box.text()) != float(self.config['aom_signal']['aom_phase_saved'])):
            return True
        if(self.offset_unit_combobox.currentIndex() != int(self.config['offset']['index_saved'])):
            return True
        if(self.offset_spinbox.value() != float(self.config['offset']['offset_saved'])):
            return True
        if(float(self.offset_step_size_box.text()) != float(self.config['offset']['offset_step_size_saved'])):
            return True
        
        return False
        
    def save_config(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_filename)
        
        # PID value configuration 
        self.config['PID']['P_saved'] = self.P_box.text()
        self.config['PID']['I_saved'] = self.I_box.text()
        self.config['PID']['D_saved'] = self.D_box.text()

        # Beam geometry configuration
        self.config['beam_geometry']['index_saved'] = str(self.beam_geometry_combobox.currentIndex())

        # Tracking signal configuration
        self.config['tracking_signal']['tracking_freq_saved'] = self.tracking_freq_box.text()
        self.config['tracking_signal']['tracking_power_saved'] = self.tracking_power_box.text()
        self.config['tracking_signal']['tracking_phase_saved'] = self.tracking_phase_box.text()

        # Aom signal configuration
        #self.config['aom_signal']['aom_freq_saved'] = self.aom_freq_box.text()
        self.config['aom_signal']['aom_power_saved'] = self.aom_power_box.text()
        self.config['aom_signal']['aom_phase_saved'] = self.aom_phase_box.text()
        
        # Offset configuration
        self.config['offset']['index_saved'] = str(self.offset_unit_combobox.currentIndex())
        self.config['offset']['offset_saved'] = str(self.offset_spinbox.value())
        self.config['offset']['offset_step_size_saved'] = self.offset_step_size_box.text()
        
        with open(self.config_filename, 'w') as new_config_file:
            self.config.write(new_config_file)
            
    def closeEvent(self, event):       
        # Return to initlal state
        self.PID.comp_stop()
        
        # Turn off all signal         
        self.PID.power_down(1, 1) 
        self.PID.dds_stop()
        self.PID.adc_stop()
        
        if self.config_changed():
            self.save_config()
            print('Configuration change saved!')
            
        self.fpga.close()
        
        
    #########################################################################################################################
    ## GUI manipulation
    #########################################################################################################################
    
    ################################### Beam geometry manipulation ############################################################
    def feedback_select(self):
        current_index = self.beam_geometry_combobox.currentIndex()
        feedback_direction = self.beam_geometry_feedback_direction_list[current_index]
        geometry = self.beam_geometry_geometry_list[current_index]
        
        print(feedback_direction)
        print(geometry)
        
        if(feedback_direction == 'NORMAL'):
            self.PID.normal_feedback()
        else:
            self.PID.reverse_feedback()
            
        if(geometry == 'SINGLE PASS'):
            self.PID.single_pass()
        else:
            self.PID.double_pass()
        
        # Frequency update
        self.freq_apply()
        
        return
    
    ################################### Manual Lock manipulation ############################################################
    def ADC_read(self):
        freq_difference = self.PID.adc_load_large_data()
        self.freq_difference_box.setText(str(freq_difference) + 'Hz')
    
    def freq_add(self):
        try:
            freq_difference = float(self.freq_difference_box.text()[0 : -2])
            tracking_freq = float(self.tracking_freq_box.text()) * (10 ** 6) # MHz unit
        except:
            print('Failed to read freq_difference')
            return
        
        tracking_freq += freq_difference
        tracking_freq = tracking_freq / (10 ** 6) # MHz unit
        self.tracking_freq_box.setText("%.6f" % tracking_freq)
        self.freq_apply()
        
    def freq_substract(self):
        try:
            freq_difference = float(self.freq_difference_box.text()[0 : -2]) 
            tracking_freq = float(self.tracking_freq_box.text()) * (10 ** 6) # MHz unit
        except:
            print('Failed to read freq_difference')
            return
        
        tracking_freq -= freq_difference        
        tracking_freq = tracking_freq / (10 ** 6) # MHz unit
        self.tracking_freq_box.setText("%.6f" % tracking_freq)
        self.freq_apply()
    
    ################################### Signal Manipulation ############################################################
    def freq_apply(self): # frequency apply (tracking + AOM)
        try:
            tracking_freq = float(self.tracking_freq_box.text())
            
            if(tracking_freq < self.tracking_freq_min or tracking_freq > self.tracking_freq_max):
                print('tracking freqeucny out of range, check the range first\n')
                return
            
            beam_geometry_formula = self.beam_geometry_formula_list[self.beam_geometry_combobox.currentIndex()]
            
            # tracking frequency is third order, so we have to divide N by 3
            # hyperfine energy[GHz], offset_frequency[kHz], tracking_freq[MHz], detuning[MHz], fixed_aom_freq [MHz]
            detuning = self.hyperfine_energy * (10 ** 3) + self.offset_frequency / (10 ** 3) - (self.N / 3) * tracking_freq 
            fixed_aom_freq = float(self.beam_geometry_fixed_aom_freq_list[self.beam_geometry_combobox.currentIndex()]) 
            
            aom_freq = eval(beam_geometry_formula)
        except:
            return
        
        try:
            self.tracking_freq_box.setText("%.6f" % tracking_freq) # MHz formatting
            self.aom_freq_box.setText("%.6f" % aom_freq) # MHz formatting

            self.PID.set_frequency(tracking_freq, 1, 0)
            self.PID.set_frequency(aom_freq, 0, 1)
            return aom_freq
        except:
            return
        
        
    def tracking_signal_onoff(self):
        if (self.tracking_signal_on == True):
            self.tracking_signal_on = False
            self.tracking_signal_onoff_button.setIcon(self.off_icon)
            self.PID.power_down(1, 0)
        else:
            self.tracking_signal_on = True
            self.tracking_signal_onoff_button.setIcon(self.on_icon)
            self.PID.power_up(1, 0)
        
    def aom_signal_onoff(self):
        if (self.aom_signal_on == True):
            self.aom_signal_on = False
            self.aom_signal_onoff_button.setIcon(self.off_icon)
            self.PID.power_down(0, 1)
        else:
            self.aom_signal_on = True
            self.aom_signal_onoff_button.setIcon(self.on_icon)
            self.PID.power_up(0, 1)
    
    ################################### Locking manipulation ############################################################
    def lock_start(self):
        self.isLockOn = True
        
        # Color Setting
        #self.P_box.setStyleSheet("background-color: #FFFF00") # yellow
        #self.I_box.setStyleSheet("background-color: #FFFF00")
        #self.D_box.setStyleSheet("background-color: #FFFF00")
            
        self.tracking_freq_box.setStyleSheet("background-color: #FFFF00")
        self.tracking_power_box.setStyleSheet("background-color: #FFFF00")
        self.tracking_phase_box.setStyleSheet("background-color: #FFFF00")

        self.aom_freq_box.setStyleSheet("background-color: #FFFF00")
        self.aom_power_box.setStyleSheet("background-color: #FFFF00")
        self.aom_phase_box.setStyleSheet("background-color: #FFFF00")
                
        self.adc_voltage_box.setStyleSheet("background-color: #FFFF00")
            
        self.lock_start_button.setStyleSheet("background-color: #D3D3D3") # gray
        self.lock_stop_button.setStyleSheet("background-color: #FF0000") # red
            
        # Access enable setting
        self.reload_config_button.setEnabled(False)
        self.edit_config_button.setEnabled(False)
        self.save_config_button.setEnabled(False)
        
        self.beam_geometry_combobox.setEnabled(False)
        #self.P_box.setEnabled(False)
        #self.I_box.setEnabled(False)
        #self.D_box.setEnabled(False)

        self.ADC_read_button.setEnabled(False)
        self.freq_add_button.setEnabled(False)
        self.freq_substract_button.setEnabled(False)

        self.tracking_freq_box.setEnabled(False)
        self.tracking_power_box.setEnabled(False)
        self.tracking_phase_box.setEnabled(False)
        self.tracking_signal_onoff_button.setEnabled(False)

        self.aom_power_box.setEnabled(False)
        self.aom_phase_box.setEnabled(False)
        self.aom_signal_onoff_button.setEnabled(False)
        
        self.lock_start_button.setEnabled(False)
        self.lock_stop_button.setEnabled(True)
        
        # Lock start
        self.PID.comp_start()
        self.real_time_data_read()
       
    def real_time_data_read(self):      
         real_time_data = self.PID.load_data()
         adc_voltage = real_time_data[0]
         freq_tracking_MHz = real_time_data[1] 
         freq_aom_MHz = real_time_data[2] - self.offset # Preserve original value by substracting offset
         
         if freq_tracking_MHz < self.tracking_freq_min or freq_tracking_MHz > self.tracking_freq_max:
             print('tracking frequency out of range, lock aborted for safety\n')
             return
         
         # Data display
         self.tracking_freq_box.setText("%.6f" % freq_tracking_MHz)
         self.aom_freq_box.setText("%.6f" % freq_aom_MHz)
         self.adc_voltage_box.setText("%.4f" %adc_voltage)
         
         # Data save for plotting
         length_read_data = len(self.tracking_signal_queue) # Length of data read before
         
         if(length_read_data < self.max_data_length):
             self.tracking_signal_queue.append(freq_tracking_MHz)
             self.aom_signal_queue.append(freq_aom_MHz)
             self.adc_queue.append(adc_voltage)
             
         else: # Only save latest data (Use deque for O(1) complexity of append and pop)
             self.tracking_signal_queue.popleft()
             self.aom_signal_queue.popleft()
             self.adc_queue.popleft()
             
             self.tracking_signal_queue.append(freq_tracking_MHz)
             self.aom_signal_queue.append(freq_aom_MHz)
             self.adc_queue.append(adc_voltage)
         
         # Repeat reading data continuously
         if(self.isLockOn):
             threading.Timer(self.sampling_time, self.real_time_data_read).start()

             
    def lock_stop(self):
        self.isLockOn = False
        
        # Color Setting
        #self.P_box.setStyleSheet("background-color: #FFFFFF") # white
        #self.I_box.setStyleSheet("background-color: #FFFFFF")
        #self.D_box.setStyleSheet("background-color: #FFFFFF")
            
        self.tracking_freq_box.setStyleSheet("background-color: #FFFFFF")
        self.tracking_power_box.setStyleSheet("background-color: #FFFFFF")
        self.tracking_phase_box.setStyleSheet("background-color: #FFFFFF")

        self.aom_freq_box.setStyleSheet("background-color: #FFFFFF")
        self.aom_power_box.setStyleSheet("background-color: #FFFFFF")
        self.aom_phase_box.setStyleSheet("background-color: #FFFFFF")
                
        self.adc_voltage_box.setStyleSheet("background-color: #FFFFFF")
            
        self.lock_start_button.setStyleSheet("background-color: #008000") # green
        self.lock_stop_button.setStyleSheet("background-color: #D3D3D3") # gray
            
        # Access enable setting
        self.reload_config_button.setEnabled(True)
        self.edit_config_button.setEnabled(True)
        self.save_config_button.setEnabled(True)
        
        self.beam_geometry_combobox.setEnabled(True)
        #self.P_box.setEnabled(True)
        #self.I_box.setEnabled(True)
        #self.D_box.setEnabled(True)

        self.ADC_read_button.setEnabled(True)
        self.freq_add_button.setEnabled(True)
        self.freq_substract_button.setEnabled(True)

        self.tracking_freq_box.setEnabled(True)
        self.tracking_power_box.setEnabled(True)
        self.tracking_phase_box.setEnabled(True)
        self.tracking_signal_onoff_button.setEnabled(True)

        self.aom_power_box.setEnabled(True)
        self.aom_phase_box.setEnabled(True)
        self.aom_signal_onoff_button.setEnabled(True)
        
        self.lock_start_button.setEnabled(True)
        self.lock_stop_button.setEnabled(False)
        
        # Lock stop
        self.PID.comp_stop()
        
    ################################### Offset Manipulation ############################################################
    def offset_apply(self):
        offset_unit = self.offset_unit_combobox.currentText()
        if offset_unit == 'Hz':
            self.offset = self.offset_spinbox.value() / (10 ** 6)
        elif offset_unit == 'kHz':
            self.offset = self.offset_spinbox.value() / (10 ** 3)
        else:
            self.offset = self.offset_spinbox.value()
        
        aom_freq = float(self.aom_freq_box.text()) + self.offset
        
        if(self.isLockOn == False):
            self.PID.set_frequency(aom_freq, 0, 1)
            
        else: # If lock is going on, first stop lock and update offset, and start lock again
            self.PID.comp_stop()
            self.PID.set_frequency(aom_freq, 0, 1)
            self.PID.comp_start()
        
            
    def offset_step_size_apply(self):
        try:
            offset_step_size = float(self.offset_step_size_box.text())
        except:
            return
        
        self.offset_step_size_box.setText("%.6f" % offset_step_size)
        self.offset_spinbox.setSingleStep(offset_step_size)

    ################################### Plot Manipulation ############################################################
    def data_plot(self):
        
        # Save data to excel
        length_read_data = len(self.tracking_signal_queue) # Length of data read before
        if(length_read_data < self.max_data_length):
            time_array = list(np.linspace(0, (self.sampling_time * length_read_data) / 60, length_read_data))
        else:    
            time_array = list(np.linspace(0, self.measure_time, self.max_data_length))  
        
        df = DataFrame({'Time(minute)': time_array, 'Tracking freq[MHz]': list(self.tracking_signal_queue), 'AOM freq[MHz]': list(self.aom_signal_queue), \
                        'ADC voltage[V]': list(self.adc_queue)})
        
        now = datetime.now()
        save_file_name = '%s_%s%s%s_%s%s.xlsx' %(socket.gethostname(), now.year, str(now.month).zfill(2), str(now.day).zfill(2), str(now.hour).zfill(2), str(now.minute).zfill(2))
        drift_measure_dirname = dirname + '/Drift_measure/'
        save_file_name = drift_measure_dirname + save_file_name 
    
        writer = pd.ExcelWriter(save_file_name, engine='xlsxwriter')
        df.to_excel(writer, sheet_name = 'Sheet1')
                          
        writer.close()
        
        # Plot data
        # python plot             
          
        plt.figure(figsize = (8, 27))
        
        plt.subplot(311)
        plt.plot(time_array, list(self.tracking_signal_queue), color = 'r', label = 'Tracking signal')                    
        plt.title('Data plot')
        plt.xlabel('Time (minute)')
        plt.ylabel('Tracking freq[MHz]')       
        plt.legend(fontsize = 20)
        plt.legend(loc = 'upper right')
		    
        plt.subplot(312)
        plt.plot(time_array, list(self.aom_signal_queue), color = 'b', label = 'AOM signal')
        plt.xlabel('Time (minute)')
        plt.ylabel('AOM freq[MHz]')
        plt.legend(fontsize = 20)
        plt.legend(loc = 'upper right')
        
        plt.subplot(313)
        plt.plot(time_array, list(self.adc_queue), color = 'g', label = 'ADC')
        plt.xlabel('Time (minute)')
        plt.ylabel('ADC Voltage[V]')
        plt.legend(fontsize = 20)
        plt.legend(loc = 'upper right')
        
        plt.show()
        
        print("Data plot and save complete!")
        

if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    
    raman_pid_controller_gui = Raman_PID_Controller_GUI()
    raman_pid_controller_gui.show()
    sys.exit(app.exec_())



        








