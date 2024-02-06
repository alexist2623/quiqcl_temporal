# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 22:37:43 2021

@author: QCP32
"""
import os
from PyQt5 import uic
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore    import pyqtSignal, QMutex, QWaitCondition, QThread

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/count_viewer.ui'
Ui_Form, QtBaseClass = uic.loadUiType(uifile)
version = "2.0"

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
        self._initUi()
        self._initParameters()
        
        # plotter settings
        self.plot_handler = PlotHandler(self)
        self.plot_handler._sig_plot_process_done.connect(self.updatePlot)
        self.plot_handler.start()
                
    def _initUi(self):
        self.disable_list = [self.BTN_set_PMT_aveage,
                             self.BTN_set_PMT_exposure,
                             self.BTN_start,
                             self.BTN_stop]
    
        
        self.toolbar, self.ax, self.canvas = self._create_canvas(self.GBOX_plot)
        
        
    def _initParameters(self):
        self.exposure_time = 1
        self.avg_num = 1
        
        self.PMT_counts_list = []
        self.PMT_number_list = []
        self.PMT_num = 0
                
        self.PMT_vmin = 0
        self.PMT_vmax = 100
        
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
        # Note that the thread does all the work, the main thread updates the plot only.
        self.canvas.draw_idle()
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
        self.sequencer.loadSequencerFile(seq_file= dirname + "/simple_exposure.py",
                                         replace_dict={13:{"param": "EXPOSURE_TIME_IN_100US", "value": int(self.exposure_time*10)},
                                                       14:{"param": "NUM_REPEAT", "value": self.avg_num}})
        
    def setPMTMin(self):
        try:
            self.PMT_vmin = float(self.TXT_y_min.text())
        except Exception as e:
            self.toStatusBar("The min PMT count should be a float. (%s)" % e)
        
    def setPMTMax(self):
        try:
            self.PMT_vmax = float(self.TXT_y_max.text())
        except Exception as e:
            self.toStatusBar("The max PMT count should be a float. (%s)" % e)
    
    
    #%% ?
    def _setEnableObjects(self, flag):
        for obj in self.disable_list:
            obj.setEnabled(flag)
    
    def _create_canvas(self, frame):
        fig = plt.Figure(tight_layout=True)
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        frame.setLayout(layout)
        
        ax = fig.add_subplot(1,1,1)
        
        spine_list = ['bottom', 'top', 'right', 'left']
        
        if self._theme == "black":
            plt.style.use('dark_background')
            plt.rcParams.update({"savefig.facecolor": [0.157, 0.157, 0.157],
                                "savefig.edgecolor": [0.157, 0.157, 0.157]})
            
            fig.set_facecolor([0.157, 0.157, 0.157])
            ax.set_facecolor([0.157, 0.157, 0.157])
            ax.tick_params(axis='x', colors=[0.7, 0.7, 0.7], length=0)
            ax.tick_params(axis='y', colors=[0.7, 0.7, 0.7], length=0)
            
            for spine in spine_list:
                ax.spines[spine].set_color([0.7, 0.7, 0.7])

            for action in toolbar.actions():
                action_text = action.text()
                action.setIcon(QtGui.QIcon(os.path.dirname(dirname) + '/icons/%s.png' % action_text))
            
            
        elif self._theme == "white":
            plt.style.use('default')
            plt.rcParams.update({"savefig.facecolor": [1, 1, 1],
                                "savefig.edgecolor": [1, 1, 1]})
            fig.set_facecolor([1, 1, 1])
            ax.set_facecolor([1, 1, 1])
            ax.tick_params(axis='x', colors='k', length=0)
            ax.tick_params(axis='y', colors='k', length=0)
            
            for spine in spine_list:
                ax.spines[spine].set_color('k')
            toolbar.setStyleSheet("background-color:rgb(255, 255, 255);")
            
        return toolbar, ax, canvas
                
        
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
                self.PMT_counts_list.append(pmt_count)
                self.PMT_number_list.append(self.PMT_num)
                
                self.TXT_pmt_result.setText("%.3f" % pmt_count)
                self.sig_update_plot.emit()

    
class PlotHandler(QThread):
    
    _sig_plot_process_done = pyqtSignal()    
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.parent.sig_update_plot.connect(self.wakeupThread)
        self.PMT_counts_list = self.parent.PMT_counts_list
        self.PMT_number_list = self.parent.PMT_number_list
        
        # figures
        self.ax = self.parent.ax
        
        # running
        self.cond = QWaitCondition()
        self.mutex = QMutex()        
        self.status = "standby"
        
    def PlotPMTResult(self):
        self.ax.clear()
        
        if len(self.PMT_counts_list) > 50:
            self.PMT_counts_list.pop(0)
            self.PMT_number_list.pop(0)

        self.ax.plot(self.PMT_number_list, self.PMT_counts_list, color='teal')
        if self.parent.radio_auto.isChecked():
            self.ax.set_ylim(min(self.PMT_counts_list), max(self.PMT_counts_list))
        else:
            self.ax.set_ylim(self.parent.PMT_vmin, self.parent.PMT_vmax)
        
        self._sig_plot_process_done.emit()
        
    def wakeupThread(self):
        self.cond.wakeAll()
        
    def run(self):
        while True:
            self.mutex.lock()
            self.status = "plotting"
            
            self.PlotPMTResult()
            
            self.status = "standby"
            self.cond.wait(self.mutex)
            self.mutex.unlock()

if __name__ == "__main__":
    pa = PMTAligner()
    pa.show()