# -*- coding: utf-8 -*-
"""
Created on Sat Aug 21 23:22:02 2021

Author: JHJeong32
"""
import os
version = "1.1"

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

# PyQt libraries
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QFileDialog

from main_panel_theme import main_panel_theme_base
main_ui_file = dirname + "/main_panel.ui"
main_ui, _ = uic.loadUiType(main_ui_file)

class MainPanel(QtWidgets.QMainWindow, main_ui, main_panel_theme_base):
    
    num_switches = 12
    switch_button_list = []
    switch_label_list = []
    user_update = True
    user_run_flag = False # This flag is to distinguish whether the Sequencer is running by itself.
    latest_button_dict = {}
    
    slider_user_interaction_flag = [False, False] # This is not to be updated while the user handling the slider.

    
    def closeEvent(self, e):
        self.parent.socket.breakConnection(True)
    
    def __init__(self, device_dict={}, parent=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.device_dict = device_dict
        self.parent = parent
        self._theme = theme
        self._initUi()
        
    def _initUi(self):
        self.TXT_ip.setText(self.parent.cp.get("win_server", "ip"))
        self.TXT_port.setText(self.parent.cp.get("win_server", "port"))
        self.TXT_config.setText(self.parent.cp.get("client", "conf_file"))
        
        for idx_switch_button in range(self.num_switches):
            switch_button = getattr(self, "BTN_switch__%d" % idx_switch_button)
            switch_button.toggled.connect(self.buttonSwitchPressed)
            switch_label = getattr(self, "EXP_switch__%d" % idx_switch_button)
            self.switch_button_list.append(switch_button)
            self.switch_label_list.append(switch_label)
            
        # for srv section in the panel
        self.srv_disable_list = [self.BTN_load_config,
                                 self.TXT_config,
                                 self.TXT_ip,
                                 self.TXT_port]
            
        # for dds sections in the panel
        if "dds" in self.parent.cp.sections():
            self.device_dict["dds"].sig_update_callback.connect(self._updateDDSSection)
            try:
                self.main_board_channel = int(self.parent.cp.get("dds", "main_board_channel"))
                if "ch1_max_power" in self.parent.cp.options("dds"):
                    max_value = int(self.parent.cp.get("dds", "ch1_max_power"))
                    self.SLD_CH1_curr.setMaximum(max_value)
                    self.SLD_CH1_curr.setTickInterval(int(max_value/10))
                if "ch2_max_power" in self.parent.cp.options("dds"):
                    max_value = int(self.parent.cp.get("dds", "ch2_max_power"))
                    self.SLD_CH2_curr.setMaximum(max_value)
                    self.SLD_CH2_curr.setTickInterval(int(max_value/10))
            except Exception as e:
                self.toStatusBar("An error happened while reading a dds setting. (%s)" % e)
                
                
        # for sequencer section in the panel
        if 'sequencer' in self.device_dict.keys():
            self.sequencer = self.device_dict['sequencer']
            
            self.TXT_serial.setText(self.sequencer.ser_num)
            self.TXT_com.setText(self.sequencer.com_port)
            
            self.sequencer.sig_dev_con.connect(self.changeFPGAconn)
            self.sequencer.sig_seq_complete.connect(self._completeProgress)
            self.sequencer.sig_occupied.connect(self._restoreSwitches)
            
        # for dac sections in the panel
        if "dac" in self.parent.cp.sections():
            self.dac_textbox_list = []
            self.device_dict["dac"].sig_update_callback.connect(self._updateDACSection)
            self.dac_num_channel = 16
            for ch_idx in range(self.dac_num_channel):
                item = getattr(self, "TXT_ELEC_%d" % ch_idx)
                item.returnPressed.connect(self.changedDACVoltage)
                self.dac_textbox_list.append(item)
            
    #%% Buttons
    def buttonSRVCONPressed(self, flag):
        if flag:
            con_status = self.parent.makeConnection(self.TXT_ip.text(), int(self.TXT_port.text()))
            
            if con_status == -1:
                self.BTN_srv_connect.setChecked(False)
                self.toStatusBar("Unable to connect to the server.")
                return
            
            else:
                for obj in self.srv_disable_list:
                    obj.setEnabled(False)
        else:
            if self.BTN_dds_connect.isChecked():
                self.BTN_dds_connect.setChecked(False)
            self.parent.breakConnection()
            for obj in self.srv_disable_list:
                obj.setEnabled(True)
                    
    def buttonScanPressed(self):
        ser_num = self.TXT_serial.text()
        com_port = self.sequencer.getComPort(ser_num)
        
        if com_port == None:
           self.TXT_com.setText("")
        else:
            self.TXT_com.setText(com_port)
            self.sequencer.com_port = com_port
            self.toStatusBar("Scanned FPGA.")

    def buttonFPGACONPressed(self, flag):
        if self.user_update:
            if flag:
                com_port = self.TXT_com.text()
                open_flag = self.sequencer.openDevice(com_port)
                if open_flag == -1:
                    self.toStatusBar("Failed to open the FPGA.")
                    self.changeFPGAconn(False)
                    return
            else:
                self.sequencer.closeDevice()
        self.setupSwitches(flag)
        
    def buttonHardwareDefinitionPressed(self):
        try:
            self.sequencer.openHardwareDefinitionFile()
        except Exception as ee:
            self.toStatusBar("An error while opening the hardware definition file. (%s)" % ee)
        
            
    def buttonConfigPressed(self):
        config_file = QFileDialog.getOpenFileName(self, 'Open .ini file.',
                                                  os.path.basename(self.TXT_config.text()), 'ini files(*.ini)')[0]
        self.loadConfig(config_file)
        
       
    def buttonSwitchPressed(self):
        if self.device_dict["sequencer"].is_opened:
            if self.user_update:
                for idx in range(len(self.key_list)):
                    switch_flag = self.switch_button_list[idx].isChecked()
                    switch_out = self.switch_button_list[idx].text()
                    
                    self.latest_button_dict[switch_out] = switch_flag
                    
                self._runButtonSequencer(self.latest_button_dict)

                
    def _runButtonSequencer(self, button_dict):
        self.user_run_flag = True

        replace_string_list = []
        for switch_out, switch_flag in button_dict.items():
            replace_string = "(hd.%s, %d)" % (switch_out, switch_flag)
            replace_string_list.append(replace_string)
        replace_string = ",".join(replace_string_list)
        
        file_string = self._getReplacedFileString(replace_string)
        self.sequencer.spontaneous = True
        self.sequencer._executeFileString(file_string)
        self.sequencer.runSequencerFile()
        self.sequencer.spontaneous = False
            
    def _getReplacedFileString(self, replace_string):
        file_string = ''
        seq_file = dirname + '/sequencer/' + 'Switch_sequencer_base.py'
        with open (seq_file) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if " as hd\n" in line:
                    line = "import %s as hd\n" % self.sequencer.hw_def
                if "Will_be_replaced_line" in line:
                    line = "s.set_output_port(hd.external_control_port, [%s])" % replace_string
                file_string += line
        return file_string
                
    #%%
    def loadConfig(self, config_file):
        from configparser import ConfigParser
        cp  = ConfigParser()
        try:
            cp.read(config_file)
        except:
            self.toStatusBar("Couldn't read the config file.")
            return
        
        self.TXT_ip.setText(cp.get("server", "ip"))
        self.TXT_port.setText(cp.get("server", "port"))
        self.TXT_config.setText(config_file)
        self.toStatusBar("Loaded a config file.")
        
    def setupSwitches(self, flag):
        if flag:
            FPGA = self.device_dict["sequencer"]
            key_list = list(FPGA.hd.output_mapping.keys())
            self.key_list = key_list
            for idx in range(self.num_switches):
                desc_text = ""
                
                if idx < len(key_list):
                    key = key_list[idx]
                    self.switch_button_list[idx].setText(key + "_out")

                    if "description" in FPGA.hd.__dict__.keys():
                        desc_text += FPGA.hd.description[key] + "\n"
                    desc_text += "(%s)" % FPGA.hd.output_mapping[key]

                else:
                    self.switch_button_list[idx].setVisible(False) # set undefined buttons invisible
                self.switch_label_list[idx].setText(desc_text)
                    
        else:
            for idx in range(self.num_switches):
                self.switch_button_list[idx].setVisible(True)
                self.switch_button_list[idx].setChecked(False)
                self.switch_button_list[idx].setText("PushButton")
                self.switch_label_list[idx].setText("TextLabel")
        
    def toStatusBar(self, message):
        if not self.parent == None:
            self.parent.toStatusBar(message)
        else:
            print(message)
             
    #%% DDS control
    def buttonDDSCONPressed(self, flag):
        if self.BTN_srv_connect.isChecked():
            if flag:
                if self.device_dict["dds"].gui == None:  # This logic should be changed. This is just absurd
                    self.device_dict["dds"].openGui()
                self.device_dict["dds"].openDevice()
            else:
                self.device_dict["dds"].closeDevice()
                
        else:
            self.BTN_dds_connect.setChecked(False)
            self.toStatusBar("You must connect to the server first.")
    
    def sliderDDSPressed(self):
        if self.sender() == self.SLD_CH1_curr:
            self.slider_user_interaction_flag[0] = 1
        else:
            self.slider_user_interaction_flag[1] = 1

    def sliderDDSReleased(self):
        if self.sender() == self.SLD_CH1_curr:
            self.slider_user_interaction_flag[0] = 0
        else:
            self.slider_user_interaction_flag[1] = 0
            
    def _updateDDSSection(self):
        """
        current_settings =
        {1: {'current': [0, 0], 'freq_in_MHz': [0, 0], 'power': [0, 0]},
         2: {'current': [0, 0], 'freq_in_MHz': [0, 0], 'power': [0, 0]}}
        """
        current_settings = self.device_dict["dds"]._current_settings
        board_idx = self.main_board_channel
        self.user_update = False
        
        self.BTN_dds_connect.setChecked(self.device_dict["dds"]._is_opened)
        for setting, value_list in current_settings[board_idx].items():
            if setting == "current":
                for channel, value in enumerate(value_list):
                    if not self.slider_user_interaction_flag[channel]:
                        slider = getattr(self, "SLD_CH%d_curr" % (channel+1))
                        if not value == slider.value():
                            slider.setValue(int(value))
            elif setting == "freq_in_MHz":
                for channel, value in enumerate(value_list):
                    line_edit = getattr(self, "TXT_CH%d_freq" % (channel+1))
                    try: txt_value = float(line_edit.text())
                    except: txt_value = 0
                    
                    if not value == txt_value:
                        line_edit.setText("%.2f" % value)
            elif setting == "power":
                for channel, value in enumerate(value_list):
                    push_button = getattr(self, "BTN_CH%d_power" % (channel+1))
                    if not value == push_button.isChecked():
                        push_button.setChecked(value)
        self.user_update = True
        
    def changeFreq(self):
        if self.user_update:
            if self.BTN_dds_connect.isChecked():
                if self.sender() == self.TXT_CH1_freq:
                    ch1 = 1
                    ch2 = 0
                else: 
                    ch1 = 0
                    ch2 = 1
                
                try: freq_in_MHz = float(self.sender().text())
                except:
                    self.toStatusBar("The frequency value must be a number.")
                    return
                
                self.device_dict["dds"].setFrequency(self.main_board_channel, ch1, ch2, freq_in_MHz)
            else:
                self.sender().setText("0.00")
                self.toStatusBar("You must connect to DDS first.")
        
    def changeCurr(self, curr_value):
        if self.user_update:
            if self.BTN_dds_connect.isChecked():
                if self.sender() == self.SLD_CH1_curr:
                    ch1 = 1
                    ch2 = 0
                else:
                    ch1 = 0
                    ch2 = 1
                
                self.device_dict["dds"].setCurrent(self.main_board_channel, ch1, ch2, curr_value)
            else:
                self.sender().setValue(0)
                self.toStatusBar("You must connect to DDS first.")
                
    def buttonDDSPowerPressed(self, flag):
        if self.BTN_dds_connect.isChecked():
            if self.sender() == self.BTN_CH1_power:
                ch1 = 1
                ch2 = 0
            else:
                ch1 = 0
                ch2 = 1
            
            if flag:
                self.device_dict["dds"].powerUp(self.main_board_channel, ch1, ch2)
            else:
                self.device_dict["dds"].powerDown(self.main_board_channel, ch1, ch2)
        else:
            self.sender().setChecked(False)
            self.toStatusBar("You must connect to DDS first.")
        
    #%% DAC control
    def buttonDACCONPressed(self, flag):
        if self.BTN_srv_connect.isChecked():
            if flag:
                if self.device_dict["dac"].gui == None:
                    self.device_dict["dac"].openGui()
                self.device_dict["dac"].openDevice()
            else:
                self.device_dict["dac"].closeDevice()
        else:
            self.BTN_dac_connect.setChecked(False)
            self.toStatusBar("You must connect to the server first.")
    
    def buttonDACLoadPressed(self):
        if self.BTN_dac_connect.isChecked():
            self.device_dict["dac"].gui.buttonLoadPressed()
        else:
            self.toStatusBar("You must connect to the DAC first.")
    
    def buttonDACSavePressed(self):
        if self.BTN_dac_connect.isChecked():
            self.device_dict["dac"].gui.buttonSavePressed()
        else:
            self.toStatusBar("You must connect to the DAC first.")
    
    def buttonDACResetPressed(self):
        if self.BTN_dac_connect.isChecked():
            self.device_dict["dac"].resetDevice()
        else:
            self.toStatusBar("You must connect to the DAC first.")
    
    
    def changedDACVoltage(self):
        prev_voltage_list = self.device_dict["dac"]._voltage_list
        channel_list = []
        voltage_list = []
        
        for ch_idx in range(len(self.dac_textbox_list)):
            try:
                user_voltage = float(self.dac_textbox_list[ch_idx].text())
                if not prev_voltage_list[ch_idx] == user_voltage:
                    channel_list.append(ch_idx)
                    voltage_list.append(user_voltage)
                    
            except:
                self.toStatusBar("The voltage value must be a number")
        self.device_dict["dac"].setVoltage(channel_list, voltage_list)
                            
    def _updateDACSection(self, sig_str):
        self.user_update = False
        
        if sig_str == "o":
            self.BTN_dac_connect.setChecked(True)
        elif sig_str == "c":
            self.BTN_dac_connect.setChecked(False)
            
        elif sig_str == "r":
            for ch in range(16):
                self.dac_textbox_list[ch].setText("0.00")
            
        elif sig_str == "v":
            voltage_list = self.device_dict["dac"]._voltage_list
            for ch in range(16):
                self.dac_textbox_list[ch].setText("%.2f" % voltage_list[ch])
            
        self.user_update = True

            
    def changeDDSconn(self, flag):
        self.user_update = False
        self.BTN_dds_connect.setChecked(flag)
        self.user_update = True
        
    def changeFPGAconn(self, flag):
        self.user_update = False
        self.BTN_fpga_connect.setChecked(flag)
        if flag:
            if not self.TXT_serial.text() == self.sequencer.ser_num:
                self.TXT_serial.setText(self.sequencer.ser_num)
            if not self.TXT_serial.text() == self.sequencer.com_port:
                self.TXT_com.setText(self.sequencer.com_port)
        self.user_update = True
        
        
    def _completeProgress(self, flag):
        if self.user_run_flag:
            self.user_run_flag = False
        
    def _restoreSwitches(self, occupation_flag):
        if not occupation_flag:
            if not self.user_run_flag:
                for button in self.switch_button_list:
                    button.setEnabled(True)
                    
                self.BTN_fpga_scan.setEnabled(True)
                self.BTN_fpga_connect.setEnabled(True)
                self.user_update = False
                for idx, value in enumerate(self.latest_button_dict.values()):
                    self.switch_button_list[idx].setChecked(value)
                    
                self.user_update = True
                self._runButtonSequencer(self.latest_button_dict)
                
        else:
            if not self.user_run_flag:
                for button in self.switch_button_list:
                    button.setEnabled(False)
                self.BTN_fpga_scan.setEnabled(False)
                self.BTN_fpga_connect.setEnabled(False)
        
        
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    panel = MainPanel()
    panel.show()
    panel.changeTheme('white')

    #app.exec_()
    #sys.exit(app.exec())