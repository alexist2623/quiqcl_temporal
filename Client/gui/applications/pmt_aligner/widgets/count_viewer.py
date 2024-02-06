# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 22:37:43 2021

@author: QCP32
"""
import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtGui     import QColor
from PyQt5.QtCore    import pyqtSignal

import numpy as np
import pyqtgraph as pg


filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/count_viewer.ui'
Ui_Form, QtBaseClass = uic.loadUiType(uifile)
version = "3.1"

seq_dirname = dirname + "/../../../libraries/sequencer_files/"

pg.setConfigOptions(antialias=True)

#%% Temporary
class CountViewer(QtWidgets.QWidget, Ui_Form):
    
    sig_update_plot = pyqtSignal()
    
    user_run_flag = False
    counting_flag = False
    
    def __init__(self, device_dict=None, parent=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        
        self.device_dict = device_dict
        self.parent = parent

        self._theme = theme
                
        # sequencer settings
        self.sequencer = self.device_dict["sequencer"]
        self.sequencer.sig_occupied.connect(self._setInterlock)
        self.sequencer.sig_seq_complete.connect(self._completedProgress)

        self.cp = self.parent.cp
        self._initParameters()
        self._initUi()
        
                
    def _initUi(self):
        self.disable_list = [self.BTN_set_PMT_aveage,
                             self.BTN_set_PMT_exposure,
                             self.BTN_start,
                             self.BTN_stop]
    
        
        self.canvas, self.ax, self.plot = self._create_canvas(self.GBOX_plot)
        
        
    def _initParameters(self):
        self.exposure_time = 1
        self.avg_num = 1
        
        self.PMT_counts_list = []
        self.PMT_number_list = []
        self.PMT_num = 0
                
        self.PMT_vmin = 0
        self.PMT_vmax = 100
        
        
    def showEvent(self, evt):
        self.updatePlot()
        
    def pressedStartCounting(self):
        if not self.sequencer.is_opened:
            self.toStatusBar("The FPGA is not opened!")
        else:
            if self.counting_flag:
                self.toStatusBar("The counting is already running...")
            else:
                self.counting_flag = True
                self.user_run_flag = True
                
                self.sequencer.occupant = "count_viewer"
                self.sequencer.sig_occupied.emit(True)
                
                self.toStatusBar("Start PMT exposures.")
                self.runPMT_Exposure()
            
    def pressedStopCounting(self):
        if not self.counting_flag:
            self.toStatusBar("The counting has not been started yet.")
        else:
            self.counting_flag = False
            self.user_run_flag = False
            
            self.sequencer.occupant = ""
            self.sequencer.sig_occupied.emit(False)
            
            self.toStatusBar("Stopped PMT exposures.")
            
    def updatePlot(self):      
        if (not self.isHidden() and not self.isMinimized()):
            self.plot.setData(self.PMT_number_list, self.PMT_counts_list)
            
            if self.radio_manual.isChecked():
                self.ax.setYRange(self.PMT_vmin, self.PMT_vmax)
                
            elif self.radio_auto.isChecked():
                y_max = np.ceil(np.max(self.PMT_counts_list))
                y_min = np.floor(np.min(self.PMT_counts_list))
                
                self.ax.setYRange(y_min, y_max)
                
            QtWidgets.QApplication.processEvents()
                
    
        if self.counting_flag and self.user_run_flag:
            self.runPMT_Exposure()
        
    def toStatusBar(self, msg):
        self.parent.toStatusBar(msg)
        
    def runPMT_Exposure(self):
        self._setSequencerFile()
        self.sequencer.runSequencerFile()
        
        
    #%% Settings
    def setAverageNumber(self):
        try:
            self.avg_num = int(self.TXT_PMT_count.text())
        except Exception as e:
            self.toStatusBar("The average number should be an int. (%s)" % e)
            
            
    def setExposureTime(self):
        try:
            self.exposure_time = int(self.TXT_exposure_time.text())
        except Exception as e:
            self.toStatusBar("The exposure time should be an int in ms. (%s)" % e)
            
        
    def _setSequencerFile(self):
        # CHECK FOR SYNTAX
        self.sequencer.loadSequencerFile(seq_file= seq_dirname + "/simple_exposure.py",
                                         replace_dict={13:{"param": "EXPOSURE_TIME_IN_MS", "value": int(self.exposure_time*10)},
                                                       14:{"param": "NUM_AVERAGE", "value": self.avg_num}},
                                         replace_registers={"PMT": self.parent.detector})
        
    def setPMTMin(self):
        try:
            self.PMT_vmin = np.floor(float(self.TXT_y_min.text()))
        except Exception as e:
            self.toStatusBar("The min PMT count should be a float. (%s)" % e)
        
    def setPMTMax(self):
        try:
            self.PMT_vmax = np.ceil(float(self.TXT_y_max.text()))
        except Exception as e:
            self.toStatusBar("The max PMT count should be a float. (%s)" % e)
    
    
    #%% ?
    def _setEnableObjects(self, flag):
        for obj in self.disable_list:
            obj.setEnabled(flag)
    
    def _create_canvas(self, frame):
        if self._theme == "black":
            pg.setConfigOption('background', QColor(40, 40, 40))
            styles = {"color": "#969696","font-size": "15px", "font-family": "Arial"}
            self.line_color = QColor(141, 211, 199)
            
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
            styles = {"color": "k", "font-size": "15px", "font-family": "Arial"}

            self.line_color = QColor(31, 119, 180)
        self.line_width = 3
        
        canvas = pg.GraphicsLayoutWidget()
        ax = canvas.addPlot()
        ax.setDefaultPadding(0)

        layout = QVBoxLayout()
        layout.layoutLeftMargin = 0
        layout.layoutRightMargin = 0
        layout.layoutTopMargin = 0
        layout.layoutBottomMargin = 0
        layout.addWidget(canvas)
        
        frame.setLayout(layout)
        
        plot = ax.plot(self.PMT_number_list, self.PMT_counts_list, pen=pg.mkPen(self.line_color, width=self.line_width))
        
        ax.setLabel("bottom", "Exposure indices", **styles)
        ax.setLabel("left", "PMT counts", **styles)
        
        return canvas, ax, plot
        
    ## Sequencer signals
    ####################
    def _startProgress(self):
        if not self.user_run_flag:
            self._setEnableObjects(False)
            
    def _setInterlock(self, occupied_flag):
        if occupied_flag:
            if not self.sequencer.occupant == "count_viewer":
                self._setEnableObjects(False)
        else:
            self._setEnableObjects(True)
            
    
    def _completedProgress(self):
        if self.user_run_flag:
            if self.counting_flag:
                raw_pmt_count = np.asarray(self.sequencer.data[0]) # kind of deep copying...
                if len(raw_pmt_count) > 1:
                    pmt_count = np.mean(raw_pmt_count[:, 2])
                else:
                    pmt_count = raw_pmt_count[0][2]
                    
                self.PMT_num += 1
                while len(self.PMT_counts_list) > 50:
                    self.PMT_counts_list.pop(0)
                    self.PMT_number_list.pop(0)
                    
                self.PMT_counts_list.append(pmt_count)
                self.PMT_number_list.append(self.PMT_num)
                
                self.TXT_pmt_result.setText("%.3f" % pmt_count)
                self.updatePlot()

if __name__ == "__main__":
    pa = CountViewer()
    pa.show()