from PyQt5.QtCore import QThread
from queue import Queue
from GDM8341 import *

class AdcController(QThread):
    """
    The controller class uses QThread class as a base, handling commands and the device is done by QThread.
    This avoids being delayed by the main thread's jam.
    
    The logger decorator automatically records exceptions when bugs happen.
    """
    _status = "standby"
    
    def __init__(self, logger=None, parent=None, device=None):  #원래는 device 자리에 adc 들어가있었음
        super().__init__()
        self.logger = logger
        print("ADC controller v0.01")
        self.queue = Queue()
        self.adc = GDM8341()
    
    def logger_decorator(func):
        """
        It writes logs when an exception happens.
        """
        def wrapper(self, *args):
            try:
                func(self, *args)
            except Exception as err:
                if not self.logger == None:
                    self.logger.error("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
                else:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return wrapper
    
    @logger_decorator
    def openDevice(self):
        self.adc.openDevice()
    
    @logger_decorator
    def closeDevice(self):
        self.adc.closeDevice()

    @logger_decorator    
    def toWorkList(self, cmd):
        client = cmd[-1]
        if not client in self._client_list:
            self._client_list.append(client)
            
        self.queue.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started")

# Command : Type of command
# Data : value of command - freq / power

    @logger_decorator          
    def run(self):
        while True:
            # work example: ["Q", "VOLT", [1]]
            work = self.queue.get()
            self._status  = "running"
            # decompose the job
            work_type, command = work[:2]
            client = work[-1]    

            if work_type == "C":
                if command == "ON":
                    """
                    When a client is connected, opens the devcie and send voltage data to the client.
                    """
                    print("opening the device")
                    if not self.adc._is_opened:
                        self.openDevice()
                    else:
                        print("The device is already opened")
                        
                    client.toMessageList(["D", "ADC", "HELO", []])
                    
                elif command == "OFF":
                    """
                    When a client is disconnected, terminate the client and close the device if no client left.
                    """
                    if client in self._client_list:
                        self._client_list.remove(client)
                    # When there's no clients connected to the server. close the device.
                    if not len(self._client_list):
                        self.closeDevice()
                        self.toLog("info", "No client is being connected. closing the device.")
                else:
                    self.toLog("critical", "Unknown command (\"%s\") has been detected." % command)

                #work[2] may be used for selecting the channel of ADC 
                
            elif work_type == "Q":
                if command == "VOLT":
                    data = work[2] 
                    result, toall = self.adc.readVoltage("DC"), False
                    
                elif command == "CURR":
                    data = work[2] 
                    result, toall = self.adc.readCurrent("DC"), False
                                        
                elif command == "RESI":
                    data = work[2] 
                    result, toall = self.adc.readResistance(), False
                    
                else:
                    self.toLog("critical", "Unknown command (\"%s\") has been detected." % command)

            else:
                self.toLog("critical", "Unknown work type (\"%s\") has been detected." % work_type)
                
            msg = ['D', 'ADC', work_type , [result]]  #result value should have a list form
            
            if toall == True:
                self.informClients(msg, self._client_list)
            else:
                self.informClients(msg, client)
                
            self._status = "standby"

    @logger_decorator
    def informClients(self, msg, client):
        if type(client) != list:
            client = [client]
        
        print('To Client :', msg)
        #self.informing_msg = msg
        for clt in client:
            clt.toMessageList(msg)
            
        print("informing Done!")
         
    def toLog(self, log_type, log_content):
        if not self.logger == None:
            if log_type == "debug":
                self.logger.debug(log_content)
            elif log_type == "info":
                self.logger.info(log_content)
            elif log_type == "warning":
                self.logger.warning(log_content)
            elif log_type == "error":
                self.logger.error(log_content)
            else:
                self.logger.critical(log_content)
        else:
            print(log_type, log_content)

        
class DummyClient():
    
    def __init__(self):
        pass
    
    def sendMessage(self, msg):
        print(msg)
        
