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
        self.LBL_status.setText("Status:")

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

    
            

if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    pb = ProgressBar()
    pb.show()