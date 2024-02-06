# -*- coding: utf-8 -*-
"""
Created on Sat Aug 21 23:22:02 2021

@author: JHJeong
"""

import os, sys

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

new_path_list = []
new_path_list.append(dirname + '/ui_resources') # For resources_rc.py
# More paths can be added here...
for each_path in new_path_list:
    if not (each_path in sys.path):
        sys.path.append(each_path)

# PyQt libraries
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QRect, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

main_ui_file = dirname + "/ui_resources/TripleBoard_AD9912_GUI_main_v0_01.ui"
sub_ui_file  = dirname + "/ui_resources/TripleBoard_AD9912_sub_ui_v0_01.ui"

main_ui, _ = uic.loadUiType(main_ui_file)
sub_ui,  _ = uic.loadUiType(sub_ui_file)

from TripleBoard_GUI_base import DDS_gui_base

#%% SubWindow
class SubWindow(QtWidgets.QWidget, sub_ui):
    
    _freq_signal = pyqtSignal(int, float)
    _curr_signal = pyqtSignal(int, float)
    _power_signal = pyqtSignal(int, bool)
    _phase_signal = pyqtSignal(int, int)
    
    def __init__(self, parent=None, board_idx=0):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.parent = parent
        self.board_idx = board_idx
        self.user_update = True
        self.unit = "MHz"
        self.unit_dict = {"MHz": 1, "kHz": 1e3, "Hz": 1e6}
        
        self._power_signal.connect(self.parent.powerOn)
        self._freq_signal.connect(self.parent.changeFreq)
        self._curr_signal.connect(self.parent.changeCurr)
        self._phase_signal.connect(self.parent.changePhase)
        
    def powerOn(self, on_flag):
        if "BTN_power_on_1" == self.sender().objectName():
            channel = 1
        else:
            channel = 2
        
        if not on_flag:
            self.user_update = False
            curr_spin_box = getattr(self, "Board1_DDS%d_power_spinbox" % (channel))
            curr_spin_box.setValue(0)
            self.user_update = True
        
        if self.user_update:
            self._power_signal.emit(channel, on_flag)
        
    def changeStep(self):
        obj_name = self.sender().objectName()
        spin_box = getattr(self, obj_name[:obj_name.rfind("_step_size")] + "_spinbox")
        spin_box.setSingleStep(float(self.sender().text()))

                
    def changeUnit(self, unit):
        obj_name = self.sender().objectName()
        spin_box = getattr(self, obj_name[:obj_name.rfind("_unit")] + "_spinbox")
        self.unit = unit
        
        if self.unit == "MHz":
            spin_box.setMaximum(450)
        elif self.unit == "kHz":
            spin_box.setMaximum(450e3)
        elif self.unit == "Hz":
            spin_box.setMaximum(450e6)
            
    def changeFreq(self, value):
        if self.user_update:
            obj_name = self.sender().objectName()
            if "DDS1" in obj_name:
                channel = 1
            else:
                channel = 2
            value = value/self.unit_dict[self.unit] # scales to MHz
            self._freq_signal.emit(channel, value)
            
    def changeCurr(self, value):
        if self.user_update:
            obj_name = self.sender().objectName()
            if "DDS1" in obj_name:
                channel = 1
            else:
                channel = 2
            self._curr_signal.emit(channel, value)
            
    def changePhase(self, value):
        if self.user_update:
            obj_name = self.sender().objectName()
            if "DDS1" in obj_name:
                channel = 1
            else:
                channel = 2
            self._phase_signal.emit(channel, value)
            
        

#%% MainWindow
class MainWindow(QtWidgets.QWidget, main_ui, DDS_gui_base):
    
    _update_signal = pyqtSignal()
    
    def __init__(self, controller=None, ext_update=False):
        QtWidgets.QWidget.__init__(self)
        # main_ui.__init__(self)
        self.setupUi(self)
        self.controller = controller
        self.ext_update = ext_update
        
        self.dds_list = []
        self.setWindowTitle("AD9912 with VVA")
        self._initUi()
        
        self.controller.sig_update_callback.connect(self._guiUpdate)
        self.user_update = True
        
    def _initUi(self):
        for board_idx in range(self.controller._num_boards):
            sub_window = SubWindow(parent=self, board_idx=board_idx)
            self.dds_list.append(sub_window)
        ## This must be done in the config
        for idx, sub_dds in enumerate(self.dds_list):
            sub_dds.Board_wrapper.setTitle("%s chamber" % (self.controller._board_nickname[idx]))
            self.HFrameLayout.addWidget(sub_dds)


        num_sub_widget = len(self.dds_list)
        widget_geometry = QRect(self._widget_x,
                                self._widget_y,
                                self._widget_width*num_sub_widget + 10*(num_sub_widget-1),
                                self._widget_height)


        self.HFrameLayout.setGeometry(widget_geometry)
        self.setGeometry(50,
                         150,
                         self._widget_width*num_sub_widget + 10*(num_sub_widget-1) + 20,
                         self._widget_height + 20)
        
        self.TXT_IP.setText("%s" % self.controller.sck.IP)
        self.TXT_PORT.setText("%d" % self.controller.sck.PORT)
        self.TXT_config.setText("%s" % self.controller.config_file)
        
        
    def toStatus(self, msg):
        self.LBL_status.setText(msg)

    def connectToServer(self, on_flag):
        if on_flag:
            self.controller.openDevice()
        else:
            self.controller.closeDevice()
            self.toStatus("Disconnected from the server.")
    
    def readConfig(self):
        config_file = self.TXT_config.text()
        self.controller.readConfig(config_file)
        
        self._initUi()
        
    def openConfig(self):
        config_file = QFileDialog.getOpenFileName(self, caption="Load a config file", directory=dirname, filter="*.conf")
        self.TXT_config.setText(config_file[0])
        self.readConfig()
                
    def powerOn(self, channel, value):
        board = self._getBoardIndex(self.sender())
        ch1, ch2 = self._getChannelFlags(channel)

        if value: # power up
            self.controller.powerUp(board, ch1, ch2) 
        else:
            self.controller.powerDown(board, ch1, ch2)
        
        
    def changeCurr(self, channel, current):
        board = self._getBoardIndex(self.sender())
        ch1, ch2 = self._getChannelFlags(channel)

        self.controller.setCurrent(board, ch1, ch2, current)
        
    def changeFreq(self, channel, freq_in_MHz):
        board = self._getBoardIndex(self.sender())
        ch1, ch2 = self._getChannelFlags(channel)
            
        self.controller.setFrequency(board, ch1, ch2, freq_in_MHz)
        
    def changePhase(self, channel, value):
        print("This function is not implemented yet.")
        
    def _guiUpdate(self):
        """
        When update GUI from external script....
        Not sure if it is a right approach.
        """
        if self.ext_update:
            self._update_signal.emit()
        else:
            self.updateUi()
            
    def updateUi(self):
        """
        current_settings =
        {1: {'current': [0, 0], 'freq_in_MHz': [0, 0], 'power': [0, 0]},
         2: {'current': [0, 0], 'freq_in_MHz': [0, 0], 'power': [0, 0]}}
        """
        current_settings = self.controller._current_settings
        
        for board_idx, board_settings in current_settings.items():
            self.dds_list[board_idx-1].user_update = False
            for setting, value_list in board_settings.items():
                if setting == "current":
                    for channel, value in enumerate(value_list):
                        spin_box = getattr(self.dds_list[board_idx-1], "Board1_DDS%d_power_spinbox" % (channel+1))
                        if not value == spin_box.value():
                            spin_box.setValue(value)
                            
                elif setting == "freq_in_MHz":
                    for channel, value in enumerate(value_list):
                        spin_box = getattr(self.dds_list[board_idx-1], "Board1_DDS%d_freq_spinbox" % (channel+1))
                        if not value == spin_box.value():
                            spin_box.setValue(value)
                            
                elif setting == "power":
                    for channel, value in enumerate(value_list):
                        push_button = getattr(self.dds_list[board_idx-1], "BTN_power_on_%d" % (channel+1))
                        if not value == push_button.isChecked():
                            push_button.setChecked(value)
                            
            self.dds_list[board_idx-1].user_update = True
        self.BTN_connect.setChecked(self.controller._is_opened)
                
    def _getBoardIndex(self, board_object):
        for idx, board in enumerate(self.dds_list):
            if self.sender() == board:
                board_idx = idx+1
                return board_idx
            
    def _getChannelFlags(self, channel):
        if channel == 1:
            ch1 = 1
            ch2 = 0
        else:
            ch1 = 0
            ch2 = 1
        return (ch1, ch2)
        
if __name__ == "__main__":
    from DDS_client_controller import DDS_ClientInterface
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    dds = MainWindow(controller = DDS_ClientInterface())
    dds.show()
