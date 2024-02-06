# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 18:03:23 2021

@author: QCP32
"""
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
import os
from Mail_API import MailAPI

class MailSender(QThread):
    
    device_type = "library"
    
    sig_mail_conn = pyqtSignal(int)
    sig_mail_sent = pyqtSignal()


    def __init__(self):
        super().__init__()
        self.mail = MailAPI(auto_connect=False)
        self.queue = Queue()
        
        pc_name = os.getenv("COMPUTERNAME", 'defaultValue')
        self.setPCname(pc_name)
        
    def connect(self):
        self.toWorkList(["C", "CON"])
        
    def disconnect(self):
        self.mail.disconnectNET()
        self.sig_mail_conn.emit(False)
           
    def setPCname(self, pc_name):
        self.mail.setPCname(pc_name)
        
    def setExperimentName(self, exp_name):
        self.mail.setExperimentName(exp_name)
        
    def setReceiver(self, address):
        self.mail.setReceiver(address)
        
    def sendMail(self):
        self.toWorkList(["C", "SEND"])
            
            
    def toWorkList(self, cmd):         
        self.queue.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started")

    def run(self):
        while True:
            work = self.queue.get()
            self._status  = "running"
            # decompose the job
            work_type, command = work[:2]
    
            if work_type == "C":
                if command == "CON":
                    """
                    Successfully received a response from the server
                    """
                    conn = self.mail.connectNET()
                    if conn:
                        print("mail server connected")
                        self.sig_mail_conn.emit(1)
                    else:
                        self.sig_mail_conn.emit(-1)
                    
                
                elif command == "SEND":
                    sent = self.mail.sendMail()
                    if sent:
                        print("Mail sent.")
                        self.sig_mail_sent.emit()
                    
if __name__ == "__main__":
    ms = MailSender()