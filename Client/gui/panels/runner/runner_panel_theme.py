# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 17:55:59 2021

@author: QCP32
"""
class runner_panel_theme_base():
    
    _themes = ["black", "white"]
    _theme = "white"
                                     
    _mainwindow_stylesheet = {"white": """
                                      QWidget{
                                             background-color:rgb(255,255,255);
                                             selection-background-color:rgb(130,150,200);
                                             gridline-color:rgb(120,120,120);
                                             color:rgb(0,0,0);
                                             }
                                     QHeaderView{background-color:rgb(210,210,210);}
                                     QHeaderView::section{background-color:rgb(210,210,210);}
                                     QHeaderView::section::checked{background-color:rgb(130,150,200);color:rgb(255,255,255);}
                                     QTableCornerButton::section{background-color:rgb(255,255,255);}
                                     QComboBox{background-color:rgb(210,210,210);}
                                     QPushButton{background-color:rgb(255,255,255);}
                                     """,
                              "black": """
                                      QWidget{
                                             background-color:rgb(40,40,40);
                                             selection-background-color:rgb(240,180,60);
                                             color:rgb(180,180,180);
                                             gridline-color:rgb(120,120,120);
                                             }
                                     QHeaderView{background-color:rgb(40,40,40);}
                                     QHeaderView::section{background-color:rgb(80,80,80);}
                                     QHeaderView::section::checked{background-color:rgb(210,120,20);color:rgb(255,255,255);}
                                     QTableCornerButton::section{background-color:rgb(80,80,80);}
                                      """}
    
    _pushbutton_stylesheet = {"white": """
                                      QPushButton {
                                                   border-radius: 5px; background-color: rgb(180, 180, 180);
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
                                                  border-radius: 5px; background-color: rgb(120, 120, 120);
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
    
    _combobox_stylesheet = {"white": "",
                            "black": """
                                    QWidget{
                                             background-color:rgb(80,80,80);
                                             selection-background-color:rgb(210,120,20);
                                             color:rgb(180,180,180);
                                             }
                                    QComboBox{
                                            color: rgb(180, 180, 180);
                                            background-color: rgb(80, 80, 80);
                                            selection-background-color: rgb(160, 80, 10);
                                            }
                                    QComboBox::hover{
                                                    background-color:rgb(160, 80, 10);
                                                    color:rgb(180, 180, 180);
                                                    }
                                    """}
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
                                   
    _checkbox_stylesheet = {"white":"",
                           "black": """
                                   QCheckBox::indicator::unchecked:hover{ border: 1px solid orange; background-color:white;}
                                   QCheckBox::indicator::checked:hover{ border: 1px solid dark-gray; background-color:orange;}
                                   """}
                                   
    
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
            elif "CBOX_" in item:
                getattr(self, item).setStyleSheet(self._combobox_stylesheet[self._theme])
            elif "CHBOX_" in item:
                getattr(self, item).setStyleSheet(self._checkbox_stylesheet[self._theme])                



