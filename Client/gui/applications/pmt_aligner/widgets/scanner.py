# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 22:37:43 2021

@author: Junho Jeong
"""
import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout
from PyQt5.QtGui     import QColor
from PyQt5.QtCore    import pyqtSignal, QObject

import numpy as np
import pickle
import datetime
import pyqtgraph as pg

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/scanner.ui'
Ui_Form, QtBaseClass = uic.loadUiType(uifile)
version = "3.1"

seq_dirname = dirname + "/../../../libraries/sequencer_files/"

#%% Temporary
class ScannerGUI(QtWidgets.QWidget, Ui_Form):
    
    def __init__(self, parent=None, sequencer=None, motor_controller=None, motor_nicks=[], theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.parent = parent
        self.cp = self.parent.cp
        self.app_name = self.parent.app_name

        self.motors = {nick: motor_controller._motors[nick] for nick in motor_nicks if ("x" in nick or "y" in nick)}
        self.sequencer = sequencer
        
        self._theme = theme
        
        self.im_min = 0
        self.im_max = 100
        self.plot_im = np.random.random((5, 5))
        self.significant_figure = 1
        
        self._disable_list = [self.BTN_scan_vicinity,
                              self.BTN_start_scanning,
                              self.BTN_go_to_max]
        self._initUi()
        
        self.scanner = PMTScanner(self, self.sequencer, self.motors, self.parent)
        self.scanner._sig_scanner.connect(self.recievedScannerSignal)
        
        self.sequencer.sig_occupied.connect(self.setInterlock)


    def saveData(self, save_file_name=""):
        if save_file_name == "":
            save_file_name = self.LE_save_file_dir.text() + "/" + self.LE_save_file_name.text()
        if save_file_name[-3:] == "pkl":
            save_file_name = save_file_name[:-4]
            
        save_dict = {"img": self.plot_im,
                     "x_pos": self.scanner.x_scan_range,
                     "y_pos": self.scanner.y_scan_range}
        if os.path.isfile(save_file_name + ".pkl"):
            idx = 0
            while True:
                if os.path.isfile(filename + "_%02d" % idx + ".pkl"):
                    idx += 1
                else:
                    break
            save_file_name = save_file_name + "_%02d" % idx
            
        
        with open (save_file_name + ".pkl", "wb") as fw:
            pickle.dump(save_dict, fw)
        
        try:
            self.parent.grab().save(save_file_name + ".png")
        except Exception as ee:
            self.toStatusBar("An error while saving a screenshot. (%s)" % ee)
        self._setDefaultFileName()
        
    def loadData(self, data_file_name=""):
        try:
            with open (data_file_name, "rb") as fr:
                loaded_data_dict = pickle.load(fr)
                img, x_scan_range, y_scan_range = loaded_data_dict["img"], loaded_data_dict["x_pos"], loaded_data_dict["y_pos"]
                # self.plot_im = loaded_data_dict["img"]
                # self.scanner.x_scan_range = loaded_data_dict["x_pos"]
                # self.scanner.y_scan_range = loaded_data_dict["y_pos"]
            step_value = np.round(np.diff(x_scan_range)[0], 3)
            self.setSignificant_figure(step_value)
            self._temporaryUpdatePlot(img, x_scan_range, y_scan_range)
            self.toStatusBar("Successfully loaded a data file. (%s)" % os.path.basename(data_file_name))
                
        except Exception as ee:
            self.toStatusBar("An error while opening the data file.(%s)" % ee)
            
    def _temporaryUpdatePlot(self, plot_im, x_scan_range, y_scan_range):
        """
        This method is a temporary debugging method for loading a saved data. This will be deprecated.
        """
        if self.CB_auto_minmax.isChecked():
            im_min, im_max = np.min(plot_im), np.max(plot_im)
            self.plot_min.setText("%.1f" % im_min)
            self.plot_max.setText("%.1f" % im_max)
        else:
            try:
                value_list = [float(self.plot_min.text()), float(self.plot_max.text())]
                value_list.sort()
                im_min, im_max = value_list
            except:
                self.toStatusBar("The min and max values should be numbers.")
                
        self.colorbar.setLevels( (im_min, im_max) )
        self.im.setImage(plot_im, autoLevels=False)
        
        ax = self.plot.getAxis('bottom')  # This is the trick
        dx = [(idx+0.5, str(round(value, self.significant_figure))) for idx, value in enumerate(x_scan_range)]
        ax.setTicks([dx, []])
        
        ay = self.plot.getAxis('left')  # This is the trick
        dy = [(idx+0.5, str(round(value, self.significant_figure))) for idx, value in enumerate(y_scan_range)]
        ay.setTicks([dy, []])
        
        self.plot.setLimits(xMin=0, xMax=len(x_scan_range), yMin=0, yMax=len(y_scan_range))
                    
        
    def _initUi(self):
        self.plot, self.im, self.colorbar = self._create_canvas(self.image_viewer)
        self.updatePlot()
        
        self.save_file_dir = dirname + "\\data"
        if not os.path.isdir(self.save_file_dir):
            os.mkdir(self.save_file_dir)
        
        self.save_file_dir += "\\%s" % self.app_name
        if not os.path.isdir(self.save_file_dir):
            os.mkdir(self.save_file_dir)
            self.toStatusBar("No save data directory for this application has been found, a new dir has been created.")
        self._initializePosition()
        self._setDefaultFileName()
        
    def _initializePosition(self):
        for axis in ["x", "y"]:
            initial_pos = float(getattr(self.parent, "LBL_%s_pos" % axis.upper()).text())
            step = getattr(self, "GUI_%s_step" % axis).value()
            getattr(self, "GUI_%s_start" % axis).setValue(initial_pos - step*self.SPBOX_vicinity_length.value())
            getattr(self, "GUI_%s_stop" % axis).setValue(initial_pos + step*self.SPBOX_vicinity_length.value())
        
    def _setDefaultFileName(self):
        self.LE_save_file_dir.setText(self.save_file_dir)
        self.LE_save_file_name.setText("%s_%s" % (datetime.datetime.now().strftime("%y%m%d_%H%M%S"), self.app_name))
        
    def _readConfig(self):
        if "color_map" in self.cp.options(self.app_name):
            color_map = self.cp.get(self.app_name, "color_map")
            
            return color_map
    
    def _create_canvas(self, frame):
        if self._theme == "black":
            pg.setConfigOption('background', QColor(40, 40, 40))
            color_map = "inferno"
            
        else:
            color_map = "viridis"
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
            
        config_color_map = self._readConfig()
        if config_color_map:
            color_map = config_color_map
        
        canvas = pg.GraphicsLayoutWidget()
        plot = canvas.addPlot()
        plot.setDefaultPadding(0)

        layout = QHBoxLayout()
        layout.layoutLeftMargin = 0
        layout.layoutRightMargin = 0
        layout.layoutTopMargin = 0
        layout.layoutBottomMargin = 0
        layout.addWidget(canvas)
        
        frame.setLayout(layout)
        
        plot.vb.setLimits(xMin=0,
                          xMax=self.plot_im.shape[1],
                          yMin=0,
                          yMax=self.plot_im.shape[0])
        plot.vb.invertY(True)

        
        im = pg.ImageItem(self.plot_im, axisOrder="row-major", autoRange=False)
        im.setAutoDownsample(True)
        im.setImage(self.plot_im, autoLevels=False)

        plot.addItem(im)
        plot.installEventFilter(self)
        
        cmap = pg.colormap.getFromMatplotlib( color_map )
        
        colorbar = pg.ColorBarItem(colorMap=cmap, interactive=False)
        colorbar.setImageItem(im, insert_in=plot)
        
        return plot, im, colorbar
    
    
    def updatePlot(self):
        if (not self.isHidden() and not self.isMinimized()):
            if self.CB_auto_minmax.isChecked():
                self.im_min, self.im_max = np.min(self.plot_im), np.max(self.plot_im)
                self.plot_min.setText("%.1f" % self.im_min)
                self.plot_max.setText("%.1f" % self.im_max)
            else:
                try:
                    value_list = [float(self.plot_min.text()), float(self.plot_max.text())]
                    value_list.sort()
                    self.im_min, self.im_max = value_list
                except:
                    self.toStatusBar("The min and max values should be numbers.")
                    
            self.colorbar.setLevels( (self.im_min, self.im_max) )
            self.im.setImage(self.plot_im, autoLevels=False)
            
            ax = self.plot.getAxis('bottom')  # This is the trick
            dx = [(idx+0.5, str(round(value, self.significant_figure))) for idx, value in enumerate(self.scanner.x_scan_range)]
            ax.setTicks([dx, []])
            
            ay = self.plot.getAxis('left')  # This is the trick
            dy = [(idx+0.5, str(round(value, self.significant_figure))) for idx, value in enumerate(self.scanner.y_scan_range)]
            ay.setTicks([dy, []])
                        
            self.LBL_latest_count.setText("%.2f" % self.scanner.recent_pmt_result)
            self.LBL_points_done.setText("%d" % (self.scanner.scan_idx+1))
            self.LBL_total_points.setText("%d" % self.scanner.scan_length)
            
            QtWidgets.QApplication.processEvents()

            
    def resetPlot(self):
        self.plot_im = self.scanner.scan_image
        self.plot.vb.setLimits(xMin=0,
                              xMax=self.plot_im.shape[1],
                              yMin=0,
                              yMax=self.plot_im.shape[0])
        if "Resume" in self.BTN_pause_or_resume_scanning.text():
            self.BTN_pause_or_resume_scanning.setText("Pause Scanning")
        
        self.updatePlot()
        
    def changedStepValue(self):
        value = self.sender().value()
        axis = self.sender().objectName().split("_")[1]
        for spin_box in [getattr(self, "GUI_%s_%s" % (axis, attr_name)) for attr_name in ("start", "stop")]:
            spin_box.setSingleStep(value)
        self.setSignificant_figure(value)
            
            
    def setSignificant_figure(self, value):
        if 1 <= value:
            self.significant_figure = 0
        elif 0.1 <= value and value < 1:
            self.significant_figure = 1
        elif 0.01 <= value and value < 0.1:
            self.significant_figure = 2
        else:
            self.significant_figure = 3
            
    def recievedScannerSignal(self, s):
        if s == "R":
            self.resetPlot()
        elif s == "U": # updated plot iamge
            self.updatePlot()
    
    def pressedScanStartButton(self):
        for axis in ["x", "y"]:
            start = getattr(self, "GUI_%s_start" % axis).value()
            stop  = getattr(self, "GUI_%s_stop" % axis).value()
            if stop <= start:
                self.toStatusBar("The stop value should be larger than the start value.")
                return
        self.scanner.startScanning()
    
    def pressedChangeSaveDir(self):
        save_dir = QFileDialog.getExistingDirectory(parent=self, directory=dirname + '/../save_data')
        if save_dir == "":
            self.toStatusBar("Aborted changing the saving directory.")
        else:
            self._changeSaveDir(save_dir)
            self.save_file_dir = save_dir
            self.toStatusBar("Changed the saving directory.")
    
    def pressedScanVicinityButton(self):
        try:
            for axis in ["x", "y"]:
                
                step = getattr(self, "GUI_%s_step" % axis).value()
                center = float(getattr(self.parent, "LBL_%s_pos" % axis.upper()).text())
                
                start = max(0, center - step*self.SPBOX_vicinity_length.value())
                stop = min(12, center + step*self.SPBOX_vicinity_length.value())
    
                getattr(self, "GUI_%s_start" % axis).setValue(start)
                getattr(self, "GUI_%s_stop" % axis).setValue(stop)
        except Exception as ee:
            self.toStatusBar("An error while seeting scan positions.(%s)" % ee)
            return
        
        self.scanner.startScanning()    
    
    def pressedPauseScanning(self):
        if "Pause" in self.BTN_pause_or_resume_scanning.text():
            self.BTN_pause_or_resume_scanning.setText("Resume Scanning")
            self.scanner.pauseScanning()
        else:
            self.BTN_pause_or_resume_scanning.setText("Pause Scanning")
            self.scanner.continueScanning()
    
    def pressedSaveButton(self):
        pre_filename = "%s/%s" % (self.LE_save_file_dir.text(), self.LE_save_file_name.text())
        save_file_name, _ = QFileDialog.getSaveFileName(self, "Saving file",
                                                        pre_filename, "Data files (*.pkl)")
        if save_file_name == "":
            self.toStatusBar("Aborted saving a data file.")
        else:
            self.saveData(save_file_name)
    
    def pressedLoadSaveFile(self):
        pre_filename = "%s/" % (self.LE_save_file_dir.text())
        open_file_name, _ = QFileDialog.getOpenFileName(self, "Select File", pre_filename, "Data files(*.pkl)")
       
        if open_file_name == "":
            self.toStatusBar("Aborted loading a data file.")
        else:
            self.loadData(open_file_name)
    
    def pressedGoToMax(self):
        self.scanner.goToMaxPosition()
    
    def pressedApplyButton(self):
        self.updatePlot()
                
    def setInterlock(self, occupied_flag):
        if occupied_flag:
            if self.sequencer.occupant == self.scanner:
                self.BTN_scan_vicinity.setEnabled(False)
                self.BTN_go_to_max.setEnabled(False)
                self.BTN_pause_or_resume_scanning.setEnabled(True)
                print("enabled button")
            else:
                self._setEnableObjects(False)
                self.BTN_pause_or_resume_scanning.setEnabled(False)
        else:
            self._setEnableObjects(True)
            self.BTN_pause_or_resume_scanning.setEnabled(True)
            
        
    def _setEnableObjects(self, flag):
        for obj in self._disable_list:
            obj.setEnabled(flag)
            
    def toStatusBar(self, msg):
        self.parent.toStatusBar(msg)

class PMTScanner(QObject):
    
    _sig_scanner = pyqtSignal(str) # "R: reset, U: image updated"
    _status = "standby" # scanning or paused 
    
    
    def __init__(self, gui=None, sequencer=None, motors=None, pmt_aligner=None):
        super().__init__()

        self.gui = gui
        self.sequencer = sequencer
        self.motors = motors
        self.pmt_aligner = pmt_aligner
        
        self.x_scan_range = np.arange(0, 0.6, 0.1)
        self.y_scan_range = np.arange(0, 0.6, 0.1)
        self.scan_length = 36
        self.scan_idx = 0
        self.recent_pmt_result = 0
        
        self.scan_image = np.random.random((6, 6))
        self.gui.plot_im = self.scan_image
        
        self._list_motors_moving = []
        self._connect_signals()
                
    def __call__(self):
        return "scanner"
            
    def getScanRange(self, start, end, step):
        scan_list = np.arange(start, end, step).tolist()
        if not end in scan_list:
            scan_list.append(end)
        return np.asarray(scan_list)
    
    def getScanCoordinates(self, x_range, y_range):
        x_scan_coord, y_scan_coord = np.meshgrid(x_range, y_range)
        x_scan_coord[1::2] = np.flip(x_scan_coord[1::2], 1)
        
        return x_scan_coord.flatten(), y_scan_coord.flatten()
    
    def getNextScanCoordinate(self):
        self.scan_idx += 1
        return self.x_scan_coord[self.scan_idx], self.y_scan_coord[self.scan_idx]
    
    def getIndicesOfImage(self):
        image_shape = self.scan_image.shape
        y_idx = self.scan_idx // image_shape[1]
        x_idx = self.scan_idx %  image_shape[1]
        if (y_idx % 2):
            x_idx = image_shape[1] - x_idx - 1
        
        return x_idx, y_idx
    
    def getMaxIndicesOfImage(self):
        y_idx, x_idx = np.unravel_index(self.scan_image.argmax(), self.scan_image.shape)
        return x_idx, y_idx
    
    def getMaxPositionOfImage(self):
        y_idx, x_idx = self.getMaxIndeicsOfImage()
        y_coord, x_coord = self.y_scan_range[y_idx], self.x_scan_range[x_idx]
        return x_coord, y_coord
    
    def updateScanImage(self, x_idx, y_idx, pmt_result):
        self.scan_image[y_idx][x_idx] = pmt_result
        self._sig_scanner.emit("U")
        
        if self._status == "scanning":
            if self.scan_idx+1 < self.scan_length:
                self.resumeScanning()
                return
            
        if self.gui.CB_auto_go_to_max.isChecked():
            self.goToMaxPosition()
            
        self.stopScanning()
        self.gui.saveData()
        
    def goToMaxPosition(self):
        self.x_max_pos, self.y_max_pos = self._getMaxPosition()
        position_dict = {}
        for motor_key in self.motors.keys():
            position_dict[motor_key] = getattr(self, "%s_max_pos" % ("x" if "x" in motor_key else "y"))
        self.gui.toStatusBar("Found the max position: x:%.3f, y:%.3f" % (self.x_max_pos, self.y_max_pos))
        self.pmt_aligner.MoveToPosition(position_dict)
        
        
    def resetScanning(self):
        self.x_scan_range = self.getScanRange(*[getattr(self.gui, "GUI_x_%s" % x).value() for x in ["start", "stop", "step"]])
        self.y_scan_range = self.getScanRange(*[getattr(self.gui, "GUI_y_%s" % x).value() for x in ["start", "stop", "step"]])
        

        self.x_scan_coord, self.y_scan_coord = self.getScanCoordinates(self.x_scan_range, self.y_scan_range)
        self.scan_image = np.zeros((self.y_scan_range.shape[0], self.x_scan_range.shape[0]))
        
        self.scan_idx = 0
        self.scan_length = self.x_scan_coord.shape[0]
        self._list_motors_moving = []
        self._sig_scanner.emit("R")
        
    def startScanning(self):
        self.resetScanning()
        
        if self.sequencer.is_opened:
            self.setOccupant(True)
            self._status = "scanning"
            self.moveMotorByIndex(self.scan_idx)
            
        else:
            self.pmt_aligner.toStatusBar("The FPGA is not opened!")
            
    def moveMotorByIndex(self, scan_idx):
        position_dict = {}
        for motor_key in self.motors.keys():
            self._list_motors_moving.append(motor_key)
            position_dict[motor_key] = getattr(self, "%s_scan_coord" % ("x" if "x" in motor_key else "y"))[scan_idx]
        self._list_motors_moving = list(self.motors.keys())
        self.pmt_aligner.MoveToPosition(position_dict)
        
    def pauseScanning(self):
        self._status = "paused"
        self.setOccupant(False)

    def resumeScanning(self):
        self._status = "scanning"
        self.scan_idx += 1
        self.moveMotorByIndex(self.scan_idx)
        self.setOccupant(True)

        
    def continueScanning(self):
        self._status = "scanning"
        self.moveMotorByIndex(self.scan_idx)
        self.setOccupant(True)


    def stopScanning(self):
        self._status = "standby"
        self.setOccupant(False)

        
    def setOccupant(self, flag):
        if flag:
            self.sequencer.occupant = self
        else:
            self.sequencer.occupant = ""
        self.sequencer.sig_occupied.emit(flag)
        

    def runPMT_Exposure(self):
        try:
            exposure_time = float(self.gui.LE_pmt_exposure_time_in_ms.text())
            num_average = float(self.gui.LE_pmt_average_number.text())
        except Exception as ee:
            self.pmt_aligner.toStatusBar("The value of either exposure time or average number is wrong.(%s)" % ee)
            self.stopScanning()
            return
        
        self.setExposureTime(exposure_time, num_average)
        self.sequencer.runSequencerFile()
        
    def setExposureTime(self, exposure_time, num_average=50):
        self.sequencer.loadSequencerFile(seq_file= seq_dirname + "/simple_exposure.py",
                                          replace_dict={13:{"param": "EXPOSURE_TIME_IN_MS", "value": exposure_time},
                                                        14:{"param": "NUM_AVERAGE", "value": num_average}},
                                          replace_registers={"PMT": self.pmt_aligner.detector})

    def _connect_signals(self):
        for motor in self.motors.values():
            motor._sig_motor_move_done.connect(self._motorMoved)
            
        self.sequencer.sig_seq_complete.connect(self._donePMTExposure)
            
    def _motorMoved(self, nick, position):
        if self._status == "scanning":
            if nick in self._list_motors_moving:
                self._list_motors_moving.remove(nick)
                
            if not len(self._list_motors_moving):
                self.runPMT_Exposure()
        
    def _donePMTExposure(self):
        if self.sequencer.occupant == self:
            raw_pmt_count = np.asarray(self.sequencer.data[0]) # kind of deep copying...
            if len(raw_pmt_count) > 1:
                pmt_count = np.mean(raw_pmt_count[:, 2])
            else:
                pmt_count = raw_pmt_count[0][2]
                
            self._recievedResult(pmt_count)
    
    def _recievedResult(self, pmt_result):
        self.recent_pmt_result = pmt_result
        x_idx, y_idx = self.getIndicesOfImage()
        self.updateScanImage(x_idx, y_idx, pmt_result)
        
    def _getMaxPosition(self):
        true_y_argmax, true_x_argmax = np.unravel_index(np.argmax(self.scan_image, axis=None), self.scan_image.shape)
        y_pos = self.y_scan_range[true_y_argmax]
        x_pos = self.x_scan_range[true_x_argmax]
        
        return x_pos, y_pos

if __name__ == "__main__":
    pa = Scanner()
    pa.show()