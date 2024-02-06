# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 23:06:53 2021

@author: JHJeong32
+ JJH: EC trap SG outputs through BNC

https://stackoverflow.com/questions/48590354/pyqtgraph-plotwidget-multiple-y-axis-plots-in-wrong-area
"""
SVR_IP   = "172.22.22.92"
SVR_PORT = 53000

from PyQt5 import uic, QtWidgets, QtGui
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui     import QColor
from PyQt5.QtCore    import pyqtSignal, QThread

import pyqtgraph as pg
import configparser, socket, time, os, pickle
import numpy as np

import sys
DB_path = "Q://Experiment_Scripts/_ETC/"
sys.path.append(DB_path)
from DB_ASRI133109_v0_03 import DB_ASRI133109

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/Libs/Oscilloscope_gui_v0_04.ui'
Ui_Form, _ = uic.loadUiType(uifile)

pg.setConfigOptions(antialias=True) # This makes the plot smoother.


class DS1052E_GUI(QtWidgets.QWidget, Ui_Form):

    # def closeEvent(self, e):
    #     if not self.plotter.scope._closed:
    #         self.plotter.scope.sendall(bytes("STOP\n", 'latin-1'))
    #         while self.plotter.isRunning():
    #             time.sleep(0.2)
    #         self.plotter.scope.close()
    #         print('Oscilloscope is closed')
        
    def __init__(self, instance_name, parent=None, theme="black"):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.BTN_DB.setIcon(QtGui.QIcon(dirname + '/Libs/gui_save.ico'))
        # self.BTN_DB.clicked.connect(self.SavetoDB)
        self.parent = parent
        self._theme = theme
        
        self.CH_list = [True, True]
        self.x_data = {idx: [] for idx in range(len(self.CH_list))}
        self.y_data = {idx: [] for idx in range(len(self.CH_list))}
        
        self.isInitialized = False
                        
        self.canvas, self.ax, self.plot_dict = self._createCanvas(self.LBL_PLOT)
        self.rgb_color = [0.275, 0.275, 0.275]
        
        
        # self.plotter = Fetcher(SVR_IP, SVR_PORT)
        # self.plotter.waveform_signal.connect(self.UpdatePlot)
        # self.plotter.CH_list = self.CH_list
        
        self.cp = configparser.ConfigParser()
        
        self.DB = DB_ASRI133109()
        
        self.Vscale    = [5, 5]
        self.Hscale    = 5
        self.Vposition = [5, 5]
        
    def _createCanvas(self, frame):
        if self._theme == "black":
            pg.setConfigOption("background", QColor(40, 40, 40))
            pg.setConfigOption('foreground', QColor(140, 140, 140))
            styles = {"color": "#969696","font-size": "15px", "font-family": "Arial"}
            self.line_colors = [QColor(141, 211, 199), QColor(254, 255, 179)]
            
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
            styles = {"color": "k", "font-size": "15px", "font-family": "Arial"}
            self.line_colors = [QColor(31, 119, 180), QColor(255, 127, 14)]
            
        self.line_width = 2
        
        canvas = pg.GraphicsLayoutWidget()
        ax = canvas.addPlot()
        ax.setDefaultPadding(0)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

        frame.setLayout(layout)
        plot0 = ax.plot(self.x_data[0],
                        self.y_data[0],
                        pen=pg.mkPen(self.line_colors[0], width=self.line_width))
        
        # ax1 = canvas.addPlot()
        plot1 = pg.ViewBox()
        ax.showAxis("right")
        ax.scene().addItem(plot1)
        ax.getAxis("right").linkToView(plot1)
        plot1.setXLink(ax)
        
        plot_dict = {0: plot0, 1: plot1}
        
        ax.setLabel("bottom", "Time", **styles)
        ax.setLabel("left", "Forward voltage", **styles)
        ax.setLabel("right", "Reflected voltage", **styles)
        ax.showGrid(x=True, y=True)
        
        return canvas, ax, plot_dict
        
    
    def updatePlot(self, wave_data):
        x_data = np.arange(50)
        y_data0 = np.random.random(50)*5
        y_data1 = np.random.random(50)
        
        self.plot_dict[0].setData(x_data, y_data0)
        self.plot_dict[1].addItem(pg.PlotCurveItem(x_data, y_data1, pen=pg.mkPen(self.line_colors[1], width=self.line_width)))
        self.plot_dict[1].setGeometry(self.ax.vb.sceneBoundingRect())
        
        # for ch, on in enumerate(self.CH_list):
        #     if on:
        #         y_data = wave_data["data"][ch]
        #         x_data = wave_data["time"][ch]
                
        #     if not y_data[0] == "auto":
        #         off_scale = np.linspace(-0.1, 0.1, 201)[self.Vposition[ch]]
        #         self.lines[ch].set_data(x_data, y_data + off_scale*np.mean(y_data))
        #         x_scale = np.linspace(0.1, 0.5, 11)[self.Hscale]
        #         self.axes[ch].set_xlim( np.mean(x_data) - x_scale*np.max(x_data),
        #                                 np.mean(x_data) + x_scale*np.max(x_data))
        #         y_scale = np.linspace(0.1, 1.99, 11)[self.Vscale[ch]]
        #         self.axes[ch].set_ylim( np.mean(y_data) - y_scale*np.ptp(y_data), 
        #                                 np.mean(y_data) + y_scale*np.ptp(y_data))
                
        				 
        #     self.LBL_CH1_VAVG.setText(  self.VPlotScaler( np.mean(wave_data["data"][0])  ) )
        #     self.LBL_CH2_VAVG.setText(  self.VPlotScaler( np.mean(wave_data["data"][1])  ) )
            
        #     self.CH1_P2P = np.ptp(wave_data["data"][0])
        #     self.CH2_P2P = np.ptp(wave_data["data"][1])
        #     self.LBL_CH1_P2P.setText(  self.VPlotScaler(  np.ptp(wave_data["data"][0])  ) )
        #     self.LBL_CH2_P2P.setText(  self.VPlotScaler(  np.ptp(wave_data["data"][1])  ) )

        #     self.LBL_CH1_FREQ.setText( self.FPlotScaler( wave_data["freq"][0] ) )
        #     self.LBL_CH2_FREQ.setText( self.FPlotScaler( wave_data["freq"][1] ) )
                 

        # self.canvas.draw()

        
    def ChamberChange(self, chamber):
        if chamber == "EA":
            osc_id = 1
        else:
            osc_id = 0

        self.chamber = chamber
        
        if self.plotter.isRunning():
            self.plotter.scope.sendall(bytes("REQ:%d\n" % osc_id, 'latin-1'))

        
    def ScaleChange(self, ScaleInt):
        objName = self.sender().objectName()
        if not objName.find('CH1') == -1:
            ch_index = 0
        elif not objName.find('CH2') == -1:
            ch_index = 1
        else:
            ch_index = -1 # Horizontal slider
            
        if not objName.find("VP") == -1:
            self.Vposition[ch_index] = ScaleInt
        elif not objName.find("VS") == -1:
            self.Vscale[ch_index] = ScaleInt
        else:
            self.Hscale = ScaleInt

    def RunOscillator(self, check):
        if check:
            self.CMB_CHAMBER.setEnabled(False)
            self.plotter.run_flag = True
            if self.chamber == "EA": 
                self.BTN_RUN.setStyleSheet("background-color:rgb(153, 217, 234)")
                osc_id = 1
            elif self.chamber == "EC": 
                self.BTN_RUN.setStyleSheet("background-color:rgb(112, 146, 190)")
                osc_id = 0
            
            self.plotter.start()
            self.plotter.scope.sendall(bytes("REQ:%d\n" % osc_id, 'latin-1'))
            
        else:
            self.CMB_CHAMBER.setEnabled(True)
            self.plotter.run_flag = False
            while self.plotter.isRunning():
                time.sleep(0.2)
            self.BTN_RUN.setStyleSheet("")
            self.plotter.scope.sendall(bytes("STOP\n", 'latin-1'))
            
    def VPlotScaler(self, data):
        data = abs(data)
        if data == 0.0:
            return ('----')     
        elif 1 <= data:
            val, unit = data, 'V'
        elif 1e-4 <= data < 1:
            val, unit = data*1e3, 'mV'
        elif 1e-7 <= data < 1e-4:
            val, unit = data*1e6, 'μV'
        
        return ("%.2f %s" % (val, unit))
    
    def FPlotScaler(self, data): 
        if data <= 1e12:
            if data < 1e3:
                val, unit = data, 'Hz'
            elif 1e3 <= data < 1e6:
                val, unit = data/1e3, 'kHz'
            elif 1e6 <= data < 1e9:
                val, unit = data/1e6, 'MHz'
            elif 1e9 <= data:
                val, unit = data/1e9, 'GHz'
                
            return ("%.2f %s" % (val, unit))
        else :
            return ('----')
    
    def SavetoDB(self):
#        if self.plotter.run_flag == False:
#            pass
        
        if self.chamber == "EA": 
             SG_idx = 0
        elif self.chamber == "EC": 
             SG_idx = 1
        SG = self.SG[SG_idx]

        scale = 10**(3*SG.freq_unit.currentIndex())
        RF_freq_data = SG.freq_spinbox.value() * scale
        RF_Vpp_data = SG.Vpp_spinboxes[SG_idx].value()

        if SG.connected:
            if hasattr(self, 'CH1_P2P'):
                self.DB.asri_traprf(self.chamber, #CH_ID
                                    RF_Vpp_data, #RF_AMP
                                    RF_freq_data, #RF_FREQ
                                    self.CH1_P2P, #FWD AMP
                                    self.CH2_P2P) #RFL AMP
                print('Saved to DB')
            else:
                print('Run Oscilloscope First')
        else:
            print('Signal Generator is not connected')
        
        time.sleep(0.1)

    
    def UpdateOscillator(self):
        pass
        # if self.chamber =="EA": osc_id = 1
        # else:                   osc_id = 0
        # self.plotter.scope.sendall(bytes("AUTO:%d\n" % osc_id, 'latin-1'))
        
    def pressedAutoSet(self):
        pass
    
    def pressedSaveButton(self):
        pass
    
    def changedSelectedDevice(self, idx):
        print(idx)
        
    def pressedRunButton(self, flag):
        print(flag)
        
    def changedSliderBar(self):
        print(self.sender().objectName())
        
class Fetcher(QThread):
    
    waveform_signal = pyqtSignal(dict)
    
    def __init__(self, SVR_IP, SVR_PORT):
        super().__init__()
        self.scope = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.scope.settimeout(1)
        try:
            self.scope.connect((SVR_IP, SVR_PORT))
        except socket.error as exc:
            print ("Caught exception socket.error : %s" % exc)
            
        self.data_buffer = []
        self.run_flag = False
        
    def run(self):
        while self.run_flag:
            packet = self.scope.recv(4096)
            #if not packet: break
            if not b'\r\n' in packet:
                self.data_buffer.append(packet)
                
            else:
                temp = b"".join(self.data_buffer)
                temp += packet[:packet.find(b'\r\n')]
                self.data_dict = pickle.loads(temp)
                self.waveform_signal.emit(self.data_dict)
                self.data_buffer = [packet[packet.find(b'\r\n')+2:]]
            
        
#%%
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    OSC = DS1052E_GUI(instance_name='DS1052E_v0.02')
    
    OSC.show()
