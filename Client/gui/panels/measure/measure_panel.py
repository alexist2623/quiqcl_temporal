# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 16:30:14 2021

Author: JHJeong32
"""
import os, sys, socket
version = "1.1"

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets, QtGui

from measure_panel_theme import measure_panel_theme_base
main_ui_file = dirname + "/measure_panel.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

class MeasurePanel(QtWidgets.QMainWindow, main_ui, measure_panel_theme_base):
 
    user_update = True
    
    MFF = None
    MFF_IP = "172.22.22.34"
    MFF_PORT = 52000
    
    SHT = None
    SHT_IP = "172.22.22.88"
    SHT_PORT = 51000
    
    LIT = None
    LIT_IP = "172.22.22.92"
    LIT_PORT = 53000
    
 
    def closeEvent(self, e):
        self.parent.socket.breakConnection(True)
    
    def __init__(self, device_dict={}, parent=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.device_dict = device_dict
        self.parent = parent
        self._theme = theme
        self.cp = self.parent.cp
        
        self._initUi()
        
        if "wm" in self.device_dict.keys():
            self.mini_wavemeter_dict = {}
            self._init_wavemeterUi()
            

    def _initUi(self):
        self.mirror_button_list = [self.BTN_mirror_left, self.BTN_mirror_right]
        self.shutter_button_list = [self.BTN_shutter_open, self.BTN_shutter_close]
        
        self.BTN_mirror_left.setIcon(QtGui.QIcon(dirname + '/icons/MIRROR_LEFT.png'))
        self.BTN_mirror_right.setIcon(QtGui.QIcon(dirname + '/icons/MIRROR_RIGHT.png'))
        self.BTN_shutter_open.setIcon(QtGui.QIcon(dirname + '/icons/SHUTTER_OPEN.png'))
        self.BTN_shutter_close.setIcon(QtGui.QIcon(dirname + '/icons/SHUTTER_CLOSE.png'))\
            
    def _init_wavemeterUi(self):
        sys.path.append(dirname + "/library/")
        max_num_channel = int(self.cp.get("measure_panel", "max_channel"))

        from mini_wavemeter_panel import Mini_WaveMeter
        from mini_wavemeter_panel_blank import Mini_WaveMeter_Blank
        
        channel_list = [int(x) for x in self.cp.get("measure_panel", "channel").split(",")]
        if len(channel_list) > max_num_channel:
            channel_list = channel_list[:max_num_channel]
        
        for channel in channel_list:
            
            mini_wm = Mini_WaveMeter(self.device_dict, self, channel, self._theme)
            self.mini_wavemeter_dict[channel] = mini_wm
            self.GBOX_wavemeter.layout().addWidget(mini_wm)
            mini_wm.changeTheme(self._theme)
            
        for _ in range(max_num_channel-len(channel_list)):
            self.GBOX_wavemeter.layout().addWidget(Mini_WaveMeter_Blank(self._theme))

                
        self.device_dict["wm"]._sig_gui_opened.connect(self._wavemeterGuiConnection)
        self._wavemeterGuiConnection(self.device_dict["wm"]._gui_opened)
        
        # panel_list = self.cp["panels"]
        # for panel in panel_list:
        #     # get the device nickname and its folder name from the section "device"
        #     sys.path.append(dirname + "/library/")
            
        #     exec( "from %s import %s" % (self.cp.get(panel, 'file'), self.cp.get(panel, 'class')) )
        #     exec( "self.panel_dict['%s'] = %s(self.device_dict, self, self._theme)" % (panel, self.cp.get(panel, 'class')))
        #     exec( "self.panel_dict['%s'].changeTheme(self._theme)" % (panel))
            
    def _wavemeterGuiConnection(self, flag):
        for wm_ch, mini_wm in self.mini_wavemeter_dict.items():
            mini_wm.enableGUI(flag)
            
            if flag:
                mini_wm.BTN_monitor.clicked.connect(self.device_dict["wm"].gui.monitorBtnList[wm_ch-1].click)
                mini_wm.CHBOX_use.clicked.connect(self.device_dict["wm"].gui.useCboxList[wm_ch-1].click)
                mini_wm.CHBOX_pid.clicked.connect(self.device_dict["wm"].gui.pidCboxList[wm_ch-1].click)
                mini_wm.GBOX_container.setTitle(self.device_dict["wm"].gui.chDisplayList[wm_ch-1].title())
        if flag:
            self.device_dict["wm"].gui._sigUseUpdated.connect(self._signalRouter)
            self.device_dict["wm"].gui._sigPIDUpdated.connect(self._signalRouter)
            self.device_dict["wm"].gui._sigFreqUpdated.connect(self._signalRouter)
                
    def _signalRouter(self, channel):
        if channel in self.mini_wavemeter_dict.keys():
            self.mini_wavemeter_dict[channel].updateValue()
            self.mini_wavemeter_dict[channel].updateGui()
        
    def connectToServer(self, IP, PORT):
        if type(PORT) == str:
            PORT = int(PORT)
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.settimeout(1)
        try:
            sck.connect((IP, PORT))
        except:
            self.toStatusBar("Failed to connect to the server (%s)." % IP)
            self.user_update = True
            
        return sck
    
    def disconnectFromServer(self):
        if not self.MFF == None: self.MFF.close()
        self.MFF = None
        
        if not self.SHT == None: self.SHT.close()
        self.SHT = None
        
        if not self.LIT == None: self.LIT.close()
        self.LIT = None
        
        self.toStatusBar("Disconnected from the mirror server.")
        
        self.resetUi()
    
    def controlMirror(self, command):
        mirror_idx = int(self.CBOX_mirror.currentText()[6:])
        try:
            self.MFF.sendall(bytes("MIRROR:%d:TURN:%s\n" % (mirror_idx, command), "latin-1"))
            self.MFF.recv(1024).decode('latin-1')
            self.toStatusBar("Mirror %d turned %s." % (mirror_idx, command))
        except:
            self.toStatusBar("Something wrong with the server. please reconnect.")
            
    def controlShutter(self, command):
        shutter_idx = int(self.CBOX_shutter.currentText()[7:])
        try:
            self.SHT.sendall(bytes("SHUTTER:%d:%s\n" % (shutter_idx, command), "latin-1"))
            self.SHT.recv(1024).decode('latin-1')
            self.toStatusBar("Shutter %d %s." % (shutter_idx, command))
        except:
            self.toStatusBar("Something wrong with the server. please reconnect.")
    
    def buttonConnectPressed(self, flag):
        if self.user_update:
            self.user_update = False
            if flag:
                self.MFF = self.connectToServer(self.MFF_IP, self.MFF_PORT)
                self.SHT = self.connectToServer(self.SHT_IP, self.SHT_PORT)
                self.LIT = self.connectToServer(self.LIT_IP, self.LIT_PORT)
                
                # enable light buttons
                self.BTN_Light_ON.setEnabled(True)
                self.BTN_Light_OFF.setEnabled(True)
                
                mirror_list = self.MFF.recv(1024).decode('latin-1')
                self.updateList("mirror", mirror_list)
                self.toStatusBar("Connected to the mirror server.")
                
            else:
                # enable light buttons
                self.BTN_Light_ON.setEnabled(False)
                self.BTN_Light_OFF.setEnabled(False)
                self.disconnectFromServer()
                
            self.user_update = True
        
    def buttonMirrorPressed(self, flag):        
        if self.user_update:
            self.user_update = False
            
            if self.MFF == None:
                self.sender().toggle()
                self.toStatusBar("You must connect to the server first.")
            
            else:
                sender_name = self.sender().objectName()
                for idx in range(len(self.mirror_button_list)):
                    if self.sender() == self.mirror_button_list[idx]:
                        self.mirror_button_list[not idx].setChecked(False)
                        self.controlMirror(sender_name[sender_name.rfind("_")+1:].upper())
                        
            self.user_update = True
        
    def buttonShutterPressed(self, flag):
        if self.user_update:
            self.user_update = False
            
            if self.SHT == None:
                self.sender().toggle()
                self.toStatusBar("You must connect to the server first.")
            
            else:
                sender_name = self.sender().objectName()
                for idx in range(len(self.shutter_button_list)):
                    if self.sender() == self.shutter_button_list[idx]:
                        self.shutter_button_list[not idx].setChecked(False)
                        self.controlShutter(sender_name[sender_name.rfind("_")+1:].upper())
                        
            self.user_update = True
            
    def buttonLightOnPressed(self):
        if self.user_update:
            self.user_update = False
            
            if self.LIT == None:
                self.toStatusBar("You must connect to the server first.")
            else:
                self.LIT.sendall(bytes("LIGHT:ON\n", "latin-1"))

            self.user_update = True
    
    def buttonLightOffPressed(self):
        if self.user_update:
            self.user_update = False
            
            if self.LIT == None:
                self.toStatusBar("You must connect to the server first.")
            else:
                self.LIT.sendall(bytes("LIGHT:OFF\n", "latin-1"))

            self.user_update = True

    def toStatusBar(self, message):
        if not self.parent == None:
            self.parent.toStatusBar(message)
        else:
            print(message)
        
    def updateList(self, dev_name, dev_list):
        self.CBOX_mirror.clear()
        mirror_list = dev_list.split(":")[2:]
        for mirror in mirror_list:
            if mirror[-1] == "\n":
                mirror = mirror[:-1]
            self.CBOX_mirror.addItem("%s" % mirror)
            
    def resetUi(self):
        self.user_update = False
        for item in self.mirror_button_list:
            item.setChecked(False)
        for item in self.shutter_button_list:
            item.setChecked(False)
            
        self.user_update = True
        
    def showEvent(self, event):
        self._updateStatus()
        
    def _updateStatus(self):
        pass
        
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    measure = MeasurePanel()
    measure.show()
    measure.changeTheme('black')

    #app.exec_()
    #sys.exit(app.exec())