# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 20:48:23 2021

@author: QCP32
"""
import os, time, datetime, glob
version = "1.08"
filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

sequencer_program_list = [os.path.basename(x) for x in glob.glob(dirname + "/SequencerProgram_*.py")]
sequencer_program_list.sort()
print("Found a sequencer program file:", sequencer_program_list[-1])

if sequencer_program_list[-1][-5:-3] == "08":
    from SequencerProgram_v1_08 import SequencerProgram, reg
    import SequencerUtility_v1_03 as su

else:
    from SequencerProgram_v1_07 import SequencerProgram, reg
    import SequencerUtility_v1_01 as su


from ArtyS7_v1_02 import ArtyS7
from PyQt5.QtCore import pyqtSignal, QObject, QThread

class SequencerRunner(QObject):
        
    sig_seq_run = pyqtSignal()
    sig_dev_con = pyqtSignal(bool)
    sig_seq_iter_done = pyqtSignal(int, int) # iter, total_run
    sig_seq_complete = pyqtSignal(bool) # True: completed, False: broken while running.
    sig_occupied = pyqtSignal(bool)
    # sig_swch_restore = pyqtSignal() # This signal runs the switch panel, so the switches retunrs to initial settings.
    
    sequencer = None
    is_opened = False
    seq_file = ""
    
    data_run_index = 0
    data_run_loop = 1
    
    data = []
    spontaneous = False

    user_stop = False
    device_sweep_flag = False 
    
    
    def __init__(self, ser_num=None, hw_def=None, parent=None):
        super().__init__()
        self.parent = parent
        self.ser_num = ser_num
        self.com_port = self.getComPort(ser_num)
        self.hw_def = hw_def
        self.SequencerProgram = SequencerProgram
        self.reg = reg
        self.su = su
        self.openHardwareDefinition(self.hw_def)
        self.runner = Runner(self)
        self.runner.finished.connect(self._finishedRunner)
        self.default_hw_def_dir = dirname
        
        self.start_time = None
        self.end_time = None
        
        self.iter_start_time = None
        self.iter_end_time = None
        
        self.occupant = ""
        self.verbose = False
        
    def openDevice(self, com_port=None):
        if com_port == None:
            com_port = self.com_port
        try:
            if self.sequencer == None:
                self.sequencer = ArtyS7(com_port)
            else:
                self.sequencer.com.open()
            self.toStatusBar("Connected to the FPGA.")
            self.is_opened = True
            self.sig_dev_con.emit(True)
        except Exception as e:
            self.toStatusBar("Failed to open the FPGA. (%s)" % (e))
            return -1 # open fail
            
    def closeDevice(self):
        if self.is_opened:
            try:
                self.sequencer.com.close()
                self.toStatusBar("Closed the FPGA.")
                self.is_opened = False
                self.sig_dev_con.emit(False)
                self.sequencer = None
            except Exception as ee:
                print("An error while closing the sequencer.(%s)" % ee)
        else:
            self.toStatusBar("Failed to close the FPGA. Maybe the FPGA is already closed?")
            
    def openHardwareDefinitionFile(self):
        """
        This function directly runs the hardware definition file.
        """
        full_path_of_hardware_def = os.path.abspath(dirname + '/%s.py' % self.hw_def)
        os.startfile(full_path_of_hardware_def)
            
    def openHardwareDefinition(self, hw_def):
        try:
            import sys
            sys.path.append(dirname)
            exec("import %s as hd" % hw_def)
            exec("self.hd = hd")
        except Exception as e:
             self.toStatusBar("Failed to open the hardware definition (%s)." % e)
             
    def loadSequencerFile(self, seq_file="", replace_dict={}, replace_registers={}):
        """
        Args: seq_file (str), replace_line_dict (dict), replace_register_dict (dict)
            - seq_file: It accepts the full path of the sequencer script.
                        It automatically finds where the hardware definition is defined and replaces it to its own hardware definition.
                        the "__main__" function in the seq_file will be ignored.
            - replace_dict: This replaces the given parameters in the seq_file.
                            To find parameters, please use getParameters function below.
                            replace dict = {
                                            n-th_line_where_the_parameter1_defined: {"parameter_name1"}: parameter_value,
                                            n-th_line_where_the_parameter2_defined: {"parameter_name2"}: parameter_value
                                            }
                            n-th_line_where_the_parameter1_defined: int
                            "parameter_name1": str
                             parameter_value: int
            - replace_registers: This replaces the given register to the new register. for example, from "PMT1" to "PMT2".
                                 The keys of the dict are old register strings, the values of the dict are new register strings.
                        
        """
        try:
            script_filename = os.path.basename(seq_file)
            file_string = self.replaceParameters(seq_file, replace_dict, replace_registers)
            self._executeFileString(file_string)
            self.seq_file = script_filename
        except Exception as ee:
            self.toStatusBar("An error while loading the sequencer file '%s'.(%s)" % (os.path.basename(seq_file), ee))

            
    def runSequencerFile(self, iteration=1, device_sweep=False):
        if self.is_opened:
            self.sig_seq_run.emit()
            self.device_sweep_flag = device_sweep
            self.data_run_index = 0
            self.data_run_loop = iteration
            self.data = []
            
            # spontaneous flag is needed when the running time is measured inside of this class.
            if not self.spontaneous:
                self.start_time = datetime.datetime.now()
            
            self.startRunner()
        else:
            self.toStatusBar("You must open the FPGA first.")
            
    def startRunner(self):
        self.data_run_index += 1
        self.iter_start_time = datetime.datetime.now()
        self.runner.start()
        
    def stopRunner(self):
        # user_stop lets us know whether it is aborted while running.
        self.user_stop = True
        self.sequencer.stop_sequencer()
        
    def replaceParameters(self, seq_file="", replace_dict={}, replace_registers={}):
        """
        This function reads a sequencer file and retunrs a file string with gvien parameters changed.
        """
        file_string = ''
        line_idx = 0
        line_idx_list = list(replace_dict.keys())
        with open (seq_file) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if " as hd\n" in line:
                    print ("replaced from %s" % line)
                    line = "import %s as hd\n" % self.hw_def
                    print("to %s" % line)
                if line_idx in line_idx_list:
                    line = '%s=%.0f\n' % (replace_dict[line_idx]["param"], replace_dict[line_idx]["value"])
                file_string += line
                line_idx += 1
                
        if len(replace_registers):
            for old_str, new_str in replace_registers.items():
                file_string = file_string.replace(old_str, new_str)
                
        return file_string
    
    
        
    def getComPort(self, ser_num=""):
        from serial.tools.list_ports import comports
        for dev in comports():
            if dev.serial_number == ser_num:
                return dev.device
            
        return None
        
    def getParameters(self, seq_file=""):
        """
        This function reads a sequencer file and returns parameters as a dict.
        Note that the parameter value is stored as a string. (for some reason.)
        The key of the param_dict is a line index. This line index is used to replace the parameter values.
        """
        param_dict = {}
        line_idx = 0
        with open (seq_file) as f:
            while True:
                line = f.readline()
                if not line: break
                if not line[0] == "#" and "=" in line:
                    param = line.split('=')[0]
                    param = param.replace(" ", "")
                    if  param.upper() == param: # if the key consists of capital characters only.
                        value = line.split('=')[1]
                        value = value.replace(" ", "")
                        if value[-1] == "\n":
                            value = value[:-1]
                        param_dict[line_idx] = {"param": param, "value": value}
                line_idx += 1
        return param_dict
        
            
    def toStatusBar(self, message):
        if not self.parent == None:
            self.parent.toStatusBar(message)
        else:
            print(message)
            
    def _finishedRunner(self):
        self.iter_end_time = datetime.datetime.now()

        if self.user_stop:
            self.sig_seq_complete.emit(False)
            self.sequencer.flush_input()
            self.user_stop = False # initialize the flag.
            self.toStatusBar("Stopped running sequencer.")
        else:
            if not self.data_run_index == self.data_run_loop:
                self.sig_seq_iter_done.emit(self.data_run_index, self.data_run_loop)
                self.startRunner()
            else:
                if not self.spontaneous:
                    self.end_time = datetime.datetime.now()
                self.sig_seq_complete.emit(True)
                # self.toStatusBar("Completed running sequencer.")
                
    def _executeFileString(self, file_string):
        """
        This functions runs a file string and saves it in the global dictionary.
        """
        gl = dict(globals())
        exec(file_string, gl)
        self.gl = gl
            
class Runner(QThread):
    
    sig_data_list = pyqtSignal(list)
    status = "standby"
    buffer_data = []
    data = []
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
    
    def run(self):
        try:
            self.status = "running"
            if self.controller.device_sweep_flag:
                time.sleep(1)
            
            controller = self.controller
            s = controller.gl['s']
            
            s.program(show=False, target=controller.sequencer)
            controller.sequencer.auto_mode()
            controller.sequencer.start_sequencer()
            
            self.data = []
            while(controller.sequencer.sequencer_running_status() == 'running'):
                data_count = controller.sequencer.fifo_data_length()
                self.data += controller.sequencer.read_fifo_data(data_count)
            
            data_count = controller.sequencer.fifo_data_length()
            while (data_count > 0):
                self.data += controller.sequencer.read_fifo_data(data_count)
                data_count = controller.sequencer.fifo_data_length()
    
            if self.controller.verbose:
                print(self.data)
                
            controller.data.append(self.data)
        except Exception as ee:
            print("An error occured while running the sequencer file (%s)" % ee)
        self.status = "standby"