# -*- coding: utf-8 -*-
"""
Created on Sat Aug 21 23:22:02 2021

Author: Junho Jeong
To update: The connection open the GUI, which is absurd.
"""
import os, sys
version = "2.2"

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout

from client_main_theme import client_gui_theme_base
main_ui_file = dirname + "/client_main_gui.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

class MainWindow(QtWidgets.QMainWindow, main_ui, client_gui_theme_base):
    
    menu_dict = {}
    panel_dict = {}
    library_dict = {}
    application_dict = {}
    tab_widgets = {"main_panel": None}
    
    def closeEvent(self, e):
        self.parent.socket.breakConnection(True)
        # closing devices
        for device, controller in self.device_dict.items():
            try:    
                controller.closeDevice()
            except Exception as err:
                print("An error while closing '%s', (%s)" % (device, err))
            
    def __init__(self, device_dict={}, config=None, parent=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.cp = config
        self._theme = theme
        self.parent = parent
        self.socket = self.parent.socket
        
        self.setupUi(self)
        self.device_dict = device_dict
        self._deviceSetup()
        if 'fpga' in self.cp.sections():
            self.setupSequencer()
        self._panelSetup()
        self._applicationSetup()
        self._librarySetup()
        self._initUi()
                
        self.parent._gui_signal.connect(self.handleServerMessage)
        
    def _deviceSetup(self):        
        self.menu_dict["device"] = {"menubar": self.menubar.addMenu("Devices")}
        tab_device_list = self._getListFromConfig(self.cp.get("gui", "device"))
        
        for device in tab_device_list:
            self.menu_dict["device"][device] = self.menu_dict["device"]["menubar"].addAction(self.cp.get(device, 'title'))
            self.menu_dict["device"][device].triggered.connect(self._guiControl)

            
    def _panelSetup(self):
        panel_list = self.cp["panels"]
        for panel in panel_list:
            # get the device nickname and its folder name from the section "device"
            sys.path.append(dirname + "/panels/%s" % (self.cp.get("panels", panel)))
            
            exec( "from %s import %s" % (self.cp.get(panel, 'file'), self.cp.get(panel, 'class')) )
            exec( "self.panel_dict['%s'] = %s(self.device_dict, self, self._theme)" % (panel, self.cp.get(panel, 'class')))
            exec( "self.panel_dict['%s'].changeTheme(self._theme)" % (panel))
            
    def _applicationSetup(self):
        self.menu_dict["applications"] = {"menubar": self.menubar.addMenu("Applications")}
        app_list = self.cp["applications"]
        for app in app_list:
            self.menu_dict["applications"][app] = self.menu_dict["applications"]["menubar"].addAction("%s" % self.cp.get(app, "title"))
            self.menu_dict["applications"][app].triggered.connect(self._launchApp)
            
    def _librarySetup(self):
        library_list = self.cp["libraries"]
        for library in library_list:
            sys.path.append(dirname + "/libraries/%s" % (self.cp.get("libraries", library)))
            exec( "from %s import %s" % (self.cp.get(library, 'file'), self.cp.get(library, 'class')) )
            exec( "self.library_dict['%s'] = %s()" % (library, self.cp.get(library, 'class')))
            
    def _launchApp(self):
        for key, val in self.menu_dict["applications"].items():
            if self.menu_dict["applications"][key] == self.sender():
                app = key
                
        if not app in self.application_dict.keys():
            sys.path.append(dirname + "/applications/%s" % (self.cp.get("applications", app)))
            exec( "from %s import %s" % (self.cp.get(app, 'file'), self.cp.get(app, 'class')) )
            exec( "self.application_dict['%s'] = %s(self.device_dict, self, self._theme, '%s')" % (app, self.cp.get(app, 'class'), app))
            exec( "self.application_dict['%s'].setStyleSheet(self._theme_base[self._theme])" % (app))

            if "changeTheme" in dir(self.application_dict[app]):
                self.application_dict[app].changeTheme(self._theme)

        self.application_dict[app].showNormal()
        self.application_dict[app].raise_()
        self.application_dict[app].activateWindow()
        
    def _guiControl(self):
        '''
        This function builds deivce windows following the config file.
        '''
        for device, action in self.menu_dict["device"].items():
            if self.sender() == action:
                self.openDeviceGui(device)
                
    def openDeviceGui(self, device):
        print("activated %s" % device)
        if not self.device_dict[device]._gui_opened:
            self.device_dict[device].openGui()

            if "changeTheme" in dir(self.device_dict[device].gui):
                self.device_dict[device].gui.changeTheme(self._theme)
            else:
                self.device_dict[device].gui.setStyleSheet(self._theme_base[self._theme])
                print("%s is changed by the main window" % device)
                
        self.device_dict[device].gui.showNormal()
        self.device_dict[device].gui.raise_()
        self.device_dict[device].gui.activateWindow()
                
            
    def _initUi(self):
        self.setWindowTitle("QtClient GUI v%s" % version)
        self.statusbar.setStyleSheet(self._statusbar_stylesheet[self._theme])
        self.TabWidgetMain.setStyleSheet(self._mainwindow_stylesheet[self._theme])
        self.menubar.setStyleSheet(self._menubar_stylesheet[self._theme])

        self._addTabWidgets(self.panel_dict)
        
    def _addTabWidgets(self, tab_dict=None):
        if tab_dict == None:
            tab_dict = self.tab_widgets
            
        self.tab = QTabWidget()
        for key in tab_dict.keys():
            self.tab.addTab(self.panel_dict[key], key)
            self.tab_widgets[key] = self.panel_dict[key]
            self.panel_dict[key].changeTheme(self._theme)
            
        vbox = QVBoxLayout()
        vbox.addWidget(self.tab)
        self.TabWidgetMain.setLayout(vbox)
        self.tab.setStyleSheet(self._tabbar_stylesheet[self._theme])
        
    def _getListFromConfig(self, config_content):
        content_without_blank = config_content.replace(" ", "")
        return content_without_blank.split(",")
            
    def makeConnection(self, IP, PORT):
        return self.socket.makeConnection(IP, PORT)
                    
    def breakConnection(self):
        self.socket.breakConnection(True)
        self.toStatusBar("Disconnected from the Server.")
        
    def toStatusBar(self, message, duration=8000):
        self.statusbar.showMessage(message, duration)
        
    def handleServerMessage(self, message_list):
        message = message_list.pop(1)
        if message == "HELO":
            self.toStatusBar("Connected to the Server.")
            
    def setupSequencer(self):
        sys.path.append(dirname + "/sequencer")
        from sequencer.Sequencer_Runner import SequencerRunner

        ser_num = self.cp.get('fpga', 'serial_number')
        hw_def = self.cp.get('fpga', 'hardware_definition')
        self.device_dict['sequencer'] = SequencerRunner(ser_num, hw_def, self)
        
        
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    client = MainWindow(device_dict={"DAC": None, "DDS": None})
    client.show()
    

    #app.exec_()
    #sys.exit(app.exec())