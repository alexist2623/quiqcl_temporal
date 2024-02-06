# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 17:01:22 2021

@author: jhjeong
E-mail: jhjeong32@snu.ac.kr
Tel. 010-9600-3392
"""
from QtClient_basic_v0_01 import ClientSocket

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject
from configparser import ConfigParser

import os, sys
from queue import Queue

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

class ClientMain(QObject):
    
    cp = None
    user_name = "unanimous"
    IP = "127.0.0.1"
    device_dict = {}
    
    status = "standby"
    _fire_signal = pyqtSignal()
    _gui_signal = pyqtSignal(list)
    gui = None
    
    
    ccd_cnt = 0

    def __init__(self, gui=True):
        super().__init__()
        self._readConfig()
        self.socket = ClientSocket(self, self.user_name)
        self.socket._message_signal.connect(self.receivedMessage)
        self._msg_queue = Queue()


        self._setupDevices()
        if gui:
            sys.path.append(dirname + '/gui')
            from client_main_gui import MainWindow
            self.gui = MainWindow(self.device_dict, self.cp, self, self.cp.get("gui", "theme"))
        
        self._fire_signal.connect(self.dealMessageList)
        
    def _readConfig(self):
        PC_name = os.getenv('COMPUTERNAME', 'defaultValue')
        config_file = dirname + '/config/%s.ini' % PC_name
        # import os
        if not os.path.isfile(config_file):
            from shutil import copyfile
            copyfile(dirname + "/config/default.ini", config_file)
            
        
        self.cp = ConfigParser()
        self.cp.read(config_file)
        
        if self.cp.has_section("win_server"):
            self.IP = self.cp.get("win_server", "ip")
            self.PORT = int(self.cp.get("win_server", "port"))
        else:
            pass
            # raise Exception("there is no win server")
            
        if self.cp.has_section("client"):
            self.user_name = self.cp.get("client", "nickname")
            self.cp.set("client", "conf_file", config_file)
        else:
            pass
            # raise Exception("there is no client")

    def _setupDevices(self):
        sys.path.append(dirname + "/devices")
        device_list = self.cp['device']
        for device in device_list:
            # get the device nickname and its folder name from the section "device"
            sys.path.append(dirname + "/devices/%s/" % (device.upper()))
            sys.path.append(dirname + "/devices/%s/%s/" % (device.upper(), self.cp.get('device', device)))
            exec( "from %s import %s" % (self.cp.get(device, 'file'), self.cp.get(device, 'class')) )
            exec( "self.device_dict['%s'] = %s(socket=self)" % (device, self.cp.get(device, 'class')))

    def toMessageList(self, msg):
        self._msg_queue.put(msg)
        if self.status == "standby":
            self._fire_signal.emit()
        
    def dealMessageList(self):
        self.status = "sending"
        while self._msg_queue.qsize():
            msg = self._msg_queue.get()
            self.socket.sendMessage(msg)
        self.status = "standby"
        
    def receivedMessage(self, msg_list):
        device = msg_list.pop(1)
        if not device == "SRV":
            if device.lower() in self.device_dict.keys():
                self.device_dict[device.lower()].toWorkList(msg_list)
            else:
                print("No such device is in o8ur device dict! (%s)." % device)
        
        else:
            if not self.gui == None:
                self._gui_signal.emit(msg_list)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    client = ClientMain()
    if not client.gui == None:
        client.gui.show()
    else:
        print('error')
    app.exec_()
    sys.exit(app.exec())
    # print(client.socket.makeConnection(client.IP, client.PORT))
# client.socket.sendMessage(["C", "DAC", "ON", []])
# client.socket.sendMessage(["C", "DAC", "SETV", [0, 0.3, 1, -4, 2, -0.7, 12, 8]])
# client.socket.sendMessage(["C", "EA_SG38X", "CON", []])