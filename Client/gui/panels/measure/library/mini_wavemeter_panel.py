# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 11:07:26 2022

@author: QCP32
"""
import os, sys
filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget


main_ui_file = dirname + "/mini_wavemeter.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

sys.path.append(dirname + "/../")
from measure_panel_theme import measure_panel_theme_base

class Mini_WaveMeter(QWidget, main_ui, measure_panel_theme_base):
    
    _sig_conn = pyqtSignal()
    _sig_init = pyqtSignal()
    
    
    def __init__(self, device_dict={}, parent=None, channel="", theme="black"):
        super().__init__()
        self.device_dict = device_dict
        self.parent = parent
        self.channel = channel
        self._theme = theme
        self.wm = device_dict["wm"]
        self.wm_gui = self.wm.gui
        self._variable_dict = {"freq": "",
                              "target": "",
                              "use": False,
                              "pid": False}
        
        self.setupUi(self)
        self._initUi()

    def __call__(self):
        return self.channel
    
    def enableGUI(self, flag):
        self.LBL_frequency.setEnabled(flag)
        self.TXT_target.setEnabled(flag)
        self.CHBOX_use.setEnabled(flag)
        self.CHBOX_pid.setEnabled(flag)
        self.BTN_monitor.setEnabled(flag)

    def getVariables(self):
        return self._variable_dict
            
    def showEvent(self, e):
        self.updateGui()
            
    def updateGui(self):
        if self.isVisible():
            self.LBL_frequency.setText(self._variable_dict["freq"])
            self.TXT_target.setText(self._variable_dict["target"])
            self.CHBOX_use.setChecked(self._variable_dict["use"])
            self.CHBOX_pid.setChecked(self._variable_dict["pid"])
        else:
            pass
        
    def updateValue(self):
        ferq_txt = getattr(self.wm.gui, "currentFreq%d" % (self.channel)).toPlainText()
        target_txt = getattr(self.wm.gui, "targetFreq%d" % (self.channel)).text()
        use = getattr(self.wm.gui, "useCbox%d" % (self.channel)).isChecked()
        pid = getattr(self.wm.gui, "pidCbox%d" % (self.channel)).isChecked()
        
        self._variable_dict["freq"] = ferq_txt
        self._variable_dict["target"] = target_txt
        self._variable_dict["use"] = use
        self._variable_dict["pid"] = pid
            
    
    def _initUi(self):
        pass


if __name__ == "__main__":
    mini_wm = Mini_WaveMeter()
    mini_wm.show()
    