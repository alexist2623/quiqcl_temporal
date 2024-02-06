# -*- coding: utf-8 -*-
"""
Created on Sat Jul  1 14:05:33 2023

@author: Hyrax326
"""

import os
filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets
from QSliderSlow_v1 import QSliderSlow
main_ui_file = dirname + "/test.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

class MainWindow(QtWidgets.QWidget, main_ui):
    
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.setupUi(self)
        self.my_slb = QSliderSlow(self.SLB_test, self.printValue)
        
        self.SLB_test.sliderPressed.connect(self.my_slb._pressedEvent)
        
    def printValue(self, idx):
        print(self.SLB_test.isPressed)
        # self.LE_test.setText("%d" % self.SLB_test.value())
        
        
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    test = MainWindow()
    test.show()