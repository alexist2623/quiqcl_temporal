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
                
    def run(self):
        while True:
            response = json.loads(self.client_socket.recv(1024).decode('utf-8'))
            
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
                for _name, _value in response.items():
                    setattr(self,_name,_value)
                self.message_received.emit(response)
                

class JsonRPCClient:
    def __init__(self, tcp_send_handler : TCPSendHandler, name : str = ""):
        self.tcp_send_handler : TCPSendHandler = tcp_send_handler
        self.name : str = name
        self._get_all_attr()
    
    def __getattr__(self, method):
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
    def __init__(self):
        super().__init__()
        host : str = "127.0.0.1"
        port : int = 2
        if not DEBUG:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
        else:
            self.client_socket = None
        self.setupUi(self)
        self.show()
        self.pushButton.clicked.connect(self.hi)
        self.tcp_send_handler = TCPSendHandler(self, self.client_socket)
        self.tcp_listen_handler = TCPListenHandler(self, self.client_socket)
        self.tcp_listen_handler.start()
        self.tcp_send_handler.start()
        self.ad9910 = JsonRPCClient(self.tcp_send_handler,"ad9912_0")
        
    def hi(self):
        self.ad9910.hello()
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = UiMainWindow()
    sys.exit(app.exec_())
    

    
