# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 23:06:53 2021

@author: JHJeong32
This script is designed for a spectific usage due to lack of time.
If you are looking for general python scripts for oscilloscopes, please contact JJH.
mail: jhjeong32@snu.ac.kr
Tel.: 010-9600-3392
"""
SVR_IP   = "172.22.22.92"
SVR_PORT = 53000

from PyQt5 import uic, QtWidgets, QtGui
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui     import QColor
from PyQt5.QtCore    import pyqtSignal, QThread

import pyqtgraph as pg
import configparser, socket, os, pickle
import numpy as np
from queue import Queue

from Oscillo_scope_theme import Oscilloscpoe_theme_base
from DB_ASRI133109_v0_06 import DB_ASRI133109

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/Libs/Oscilloscope_gui_v0_04.ui'
Ui_Form, _ = uic.loadUiType(uifile)

pg.setConfigOptions(antialias=True) # This makes the plot smoother.


class DS1052E_GUI(QtWidgets.QWidget, Ui_Form, Oscilloscpoe_theme_base):

    def closeEvent(self, e):
        if self.plot_fetcher.scope:
            if not self.plot_fetcher.scope._closed:
                self.plot_fetcher.scope.sendall(bytes("STOP\n", 'latin-1'))
                self.BTN_run.setChecked(False)
                self.plot_fetcher.scope.close()
                print('Oscilloscope is closed')
        self.deleteLater()
        
    def __init__(self, parent=None, theme="black"):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.BTN_DB.setIcon(QtGui.QIcon(dirname + '/Libs/gui_save.ico'))
        self.parent = parent
        self._theme = theme
        self.CH_list = [True, True]  # always 2 for this version of the app
        self.x_data = {idx: [] for idx in range(len(self.CH_list))}
        self.y_data = {idx: [] for idx in range(len(self.CH_list))}
        
        self.isInitialized = False
        self.current_idx = 0
                        
        self.canvas, self.ax_dict, self.plot_dict = self._createCanvas(self.LBL_PLOT)        
        
        self.plot_fetcher = Fetcher(self, SVR_IP, SVR_PORT)
        self.plot_fetcher.waveform_signal.connect(self.updatePlot)
        
        self.db_recorder = DB_Recorder(self, self.parent)
        
        self.cp = configparser.ConfigParser()
        
        # self.DB = DB_ASRI133109()
        
        self.Vscale    = [5, 5]
        self.Hscale    = 5
        self.Vposition = [5, 5]
        
        self.setWindowTitle("Oscilloscope v0.04")
        
    def _createCanvas(self, frame):
        if self._theme == "black":
            pg.setConfigOption("background", QColor(70, 70, 70))
            pg.setConfigOption('foreground', QColor(210, 210, 210))
            styles = {"color": "#D2D2D2","font-size": "15px", "font-family": "Arial"}
            self.line_colors = [QColor(141, 211, 199), QColor(254, 255, 179)]
            
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
            styles = {"color": "k", "font-size": "15px", "font-family": "Arial"}
            self.line_colors = [QColor(31, 119, 180), QColor(255, 127, 14)]
            
        self.line_width = 1
        
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
        ax1 = pg.ViewBox()
        ax.showAxis("right")
        ax.scene().addItem(ax1)
        ax.getAxis("right").linkToView(ax1)
        ax1.setXLink(ax)
        
        plot1 = pg.PlotDataItem(self.x_data[0],
                                 self.y_data[1],
                                 pen=pg.mkPen(self.line_colors[1], width=self.line_width))
        
        ax1.addItem(plot1)
        
        ax.setMouseEnabled(x=False,y=False)
        ax1.setMouseEnabled(x=False,y=False)
        
        plot_dict = {0: plot0, 1: plot1}
        ax_dict = {0: ax, 1: ax1}
        
        ax.setLabel("bottom", "Time", **styles)
        ax.setLabel("left", "Forward voltage", **styles)
        ax.setLabel("right", "Reflected voltage", **styles)
        
        ax.showGrid(x=True)
        
        return canvas, ax_dict, plot_dict
        
    
    def updatePlot(self, wave_data):
        if (not self.isHidden() and not self.isMinimized()):
            for ch, on in enumerate(self.CH_list):
                if on:
                    y_data = wave_data["data"][ch]
                    x_data = wave_data["time"][ch]
                    
                if not y_data[0] == "auto":
                    off_scale = np.linspace(-0.1, 0.1, 201)[self.Vposition[ch]]
                    x_scale = np.linspace(0.1, 0.5, 11)[self.Hscale]
                    
                    
                    y_scale = np.linspace(0.1, 1.99, 11)[self.Vscale[ch]]
                    
                    self.plot_dict[ch].setData(x_data, y_data + off_scale*np.mean(y_data))
                    
                    self.ax_dict[ch].setXRange( np.mean(x_data) - x_scale*np.max(x_data), np.mean(x_data) + x_scale*np.max(x_data))
                    self.ax_dict[ch].setYRange( np.mean(y_data) - y_scale*np.ptp(y_data), np.mean(y_data) + y_scale*np.ptp(y_data))

                    
                    self.LBL_CH1_VAVG.setText(  self.VPlotScaler( np.mean(wave_data["data"][0])  ) )
                    self.LBL_CH2_VAVG.setText(  self.VPlotScaler( np.mean(wave_data["data"][1])  ) )
                    
                    self.CH1_P2P = np.ptp(wave_data["data"][0])
                    self.CH2_P2P = np.ptp(wave_data["data"][1])
                    self.LBL_CH1_VPP.setText(  self.VPlotScaler(  np.ptp(wave_data["data"][0])  ) )
                    self.LBL_CH2_VPP.setText(  self.VPlotScaler(  np.ptp(wave_data["data"][1])  ) )
        
                    self.LBL_CH1_FREQ.setText( self.FPlotScaler( wave_data["freq"][0] ) )
                    self.LBL_CH2_FREQ.setText( self.FPlotScaler( wave_data["freq"][1] ) )
                else:
                    self.LBL_CH1_VAVG.setText("Settings...")
                    self.LBL_CH2_VAVG.setText("Settings...")
                    self.LBL_CH1_VPP.setText("Settings...")
                    self.LBL_CH2_VPP.setText("Settings...")
                    self.LBL_CH1_FREQ.setText("Settings...")
                    self.LBL_CH2_FREQ.setText("Settings...")
                    
            self.ax_dict[1].setGeometry(self.ax_dict[0].vb.sceneBoundingRect())
            QtWidgets.QApplication.processEvents()

        
    def changedChamber(self, chamber):
        if chamber == "EA":
            osc_id = 1
        else:
            osc_id = 0

        self.current_idx = osc_id
        
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

    # def pressedRunButton(self, flag):
    #     if flag:
    #         self.CMB_CHAMBER.setEnabled(False)
    #         self.plotter.run_flag = flag
    #         if self.chamber == "EA": 
    #             osc_id = 1
    #         elif self.chamber == "EC": 
    #             osc_id = 0
            
    #         self.plotter.start()
    #         self.plotter.scope.sendall(bytes("REQ:%d\n" % osc_id, 'latin-1'))
            
    #     else:
    #         self.CMB_CHAMBER.setEnabled(True)
    #         self.plotter.run_flag = flag
    #         while self.plotter.isRunning():
    #             time.sleep(0.2)
    #         self.plotter.scope.sendall(bytes("STOP\n", 'latin-1'))
            
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
    


        
    def pressedAutoSet(self):
        pass
        # if self.plot_fetcher.isRunning():
        #     self.plot_fetcher.queue.put("")
    
    def pressedSaveButton(self):
        self.db_recorder.start()
        
    def pressedRunButton(self, flag):
        if flag:
            self.CBOX_chamber.setEnabled(False)
            self.plot_fetcher.start()

        else:
            self.CBOX_chamber.setEnabled(True)

        
    def changedSliderBar(self):
        sender_name = self.sender().objectName()
        sender_value = self.sender().value()
        if sender_name == "SLB_H":
            self.Hscale = sender_value
        else:
            _, channel, option = sender_name.split("_")
            if channel == "CH1":
                idx = 0
            else:
                idx = 1
            
            if option == "VS": # scale
                self.Vscale[idx] = sender_value
            else: # position
                self.Vposition[idx] = sender_value
            
            
class Fetcher(QThread):
    
    waveform_signal = pyqtSignal(dict)
    
    def __init__(self, parent=None, svr_ip="", svr_port=0):
        super().__init__()
        self.parent = parent
        self.ip = svr_ip
        self.port = svr_port
        self.queue = Queue()
        
        self.data_buffer = []
        
    def run(self):
        try:
            self.scope = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.scope.settimeout(1)
            self.scope.connect((self.ip, self.port))
            self.scope.sendall(bytes("REQ:%d\n" % self.parent.current_idx, 'latin-1'))

            while self.parent.BTN_run.isChecked():
                if self.queue.qsize():
                    msg = self.queue.get()
                    self.scope.sendall(bytes(msg + "\n", "latin-1"))
                
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
                    
            self.scope.sendall(bytes("STOP\n", 'latin-1'))
            self.scope.close()
            self.scope = None
            self.data_buffer = []
            
        except socket.error as exc:
            print("Couldn't connect to the oscilloscope server. (%s)" % exc)
            self.parent.BTN_run.setChecked(False)
            
class DB_Recorder(QThread):
    
    def __init__(self, parent=None, rf_gui=None):
        super().__init__()
        self.parent = parent
        self.rf_gui = rf_gui
        
    def dBm_to_vpp(self, dBm):
        volt = 2*np.sqrt((100)/1000)*10**(dBm/20)
        return volt
        
    def saveToDB(self):
        if self.parent.current_idx == 1: # EA
              SG = "ea_rf"
              chamber = "EA"
        else:
              SG = "ec_Rf"
              chamber = "EC"
              
              

        RF_Vpp_data = self.dBm_to_vpp(self.rf_gui.panel_dict[SG].device.settings[0]["power"])
        RF_freq_data = self.dBm_to_vpp(self.rf_gui.panel_dict[SG].device.settings[0]["freq"])


        if hasattr(self.parent, 'CH1_P2P'):
            self.DB.asri_traprf(chamber, #CH_ID
                                RF_Vpp_data, #RF_AMP
                                RF_freq_data, #RF_FREQ
                                self.parent.CH1_P2P, #FWD AMP
                                self.parent.CH2_P2P) #RFL AMP
            print('Saved to DB')
        else:
            print('Run Oscilloscope First')
        
    def run(self):
        self.DB = DB_ASRI133109()
        self.saveToDb()
        self.DB.closeDB()
        self.DB = None

                
#%%
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    OSC = DS1052E_GUI(theme="black")
    OSC.changeTheme("black")
    OSC.show()
