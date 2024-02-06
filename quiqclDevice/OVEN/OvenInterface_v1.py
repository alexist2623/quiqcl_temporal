# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 13:48:03 2022

@author: QCP32
@author: pi
"""
import time, os, platform
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
conf_dir = os.path.dirname(__file__) + '/Libs/'
conf_file = platform.node() + '.conf'

from queue import Queue
from OvenController import OVEN_HandlerQT
from OVEN_Libs.DB_ASRI133109_v0_01 import DB_ASRI133109


class Oven_Interface(QThread):
    """
    This is an interface class that makes for the users to use the DC power supply and the mechanical shutter.
    This class is for more like an application-like operation.
    
    
    """
    
    _status = "standby"
    
    def __init__(self, parent=None, config=None, logger=None, device=None):
        super().__init__()
        self.parent = parent
        self.cp = config
        self._device = device
        self.isOpened = False
        self._client_list = []
        self._allowed_ip_list = []
        self.oven = None
        
        self.logger = logger
        self.que = Queue()
        self.DB = DB_ASRI133109()
      
    def logger_decorator(func):
        """
        It writes logs when an exception happens.
        """
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except Exception as err:
                if not self.logger == None:
                    self.logger.error("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
                else:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return wrapper
        
    @property
    def device(self):
        return self._device
    
    @device.setter
    def device(self, dev):
        self._device = dev
        
    @property
    def time(self):
        return self.oven_timer.time
    
    @logger_decorator
    def openDevice(self):
        if self.oven == None:
            device_file = self.cp.get("oven", "file")
            device_class = self.cp.get("oven", "class")
            device_model = self.cp.get("oven", "model")
            
            self.oven = OVEN_HandlerQT(self, self.cp, device="DC_Power_Supply_E3631A")
            self.oven.setDeviceFile(device_file, device_class, device_model)
            self._connection_flag = True
            
            self.oven.oven_timer._sig_Over.connect(self._putOvenOver)
            self.oven.oven_timer._sig_Time.connect(self._putOvenQuery)
            
        if not self.isOpened:
            return self.oven.openDevice()
        else:
            return -1
        
        
    def _putOvenQuery(self):
        cmd = ["Q", "OVEN", "RUN", self._client_list]
        self.toWorkList(cmd)
        
    def _putOvenOver(self):
        message = ["D", "OVEN", "OVER", []]
        self.informClients(message, self._client_list)
        
       
    def toWorkList(self, cmd):         
        self.que.put(cmd)
        if not self.isRunning():
            self.start()

    def run(self):
        while True:
            work = self.que.get()
            self._status  = "running"
            # decompose the job
            work_type, command = work[:2]
            client = work[-1]
            
            if not client.address in self._allowed_ip_list:
                message = ["E", "OVEN", "BAN", []]
                self.informClients(message, client)
                self._status = "standby"
                self.toLog("error", "An unallowed ip(%s) attempted to control the oven." % client.address)
                return
            
            if work_type == "C":
                if command == "ELLO":
                    if not client in self._client_list:
                        self._client_list.append(client)
                        
                    message = ["D", "OVEN", "ELLO", []]
                    self.informClients(message, client)
                    if not self.isOpened:
                        flag = self.openDevice()
                        if flag:
                            self.isOpened = True
                            message = ["D", "OVEN", "ELLO", []]
                            self.informClients(message, self._client_list)
                        else:
                            message = ["E", "OVEN", "ON", []]
                            self.informClients(message, self._client_list)
                    else:
                        message = ["D", "OVEN", "ELLO", []]
                        self.informClients(message, client)
                        
                elif command == "ON":
                    channel = work[2]
                    self.oven.channel = channel
                    # GPIO controller is needed.
                    
                    
                    message = ["D", "OVEN", "ON", []]

                    if not self.oven.isRunning():
                        self.oven.operation = True
                        self.oven.status = "on"
                        self.oven.start()
                        
                        self.informClients(message, self._client_list)
                        
                    else:
                        if self.oven.status == "on":
                            self.informClients(message, client)
                        else:
                            self.oven.status = "on"
                            self.informClients(message, self._client_list)
                        
                elif command == "OFF":
                    message = ["D", "OVEN", "OFF", [1]]
                    
                    if not self.oven.isRunning():
                        self.oven.operation = True
                        self.oven.status = "off"
                        self.oven.start()
                        
                        self.informClients(message, self._client_list)

                    else:
                        if self.oven.status == "off": # it is already getting off..
                            self.informClients(message, self.client)
                        else:
                            self.informClients(message, self._client_list)
                            
                elif command == "SETA":
                    channel, value = work[2]
                    
                elif command == "SETV":
                    channel, value = work[2]
                    
                        
            elif work_type == "Q":
                if command == "STAT":
                    if not self.oven == None:
                        data = []
                        data += ["conn", self.oven.connection]
                        data += ["oper", self.oven.operation]
                        data += ["ch", self.oven.channel]
                        data += ["tar", self.oven.target]
                        data += ["stat", self.oven.status]
                        data += ["volt", self.oven.voltage]
                        data += ["curr", self.oven.current]
                        data += ["time", self.oven.time]
                        
                        message = ["D", "OVEN", "STAT", data]
                        
                    
                    else:
                        message = ["E", "OVEN", "STAT", []]
                        
                    self.informClients(message, client)
                    
                if command == "RUN":
                    if not self.oven == None:
                        data = []
                        data += ["volt", self.oven.voltage]
                        data += ["curr", self.oven.current]
                        data += ["time", self.oven.time]
                        
                        message = ["D", "OVEN", "RUN", data]
                        
                        self.informClients(message, client)
                    
                #%%
                
                elif command == "STAT":
                    data_list = work[2]
                    for board_idx, data in enumerate(data_list):
                        while len(data):
                            param = data.pop(0)
                            if param == "C":
                                self._current_settings[board_idx+1]["current"] = data.pop(0)
                            elif param == "F":
                                self._current_settings[board_idx+1]["freq_in_MHz"] = data.pop(0)
                            elif param == "P":
                                self._current_settings[board_idx+1]["power"] = data.pop(0)
                                
                elif command == "SETC":
                    board_idx, channel_1, channel_2, current = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["current"][0] = current
                    if channel_2:
                        self._current_settings[board_idx]["current"][1] = current
                    self.toGUI("Current values of Board_%d board have been changed." % (board_idx))
                    
                elif command == "SETF":
                    board_idx, channel_1, channel_2, frequency_in_MHz = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["freq_in_MHz"][0] = frequency_in_MHz
                    if channel_2:
                        self._current_settings[board_idx]["freq_in_MHz"][1] = frequency_in_MHz
                    self.toGUI("Frequency values of Board_%d board have been changed." % (board_idx))
                    
                elif command == "PWUP":
                    board_idx, channel_1, channel_2 = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["power"][0] = 1
                        self._current_settings[board_idx]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_idx]["power"][1] = 1
                        self._current_settings[board_idx]["current"][1] = 0
                    self.toGUI("Board_%d has been powered up." % (board_idx))

                elif command == "PWDN":
                    board_idx, channel_1, channel_2 = work[2]
                    if channel_1:
                        self._current_settings[board_idx]["power"][0] = 0
                        self._current_settings[board_idx]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_idx]["power"][1] = 0
                        self._current_settings[board_idx]["current"][1] = 0
                    self.toGUI("Board_%d has been powered off." % (board_idx))

            self.sig_update_callback.emit()
            self._status = "standby"
    
    @logger_decorator
    def informClients(self, msg, client):
        if not type(client) == list:
            client = [client]
        
        for client in client:
            client.toMessageList(msg)
            while client.status == "sending":
                time.sleep(0.01)
            
        
    def _readDeviceConfig(self, device=""):
        if device == "":
            device = self.device

        self.cp.read(dirname + "/DDS.conf")
        sys.path.append(dirname + '/%s' % device)
        exec("from %s import %s as DDS" % (self.cp.get(device, "file",), self.cp.get(device, "class")))
        
        self._getSerialNumber_from_Config(directory = dirname + '/%s/config/' % device,
                                          pc_name = os.getenv("COMPUTERNAME", "defaultvalue"))
        
        sys.path.append(dirname + '/%s/config' % device)

        exec("self.dds = DDS('%s')" % (self._serial_number))
        
    def _read_config(self):
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(conf_dir + conf_file)
        
        if "PW_SUPPLY" in cp.sections():
            conf_dict = dict(cp.items("PW_SUPPLY"))
            MODEL = conf_dict.pop("MODEL")
            
            self._value_dict = {}
            for idx, (key, val) in enumerate(conf_dict.items()):
                binary_key = "{0:02b}".format(idx)
                self._value_dict[binary_key] = {"CH_ID": key.split('_')[0],
                                                "ION": key.split('_')[1] + "yb",
                                                "VOL": float(val[:val.find('V')]),
                                                "CUR": float(val[val.find(',')+1:val.find('A')])}            
            return MODEL
    
    
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
            
            
    def _discover_device(self, IDN):        
        serial_ports = [(x[0], x[1], dict(y.split('=', 1) for y in x[2].split(' ') if '=' in y)) for x in comports()]
        port_candidates = []
        
        for dev in usb.core.find(find_all=True, custom_match= lambda x: x.bDeviceClass != 9):
            if platform.system() == 'Linux':
                port_candidates = [x[0] for x in serial_ports if x[2].get('SER') != None]
            else:
                raise NotImplementedError("Implement for platform.system()=={0}".format(platform.system()))
            
            assert len(port_candidates) == 1
            
        if not len(port_candidates):
            self._to_log("No devices are found.", 'error')
            return
            
        for port in port_candidates:
            device = serial.Serial(port=port, stopbits=2, timeout=2)
            device.write(b'*IDN?\n')
            line = device.readline().decode()
            if IDN in line:
                print("Connected to", line)
                return device
            
            else:
                self._to_log("No/Wrong response from the device.", "error")
        
    def _read_config(self):
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(conf_dir + conf_file)
        
        if "PW_SUPPLY" in cp.sections():
            conf_dict = dict(cp.items("PW_SUPPLY"))
            MODEL = conf_dict.pop("MODEL")
            
            self._value_dict = {}
            for idx, (key, val) in enumerate(conf_dict.items()):
                binary_key = "{0:02b}".format(idx)
                self._value_dict[binary_key] = {"CH_ID": key.split('_')[0],
                                                "ION": key.split('_')[1] + "yb",
                                                "VOL": float(val[:val.find('V')]),
                                                "CUR": float(val[val.find(',')+1:val.find('A')])}            
            return MODEL
            
            
        else:
            self._to_log("No power supplies are declared. Check the config file.", 'warning')
            return
        
    def _discover_device(self, IDN):        
        serial_ports = [(x[0], x[1], dict(y.split('=', 1) for y in x[2].split(' ') if '=' in y)) for x in comports()]
        port_candidates = []
        
        for dev in usb.core.find(find_all=True, custom_match= lambda x: x.bDeviceClass != 9):
            if platform.system() == 'Linux':
                port_candidates = [x[0] for x in serial_ports if x[2].get('SER') != None]
            else:
                raise NotImplementedError("Implement for platform.system()=={0}".format(platform.system()))
            
            assert len(port_candidates) == 1
            
        if not len(port_candidates):
            self._to_log("No devices are found.", 'error')
            return
            
        for port in port_candidates:
            device = serial.Serial(port=port, stopbits=2, timeout=2)
            device.write(b'*IDN?\n')
            line = device.readline().decode()
            if IDN in line:
                print("Connected to", line)
                return device
            
    def to_worker(self, item: list):
        self._queue.append(item)
        if not self._thread.isAlive():
            self._thread = threading.Thread(target=self._thread_run)
            self._thread.start()
            
    def set_target(self, item: list):
        operation, client = item
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(conf_dir + conf_file)
        
        if "PW_SUPPLY" in cp.sections():
            _, ch, _, which, value = operation.split(':')
            value = float(value)
        
        if   ch == "00": key = "EA_174"
        elif ch == "01": key = "EA_171"
        elif ch == "10": key = "EC_174"
        elif ch == "11": key = "EC_171"           
        
        if which == "VOL":
            self._value_dict[ch]['VOL'] = value
        elif which == "CUR":
            self._value_dict[ch]['CUR'] = value
        else:
            self._to_log("Unknown command (%s), from (%s, %d)" % (operation, client.getpeername()[0], client.getpeername()[1]), 'error')
        
        cp.set("PW_SUPPLY", key, "%.3fV, %.3fA" % (self._value_dict[ch]['VOL'], self._value_dict[ch]['CUR']))
        with open (conf_dir + conf_file, 'w') as cw:
            cp.write(cw)
            
        self._to_client("%s of %s is set to %.3f" % (which, key, value), client)
        self._to_log("%s of %s is set to %.3f by (%s, %d)" % (which, key, value, client.getpeername()[0], client.getpeername()[1]), 'info')
        
    def _thread_run(self):
        while len(self._queue):
           queue =  self._queue.pop(0)
           operation, client = queue
           print("Current operation:", operation)
           if "ON" in operation:
               try:
                   _, channel, _ = operation.split(':')
                   self.CNT = int(8*60)
                   self.CHANNEL = channel
                   self._TAR_VOL = self._value_dict[self.CHANNEL]['VOL']
                   self._TAR_CUR = self._value_dict[self.CHANNEL]['CUR']
                   self._oven_flag = True
                   self.STATUS = "ON"
                   
                   self._timer = threading.Thread(target=self._timer_run, args=(client, ))
                   self._oven = threading.Thread(target=self._oven_run, args=(client, ))
                   self._oven.start()
                   self._timer.start()
               except Exception as e:
                   print("An error while handling (%s, %s)" % (operation, e))
               
               
           elif "OFF" in operation:
               try:
                   print("getting off")
                   _, channel, _ = operation.split(':')
                   db_dict = self._value_dict[self.CHANNEL]
                   try:
                       self.DB.asri_oven(db_dict["CH_ID"],
                                         db_dict["ION"],
                                         (self._VOL/self._CUR),
                                         self._VOL,
                                         self._CUR)
                   except:
                       print("An Error while recording data to the DB\n")
                   self.CNT = 0
                   self.STATUS = "OFF"
               except Exception as e:
                   print("An error while handling (%s, %s)" % (operation, e))
               
    def _timer_run(self, client):
        while self.CNT > 0:
            time.sleep(1)
            self.CNT -= 1
            self._to_client("OVEN:%s:CNT:%03d" % (self.CHANNEL, self.CNT), client)
            
            if self.CNT <= 0:
                if self.STATUS == "ON":
                    self.to_worker(["OVEN:%s:OFF" % self.CHANNEL, client])
               
    def _oven_run(self, client):
        start_flag = 0
        while self._oven_flag:
            time.sleep(0.2)
            self._VOL = self.DC.ReadValue_V(1)
            time.sleep(0.2)
            self._CUR = self.DC.ReadValue_I(1)
            if self.STATUS == "ON":
                if not start_flag:
                    if (self._TAR_CUR - self._CUR > 0.15):
                        self.DC.CurrentOn(1, self._CUR + 0.15)
                    else:
                        self.DC.CurrentOn(1, self._TAR_CUR)
                        start_flag = True
                
            else:
                if not self._CUR < 0.15:
                    self.DC.CurrentOn(1, self._CUR - 0.15)
                    print(self._CUR)
                else:
                    self.DC.CurrentOn(1, 0)
                    self._oven_flag = False
                    self._to_client("OVEN:%s:OFF" % self.CHANNEL, client)
            self._to_client("OVEN:%s:VOL:%.3f" % (self.CHANNEL, self._VOL), client)
            self._to_client("OVEN:%s:CUR:%.3f" % (self.CHANNEL, self._CUR), client)                
                
    def _to_client(self, msg, client):
        try:
            if isinstance(client, list):
                for cli in client:
                    cli.sendall(bytes(msg + '\n', 'latin-1'))
                    
            else: client.sendall(bytes(msg + '\n', 'latin-1'))
            
        # When lost the client during the operation.
        except:
            if not self.STATUS == "OFF":
                self.to_worker(["OVEN:OFF", client])
                print("Lost connection to the client. forcing to stop")
                self._to_log("Lost connection while handling the oven.", "warning")
            
    def _to_log(self, log_msg, log_type):
        if not self._logger == None:
            if log_type == 'info':
                self._logger.info(log_msg)
            elif log_type == 'warning':
                self._logger.warning(log_msg)
            elif log_type == 'error':
                self._logger.error(log_msg)
        
class OvenTimer(QObject):
    
    _sig_Over = pyqtSignal(bool)
    _sig_Time = pyqtSignal(int)
    
    def __init__(self, max_time=480, debug=False):
        super().__init__()
        self.max_time = max_time
        self._time = 0
        
        self.timer = QTimer() 
        self.timer.timeout.connect(self.countdown)
        
        self._debug = debug
        
    @property
    def time(self):
        return self._time
    
    @time.setter
    def time(self, time):
        self._time = time
    
    def start(self):
        self.time = self.max_time
        self.timer.start(1000) # event for every second.
        
    def stop(self):
        self.timer.stop()
        self.time = 0
        self._sig_Over.emit(False)
        
        if self._debug:
            print("Timer stopped!")
        
    def countdown(self):
        self.time -= 1
        
        self._sig_Time.emit(self.time)
            
        if self._debug:
            print("Current time: (%2d:%02d)" % ( (self.time // 60), (self.time % 60)))
            
        if self.time <= 0:
            self.timeOver()
        
    def timeOver(self):
        self.timer.stop()
        self.time = 0
        self._sig_Over.emit(True)
        
        if self._debug:
            print("Time out!")
    
        
        
if __name__ == '__main__':
    OH = OVEN_Handler()
    
    
    
"""


class DDS_Controller(QThread):
    A dummy/test class to give a guide for making a script.
    The controller class inherits QThread class and handles commands in a separated thread.
    This avoids being delayed by the main thread's tasks.
    
    The logger decorator automatically records the exception when a bug happens.
    _num_boards = 2
    _serial_number = ""
    _current_settings = {}
    _client_list = []
    _status = "standby"
    
    def __init__(self, logger=None, device="DDS_w_VVA"):
        super().__init__()
        self.logger = logger
        self.device = device
        self.queue = Queue()
        self._readDeviceConfig(device)
        
    def logger_decorator(func):
        It writes logs when an exception happens.
        def wrapper(self, *args):
            try:
                func(self, *args)
            except Exception as err:
                if not self.logger == None:
                    self.logger.error("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
                else:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return func
    
    @logger_decorator
    def openDevice(self):
        self.dds.openDevice()
    
    @logger_decorator
    def closeDevice(self):
        self.dds.closeDevice()

    @logger_decorator    
    def toWorkList(self, cmd):            
        self.queue.put(cmd)
        if not self.isRunning():
            self.start()
            print("Thread started")

    @logger_decorator          
    def run(self):
        while True:
            work = self.queue.get()
            self._status  = "running"
            # decompose the job
            work_type, command = work[:2]
            client = work[-1]    
            
            if work_type == "C":
                if command == "ON":
                    When a client is connected, opens the devcie and send voltage data to the client.
                    print("opening the device")
                    if not self.dds._connected:
                        self.openDevice()
                        
                    if not client in self._client_list:
                        self._client_list.append(client)
                    client.toMessageList(["D", "DDS", "HELO", []])
                    data = self.getCurrentSettings()
                    message = ["D", "DDS", "STAT", data]
                    self.informClients(message, client)
                    
                elif command == "OFF":
                    When a client is disconnected, terminate the client and close the device if no client left.
                    if client in self._client_list:
                        self._client_list.remove(client)
                    # When there's no clients connected to the server. close the device.
                    if not len(self._client_list):
                        self.closeDevice()
                        self.toLog("info", "No client is being connected. closing the device.")
    
                elif command == "SETC": # Set current
                    board_num, channel_1, channel_2, current = work[2]
                    self.dds.setCurrent(board_num, channel_1, channel_2, current)
                    if channel_1:
                        self._current_settings[board_num]["current"][0] = current
                    if channel_2:
                        self._current_settings[board_num]["current"][1] = current
                    # Let all clients know that the currents are updated.
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                    
                elif command == "SETF": # Set frequency
                    board_num, channel_1, channel_2, freq_in_MHz = work[2]
                    self.dds.setFrequency(board_num, channel_1, channel_2, freq_in_MHz)
                    if channel_1:
                        self._current_settings[board_num]["freq_in_MHz"][0] = freq_in_MHz
                    if channel_2:
                        self._current_settings[board_num]["freq_in_MHz"][1] = freq_in_MHz
                    # Let all clients know that the frequencies are updated.
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                    
                elif command == "PWUP": # power up
                    board_num, channel_1, channel_2, = work[2]
                    self.dds.powerUp(board_num, channel_1, channel_2)
                    if channel_1:
                        self._current_settings[board_num]["power"][0] = 1
                        self._current_settings[board_num]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_num]["power"][1] = 1
                        self._current_settings[board_num]["current"][1] = 0
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                        
                elif command == "PWDN": # power down
                    board_num, channel_1, channel_2, = work[2]
                    self.dds.powerUp(board_num, channel_1, channel_2)
                    if channel_1:
                        self._current_settings[board_num]["power"][0] = 0
                        self._current_settings[board_num]["current"][0] = 0
                    if channel_2:
                        self._current_settings[board_num]["power"][1] = 0
                        self._current_settings[board_num]["current"][1] = 0
                    self.informClients(["D", "DDS", command, work[2]], self._client_list)
                    

                
            elif work_type == "Q":
                if command == "STAT":
                    data = self.getCurrentSettings()
                    message = ["D", "DDS", "STAT", data]
                    self.informClients(message, client)
                        
            else:
                self.toLog("critical", "Unknown work type (\"%s\") has been detected." % work_type)
            self._status = "standby"
            
            
    @logger_decorator
    def getCurrentSettings(self):
        This functions returnes current settings data as list.
        data = []
        for board_idx in self._current_settings.keys():
            data.append(["C", self._current_settings[board_idx]["current"],
                         "F", self._current_settings[board_idx]["freq_in_MHz"],
                         "P", self._current_settings[board_idx]["power"]])
            
        return data
                    
    @logger_decorator
    def informClients(self, msg, client):
        if not type(client) == list:
            print("not list")
            client = [client]
        
        for client in client:
            print(client._port)
            print(client.user_name)
            client.toMessageList(msg)
            while client.status == "sending":
                time.sleep(0.01)
            
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

    def _readDeviceConfig(self, device):
        self.cp = ConfigParser()
        self.cp.read(dirname + "/DDS.conf")
        sys.path.append(dirname + '/%s' % device)
        exec("from %s import %s as DDS" % (self.cp.get(device, "file",), self.cp.get(device, "class")))
        
        self._getSerialNumber_from_Config(directory = dirname + '/%s/config/' % device,
                                          pc_name = os.getenv("COMPUTERNAME", "defaultvalue"))
        
        sys.path.append(dirname + '/%s/config' % device)

        exec("self.dds = DDS('%s')" % (self._serial_number))
        
    def _getSerialNumber_from_Config(self, directory, pc_name):
        cp = ConfigParser()
        cp.read(directory + pc_name + '.conf')
        
        self._serial_number = cp.get('FPGA', 'serial_number')
        self._num_boards = int(cp.get('DDS', 'number_of_boards'))
        
        for board_idx in range(self._num_boards):
            self._current_settings[board_idx+1] = {"current": [0, 0], "freq_in_MHz": [0, 0], "power": [0, 0]}
    
    
        
class DummyClient():
    
    def __init__(self):
        pass
    
    def toMessageList(self, msg):
        print(msg)
    
"""