# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 17:45:56 2021

@author: QCP32
"""
import os, sys, datetime, pickle, copy, time
import numpy as np
from queue import Queue

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QRect, pyqtSignal, QSize, QThread, QMutex, QWaitCondition
from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QLabel, QVBoxLayout, QFileDialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from progress_bar_theme import progress_bar_theme_base

ui_filename = dirname + "/Data_Analyzer_UI.ui"
ui_file, _ = uic.loadUiType(ui_filename)

#%% MainWindow
class DataAnalyzerGUI(QtWidgets.QMainWindow, ui_file, progress_bar_theme_base):

    # _gui_callback = pyqtSignal()
    sig_process_data = pyqtSignal()
    
    # _version = "v0.01"
    # user_update = True    
    plot_list = []
    data_dict = {}
    
    def __init__(self, device_dict=None, controller=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Data Analyzer v1.0")
        self.device_dict = device_dict
        self.controller = controller
        
        self._theme = theme
        self._init_plot()
        
        # disable list is used when the main window busy
        self.disable_list = []
        for obj in self.__dict__:
            if not obj == "BTN_file_load":
                if ("CBOX_" in obj) or \
                    ("TXT_" in obj) or \
                    ("BTN_" in obj):
                    
                    self.disable_list.append(getattr(self, obj))
        
    def showEvent(self, e):
        self.updatePlot()
        
    def _initUi(self):
        pass
          
    def changedPlotRatio(self, ratio_string):
        ratio1, ratio2 = ratio_string.split(":")
        self._changePlotRatio(int(ratio1), int(ratio2))
        
    def changedLabelText(self):
        obj_name = self.sender().objectName()
        _, which_plot, which_label = obj_name.split("_")
        plot_idx = int(which_plot[-1]) - 1
        plot_text = self.sender().text()
        
        if which_label == "title":
            self.plot_list[plot_idx].setTitle(plot_text)
        elif which_label == "xlabel":
            self.plot_list[plot_idx].setXLabel(plot_text)
        elif which_label == "ylabel":
            self.plot_list[plot_idx].setYLabel(plot_text)
            
    def changedPlotType(self, plot_type):
        obj_name = self.sender().objectName()
        plot_idx = int(obj_name.split("_")[1][-1]) - 1
        
        self.plot_list[plot_idx].changeType(plot_type)
        self.plot_list[plot_idx].wakeupThread()
        
    def changedPlot_Y_Type(self, plot_type):
        obj_name = self.sender().objectName()
        plot_idx = int(obj_name.split("_")[1][-1]) - 1
        
        self.plot_list[plot_idx].plot_y_type = plot_type
        self.plot_list[plot_idx].wakeupThread()
        
    def changedThreshold(self):
        obj_name = self.sender().objectName()
        plot_idx = int(obj_name.split("_")[1][-1]) - 1
        threshold = float(self.sender().text())
        
        self.plot_list[plot_idx].threshold = threshold
        self.plot_list[plot_idx].wakeupThread()
        
    def changedDataSorting(self, text):
        self.sig_process_data.emit()
        
    #%% Files
    def pressedFileLoad(self, load_flag):
        if load_flag:
            file_list, _ = QFileDialog.getOpenFileNames(self, "Load pickle files", dirname, "*.pkl")
            if len(file_list):
                self.load_thread = PickleLoader(self, file_list)
                self.load_thread._sig_file_loaded.connect(self._acceptedLoadSignal)
                self.load_thread.finished.connect(self._finishedLoad)
                
                self._acceptedLoadSignal(0, len(file_list))
                
                for obj in self.disable_list:
                    obj.setEnabled(False)
                self.load_thread.start()
            else:
                self.BTN_file_load.setChecked(False)
        else:
            self.load_thread.load_complete = False
        
    def pressedFileDelete(self):
        selected_item_list = self.TBL_file_list.selectedItems()
        if not len(selected_item_list):
            self.toStatusBar("No files are selected.")
            
        else:
            while len(selected_item_list):
                row = selected_item_list[0].row()                
                self.TBL_file_list.removeRow(row)
                selected_item_list = self.TBL_file_list.selectedItems()
           
            self.toStatusBar("Deleted selected files.")
            
    def updateData(self, data_dict):
        self.data_dict = data_dict
        
    def _acceptedLoadSignal(self, file_idx, file_len):
        self.setProgressBarProgress(file_idx, file_len)
        self.setProgressBarStatus("Loading data files...(%d/%d)" % (file_idx, file_len))
        
    def _finishedLoad(self):
        if not self.load_thread.load_break:
            self.setProgressbarStylesheet("complete")
            self.setProgressBarStatus("Completed Loading data files.")
        else:
            self.setProgressbarStylesheet("error")
            self.setProgressBarStatus("Aborted loading data files.")
            
        for obj in self.disable_list:
            obj.setEnabled(True)
        self.BTN_file_load.setChecked(False)
        
        self.updateFileTable(self.data_dict)
        
        self.sig_process_data.emit()

    #%%
    def updateFileTable(self, data_dict):
        self.TBL_file_list.setRowCount(len(data_dict))
        for file_idx, file_name in enumerate(data_dict.keys()):
            self.TBL_file_list.setItem(file_idx, 0, QtWidgets.QTableWidgetItem(file_name))
            self.TBL_file_list.setItem(file_idx, 1, QtWidgets.QTableWidgetItem(str(data_dict[file_name]["shape"])))
            
        self.updateParamTable(data_dict[file_name]["params"])
        
            
    def updateParamTable(self, param_dict):
        param_idx = 0
        self.TBL_param.setRowCount(len(param_dict)) # -1 for "data"
        for key, val in param_dict.items():
            if not key == "data":
                self.TBL_param.setItem(param_idx, 0, QtWidgets.QTableWidgetItem(key))
                self.TBL_param.setItem(param_idx, 1, QtWidgets.QTableWidgetItem("%d" % val))
                param_idx += 1
            
        
    def loadPickleFiles(self, file_list):
        self.loaded_data_dict = {}
        self.TBL_file_list.setRowCount(len(file_list))
        for file_idx, file_name in enumerate(file_list):
            base_file_name = os.path.basename(file_name)
            with open (file_name, 'rb') as fr:
                loaded_data = pickle.load(fr)
                self.loaded_data_dict[base_file_name] = loaded_data
            self.TBL_file_list.setItem(file_idx, 0, QtWidgets.QTableWidgetItem(base_file_name))
            self.TBL_file_list.setItem(file_idx, 1, QtWidgets.QTableWidgetItem(str(np.shape(loaded_data["data"]))))
            
        # parameter setup
        param_idx = 0
        self.TBL_param.setRowCount(len(loaded_data.keys())-1) # -1 for "data"
        for key, val in loaded_data.items():
            if not key == "data":
                self.TBL_param.setItem(param_idx, 0, QtWidgets.QTableWidgetItem(key))
                self.TBL_param.setItem(param_idx, 1, QtWidgets.QTableWidgetItem("%d" % val))
                param_idx += 1
                
        self.data_dict = {}
        for key, val in self.loaded_data_dict.items():
            indiv_data_list = []
            partial_data_list = []
            outer_loop_idx = 0
            inner_loop_idx = 0
            for data_idx in range(3):
                cbox = getattr(self, "CBOX_data%d" % data_idx)
                curr_text = cbox.currentText()
                if curr_text == "Indiv. Data":
                    indiv_data_list.append(data_idx)
                elif curr_text == "Partial Data":
                    partial_data_list.append(data_idx)
                elif curr_text == "Outer Loop":
                    outer_loop_idx = data_idx
                elif curr_text == "Inner Loop":
                    inner_loop_idx = data_idx
            data = np.array(self.loaded_data_dict[key]["data"])
            outer_loop_list = data[:, outer_loop_idx]
            inner_loop_list = data[:, inner_loop_idx]
            
            outer_loop_len = np.max(outer_loop_list)+1
            inner_loop_len = np.max(inner_loop_list)+1
            
            if not len(indiv_data_list):
                data = np.sum(data[:, min(partial_data_list):max(partial_data_list)+1], axis=1)
                
            if not len(partial_data_list):
                data = data[:, min(indiv_data_list):max(indiv_data_list)+1].reshape(-1)
                
            data = data.reshape((outer_loop_len, -1))
            self.data_dict[key] = data
                
        self.sig_process_data.emit()

    def toStatusBar(self, msg):
        self.statusbar.showMessage(msg)
        
    def updatePlot(self):
        if (not self.isHidden()) or (self.isVisible()):
            if (self.plot_list[0].status == "standby") and (self.plot_list[1].status == "standby"):
                for plot_idx in range(2):
                    self.plot_list[plot_idx].canvas.draw()#_idle()
     
    def _changePlotRatio(self, ratio1, ratio2):
        if not isinstance(ratio1, int):
            self.toStatusBar("The ratio must be an int.")
        if not isinstance(ratio2, int):
            self.toStatusBar("The ratio must be an int.")
            
        self.PlotLayout.setStretchFactor(self.GBOX_plot1, ratio1)
        self.PlotLayout.setStretchFactor(self.GBOX_plot2, ratio2)
        self.toStatusBar("Changed the ratio to %d:%d" %(ratio1, ratio2))
     
    def _init_plot(self):
        th1 = PainterThread(self, self.GBOX_plot1, self._theme, 1, False)
        th2 = PainterThread(self, self.GBOX_plot2, self._theme, 2, False)
        
        # self.sig_process_data.connect(th1.wakeupThread)
        th1.sig_update_plot.connect(self.updatePlot)
        th2.sig_update_plot.connect(self.updatePlot)
        
        th1.start()
        th2.start()
        
        self.plot_list = [th1, th2]
        
        
#%% ProgressBar
    def setProgressBarProgress(self, curr_idx, max_idx):
        percentage = int(curr_idx*100/max_idx)
        self.setProgressbarStylesheet('normal')
        self.PRGB_progress.setValue(percentage)
        
    def setProgressBarStatus(self, text):
        self.LBL_progress_status.setText("Status: %s" % text)
        
        
    def setProgressbarStylesheet(self, status):
        if status == "normal":
            self.PRGB_progress.setStyleSheet(self._progressbar_stylesheet_normal[self._theme])
            
        elif status == "complete":
            self.PRGB_progress.setStyleSheet(self._progressbar_stylesheet_complete[self._theme])
            self.PRGB_progress.setValue(100)
            
        elif status == "error":
            self.PRGB_progress.setStyleSheet(self._progressbar_stylesheet_error[self._theme])

#%%
        
class PickleLoader(QThread):
    
    _sig_file_loaded = pyqtSignal(int, int) # Loaded_file_index, File_list_length
    
    def __init__(self, parent, file_list):
        super().__init__()
        self.parent = parent
        self.file_list = file_list
        
        self._status = "standby"
        self.loaded_data_dict ={}
        
        self.file_len = len(self.file_list)
        self.load_break = False
        
    def run(self):
        self._status = "running"
        for file_idx, file_name in enumerate(self.file_list):
            self._status = "loading"
            if self.load_break:
                break
            else:
                base_file_name = os.path.basename(file_name)
                self.loaded_data_dict[base_file_name] = self.loadPickleFile(file_name)
                self.parent.updateData(self.loaded_data_dict)
                self._sig_file_loaded.emit(file_idx+1, self.file_len)
                
                
    def loadPickleFile(self, file_name):
        with open (file_name, 'rb') as fr:
            loaded_data = pickle.load(fr)
            
        loaded_data_params = {}
        for key, val in loaded_data.items():
            if not key == "data":
                loaded_data_params[key] = val
        loaded_data_dict = {"data": loaded_data["data"],
                            "shape": np.shape(loaded_data["data"]),
                            "params": loaded_data_params}
        return loaded_data_dict
                
                
#%%

class PainterThread(QThread):
    
    sig_update_plot = pyqtSignal()
    
    def __init__(self, parent=None, frame=None, theme="black", index=0, master=False):
        super().__init__()
        self.parent = parent
        self.theme = theme
        self.master = master
        self.status = "standby"
        self.run_flag = False
        self.index = index
        
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        
        self.raw_data = None        
        self.x_data = [1, 2, 3, 4, 5, 6, 7, 8]
        self.y_data = [3, 2, 5, 7, 1, 2, 3, 4]
        self.xlabel = r""
        self.ylabel = r""
        self.title = r""
        self.color = "C%d" % (not (index-1))
        
        self.data_label = r""
        self.fit_label = r""
        
        self.plot_type = "Line"
        self.plot_x_type = "Average"
        self.plot_y_type = "Average"
        self.hist_max = 0
        self.threshold = 1
        self.data_dict = {}
        
        self.makePlot(frame)
        
        self.parent.sig_process_data.connect(self.wakeupThread)
        
    def drawPlot(self):
        self.canvas.draw()
        
    def intoQueue(self, item):
        self.queue.put(item)
        
    def setTitle(self, title):
        self.title = title
        if self.status == "standby":
            self.ax.set_title(r"%s" % title)
            self.drawPlot()
        
    def setXLabel(self, label):
        self.xlabel = label
        if self.status == "standby":
            self.ax.set_xlabel(r"%s" % label)
            self.drawPlot()
        
    def setYLabel(self, label):
        self.ylabel = label
        if self.status == "standby":
            self.ax.set_ylabel(r"%s" % label)
            self.drawPlot()
            
    def changeType(self, plot_type):
        if not plot_type in ["Line", "Bar", "Point"]:
            self.parent.toStatusBar("The plot type should be one of (Line, Bar, Point).")
            return
        
        self.plot_type = plot_type
        self.plotData()
        
    def plotData(self):
        if self.status == "standby":
            self.plotByType()
            self.drawPlot()
            
    def wakeupThread(self):
        self.cond.wakeAll()
        
    def run(self):
        while True:
            self.mutex.lock()
            self.status = "running"
            
            self.processData()
            self.ax.set_title(self.title)
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.ylabel)
            self.plotByType()
            
            self.sig_update_plot.emit()
            self.status = "standby"
            self.cond.wait(self.mutex)
            self.mutex.unlock()
            
    def plotByType(self):
        self.ax.clear()
        if self.plot_type == "Line":
            self.ax.plot(self.x_data, self.y_data, color=self.color)
            
        elif self.plot_type == "Bar":
            self.ax.bar(self.x_data, self.y_data, color=self.color)
            
        elif self.plot_type == "Point":
            self.ax.scatter(self.x_data, self.y_data, color=self.color)
        
    def makePlot(self, frame):
        self.fig = plt.Figure(tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = Toolbar_With_Popup(self.canvas, frame, self.theme, self.index)
        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 6)
        frame.setLayout(layout)
        
        self.ax = self.fig.add_subplot(1,1,1)
        spine_list = ['bottom', 'top', 'right', 'left']
        
        if self.theme == "black":
            plt.style.use('dark_background')
            plt.rcParams.update({"savefig.facecolor": [0.157, 0.157, 0.157],
                                "savefig.edgecolor": [0.157, 0.157, 0.157]})
            
            self.fig.set_facecolor([0.157, 0.157, 0.157])
            self.ax.set_facecolor([0.157, 0.157, 0.157])
            self.ax.tick_params(axis='x', colors=[0.7, 0.7, 0.7], length=0)
            self.ax.tick_params(axis='y', colors=[0.7, 0.7, 0.7], length=0)
            
            for spine in spine_list:
                self.ax.spines[spine].set_color([0.7, 0.7, 0.7])
                
            for action in self.toolbar.actions():
                action_text = action.text()
                action.setIcon(QtGui.QIcon(dirname + '/icons/%s.png' % action_text))

        elif self.theme == "white":
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
            
            for action in self.toolbar.actions():
                action_text = action.text()
                if action_text == "Popup":
                    action.setIcon(QtGui.QIcon(dirname + '/icons/Popup_white.png'))
            
    def processData(self):
        if len(self.parent.data_dict):
            self.data_dict = self.trimData(self.parent.data_dict)
            
            data_list = []
            for data in self.data_dict.values():
                data_list.append(data)
            data_list = np.asarray(data_list)
    
            self.toPlotData(data_list)
        # self.plotData()
            
        
    def trimData(self, raw_data_dict):
        trimmed_data_dict = {}
        for key, val in raw_data_dict.items():
            indiv_data_list = []
            partial_data_list = []
            outer_loop_idx = 0
            inner_loop_idx = 0
            for data_idx in range(3):
                cbox = getattr(self.parent, "CBOX_data%d" % data_idx)
                curr_text = cbox.currentText()
                if curr_text == "Indiv. Data":
                    indiv_data_list.append(data_idx)
                elif curr_text == "Partial Data":
                    partial_data_list.append(data_idx)
                elif curr_text == "Outer Loop":
                    outer_loop_idx = data_idx
                elif curr_text == "Inner Loop":
                    inner_loop_idx = data_idx
            data = np.array(raw_data_dict[key]["data"])
            outer_loop_list = data[:, outer_loop_idx]
            inner_loop_list = data[:, inner_loop_idx]
            
            outer_loop_len = np.max(outer_loop_list)+1
            inner_loop_len = np.max(inner_loop_list)+1
            
            if not len(indiv_data_list):
                data = np.sum(data[:, min(partial_data_list):max(partial_data_list)+1], axis=1)
                
            if not len(partial_data_list):
                data = data[:, min(indiv_data_list):max(indiv_data_list)+1].reshape(-1)
                
            data = data.reshape((outer_loop_len, -1))
            trimmed_data_dict[key] = data
            
        return trimmed_data_dict
            
    def toPlotData(self, data_list):        
        data_list = np.asarray(data_list)            
        ext_axis = int(self.parent.CHBOX_file_loop.isChecked())
        
        if self.plot_y_type == "Accumulation":
            self.y_data = np.sum(np.sum(data_list, axis=2), axis = ext_axis)
            
        elif self.plot_y_type == "Histogram":
            max_len = np.amax(data_list) + 1
            self.y_data = np.zeros(max_len)
            for data in data_list:
                for datum in data:
                    self.y_data += np.bincount(datum, minlength=max_len)
                
        elif self.plot_y_type == "State Discrimination":
            self.y_data = np.mean(np.mean(data_list > self.threshold, axis=2), axis = ext_axis)
            
        elif self.plot_y_type == "Average":
            self.y_data = np.mean(np.mean(data_list, axis=2), axis = ext_axis)

        self.x_data = np.arange(len(self.y_data))
        

_theme_base = {"white": """
                          QWidget{
                                 background-color:rgb(255,255,255);
                                 selection-background-color:rgb(130,150,200);
                                 pressed-background-color:rgb(130,150,200);
                                 gridline-color:rgb(120,120,120);
                                 color:rgb(0,0,0);
                                 }
                         QHeaderView{background-color:rgb(210,210,210);}
                         QHeaderView::section{background-color:rgb(210,210,210);}
                         QHeaderView::section::checked{background-color:rgb(130,150,200);color:rgb(255,255,255);}
                         QTableCornerButton::section{background-color:rgb(255,255,255);}
                         QComboBox{background-color:rgb(210,210,210);}
             			 QGroupBox{background-color:rgb(255, 255, 255); color:rgb(0, 0, 0);}
                         QLineEdit{background-color:rgb(210, 210, 210); color:rgb(0, 0, 0); border:none;}
             			 QSlider::handle:horizontal {
                                                     background:rgb(145, 168, 210);
                                                     width: 12px;
                                                     height: 6px;
                                                     border-radius: 2px;
                                                     }
                         QProgressBar{border: 2px solid gray;
                                                             border-radius: 5px;
                                                             text-align: center;
                                                             background-color:rgb(255,255,255);
                                                             color:rgb(0,0,0);
                                                             }
                                                QProgressBar::chunk{background-color: lightblue;
                                                                    width: 10px;
                                                                    margin: 1px;}
                         QPushButton{
                                     border-radius: 5px ;background-color: rgb(180, 180, 180); 
                                     color: rgb(255, 255, 255); color: rgb(255, 255, 255);
                                     border-style: outset; border-bottom: 1px solid;
                                     border-right: 1px solid
                                     }
                         QPushButton:pressed {
                                              border-radius: 5px; background-color: rgb(145, 168, 210);
                                              color: rgb(255, 255, 255);
                                              border-style: outset; border-top: 2px solid; border-left: 2px solid;
                                              }
                         QPushButton:checked {
                                              border-radius: 5px; background-color: rgb(145, 168, 210);
                                              color: rgb(255, 255, 255);
                                              border-style: outset; border-top: 2px solid; border-left: 2px solid;
                                              }
                         QPushButton:hover {
                                           border-radius: 5px; background-color: rgb(145, 168, 210);
                                           color: rgb(255, 255, 255);
                                           border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                           }
                         QCheckBox::indicator::unchecked:hover{ border: 1px solid skyblue; background-color:white;}
                         QCheckBox::indicator::checked:hover{ border: 1px solid black; background-color:skyblue;}
                         QRadioButton::indicator::unchecked:hover{ border: 1px solid skyblue; background-color:white; border-radius: 5px;}
                         QRadioButton::indicator::checked:hover{ border: 1px solid black; background-color:skyblue; border-radius: 5px;}
                                  """,
               "black": """
                          QWidget{
                                 background-color:rgb(40,40,40);
                                 selection-background-color:rgb(240,180,60);
                                 pressed-background-color:rgb(240,180,60);
                                 color:rgb(180,180,180);
                                 gridline-color:rgb(120,120,120);
                                 } 
                         QProgressBar{border: 2px solid lightgray;
                                     border-radius: 5px;
                                     text-align: center;
                                     background-color:rgb(40,40,40);
                                     color:rgb(255,255,255);
                                     }
                         QProgressBar::chunk{background-color: orange;
                                            width: 10px;
                                            margin: 1px;}
                         QHeaderView{background-color:rgb(40,40,40);}
                         QHeaderView::section{background-color:rgb(80,80,80);}
                         QHeaderView::section::checked{background-color:rgb(210,120,20);color:rgb(255,255,255);}
                         QListWidget{background-color:rgb(40,40,40);}
                         QListWidget::item{background-color:rgb(80,80,80);}
                         QListWidget::item::selection{background-color:rgb(210,120,20);color:rgb(255,255,255);}
                         QTableCornerButton::section{background-color:rgb(80,80,80);}
                         QTableView::item{align:center;}
                         QLineEdit{background-color:rgb(0,0,0);color:rgb(180,180,180);border:none;}
             			 QSlider::handle:horizontal {
                                                     background:rgb(200, 95, 10);
                                                     width: 12px;
                                                     height: 6px;
                                                     border-radius: 2px;}
             			 QComboBox{
                                 color: rgb(180, 180, 180);
                                 background-color: rgb(80, 80, 80);
                                 selection-background-color: rgb(160, 80, 10);
                                 }
                         QComboBox::hover{
                                         background-color:rgb(160, 80, 10);
                                         color:rgb(180, 180, 180);
                                         }
                         QPushButton {
                                     border-radius: 5px; background-color: rgb(80, 80, 80);
                                     color: rgb(180, 180, 180);
                                     border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                     }
                         QPushButton:pressed {
                                              border-radius: 5px; background-color: rgb(200, 95, 10);
                                              color: rgb(180, 180, 180);
                                              border-style: outset; border-top: 3px solid; border-left: 3px solid;
                                              }
                         QPushButton:checked {
                                              border-radius: 5px; background-color: rgb(200, 95, 10);
                                              color: rgb(180, 180, 180);
                                              border-style: outset; border-top: 3px solid; border-left: 3px solid;
                                              }
                         QPushButton:hover {
                                           border-radius: 5px; background-color: rgb(200, 95, 10);
                                           color: rgb(180, 180, 180);
                                           border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                           }
                         QCheckBox::indicator::unchecked:hover{ border: 1px solid orange; background-color:white;}
                         QCheckBox::indicator::checked:hover{ border: 1px solid dark-gray; background-color:orange;}
                         QRadioButton::indicator::unchecked:hover{ border: 1px solid orange; background-color:white; border-radius: 5px;}
                         QRadioButton::indicator::checked:hover{ border: 1px solid dark-gray; background-color:orange; border-radius: 5px;}
                         """
                         }
     
class Toolbar_With_Popup(NavigationToolbar):
    
    def __init__(self, figure_canvas, parent=None, theme="black", index=0):
        self.toolitems = (('Home', 'Reset original view', 'home', 'home'),
          ('Back', 'Back to previous view', 'back', 'back'),
          ('Forward', 'Foward to next view', 'forward', 'forward'),
          (None, None, None, None),
          ('Pan', 'Left button pans, Right button zooms\nx/y fixes axis, CTRL fixes aspect', 'move', 'pan'),
          ('Zoom', 'Zoom to rectangle\nx/y fixes axis, CTRL fixes aspect', 'zoom_to_rect', 'zoom'),
          (None, None, None, None),
          ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
          ('Save', 'Save the figure', 'filesave', 'save_figure'),
          ('Popup', 'Open the figure in a popup window', "popup", 'popup_figure'),
          )
    
        NavigationToolbar.__init__(self, figure_canvas, parent=None)
        self.canvas = figure_canvas
        self.theme = theme
        self.index = index
        
        self.popup_list = []
        self.popup_idx = 0

    def popup_figure(self):
        new_window = self._make_popup()
        new_window._sig_closed_popup.connect(self.killPopup)
        new_window.show()
        
        self.popup_list.append(new_window)
      
    def _make_popup(self):
        time_now = datetime.datetime.now().strftime("%y%m%d_%H:%M:%S")
        
        new_window = Figure_with_Popup()
        new_window.setWindowTitle("Figure %d of Plot %d, %s" % (self.popup_idx, self.index, time_now))
        self.popup_idx += 1
        
        # Deep copying with pickle
        # Usually the matplotlib figure cannot be deep copied.
        pickled_fig = pickle.dumps(self.canvas.figure)
        
        popup_fig = pickle.loads(pickled_fig)
        popup_canvas = FigureCanvas(popup_fig)
        popup_toolbar = NavigationToolbar(popup_canvas, new_window)
        
        layout = QVBoxLayout()
        layout.addWidget(popup_toolbar)
        layout.addWidget(popup_canvas)
        layout.setContentsMargins(0, 0, 0, 6)
        new_window.setLayout(layout)
      
        if self.theme == "black":
            new_window.setStyleSheet("background-color:rgb(40,40,40); color:rgb(180,180,180);")
            for action in popup_toolbar.actions():
                action_text = action.text()
                action.setIcon(QtGui.QIcon(dirname + '/icons/%s.png' % action_text))
        elif self.theme == "white":
           new_window.setStyleSheet("background-color:rgb(255,255,255); color:rgb(0,0,0);")

        return new_window
    
    def killPopup(self):
        self.popup_list.remove(self.sender())
      
class Figure_with_Popup(QtWidgets.QWidget):
    
    _sig_closed_popup = pyqtSignal()
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        
    def closeEvent(self, e):
        self._sig_closed_popup.emit()


if __name__ == "__main__":
    theme = "black"
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    da = DataAnalyzerGUI(theme=theme)
    da.setStyleSheet(_theme_base[theme])
    da.show()

