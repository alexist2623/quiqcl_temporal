# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 17:07:33 2024

@author: alexi
"""
import json
import argparse
import sypico
import importlib

class QQQServer:
    def __init__(self, **kwargs):
        self.ip : str = "0.0.0.0"
        for key, value in kwargs.items():
            setattr(self, key, value)
    
def CreateQQQServer(json_file) -> QQQServer:
    with open(json_file, 'r') as file:
        data = json.load(file)
    qs = QQQServer(**data['server'])
    for device_name, device_data in data.get('device', {}).items():
        module = importlib.import_module(device_data.get('import'))
        class_object = getattr(module,device_data.get('class'))(**device_data.get('args'))
        class_object.name = device_name
        setattr(qs,device_name,class_object)
    
    return qs

def main(args):
    configuration = args.config if args.config else 'configuration.json'
    qs = CreateQQQServer(configuration)
    qs.hellodevice.say()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make QQQServer class based on\
                                     configuration file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-c", "--config", help="Configuration file name")
    args = parser.parse_args()
    main(args)
