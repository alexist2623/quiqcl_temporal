# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 22:52:01 2021

@author: CPO
v1.01: read a config file. compatible with EMCCD
"""
import os
os.system('CLS')

import time
import numpy as np
from datetime import datetime
from configparser import ConfigParser

from PyQt5 import uic

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

qt_designer_file = dirname + '/CCD_GUI_v2_02.ui'
Ui_Form, QtBaseClass = uic.loadUiType(qt_designer_file)

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QVBoxLayout, QFileDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QThread, QTimer, QRectF

import pyqtgraph as pg

# from Libs.CCD_oven_v0_04 import Oven_controller
from CCD_UI_Base_Abstract import CCD_UI_base


class CCD_UI(QtWidgets.QMainWindow, CCD_UI_base, Ui_Form):
        
    def showEvent(self, e):
        if not self.BTN_acquisition.isChecked():
            self.updatePlot()
    
    def __init__(self, controller=None, theme="white"):
        QtWidgets.QMainWindow.__init__(self)
        # cam
        self._readConfig(os.getenv('COMPUTERNAME', 'defaultValue'))
        self.cam = controller
        self.image_handler = self.cam.image_thread
        self._theme = theme
        
        self.setupUi(self)
        self._init_params()

        # zoom
        self.zoom_x1 = 0
        self.zoom_y1 = 0
        self.zoom_x2 = self.cam._param_dict["SIZE"][1]
        self.zoom_y2 = self.cam._param_dict["SIZE"][0]

        # roi
        self.roi_x1 = 0
        self.roi_y1 = 0
        self.roi_x2 = self.cam._param_dict["SIZE"][1]
        self.roi_y2 = self.cam._param_dict["SIZE"][0]
        
        #
        self._initUi()
        
        # self.oc = Oven_controller(self)
        self.cam.image_thread._img_recv_signal.connect(self._countPlot)
        
        self._img_cnt = 0
        self.im_min = 0
        self.im_max = 250
        self.raw_min = 0
        self.raw_max = 250
        
        # QTimer settings
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._timedOutUpdateTimer)

        self.LBL_directory.setText(dirname + "/data")
        
        
    #%% Initialization
    def _initUi(self):       
        self.LBL_ROI_x1.setText("%d" % (self.zoom_x1))
        self.LBL_ROI_x2.setText("%d" % (self.zoom_x2))
        self.LBL_ROI_y1.setText("%d" % (self.zoom_y1))
        self.LBL_ROI_y2.setText("%d" % (self.zoom_y2))
        
        self.BTN_save.setIcon(QtGui.QIcon(dirname + '/Libs/gui_save.ico'))
        self.BTN_oven_settings.setIcon(QtGui.QIcon(dirname + '/Libs/gui_settings.ico'))
        self._makePlot(self.CCD_image_label)
        
        
    def _init_params(self):
        self.LBL_gain.setText(str(self.cam._param_dict["GAIN"]))
        self.STATUS_exp_time.setText(str(self.cam._param_dict["EXPT"]))
        self.cam.save_directory = self.LBL_directory.text()
        self._height, self._width = self.cam._param_dict["SIZE"]
                
    def _readConfig(self, pc_name):
        conf_file = dirname + '/config/%s.conf' % pc_name
        if not os.path.isfile(conf_file):
            print("No config file has been found.")
            return
        
        cp = ConfigParser()
        cp.read(conf_file)
        self._camera_type = cp.get('device', 'type')
        self._theme = cp.get('ui', 'theme')
        try:
            self._available_ccd = cp.get("server", 'avails').replace(' ', '').split(',')
        except:
            self._available_ccd = [pc_name]
        
    def _changeChamber(self, chamber_id):
        pc_name = chamber_id.split("_")[-1]
        self._readConfig(pc_name)
        self.changeTheme()
        
        
    def changeTheme(self, theme):
        self._theme = theme
        self.setStyleSheet(self._theme_color[self._theme]["main"])
        item_list = dir(self)
        for item in item_list:
            if "GBOX_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["GBOX"])
            elif "BTN_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["BTN"])
            elif "LBL_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["LBL"])
            elif "STATUS_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["STATUS"])
            elif "TXT_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["TXT"])

        self.updatePlot()
        
    def _makePlot(self, frame):
        if self._theme == "black":
            pg.setConfigOption('background', QColor(60, 60, 60))
            
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
        
        self.canvas = pg.GraphicsLayoutWidget()
        self.plot = self.canvas.addPlot()
        self.plot.setDefaultPadding(0)
        self.plot.sigRangeChanged.connect(self.zoom_callback)

        self.canvas.scene().sigMouseClicked.connect(self.mouseClickedEvent)
        
        layout = QVBoxLayout()
        layout.layoutLeftMargin = 0
        layout.layoutRightMargin = 0
        layout.layoutTopMargin = 0
        layout.layoutBottomMargin = 0
        layout.addWidget(self.canvas)
        frame.setLayout(layout)
        
        
        self._plot_im = np.zeros((self._height, self._width))
        
        self.plot.vb.setLimits(xMin=0,
                               xMax=self._width,
                               yMin=0,
                               yMax=self._height)
        self.plot.vb.setAspectLocked()
        
        self.im = pg.ImageItem(self._plot_im, axisOrder="row-major", autoRange=False)
        self.im.setAutoDownsample(True)
        
        self.plot.addItem(self.im)
        self.plot.installEventFilter(self)
        
        cmap = pg.colormap.getFromMatplotlib( self._theme_color[self._theme]["color_map"] )
        
        self.colorbar = pg.ColorBarItem(colorMap=cmap, interactive=False)
        self.colorbar.setImageItem(self.im, insert_in=self.plot)
        
        
    def StartAcquisition(self, acq_flag):
        self._enableObjects(acq_flag)
        if acq_flag:
            self._img_cnt = 0
            
            self.cam.toWorkList(["C", "RUN", []])
            self.update_timer.start(self._update_interval)
            
        else:
            self.cam.toWorkList(["C", "STOP", []])
            
    def _enableObjects(self, flag):
        self.CBOX_single_scan.setEnabled(not flag)
        self.CBOX_Autosave.setEnabled(not flag)
            
    #%% Image Min & Max
    def ChangeMin(self):
        min_val = int(float(self.LBL_min.text()))

        if min_val < 0:
            min_val = 0
            
        self.LBL_min.setText(str(min_val))
        self.cam.d_min = min_val
        self.im_min = min_val
        
    def ChangeMax(self):
        max_val = int(float(self.LBL_max.text()))
            
        self.LBL_max.setText(str(max_val))
        self.cam.d_max = max_val
        self.im_max = max_val
        
    def MinSliderMoved(self, slider_val):
        min_val = int(float(self.LBL_min.text()))
        min_step = int(float(self.STATUS_min_unit.text()))
        
        new_min_val = int(min_val + (-1)**(slider_val < self._slider_min) * min_step)
        
        self._slider_min = slider_val
        self.LBL_min.setText(str(new_min_val))
        self.ChangeMin()
        
    def MaxSliderMoved(self, slider_val):
        max_val = int(float(self.LBL_max.text()))
        max_step = int(float(self.STATUS_max_unit.text()))
        
        new_max_val = int(max_val + (-1)**(slider_val < self._slider_max) * max_step)
        
        self._slider_max = slider_val
        self.LBL_max.setText(str(new_max_val))
        self.ChangeMax()
        
    def ROISet(self):
        for roi_pos in ["x1", "x2", "y1", "y2"]:
            roi_label = getattr(self, "LBL_ROI_%s" % roi_pos)
            try:
                value = int(roi_label.text())
            except:
                self.toStatusBar("ROI positions must be integers. (%s)" % roi_pos)
                return
            setattr(self, "zoom_" + roi_pos, value)
        
        if self.zoom_x1 > self.zoom_x2:
            self.zoom_x2 = self.zoom_x1
            self.zoom_x1 = int(self.LBL_ROI_x2.text())
        
        if self.zoom_y1 > self.zoom_y2:
            self.zoom_y2 = self.zoom_y1
            self.zoom_y1 = int(self.LBL_ROI_y2.text())
            
        self._zoom_in_flag = True
        self.plot.setRange( QRectF(self.zoom_x1, self.zoom_y1, self.zoom_x2 - self.zoom_x1, self.zoom_y2 - self.zoom_y1) )
                    
    #%% Gain
    def ChangeGain(self):
        gain = int(float(self.LBL_gain.text()))
        self.cam.toWorkList(["C", "GAIN", [gain]])
        
    #%% Save data
    def SelectFilepath(self):
        save_path = QFileDialog.getExistingDirectory(self, "Select Directory", self.LBL_directory.text(), QFileDialog.DontUseNativeDialog)
        if save_path == "":
            pass
        else:
            self.LBL_directory.setText(save_path)
            self.cam.save_directory = save_path
            
    def SelectSavepath(self):
        save_file, _ = QFileDialog.getSaveFileName(self, 'Save File', self.LBL_directory.text(), options=QFileDialog.DontUseNativeDialog)
        if save_file == "":
            pass
        else:
            save_path, save_name = os.path.split(save_file)
            self.SaveImage(save_path, save_name)
            
    def SaveImage(self, save_path="", save_name=""):
        if save_path == "":
            save_path = self.LBL_directory.text()
        if save_name == "":
            save_name = datetime.now().strftime("%y%m%d_%H%M_default")
        
        if (save_name[-4:] == ".png") or (save_name[-4:] == ".tif"):
            save_name = save_name[:-4]
        
        save_name = save_path + "/" + save_name
        
        if os.path.exists(self.AddExtention(save_name)):
            save_name += "_%03d"
            idx = 0
            while os.path.exists(self.AddExtention(save_name % idx)):
                idx += 1
            save_name = save_name % idx
        
        if self.CBOX_file_format.currentText() == "png":
            self.cam.saveImages( self.AddExtention(save_name), False, self.CBOX_Full.isChecked() )
        else:
            self.cam.saveImages( self.AddExtention(save_name), True, self.CBOX_Full.isChecked() )
            
    def AddExtention(self, save_name):
        return save_name + ('.png' if self.CBOX_file_format.currentText() == "png" else '.tif')

    def ChangeFileFormat(self, file_format):
        self.cam.save_format = file_format
        
    def SetRecord(self, record_flag):
        self._auto_save = record_flag
    
    def SetScanLength(self):
        try:
            length = int(self.LBL_scan_length.text())
            self.LBL_scan_length.setText("%d" % length)
            self.cam.toWorkList(["C", "NTRG", [length]])
        except Exception as err:
            self.toStatusBar(err)
            
    def SetSinglescan(self, single_scan):
        if single_scan:
            self.cam.toWorkList(["C", "ACQM", ['single_scan']])
            if not int(self.LBL_scan_length.text()):
                self.LBL_scan_length.setText("1")
        else:
            self.cam.toWorkList(["C", "ACQM", ['continuous_scan']])
            
    def setFlip(self, flag):
        if self.sender() == self.CBOX_flip_horizontal:
            self.cam.toWorkList(["C", "FLIP", ["x", flag]])
        else:
            self.cam.toWorkList(["C", "FLIP", ["y", flag]])
            
    def toStatusBar(self, msg):
        self.statusBar.showMessage(msg)
           
            
    #%% Mouse Interaction
    def clickedZoomIn(self):
        self.plot.setRange( QRectF(self.zoom_x1, self.zoom_y1, self.zoom_x2 - self.zoom_x1, self.zoom_y2 - self.zoom_y1) )
        if self.BTN_draw_rect.isChecked():
            self.BTN_draw_rect.setChecked(False)
    
    def clickedZoomOut(self):
        self.plot.setRange( QRectF(0, 0, self._width, self._height) )
        if self.BTN_draw_rect.isChecked():
            self.BTN_draw_rect.setChecked(False)
    
    def clickedDrawRect(self, flag):
        if flag:
            self.plot.vb.setMouseMode(self.plot.vb.RectMode)
        else:
            self.plot.vb.setMouseMode(self.plot.vb.PanMode)
    
    def zoom_callback(self):
        if self._zoom_in_flag:
            self._zoom_in_flag = False
            return
        (x1, x2), (y1, y2) = [[int(x[0]), int(x[1])] for x in self.plot.getViewBox().viewRange()]
        
        if not (x1 == 0 and x2 == self._width and y1 == 0 and y2 == self._height):
            self.zoom_x1 = x1
            self.zoom_x2 = x2
            self.zoom_y1 = y1
            self.zoom_y2 = y2
        
        self.LBL_ROI_x1.setText("%d" % x1)
        self.LBL_ROI_x2.setText("%d" % x2)
        self.LBL_ROI_y1.setText("%d" % y1)
        self.LBL_ROI_y2.setText("%d" % y2)
        
        if self.BTN_draw_rect.isChecked():
            self.BTN_draw_rect.setChecked(False)

    def mouseClickedEvent(self, event):
        scene_coords = event.scenePos()
        if self.plot.sceneBoundingRect().contains(scene_coords):
            mouse_point = self.plot.vb.mapSceneToView(scene_coords)

            x = int(mouse_point.x())
            y = int(mouse_point.y())
            if x >= 0 and x <= self._width:
                if y >= 0 and y <= self._height:
                    QtWidgets.QToolTip.showText(QtGui.QCursor().pos(), "x: {}\ny: {}\ncount: {}".format(x, y, self._plot_im[y][x]))

    def ChangeExposureTime(self):
        exp_time = float(self.STATUS_exp_time.text())
        self.cam.toWorkList(["C", "EXPT", [exp_time]])
        
    def _timedOutUpdateTimer(self):
        if self._update_enable_flag:
            self.updatePlot()
            self._update_enable_flag = False
        if self.BTN_acquisition.isChecked():
            self.update_timer.start(self._update_interval)
        
    def _countPlot(self, raw_min, raw_max):
        self._img_cnt += 1
        self.raw_min, self.raw_max = raw_min, raw_max
        self._update_enable_flag = True
        
        if self.CBOX_single_scan.isChecked():
            if self._img_cnt == int(self.LBL_scan_length.text()):
                self._enableObjects(False)
                self.BTN_acquisition.setChecked(False)
                if self.CBOX_Autosave.isChecked():
                    self.SaveImage()
                
    def updatePlot(self):
        if (not self.isHidden() and not self.isMinimized()):
            if self.CBOX_auto.isChecked():
                self.im_min, self.im_max = self.raw_min, self.raw_max
                self.LBL_min.setText(str(self.im_min))
                self.LBL_max.setText(str(self.im_max))
                
            self.STATUS_raw_min.setText(str(self.raw_min))
            self.STATUS_raw_max.setText(str(self.raw_max))
            
            self.colorbar.setLevels( (self.im_min, self.im_max) )
            self._plot_im = self.image_handler.image_buffer
            
            self.im.setImage(self._plot_im, autoLevels=False)
            
            QtWidgets.QApplication.processEvents()
                            
    #%% for EMCCD
    def CoolingOn(self):
        target_temp = int(self.LBL_temp.text())
        if target_temp < 30:
            self.cam.cooler_on(target_temp)
            if not self._cooler_thread.isRunning():
                self._cooler_thread.running_flag = True
                self._cooler_thread.start()
            print("Cooler on.")
                
        else:
            self.cam.cooler_off()
            self._cooler_thread.running_flag = False
            self._cooler_thread.wait()
            print("Cooler off.")
            self.LBL_temp.setStyleSheet(self._theme_color[self._theme]["LBL"])
            
            
        
class Cooling_Thread(QThread):
    
    def __init__(self, parent):
        super().__init__()
        self.GUI = parent
        self.cam = self.GUI.cam
        self.running_flag = False
        
    def run(self):
        while self.running_flag:
            if self.cam._cool_status == "cooling":
                self.GUI.LBL_temp.setStyleSheet(self.GUI._emccd_cooler_theme[self.GUI._theme]["red"])
            elif self.cam._cool_status == "stabilized":
                self.GUI.LBL_temp.setStyleSheet(self.GUI._emccd_cooler_theme[self.GUI._theme]["blue"])
                
            self.GUI.LBL_temp.setText(str(self.cam.temperature))
            time.sleep(3)
            if not self.GUI.BTN_acquisition.isChecked():
                self.GUI.update()
                
  
    
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    CCD = CCD_UI(instance_name='QuIQCL_CCD_v2.02')
    CCD.setWindowTitle('QuIQCL_CCD_v2.02')
    CCD.show()

#CCD.cam._thor_cam.set_trigger_count(10)
#CCD.cam._buffer_size = 10