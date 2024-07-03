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

clients: list = []

class JsonRPCServer:
    host : str = None
    port_list : int = None
    device_list : dict[str : object] = {}
    thread_list : dict[int : threading.Thread] = {}
    
    def __init__(self):
        self.sockets : dict[socket] = {}
        self.conn : dict[int : object] = {}
        for port in self.port_list:
            self.sockets[port] = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            self.sockets[port].bind((self.host, port))
            self.sockets[port].listen()
            self.thread_list[port] = threading.Thread(target=self.listen, args=(port, ))
            self.thread_list[port].daemon = True
            self.thread_list[port].start()
            
        self._message_queue = queue.Queue()
    
    @classmethod
    def SetClassVars(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(cls, key, value)
                
    def listen(self, port : int) -> None:
        print(f">> Server host : {self.host}, port : {port} opened")
        while True:
            conn, addr = self.sockets[port].accept()
            self.conn[port] = conn
            print(f"Connection from {addr} on port {port}")
            while True:
                message = conn.recv(1024)
                json_data = json.loads(message.decode('utf-8'))
                self._message_queue.put(json_data)
            conn.close()
    
    def run(self):
        while True:
            if not self._message_queue.empty():
                message = self._message_queue.get()
                print(message)
                self.functionCall(message)
                    
    def functionCall(self, item: json) -> None:
        object_name = item["name"]
        method_name = item["method"]
        obj = self.device_list[object_name]
        method = getattr(obj, method_name)
        if item["params"]:
            return_value = method(obj, **item["params"])
        else:
            return_value = method(obj)
            
        self.notify(object_name)
        
        return
    
    def notify(self, object_name : str) -> None:
        data = self.device_list[object_name].get_changed_attributes()
        item = RPCResponse(
            result = data,
            name = object_name
        )
        for port, conn in self.conn.items():
            conn.sendall(item.encode('utf-8'))
    
def RPCResponse(
        result: object,
        name : str) -> json:
    
    item = {
        "result" : result,
        "name" : name
    }
    return json.dumps(item)

def getAllValue(item: json) -> json:
    object_name = item.name
    obj = globals()[object_name]
    return RPCResponse(
        name = object_name,
        result = vars(obj)
    )

def setVariable(item: json) -> json:
    object_name = item.name
    return RPCResponse(
        status = "OK", 
        name_value = object_name,
        value = None)

def CreateJsonRPCServer(json_file : str) -> JsonRPCServer:
    with open(json_file, 'r') as file:
        data = json.load(file)
    JsonRPCServer.SetClassVars(**data['server'])
    for path in JsonRPCServer.path:
        sys.path.append(path) 
    for device_name, device_data in data.get('device', {}).items():
        module = importlib.import_module(device_data.get('import'))
        class_object = getattr(module,device_data.get('class'))(**device_data.get('args'))
        if hasattr(device_data,'attr'):
            for key, value in device_data.get('attr').items():
                setattr(class_object, key, value)
        setDevice(device_name,class_object)   
    
    json_rpc_server = JsonRPCServer()
    return json_rpc_server
        
def getallattr(self):
    return {k: v for k, v in self.__dict__.items() if not callable(v)}

def setDevice(device_name : str,
              class_object : object) -> None:
    setattr(class_object,'name', device_name)
    setattr(class_object,'_changed_attributes', set())
    setattr(class_object,'getallattr',getallattr)
    JsonRPCServer.device_list[device_name] = class_object
    class_object.get_changed_attributes()
    
    return
    
def main(args):
    configuration = args.config if args.config else 'configuration.json'
    json_rpc_server = CreateJsonRPCServer(configuration)
    json_rpc_server.run()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Make JsonRPCServer class based on configuration file")
    )
    parser.add_argument("-c", "--config", help="Configuration file name")
    args = parser.parse_args()
    main(args)
