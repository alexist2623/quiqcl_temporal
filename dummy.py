# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 14:17:13 2024

@author: alexi
"""

class dummy_class:
    def __init__(self, name : str):
        self.a = 1
        print('hihihi' + name)
        
    def __setattr__(self, name, value):
        if (not name == '_changed_attributes') and (not name == '_notify_vars'):
            if not hasattr(self, "_changed_attributes"):
                self._changed_attributes = set()
            if not hasattr(self, "_notify_vars"):
                self._notify_vars = []
            if name in self._notify_vars:
                self._changed_attributes.add(name)
        super().__setattr__(name, value)
    
    def getChangedAttributes(self):
        changed_attributes = list(self._changed_attributes)
        self._changed_attributes = set()
        return changed_attributes

    def do_print(self, var : str) -> None:
        print(var)
        self.a = self.a + 1
        print(self.a)
        
    def hello(self):
        self.frequency = self.frequency + 1
        self.a = 30
        print("hello")