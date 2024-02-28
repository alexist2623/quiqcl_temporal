# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 14:17:13 2024

@author: alexi
"""

class dummy_class:
    def __init__(self, name : str):
        self.a = 1
        print('hihihi' + name)
        
    def do_print(self, var : str) -> None:
        print(var)
        self.a = self.a + 1
        print(self.a)