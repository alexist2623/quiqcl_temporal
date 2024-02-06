# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 11:04:18 2021

@author: QCP32
"""

class experimenter_theme_base():
    
    _themes = ["black", "white"]
    _theme = "white"
                                     
    _mainwindow_stylesheet = {"white": "background-color:rgb(255, 255, 255)",
                              "black": "background-color:rgb(80, 80, 80); color:rgb(180, 180, 180); QTabWidget {background-color:rgb(40, 40, 40);}"}
                              
    _tabbar_main_stylesheet = {"white": "background-color:rgb(255, 255, 255)",
                              "black": "background-color:rgb(40, 40, 40); color:rgb(180, 180, 180)"}
                          
    _tabbar_stylesheet = {"white": "",
                          "black": """ 
                                    QTabWidget {background-color:rgb(40, 40, 40);}
                                    QTabBar {border-radius:5px;background:rgb(40, 40, 40)}
                                    QTabBar::tab:selected {background:rgb(40, 40, 40); color:rgb(180, 180, 180);}
                                    QTabBar::tab:hover {background:rgb(180, 90, 8); color:rgb(180, 180, 180);}
                                    QTabBar::tab{background:rgb(40, 40, 40); color:rgb(180, 180, 180);}
                                    QTabWidget::pane { border: 0; }
                                    QTabWidget>QWidget>QWidget{background:rgb(40, 40, 40);}
                                    """
                                    }
                              
                              
    _theme_base = {"white": """
                          QWidget{
                                 background-color:rgb(240,240,240);
                                 selection-background-color:rgb(130,150,200);
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
                         QFrame {background-color:rgb(255,255,255); border: 0px;}

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
                                 background-color:rgb(80,80,80);
                                 selection-background-color:rgb(240,180,60);
                                 color:rgb(180,180,180);
                                 gridline-color:rgb(120,120,120);
                                 } 
                         QTabWidget {background-color:rgb(40, 40, 40);}
                         QTabBar {border-radius:5px;background:rgb(40, 40, 40)}
                         QTabBar::tab:selected {background:rgb(40, 40, 40); color:rgb(180, 180, 180);}
                         QTabBar::tab:hover {background:rgb(180, 90, 8); color:rgb(180, 180, 180);}
                         QTabBar::tab{background:rgb(40, 40, 40); color:rgb(180, 180, 180);}
                         QTabWidget::pane { border: 0; }
                         QTabWidget>QWidget{background:rgb(40, 40, 40);}
                         QFrame {background-color:rgb(40,40,40); border: 0px;}
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
        self.setStyleSheet(self._theme_base[self._theme])
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
                           
        #self.tabWidget.setStyleSheet(self._theme_base[self._theme])
        #for tab in self.tab_dict.values():
        #    tab.setStyleSheet(self._theme_base[self._theme])