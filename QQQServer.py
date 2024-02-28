# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 17:07:33 2024

@author: alexi
"""
import json
import argparse
import importlib
import sys
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()
device_list : list[str] = [] 

class RPC_parameter(BaseModel):
    key : int
    action: str
    name: str
    args: list
    kwargs: dict

@app.post("/call/")
async def function_call(item: RPC_parameter) -> RPC_parameter:
    object_name, method_name  = item.name.split('.')
    obj = globals()[object_name]
    method = getattr(obj, method_name)
    if hasattr(item, 'args') and item.args != None:
        if hasattr(item, 'kwargs') and item.kwargs != None:
            return_value = method(*item.args, **item.kwargs)
        else:
            return_value = method(*item.args)
    else:
        if hasattr(item, 'kwargs') and item.kwargs != None:
            return_value = method(**item.kwargs)
        else:
            return_value = method()
        
    return item

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
    globals()[device_name] = class_object
    setattr(class_object,'name', device_name)
    device_list.append(device_name)
    return
    
def getDevice(device_name : str) -> object:
    return globals()[device_name]

def main(args):
    configuration = args.config if args.config else 'configuration.json'
    CreateQQQServer(configuration)
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make QQQServer class based on\
                                     configuration file")
    parser.add_argument("-c", "--config", help="Configuration file name")
    args = parser.parse_args()
    main(args)
