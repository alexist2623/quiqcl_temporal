# -*- coding: utf-8 -*-
"""
Created on Wed Dec 29 18:29:34 2021

@author: QCP32
"""
from PyQt5.QtCore import QObject, QThread, QMutex, QWaitCondition, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

import os, glob, time
import pickle
import numpy as np

from multiprocessing import Process
from multiprocessing import Queue as mpQueue

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

class DataAnalyzer(QObject):
             
    # _version = "v0.01"
    # user_update = True
    _sig_pickle_load = pyqtSignal(bool)
    _gui = None
    _num_plots = 2
    
    def __init__(self, parent=None):
        super().__init__()
        self._controller = parent
        self.load_thread = PickleLoader(self)
        self.load_thread.finished.connect(self._finishedLoad)
        
        self.data_dict = {}
        self.data_class = {0: "OL", 1: "IL", 2: "ID"}
        
        self.dh_list = []
        for idx in range(self._num_plots):
            dh = DataHandler(self, idx)
            self.dh_list.append(dh)
        
    def loadPickleFiles(self, directory=dirname):
        file_list, _ = QFileDialog.getOpenFileNames(None, "Load pickle files", directory, "*.pkl")
        if len(file_list):
            self.load_thread.setFileList(file_list)
            self.load_thread.start()
            
    def setDataClass(self, data_class):
        """
        The sequencer data consists of (reg[x], reg[x], reg[x], some_int)
        You need to specify which one is which.        
        
        Avails class:
            Data[0]: Outer Loop, Indiv. data, Partial data
            Data[1]: Inner Loop, Indiv. data, Partial data
            Data[2]: Indiv. datga, Partial data
            
        Keys of classes:
            OL: Outer Loop
            IL: Inner Loop
            ID: Indiv. Data
            PD: Partial Data
            
        """
        if not isinstance(data_class, dict):
            raise ValueError ("The input must be a dictionary.")
            return
            
        for key, val in data_class.items():
            if key == 0:
                if not val in ["OL", "ID", "PD"]:
                    raise ValueError("The key value must be one of ['OL', 'ID', 'PD']")
                else:
                    self.data_class[key] = val
                    
            elif key == 1:
                if not val in ["IL", "ID", "PD"]:
                    raise ValueError("The key value must be one of ['IL', 'ID', 'PD']")
                    
                else:
                    self.data_class[key] = val
                
            elif key == 2:
                if not val in ["ID", "PD"]:
                    raise ValueError("The key value must be one of ['ID', 'PD']")
                    
                else:
                    self.data_class[key] = val
                
            else:
                raise ValueError ("You must check on the keys in the dict.")
                
    def setDataType(self, plot_idx, data_type):
        """
        M: 'M'ean
        A: 'A'cculumation
        D: state 'D'iscrimination
        H: 'H'istogram
        """
        if not isinstance(idx, int):
            raise ValueError ("The plot index must be an int.")
            return
        else:
            if not pot_idx in [0, 1]:
                raise ValueError ("The plot index must be 0 or 1.")
                return
            
        if not isinstance(data_type, str):
            raise ValueError ("The data type must be a string")
            return
        else:
            if data_type not in ["M", "A", "D", "H"]:
                self.dh_list[idx].setDataType(data_type)
            else:
                raise ValueErorr("")
                return
        
    def updateData(self, data_dict):
        self.data_dict = data_dict
            
    def _finishedLoad(self):
        """
        True: completed
        False: Aborted
        """
        self._sig_pickle_load.emit(True if not self.load_thread else False)
        self.toStatusBar("Finished loading pickle files.")
        
    def toStatusBar(self, msg):
        if not self._gui == None:
            self._gui.toStatusBar(msg)
        else:
            print(msg)

#%%
        
class PickleLoader(QThread):
    
    _sig_file_loaded = pyqtSignal(int, int) # Loaded_file_index, File_list_length
    file_list = []
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        
        self._status = "standby"
        self.loaded_data_dict = {}
        
        self.file_len = len(self.file_list)
        self.load_break = False
        
    def run(self):
        self._status = "running"
        self.load_break = False
        for file_idx, file_name in enumerate(self.file_list):
            self._status = "loading"
            if self.load_break:
                break
            else:
                try:
                    self._sig_file_loaded.emit(0, self.file_len)
                    base_file_name = os.path.basename(file_name)
                    self.loaded_data_dict[base_file_name] = self.loadPickleFile(file_name)
                    self.parent.updateData(self.loaded_data_dict)
                    self._sig_file_loaded.emit(file_idx+1, self.file_len)
                except Exception as e:
                    self.parent.toStatusBar("Error while loading %s. (%s)" % (file_name, e))
                
                
    def setFileList(self, file_list):
        self.file_list = file_list
        
    def stopLoading(self):
        self.load_break = True
        
                
    def loadPickleFile(self, file_name):
        if not len(self.file_list):
            raise RuntimeError ("You should set pickle files first.")
        else:
            with open (file_name, 'rb') as fr:
                loaded_data = pickle.load(fr)
                
            loaded_data_params = {}
            for key, val in loaded_data.items():
                if not key == "data":
                    loaded_data_params[key] = val
            loaded_data_dict = {"data": loaded_data["data"],
                                "shape": np.shape(loaded_data["data"]),
                                "params": loaded_data_params}
            return loaded_data_dict
    
#%%
class DataHandler(QThread):
    
    _status = "standby"
    _sig_done_processing = pyqtSignal(int)
    
    def __init__(self, parent=None, idx=0):
        super().__init__()
        self.parent = parent
        self.idx = idx
        
        self._proc_que = mpQueue()
        self._cons_que = mpQueue()
        
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        
        self._running_flag = False
        
        self._live_flag = False
        self.data_type = "m" # mean
        
        self.processor = DataProcess(self._proc_que, self._cons_que)
        self.x_data = None
        self.y_data = None
        
    def setLiveProcessing(self, flag:bool):
        self._live_flag = flag
        
    def setDataType(self, data_type):
        """
        M: 'M'ean
        A: 'A'cculumation
        D: state 'D'iscrimination
        H: 'H'istogram
        """
        self.data_type = data_type
            
        
    def runProcessing(self):
        self._proc_que.put([self.parent.data_class, self.data_type, self.parent.data_dict])
        
        self.x_data, self.y_data = self._cons_que.get()
        self._sig_done_processing.emit()
        print("Got an Array from the consumer's queue")
        
    def putArr(self):
        my_arr = self._getRandint(self._arr_size)
        self._proc_que.put(my_arr)
        print("Put an Array to the producer's queue.")
        
    def run(self):
        while True:
            self.mutex.lock()
            self._status = "processing"
            
            self.setupProcessing()
            
            while self._live_flag:
                time.sleep(2)
                self.setupProcessing()
            
            self._status = "standby"
            self.cond.wait(self.mutex)
            self.mutex.unlock()

    def set_status(self):
        self.pause = False
        self.cond.wakeAll()

    def pause_status(self):
        self.pause = True
        
    def _getRandint(self, my_size):
        return np.random.randint(0, 500, my_size)
        
class DataProcess(Process):
        
    def __init__(self, proc_q=None, cons_q=None):
        super(DataProcess, self).__init__()
        self._proc_que = proc_q
        self._cons_que = cons_q
        self._order = False
        self._running_flag = False
        
    def setOrder(self, order):
        self._order = order
        
    def _sortArray(self, arr):
        ordered = np.sort(arr)
        if self._order:
            ordered = ordered[::-1]
            
        return ordered
    
    def run(self):
        while self._running_flag:
            if not self._proc_que.empty():
                cmd = self._proc_que.get()
                
                class_dict, data_type, data_dict = cmd
                
                try:
                    x_data, y_data = self.processData(class_dict, data_type, data_dict)
                    self._cons_queue.put(["d", x_data, y_data])
                except Exception as err_msg:
                    self._cons_que.put(["e", err_msg])
                
                
                sorted_arr = self._sortArray(arr)
                self._cons_que.put(sorted_arr)
        
    def _cleanupQue(self):
        while not self._proc_que.empty():
            self._proc_que.get()
    
    def processData(self, class_dict, data_type, data_dict):
        
        processed_dict = {}
        for pkl_file, pkl_data in data_dict.items():
            processed_dict[pkl_file] = self._preprocessData(class_dict, pkl_data)
            
        
        
    def _preprocessData(self, class_dict, data_list):
        """
        This function convert the data into a desirable array that contains valuable data only.
        """
        np_data = np.asarray(data_list)
        if class_dict[0] == "OL":
            
            if class_dict[1] == "IL":
                shape0 = np.max(np_data[:, 0])+1
                shape1 = np.max(np_data[:, 1])+1
                processed_data = np_data[:, 2].reshape((shape0, shape1))
                
            elif class_dict[1] == "ID":
                processed_data = np_data[:, 1:3].reshape(-1)
                
            elif class_dict[1] == "PD":
                processed_data = np_data[:, 1:3]
                
        elif class_dict[0] == "ID":
            processed_data = np_data[:, :3].reshape(-1)
            
        elif class_dict[0] == "PD":
            processed_data = np_data[:, :3]
            
        return processed_data
            
    def _postprocessData(self, data_type, processed_dict):
        
        
    
      
if __name__ == "__main__":
    da = DataAnalyzer()
# class DataProcessor(Process):
    
#     def __init__(self, parent=None):
                
                