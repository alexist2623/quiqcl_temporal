# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 17:07:33 2024

@author: alexi
"""
import json
import argparse
import importlib
import sys
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn
from typing import List, Optional

app = FastAPI()
device_list : list[str] = [] 
clients: List[WebSocket] = []

class RPC_parameter(BaseModel):
    action: str
    name: str
    args: list
    kwargs: dict
    
class RPC_response(BaseModel):
    status : str
    name: str
    value: object
    
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    await websocket.send_text('OK')
    try:
        while True:
            # Keeping the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)
        
@app.post("/call/")
async def function_call(item: RPC_parameter) -> RPC_response:
    object_name, method_name  = item.name.split('.')
    obj = globals()[object_name]
    method = getattr(obj, method_name)
    #Todo : check whether method_name is callable and key is right.
    #And make put function call into queue
    if hasattr(item, 'args') and item.args:
        if hasattr(item, 'kwargs') and item.kwargs:
            return_value = method(*item.args, **item.kwargs)
        else:
            return_value = method(*item.args)
    else:
        if hasattr(item, 'kwargs') and item.kwargs:
            return_value = method(**item.kwargs)
        else:
            return_value = method()
    notify(object_name)
    return RPC_response(status = "OK", 
                        name = object_name,
                        value = return_value)

def notify(object_name : str) -> None:
    data = globals()[object_name].get_changed_attributes()
    for client in clients:
        print(client)
        client.send_text(json.dumps(data))

@app.post("/get/")
async def get_value(item: RPC_parameter) -> RPC_response:
    pass

@app.post("/getallattr/")
async def get_all_value(item: RPC_parameter) -> RPC_response:
    object_name = item.name
    obj = globals()[object_name]
    return RPC_response(status = "OK", 
                    name = object_name,
                    value = vars(obj))

@app.post("/set/")
async def set_variable(item: RPC_parameter) -> RPC_response:
    object_name = item.name
    return RPC_response(status = "OK", 
                    name = object_name,
                    value = None)

class QQQServer:
    ip : str = "0.0.0.0"
    path : list[str] = []    
    port : int = 0
    def __init__(self):
        pass
    
    @classmethod
    def SetClassVars(cls, **kwargs):
        for key, value in kwargs.items():
            setattr(cls, key, value)
    
def CreateQQQServer(json_file : str) -> QQQServer:
    with open(json_file, 'r') as file:
        data = json.load(file)
    QQQServer.SetClassVars(**data['server'])
    for path in QQQServer.path:
        sys.path.append(path) 
    for device_name, device_data in data.get('device', {}).items():
        module = importlib.import_module(device_data.get('import'))
        class_object = getattr(module,device_data.get('class'))(**device_data.get('args'))
        if hasattr(device_data,'attr'):
            for key, value in device_data.get('attr').items():
                setattr(class_object, key, value)
        setDevice(device_name,class_object)    

def setDevice(device_name : str,
              class_object : object) -> None:
    setattr(class_object,'name', device_name)
    setattr(class_object,'_changed_attributes', set())
    globals()[device_name] = class_object
    class_object.get_changed_attributes()
    device_list.append(device_name)
    return
    
def getDevice(device_name : str) -> object:
    return globals()[device_name]

def main(args):
    configuration = args.config if args.config else 'configuration.json'
    CreateQQQServer(configuration)
    #Todo : change host to QQQServer.ip and port
    uvicorn.run(app, host = QQQServer.ip, port = QQQServer.port)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make QQQServer class based on\
                                     configuration file")
    parser.add_argument("-c", "--config", help="Configuration file name")
    args = parser.parse_args()
    main(args)
