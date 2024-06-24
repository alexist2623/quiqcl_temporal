# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:58:01 2024

@author: alexi
"""

import requests
import asyncio
import websockets
import json
import time

class QQQClient:
    _url = "http://127.0.0.1:8000"
    def __init__(self):
        pass
    
    def __getattr__(self, name):
        def proxy(*args, **kwargs):
            return self.__do_rpc(findVariableName(self) + '.' + name, 
                                 "call", args, kwargs)
        return proxy

    def __do_rpc(self, 
                 name : str, 
                 action : str, 
                 args : list, 
                 kwargs : dict):
        item = {
               "action": action, 
               "name": name,
               "args": [] if args == None else args,
               "kwargs" : {} if kwargs == None else kwargs
               }
            
        return requests.post(QQQClient._url+f'/{action}/', json=item)
    
    def _get_all_attr(self) -> None:
        attr_dict = self.__do_rpc(findVariableName(self), 
                                  "getallattr", None, None).json().get('value')
        for _name, _value in attr_dict.items():
            setattr(self,_name,_value)
    
def findVariableName(obj):
    for name, value in globals().items():
        if value is obj:
            return name
    return None

async def listen(connection_future):
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        connection_future.set_result(True)
        while True:
            message = await websocket.recv()
            # data = json.loads(message)  # Deserialize JSON data
            print(f"Received from server: {message}")

def openWebSocket():
    connection_future = asyncio.Future()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    task = loop.create_task(listen(connection_future))
    if not loop.is_running():
        loop.run_until_complete(task)

if __name__ == '__main__':
    openWebSocket()
    ad9912_0 = QQQClient()
    ad9912_0._get_all_attr()
    ad9912_0.do_print('hi')
    print(ad9912_0.name)
