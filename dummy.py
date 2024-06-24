# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 14:17:13 2024

@author: alexi
"""

class dummy_class:
    def __init__(self, name : str):
        self._changed_attributes = set()
        self.a = 1
        print('hihihi' + name)
        
    def do_print(self, var : str) -> None:
        print(var)
        self.a = self.a + 1
        print(self.a)

    def __setattr__(self, name, value):
        if not name == '_changed_attributes':
            self._changed_attributes.add(name)
        super().__setattr__(name, value)
        
    def get_changed_attributes(self):
        changed_attributes = list(self._changed_attributes)
        self._changed_attributes = set()
        return changed_attributes