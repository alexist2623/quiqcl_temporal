# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 20:12:14 2021

@author: QCP32
"""

class DeviceServerBase:
    """
    This class is not usual base class to provide instructions of basic methods.
    Instead, it conceals redundant parameters and methods to clean up the script.
    """
        
    IP = "127.0.0.1"
    PORT = 51234
    
    cp = None
    device_dict = {}
    
    
    def _getHostName(self):
        import socket
        return socket.gethostname()
    
    def _getPublicIP(self):
        import socket
        return socket.gethostbyname(socket.gethostname())
    