# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 18:51:52 2023

@author: QCP75
The GUI v3 supports pyqtGraph
"""

import os
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox


filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/motor_status_ui_v2.ui'

Ui_Form, _ = uic.loadUiType(uifile)


class MotorController_GUI(QtWidgets.QWidget, Ui_Form):
    
    _gui_initialized = False
    
    def __init__(self, controller=None):
        QtWidgets.QWidget.__init__(self)
        
        self.setupUi(self)
        self.checkBox.setVisible(False)
       
        self.parent = controller
        
        self.motor_idx = 1
        self.motor_dict = {}
            
        self.setWindowTitle("Motor Controller v3.0")
        self.parent._sig_motors_positions.connect(self.updatePosition)
        
        if not self.parent == None:
            self._initMotors(self.parent._motors)
            
        self._gui_initialized = True
            
    def showEvent(self, event):
        if self._gui_initialized:
            self.updateMotorStatus()
        
    def updateMotorStatus(self):
        for motor_handle in self.motor_dict.values():
            motor_handle.updateStatus()
        
    def _initMotors(self, motor_dict):
        for nick, motor in motor_dict.items():
            self.addMotor(nick, motor.serial, motor)
        
    def addMotor(self, nickname="", serial_number="", motor=None):
        if nickname in self.motor_dict.keys():
            raise ValueError ("The nickname '%s' is already taken." % nickname)
            return
        
        self.motor_dict[nickname] = IndividualMotorGUI(self, nickname, serial_number, motor)
        self.motor_dict[nickname].Qposition.returnPressed.connect(self.requestedMotorMoving)

        self.gridLayout.addWidget(self.motor_dict[nickname].QcheckBox, self.motor_idx, 0)
        self.gridLayout.addWidget(self.motor_dict[nickname].Qnickname, self.motor_idx, 1)
        self.gridLayout.addWidget(self.motor_dict[nickname].Qserial,   self.motor_idx, 2)
        self.gridLayout.addWidget(self.motor_dict[nickname].Qposition, self.motor_idx, 3)
        self.gridLayout.addWidget(self.motor_dict[nickname].Qstatus,   self.motor_idx, 4)

        self.motor_idx += 1

        self.setFixedHeight( int(50 + 25*self.motor_idx) )
        
    def requestedMotorMoving(self):
        for motor_nick, motor_handle in self.motor_dict.items():
            if motor_handle.Qposition == self.sender():
                try:
                    data_dict = {motor_nick: float(motor_handle.Qposition.text())}
                    self.parent.moveToPosition(data_dict)
                    return
                except:
                    motor_handle.changedStatus(self.nickname, "error")
        
    def pressedOpenMotors(self):
        motor_list = []
        for motor_nick, motor_handle in self.motor_dict.items():
            if motor_handle.isChecked:
                motor_list.append(motor_nick)
                motor_handle.QcheckBox.setChecked(False)
        self.parent.openDevice(motor_list)
        
    def pressedHomeMotors(self):
        motor_list = []
        for motor_nick, motor_handle in self.motor_dict.items():
            if motor_handle.isChecked:
                motor_list.append(motor_nick)
                motor_handle.QcheckBox.setChecked(False)
        self.parent.homePosition(motor_list)
              
    def pressedCloseMotors(self):
        motor_list = []
        for motor_nick, motor_handle in self.motor_dict.items():
            if motor_handle.isChecked:
                motor_list.append(motor_nick)
                motor_handle.QcheckBox.setChecked(False)
        self.parent.closeDevice(motor_list)
        
    def changeItem(self, row_idx, col_idx, string):
        if row_idx > len(self.table_dict)-1 or col_idx > 3:
            raise ValueError ("Unexpected row id")
        
        self.tableWidget.item(row_idx, col_idx).setText(string)

        
    def getItem(self, row_idx, col_idx):
        text = self.tableWidget.item(row_idx, col_idx).text()
        return text
    
    def updatePosition(self, position_dict):
        for motor_nick, motor_position in position_dict.items():
            self.motor_dict[motor_nick].changedPosition(motor_position)
    
class IndividualMotorGUI(QObject):
    
    isChecked = False
    status = "closed"
    
    def __init__(self, parent=None, nick="", serial_number="", motor=None):
        super().__init__()
        self.parent = parent
        self.nickname = nick
        self.serial = serial_number
        
        self.QcheckBox = QCheckBox(self.parent)
        self.Qnickname = self._createQLabel(nick)
        self.Qserial   = self._createQLabel(serial_number)
        self.Qposition = QLineEdit("0.000")
        self.Qstatus   = self._createQLabel("Closed")
        
        self.motor = motor
        
        self.Qposition.setEnabled(False)
        self.Qstatus.setText("Closed")
        self.Qstatus.setStyleSheet("background-color:rgb(20, 20, 20); color:rgb(200, 200, 200);")
        
        self.QcheckBox.toggled.connect(self.toggledCheckBox)
        
        self.motor._sig_motor_initialized.connect(self.initiatedMotor)
        self.motor._sig_motor_error.connect(self.erroredMotor)
        self.motor._sig_motor_move_done.connect(self.movedMotor)
        self.motor._sig_motor_homed.connect(self.homedMotor)
        
        self.motor._sig_motors_changed_status.connect(self.changedStatus)
        
        
    def toggledCheckBox(self, flag):
        self.isChecked = flag
        
    def initiatedMotor(self, nick):
        self.Qposition.setText("%.3f" % self.motor.position)
    
    def erroredMotor(self, nick):
        self.changedStatus(self.nickname, "error")
    
    def movedMotor(self, nick, position):
        self.Qposition.setText("%.3f" % self.motor.position)
    
    def homedMotor(self, nick):
        self.Qposition.setText("0.000")
        
    def changedPosition(self, position):
        self.Qposition.setText("%.3f" % position)
    
    def changedStatus(self, nick, status):
        if status == "standby":
            self.Qposition.setEnabled(True)
            self.Qstatus.setStyleSheet("background-color:rgb(10, 150, 10); color:rgb(200, 200, 200);")
        elif status == "initiating":
            self.Qposition.setEnabled(False)
            self.Qstatus.setStyleSheet("background-color:rgb(130, 130, 130); color:rgb(200, 200, 200);")
        elif status == "moving":
            self.Qposition.setEnabled(False)
            self.Qstatus.setStyleSheet("background-color:rgb(10, 10, 150); color:rgb(200, 200, 200);")
        elif status == "homing":
            self.Qposition.setEnabled(False)
            self.Qstatus.setStyleSheet("background-color:rgb(150, 10, 10); color:rgb(200, 200, 200);")
        elif status == "closed":
            self.Qposition.setEnabled(False)
            self.Qstatus.setStyleSheet("background-color:rgb(20, 20, 20); color:rgb(200, 200, 200);")
        elif status == "error":
            self.Qposition.setEnabled(True)
            self.Qstatus.setStyleSheet("background-color:rgb(150, 10, 10); color:rgb(200, 200, 200);")

        self.Qstatus.setText(status)
        
    def updateStatus(self):
        position = self.motor.position
        status = self.motor.status
        
        self.changedPosition(position)
        self.changedStatus(self.nickname, status)
        
    def _createQLabel(self, label_text):
        qlabel = QLabel(label_text)
        qlabel.setAlignment(Qt.AlignCenter)
        return qlabel

        

        
if __name__ == "__main__":
    gui = MotorController_GUI()
    gui.show()