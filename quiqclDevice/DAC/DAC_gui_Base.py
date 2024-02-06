# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 11:27:37 2021

@author: QCP32
"""
class DAC_GuiBase():
    
    _num_ch = 16
    _num_axes = 5
    
    dc_textbox_list  = []
    dc_offset_list   = []
    sft_textbox_list = []
    sft_offset_list  = []
    sft_scroll_list = []
        
    _sft_dict = {0: "sym", 1: "asym", 2: "x", 3: "y", 4: "z"}
    _sft_values = {"sym":  [0]*14 + [0.04,  0.04],
                   "asym": [0]*14 + [0.04, -0.04],
                   "x":    [0.05]*6 + [0] + [-0.05]*6 + [0] + [0, 0],
                   "y":    [0.05]*2 + [-0.09]*2 + [-0.05]*2 + [0] + [0.05]*2 + [-0.09]*2 + [-0.05]*2 + [0] + [0, 0],
                   "z":    [0.04]*2 + [0]*2 + [-0.04]*2 + [0] + [0.04]*2 + [0]*2 + [-0.04]*2 + [0] + [0, 0]}
    
    _prev_sft_values = [0]*5
    
    _slider_changed = True
    
    _theme = "black"
    _theme_list = ["white", "black"]
    _theme_color = {
                    "white": {"main": """
                                      QWidget{
                                            background-color:rgb(255,255,255);
                                            selection-background-color:rgb(130,150,200);
                                            pressed-background-color:rgb(130,150,200);
                                            }""",
                              "title":    "background-color:rgb(100, 100, 100);\n color:rgb(255, 255, 255);",
                              "text_box": "border:1px solid rgb(0, 0, 0);",
                              "elec_d":   "background-color:rgb(9, 0, 144);\nborder-style: outset;\nborder-width:1px;",
                              "elec_i":   "background-color:rgb(7, 109, 0);\nborder-style: outset;\nborder-width:1px;",
                              "button":   """
                                      QPushButton {
                                                   background-color: rgb(180, 180, 180);
                                                   border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                                  }
                                      QPushButton::pressed {
                                                           background-color: rgb(145, 168, 210);
                                                           color: rgb(255, 255, 255);
                                                           border-style: outset; border-top: 2px solid; border-left: 2px solid;
                                                           }
                                      QPushButton::checked {
                                                           background-color: rgb(145, 168, 210);
                                                           color: rgb(255, 255, 255);
                                                           border-style: outset; border-top: 2px solid; border-left: 2px solid;
                                                           }
                                      QPushButton::hover {
                                                        background-color: rgb(145, 168, 210);
                                                        color: rgb(255, 255, 255);
                                                        border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                                        }
                                       """,
                              "edit_not_finished": "border:1px solid rgb(0, 0, 0); background-color:rgb(255, 240, 0);"
                              },
                    
                    "black": {"main": """
                                      QWidget{
                                            background-color:rgb(30,30,30);
                                            selection-background-color:rgb(240,180,60);
                                            pressed-background-color:rgb(240,180,60);
                                            color:rgb(255,255,255);
                                            gridline-color:rgb(120,120,120);
                                            }""",
                              "title":    "background-color:rgb(200, 200, 200);\n color:rgb(5, 5, 5);",
                              "text_box": "background-color:rgb(60, 60, 60); border:1px solid gray;",
                              "elec_d":   "background-color:rgb(49, 40, 204);\nborder-style: outset;\nborder-width:1px;",
                              "elec_i":   "background-color:rgb(7, 109, 0);\nborder-style: outset;\nborder-width:1px;",
                              "button":   """
                                      QPushButton {
                                                  background-color: rgb(60, 60, 60);
                                                  border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                                  }
                                      QPushButton::pressed {
                                                           background-color: rgb(200, 95, 10);
                                                           color: rgb(180, 180, 180);
                                                           border-style: outset; border-top: 3px solid; border-left: 3px solid;
                                                           }
                                      QPushButton::checked {
                                                           background-color: rgb(200, 95, 10);
                                                           color: rgb(180, 180, 180);
                                                           border-style: outset; border-top: 3px solid; border-left: 3px solid;
                                                           }
                                      QPushButton::hover {
                                                        background-color: rgb(200, 95, 10);
                                                        color: rgb(180, 180, 180);
                                                        border-style: outset; border-bottom: 1px solid; border-right: 1px solid;
                                                        }""",
                              "edit_not_finished": "border:1px solid gray; background-color:rgb(210, 160, 0);"
                              }
        }
            
    def changeTheme(self, theme):
        self._theme = theme
        self.setStyleSheet(self._theme_color[self._theme]["main"])
        self.LBL_PC_name.setStyleSheet(self._theme_color[self._theme]["title"])
        item_list = dir(self)
        for item in item_list:
            if "_Textbox_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["text_box"])
            elif "Layout_D" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["elec_d"])
            elif "Layout_I" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["elec_i"])
            elif "BTN_" in item:
                getattr(self, item).setStyleSheet(self._theme_color[self._theme]["button"])