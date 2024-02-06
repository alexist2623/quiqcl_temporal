# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 22:51:42 2023

@author: Junho Jeong
"""

import os, sys
from ui_resources.RF_client_device_indicator import DeviceIndicator
from configparser import ConfigParser

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)

sub_file_path = dirname + "/ui_resources"
main_ui_file = sub_file_path + "/RF_controller_main_ui.ui"
ref_ui_file = sub_file_path + "/sub_widgets/channel_refbox_ui.ui"
channel_ui_file = sub_file_path + "/sub_widgets/channel_groupbox_ui.ui"

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout

widget_dir = dirname + "/../../gui/libraries/widgets/"
sys.path.append(widget_dir)
from QSliderSlow_v1 import QSliderSlow

import numpy as np
from RF_client_theme import RF_client_theme_base

main_ui, _ = uic.loadUiType(main_ui_file)
ref_ui,  _ = uic.loadUiType(ref_ui_file)
channel_ui,  _ = uic.loadUiType(channel_ui_file)

version = "v2.2"


def Vpp_to_dBm(vpp):
    dBm = 20*np.log10(vpp/np.sqrt(8)/(0.001 * 50)**0.5)
    return dBm


class RF_ControllerGUI(QtWidgets.QMainWindow, RF_client_theme_base, main_ui):
    
        
    def __init__(self, parent=None, device_dict={}):
        QtWidgets.QMainWindow.__init__(self)
        self.controller = parent
        self.setupUi(self)
        self.panel_dict = {}
        self._di_dict = {}
        
        self.setWindowTitle("RF_Interface_%s" % version)
        self._readConfig()

        
    def _initUi(self, device_dict):
        for device_name, device_params in device_dict.items():
            
            if not device_name in self.panel_dict.keys():
                layout = QVBoxLayout()
                layout_widget = QtWidgets.QWidget()
                layout_widget.setLayout(layout)
                
                curr_dev = RF_ChannelWidget(self, device_name, device_dict[device_name], self.rf_config, self._theme)
                layout.addWidget(curr_dev)
                
                self.tabWidget.addTab(layout_widget, device_name.upper())
                di = DeviceIndicator(self, device_name, device_dict[device_name], self._theme)
                di.createLabel(self.IndicatorLayout)

                curr_dev.sigOutputChanged.connect(di.checkDeviceOutput)
                self.panel_dict[device_name] = curr_dev
                self._di_dict[device_name] = di
                
    def _readConfig(self, config_file=""):
        if config_file == "":
            config_file = dirname + "/RF_settings.conf"
            
        if os.path.isfile(config_file):
            self.LE_config.setText(os.path.abspath(config_file))
            self.rf_config = ConfigParser()
            self.rf_config.read(config_file)
        else:
            self.rf_config = None
            self.toStatusBar("No config file has been found.")
        
            
    def updateGUI(self, device:str, cmd:str, data:list):
        if device == "RF": # Upper level
            if cmd == "CON":
                self._initUi(self.controller.RF_dict)
                
        elif device in self.controller.RF_dict.keys():
            self.panel_dict[device].updateGUI(cmd, data)
            
        else:
            self.toStatusBar("what")
                
    def pressedConButton(self, flag):
        if flag:
            if not self.controller.sck.socket.isConnected:
                self.toStatusBar("The main client is not connected yet.")
                self.BTN_connect.setChecked(False)
            self.controller.connectRF()
        else:
            self.controller.disconnectRF()

    def pressedUpdateButton(self):
        try:
            config_file = self.LE_config.text()
            self._readConfig(config_file)
        except Exception as ee:
            self.toStatusBar("An exception while loading the config file. (%s)" % ee)
            print(ee)
        
    def pressedOpenButton(self):
        conf_file = self.LE_config.text()
        # txt_program = "notepad.exe"
        os.startfile(conf_file)
        
    def toStatusBar(self, msg, time_to_show=5000):
        self.statusbar.showMessage(msg, time_to_show)
        
        
        
#%%        
        
class RF_ChannelWidget(QtWidgets.QWidget, channel_ui):
    

    _default_stylesheet = ""
    _not_updated_stylesheet = "background-color:rgb(255, 255, 0)"
    sigOutputChanged = pyqtSignal()
    
    key_dict = {"o": "out",
                "p": "power",
                "f": "freq",
                "ph": "phase",
                "maxp": "max_power",
                "minp": "min_power",
                "maxf": "max_freq",
                "minf": "min_freq"}
    
    
    def ignore_when_hidden(func):
        """
        It writes logs when an exception happens.
        """
        def wrapper(self, *args, **kwargs):
            if self.isVisible():
                try:
                    return func(self, *args, **kwargs)
                except Exception as err:
                    print("An error ['%s'] occured while handling ['%s']." % (err, func.__name__))
        return wrapper
    
    
    def __init__(self, parent=None, device_name="", device_settings=None, config=None, theme="black"):
        QtWidgets.QWidget.__init__(self)
        self.main_gui = parent
        self.device_name = device_name
        self.device = device_settings
        self.config = config
        self.controller = self.main_gui.controller
        self._theme = theme
        
        self.isUiInitiated = False
        self.device_channel = 0


        self.setupUi(self)
        self.BTN_oscillo.setVisible(False)
        self._initUi()
        
        self.isUiInitiated = True
        
        self.SLB_p  = QSliderSlow(qslider=self.SLB_power, pressed=self.pressedPowerSliderBar, released=self.editedPower)
        self.SLB_f  = QSliderSlow(self.SLB_freq, self.pressedFreqSliderBar)
        self.SLB_ph = QSliderSlow(self.SLB_phase, self.pressedPhaseSliderBar)
        
        self._power_list_vpp = np.linspace(0.02, 0.2, 100)
        self._power_list_dBm = Vpp_to_dBm(self._power_list_vpp)
        
    def pressedPowerSliderBar(self, value_delta:int):
        power_idx = self.SLB_power.value()
        power_dBm = self._power_list_dBm[power_idx]
        self.updatePower(power_dBm)
        
        
    def pressedFreqSliderBar(self, value_delta:int):
        freq = self.SPB_freq.value() + value_delta*self.SPB_freq_step.value()
        self.SPB_freq.setValue(freq)
        self.editedFreq()
        
    def pressedPhaseSliderBar(self, value_delta:int):
        print(value_delta)
        

    def readConfig(self):
        if self.device_name in self.config.sections():
            
            config_options = self.config.options(self.device_name)
        
            for ch in range(len(self.device.settings)):
                if "ch%d" % (ch+1) in config_options:
                    channel_name = self.config.get(self.device_name, "ch%d" % (ch+1))
                    item_idx = self.CBOX_channel.findText(("ch%d" % (ch+1)).upper())
                    if not item_idx == -1: # found the item
                        self.CBOX_channel.setItemText(item_idx, channel_name)
                    
            if "oscillo" in config_options:
                 self.BTN_oscillo.setVisible(True)
                 self.BTN_oscillo.clicked.connect(self.openOscilloScope)
                 
            if "power_unit" in config_options:
                power_unit = self.config.get(self.device_name, "power_unit")
                if power_unit in ["vpp", "Vpp"]:
                    self.CBOX_power.setCurrentIndex(0)
                elif power_unit in ["dbm", "dBm"]:
                    self.CBOX_power.setCurrentIndex(1)
                else:
                    self.CBOX_power.setCurrentIndex(2)
                    
            if ("frequency_unit" in config_options) or ("freq_unit" in config_options): 
                frequency_unit = self.config.get(self.device_name, "frequency_unit")
                if frequency_unit == "kHz":
                    self.CBOX_freq.setCurrentIndex(0)
                elif frequency_unit == "MHz":
                    self.CBOX_freq.setCurrentIndex(1)
                elif frequency_unit == "GHz":
                    self.CBOX_freq.setCurrentIndex(2)
                else:
                    self.toStatusBar("An unknown frequency unit is found. (%s)" % frequency_unit)
                    self.CBOX_freq.setCurrentIndex(1)
                    
            if "curr_channel" in config_options:
                curr_channel = self.config.get(self.device_name, "curr_channel")
                item_idx = self.CBOX_channel.findText(curr_channel)
                if not item_idx == -1: # found the item
                    self.CBOX_channel.setCurrentIndex(item_idx)
                    self.device_channel = item_idx
                    
            for ch in range(len(self.device.settings)):
                if "max_power_ch%d" % (ch+1) in config_options:
                    max_power = float(self.config.get(self.device_name, "max_power_ch%d" % (ch+1)))
                    self.device.settings[ch]["max_power"] = max_power
                

    def _initUi(self):
        for ch in range(len(self.device.settings)):
            channel_name = "CH%d" % (ch+1)
            self.CBOX_channel.addItem(channel_name)
        
        if self.config:
            self.readConfig()
                     
            
        self.CBOX_channel.currentIndexChanged.connect(self.changedChannel)
        self.CBOX_channel.setVisible(len(self.device.settings) > 1) # if the device has a single channel, it hides the combobox.
        
        self.CBOX_power.currentTextChanged.connect(self.changedPowerUnit)
        self.CBOX_freq.currentTextChanged.connect(self.changedFreqUnit)
        self.CBOX_phase.currentTextChanged.connect(self.changedPhaseUnit)
        
        self._interaction_objects = [self.SPB_power, self.SPB_freq, self.SPB_phase,
                                     self.SLB_power, self.SLB_freq, self.SLB_phase,
                                     self.BTN_lock, self.BTN_on]
        

    def showEvent(self, evt):
        if self.isUiInitiated:
            self.updateAllParameters()
            
            
    def updateAllParameters(self):
        con_flag = self.device.isConnected
        self.BTN_connect.setChecked(con_flag)
        self.enableInteractionObjects(con_flag)
        for key in self.device.settings[0].keys():
            self.updateParametersByKey(key)
            
        self.setSliderBarPowerLimits()
                
    def updateParametersByKey(self, key):
        if key in self.key_dict.keys():
            key = self.key_dict[key]

        ch = self.device_channel
        value = self.device.settings[ch][key]
        
        if not value == None:
            if key == "out":
                self.updateOutput(value)
            elif key == "power":
                self.updatePower(value)
            elif key == "freq":
                self.updateFreq(value)
            elif key == "phase":
                self.updatePhase(value)
            elif key == "min_power":
                self.setPowerLimit(key, value)
            elif key == "max_power":
                self.setPowerLimit(key, value)
            elif key == "min_freq":
                self.setFreqLimit(key, value)
            elif key == "max_freq":
                self.setFreqLimit(key, value)
            else:
                pass
        
        if key == "out":
            self.sigOutputChanged.emit()
                
                
    def setPowerLimit(self, key, value):
        if not value == None:
            if self.CBOX_power.currentText() == "Vpp":
                p_value = self.dBm_to_vpp(value)
            elif self.CBOX_power.currentText() == "mW":
                p_value = self.dBm_to_mW(value)
            else:
                p_value = value
            
            if key == "min_power":
                self.SPB_power.setMinimum(p_value)
            else:
                self.SPB_power.setMaximum(p_value)
                
            self.setSliderBarPowerLimits()
            
    def setFreqLimit(self, key, value):
        if not value == None:
            if self.CBOX_freq.currentText() == "kHz":
                f_value = value/1000
            elif self.CBOX_freq.currentText() == "MHz":
                f_value = value/1000000
            else:
                f_value = value/1000000000
                
            if key == "min_freq":
                self.SPB_freq.setMinimum(f_value)
            else:
                self.SPB_freq.setMaximum(f_value)
        

    def updateGUI(self, cmd:str, data=[]):
        if cmd == "STAT":
            self.updateAllParameters()
            self.readConfig()
        elif cmd in ["c", "con"]:
            flag = data[0]
            self.BTN_connect.setChecked(flag)
            if flag:
                self.toStatusBar("Connected to the device (%s)." % self.device_name)
            else:
                self.toStatusBar("Disonnected from the device (%s)." % self.device_name)
            self.enableInteractionObjects(flag)
        elif cmd == "g":
            flag = data[0]
            self.disableWhileUpdating(flag)
        elif cmd == "e":
            if data[0] == "con":
                self.toStatusBar("Could not connect to the device! (%s)" % self.device_name)
                self.BTN_connect.setChecked(False)
        elif cmd == "l":
            flag = data[0]
            self.BTN_lock.setChecked(flag)
        else:
            self.updateParametersByKey(cmd)
            
    def toStatusBar(self, msg, time=5000):
        self.main_gui.toStatusBar(msg, time)
        
    def changedChannel(self, channel:int):
        self.device_channel = channel
        self.SLB_freq.setValue(5)
        self.updateAllParameters()
        
    def disableWhileUpdating(self, flag):
        self.SPB_power.setEnabled(not flag)
        self.SLB_power.setEnabled(not flag)
        self.BTN_on.setEnabled(not flag)
    
    @ignore_when_hidden
    def updateOutput(self, flag):
        self.BTN_on.setChecked(flag)
            
    @ignore_when_hidden
    def updatePower(self, value):
        if self.CBOX_power.currentText() == "Vpp":
            p_value = self.dBm_to_vpp(value)
        elif self.CBOX_power.currentText() == "mW":
            p_value = self.dBm_to_mW(value)
        else:
            p_value = value
        self.SPB_power.setValue(p_value)
        self.SPB_power.setStyleSheet(self._default_stylesheet)
        
        if not self.SLB_p.isActivated:
            slb_idx = np.argmin( np.abs( self._power_list_dBm - value) )
            self.SLB_power.setValue(slb_idx)
        
    @ignore_when_hidden
    def updateFreq(self, value):
        if self.CBOX_freq.currentText() == "kHz":
            f_value = value/1e3
        elif self.CBOX_freq.currentText() == "MHz":
            f_value = value/1e6
        elif self.CBOX_freq.currentText() == "GHz":
            f_value = value/1e9
            
        self.SPB_freq.setValue(f_value)
        self.SPB_freq.setStyleSheet(self._default_stylesheet)
        
    @ignore_when_hidden
    def updatePhase(self, value):
        self._phase = value
        self.SPB_phase.setValue(self._phase)
        self.SPB_phase.setStyleSheet(self._default_stylesheet)
        
    def saveSpinBoxStyleSheet(self, stylesheet):
        self._stylesheet = stylesheet
    
    def editedPower(self):
        p_value = self.SPB_power.value()
        if self.CBOX_power.currentText() == "Vpp":
            power = self.vpp_to_dBm(p_value)
        elif self.CBOX_power.currentText() == "mW":
            power = self.mW_to_dBm(p_value)
        else:
            power = p_value
            
        min_power = self.device.settings[self.device_channel]["min_power"]
        max_power = self.device.settings[self.device_channel]["max_power"]
        
        power = max( min_power, min( max_power, power ) )

        
        if not np.round(self.device.settings[self.device_channel]["power"], 3) == power:
            self.controller.setPower(self.device_name, self.device_channel, power)
            self.SPB_power.setStyleSheet(self._not_updated_stylesheet)
        else:
            self.SPB_power.setStyleSheet(self._default_stylesheet)
        

    def changedPowerUnit(self, unit:str):
        power = self.device.settings[self.device_channel]["power"]
        min_power = self.device.settings[self.device_channel]["min_power"]
        max_power = self.device.settings[self.device_channel]["max_power"]
        if not power == None:
            if unit == "Vpp":
                p_value = self.dBm_to_vpp(power)
            elif unit == "dBm":
                p_value = power
            elif unit == "mW":
                p_value = self.dBm_to_mW(power)
            self.setPowerLimit("min_power", min_power)
            self.setPowerLimit("max_power", max_power)
            
            self.SPB_power.setValue(p_value)
            self.SPB_power.setStyleSheet(self._default_stylesheet)
            
    def editedFreq(self):
        f_value = self.SPB_freq.value()
        if self.CBOX_freq.currentText() == "kHz":
            freq = f_value*1e3
        elif self.CBOX_freq.currentText() == "MHz":
            freq = f_value*1e6
        elif self.CBOX_freq.currentText() == "GHz":
            freq = f_value*1e9
            
        min_freq = self.device.settings[self.device_channel]["min_freq"]
        max_freq = self.device.settings[self.device_channel]["max_freq"]
        
        freq = max( min_freq, min( max_freq, freq ) )

        if not np.round(self.device.settings[self.device_channel]["freq"], 3) == freq:
            self.controller.setFrequency(self.device_name, self.device_channel, freq)
            self.SPB_freq.setStyleSheet(self._not_updated_stylesheet)
        else:
            self.SPB_freq.setStyleSheet(self._default_stylesheet)
            
    def editedPhase(self):
        ph_value = self.SPB_phase.value()
        if self.CBOX_phase.currentText() == "degree":
            phase = ph_value
        elif self.CBOX_phase.currentText() == "radian":
            phase = ph_value/180*np.pi
        
        if not np.round(self.device.settings[self.device_channel]["phase"], 3) == phase:
            self.controller.setPhase(self.device_name, self.device_channel, phase)
            self.SPB_phase.setStyleSheet(self._not_updated_stylesheet)
        else:
            self.SPB_phase.setStyleSheet(self._default_stylesheet)        
        
        
    def changedPowerStep(self, step):
        self.SPB_power.setSingleStep(step)
                
    def changedFreqStep(self, step):
        self.SPB_freq.setSingleStep(step)
        
    def changedPhaseStep(self, step):
        self.SPB_phase.setSingleStep(step)

    def changedFreqUnit(self, unit:str):
        freq = self.device.settings[self.device_channel]["freq"]
        
        if not freq == None:
            if unit == "kHz":
                divider = 1e3
            elif unit == "MHz":
                divider = 1e6
            elif unit == "GHz":
                divider = 1e9
                
            self.setFreqLimit("min_freq", self.device.settings[self.device_channel]["min_freq"])
            self.setFreqLimit("max_freq", self.device.settings[self.device_channel]["max_freq"])
    
            self.SPB_freq.setValue(freq/divider)
            self.SPB_freq.setStyleSheet(self._default_stylesheet)
            
    def changedPhaseUnit(self):
        phase = self.device.settings[self.device_channel]["phase"]
        
        if phase:
            if self.CBOX_phase.currentText == "degree":
                ph_value = phase
            elif self.CBOX_phase.currentText == "radian":
                ph_value = ph_value/180*np.pi
            self.SPB_phase.setValue(ph_value)
            self.SPB_phase.setStyleSheet(self._default_stylesheet)


    def dBm_to_vpp(self, dBm):
        volt = 2*np.sqrt((100)/1000)*10**(dBm/20)
        return volt
        
    def vpp_to_dBm(self, vpp):
        dBm = 20*np.log10(vpp/np.sqrt(8)/(0.001 * 50)**0.5)
        return dBm
    
    def dBm_to_mW(self, dBm):
        mW = 10**(dBm/10)
        return mW
    
    def mW_to_dBm(self, mW):
        dBm = 10*np.log10(mW)
        return dBm
    
    def pressedPowerButton(self, flag):
        if not flag: # The power should be minimized before the output is turned off.
            self.controller.setPower(self.device_name, self.device_channel, self.device.settings[self.device_channel]["min_power"])
        self.controller.setOutput(self.device_name, self.device_channel, flag)

            
    def setSliderBarPowerLimits(self):
        ch = self.device_channel
        min_power_dbm = self.device.settings[ch]["min_power"]
        max_power_dbm = self.device.settings[ch]["max_power"]
        
        min_power_vpp = self.dBm_to_vpp(min_power_dbm)
        max_power_vpp = self.dBm_to_vpp(max_power_dbm)
        
        self._power_list_vpp = np.linspace(min_power_vpp, max_power_vpp, 100)
        self._power_list_dBm = self.vpp_to_dBm(self._power_list_vpp)
        
    def pressedConnect(self, flag):
        if flag:
            self.controller.openDevice(self.device_name)
        else:
            self.controller.closeDevice(self.device_name)
            
    def pressedLockButton(self, flag):
        unit = self.CBOX_ref.currentText()
        if unit == "MHz":
            multiplier = 1e6
        elif unit == "GHz":
            multiplier = 1e9
        frequency = self.SPB_ref.value()*multiplier
        if self.RDO_Internal.isChecked():
            flag = not flag
        self.controller.setLock(self.device_name, flag, frequency)
        
    def enableInteractionObjects(self, flag):
        for obj in self._interaction_objects:
            obj.setEnabled(flag)
            
    def openOscilloScope(self):
        if not "OSC" in self.__dict__:
        
            sys.path.append(sub_file_path + "/sub_widgets/")
            from Oscillo_scope_gui_v0_04 import DS1052E_GUI
            self.OSC = DS1052E_GUI(self, self._theme)    
            self.OSC.changeTheme(self._theme)
    
            if self.device_name == "ea_rf":
                self.OSC.CBOX_chamber.setCurrentIndex(1)
            else:
                self.OSC.CBOX_chamber.setCurrentIndex(0)
                
        self.OSC.raise_()
        self.OSC.activateWindow()
        self.OSC.showNormal()



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    if app is None:
        app = QtWidgets.QApplication([])
    temp_device_dict = {"EA_RF": {"num_ch": 2},
                        "EC_RF": {"num_ch": 2},
                        "EOM_7G": {"num_ch": 1}}
    RF = RF_ControllerGUI(None, temp_device_dict)
    RF.setWindowTitle("RF GUI v2")
    RF.show()