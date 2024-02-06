# -*- coding: utf-8 -*-
"""
Created on Thu Aug 31 12:41:13 2023

@author: jhjeong
E-mail: jhjeong32@snu.ac.kr
Tel. 010-9600-3392
"""
from QtClient_basic_v0_01 import ClientSocket
from PyQt5.QtCore import pyqtSignal, QObject
from queue import Queue


class SocketHandler(QObject):
    
    def __init__(self, parent=None, cp=None):
        self.socket_dict = {}
        ##
        self.parent = parent
        self.cp = cp
        self.createServerDictfromConfig()
        
        
    def __call__(self):
        return self.socket_dict
        
    def createServerDictfromConfig(self):
        self.user_name = self.cp.get("client", "nickname")
        
        server_list = list(self.cp.options("server"))
        
        for server in server_list:
            self.socket_dict[server] = {
                                        "IP": self.cp.get(server, "ip"),
                                        "PORT": self.cp.get(server, "port"),
                                        "description": self.cp.get("server", server),
                                        "socket": ClientSocket
                                        }
        
    def makeNewConnection(self, IP="", PORT=0):
        self.socket = ClientSocket(self, self.user_name)
        
        
    def closeTheConnection(self):
        pass
        
        
    def _appendSocket(self, socket, ):
        self.socket_list.append(socket)
        
    def _removeSocket(self, sck_nick):
        
        
    
