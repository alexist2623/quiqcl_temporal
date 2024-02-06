# -*- coding: utf-8 -*-
"""
Created on Wed Nov  3 10:10:46 2021

@author: QCP32
"""
import os
version = "1.1"

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
import pickle, datetime
import numpy as np

# PyQt libraries
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QGridLayout, QFileDialog

# from main_panel_theme import main_panel_theme_base
main_ui_file = dirname + "/runner_panel.ui"
main_ui, _ = uic.loadUiType(main_ui_file)
    
from progress_bar import ProgressBar
from runner_panel_theme import runner_panel_theme_base

class RunnerPanel(QtWidgets.QMainWindow, main_ui, runner_panel_theme_base):
    
    seq_file = ""
    user_update = True
    user_run_flag = False
    
    sweep_run_flag = False
    sweep_run_num = 0
    sweep_run_list = []
    
    def __init__(self, device_dict={}, parent=None, theme="black"):
        super().__init__()
        self.setupUi(self)
        self.device_dict = device_dict
        self.parent = parent
        self._theme = theme
        self._setupProgress()
        self._initUi()
        
        self.saver = SaveRunner(self)
        self.saver.finished.connect(self.logSavedFile)

        # for sequencer section in the panel
        if 'sequencer' in self.device_dict.keys():
            self.sequencer = self.device_dict['sequencer']
            
            self.TXT_serial.setText(self.sequencer.ser_num)
            self.TXT_com.setText(self.sequencer.com_port)
            
            self.sequencer.sig_dev_con.connect(self.changeFPGAconn)
            self.sequencer.sig_occupied.connect(self._setInterlock)
            self.sequencer.sig_seq_iter_done.connect(self.progress_bar.iterationDone)
            self.sequencer.sig_seq_iter_done.connect(self._iterationProgress)
            self.sequencer.sig_seq_complete.connect(self.progress_bar.runDone)
            self.sequencer.sig_seq_complete.connect(self._completeProgress)
            
        self._disable_object_list = [
                                    self.BTN_file_load,
                                    self.BTN_fpga_connect,
                                    
                                    self.CBOX_device,
                                    self.CBOX_parameter,
                                    self.CHBOX_sweep,
                                    self.TXT_sweep,
                                    
                                    self.CHBOX_save,
                                    self.CHBOX_individual,
                                    self.TXT_data_path,
                                    self.TXT_data_filename,
                                    self.BTN_data_path,
                                    ]
        
        self._setupDeviceDict()
        
    #%% Sequencer
    def runSequencer(self):
        self.user_run_flag = True
        
        self.sequencer.occupant = "runner"
        self.sequencer.sig_occupied.emit(True)
        
        self.seq_file = self.TXT_filename.text()
        new_value_dict = self.getParametersFromTable()
        
        iteration = 1
        if "NUM_EXTERNAL_ITERATION" in new_value_dict.keys():
            iteration = new_value_dict["NUM_EXTERNAL_ITERATION"]
        
        replace_dict = {}
        # The replace dict should consist of 
        # replace_dict[line_idx] = {'param': param, 'value': value}
            # line_idx: indicate where the parameter is defined in the sequencer file.
            # param: the parameter name that should be changed.
            # value: the new value of the parameter
        for line_idx, param_dict in self.file_param_dict.items():
            for param in new_value_dict.keys():
                if param == param_dict['param']:
                    replace_dict[line_idx] = {'param': param, 'value': new_value_dict[param]}
                
        self.sequencer.loadSequencerFile(self.seq_file, replace_dict)
        self.sequencer.runSequencerFile(iteration=iteration)
        
    def stopSequencer(self):
        self.sequencer.stopRunner()
        
    def setDeviceSweep(self):
        device = self.CBOX_device.currentText()
        if self.device_dict[device]._is_opened:
            parameter = self.CBOX_parameter.currentText()

            if not self.sweep_run_flag:
                try:
                    sweep_string = self.TXT_sweep.text()
                    start, end, num = sweep_string.split(":")
                    self.sequencer.device_sweep_flag = True
                    self.sweep_run_list = np.linspace(float(start), float(end), int(num))
                    self.sweep_run_num = 0
                    self.start_time = datetime.datetime.now()
                except:
                    self.toStatusBar("You must set the sweep parameters correctly.")
                    self.user_update = False
                    self.BTN_file_run.setChecked(False)
                    self.user_update = True
                    self.sequencer.occupant = ""
                    self.sequencer.sig_occupied.emit(False)
                    return
        self.setDeviceByParameter(device, parameter, self.sweep_run_list[self.sweep_run_num])
        self.sweep_run_num += 1
        self.sweep_run_flag = True
        self.runSequencer()
            
    def setDeviceByParameter(self, device, parameter, value):
        """
        args: 
            - device: The key of in the device_dict. The device_type will be recognized here.
            - parameter: The parameter you want to sweep.
            - value: The value that you want to set.
        """
        controller = self.device_dict[device]
        if controller.device_type == "DDS":            
            opt1 = self.CBOX_sweep_option_0.currentText()
            opt2 = self.CBOX_sweep_option_1.currentText()
            
            board_num = int(opt1[3:])
            ch = int(opt2[2:])
            if ch == 1:
                ch1 = 1
                ch2 = 0
            else:
                ch1 = 0
                ch2 = 1
            
            if parameter == "Freq. in MHz":
                controller.setFrequency(board_num, ch1, ch2, value)
                
            elif parameter == "Power":
                controller.setCurrent(board_num, ch1, ch2, value)
        #elif ~
        
    def loadSequencerFile(self, seq_file):
        self.seq_file = seq_file
        self.TXT_filename.setText(self.seq_file)
        self.fillParameterTable(seq_file)
        
    def pressedHardwareDefinition(self):
        try:
            self.sequencer.openHardwareDefinitionFile()
        except Exception as ee:
            self.toStatusBar("An error while opening the hardware definition file.(%s)" % ee)
        
 
    #%% button slots
    def buttonFileLoadPressed(self):
        if self.sequencer.is_opened:
            seq_file, _ = QFileDialog.getOpenFileName(self, "Load a sequencer file(.py)", dirname, "*.py")
            if seq_file == "":
                self.toStatusBar("Aborted loading a sequencer file.")
                return
            self.loadSequencerFile(seq_file)
        else:
            self.toStatusBar("You must open the FPGA first.")
        
    def buttonFileRunPressed(self, flag):
        if self.user_update:
            if flag:
                if self.sequencer.is_opened:
                    if self.TXT_filename.text() == "":
                        self.toStatusBar("You must open the sequencer file first.")
                        self.user_update = False
                        self.BTN_file_run.setChecked(False)
                        self.user_update = True
                        return
                    self.insertTextLog("(%s) Start to run sequencer." % datetime.datetime.now().strftime("%H:%M:%S"))
                    
                    self.sequencer.occupant = "runner"
                    self.sequencer.sig_occupied.emit(True)
                    
                    self.progress_bar.changeProgressBar(0, 1)
                    self.progress_bar.changeLabelText("Started sequencer...")
                    if self.CHBOX_sweep.isChecked():
                        self.setDeviceSweep()
                    else:
                        self.runSequencer()
                else:
                    self.toStatusBar("You must open the FPGA first.")
                    self.user_update = False
                    self.BTN_file_run.setChecked(False)
                    self.user_update = True
                
            else:
                self.stopSequencer()
    
    def buttonFPGAConnPressed(self, flag):
        if self.user_update:
            if flag:
                open_flag = self.sequencer.openDevice()
                if open_flag == -1:
                    self.changeFPGAconn(False)
                    return
                if not self.TXT_serial.text() == self.sequencer.ser_num:
                    self.TXT_serial.setText(self.sequencer.ser_num)
                if not self.TXT_serial.text() == self.sequencer.com_port:
                    self.TXT_com.setText(self.sequencer.com_port)
            else:
                self.sequencer.closeDevice()
    
    def buttonDataLoadPathPressed(self):
        save_path = QFileDialog.getExistingDirectory(self, "Select data save path", dirname)
        if save_path == "":
            return
        self.TXT_data_path.setText(save_path)
        
    #%% Combobox
    def selectComboDevice(self, device):
        controller = self.device_dict[device]
        
        device_type = controller.device_type
        if device_type == "DDS":
            self.CBOX_parameter.addItems(["Freq. in MHz", "Power"])
            sweep_parameter_dict = controller.sweep_parameter_dict
            for idx, option in enumerate(sweep_parameter_dict.keys()):
                value_list = sweep_parameter_dict[option]
                for value in value_list:
                    cbox = getattr(self, "CBOX_sweep_option_%d" % idx)
                    cbox.addItem(option + str(value))

            
        elif device_type == "DAC":
            self.CBOX_parameter.addItems(["Voltage"])
    
    #%%
    def fillParameterTable(self, seq_file=""):       
        if not 'sequencer' in self.device_dict:
            self.toStatusBar("Sequencer is not found in the device_dict.")
            return
        
        if seq_file == "":
            seq_file = self.seq_file
        
        table = self.TBL_parameters
        try:
            file_param_dict = self.sequencer.getParameters(seq_file)
        except:
            self.toStatusBar("Couldn't load the parameters from the sequence file (%s)." % seq_file)
            return
        self.file_param_dict = file_param_dict
        param_list = ['NUM_EXTERNAL_ITERATION']
        value_list = ['1']
        for line_idx, param_dict in file_param_dict.items():
            param_list.append(param_dict["param"])
            value_list.append(param_dict["value"])
            
        # Fill table values
        table.setRowCount(len(file_param_dict)+1) # +1 is for including NUM_EXTERNAL_ITERATION
        table.setVerticalHeaderLabels(param_list)
        for value_idx, value in enumerate(value_list):
            table.setItem(value_idx, 0, QtWidgets.QTableWidgetItem("%s" % value)) # Fill the current vlaue item from the loaded file.
            table.setItem(value_idx, 1, QtWidgets.QTableWidgetItem(""))             # Fill the new value item with an empty string.
            
    def getParametersFromTable(self):
        param_count = self.TBL_parameters.rowCount()
        replace_dict = {}
        for param_idx in range(param_count):
            new_value = self.TBL_parameters.item(param_idx, 1).text()
            
            if not new_value == "":
                param = self.TBL_parameters.verticalHeaderItem(param_idx).text()
                try:
                    value = int(new_value)
                except:
                    self.toStatusBar("%s should be an integer number." % param)
                    return
                replace_dict[param] = value
            
        return replace_dict
               
    def toStatusBar(self, message):
        if not self.parent == None:
            self.parent.toStatusBar(message)
        else:
            print(message)
            
    def insertTextLog(self, message):
        self.TXT_log.insertPlainText(message + '\n')
            
    def changeFPGAconn(self, flag):
        self.user_update = False
        if flag:
            if not self.TXT_serial.text() == self.sequencer.ser_num:
                self.TXT_serial.setText(self.sequencer.ser_num)
            if not self.TXT_serial.text() == self.sequencer.com_port:
                self.TXT_com.setText(self.sequencer.com_port)
        self.BTN_fpga_connect.setChecked(flag)
        self.user_update = True
        
    #%% Handling sequencer progress
    def _setInterlock(self, occupation_flag):
        if occupation_flag:
            if not self.sequencer.occupant == "runner":
                self.BTN_file_run.setEnabled(False)
            for obj in self._disable_object_list:
                obj.setEnabled(False)
        else:
            self._restoreObjects()
            self.BTN_file_run.setEnabled(True)
        
    def _iterationProgress(self):
        if self.user_run_flag:
            if self.CHBOX_individual.isChecked():
                self._runSaver()
        
        
    def _completeProgress(self, flag):
        if self.user_run_flag:
            if flag:
                if self.sweep_run_flag:
    
                    self._runSaver()
                    if not self.sweep_run_num >= len(self.sweep_run_list):
                        self.progress_bar.changeProgressBar(self.sweep_run_num, len(self.sweep_run_list))
                        time_str = self.progress_bar._calculateTime(self.sequencer.start_time, self.sequencer.end_time)
                        self.progress_bar.changeLabelText("Running (%d/%d)...[%s per iter.]" % (self.sweep_run_num, len(self.sweep_run_list), time_str))
                        self.setDeviceSweep()
                        return
                    else:
                        self.progress_bar.completeProgressBar(flag)
                        self.end_time = datetime.datetime.now()
                        time_str = self.progress_bar._calculateTime(self.start_time, self.end_time)
                        self.progress_bar.changeLabelText("Completed. Total running time: (%s)" % time_str)
                        self.sweep_run_flag = False
                        self.sequencer.device_sweep_flag = False
                        
                        self.sequencer.occupant = ""
                        self.sequencer.sig_occupied.emit(False)
                        self._sendMail()
                else:
                    self._runSaver()
                    self.sequencer.occupant = ""
                    self.sequencer.sig_occupied.emit(False)
                    self._sendMail()
            else:
                self.progress_bar.completeProgressBar(flag)
                self.progress_bar.changeLabelText("Stopped running.")
                self.sweep_run_flag = False
                self.sequencer.device_sweep_flag = False
                
                self.sequencer.occupant = ""
                self.sequencer.sig_occupied.emit(False)
                self._sendMail()
                
    #%% Redundants
    def _restoreObjects(self):
        self.user_update = False
        for obj in self._disable_object_list:
            obj.setEnabled(True)
        self.BTN_file_run.setChecked(False)
        self.user_update = True
        self.user_run_flag = False
                    
    def _runSaver(self):
        if self.CHBOX_save.isChecked():
            individual_flag = self.CHBOX_individual.isChecked()
            self.saver.inidivual_flag = individual_flag
            self.saver.sweep_flag = self.sweep_run_flag
            
            if individual_flag:
                data = self.sequencer.runner.data
            else:
                data = self.sequencer.data
            
            self.saver.getData(data)
            self.saver.start()
        
    def _setupProgress(self):
        self.progress_bar = ProgressBar(self)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.progress_bar)
        self.GBOX_progress.setLayout(layout)
        self.progress_bar.changeTheme(self._theme)
        
    def _setupDeviceDict(self):
        for device, controller in self.device_dict.items():
            if not device == "sequencer":
                self.CBOX_device.addItem(device)
        
    def _initUi(self):
        self.TXT_data_path.setText(dirname)
        self.TXT_data_filename.setText("default_file")
        
    def _sendMail(self):
        if self.CHBOX_mail.isChecked():
            receiver = self.TXT_mail.text()
            self.parent.library_dict["mail_sender"].setExperimentName("Sequencer")
            self.parent.library_dict["mail_sender"].setReceiver(receiver)
            self.parent.library_dict["mail_sender"].connect()
            self.parent.library_dict["mail_sender"].sendMail()
            self.parent.library_dict["mail_sender"].disconnect()
            self.insertTextLog("(%s) A Notification mail sent." % datetime.datetime.now().strftime("%H:%M:%S"))

    #%% Save file 
    def _getSaveLogStr(self):
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        save_name = self.saver.save_name
        seq_file = self.sequencer.seq_file

        log_str = "(%s) Ran {'%s'}, saved ['%s']." % (now_time, seq_file, save_name)
        return log_str
    
    def logSavedFile(self):
        log_str = self._getSaveLogStr()
        self.insertTextLog(log_str)
        
    def checkDeviceSweep(self, check):
        """
        Devcie sweep and saving individual run cannot be simuntaneous.
        """
        if check:
            self.CHBOX_individual.setChecked(False)
            
    def checkIndividualSave(self, check):
        """
        Devcie sweep and saving individual are not compatible.
        """
        if check:
            self.CHBOX_sweep.setChecked(False)
        
        
class SaveRunner(QThread):
    
    save_name = ""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.individual_flag = False
        self.sweep_flag = False
        self.status = "standby"
        
    def run(self):
        self.status = "running"
        file_path = self.parent.TXT_data_path.text()
        file_name = self.parent.TXT_data_filename.text()
        
        self.saveDataFile(file_path, file_name, self.data)
        self.status = "standby"
        
    def getData(self, data):
        self.data = data
            
        
    def saveDataFile(self, file_path, file_name, data):
        save_name = file_path + '/' + file_name
        if self.sweep_flag:
            device = self.parent.CBOX_device.currentText()
            param = self.parent.CBOX_parameter.currentText()
            value = self.parent.sweep_run_list[self.parent.sweep_run_num-1]
            if int(value*1e6) - float(value*1e6) > 1e-3:
                save_name += "_%s_%s_%.9f" % (device, param, value)
            if int(value*1e3) != float(value*1e3) > 1e-3:
                save_name += "_%s_%s_%.6f" % (device, param, value)
            else:
                save_name += "_%s_%s_%.3f" % (device, param, value)
        
        if not file_name[-4:] == ".pkl":
            save_name += '.pkl'
            
        save_idx = 1
        if os.path.isfile(save_name):
            save_name = save_name[:-4] + "_%03d" + save_name[-4:]
            
            while os.path.isfile(save_name % (save_idx)):
                save_idx += 1
            save_name = save_name % save_idx
        self.save_path = file_path
        self.save_name = os.path.basename(save_name)
        
        
        save_dict = {}
        param_dict = self.parent.getParametersFromTable()
        
        for key, val in param_dict.items():
            save_dict[key] = val
        save_dict["data"] = data
        
        with open (save_name, 'wb') as fw:
            pickle.dump(save_dict, fw)
        
        
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    sr = RunnerPanel(theme='black')
    sr.changeTheme('black')
    sr.show()