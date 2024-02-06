# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ADC_GUI_ex5.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from ADC_Client_Controller import ADC_ClientInterface
from PyQt5.QtCore import pyqtSignal, QObject

class Ui_MainWindow(QObject):
    
    _update_signal = pyqtSignal(list)
    
    
    def __init__(self, controller = None):
        super().__init__()
        self.controller = controller
        self.controller = ADC_ClientInterface()
        self._is_connected = False
        self._is_running = False
        self.current_channel = 0 
        self.voltData_plot = {0:[], 1:[], 2:[], 3:[]}
    
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(737, 440)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Channelbox = QtWidgets.QComboBox(self.centralwidget)
        self.Channelbox.setGeometry(QtCore.QRect(540, 30, 181, 31))
        self.Channelbox.setObjectName("Channelbox")
        self.Channelbox.addItem("")
        self.Channelbox.addItem("")
        self.Channelbox.addItem("")
        self.Channelbox.addItem("")
        self.connect_button = QtWidgets.QPushButton(self.centralwidget)
        self.connect_button.setGeometry(QtCore.QRect(540, 220, 181, 91))
        self.connect_button.setStyleSheet("font: 75 20pt \"Cambria\";\n"
"")
        self.connect_button.setObjectName("connect_button")
        self.start_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(540, 320, 181, 91))
        self.start_button.setStyleSheet("font: 75 20pt \"Cambria\";")
        self.start_button.setObjectName("start_button")
        self.plot = QtWidgets.QGraphicsView(self.centralwidget)
        self.plot.setGeometry(QtCore.QRect(15, 31, 511, 381))
        self.plot.setObjectName("plot")
        self.selected_channel = QtWidgets.QLabel(self.centralwidget)
        self.selected_channel.setGeometry(QtCore.QRect(540, 80, 161, 16))
        self.selected_channel.setStyleSheet("font: 75 14pt \"Cambria\";")
        self.selected_channel.setObjectName("selected_channel")
        self.voltage = QtWidgets.QLabel(self.centralwidget)
        self.voltage.setGeometry(QtCore.QRect(540, 150, 111, 20))
        self.voltage.setStyleSheet("font: 75 14pt \"Cambria\";")
        self.voltage.setObjectName("voltage")
        self.select_channel_display = QtWidgets.QLabel(self.centralwidget)
        self.select_channel_display.setGeometry(QtCore.QRect(540, 100, 141, 31))
        self.select_channel_display.setStyleSheet("border: 1px solid black;\n"
"font: 11pt \"Cambria\";\n"
"background: white;\n"
"")
        self.select_channel_display.setText("")
        self.select_channel_display.setObjectName("select_channel_display")
        self.voltage_display = QtWidgets.QLabel(self.centralwidget)
        self.voltage_display.setGeometry(QtCore.QRect(540, 175, 141, 31))
        self.voltage_display.setStyleSheet("border: 1px solid black;\n"
"font: 11pt \"Cambria\";\n"
"background: white;\n"
"")
        self.voltage_display.setText("")
        self.voltage_display.setObjectName("voltage_display")
        self.status = QtWidgets.QLabel(self.centralwidget)
        self.status.setGeometry(QtCore.QRect(20, 5, 241, 21))
        self.status.setStyleSheet("font: 12pt \"Calibri\";")
        self.status.setObjectName("status")
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 737, 21))
        self.menubar.setObjectName("menubar")
        
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.Channelbox.setItemText(0, _translate("MainWindow", "Channel 1"))
        self.Channelbox.setItemText(1, _translate("MainWindow", "Channel 2"))
        self.Channelbox.setItemText(2, _translate("MainWindow", "Channel 3"))
        self.Channelbox.setItemText(3, _translate("MainWindow", "Channel 4 "))
        self.connect_button.setText(_translate("MainWindow", "Connect"))
        self.start_button.setText(_translate("MainWindow", "Start Measure"))
        self.selected_channel.setText(_translate("MainWindow", "Selected Channel"))
        self.voltage.setText(_translate("MainWindow", "Voltage [mV]"))
        self.status.setText(_translate("MainWindow", "status:"))

        #connect
        self.connect_button.clicked.connect(self.connectPressed)
        self.start_button.clicked.connect(self.startPressed)
        self.Channelbox.currentIndexChanged.connect(self.channelSelected)
        self._update_signal.connect(self.updatePlot)
        
                
        #show the changed status
    def toStatus(self, msg):
        self.status.setText(msg)
        
    def updatePlot(self, voltData_list):
        print(voltData_list)
        
    def connectPressed(self):
        if self._is_connected == False:
            self.controller.openDevice()
        else:
            self.controller.closeDevice()
            
    def startPressed(self):
        if self._is_running == False:
            self.controller.startMeasure(self.current_channel)
            self.start_button.setText("Stop Measure")
            self._is_running = True 
            
        elif self._is_running == True:
            self.controller.stopMeasure(self.current_channel)
            self.startbutton.setText("Start Measure")                 
            self._is_running = False
            
    def channelSelected(self):
        self.current_channel = self.Channelbox.currentIndex()
        self.controller.switchChannel(self.current_channel)
       
    def switchChannel(self, channelNumber):
        self.selected_channel.setText("Channel: %d" % channelNumber)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    
    
    
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

