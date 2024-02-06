# -*- coding: utf-8 -*-
"""
Thie Oven controller class is designed to be integrated with the CCD GUI

The oven is controlled by a raspberry pi and sending data through TCP communication.

Some modification requires if you want to controll the oven in local with USB.

v0.02: It gets theme color from the parent.
"""
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread

import socket
import time

class Oven_controller(QtWidgets.QWidget):
    
    closing = pyqtSignal(int)

    def close_oven(self):
        self.HeaterON(False)
        print("closing the oven...")
        while self.OVEN.isRunning():
            time.seep(0.2)
        self.OVEN.oven.close()
        self.OVEN.mirror.close()
    
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.GUI = parent
        self.OVEN = OvenClient()
        self.OVEN.OC = self

        self.ON = False
        
        self.V_Label = self.GUI.LBL_vol_val
        self.I_Label = self.GUI.LBL_cur_val
        self.BTN_ON = self.GUI.BTN_oven_on
        self.Timer = self.GUI.NON_Timer
               
        # connect
        self.BTN_ON.toggled.connect(self.HeaterON)
            
        # Ui Setup
        self.OVEN.time_signal.connect(self.uiUPDATE)
        self.OVEN.vol_signal.connect(self.volLABEL)
        self.OVEN.cur_signal.connect(self.curLABEL)
        self.OVEN.off_signal.connect(self.RestoreACT)
        
    def HeaterON(self, on_flag):
        if on_flag:
            self.ON = True
            try:
                self.OVEN.oven.sendall(bytes("SHUTTER:1:OPEN\n", 'latin-1'))
            except:
                print("Lost connection to the oven server. trying to reconnect.")
                try:
                    self.OVEN.connect_to_oven()
                    self.OVEN.oven.sendall(bytes("SHUTTER:1:OPEN\n", 'latin-1'))
                except:
                    print("Failed to reconnect. please check the status of the server.")
                
            self.OVEN.oven.recv(1024)
            
            if self.GUI.CBOX_target.currentText().split('_')[-1] == "EC":
                mirror_direction = "LEFT"
                
                if self.GUI.RDO_174.isChecked():
                    self.CH = "10"
                else:
                    self.CH = "11"
            else: 
                mirror_direction = "RIGHT"
                
                if self.GUI.RDO_174.isChecked():
                    self.CH = "00"
                else:
                    self.CH = "01"
                    
            try:
                self.OVEN.mirror.sendall(bytes("MIRROR:2:TURN:%s\n" % (mirror_direction), 'latin-1'))
            except:
                print("Lost connection to the mirror server. trying to reconnect.")
                try:
                    self.OVEN.connect_to_mirror()
                    self.OVEN.mirror.sendall(bytes("MIRROR:2:TURN:LEFT\n", 'latin-1'))
                except:
                    print("Failed to reconnect. please check the status of the server.")
            self.OVEN.mirror.recv(1024)
            
            self.OVEN.oven.sendall(bytes("OVEN:%s:ON\n" % self.CH, 'latin-1'))
            data = self.OVEN.oven.recv(1024)
            
            # If the chamber is busy, nothing to do
            if "BUSY" in data.decode('latin-1'):
                self.RestoreACT()
                print("The oven is busy!. Maybe it is occupied by another client.")
            else:
                self.OVEN.start()
                
        else:
            if self.ON:
                self.OVEN.oven.sendall(bytes("OVEN:%s:OFF\n" % self.CH, 'latin-1'))
                self.BTN_ON.setEnabled(False)
                if self.GUI.CBOX_turn_off.isChecked():
                    time.sleep(0.2)
                    self.OVEN.oven.sendall(bytes("SHUTTER:1:CLOSE\n", 'latin-1'))
                    data = self.OVEN.oven.recv(1024).decode('latin-1')
                    if "CLOSE" in data:
                        print("Shutter closed.")
            else:
                self.RestoreACT()
            
        
    def RestoreACT(self):
        """
        RestoreACT resets the GUI button and functions
        """
        self.BTN_ON.setEnabled(True)
        
        self.volLABEL(0)
        self.curLABEL(0)
        self.Timer.setStyleSheet('')
        self.Timer.setText("Timer: 00:00")
        
    
    def uiUPDATE(self, count):
        if 0 < count and count <= 60:
            self.Timer.setStyleSheet('color:rgb(255, 0, 0)')
        else:
            self.Timer.setStyleSheet('')
            
        self.Timer.setText("Timer: %02d:%02d" % (count / 60, count % 60))
        
    def volLABEL(self, vol):
        if not self.ON: vol = 0
        self.V_Label.setText("%.3f" % vol)
            
    def curLABEL(self, cur):
        if not self.ON: cur = 0
        self.I_Label.setText("%.3f" % cur)
    
class OvenClient(QThread):
    
    time_signal = pyqtSignal(int)
    cur_signal = pyqtSignal(float)
    vol_signal = pyqtSignal(float)
    off_signal = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__()
        self.OC = parent
        self.connect_to_oven()
        self.connect_to_mirror()

    def connect_to_oven(self):
        # conenct to oven. oven controller is a Raspberry pi
        self.oven = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.oven.connect(("172.22.22.88", 51000))
        self.oven.settimeout(1)

    def connect_to_mirror(self):
        # connect to mirror. mirror controller is a windows PC
        self.mirror = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mirror.connect(('172.22.22.34', 52000))
        self.mirror.settimeout(1)
        
        
        
    def run(self):
        while self.OC.ON:
            line = self.oven.recv(1024).decode('latin-1')
            cmds = line.split('\n')[:-1]
            
            for cmd in cmds:
                each_cmd = cmd.split(':')
                if "CNT" in cmd:
                    idx = each_cmd.index("CNT") + 1
                    val = int(each_cmd[idx])
                    if val > 0:
                        self.time_signal.emit(val)
                elif "VOL" in cmd:
                    idx = each_cmd.index("VOL") + 1
                    val = float(each_cmd[idx])
                    if val > 0:
                        self.vol_signal.emit(val)
                elif "CUR" in cmd:
                    idx = each_cmd.index("CUR") + 1
                    val = float(each_cmd[idx])
                    if val > 0:
                        self.cur_signal.emit(val)
                elif "OFF" in cmd:
                    if self.OC.ON:
                        self.OC.ON = False
                        self.off_signal.emit(1)

            
            time.sleep(0.3)
            