# -*- coding: utf-8 -*-
"""
Created on Mon Jan 10 11:01:00 2022

@author: QCP32
"""

import smtplib
import datetime
from email.message import EmailMessage
#%%

class MailAPI(object):
    
    def __init__(self, auto_connect=True):
        
        self.net_flag = False
        self.server = None
        self.receiver = None
        self.pc_name = "unknown"
        self.exp_name = "unknown"
        
        self.__ID = "iontrap.rpi109snu@gmail.com"
        self.__PW = "171Yb+qubit"
        
        if auto_connect:
            self.connectNET()
        
#%%

    def setLoginID(self, ID):
        if not isinstance(ID, str):
            raise ValueError("The login ID must be a string.")
        else:
            self.__ID = ID
    
    
    def setLoginPW(self, PW):
        if not isinstance(PW, str):
            raise ValueError("The login ID must be a string.")
        else:
            self.__PW = PW
    
            
    def setLoginPassword(self, PW):
        """
        To make it flexible, you can use this function as well.
        """
        self.setLoginPW(PW)
    
    
    def connectNET(self):
        if self.net_flag:
            raise Warning ("The e-mail server is already opened.")
            return
        
        else:
            try:
                self.server = smtplib.SMTP_SSL('smtp.gmail.com', 465) # gamil
                self.server.login(self.__ID, self.__PW)
                self.net_flag = True
                return True
            
            except:
                raise RuntimeError ("Failed to connect to the e-mail server.")
                return False

    def disconnectNET(self):
        if not self.net_flag:
            raise Warning ("The e-mail server was already closed.")
        self.net_flag = False
        
    def quitNET(self):
        self.server.quit()
    
    def isConnected(self):
        return self.nat_flag
    
    def setPCname(self, pc_name):
        self.pc_name = pc_name
        
    def setExperimentName(self, exp_name):
        self.exp_name = exp_name
        
    def setReceiver(self, address):
        if isinstance(address, list):
            self.receiver = address
        elif isinstance(address, str):
            self.receiver = [address]

    def setMessage(self, msg):
        self.message = msg
#%%    
    def sendMail(self, default=True):
        if self.receiver == None:
            raise RuntimeError ("You should set the receiver first.")
            return
        
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        msg = EmailMessage()
        # set an alternative html body

        if default:
            TXT_message = """
                        <html>
                               <b> #### Done experiment! #### </b><br><br>
                               The experiment run on (%s) has been finished! <br>
                                ===================================== <br>
                                <br>
                                Experiment: %s <br>
                                Finished at (%s) <br>
                                <br>
                                For more information, please contact <br>
                                E-mail: Jhjeong32@snu.ac.kr <br>
                                Tel.: 010-9600-3392 <br>
                            </p>
                        </html>
                        """ % (self.pc_name, self.exp_name, time_now)
        else:
            TXT_message = self.message
        
        msg.add_alternative(TXT_message, subtype='html')
       
        msg['Subject'] = "Done Experiment! (%s)" % self.exp_name
        msg['From'] = "iontrap.rpi109snu@gmail.com"
        msg['To'] = self.receiver
      
        self.server.send_message(msg)
        self.receiver = None
        return True
            
#%%
    
if __name__ == '__main__':
    my_mail = MailAPI()