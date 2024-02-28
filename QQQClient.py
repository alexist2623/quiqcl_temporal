# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:58:01 2024

@author: alexi
"""

import requests

class QQQClient:
    __key = 0000
    __url = "http://127.0.0.1:8000"
    def __init__(self):
        pass
    
    def __getattr__(self, name):
        def proxy(*args, **kwargs):
            return self.__do_rpc(findVariableName(self) + '.' + name, "call", args, kwargs)
        return proxy

    def __do_rpc(self, 
                 name : str, 
                 action : str, 
                 args : list, 
                 kwargs : dict):
        item = {
               "key": QQQClient.__key,
               "action": action, 
               "name": name, 
               "args": args, 
               "kwargs": kwargs}
        return requests.post(QQQClient.__url+f'/{action}/', json=item)
    
def findVariableName(obj):
    for name, value in globals().items():
        if value is obj:
            return name
    return None

if __name__ == '__main__':
    ad9912_0 = QQQClient()
    ad9912_0.do_print('hi')