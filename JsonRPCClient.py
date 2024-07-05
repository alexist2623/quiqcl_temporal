# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:58:01 2024

@author: alexi
"""

import json
import socket
import queue
import sys
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5 import QtWidgets, uic

DEBUG = 0

class TCPSendHandler(QThread):
    
    def __init__(self, parent, client_socket):
        super().__init__(parent)
        self.client_socket = client_socket
        self._msg_queue = queue.Queue()
        self.parent = parent
            
    def run(self):
        while True:
            if not self._msg_queue.empty():
                self.sendMessage(self._msg_queue.get())
    
    def addRPCQueue(self, item : json = None) -> None:
        self._msg_queue.put(item)
        
    def sendMessage(self, item : json = None) -> None:
        if not DEBUG:
            self.client_socket.sendall(json.dumps(item).encode('utf-8'))
        else:
            print(item)
            
class TCPListenHandler(QThread):
    message_received = pyqtSignal(str)
    
    def __init__(self, parent, client_socket):
        super().__init__(parent)
        self.parent = parent
        self.client_socket = client_socket
        self.message_received.connect(self.parent.notified)
                
    def run(self):
        while True:
            response = json.loads(self.client_socket.recv(1024).decode('utf-8'))
            print(response)
            if hasattr(response, "error"):
                error_code = response["error"]["code"]
                error_message = response["error"]["message"]
                if hasattr(response["error"],"data"):
                    error_data = response["error"]["data"]
                else:
                    error_data = None
                    
                if error_code == -32700:
                    print(error_message)
                    print(error_data)
                    raise Exception("Parse Error")
                elif error_code == -32600:
                    print(error_message)
                    print(error_data)
                    raise Exception("Invalname Request")
                elif error_code == -32601:
                    print(error_message)
                    print(error_data)
                    raise Exception("Method not found")
                elif error_code == -32602:
                    print(error_message)
                    print(error_data)
                    raise Exception("Invalname params")
                elif error_code == -32603:
                    print(error_message)
                    print(error_data)
                    raise Exception("Internal error")
                elif (-32099 < error_code and error_code < -32000):
                    print(error_message)
                    print(error_data)
                    raise Exception("Server error")
            else:
                self.message_received.emit(json.dumps(response))
                

class JsonRPCClient:
    def __init__(self, tcp_send_handler : TCPSendHandler, name : str = ""):
        self.tcp_send_handler : TCPSendHandler = tcp_send_handler
        self.name : str = name
        self._notify_vars = []
        self._get_all_attr()
    
    def __getattr__(self, method):
        print(method)
        if method == "_notify_vars" or method in self._notify_vars:
            return object.__getattribute__(self, method)
        else:
            def proxy(*args, **params):
                if len(args) != 0:
                    raise Exception("only key based params are supported")
                return self.__do_rpc(method, params)
            return proxy

    def __do_rpc(self, 
                 method : str, 
                 params : dict):
        item : json = RPCparameter(
            method, 
            params,
            self.name
        )
        json_data = json.dumps(item)
        
        self.tcp_send_handler.addRPCQueue(item)
    
    def _get_all_attr(self) -> None:
        if not DEBUG:
            self.__do_rpc("getallattr", None)

def RPCparameter(
    method: str,
    params: dict,
    name : str
) -> dict:
    
    """
        method: method
        params: parameter values. this should have dictionary format
        name : object name
    """
    
    item = {
        "method" : method,
        "params" : params if params is not None else {},
        "name" : name
    }
    return item

form_window = uic.loadUiType("test.ui")[0]
class UiMainWindow(QtWidgets.QMainWindow, form_window):
    def __init__(self, host : str = "127.0.0.1", port : int = 2):
        super().__init__()
        self.host : str = host
        self.port : int = port
        if not DEBUG:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
        else:
            self.client_socket = None
        self.setupUi(self)
        self.show()
        self.pushButton.clicked.connect(self.hi)
        self.tcp_send_handler = TCPSendHandler(self, self.client_socket)
        self.tcp_listen_handler = TCPListenHandler(self, self.client_socket)
        self.tcp_listen_handler.start()
        self.tcp_send_handler.start()
        
        self.ad9912_0 = JsonRPCClient(self.tcp_send_handler,"ad9912_0")
        
    def hi(self):
        self.ad9912_0.hello()
    
    def notified(self, message) -> None:
        response = json.loads(message)
        print(response["result"])
        class_obj = getattr(self,response["name"])
        for k, v in response["result"].items():
            if not k in class_obj._notify_vars:
                class_obj._notify_vars.append(k)
            setattr(class_obj,k,v)
        print(class_obj.frequency)
        
if __name__ == '__main__':
    host = "127.0.0.1"
    port : int = int(input())
    app = QtWidgets.QApplication(sys.argv)
    main_window = UiMainWindow(host, port)
    sys.exit(app.exec_())
    

    
