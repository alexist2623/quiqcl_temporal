# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 09:52:59 2021

@author: QCP32
"""
################ Importing Sequencer Programs ###################
# import sys
# sys.path.append("Q://Experiment_Scripts/GUI_Control_Program/RemoteEntangle/Sequencer/Sequencer Library")
# from SequencerProgram_v1_07 import SequencerProgram, reg
# import SequencerUtility_v1_01 as su
# from ArtyS7_v1_02 import ArtyS7
# import HardwareDefinition_EC as hd

################# Importing Hardware APIs #######################
  # Thorlabs KDC101 Motor Controller
# from DUMMY_PMT import PMT

################ Importing GUI Dependencies #####################
import os, sys
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore    import pyqtSignal, QObject, QTimer


filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/pmt_aligner_v3.ui'
widgetdir = dirname + '/widgets/'

Ui_Form, QtBaseClass = uic.loadUiType(uifile)
version = "3.1"

from pmt_aligner_theme import pmt_aligner_theme_base
        
class PMTAlginerGUI(QtWidgets.QMainWindow, Ui_Form, pmt_aligner_theme_base):
    
    _gui_initialized = False
    
    def __init__(self, device_dict=None, parent=None, theme="black", app_name=""):
        QtWidgets.QMainWindow.__init__(self)
        
        self.setupUi(self)
        self.parent = parent
        self._theme = theme
        self.app_name = app_name
        
        self.motor_dict = {}
        self.device_dict = device_dict
        
        self.motor_controller = self.device_dict["motors"]
        self.motor_controller._sig_motors_positions.connect(self._liveUpdatePosition)
        
        self.sequencer = self.device_dict["sequencer"]
        self.sequencer.sig_dev_con.connect(self._changeFPGAConn)
        
        self.cp = self.parent.cp
        self.operation_mode = "local"

        self.motor_opener = MotorOpener(self, self._theme)

        self._initParameters()
        self._initUi()
        self.setWindowTitle("%s v%s" % (self.app_name, version))
        self._gui_initialized = True
        
    def showEvent(self, event):
        if self._gui_initialized:
            self.readAllPositions()
        
    def readAllPositions(self):
        for motor_handle in self.motor_dict.values():
            motor_handle.updatePosition()
            
        
    def showOnTop(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        
    def _initParameters(self):
        motor_str = self.cp.get(self.app_name, "motors")
        motor_list = map(str.strip, motor_str.split(',')) # This is the fastest one to split by comma and remove white spaces
            
        if "remote" in self.cp.options(self.app_name):
            self.operation_mode = "remote"
            
        for motor_idx, motor_nick in enumerate(motor_list):
            nick_label = getattr(self, "NON_%s_pos" % chr(88 + motor_idx))
            value_label = getattr(self, "LBL_%s_pos" % chr(88 + motor_idx))
            motor_handle = self.device_dict["motors"]._motors[motor_nick]
            
            self.motor_dict[motor_nick] = MotorController(self,
                                                          nick_label,
                                                          value_label,
                                                          motor_nick,
                                                          self.motor_controller,
                                                          True if self.operation_mode=="local" else False)
            self.motor_opener.addMotor(motor_handle)
            
        if "detector" in self.cp.options(self.app_name):
            self.detector = self.cp.get(self.app_name, "detector")
            self.LBL_detector.setText(self.detector)
            print("Detector is set to %s" % self.detector)
        else:
            self.detector = "PMT"
            print("No detector has been found.")
            
        self.motor_opener.startLoadingMotors()
        
            
    def pressedConnectSequencer(self, flag):
        if flag:
            open_result = self.sequencer.openDevice()
            if open_result == -1:
                self.sender().setChecked(False)
                self.toStatusBar("Failed opening the FPGA.")
        else:
            self.sequencer.closeDevice()
                
    def pressedMovePosition(self):
        position_dict = {}
        for motor_nick, motor_handle in self.motor_dict.items():
            position_dict[motor_nick] = motor_handle.getPositioin()
        self.MoveToPosition(position_dict)
        
    def MoveToPosition(self, position_dict):
        self.motor_controller.moveToPosition(position_dict)

    def pressedReadPosition(self):
        self.readAllPositions()
        
    def pressedMotorSettings(self):
        pass
        
    
    def _initUi(self):
        sys.path.append(widgetdir)
        from scanner import ScannerGUI
        from count_viewer import CountViewer
        self.scanner = ScannerGUI(parent=self,
                                  sequencer=self.sequencer,
                                  motor_controller=self.motor_controller,
                                  motor_nicks = list(self.motor_dict.keys()),
                                  theme=self._theme)
        self.count_viewer = CountViewer(device_dict=self.device_dict, parent=self, theme=self._theme)
        
        self._addTabWidget(self.scanner, "PMT Scanner")
        self._addTabWidget(self.count_viewer, "PMT Count Viewer")
        
        if self.sequencer.is_opened:
            self.BTN_connect_sequencer.setChecked(True)
            
            
    def toStatusBar(self, msg, up_time=5000):
        self.statusbar.showMessage(msg, up_time)
        
    def _setInterlock(self, occupation_flag):
        if occupation_flag:
            self.BTN_connect_sequencer.setEnabled(False)
            if self.sequencer.occupant == "scanner":
                self.BTN_SET_pos.setEnabled(False)
                self.BTN_READ_pos.setEnabled(False)
        else:
            self.BTN_connect_sequencer.setEnabled(True)
            self.BTN_SET_pos.setEnabled(True)
            self.BTN_READ_pos.setEnabled(True)
            
    def _changeFPGAConn(self, conn_flag):
        self.BTN_connect_sequencer.setChecked(conn_flag)
        
    def _addTabWidget(self, widget, title):
        self.TabWidgetMain.addTab(widget, title)
        
    def _liveUpdatePosition(self, motor_dict):
        for motor_nick, motor_pos in motor_dict.items():
            if motor_nick in self.motor_dict.keys():
                self.motor_dict[motor_nick].changePosition(motor_pos)
                
    def returnedDetector(self):
        self.detector = self.LBL_detector.text()
        self.toStatusBar("A detector has been set to %s." % self.detector)
        
class MotorController(QObject):
    
    def __init__(self, parent, nick_label, value_label, nickname, motor_controller, local=True):
        super().__init__()
        self.parent = parent
        self.nick_label = nick_label
        self.value_label = value_label
        self.setNickname(nickname)
        self.motor_controller = motor_controller
        self.local = local
        self.setMotor(self.motor_controller._motors[self.nickname])
        
    def __call__(self):
        return self.nickname
        
    def setMotor(self, motor):
        self.motor = motor
        self.motor._sig_motor_initialized.connect(self._initializedMotor)
        self.motor._sig_motor_move_done.connect(self._finishedMoving)
        self.motor._sig_motor_homed.connect(self._finishedMoving)
        self.motor._sig_motors_changed_status.connect(self._changedStatus)
        if not self.motor._is_opened:
            self.motor_controller.openDevice(self.motor.nickname)
        
        self.updatePosition()
        
    def setNickname(self, nick_name):
        self.nickname = nick_name
        self.changedNickname(nick_name)
        
    def _initializedMotor(self, nick):
        position = self.motor.getPosition()
        self.changePosition(position)
        
    def _changedStatus(self, nickname, status):
        self.value_label.setEnabled(status == "standby")
        
    def changedNickname(self, nickname):
        self.nick_label.setText(nickname)
        
    def changePosition(self, position):
        self.value_label.setText("%.3f" % position)
        
    def updatePosition(self):
        position = self.motor.position
        self.changePosition(position)
        
    def getPositioin(self):
        try:
            position = float(self.value_label.text())
        except:
            position = self.motor.position
            self.parent.toStatusBar("The position of %s is wrong. (%s)" % self.nickname, self.value_label.text())
        return position
        
    def _finishedMoving(self):
        self.updatePosition()
        

from progress_bar import ProgressBar
from motoropener_theme_base import MotorOpener_Theme_Base

class MotorOpener(QtWidgets.QWidget, MotorOpener_Theme_Base):
    
    _finished_initialization = pyqtSignal()
    
    
    def __init__(self, controller=None, theme="black"):
        QtWidgets.QWidget.__init__(self)
        self.controller = controller
        self._theme = theme
        self.initUi()
        self._motor_list = []
        self.num_motors = 0
        
    def addMotor(self, motor):
        if not motor._is_opened:
            self._motor_list.append(motor.nickname)
            motor._sig_motor_initialized.connect(self.changeProgressBar)
            self.num_motors += 1
        
    # def changeTheme(self, theme):
    #     self._theme = theme
    #     styleSheet = {"white": "background-color:rgb(255, 255, 255)",
    #                   "black": "background-color:rgb(40, 40, 40); color:rgb(180, 180, 180)"}
        
    #     self.setStyleSheet(self._mainwindow_stylesheet[self._theme])

        
    def initUi(self):
        frame = QVBoxLayout()
        self.progress_bar = ProgressBar(self, self._theme)
        frame.addWidget(self.progress_bar)
        frame.setContentsMargins(0, 0, 0, 0)
        self.setLayout(frame)
        self.changeTheme(self._theme)
        
        self.resize(500, 60)
        self.setWindowTitle("KDC101 Loader")
        
    def changeProgressBar(self, nickname):
        if nickname in self._motor_list:
            self._motor_list.remove(nickname)
        self.progress_bar.changeProgressBar(self.num_motors-len(self._motor_list), self.num_motors)
        self.progress_bar.changeLabelText("Initiating motors (%d/%d)..." % (self.num_motors-len(self._motor_list), self.num_motors))
        
        if not len(self._motor_list):
            self.finishLoadingMotors()
            
    def startLoadingMotors(self):
        if len(self._motor_list):
            self.opener_timer = QTimer()
            self.opener_timer.setSingleShot(True)
            self.opener_timer.timeout.connect(self._open_loader)
            self.opener_timer.start(800)
            
    def finishLoadingMotors(self):
        self.progress_bar.completeProgressBar(True)
        self.progress_bar.changeLabelText("Finished initiating motors...")
        self.close()
        self.deleteLater()
        self.controller.showOnTop()
            
    def showOnTop(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
            
    def _open_loader(self):
        self.showOnTop()
        self.changeProgressBar("init")
    

        
if __name__ == "__main__":
    pmt = PMTAlginerGUI()
    pmt.show()
