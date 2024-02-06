# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 18:59:15 2023

@author: QCP75
"""

import os

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets

from Experimenter_theme import experimenter_theme_base

exp_gui_file = dirname + "/ui/Experimenter.ui"
exp_gui, _ = uic.loadUiType(exp_gui_file)

class ExperimenterGUI(QtWidgets.QMainWindow, exp_gui, experimenter_theme_base):
    
    def __init__(self, device_dict={}, parent=None, theme="black", app_name="experimenter"):
        QtWidgets.QMainWindow.__init__(self)
        self.device_dict = device_dict
        self.sequencer = self.device_dict["sequencer"]
        self.tab_dict = {}
        self.experiment_dict = {}
        self.parent = parent
        self._theme = theme
        self.app_name = app_name
        self.setupUi(self)
        self.setWindowTitle("Experimenter")
        
        folder_list = [folder for folder in os.listdir(dirname) if (os.path.isdir(folder) and not (folder == "ui" or folder == "__pycache__"))]

        self.setTabs(folder_list)
        self.sequencer.sig_occupied.connect(self._setInterlock)
        self.sequencer.sig_dev_con.connect(self._changeFPGAConn)
        if self.sequencer.is_opened:
            self.BTN_connect_FPGA.setChecked(True)
            
    def __call__(self):
        return self.experiment_dict

    def setTabs(self, folder_list):
        from parametric_heating.parametric_heating_widget import ParametricHeatingGUI
        self.tab_dict["parametric_heating"] = my_widget = ParametricHeatingGUI(self.device_dict, self, self._theme)
        self.tabWidget.addTab(my_widget, "parametric_heating")

    def connectFPGA(self, flag):
        if flag:
            open_result = self.sequencer.openDevice()
            if open_result == -1:
                self.sender().setChecked(False)
                self.toStatusBar("Failed opening the FPGA.")
        else:
            self.sequencer.closeDevice()
    
    def _changeFPGAConn(self, conn_flag):
        self.BTN_connect_FPGA.setChecked(conn_flag)
        
    def _setInterlock(self, occupation_flag):
        if occupation_flag:
            self.BTN_connect_FPGA.setEnabled(False)
        else:
            self.BTN_connect_FPGA.setEnabled(True)
        
    def openFolder(self):
        os.startfile(dirname + "/data")
        
        
    def _addTab(self, name, widget):
        self.tab_dict[name] = widget
        self.tabWidget.addTab(widget, name)
        
    def toStatusBar(self, message, duration=5000):
        self.statusbar.showMessage(message, duration)
        
        
        
if __name__ == "__main__":
    exp_gui = ExperimenterGUI()
    exp_gui.show()