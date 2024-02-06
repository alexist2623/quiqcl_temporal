# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 17:55:59 2021

@author: QCP32
"""
class main_panel_theme_base():
    
    _themes = ["black", "white"]
    _theme = "white"
                                     
    _mainwindow_stylesheet = {"white": "background-color:rgb(255, 255, 255)",
                              "black": "background-color:rgb(40, 40, 40); color:rgb(180, 180, 180)"}
    
    _pushbutton_stylesheet = {"white": """
                                      QPushButton {
                                                   border-radius: 5px; background-color: rgb(120, 120, 120);
                                                   color: rgb(255, 255, 255);
                                                   border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
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
                                       """,
                              "black": """                              
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
                                       """}
                                       
    _label_stylesheet = {"white": "background-color:rgb(210, 210, 210); color:rgb(0, 0, 0); border:none;",
                         "black": "background-color:rgb(0, 0, 0); color:rgb(180, 180, 180); border:none;"}
                                       
    _groupbox_stylesheet = {"white": "background-color:rgb(255, 255, 255); color:rgb(0, 0, 0)",
                            "black": "background-color:rgb(0, 0, 0); color:rgb(180, 180, 180)"}
    
    _slider_stylesheet = {"white": """
                                   QSlider::handle:horizontal {
                                            background:rgb(145, 168, 210);
                                            width: 12px;
                                            height: 6px;
                                            border-radius: 2px;
                                            }
                                   """,
                          "black": """
                                   QSlider::handle:horizontal {
                                            background:rgb(200, 95, 10);
                                            width: 12px;
                                            height: 6px;
                                            border-radius: 2px;
                                            }
                                   """}
    _electrode_stylesheet = {"white": "background:rgb(145, 168, 210); border: 1px solid rgb(40, 80, 180);",
                            "black": "background:rgb(200, 95, 10); border: 1px solid rgb(255,180,60);"}
    _electrode_laybel_stylesheet = {"white":"",
                                    "black": "background-color:rgb(40, 40, 40);border: 1px solid rgb(140,140,140);"}

    
    def changeTheme(self, theme):
        self._theme = theme
        self.setStyleSheet(self._mainwindow_stylesheet[self._theme])
        item_list = dir(self)
        for item in item_list:
            if "BTN_" in item:
                getattr(self, item).setStyleSheet(self._pushbutton_stylesheet[self._theme])
            elif "TXT_" in item:
                getattr(self, item).setStyleSheet(self._label_stylesheet[self._theme])
            elif "SLD_" in item:
                getattr(self, item).setStyleSheet(self._slider_stylesheet[self._theme])
            elif "ELEC_dac" in item:
                getattr(self, item).setStyleSheet(self._electrode_stylesheet[self._theme])
            elif "ELEC_value_" in item:
                getattr(self, item).setStyleSheet(self._electrode_laybel_stylesheet[self._theme])