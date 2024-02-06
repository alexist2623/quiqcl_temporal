# -*- coding: utf-8 -*-
"""
Created on Sat Sep  4 23:30:12 2021

@author: jhjeong
e-mail: jhjeong32@snu.ac.kr
Tel. 010-9600-3392
"""
import sys, os

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtWidgets


from configparser import ConfigParser
from QtServer_Request_Handler_v0_01 import RequestHandler
from QtDeviceBase_v0_01 import DeviceServerBase

import logging
from logging.handlers import TimedRotatingFileHandler

class DeviceServer(DeviceServerBase):
    """
    v0.02: Load devices by a config file.
    
    This class simply gathers the necessary modules to run the server.
        - It creates a logger to record the history of the server
        - It imports device controller modules to device_dict
        - Opens the RequestHandler that deals the communications.
    """
    def __init__(self, auto_setup=True):
        super().__init__()
        self._readConfig(auto_setup)
        self._makeLogger()
        self._setupDevices()
        
        # Open server
        self.rh = RequestHandler(self.device_dict, self.logger.getChild("RequestHandler"))
        status = self.rh.openSession(self.IP, self.PORT)
        if status == 1:
            self.logger.info("Session opened.")
        elif status == 0:
            self.logger.info("Session already opened")
        elif status == -1:
            self.logger.warning("Failed to open the session")
        
    def _readConfig(self, auto_setup):
        self._default_ini_path = dirname + '/config/'
        # self._default_ini_path = default_ini_path.replace("\\", "/")
        if auto_setup:
            config_file = self._default_ini_path + self._getHostName() + '.ini'
        else:
            config_file = QFileDialog.getOpenFileName(None, 'Open .ini file.', self._default_ini_path, 'ini files(*.ini)')[0]
        if not os.path.isfile(config_file):
            self._makeDefault_ini(self._default_ini_path + "default.ini", self._default_ini_path + self._getHostName() + '.ini')
        
        self.cp = ConfigParser()
        self.cp.read(config_file)
        self.IP = self.cp.get("server", "ip")
        self.PORT = int(self.cp.get("server", "port"))
        
    def _setupDevices(self):
        sys.path.append(dirname + "/devices")
        # Added in the new version
        device_dir_list = os.listdir(dirname + "/devices")
        for device_dir in device_dir_list:
            if os.path.isdir(dirname + "/devices/" + device_dir):
                sys.path.append(dirname + "/devices/" + device_dir)
        
        device_list = self.cp['device']
        for device in device_list:
            # get the device nickname and its folder name from the section "device"
            
            exec( "from %s import %s" % (self.cp.get(device, 'file'), self.cp.get(device, 'class')) )
            exec( "self.device_dict['%s'] = %s(self, self.cp, logger=self.logger.getChild('%s'), device='%s')" % (device.upper(), self.cp.get(device, 'class'), device, device))

            print("Opened %s" % device)

    def _makeLogger(self, log_name = "QtDeviceServer_log"):
        self.logger = logging.getLogger("Server")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        log_path = os.path.dirname(__file__) + "/Logs/"
        if not os.path.exists(log_path):
            os.mkdir(log_path)
            
        log_name = log_name
        handler = TimedRotatingFileHandler(log_path + log_name + '.log', when="midnight", interval=10)
        handler.setFormatter(formatter)
        handler.suffix = "%Y%m%d"
        self.logger.addHandler(handler)
        
    def _makeDefault_ini(self, default_name, copyname):
        from shutil import copyfile
        try:
            print("No initial config file has been found. A default ini file has been copied and renamed to '%s'" % os.path.basename(copyname))
            copyfile(default_name, copyname)
        except Exception as ee:
            raise FileNotFoundError ("No such file has been found: %s" % default_name)
            print("Error: %s" % ee)
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    if app is None:
        app = QtWidgets.QApplication([])
    srv = DeviceServer(True)
    app.exec_()
    sys.exit(app.exec())
    
    
if __name__ == "__main__":
    # app = QtWidgets.QApplication(sys.argv)
    # if app is None:
    #     app = QtWidgets.QApplication([])
    # srv = DeviceServer(True)
    # app.exec_()
    # sys.exit(app.exec())
    main()
