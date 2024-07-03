# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 17:07:33 2024

@author: alexi
"""
import json
import argparse
import sys
import socket
import importlib
import threading
import queue

device_list : list[str] = [] 
clients: list = []


class JsonRPCServer:
    host : str = None
    port : int = None
    def __init__(self, host : str = "0.0.0.0", port : int = 0):
        self.host = host
        self.port = port
        self.socket : socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
    
    @classmethod
    def SetClassVars(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(cls, key, value)
                
    def listen(self):
        while True:
            self.socket.listen()

                    
def functionCall(item: json) -> json:
    object_id, method_id  = item.id.split('.')
    obj = globals()[object_id]
    method = getattr(obj, method_id)
    if hasattr(item, 'kwargs') and item.kwargs:
        return_value = method(**item.kwargs)
    else:
        return_value = method()
    notify(object_id)
    return RPC_response(
        status = "OK", 
        id = object_id,
        value = return_value
    )


def notify(object_id : str) -> None:
    data = globals()[object_id].get_changed_attributes()
    for client in clients:
        print(client)
        client.send_text(json.dumps(data))
    
def RPC_response(
    status : str,
    id_value: str,
    value: object) -> json:
    
    item = {
        "status" : status,
        "id": id_value,
        "value": {
            "value" : value,
            "type" : str(type(value))
        }
    }
    return item

def getAllValue(item: json) -> json:
    object_id = item.id
    obj = globals()[object_id]
    return RPC_response(
        status = "OK", 
        id = object_id,
        value = vars(obj))

def setVariable(item: json) -> json:
    object_id = item.id
    return RPC_response(
        status = "OK", 
        id_value = object_id,
        value = None)

def CreateJsonRPCServer(json_file : str) -> JsonRPCServer:
    with open(json_file, 'r') as file:
        data = json.load(file)
    JsonRPCServer.SetClassVars(**data['server'])
    for path in JsonRPCServer.path:
        sys.path.append(path) 
    for device_id, device_data in data.get('device', {}).items():
        module = importlib.import_module(device_data.get('import'))
        class_object = getattr(module,device_data.get('class'))(**device_data.get('args'))
        if hasattr(device_data,'attr'):
            for key, value in device_data.get('attr').items():
                setattr(class_object, key, value)
        setDevice(device_id,class_object)    
        

def setDevice(device_id : str,
              class_object : object) -> None:
    setattr(class_object,'id', device_id)
    setattr(class_object,'_changed_attributes', set())
    globals()[device_id] = class_object
    class_object.get_changed_attributes()
    device_list.append(device_id)
    return
    
def getDevice(device_id : str) -> object:
    return globals()[device_id]

def main(args):
    configuration = args.config if args.config else 'configuration.json'
    CreateJsonRPCServer(configuration)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Make JsonRPCServer class based on configuration file")
    )
    parser.add_argument("-c", "--config", help="Configuration file name")
    args = parser.parse_args()
    main(args)
