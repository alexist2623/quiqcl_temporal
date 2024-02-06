#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 18 15:16:43 2021

@author: pi
"""

import socket
import threading
import socketserver
import datetime
import struct, fcntl, os

default_TCPPort = 51000
Debugging = False

#%%% Logger

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    
    Client_list = []
    request_buffer = []
    allowed_ip = []
    logger = None
    
    GPIO = None
    OVEN = None
        
    def handle(self):
        global activeClientSocket, instLock
        
        self.clientSocket = self.request
        clientAddress = self.clientSocket.getpeername()
        
        if not clientAddress[0] in self.allowed_ip:
            self.clientSocket.sendall(bytes("Connection from this IP is not allowed.\n", 'latin-1'))
            self.logger.warning("Illegitimate connection is detected from (%s,%d)" % clientAddress)
            return
                
        if (threading.activeCount() > 15):
            activeClientAddress = activeClientSocket.getpeername()
            self.clientSocket.sendall(bytes('A:%s:$d\n' % activeClientAddress, 'latin-1'))
            self.clientSocket.close()
            print("%s: Refused connection from %s due to active connection with %s" %\
                  (datetime.datetime.now().isoformat(), clientAddress, activeClientAddress))
            self.logger.warning("Refused the connectiotn from (%s,%d) due to too many clients" % clientAddress)
            return
        
        else:
            activeClientSocket = self.clientSocket
                
            print('\nConnection from (%s,%d) become active connection\n' % clientAddress)
            self.Client_list.append(self.clientSocket)
            self.logger.info("Connected with (%s,%d)" % clientAddress)
            
        while True:
            data = self.clientSocket.recv(1024).decode('latin-1')[:-1] # drop EOL
            
            if len(data) == 0:
                self.Client_list.remove(self.clientSocket)
                self.logger.info("Disconnected from (%s,%d)" % clientAddress)
                return
            
            if "OVEN" in data:
                if not "SET" in data:
                    print(data)
                    if self.OVEN._oven_flag:
                        channel = data.split(':')[1]
                        if channel == self.OVEN.CHANNEL:
                            if "ON" in data: pass
                            else:
                                self.OVEN.CNT = 0
                                self.OVEN.to_worker([data, self.clientSocket])
                        else:
                            self.clientSocket.sendall(bytes("The oven channel(%s) is busy! you must wait unitl it finishes.\n" % channel, 'latin-1'))
                    else:
                        self.GPIO.to_worker([data, self.clientSocket])
                        self.OVEN.to_worker([data, self.clientSocket])
                        print("Done GPIO")
                else: # if "SET" in data
                    self.OVEN.set_target([data, self.clientSocket])
                
            elif "SHUTTER" in data:
                self.GPIO.to_worker([data, self.clientSocket])
                
            else:
                self.clientSocket.sendall(bytes("Detected an unknown command.\n", 'latin-1'))
                self.logger.error("Unknown command (%s) from (%s, %d)" % (data, clientAddress[0], clientAddress[1]))
                
            self.logger.info("Command (%s) from (%s, %d)" % (data, clientAddress[0], clientAddress[1]))
            
            
    def Announce(self, data, client=None):
        if client == None: Client_list = self.Client_list
        else             : Client_list = [client]
        for cli in Client_list:
            try: cli.sendall(bytes(data + "\n", 'latin-1'))
            except: 
                self.logger.warning("Client (%s) is disconnected while getting data (%s)" % (cli.getpeername()[0], data))
                self.Client_list.remove(client)


#%%                
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,
                struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])
   

#%%
if __name__ == "__main__":
    global activeClientSocket, instLock, PMT, CHARGING
    
    TCPPort = default_TCPPort
    activeClientSocket = None
    
    instLock = threading.Lock()
    
    ThreadedTCPServer.allow_reuse_address = True