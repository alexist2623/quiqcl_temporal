# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 13:07:35 2022

@author: QCP32
"""
from PyQt5.QtCore import QObject, pyqtSignal
import os, sys

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

class WaveMeterInterface(QObject):
    
    _gui_opened = False
    _sig_gui_opened = pyqtSignal(bool)
    
    def __init__(self, socket=None, gui=None):
        super().__init__()
        self.parent = socket
        self.gui = gui
        
    def openGui(self):
        if not self._gui_opened:
            sys.path.append(dirname + '/../')
            from wave_client import WavemeterWindow
            self.gui = WavemeterWindow(self, self.parent.gui._theme)
            self.gui.openConfig()
            self._gui_opened = True
            self._sig_gui_opened.emit(True)
  
    def closeDevice(self):
        self.gui.close()
        self._sig_gui_opened.emit(False)
        print("Closed wm")

    


# def _deviceSetup(self):        
#     self.menu_dict["device"] = {"menubar": self.menubar.addMenu("Devices")}
#     tab_device_list = self._getListFromConfig(self.cp.get("gui", "device"))
    
#     for device in tab_device_list:
#         self.menu_dict["device"][device] = self.menu_dict["device"]["menubar"].addAction(self.cp.get(device, 'title'))
#         self.menu_dict["device"][device].triggered.connect(self._guiControl)
    
# exec( "self.device_dict['%s'] = %s(socket=self)" % (device, self.cp.get(device, 'class')))
    
    
# def _guiControl(self):
#     '''
#     This function builds deivce windows following the config file.
#     '''
#     for device, action in self.menu_dict["device"].items():
#         if self.sender() == action:
#             print("activated %s" % device)
#             if not self.device_dict[device]._gui_opened:
#                 self.device_dict[device].openGui()

#             self.device_dict[device].gui.show()
#             if "changeTheme" in dir(self.device_dict[device].gui):
#                 self.device_dict[device].gui.changeTheme(self._theme)
#             else:
#                 self.device_dict[device].gui.setStyleSheet(self._theme_base[self._theme])
#             return
        
    