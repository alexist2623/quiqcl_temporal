# -*- coding: utf-8 -*-
"""
Created on Sat Aug 21 23:22:02 2021

@author: JHJeong
"""

from __future__ import unicode_literals
import os, sys, datetime
import pandas as pd
from configparser import ConfigParser

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QRect, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QLabel, QVBoxLayout, QFileDialog

main_ui_file = dirname + "/DAC_16ch_v0_02.ui"

main_ui, _ = uic.loadUiType(main_ui_file)

from DAC_gui_Base import DAC_GuiBase

#%% MainWindow
class MainWindow(QtWidgets.QWidget, main_ui, DAC_GuiBase):
    """
    This GUI class is for controlling 16 channel DAC.
    Shifts axes are
        - Symmetric
        - Asymmetric
        - X axis
        - Y axis
        - Z axis
    """
    
    # _num_ch = 16 # 1~7: left electodes, 8~14: right electrodes, 15: inner left electrode, 16: inner right electrode
    # _num_axes = 5 # S,A,X,Y,Z
    
    _update_signal = pyqtSignal()
    
    _version = "v0.01"
    user_update = True    
    
    def __init__(self, controller=None, ext_update=False):
        QtWidgets.QWidget.__init__(self)
        # main_ui.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("DAC 16ch %s" % self._version)
        self.pc_name =  os.getenv("COMPUTERNAME", "defaultvalue")
        self.LBL_PC_name.setText("Control PC - %s" % self.pc_name)
        
        self.controller = controller
        self.ext_update = ext_update
        
        self._initUi()
        self._loadShiftSet(dirname + '/config/%s.csv' % self.pc_name)
        
        self.controller.sig_update_callback.connect(self._guiUpdate)
        self._changed_list = []
        
    def _initUi(self):
        for ch in range(self._num_ch):
            textbox = getattr(self, "DC_Textbox_%d" % (ch+1))
            offset = getattr(self, "DC_Offset_%d" % (ch+1))
            
            textbox.textChanged.connect(self.voltageTextChanged)
            textbox.returnPressed.connect(self.voltageEditFinished)
            
            
            self.dc_textbox_list.append(textbox)
            self.dc_offset_list.append(offset)
            
        for ax in range(self._num_axes):
            textbox = getattr(self, "SFT_Textbox_%d" % (ax+1))
            offset = getattr(self, "SFT_Offset_%d" % (ax+1))
            scroll = getattr(self, "SFT_Scrollbar_%d" % (ax+1))
            
            self.sft_textbox_list.append(textbox)
            self.sft_offset_list.append(offset)
            self.sft_scroll_list.append(scroll)
            
        # set disable items
        self._setItemEnabled(False)
        
    def voltageTextChanged(self):
        if self.user_update:
            self.sender().setStyleSheet(self._theme_color[self._theme]["edit_not_finished"])
            if not self.sender() in self._changed_list:
                self._changed_list.append(self.sender())
        
    def voltageEditFinished(self): 
        channel_list = []
        voltage_list = []
        for text_box in self._changed_list:
            try:
                value = float(text_box.text())
                idx = int(text_box.objectName()[11:]) - 1 # get index number
                
                channel_list.append(idx)
                voltage_list.append(value)
                
                text_box.setText("%.2f" % value)    
                text_box.setStyleSheet(self._theme_color[self._theme]["text_box"])
            except Exception as e:
                self.toStatus("The voltage value should be a number %s" % e)
            
        self.controller.setVoltage(channel_list, voltage_list)
                


    #%% Buttons
    def buttonConnectPressed(self, flag):
        if flag:
            if self.user_update:
                try:
                    self.controller.openDevice()
                    self.toStatus("Opened the DAC.")
                    self._setItemEnabled(flag)
                except Exception as e:
                    self.toStatus("Couldn't open the dac (%s)" % e)
                    self.user_update = False
                    self.BTN_connect.setChecked(False)
                    self.user_update = True
            else:
                self._setItemEnabled(flag)
        else:
            if self.user_update:
                self.controller.closeDevice()
            self._setItemEnabled(flag)
            self.toStatus("Closed the DAC.")
            
    def buttonSavePressed(self):
        pre_filename = "%s_%s" % (datetime.datetime.now().strftime("%y%m%d_%H%M%S"), self.pc_name)
        save_file_name, _ = QFileDialog.getSaveFileName(self, "Saving file",
                                                        dirname + "/" + pre_filename, "Data files (*.csv)")
        
        if save_file_name == "":
            self.toStatus("Aborted saving.")
        else:
            self.saveVoltageSet(save_file_name)
        
        
    def buttonLoadPressed(self):
        load_file_name, _ =  QFileDialog.getOpenFileName(self, "Loading file",
                                                        dirname, "Data files (*.csv)")
        if load_file_name == "":
            self.toStatus("Aborted loading.")
        else:
            self.loadVoltageSet(load_file_name)
            
    def buttonRestorePressed(self):
        channel_list = []
        voltage_list = []
        
        self.user_update = False
        
        # voltage
        for idx in range(self._num_ch):
            voltage = float(self.dc_offset_list[idx].text())
            self.dc_textbox_list[idx].setText("%.2f" % voltage)
            
            channel_list.append(idx)
            voltage_list.append(voltage)
           
        # shifts
        for idx in range(self._num_axes):
            value = int(self.sft_offset_list[idx].text())
            self.sft_textbox_list[idx].setText("%d" % value)
            
        self.user_update = True

        self.controller.setVoltage(channel_list, voltage_list)            
            
    def buttonResetPressed(self):
        self.controller.resetDevice()
        
        self.user_update = False
        for item in self.dc_textbox_list:
            item.setText("0.00")
        for item in self.dc_offset_list:
            item.setText("0.00")
            
        for item in self.sft_textbox_list:
            item.setText("0.00")
        for item in self.sft_offset_list:
            item.setText("0.00")
            
        for item in self.sft_scroll_list:
            item.setValue(0)
        self.user_update = True
        self.toStatus("Reset the DAC.")
        
        
    def sliderValueChanged(self, sft_step):
        for idx in range(self._num_axes):
            if self.sft_scroll_list[idx] == self.sender():
                ax_idx = idx
            
        # print(ax_idx)
        delta = self._prev_sft_values[ax_idx] - sft_step
        ax_key = self._sft_dict[ax_idx]
        
        if self.user_update:
            for ch in range(self._num_ch):
                value = float(self.dc_textbox_list[ch].text())
                value += self._sft_values[ax_key][ch] * delta
                self.dc_textbox_list[ch].setText("%.2f" % value)
            
            self.sft_textbox_list[ax_idx].setText("%.2f" % -sft_step)
        
            self.voltageEditFinished()
        self._prev_sft_values[ax_idx] = sft_step
        

    #%%
    def saveVoltageSet(self, file_name):
        if not file_name[-4:] == ".csv":
            file_name += ".csv"
        
        voltage_list = self.controller._voltage_list
        sft_list = []
        
        for sft_textbox in self.sft_textbox_list:
            sft_list.append(int(float(sft_textbox.text())))
            
        save_dict = {"voltage": voltage_list,
                     "shift": sft_list}
        df = pd.DataFrame(dict([(k, pd.Series(v)) for k,v in save_dict.items()]))
        df.to_csv(file_name)
        
        self.grab().save(file_name[:-4] + '.png')
        self.toStatus("Saved the file as '%s'" % file_name)
        
    def loadVoltageSet(self, file_name):
        try:
            df = pd.read_csv(file_name, index_col = 0)
        
            loaded_dict = {k: v.dropna().to_dict() for k,v in df.items() }
            voltage_list = list(loaded_dict["voltage"].values())
            sft_list = list(loaded_dict["shift"].values())
            self._prev_sft_values = sft_list
            
            self.user_update = False
            for ch_idx in range(self._num_ch):
                self.dc_offset_list[ch_idx].setText("%.2f" % voltage_list[ch_idx])
            
            for ax_idx in range(self._num_axes):
                self.sft_textbox_list[ax_idx].setText("%.2f" % sft_list[ax_idx])
                self.sft_offset_list[ax_idx].setText("%d" % sft_list[ax_idx])
                self.sft_scroll_list[ax_idx].setValue( int(sft_list[ax_idx]) )
                
            self.user_update = True
            self.controller.setVoltage(list(range(self._num_ch)), voltage_list)
            self.toStatus("Loaded a file '%s'" % file_name)
            
        except Exception as e:
            self.toStatus("Couldn't open the file (%s)" % e)
            return
        
    def _loadShiftSet(self, file_name):
        if not os.path.isfile(file_name):
            self.toStatus("Couldn't find the shift config file '%s', Using default values." % os.path.basename(file_name))
            return
        
        try:
            df = pd.read_csv(file_name, index_col = 0)
        
            loaded_dict = {k: v.dropna().to_dict() for k,v in df.items() }
            
            for ax_key in loaded_dict.keys():
                self._sft_values[ax_key] = list(loaded_dict[ax_key].values())
            
            self.toStatus("Loaded a shift config file '%s'" % os.path.basename(file_name))
            
        except Exception as e:
            self.toStatus("Couldn't open the file (%s)" % e)
            return
        
    def _setItemEnabled(self, flag):
        for item in self.dc_textbox_list:
            item.setEnabled(flag)
        for item in self.sft_scroll_list:
            item.setEnabled(flag)
        for item in self.sft_textbox_list:
            item.setEnabled(flag)

        self.BTN_reset.setEnabled(flag)
        self.BTN_restore.setEnabled(flag)
        self.BTN_save.setEnabled(flag)
        self.BTN_load.setEnabled(flag)


    def toStatus(self, msg):
        self.STS_Textbox.appendPlainText(msg)
        
    def _guiUpdate(self, sig_str):
        """
        When update GUI from external script....
        Not sure if it is a right approach.
        """
        if self.ext_update:
            self._update_signal.emit(sig_str)
        else:
            self.updateUi(sig_str)
            
    def updateUi(self, sig_str):
        self.user_update = False
        
        if sig_str == "o":
            self.BTN_connect.setChecked(True)
        elif sig_str == "c":
            self.BTN_connect.setChecked(False)
            
        elif sig_str == "r":
            for ch in range(self._num_ch):
                self.dc_textbox_list[ch].setText("0.00")
            
        elif sig_str == "v":
            voltage_list = self.controller._voltage_list
            for ch in range(self._num_ch):
                self.dc_textbox_list[ch].setText("%.2f" % voltage_list[ch])
            
        self.user_update = True
                
        
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    dac = MainWindow(controller = None)
    dac.show()
