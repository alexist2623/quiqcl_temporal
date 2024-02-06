# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 13:45:52 2022

@author: QCP32
"""

import os, sys
filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget


main_ui_file = dirname + "/mini_wavemeter_blank.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

sys.path.append(dirname + "/../")
from measure_panel_theme import measure_panel_theme_base

class Mini_WaveMeter_Blank(QWidget, main_ui, measure_panel_theme_base):
    
    def __init__(self, theme="black"):
        super().__init__()
        
        self._theme = theme
        self.setupUi(self)


if __name__ == "__main__":
    mini_wm = Mini_WaveMeter_Blank()
    mini_wm.show()
    