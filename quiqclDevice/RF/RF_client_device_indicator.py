# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 20:50:28 2023

@author: QCP75
"""

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLabel


class DeviceIndicator(QObject):
    
    __stylesheet = {1 : """
                            background:rgb(40,140,40);
                            border-radius: 8px;
                            margin-left: 2px;
                            margin-right:2px;
                            color:rgb(210, 210, 210);
                            font: 87 9pt "Arial Black";
                            """,
                    0: """
                            background:rgb(140,40,40);
                            border-radius: 8px;
                            margin-left: 2px;
                            margin-right:2px;
                            color:rgb(210, 210, 210);
                            font: 87 9pt "Arial Black";
                            """}
    
    def __init__(self, parent=None, device_name="", device_setting=None, theme="black"):
        super().__init__()
        self.parent = parent
        self.device_name = device_name
        self.device = device_setting
        self._theme = theme

        
    def createLabel(self, container=None):
        if not container == None:
            self.label = QLabel()
            self.label.setText(self.device_name.upper())
            self.label.setMaximumWidth(len(self.device_name)*12)
            self.label.setMinimumWidth(len(self.device_name)*12)
            self.label.setMaximumHeight(20)
            self.label.setAlignment(Qt.AlignCenter)
            
            container.addWidget(self.label)
            
            stylesheet = self.__stylesheet[0]
            self.label.setStyleSheet(stylesheet)
            
            if self._theme == "black":
                self.label.setStyleSheet("background-color:rgb(40,40,40)")
            
    def checkDeviceOutput(self):
        flag = 0
        for ch, setting in self.device.settings.items():
            flag += setting["out"]
        stylesheet = self.__stylesheet[flag > 0]
        self.label.setStyleSheet(stylesheet)
        