# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 16:10:01 2023

@author: QCP75
"""

import os, time
import numpy as np
import pandas as pd
import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets, QtGui
from PyQt5.QtCore    import pyqtSignal, QMutex, QWaitCondition, QThread
from PyQt5.QtWidgets import QVBoxLayout

# Custom widgets
from .Connection_widget import CustomDevice



ph_ui_file = dirname + "/ui/parametric_heating.ui"
ph_ui, _ = uic.loadUiType(ph_ui_file)

def vpp_to_dBm(vpp):
    dBm = 20*np.log10(vpp/np.sqrt(8)/(0.001 * 50)**0.5)
    return dBm

def checkError(func):
    """Decorator that checks the error of methods..
    """
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as ee:
            self.toStatusBar("An error while running '%s'. (%s)" % (func.__name__, ee))
            return
    return wrapper


class RabiOscillationGUI(QtWidgets.QWidget, ph_ui):
    
    
    def __init__(self, device_dict={}, parent=None, theme="white"):
        QtWidgets.QWidget.__init__(self)
        self.device_dict = device_dict
        self.parent = parent
        self._theme = theme
        
        self.sequencer = self.device_dict["sequencer"]
        self.sequencer.sig_occupied.connect(self._setInterlock)

        self.setupUi(self)
        self.toolbar, self.ax, self.canvas, self.plot = self._create_canvas(self.GBOX_plot)
        
        self.initUi()
        self.plot_handler = PlotHandler(self)
        self.plot_handler.update_signal.connect(self.updatePlot)
        self.plot_handler.finished_signal.connect(self.finishedRun)
        
        self.disable_list = [self.BTN_start, self.con.BTN_connection]

        
    def initUi(self):
        self.custom_con = CustomDevice(self)
        self.non_custom_con = CustomDevice() # This should be changed later
        
        self.GBOX_device.layout().addWidget(self.custom_con)
        self.GBOX_device.layout().addWidget(self.non_custom_con)
        
        self.changeConnectionDevice()
        
    def updatePlot(self, percentage):
        if self.CBOX_Auto.isChecked():
            self.TXT_ymax.setText("%.2f" % self.plot_handler.y_max)
            self.TXT_ymin.setText("%.2f" % self.plot_handler.y_min)
            self.changedYLimit()
        else:
            self.canvas.draw()
        self.progressBar.setValue(percentage)

    def changeConnectionDevice(self):
        if self.CBOX_custom.isChecked():
            self.non_custom_con.hide()
            self.custom_con.show()
            self.con = self.custom_con
        else:
            self.custom_con.hide()
            self.non_custom_con.show()
            self.con = self.non_custom_con
            
    @checkError
    def pressedStartButton(self, flag):
        if flag:
            if not self.sequencer.is_opened:
                self.toStatusBar("The FPGA is not opened!")
                self.BTN_start.setChecked(False)
            else:
                f_init, f_end, f_step = float(self.TXT_init_freq.text())*1e6, \
                                        float(self.TXT_end_freq.text())*1e6,  \
                                        float(self.TXT_delta_freq.text())*1e3
                exposure_time = int(self.TXT_exp_time.text())
                average_number = int(self.TXT_avg_num.text())
                power_in_dBm = vpp_to_dBm(float(self.TXT_Vpp.text()))
                
                
                self.plot_handler.switchingDevice(flag, power_in_dBm)
                self.plot_handler.setFrequencyRange(f_init, f_end, f_step)
                self.plot_handler._resetProgress()
                self.plot_handler._setSequencerFile(exposure_time, average_number)
                self.sequencer.occupant = "parametric_heating"
                self.sequencer.sig_occupied.emit(True)
                self.plot_handler.start()
                    
                self.toStatusBar("Started heating.")
                
        else:
            self.plot_handler.wakeupThread()  # This make sure the thread stops

    @checkError
    def cancelStartButton(self, no_input=True):
        self.BTN_start.setChecked(False)
        self.BTN_start.setText("Start")

    
    @checkError
    def changedYLimit(self, no_input=True):
        y_max = float(self.TXT_ymax.text())
        y_min = float(self.TXT_ymin.text())
        self.ax.set_ylim(y_min, y_max)
        self.canvas.draw()
        
    @checkError
    def changeXLimit(self, no_input=True):
        x_min = float(self.TXT_init_freq.text())
        x_max = float(self.TXT_end_freq.text())
        self.ax.set_xlim(x_min, x_max)
        
    @checkError
    def finishedRun(self):
        self.BTN_start.setChecked(False)
        self.progressBar.setValue(100)
                
        
    def toStatusBar(self, txt):
        if not self.parent == None:
            self.parent.toStatusBar(txt)
        else:
            print(txt)
            
    def _setInterlock(self, occupied_flag):
        if occupied_flag:
            if not self.sequencer.occupant == "parametric_heating":
                self._setEnableObjects(False)
            else:
                self.con.BTN_connection.setEnabled(False)
        else:
            self._setEnableObjects(True)
            
    def _setEnableObjects(self, flag):
        for enb_object in self.disable_list:
            enb_object.setEnabled(flag)
            
    def _create_canvas(self, gbox):
        fig = plt.Figure(tight_layout=True)
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        gbox.setLayout(layout)
        
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
            ax.xaxis.label.set_color([0.7, 0.7, 0.7])
            ax.yaxis.label.set_color([0.7, 0.7, 0.7])
            
            for spine in spine_list:
                ax.spines[spine].set_color([0.7, 0.7, 0.7])

            for action in toolbar.actions():
                action_text = action.text()
                action.setIcon(QtGui.QIcon(os.path.dirname(dirname) + '/icons/%s.png' % action_text))
                
            plot, = ax.plot([], [], "C4")
            
            
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
            
            plot, = ax.plot([], [], "C3")
            
        ax.set_ylabel("Number of photons")
        ax.set_xlabel("Modulation frequency [MHz]")
        ax.set_ylim(0, 100)
        ax.set_xlim(1, 2)
        return toolbar, ax, canvas, plot
            
#%%
class PlotHandler(QThread):
    
    update_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.ax      = parent.ax
        self.plot    = parent.plot
        self.con     = parent.con
        
        self.sequencer = self.parent.sequencer
        self.sequencer.sig_seq_complete.connect(self._completedProgress)
        
        # running
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.status = "standby"
        
        self._resetProgress()
        
    @checkError
    def _resetProgress(self):
        self.x_data = []
        self.y_data = []
        self.scan_idx = 0
        
    @checkError
    def _setSequencerFile(self, exposure_time_in_ms, average_number):
        # CHECK FOR SYNTAX
        self.sequencer.loadSequencerFile(seq_file= dirname + "/simple_exposure.py",
                                         replace_dict={11:{"param": "EXPOSURE_TIME_IN_MS", "value": exposure_time_in_ms},
                                                       12:{"param": "NUM_REPEAT", "value": average_number}})

    @checkError
    def _completedProgress(self, no_input=True):
        if self.parent.BTN_start.isChecked():
            raw_pmt_count = np.asarray(self.sequencer.data[0]) # kind of deep copying...
            if len(raw_pmt_count) > 1:
                pmt_count = np.mean(raw_pmt_count[:, 2])
            else:
                pmt_count = raw_pmt_count[0][2]
                
            self.scan_idx += 1
            
            self.x_data.append(self.current_frequency/1e6)
            self.y_data.append(pmt_count)
            
            self.y_max = np.ceil(np.max(self.y_data))
            self.y_min = np.floor(np.min(self.y_data))
            
            self.plot.set_data(self.x_data, self.y_data)
            self.update_signal.emit( int( (self.scan_idx+1)*100/ self.total_length ) )
            
        self.wakeupThread()
        
    def wakeupThread(self):
        self.cond.wakeAll()
        
    @checkError
    def switchingDevice(self, flag, power):
        self.con.setPower(power)
        if flag:
            self.con.enableOutput()
        else:
            self.con.disableOutput()
        
    @checkError
    def setFrequencyRange(self, init, end, step):
        self.init, self.end, self.step = init, end, step
        self.total_length = int((self.end - self.init)/self.step) + 1 # The end frequency should be included
        
    @checkError
    def runSequencer(self):
        self.sequencer.runSequencerFile()
        
    @checkError
    def run(self):
        while self.parent.BTN_start.isChecked():
            self.status = "hmm"
            self.mutex.lock()
            self.status = "running"
            if self.scan_idx <= self.total_length:
                self.current_frequency = self.init + self.step*self.scan_idx
                self.con.setFrequency(self.current_frequency)
                
                if self.parent.CBOX_precise.isChecked():
                    while not (self.current_frequency == self.con.readFrequency()):
                        time.sleep(0.3)
                
                self.status = "about_to_run_seq"
                self.runSequencer()
                
                self.status = "wait_for_mutex"
                self.cond.wait(self.mutex)
                self.mutex.unlock()
                
            else:
                self.sequencer.occupant = ""
                self.sequencer.sig_occupied.emit(False)
                self.switchingDevice(False, -30)
                self.saveData()
                self.finished_signal.emit()
                self.toStatusBar("Stopped heating.")
                self.parent.BTN_start.setChecked(False)
                self.status = "standby"
                self.mutex.unlock()


    @checkError
    def saveData(self):
        save_file_name = dirname + "/../data/parametric_heating/%s_parametric_heating" % datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        
        detail_string = self._makeDetails()
        df = pd.DataFrame({"frequency[MHz]": self.x_data,
                           "Photon counts": self.y_data})
        
        
        with open (save_file_name + ".csv", "w") as fp:
            fp.write(detail_string)
        df.to_csv(save_file_name + ".csv", header=True, index=False, mode="a")
        
        window_qpixmap = self.parent.grab()
        window_qpixmap.save(save_file_name + ".png", "PNG")
        
        
    def _makeDetails(self):
        detail = """Experimental data of parametric heating.
%s
Initial Modulation frequency [MHz]: %s
End Modulation frequency [MHz]: %s
Modulation Vpp [V]: %s
369-nm Laser frequency [THz]: %s
Trap RF frequency [MHz]: %s
Exposure time [ms]: %s
Average number: %s
==============================================
""" % ( datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
                        self.parent.TXT_init_freq.text(),
                        self.parent.TXT_end_freq.text(),
                        self.parent.TXT_Vpp.text(),
                        self.parent.TXT_laser_freq.text(),
                        self.parent.TXT_RF_freq.text(),
                        self.parent.TXT_exp_time.text(),
                        self.parent.TXT_avg_num.text())
        return detail
            
    def toStatusBar(self, txt):
        if not self.parent == None:
            self.parent.toStatusBar(txt)
        else:
            print(txt)
            

if __name__ == "__main__":
    ph = ParametricHeatingGUI({"sequencer"})
    ph.show()