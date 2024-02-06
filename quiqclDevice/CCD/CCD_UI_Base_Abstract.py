# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 18:48:04 2023

@author: QCP75
"""

class CCD_UI_base:
    
    _img_cnt = 0
    
    _camera_type = "CCD"
    
    _slider_min = 0
    _slider_max = 0
    
    _im_min = 19
    _im_max = 216
    
    _zoom_in_flag = False
    _auto_save = False
    _slow_mode = False
    
    _update_interval = 50 # ms
    _update_enable_flag = False
    
    _theme = "white"    
    _theme_color = {
                    "white": {"main":   "",
                              "GBOX":   "",
                              "BTN":"""
                                      QPushButton{
                                                border-radius: 5px ;background-color: rgb(140, 140, 140); 
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
                              """,
                              "LBL":    "background-color:rgb(180, 180, 180);",
                              "STATUS": "background-color:rgb(10, 10, 10); color:rgb(255, 255, 255);",
                              "TXT": "background-color:rgb(240, 240, 240); color:rgb(0, 0, 0);",
                              
                              "fig_face_color": "w",
                              "ax_face_color": "w",
                              "tick_color": "k",
                              "color_map": "gist_earth"
                              },
                    
                    "black": {"main":   "background-color:rgb(30,30,30); color:rgb(140, 140, 140);",
                              "GBOX":   "color:rgb(140, 140, 140);",
                              "BTN":"""
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
                              """,
                              "LBL":    "background-color:rgb(0, 0, 0);",
                              "STATUS": "background-color:rgb(180, 180, 180); color:rgb(10, 10, 10);",
                              "TXT": "background-color:rgb(30,30,30); color:rgb(140, 140, 140);",
                              
                              "fig_face_color": [0.235, 0.235, 0.235],
                              "ax_face_color": [0.118, 0.118, 0.118],
                              "tick_color": [0.7, 0.7, 0.7],
                              "color_map": "afmhot"
                              }
        }
    
    _emccd_cooler_theme = {
                            "white": {"blue": "background-color:rgb(65, 150, 80)",
                                      "red": "background-color:rgb(150, 60, 140)"
                                      },
                            "black": {"blue": "background-color:rgb(0, 100, 20)",
                                      "red": "background-color:rgb(120, 40, 120)"
                                      }
        }
    
    
    _available_ccd = []