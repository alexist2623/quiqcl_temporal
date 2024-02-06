# -*- coding: utf-8 -*-
"""
Created on Wed Nov  3 09:37:54 2021

@author: QCP32
"""
import os
version = "1.1"

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets
from progress_bar_theme import progress_bar_theme_base
main_ui_file = dirname + "/progressbar.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

class ProgressBar(QtWidgets.QWidget, main_ui, progress_bar_theme_base):
    
    def __init__(self, parent=None, theme="black"):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        self._theme = theme
        
    def resetProgressBar(self):
        self.PRGB_status.setValue(0)
        self.setProgressbarStylesheet("normal")
        self.LBL_status.setText("Standby")
        
    def iterationDone(self, curr_idx, max_idx):
        if not self.parent.sweep_run_flag:
            if self.parent.user_run_flag:
                self.changeProgressBar(curr_idx, max_idx)
                time_str = self._calculateTime(self.parent.sequencer.iter_start_time, self.parent.sequencer.iter_end_time)
                self.changeLabelText("Running (%d/%d)...[%s per iter.]" % (curr_idx, max_idx, time_str))
             
    def runDone(self, flag):
        if not self.parent.sweep_run_flag:
            if self.parent.user_run_flag:
                self.completeProgressBar(flag)
                if flag:
                    time_str = self._calculateTime(self.parent.sequencer.start_time, self.parent.sequencer.end_time)
                    self.changeLabelText("Completed. Total running time: (%s)" % time_str)
                else:
                    self.changeLabelText("Stopped running.")

        
    def changeProgressBar(self, curr_idx, max_idx):
        percentage = int(curr_idx*100/max_idx)
        self.setProgressbarStylesheet("normal")
        self.PRGB_status.setValue(percentage)
        

    def changeLabelText(self, text):
        self.LBL_status.setText(text)
        
    
    def completeProgressBar(self, flag): # True: completed, False: borken
        if flag:
            self.PRGB_status.setValue(100)            
            self.setProgressbarStylesheet("complete")
        else:
            self.setProgressbarStylesheet("error")
            
            
    def setProgressbarStylesheet(self, status):
        if status == "normal":
            self.PRGB_status.setStyleSheet(self._progressbar_stylesheet_normal[self._theme])
            
        elif status == "complete":
            self.PRGB_status.setStyleSheet(self._progressbar_stylesheet_complete[self._theme])
            
        elif status == "error":
            self.PRGB_status.setStyleSheet(self._progressbar_stylesheet_error[self._theme])
        
    def _calculateTime(self, start_time, end_time):
        delta = end_time - start_time
        
        if delta.seconds > 3600:
            return str(delta)[:7]
        if delta.seconds > 60:
            return str(delta)[2:7]
        if delta.seconds > 1:
            return ("%d s" % delta.seconds)
        else:
            return ("less than 1s")
            
            
            

if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    pb = ProgressBar()
    pb.show()