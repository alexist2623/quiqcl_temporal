# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 11:53:41 2022

@author: QCP32
"""

class WaveMeter_Theme_Base():
    
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
                                     QTableView::item{align:center;}
                                      """}
                                      
    _menubar_stylesheet = {"white": """
                                QMenuBar{background-color: rgb(180, 180, 180); color: rgb(0, 0, 0);}
                                """,
                       "black": """
                                QMenuBar{background-color: rgb(70, 70, 70); color: rgb(180, 180, 180);}
                                QMenuBar::item{background-color: rgb(70, 70, 70); color: rgb(180, 180, 180);}
                                QMenuBar::item::selected{background-color: rgb(200, 95, 10); color: rgb(180, 180, 180);}
                                QMenu::item::selected{background-color: rgb(200, 95, 10); color: rgb(180, 180, 180);}
                                 """
                                 }
    
    _statusbar_stylesheet = {"white": "",
                              "black": "background-color:rgb(40, 40, 40); color:rgb(180, 180, 180)"}

    _tabbar_stylesheet = {"white": "",
                          "black": """ 
                                    QTabBar {border-radus:5px;}
                                    QTabBar::tab:selected {background:rgb(70, 70, 70); color:rgb(180, 180, 180);}
                                    QTabBar::tab{background:rgb(70, 70, 70); color:rgb(180, 180, 180);}
                                    QTabWidget::pane { border: 0; }
                                    QTabWidget>QWidget>QWidget{background:rgb(80, 80, 80);}
                                    """
                                    }
    
    _pushbutton_stylesheet = {"white": """
                                      QPushButton {
                                                   border-radius: 5px; background-color: rgb(140, 140, 140);
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
    _textbrowser_stylesheet = {"white": "background-color:rgb(210, 210, 210); border:0px;",
                               "black": "background-color:rgb(0, 0, 0); border:1px solid rgb(180, 180, 180);"}
                                       
                                       
    _lineedit_stylesheet = {"white": "background-color:rgb(210, 210, 210); color:rgb(0, 0, 0); border-color:rgb(0, 0, 0); border:1px solid;",
                           "black": "background-color:rgb(0, 0, 0); color:rgb(180, 180, 180); border-color:rgb(180, 180, 180);border:1px solid;"}
                                       
    _groupbox_stylesheet = {"white": "background-color:rgb(255, 255, 255); color:rgb(0, 0, 0)",
                            "black": "background-color:rgb(40, 40, 40); color:rgb(180, 180, 180)"}
    
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
    _slider_stylesheet = {"white": "background-color:rgb(210, 210, 210);",
                          "black": """
                                   """}
                                   
    _checkbox_stylesheet = {"white":"",
                           "black": """
                                   QCheckBox::indicator::unchecked:hover{ border: 1px solid orange; background-color:white;}
                                   QCheckBox::indicator::checked:hover{ border: 1px solid dark-gray; background-color:orange;}
                                   """}
                                   
    
    def changeTheme(self, theme):
        self._theme = theme
        self.setStyleSheet(self._mainwindow_stylesheet[self._theme])
        self.statusbar.setStyleSheet(self._statusbar_stylesheet[self._theme])
        self.menubar.setStyleSheet(self._menubar_stylesheet[self._theme])
        item_list = dir(self)
        for item in item_list:
            item_object= getattr(self, item)
            if "QPushButton" in str(item_object.__class__):
                item_object.setStyleSheet(self._pushbutton_stylesheet[self._theme])
            elif "QTextBrowser" in str(item_object.__class__):
                item_object.setStyleSheet(self._textbrowser_stylesheet[self._theme])
            elif "QLineEdit" in str(item_object.__class__):
                item_object.setStyleSheet(self._lineedit_stylesheet[self._theme])
            elif "QScrollBar" in str(item_object.__class__):
                 item_object.setStyleSheet(self._slider_stylesheet[self._theme])
            elif "QComboBox" in str(item_object.__class__):
                item_object.setStyleSheet(self._combobox_stylesheet[self._theme])
            elif "QCheckBox" in str(item_object.__class__):
                item_object.setStyleSheet(self._checkbox_stylesheet[self._theme])
            elif "QGroupBox" in str(item_object.__class__):
                item_object.setStyleSheet(self._groupbox_stylesheet[self._theme])



