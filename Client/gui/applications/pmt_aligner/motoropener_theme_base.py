# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 17:55:59 2021

@author: QCP32
"""
class MotorOpener_Theme_Base():
    
    _themes = ["black", "white"]
    _theme = "white"
    
    _mainwindow_stylesheet = {"white": "background-color:rgb(255, 255, 255)",
                              "black": "background-color:rgb(40, 40, 40); color:rgb(180, 180, 180)"}
                                   
    _progressbar_stylesheet_normal = {"white": """
                                                QProgressBar{border: 2px solid gray;
                                                             border-radius: 5px;
                                                             text-align: center;
                                                             background-color:rgb(255,255,255);
                                                             color:rgb(0,0,0);
                                                             }
                                                QProgressBar::chunk{background-color: lightblue;
                                                                    width: 10px;
                                                                    margin: 1px;}
                                                """,
                                      "black": """
                                                QProgressBar{border: 2px solid lightgray;
                                                             border-radius: 5px;
                                                             text-align: center;
                                                             background-color:rgb(40,40,40);
                                                             color:rgb(180,180,180);
                                                             }
                                                QProgressBar::chunk{background-color: orange;
                                                                    width: 10px;
                                                                    margin: 1px;}
                                        """}
    _progressbar_stylesheet_complete = {"white": """
                                                QProgressBar{border: 2px solid gray;
                                                             border-radius: 5px;
                                                             text-align: center;
                                                             background-color:rgb(255,255,255);
                                                             color:rgb(0,0,0);
                                                             }
                                                QProgressBar::chunk{background-color: lightgreen;
                                                                    width: 10px;
                                                                    margin: 1px;}
                                                """,
                                        "black": """
                                                  QProgressBar{border: 2px solid lightgray;
                                                               border-radius: 5px;
                                                               text-align: center;
                                                               background-color:rgb(40,40,40);
                                                               color:rgb(180,180,180);
                                                               }
                                                  QProgressBar::chunk{background-color: green;
                                                                      width: 10px;
                                                                      margin: 1px;}
                                          """}
                                          
    _progressbar_stylesheet_error = {"white": """
                                                QProgressBar{border: 2px solid gray;
                                                             border-radius: 5px;
                                                             text-align: center;
                                                             background-color:rgb(255,255,255);
                                                             color:rgb(0,0,0);
                                                             }
                                                QProgressBar::chunk{background-color: red;
                                                                    width: 10px;
                                                                    margin: 1px;}
                                                """,
                                        "black": """
                                                  QProgressBar{border: 2px solid lightgray;
                                                               border-radius: 5px;
                                                               text-align: center;
                                                               background-color:rgb(40,40,40);
                                                               color:rgb(180,180,180);
                                                               }
                                                  QProgressBar::chunk{background-color: rgb(190,15,20);
                                                                      width: 10px;
                                                                      margin: 1px;}
                                          """}
                                          
    def changeTheme(self, theme):
        self._theme = theme
        self.setStyleSheet(self._mainwindow_stylesheet[self._theme])
        item_list = dir(self)
        for item in item_list:
            if "PRGB" in item:
                getattr(self, item).setStyleSheet(self._progressbar_stylesheet_normal[self._theme])



