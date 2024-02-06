# -*- coding: utf-8 -*-
"""
Created on Wed Nov 17 11:39:33 2021

@author: QCP32
"""
from PyQt5.QtCore import QThread, pyqtSignal
import socket
import time
from queue import Queue

class SocketHandler(QThread):
    """
    Since some servers do not use QtTcpServer, 
    This class is made to enhance the unity of the developed control programs.
    
    This class supports continuous listening to the server with QThread.
    It helps synchronizing the current status of the devices.    
    """
    
    is_connected = False
    sig_message = pyqtSignal()
    
    def __init__(self, parent=None, IP="", PORT=0, nick_name="default_name"):
        super().__init__()        
        assert isinstance(IP, str), "The IP must be a string."
        self.ip = IP
        try:
            self.port = int(PORT)
        except Exception as e:
            raise ValueError("The port should be able to be an int. (%s)" % e)
            
        self.parent = parent
        self.nick_name = nick_name
        self.msg_queue = Queue()
        
    def connectToServer(self, ip=None, port=None):
        if not self.is_connected:
            self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if ip == None:
                ip = self.ip
            if port == None:
                port = self.port
                
            try:
                self.sck.connect((ip, port))
                self.is_connected = True
                
                if not self.isRunning():
                    self.start()
            except Exception as e:
                self.toStatusBar("%s couldn't connect to the server. (%s)" % (self.nick_name, e))
        else:
            self.toStatusBar("You are already connected to the server.")
    
    def disconnectFromServer(self):
        if self.is_connected:
            self.sck.close()
        else:
            self.toStatusBar("You should connect to the server first.")
            
    def writeToServer(self, msg):
        if self.is_connected:
            self.sck.sendall(bytes("%s\n" % msg, "latin-1"))
        else:
            self.toStatusBar("You should connect to the server first.")
            
    def run(self):
        while self.is_connected:
            recv_data = self.sck.recv(1024).decode('latin-1')
            data_list = recv_data.split("\n")[:-1]
            print(data_list)
            self.sig_message.emit()
            time.sleep(0.1)
                
            
    def toStatusBar(self, msg):
        if not self.parent == None:
            self.parent.toStatusBar(msg)
        else:
            print(msg)
            
if __name__ == "__main__":
    client = SocketHandler(IP="127.0.0.1", PORT=61588)
    client.connectToServer()
    client.writeToServer("hey")
