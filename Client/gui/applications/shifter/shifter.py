# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 2022

@author: Jaeun Kim
"""
import os
from PyQt5 import uic
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, QMutex, QWaitCondition, QThread, Qt
from configparser import ConfigParser
import numpy as np
import sys

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/shifter.ui'
Ui_Form, QtBaseClass = uic.loadUiType(uifile)
version = "0.0"


class Shifter(QtWidgets.QWidget, Ui_Form):
    
    sig_move_done = pyqtSignal()  # dummy signal to respond to motorcontroller

    def __init__(self, device_dict=None, parent=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        
        self.device_dict = device_dict
        self.motors = self.device_dict["motors"]
        self.parent = parent
        self._theme = theme

        # following 2 lines: local test mode
        # self.cp = ConfigParser()
        # self.cp.read("C:/Users/jaeunkim/PycharmProjects/QtDevice_Server/Client/config/DESKTOP-0VR9MP4.ini")
        self.cp = self.parent.cp

        self._initUi()
        self._initParams()
        self._connect_signals()  # TODO
        self.readStagePosition(["shifter_x", "shifter_y", "shifter_z"])
        
        self.actions = {
            "Key_Left": {"axis": "x", "direction": -1},
            "Key_Right": {"axis": "x", "direction": 1},
            "Key_Down": {"axis": "y", "direction": -1},
            "Key_Up": {"axis": "y", "direction": 1},
            "Wheel_Down": {"axis": "z", "direction": -1},
            "Wheel_Up": {"axis": "z", "direction": 1},
            
            "Button_x_decrement": {"axis": "x", "direction": -1},
            "Button_x_increment": {"axis": "x", "direction": 1},
            "Button_y_decrement": {"axis": "y", "direction": -1},
            "Button_y_increment": {"axis": "y", "direction": 1},
            "Button_z_decrement": {"axis": "z", "direction": -1},
            "Button_z_increment": {"axis": "z", "direction": 1},
            }
        
    def _initUi(self):
        self.btn_x_left.setIcon(QtGui.QIcon(dirname+"\icons\Back.png"))
        self.btn_x_right.setIcon(QtGui.QIcon(dirname+"\icons\Forward.png"))
        self.btn_y_left.setIcon(QtGui.QIcon(dirname+"\icons\Back.png"))
        self.btn_y_right.setIcon(QtGui.QIcon(dirname+"\icons\Forward.png"))
        self.btn_z_left.setIcon(QtGui.QIcon(dirname+"\icons\Back.png"))
        self.btn_z_right.setIcon(QtGui.QIcon(dirname+"\icons\Forward.png"))

    def _initParams(self):
        self.axis_info = {
            "x": {"motor_nickname": "shifter_x", "step": float(self.cp.get("motors", "shifter_x_step")), "curr_pos_lbl": self.lbl_x_curr_pos},
            "y": {"motor_nickname": "shifter_y", "step": float(self.cp.get("motors", "shifter_y_step")), "curr_pos_lbl": self.lbl_y_curr_pos},
            "z": {"motor_nickname": "shifter_z", "step": float(self.cp.get("motors", "shifter_z_step")), "curr_pos_lbl": self.lbl_z_curr_pos},
            }
    
    def _connect_signals(self):
        self.sb_x_step.valueChanged.connect(self.updateStep)
        self.sb_y_step.valueChanged.connect(self.updateStep)
        self.sb_z_step.valueChanged.connect(self.updateStep)
        
        self.btn_x_left.clicked.connect(lambda: self.processGUIAction("Button_x_decrement"))
        self.btn_x_right.clicked.connect(lambda: self.processGUIAction("Button_x_increment"))
        self.btn_y_left.clicked.connect(lambda: self.processGUIAction("Button_y_decrement"))
        self.btn_y_right.clicked.connect(lambda: self.processGUIAction("Button_y_increment"))
        self.btn_z_left.clicked.connect(lambda: self.processGUIAction("Button_z_decrement"))
        self.btn_z_right.clicked.connect(lambda: self.processGUIAction("Button_z_increment"))

    def updateStep(self):
        axis_name = self.sender().objectName().split("_")[1]  # "x", "y", "z"
        self.axis_info[axis_name]["step"] = float(self.sender().text())  
        print(self.sender().objectName(), self.sender().text())

    def keyPressEvent(self, event):
        print("KEYPRESSEVENT ACTIVATED", event.key())
        key = event.key()

        if key == Qt.Key_A:
            self.processGUIAction("Key_Left")
        if key == Qt.Key_D:
            self.processGUIAction("Key_Right")
        if key == Qt.Key_S:
            self.processGUIAction("Key_Down")
        if key == Qt.Key_W:
            self.processGUIAction("Key_Up")

    def wheelEvent(self, event):
        # print("mouse wheel movement: ", event.angleDelta().y())
        if event.angleDelta().y() < 0:
            self.processGUIAction("Wheel_Down")
        if event.angleDelta().y() > 0:
            self.processGUIAction("Wheel_Up")
    
    def processGUIAction(self, action_name):
        target_axis_info = self.axis_info[self.actions[action_name]["axis"]]
        # target position = current position + (direction: plus or minus) * step
        target_position = float(target_axis_info["curr_pos_lbl"].text()) + self.actions[action_name]["direction"] * target_axis_info["step"]
        print("[processGUIAction]", target_axis_info, action_name, target_position)
        self.moveMotorPosition(target_axis_info["motor_nickname"], target_position)
    
    def moveMotorPosition(self, motor_nickname, target_position):
        self.motors.toWorkList(["C", "MOVE", [motor_nickname, target_position], self])
        
    def readStagePosition(self, motor_nickname):
        if isinstance(motor_nickname, list):
            self.motors.toWorkList(["Q", "POS", motor_nickname, self])
        else:
            self.motors.toWorkList(["Q", "POS", [motor_nickname], self])
        
    def toMessageList(self, msg):  # decoding answers from motorcontroller 
        print("entered [toMessageList]", msg)
        if msg[2] == "POS":
            data = msg[-1]
            
            nickname_list = data[0::2]
            position_list = data[1::2]
            
            for nickname, position in zip(nickname_list, position_list):
                if nickname == "shifter_x":
                    self.lbl_x_curr_pos.setText(str(round(position*1000)/1000))
                if nickname == "shifter_y":
                    self.lbl_y_curr_pos.setText(str(round(position*1000)/1000))
                if nickname == "shifter_z":
                    self.lbl_z_curr_pos.setText(str(round(position*1000)/1000)) 
            self.sig_move_done.emit()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = Shifter()
    ex.show()
    sys.exit(app.exec_())