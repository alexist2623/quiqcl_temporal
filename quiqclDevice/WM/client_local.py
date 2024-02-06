from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5 import uic

from configparser import ConfigParser
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from wavemeter_theme_base import WaveMeter_Theme_Base

import sys
import os

Ui_MainWindow = uic.loadUiType("UI/clientMainWindow.ui")[0]
# Ui_tabWindow = uic.loadUiType("UI/tabWidget.ui")[0]
# Ui_tabCalWindow = uic.loadUiType("UI/tabWidgetCal.ui")[0]
Ui_tabWindow = uic.loadUiType("UI/tabWidget_sep.ui")[0]
Ui_tabCalWindow = uic.loadUiType("Ui/tabWidgetCal_sep.ui")[0]
Ui_serverInfoWindow = uic.loadUiType("Ui/serverInfoWindow.ui")[0]
Ui_PIDWindow = uic.loadUiType("UI/PIDWidget.ui")[0]

status = {'disconnected':-1, 'stopped':0, 'started':1}

class MainWindow(QMainWindow, Ui_MainWindow, WaveMeter_Theme_Base):
    def closeEvent(self, QCloseEvent):
        if self.status != status['disconnected']:
            self.socket.sendMSG(['C', 'DCN', [self.socket.userName]])

    def __init__(self, theme="black"):
        super().__init__()
        self.setupUi(self)
        self.userName = ""
        self.channelList = {}
        self.monitorTabList = {}
        self.openChNum = 0
        self.calChNum = -1
        self.socket = Socket(self)
        self.status = status['disconnected']
        self.initUI()
        self._theme = theme

    def initUI(self):
        ### Initialize Menubar
        self.actionOpenConfig.setShortcut('Ctrl+O')
        self.actionOpenConfig.triggered.connect(self.openConfig)
        self.actionSaveConfig.setShortcut('Ctrl+S')
        self.actionSaveConfig.triggered.connect(self.saveConfig)
        self.actionSaveConfigDefault.setShortcut('Ctrl+Shift+S')
        self.actionSaveConfigDefault.triggered.connect(self.saveConfigDefault)
        self.actionExit.triggered.connect(self.close)
        self.actionConnect.triggered.connect(self.connectClicked)
        self.actionDisconnect.triggered.connect(self.connectClicked)
        self.actionDisconnect.setEnabled(False)
        self.actionServerStatus.setShortcut('Ctrl+I')
        self.actionServerStatus.triggered.connect(self.showServerInfo)
        self.actionServerStatus.setEnabled(False)

        ### Initialize Button
        self.btnConnect.clicked.connect(self.connectClicked)
        self.btnStart.clicked.connect(self.start)
        self.cboxFreq.clicked.connect(self.unitConvert)
        self.cboxWavelen.clicked.connect(self.unitConvert)

        ### Initialize Main Display
        self.useCboxList = [self.useCbox1, self.useCbox2, self.useCbox3, self.useCbox4,
                        self.useCbox5, self.useCbox6, self.useCbox7, self.useCbox8]
        self.pidCboxList = [self.pidCbox1, self.pidCbox2, self.pidCbox3, self.pidCbox4,
                        self.pidCbox5, self.pidCbox6, self.pidCbox7, self.pidCbox8]
        self.monitorBtnList = [self.btnMonitor1, self.btnMonitor2, self.btnMonitor3, self.btnMonitor4,
                        self.btnMonitor5, self.btnMonitor6, self.btnMonitor7, self.btnMonitor8]
        self.chDisplayList = [self.channel1, self.channel2, self.channel3, self.channel4,
                        self.channel5, self.channel6, self.channel7, self.channel8]
        self.currentFreqMonitorList = [self.currentFreq1, self.currentFreq2, self.currentFreq3, self.currentFreq4,
                        self.currentFreq5, self.currentFreq6, self.currentFreq7, self.currentFreq8]
        self.targetFreqMonitorList = [self.targetFreq1, self.targetFreq2, self.targetFreq3, self.targetFreq4,
                        self.targetFreq5, self.targetFreq6, self.targetFreq7, self.targetFreq8]
        for i in range(0, 8):
            self.useCboxList[i].setCheckable(False)
            self.useCboxList[i].clicked.connect(self.useCboxToggled)

            self.pidCboxList[i].setCheckable(False)
            self.pidCboxList[i].clicked.connect(self.pidCboxToggled)

            self.monitorBtnList[i].clicked.connect(self.monitorBtnClicked)

            self.chDisplayList[i].setHidden(True)

    def openConfig(self):
        ### Should be called only when disconnected or stopped
        if self.status == status['started']:
            self.statusBar().showMessage("Cannot open configuration file during start state")
            return

        homeDir = os.path.realpath(__file__)
        fname = QFileDialog.getOpenFileName(self, 'Open Configuration File', homeDir)
        if fname[0]:
            parser = ConfigParser()
            parser.read(fname[0])
            
            ### Validity check for the opened configuration file
            for section in parser.sections():
                if((section != 'Custom' and section[0:2] != 'CH') or
                ((section[0:2] == 'CH') and ((int(section[2]) < 1) or (int(section[2]) > 8)))):
                    self.statusBar().showMessage("Invalid configuration file")
                    return

            ### Hide all table rows again and show only rows corresponding to config
            self.channelList = {}
            self.monitorTabList = {}
            for i in range(0, 8):
                self.chDisplayList[i].setHidden(True)

            for section in parser.sections():
                if(section == 'Custom'):
                    self.userName = parser[section]['user name']
                    self.socket.userName = self.userName
                    self.historyDuration = int(parser[section]['historyduration'])
                    self.pidHistoryDuration = int(parser[section]['pidhistoryduration'])
                    # debug - print(self.socket.userName)
                
                elif(section[0:2] == 'CH'):
                    chNum = int(section[2])
                    name = parser[section]['laser name']
                    targetFreq = float(parser[section]['target frequency'])
                    targetWavelen = float(parser[section]['target wavelength'])
                    PP = float(parser[section]['P'])
                    II = float(parser[section]['I'])
                    DD = float(parser[section]['D'])
                    gain = float(parser[section]['gain'])
                    initOutput = float(parser[section]['initial output'])

                    self.channelList[chNum] = Channel(self, chNum, name, [targetFreq, targetWavelen, PP, II, DD, gain, initOutput])
                    if name != "780nm":
                        self.monitorTabList[chNum] = tabWidget(self, chNum, name)
                        self.chDisplayList[chNum-1].setTitle("Ch " + str(chNum) + " (" + name + ")")
                    else:
                        self.monitorTabList[chNum] = tabWidgetCal(self, chNum, name)
                        self.chDisplayList[chNum-1].setTitle("Ch " + str(chNum) + " (" + name + " - for calibration)")
                        self.calChNum = chNum              
                    self.monitorTabList[chNum].changeTheme(self._theme)

                    self.chDisplayList[chNum-1].setHidden(False)
                    if self.cboxFreq.isChecked():
                        if targetFreq != 0.0:
                            self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(targetFreq))
                        else:
                            self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(unitConvert(targetWavelen)))
                    else:
                        if targetWavelen == 0.0:
                            self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(unitConvert(targetFreq)))
                        else:
                            self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(targetWavelen))

    def saveConfig(self):
        config = ConfigParser()
        homeDir = os.path.realpath(__file__)

        if not self.channelList:
            self.statusBar().showMessage("No configuration to save")
            return
        
        config['Custom'] = {'user name': self.userName}
        for chNum, channel in self.channelList.items():
            if channel.targetFreq != 0.0:
                config['CH'+str(chNum)] = {'laser name': channel.name, 'target frequency': channel.targetFreq,
                'target wavelength': 0.0, 'P': channel.PP, 'I': channel.II, 'D': channel.DD, 'gain': channel.gain,
                'initial output': channel.currentOutput}
            else:
                config['CH'+str(chNum)] = {'laser name': channel.name, 'target frequency': 0.0,
                'target wavelength': channel.targetWavelen, 'P': channel.PP, 'I': channel.II, 'D': channel.DD, 'gain': channel.gain,
                'initial output': channel.currentOutput}

        fname = QFileDialog.getSaveFileName(self, 'Save Current Configuration', homeDir)
        configFile = open(fname[0], 'w')
        config.write(configFile)

        self.statusBar().showMessage("Current configuration saved")

    def saveConfigDefault(self):
        print("saveConfigDefault called")

    def showServerInfo(self):
        self.serverStatusWindow = ServerStatus(self)
        self.serverStatusWindow.show()

    def connectClicked(self):
        ### Disconnected status to stopped status
        if self.status == status['disconnected']:
            ### Check whether the configuration file is opened or not
            if not self.channelList:
                self.statusBar().showMessage("Configuration file should be opened first")
                return

            host = self.inputHostAddress.text()
            try:
                port = int(self.inputHostPort.text())
            except ValueError:
                self.statusBar().showMessage("Invalid port number")
                return

            if(self.socket.makeConnection(host, port) < 0):
                self.statusBar().showMessage("Fail to connect to the server")
                return

            ### Activate use buttons
            for chNum in self.channelList:
                self.useCboxList[chNum-1].setCheckable(True)

            self.status = status['stopped']
            self.btnConnect.setText('Disconnect')
            self.actionConnect.setEnabled(False)
            self.actionDisconnect.setEnabled(True)
            self.actionServerStatus.setEnabled(True)
            self.statusBar().showMessage("Successfully connect to the server")

        ### Stopped status to disconnected status
        elif self.status == status['stopped']:
            self.socket.breakConnection(True)
        
        elif self.status == status['started']:
            self.start()
            self.socket.breakConnection(True)
            

    def start(self):
        if self.status == status['stopped']:
            startChannelList = []
            ### Sends the channel of use-checked to the server
            for chNum in self.channelList:
                if self.channelList[chNum].useEnabled:
                    channel = self.channelList[chNum]
                    startChannelList.append(channel.name)          
                    ### Activate PID, focus buttons for the channels in the uselist
                    if channel.name != '780nm':
                        self.pidCboxList[chNum-1].setCheckable(True)
                        self.monitorTabList[chNum].cboxPID.setCheckable(True)
                        self.monitorTabList[chNum].cboxFocus.setCheckable(True)
                        self.monitorTabList[chNum].cboxAutoExp.setCheckable(True)
            message = ['C', 'SRT', startChannelList]
            self.socket.sendMSG(message)
            self.status = status['started']
            self.btnStart.setText("Stop")
            self.statusBar().showMessage("Wavemeter monitor started")

        elif self.status == status['started']:
            message = ['C', 'STP', []]
            self.socket.sendMSG(message)
            for chNum in self.channelList:
                if chNum != self.calChNum and self.channelList[chNum].useEnabled:
                    self.channelList[chNum].useEnabled = False
                    self.useCboxList[chNum-1].setChecked(False)
                    self.pidCboxList[chNum-1].setChecked(False)
                    self.pidCboxList[chNum-1].setCheckable(False)
                    self.monitorTabList[chNum].cboxPID.setChecked(False)
                    self.monitorTabList[chNum].cboxPID.setCheckable(False)
                    self.monitorTabList[chNum].cboxFocus.setChecked(False)
                    self.monitorTabList[chNum].cboxFocus.setCheckable(False)
                    self.monitorTabList[chNum].cboxAutoExp.setChecked(False)
                    self.monitorTabList[chNum].cboxAutoExp.setCheckable(False)
            self.btnStart.setText('Start')
            self.status = status['stopped']
            self.statusBar().showMessage("Wavemeter monitor stopped")

        elif self.status == status['disconnected']:
            self.statusBar().showMessage("Server not connected")

    def useCboxToggled(self):
        if not self.sender().isCheckable():
            return

        chNum = self.useCboxList.index(self.sender()) + 1
        checkBoxState = self.sender().isChecked()
        self.channelList[chNum].useEnabled = checkBoxState

        ### If the status is started, send "use on/off" to the server
        ### with activating the buttons for PID and Focus
        if self.status == status['started']:
            if checkBoxState == True:
                message = ['C', 'UON', [self.channelList[chNum].name]]
                if chNum != self.calChNum:
                    self.pidCboxList[chNum-1].setCheckable(True)
                    self.monitorTabList[chNum].cboxPID.setCheckable(True)
                    self.monitorTabList[chNum].cboxFocus.setCheckable(True)
                    self.monitorTabList[chNum].cboxAutoExp.setCheckable(True)
            else:
                message = ['C', 'UOF', [self.channelList[chNum].name]]
                if chNum != self.calChNum:
                    self.pidCboxList[chNum-1].setCheckable(False)
                    self.monitorTabList[chNum].cboxPID.setCheckable(False)
                    self.monitorTabList[chNum].cboxFocus.setCheckable(False)
                    self.monitorTabList[chNum].cboxAutoExp.setCheckable(False)
            self.socket.sendMSG(message)

    def pidCboxToggled(self):
        if not self.sender().isCheckable():
            return

        chNum = self.pidCboxList.index(self.sender()) + 1
        channel = self.channelList[chNum]
        checkBoxState = self.sender().isChecked()
        channel.pidEnabled = checkBoxState
        self.monitorTabList[chNum].cboxPID.setChecked(checkBoxState)

        ### Activate/inactivate slidebar and targetfreq, output spinbox
        self.monitorTabList[chNum].spinboxOutput.setReadOnly(checkBoxState)
        self.monitorTabList[chNum].btnSetOutput.setCheckable(not checkBoxState)
        self.monitorTabList[chNum].voltageSlider.setVisible(not checkBoxState)
        # q) inactivate changing target freq or not?
        
        ### Send "pid on/off" to the server
        if checkBoxState == True:
            data = [channel.name]
            if channel.targetFreq == 0.0:
                data.append('W')
                data.append(channel.targetWavelen)
            else:
                data.append('F')
                data.append(channel.targetFreq)
            data.append(channel.PP)
            data.append(channel.II)
            data.append(channel.DD)
            data.append(channel.gain)
            data.append(channel.currentOutput)
            message = ['C', 'PON', data]
        else:
            message = ['C', 'POF', [channel.name]]
        self.socket.sendMSG(message)
        
    def monitorBtnClicked(self):
        chNum = self.monitorBtnList.index(self.sender()) + 1
        status = self.monitorTabList[chNum].status
        if(status == False):
            self.monitorTabList[chNum].show()
            self.monitorTabList[chNum].status = True
        else:
            self.monitorTabList[chNum].activateWindow()

    def unitConvert(self):
        for chNum, channel in self.channelList.items():
            if self.sender().objectName() == "cboxFreq":
                self.currentFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.currentFreq))
                self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.targetFreq))
            elif self.sender().objectName() == "cboxWavelen":
                self.currentFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.currentWavelen))
                self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.targetWavelen))
            else:
                print(" # debug - who calls me?")

    def messageHandler(self, control, command, data):
        ### Server disconnect the communication
        if control == 'C' and command == 'DCN':
            if self.status == status['started']:
                self.start()
                self.socket.breakConnection(False)
            elif self.status == status['stopped']:
                self.socket.breakConnection(False)
            return

        ### Except for CON, DCN, SRT, STP, data[0] means the channel name
        if not (control == 'C' and command == 'WMS'):
            channelExist = False
            for chNum, channel in self.channelList.items():
                if channel.name == data[0]:
                    channelExist = channel.useEnabled
                    break
            if not channelExist:
                return

        if control == 'C':
            ### Someone turns on the PID
            if command == 'PON':
                if data[1] == 'W':
                    channel.targetWavelen = data[2]
                    channel.targetFreq = unitConvert(data[2])
                elif data[1] == 'F':
                    channel.targetFreq = data[2]
                    channel.targetWavelen = unitConvert(data[2])
                else:
                    # q) how to print error msg?
                    print("Wrong Format")
                    return
                channel.PP = data[3]
                channel.II = data[4]
                channel.DD = data[5]
                channel.gain = data[6]
                channel.currentOutput = data[7]
                channel.pidEnabled = True

                ### Turn on PID buttons on mainWindow and tabWidget with updating values
                self.pidCboxList[chNum-1].setChecked(True)
                self.monitorTabList[chNum].cboxPID.setChecked(True)
                self.monitorTabList[chNum].updatePIDui(data)
                ### Inactivate slidebar and output spinbox
                self.monitorTabList[chNum].spinboxOutput.setReadOnly(True)
                self.monitorTabList[chNum].btnSetOutput.setCheckable(False)
                self.monitorTabList[chNum].voltageSlider.setVisible(False)
                # q) inactivate changing target freq or not?
            elif command == 'POF':
                channel.pidEnabled = False
                ### Turn off PID buttons on mainWindow and targetWidget
                self.pidCboxList[chNum-1].setChecked(False)
                self.monitorTabList[chNum].cboxPID.setChecked(False)
                ### Activate slidebar and output spinbox
                self.monitorTabList[chNum].spinboxOutput.setReadOnly(False)
                self.monitorTabList[chNum].btnSetOutput.setCheckable(True)
                self.monitorTabList[chNum].voltageSlider.setVisible(True)
                # q) activate changing target freq or not?
            elif command == 'FON':
                ### Inactivate all PID, USE, focus checkboxes except the specified one
                self.statusBar().showMessage("Focus on the laser " + data[0] + " turned on")
                for chNum, channel in self.channelList.items():
                    if channel.name == '780nm':
                        # todo - what to do for 780nm when other channel is focused?
                        pass
                    elif channel.name != data[0]:
                        self.useCboxList[chNum-1].setCheckable(False)
                        self.pidCboxList[chNum-1].setCheckable(False)
                        self.monitorTabList[chNum].cboxPID.setCheckable(False)
                        self.monitorTabList[chNum].cboxFocus.setCheckable(False)
                        self.monitorTabList[chNum].cboxAutoExp.setCheckable(False)
                    else:
                        self.monitorTabList[chNum].cboxFocus.setChecked(True)
            elif command == 'FOF':
                self.statusBar().showMessage("Focused on the laser " + data[0] + " turned off")
                ### Activate all PID, USE, focus checkboxes
                for chNum, channel in self.channelList.items():
                    if channel.name == '780nm':
                        # todo what to do for 780nm when other channel is focused?
                        pass
                    else:
                        self.useCboxList[chNum-1].setCheckable(True)
                        self.pidCboxList[chNum-1].setCheckable(True)
                        self.monitorTabList[chNum].cboxPID.setCheckable(True)
                        self.monitorTabList[chNum].cboxFocus.setCheckable(True)
                        self.monitorTabList[chNum].cboxAutoExp.setCheckable(True)
                        if channel.useEnabled:
                            self.useCboxList[chNum-1].setChecked(True)
                        if channel.pidEnabled:
                            self.pidCboxList[chNum-1].setChecked(True)
                            self.monitorTabList[chNum].cboxPID.setChecked(True)
                        if channel.name == data[0]:
                            self.monitorTabList[chNum].cboxFocus.setChecked(False)
            elif command == 'AEN':
                self.monitorTabList[chNum].cboxAutoExp.setChecked(False)
            elif command == 'AEF':
                self.monitorTabList[chNum].cboxAutoExp.setChecked(False)
            elif command == 'NAK':
                ### data[0] : error code / data[1] : errored message
                if data[0] == -1:
                    print("Invalid control character '", data[1],"' sent to the server")
                elif data[0] == -2:
                    print("Invalid command '", data[1], "' sent to the server")
                elif data[0] == -3:
                    print("Invalid channel '", data[1], "' sent to the server")
                elif data[0] == -4:
                    print("Invalid data Control - ", data[1][0], ", Command - ", data[1][1], \
                        ", Data index - ", data[1][2], ", Data - ", data[1][3], "sent to the server")
            elif command == 'WMS':
                ### data[0] : list of channel name / data[1] : list of users in each channel
                ### data[2] : list of pid status / data[3] : list of focus status
                ### data[4] : list of fiber switch / data[5] : list of DAC channel
                ### data[6] : list of exp time set
                print("here")
                self.serverStatusWindow.displayInfo(data)
            else:
                # q) how to print error message
                print("Wrong format")
        elif control == 'D':
            if command == 'CFR':
                if data[1] != -3 and data[1] != -4:
                    channel.currentFreq = data[1]
                    channel.currentWavelen = unitConvert(data[1])
                    if self.cboxFreq.isChecked():
                        self.currentFreqMonitorList[chNum-1].setText("{:.6f}".format(data[1]))
                    else:
                        self.currentFreqMonitorList[chNum-1].setText("{:.6f}".format(unitConvert(data[1])))
                
                    if chNum == self.calChNum:
                        # todo - update for calTabWidget
                        # todo - consider over/under exposed for 780nm?
                        return

                    if self.monitorTabList[chNum].cboxFreq.isChecked():
                        self.monitorTabList[chNum].monitorCurrentFreq.setText("{:.6f}".format(data[1]))
                    else:
                        self.monitorTabList[chNum].monitorCurrentFreq.setText("{:.6f}".format(unitConvert(data[1])))
                    self.monitorTabList[chNum].updatePlot(data[2], channel.currentFreq)
                elif data[1] == -3:
                    self.currentFreqMonitorList[chNum-1].setText("Underexposed")
                    self.monitorTabList[chNum].monitorCurrentFreq.setText("Underexposed")
                else:
                    self.currentFreqMonitorList[chNum-1].setText("Overexposed")
                    self.monitorTabList[chNum].monitorCurrentFreq.setText("Overexposed")
            elif command == 'CWL':
                channel.currentFreq = unitConvert(data[1])
                channel.currentWavelen = data[1]
                if self.cboxWavelen.isChecked():
                    self.currentFreqMonitorList[chNum-1].setText("{:.6f}".format(data[1]))
                else:
                    self.currentFreqMonitorList[chNum-1].setText("{:.6f}".format(unitConvert(data[1])))

                if chNum == self.calChNum:
                    return

                if self.monitorTabList[chNum].cboxWavelen.isChecked():
                    self.monitorTabList[chNum].monitorCurrentFreq.setText("{:.6f}".format(data[1]))
                else:
                    self.monitorTabList[chNum].monitorCurrentFreq.setText("{:.6f}".format(unitConvert(data[1])))
                self.monitorTabList[chNum].updatePlot(data[2], channel.currentFreq)
            elif command == 'TWL':
                channel.targetFreq = unitConvert(data[1])
                channel.targetWavelen = data[1]
                if self.cboxWavelen.isChecked():
                    self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.targetWavelen))
                else:
                    self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.targetFreq))
                self.monitorTabList[chNum].spinboxTargetFreq.setValue(channel.targetFreq)
            elif command == 'TFR':
                channel.targetFreq = data[1]
                channel.targetWavelen = unitConvert(data[1])
                if self.cboxFreq.isChecked():
                    self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.targetFreq))
                else:
                    self.targetFreqMonitorList[chNum-1].setText("{:.6f}".format(channel.targetWavelen))
                self.monitorTabList[chNum].spinboxTargetFreq.setValue(channel.targetFreq)
            elif command == 'VLT':
                channel.currentOutput = data[1]
                self.monitorTabList[chNum].spinboxOutput.setValue(channel.currentOutput)
                self.monitorTabList[chNum].outputSetClicked(True)
            elif command == 'PPP':
                channel.PP = data[1]
                self.monitorTabList[chNum].PIDWidget.PSpinbox.setValue(channel.PP)
            elif command == 'III':
                channel.II = data[1]
                self.monitorTabList[chNum].PIDWidget.ISpinbox.setValue(channel.II)
            elif command == 'DDD':
                channel.DD = data[1]
                self.monitorTabList[chNum].PIDWidget.DSpinbox.setValue(channel.DD)
            elif command == 'GAN':
                channel.gain = data[1]
                self.monitorTabList[chNum].PIDWidget.gainSpinbox.setValue(channel.gain)
            elif command == 'EX1':
                channel.expTime = data[1]
                self.monitorTabList[chNum].spinboxExpTime.setValue(channel.expTime)
            elif command == 'APD':
                self.monitorTabList[chNum].PIDWidget.updatePlot(data[1:])
            else:
                # q) - how to print error message?
                print("Message of wrong format", command)
                return
            
        else:
            # q) how to print error message?
            print("Message of wrong format", control)
            return

class tabWidget(QMainWindow, Ui_tabWindow, WaveMeter_Theme_Base):
    def closeEvent(self, QCloseEvent):
        self.status = False

    def __init__(self, mw, chNum, name):
        super().__init__()
        self.setupUi(self)
        self.mw = mw
        self.socket = mw.socket
        self.chNum = chNum
        self.channel = self.mw.channelList[chNum]
        self.PIDWidget = PIDWidget(mw, self, chNum, name)
        self.PIDWidget.changeTheme(mw._theme)
        self.name = name
        self.status = False

        self.initUI()
        self.initPlot()

    def initUI(self):
        ### Initializing related values
        self.setWindowTitle(self.name)
        ### History Panel
        self.spinboxNumHistory.setValue(self.mw.historyDuration)
        self.scaleMinMax.setText("1e+3")
        self.spinboxMinmax.setValue(float(1.0))
        ### Control Panel
        self.voltageSlider.setValue(int(self.voltageSlider.maximum() * self.channel.currentOutput / 2.5))
        ### Monitor Panel
        self.spinboxTargetFreq.setValue(float("{:.6f}".format(self.channel.targetFreq)))
        self.spinboxOutput.setValue(self.channel.currentOutput)
        self.spinboxExpTime.setValue(self.channel.expTime)
        self.scaleTargetFreq.setText("1")
        self.spinboxTargetFreq.setSingleStep(0.000001)
        self.scaleOutput.setText("1")
        self.spinboxOutput.setSingleStep(0.001)
        self.scaleExpTime.setText("1")
        self.spinboxExpTime.setSingleStep(1)

        ### Inactivate checkboxes
        self.cboxAutoExp.setCheckable(False)
        self.cboxFocus.setCheckable(False)
        self.cboxPID.setCheckable(False)

        ### Event handler for history and voltage output slider
        self.btnSetNumHistory.clicked.connect(self.changeNumHistory)
        self.btnMinmaxRight.clicked.connect(self.increaseMinmaxStep)
        self.btnMinmaxLeft.clicked.connect(self.decreaseMinmaxStep)
        self.btnSetMinmax.clicked.connect(self.changeMinmax)
        self.voltageSlider.valueChanged.connect(self.sliderValueChanged)

        ### Event handler for checkboxes
        self.cboxFreq.clicked.connect(self.unitCboxToggled)
        self.cboxWavelen.clicked.connect(self.unitCboxToggled)
        self.cboxFocus.clicked.connect(self.focusCboxToggled)
        self.cboxAutoExp.clicked.connect(self.autoExpCboxToggled)
        self.cboxPID.clicked.connect(self.pidCboxToggled)

        ### Event handler for step modifying
        self.btnTargetFreqLeft.clicked.connect(self.decreaseStepTargetFreq)
        self.btnTargetFreqRight.clicked.connect(self.increaseStepTargetFreq)
        self.btnOutputLeft.clicked.connect(self.decreaseStepOutput)
        self.btnOutputRight.clicked.connect(self.increaseStepOutput)
        self.btnExpTimeLeft.clicked.connect(self.decreaseStepExpTime)
        self.btnExpTimeRight.clicked.connect(self.increaseStepExpTime)

        ### Event handler for pushButtons
        self.btnSetTargetFreq.clicked.connect(self.targetFreqSetClicked)
        self.btnSetOutput.clicked.connect(self.outputSetClicked)
        self.btnSetExpTime.clicked.connect(self.expTimeSetClicked)
        self.btnSetall.clicked.connect(self.setallClicked)
        self.btnPIDMonitor.clicked.connect(self.PIDMonitorClicked)

    def initPlot(self):
        self.x_timeList = []
        self.y_freqDiffList = []
        self.initTime = 0
        self.history = 0
        self.numHistory = self.spinboxNumHistory.value()
        self.maxFreq = (float(self.scaleMinMax.toPlainText()))*(self.spinboxMinmax.value())
        self.minFreq = -self.maxFreq

        self.canvas = PlotCanvas(self, self.plotPanel, 'C0', mw._theme)
        self.canvas.plot(top=0.9, bottom=0.22, left=0.15, right=0.9)

    def updatePlot(self, time, freq):
        if freq > 0.0:
            diff = (freq - self.channel.targetFreq) * 1e+6  ### MHz
            
            if self.cboxAutominmax.isChecked():
                if len(self.y_freqDiffList) == 0:
                    self.maxFreq = diff + 10
                    self.minFreq = diff - 10
                else:
                    self.maxFreq = max(self.y_freqDiffList)
                    self.minFreq = min(self.y_freqDiffList)
            if len(self.y_freqDiffList) <= self.numHistory:
                self.y_freqDiffList.append(diff)
                if len(self.x_timeList) == 0:
                    self.initTime = time
                    self.x_timeList.append(0)
                else:
                    self.x_timeList.append(time - self.initTime)
            else:
                self.x_timeList = self.x_timeList[len(self.x_timeList)-(self.numHistory):]
                self.x_timeList.append(time - self.initTime)
                self.y_freqDiffList = self.y_freqDiffList[len(self.y_freqDiffList)-(self.numHistory):]
                self.y_freqDiffList.append(diff)
        ### Overexposed
        elif freq == -4:
            self.statusbar.setText("Overexposed at time ", time)
        ### Underexposed
        elif freq == -3:
            self.statusbar.setText("Underexposed at time", time)

        self.history = self.history + 1

        if len(self.y_freqDiffList) > 1:
            self.canvas.ax.set_xlim(self.x_timeList[0], self.x_timeList[len(self.x_timeList)-1])
            self.canvas.ax.set_ylim(self.minFreq - 5.0e-1, self.maxFreq + 5.0e-1)
            self.canvas.line1.set_data(self.x_timeList, self.y_freqDiffList)
            self.canvas.fig.canvas.draw()
            self.canvas.fig.canvas.flush_events()

    def changeNumHistory(self):
        self.numHistory = self.spinboxNumHistory.value()

    def increaseMinmaxStep(self):
        value = list(self.scaleMinMax.toPlainText())
        exponent = int(value[-1])
        if exponent == 9:
            return
        value[-1] = str(exponent + 1)
        self.scaleMinMax.setText("".join(value))

    def decreaseMinmaxStep(self):
        value = list(self.scaleMinMax.toPlainText())
        exponent = int(value[-1])
        if exponent == 1:
            return
        value[-1] = str(exponent - 1)
        self.scaleMinMax.setText("".join(value))

    def changeMinmax(self):
        self.maxFreq = (float(self.scaleMinMax.toPlainText()))*(self.spinboxMinmax.value())
        self.minFreq = -self.maxFreq

    def sliderValueChanged(self):
        if self.voltageSlider.isSliderDown():
            newOutput = self.voltageSlider.value() * 2.5 / self.voltageSlider.maximum()
            self.spinboxOutput.setValue(newOutput)
            self.outputSetClicked(False)

    def targetFreqSetClicked(self):
        newTargetFreq = self.spinboxTargetFreq.value()
        self.channel.targetFreq = newTargetFreq
        self.channel.targetWavelen = unitConvert(newTargetFreq)
        if self.mw.cboxFreq.isChecked():
            self.mw.targetFreqMonitorList[self.chNum-1].setText("{:.6f}".format(self.channel.targetFreq))
        else:
            self.mw.targetFreqMonitorList[self.chNum-1].setText("{:.6f}".format(self.channel.targetWavelen))

        # todof - if changing target freq during pid is allowed, leave below
        # todof - otherwise, 'TRF' may be useless
        if self.mw.status == status['started']:
            self.socket.sendMSG(['D', 'TFR', [self.name, newTargetFreq]])

    def outputSetClicked(self, fromNetwork=False):
        newOutput = self.spinboxOutput.value()
        self.channel.currentOutput = newOutput
        max = self.voltageSlider.maximum()
        self.voltageSlider.setValue(int(max * newOutput / 2.5))

        if not fromNetwork and self.status == status['started']:
            self.socket.sendMSG(['D', 'VLT', [self.name, newOutput]])

    def expTimeSetClicked(self):
        newExpTime = self.spinboxExpTime.value()
        self.channel.expTime = newExpTime

        if self.mw.status == status['started']:
            self.socket.sendMSG(['D', 'EX1', [self.name, newExpTime]])

    def setallClicked(self):
        self.targetFreqSetClicked()
        self.outputSetClicked()
        self.expTimeSetClicked()

    def unitCboxToggled(self):
        if self.cboxFreq.isChecked():
            self.monitorCurrentFreq.setText("{:.6f}".format(self.channel.currentFreq))
        else:
            self.monitorCurrentFreq.setText("{:.6f}".format(self.channel.currentWavelen))

    def updatePIDui(self, data):
        ### Update target frequency/wavelength in the tabWidget
        if data[1] == 'W':
            if self.cboxWavelen.isChecked():
                self.spinboxTargetFreq.setValue(data[2])
            else:
                self.spinboxTargetFreq.setValue(unitConvert(data[2]))
        elif data[1] == 'F':
            if self.cboxWavelen.isChecked():
                self.spinboxTargetFreq.setValue(unitConvert(data[2]))
            else:
                self.spinboxTargetFreq.setValue(data[2])
        else:
            # q) how to print err message?
            print("Wrong Format")
            return
        self.spinboxExpTime.setValue(data[7])

        ### Update P, I, D, gain values in the PIDWidget
        self.PIDWidget.PSpinbox.setValue(self.channel.PP)
        self.PIDWidget.ISpinbox.setValue(self.channel.II)
        self.PIDWidget.DSpinbox.setValue(self.channel.DD)
        self.PIDWidget.gainSpinbox.setValue(self.channel.gain)

    def increaseStepTargetFreq(self):
        step = int(self.scaleTargetFreq.toPlainText())
        newStep = step + 1
        self.scaleTargetFreq.setText(str(newStep))
        self.spinboxTargetFreq.setSingleStep(newStep*(1e-6))

    def decreaseStepTargetFreq(self):
        step = int(self.scaleTargetFreq.toPlainText())
        newStep = step - 1
        if newStep <= 0:
            newStep = 1

        self.scaleTargetFreq.setText(str(newStep))
        self.spinboxTargetFreq.setSingleStep(newStep*(1e-6))

    def increaseStepOutput(self):
        step = int(self.scaleOutput.toPlainText())
        newStep = step + 1
        self.scaleOutput.setText(str(newStep))
        self.spinboxOutput.setSingleStep(newStep*(1e-3))

    def decreaseStepOutput(self):
        step = int(self.scaleOutput.toPlainText())
        newStep = step - 1
        if newStep <= 0:
            newStep = 1

        self.scaleOutput.setText(str(newStep))
        self.spinboxOutput.setSingleStep(newStep*(1e-3))

    def increaseStepExpTime(self):
        step = int(self.scaleExpTime.toPlainText())
        newStep = step + 1
        self.scaleExpTime.setText(str(newStep))
        self.spinboxExpTime.setSingleStep(newStep)

    def decreaseStepExpTime(self):
        step = int(self.scaleExpTime.toPlainText())
        newStep = step - 1
        if newStep <= 0:
            newStep = 1

        self.scaleExpTime.setText(str(newStep))
        self.spinboxExpTime.setSingleStep(newStep)
    
    def focusCboxToggled(self):
        if not self.sender().isCheckable():
            return 
        
        if self.cboxFocus.isChecked():
            self.socket.sendMSG(['C', 'FON', [self.name]])
            # todof - if cbox is checked after server's admission, add
            # self.cboxFocus.setChecked(False)
        else:
            self.socket.sendMSG(['C', 'FOF', [self.name]])
            # todof - if cbox is checked after server's admission, add
            # self.cboxFocus.setChecked(True)

    def autoExpCboxToggled(self):
        if not self.sender().isCheckable():
            return
        
        if self.cboxAutoExp.isChecked():
            self.socket.sendMSG(['D', 'AEN', [self.name]])
        else:
            self.socket.sendMSG(['D', 'AEF', [self.name]])

    def pidCboxToggled(self):
        if not self.sender().isCheckable():
            return

        checkBoxState = self.cboxPID.isChecked()
        self.channel.pidEnabled = checkBoxState
        self.mw.pidCboxList[self.chNum-1].setChecked(checkBoxState)

        ### Activate/inactivate slidebar and targetfreq, output spinbox
        self.spinboxOutput.setReadOnly(checkBoxState)
        self.btnSetOutput.setCheckable(not checkBoxState)
        self.voltageSlider.setVisible(not checkBoxState)
        # q) inactivate changing target freq or not?

        if checkBoxState:
            data = [self.name]
            if self.channel.targetFreq == 0.0:
                data.append('W')
                data.append(self.channel.targetWavelen)
            else:
                data.append('F')
                data.append(self.channel.targetFreq)
            data.append(self.channel.PP)
            data.append(self.channel.II)
            data.append(self.channel.DD)
            data.append(self.channel.gain)
            data.append(self.channel.currentOutput)
            message = ['C', 'PON', data]
        else:
            message = ['C', 'POF', [self.name]]
        self.socket.sendMSG(message)

    def PIDMonitorClicked(self):
        self.PIDWidget.show()
        self.PIDWidget.activateWindow()

class tabWidgetCal(QMainWindow, Ui_tabCalWindow, WaveMeter_Theme_Base):
    def closeEvent(self, QCloseEvent):
        self.status = False

    def __init__(self, mw, chNum, name):
        super().__init__()
        self.setupUi(self)
        self.mw = mw
        self.socket = mw.socket
        self.chNum = chNum
        self.channel = self.mw.channelList[chNum]
        self.name = name
        self.status = False

        self.initUI()

    def initUI(self):
        self.scaleExpTime.setText("1")
        self.spinboxExpTime.setSingleStep(1)
        self.scaleTargetFreq.setText("1")
        self.spinboxTargetFreq.setSingleStep(1e-6)

        self.btnExpTimeLeft.clicked.connect(self.decreaseExpTimeStep)
        self.btnExpTimeRight.clicked.connect(self.increaseExpTimeStep)
        self.btnSetExpTime.clicked.connect(self.expTimeSetClicked)
        self.btnTargetFreqLeft.clicked.connect(self.decreaseTargetFreqStep)
        self.btnTargetFreqRight.clicked.connect(self.increaseTargetFreqStep)
        self.btnSetTargetFreq.clicked.connect(self.targetFreqSetClicked)
        self.btnCalibrate.clicked.connect(self.btnCalClicked)
        self.btnCalOnce.clicked.connect(self.btnCalOnceClicked)

    def decreaseExpTimeStep(self):
        step = int(self.scaleExpTime.toPlainText())
        newStep = step - 1

        if(newStep <= 0):
            newStep = 1

        self.scaleExpTime.setText(str(newStep))
        self.spinboxExpTime.setSingleStep(newStep)

    def increaseExpTimeStep(self):
        step = int(self.scaleExpTime.toPlainText())
        newStep = step + 1

        self.scaleExpTime.setText(str(newStep))
        self.spinboxExpTime.setSingleStep(newStep)

    def expTimeSetClicked(self):
        newExpTime = int(self.spinboxExpTime.value())
        if newExpTime > 2000 or newExpTime < 0.0:
            # q) how to print error message
            self.spinboxExpTime.setValue(self.channel.expTime)
            return
        self.channel.expTime = newExpTime
        
        if self.mw.status == status['started']:
            self.socket.sendMSG(['D', 'EX1', [self.name, newExpTime]])

    def decreaseTargetFreqStep(self):
        step = int(self.scaleTargetFreq.toPlainText())
        newStep = step - 1
        if newStep <= 0:
            newStep = 1

        self.scaleTargetFreq.setText(str(newStep))
        self.spinboxTargetFreq.setSingleStep(newStep*(1e-6))

    def increaseTargetFreqStep(self):
        step = int(self.scaleTargetFreq.toPlainText())
        newStep = step + 1

        self.scaleTargetFreq.setText(str(newStep))
        self.spinboxTargetFreq.setSingleStep(newStep*(1e-6))

    def targetFreqSetClicked(self):
        newTargetFreq = float(self.spinboxTargetFreq.value())
        if newTargetFreq > 1000 or newTargetFreq < 0.0:
            self.spinboxTargetFreq.setValue(self.channel.targetFreq)
            return
        self.channel.targetFreq = newTargetFreq

        # todof - if changing target freq during calibration is allowed, leave below
        # todof - otherwise, 'TRF' may be useless
        if self.mw.status == status['started']:
            self.socket.sendMSG(['D', 'TFR', [self.name, newTargetFreq]])

    def btnCalClicked(self):
        self.socket.sendMSG(['C', 'CAL', [self.name, self.channel.targetFreq]])

    def btnCalOnceClicked(self):
        self.socket.sendMSG(['C', 'ACL', [self.name, self.channel.targetFreq]])

class PIDWidget(QMainWindow, Ui_PIDWindow, WaveMeter_Theme_Base):
    def __init__(self, mw, tab, chNum, name):
        super().__init__()
        self.setupUi(self)
        self.mw = mw
        self.tabWidget = tab
        self.chNum = chNum
        self.channel = self.mw.channelList[chNum]
        self.name = name

        self.initUI()
        self.initPlot()

    def initUI(self):
        self.setWindowTitle("PID Monitor - " + self.name)
        self.PSpinbox.setValue(self.channel.PP)
        self.ISpinbox.setValue(self.channel.II)
        self.DSpinbox.setValue(self.channel.DD)
        self.gainSpinbox.setValue(self.channel.gain)
        self.stepSpinbox.setText("1.0")

        self.btnSet.clicked.connect(self.updatePID)
        self.btnStepRight.clicked.connect(self.increaseStep)
        self.btnStepLeft.clicked.connect(self.decreaseStep)

    def initPlot(self):
        self.x_tries = []
        self.y_Pval = []
        self.y_Ival = []
        self.y_Dval = []
        self.y_Oval = []
        self.count = 0
        self.numPIDHistory = self.mw.pidHistoryDuration

        self.maxP = 0.0
        self.minP = 0.0
        self.maxI = 0.0
        self.minI = 0.0
        self.maxD = 0.0
        self.minD = 0.0
        self.maxO = 0.0
        self.minO = 0.0

        self.canvasP = PlotCanvas(self, self.PGroupBox, 'C3', mw._theme)
        self.canvasI = PlotCanvas(self, self.IGroupBox, 'C2', mw._theme)
        self.canvasD = PlotCanvas(self, self.DGroupBox, 'C1', mw._theme)
        self.canvasO = PlotCanvas(self, self.OutGroupBox, 'C5', mw._theme)

        self.canvasP.plot(top = 0.95, bottom = 0.3, left = 0.28, right = 0.85)
        self.canvasI.plot(top = 0.95, bottom = 0.3, left = 0.28, right = 0.85)
        self.canvasD.plot(top = 0.95, bottom = 0.3, left = 0.28, right = 0.85)
        self.canvasO.plot(top = 0.95, bottom = 0.3, left = 0.28, right = 0.85)

    def updatePlot(self, APD):
        accum = APD[0] * (1e+3)
        prop = APD[1] * (1e+3)
        diff = APD[2] * (1e+3)
        out = self.channel.currentOutput

        if self.count == 0:
            self.maxP = prop + 1.0
            self.minP = prop - 1.0
            self.maxI = accum + 1.0
            self.minI = accum - 1.0
            self.maxD = diff + 1.0
            self.minD = diff - 1.0
            self.maxO = out + 1.0
            self.minO = out - 1.0

        if accum > self.maxI:
            self.maxI = accum
        elif accum < self.minI:
            self.minI = accum
        
        if prop > self.maxP:
            self.maxP = prop
        elif prop < self.minP:
            self.minP = prop

        if diff > self.maxD:
            self.maxD = diff
        elif diff < self.minD:
            self.minD = diff

        if out > self.maxO:
            self.maxO = out
        elif out < self.minO:
            self.minO = out

        if self.count <= self.numPIDHistory:
            self.count += 1
            self.x_tries.append(self.count)
            self.y_Pval.append(prop)
            self.y_Ival.append(accum)
            self.y_Dval.append(diff)
            self.y_Oval.append(out)
        
        else:
            self.count += 1
            del self.x_tries[0]
            self.x_tries.append(self.count)
            del self.y_Pval[0]
            self.y_Pval.append(prop)
            del self.y_Ival[0]
            self.y_Ival.append(accum)
            del self.y_Dval[0]
            self.y_Dval.append(diff)
            del self.y_Oval[0]
            self.y_Oval.append(out)

        self.canvasP.ax.set_xlim(self.x_tries[0], self.x_tries[len(self.x_tries)-1])
        self.canvasP.ax.set_ylim(self.minP, self.maxP)
        self.canvasP.line1.set_data(self.x_tries, self.y_Pval)
        self.canvasP.draw()

        self.canvasI.ax.set_xlim(self.x_tries[0], self.x_tries[len(self.x_tries)-1])
        self.canvasI.ax.set_ylim(self.minI, self.maxI)
        self.canvasI.line1.set_data(self.x_tries, self.y_Ival)
        self.canvasI.draw()
        
        self.canvasD.ax.set_xlim(self.x_tries[0], self.x_tries[len(self.x_tries)-1])
        self.canvasD.ax.set_ylim(self.minD, self.maxD)
        self.canvasD.line1.set_data(self.x_tries, self.y_Dval)
        self.canvasD.draw()

        self.canvasO.ax.set_xlim(self.x_tries[0], self.x_tries[len(self.x_tries)-1])
        self.canvasO.ax.set_ylim(self.minO, self.maxO)
        self.canvasO.line1.set_data(self.x_tries, self.y_Oval)
        self.canvasO.draw()

    def updatePID(self):
        chName = self.name
        self.channel.PP = float(self.PSpinbox.value())
        self.channel.II = float(self.ISpinbox.value())
        self.channel.DD = float(self.DSpinbox.value())
        self.channel.gain = float(self.gainSpinbox.value())

        self.mw.socket.sendMSG(['D', 'PPP', [chName, self.channel.PP]])
        self.mw.socket.sendMSG(['D', 'III', [chName, self.channel.II]])
        self.mw.socket.sendMSG(['D', 'DDD', [chName, self.channel.DD]])
        self.mw.socket.sendMSG(['D', 'GAN', [chName, self.channel.gain]])

    def increaseStep(self):
        step = float(self.stepSpinbox.toPlainText())
        newStep = step + 0.1
        self.stepSpinbox.setText("{:.1f}".format(newStep))

        self.PSpinbox.setSingleStep(newStep)
        self.ISpinbox.setSingleStep(newStep)
        self.DSpinbox.setSingleStep(newStep)
        self.gainSpinbox.setSingleStep(newStep)

    def decreaseStep(self):
        step = float(self.stepSpinbox.toPlainText())
        newStep = step - 0.1
        
        ### newStep should be positive
        if(newStep <= 0):
            newStep = 0.1

        self.stepSpinbox.setText("{:.1f}".format(newStep))

        self.PSpinbox.setSingleStep(newStep)
        self.ISpinbox.setSingleStep(newStep)
        self.DSpinbox.setSingleStep(newStep)
        self.gainSpinbox.setSingleStep(newStep)

class ServerStatus(QMainWindow, Ui_serverInfoWindow, WaveMeter_Theme_Base):
    def __init__(self, mw):
        super().__init__()
        self.setupUi(self)
        self.actionRefresh.setShortcut('F5')
        self.actionRefresh.triggered.connect(self.requestWMS)
        self.mw = mw

        self.requestWMS()

    def requestWMS(self):
        if self.mw.status == status['disconnected']:
            self.statusBar().showMessage("Not connected to the server")
        else:
            self.mw.socket.sendMSG(['C', 'WMS', []])

    def displayInfo(self, data):
        ### data[0] : list of channel name / data[1] : list of users in each channel
        ### data[2] : list of pid status / data[3] : list of focus status
        ### data[4] : list of fiber switch / data[5] : list of DAC channel
        ### data[6] : list of exp time set
        print("called")
        for i in range(len(data[0])):
            self.infoTable.setItem(i, 0, QTableWidgetItem(data[0][i]))
            self.infoTable.setItem(i, 2, QTableWidgetItem(str(data[4][i])))
            self.infoTable.setItem(i, 3, QTableWidgetItem(str(data[5][i])))
            self.infoTable.setItem(i, 4, QTableWidgetItem(str(data[2][i])))

            text = ""
            for user in data[1][i]:
                text = text + " / " + user
            if text != "":
                text = text[3:]
            self.infoTable.setItem(i, 1, QTableWidgetItem(text))

class PlotCanvas(FigureCanvas):
    def __init__(self, parent, frame, color, theme="black"):
        self.parentWindow = parent
        self.frame = frame
        self.fig = Figure(dpi = 140)
        super().__init__(self.fig)

        layout = QHBoxLayout()
        layout.layoutLeftMargin = 0
        layout.layoutRightMargin = 0
        layout.layoutTopMargin = 0
        layout.layoutBottomMargin = 0

        layout.addWidget(self)
        self.frame.setLayout(layout)

        super().updateGeometry()
        self.setParent(self.frame)
        # self.parentWindow.resize.connect(self.updateSize)
        self.ax = self.fig.add_subplot(1,1,1)
        self.line1, = self.ax.plot([],[], color)
        
        spine_list = ['bottom', 'top', 'right', 'left']
        
        if theme == "black":
            plt.style.use('dark_background')
            plt.rcParams.update({"savefig.facecolor": [0.157, 0.157, 0.157],
                                "savefig.edgecolor": [0.157, 0.157, 0.157]})
            
            self.fig.set_facecolor([0.157, 0.157, 0.157])
            self.ax.set_facecolor([0.157, 0.157, 0.157])
            self.ax.tick_params(axis='x', colors=[0.7, 0.7, 0.7], length=0)
            self.ax.tick_params(axis='y', colors=[0.7, 0.7, 0.7], length=0)
            
            for spine in spine_list:
                self.ax.spines[spine].set_color([0.7, 0.7, 0.7])
                
        elif theme == "white":
            plt.style.use('default')
            plt.rcParams.update({"savefig.facecolor": [1, 1, 1],
                                "savefig.edgecolor": [1, 1, 1]})
            self.fig.set_facecolor([1, 1, 1])
            self.ax.set_facecolor([1, 1, 1])
            self.ax.tick_params(axis='x', colors='k', length=0)
            self.ax.tick_params(axis='y', colors='k', length=0)
            
            for spine in spine_list:
                self.ax.spines[spine].set_color('k')
            self.toolbar.setStyleSheet("background-color:rgb(255, 255, 255);")
            
            

    def plot(self, top, bottom, left, right):
        self.fig.subplots_adjust(top = top, bottom = bottom, left = left, right = right)

    def updateSize(self):
        self.fig.set_size_inches(self.frame.width() / 140, self.frame.height() / 140, forward = True)

class Socket(QTcpSocket):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw
        self.userName = ""
        self.blockSize = 0
        
        self.readyRead.connect(self.receiveMSG)
        self.disconnected.connect(self.breakConnection)

    def makeConnection(self, host, port):
        self.connectToHost(host, int(port), QIODevice.ReadWrite)
        if(self.waitForConnected(1000) != True):
            return -1

        ### Send CON message to notify the name of the user
        message = ['C', 'CON', [self.userName]]
        self.sendMSG(message)
        return 0

    def breakConnection(self, spontaneous=False):
        if spontaneous:
            self.sendMSG(['C', 'DCN', [self.userName]])
            self.disconnectFromHost()
        self.mw.status = status['disconnected']
        self.mw.btnConnect.setText('Connect')
        self.mw.btnStart.setText('Start')
        self.mw.actionConnect.setEnabled(True)
        self.mw.actionDisconnect.setEnabled(False)

    def sendMSG(self, msg):
        if not self.isOpen():
            self.mw.statusBar().showMessage("Server not connected")
            self.status = status['disconnected']
            return

        block = QByteArray()
        output = QDataStream(block, QIODevice.WriteOnly)
        output.setVersion(QDataStream.Qt_5_0)

        output.writeUInt16(0)
        output.writeQString(msg[0])         ### flag C/S
        output.writeQString(msg[1])         ### command of 3 or 4 characters
        output.writeQVariantList(msg[2])    ### data
        output.device().seek(0)
        output.writeUInt16(block.size()-2)

        self.write(block)

    def receiveMSG(self):
        stream = QDataStream(self)
        stream.setVersion(QDataStream.Qt_5_0)
        while True:
            if self.blockSize == 0:
                if self.bytesAvailable() < 2:
                    return
                self.blockSize = stream.readUInt16()
            if self.bytesAvailable() < self.blockSize:
                return

            control = str(stream.readQString())     ### flag C/S
            command = str(stream.readQString())     ### command of 3 or 4 characters
            data = list(stream.readQVariantList())   ### data
            self.blockSize = 0
            print(control, command, data)

            self.mw.messageHandler(control, command, data)

class Channel():
    def __init__(self, mw, chNum, name, list):
        self.mw = mw
        self.num = chNum
        self.name = name
        if list[0] == 0.0:
            assert list[1] != 0.0
            self.targetFreq = unitConvert(list[1])
        else:
            self.targetFreq = list[0]
        if list[1] == 0.0:
            assert list[0] != 0.0
            self.targetWavelen = unitConvert(list[0])
        else:
            self.targetWavelen = list[1]
        self.PP = list[2]
        self.II = list[3]
        self.DD = list[4]
        self.gain = list[5]
        self.expTime = 0

        self.currentFreq = 0.0
        self.currentWavelen = 0.0
        self.currentOutput = list[6]

        self.useEnabled = False
        self.pidEnabled = False
        self.focusEnabled = False

def unitConvert(val):
    SpeedOfLight = 299792458.0
    return SpeedOfLight/float(val)/1000.0


if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    mw = MainWindow()
    mw.show()
    mw.openConfig()
    mw.changeTheme(mw._theme)
    
    # app = QApplication(sys.argv)
    # mw = MainWindow()
    # mw.show()
    # mw.openConfig()
    #sys.exit(app.exec_())