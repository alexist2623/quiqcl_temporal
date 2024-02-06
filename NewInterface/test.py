# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 12:29:33 2024

@author: alexi
"""
import functools
import logging
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import requests
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QCheckBox, QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSlider, QVBoxLayout, QWidget
)

import qiwis

logger = logging.getLogger(__name__)

class DDSControllerWidget(QWidget):
    """Single DDS channel controller widget.
    
    Attributes:
        profileWidgets: Dictionary with frequency, amplitude, phase spin box,
          and switching check box.
        attenuationSpinbox: Spin box for setting the attenuation.
        switchButton: Button for turning on and off the TTL switch that controls the output of DDS.

    Signals:
        profileSet(frequency, amplitude, phase, switching):
          The default profile setting is set to frequency in Hz, amplitude, and phase.
          If switching is True, the current DDS profile is set to the default profile.
        attenuationSet(attenuation): Current attenuation setting is set to attenuation.
        switchClicked(on): If on is True, the switchButton is currently checked.
    """

    profileSet = pyqtSignal(float, float, float, bool)
    attenuationSet = pyqtSignal(float)
    switchClicked = pyqtSignal(bool)

    def __init__(
        self,
        name: str,
        device: str,
        channel: int,
        frequencyInfo: Optional[Dict[str, Any]] = None,
        amplitudeInfo: Optional[Dict[str, Any]] = None,
        phaseInfo: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None
    ):  # pylint: disable=too-many-arguments, too-many-locals
        """Extended.
        
        Args:
            name: DDS channel name.
            device: DDS device name.
            channel: DDS channel number.
            frequencyInfo: Dictionary with frequency info. Each key and its value are:
              ndecimals: Number of decimals that can be set. (default=2)
              min, max: Min/Maximum frequency that can be set. (default=1e6, 4e8)
              step: Step increased/decreased through spinbox arrows. (default=1)
              unit: Unit of frequency. It should be one of "Hz", "kHz", and "MHz". (default="Hz")
            amplitudeInfo: Dictionary with amplitude info. Each key and its value are:
              ndecimals: Number of decimals that can be set. (default=2)
              step: Step increased/decreased through spinbox arrows. (default=0.01)
            phaseInfo: Dictionary with phase info. Each key and its value are:
              ndecimals: Number of decimals that can be set. (default=2)
              step: Step increased/decreased through spinbox arrows. (default=0.01)
        """
        super().__init__(parent=parent)
        # profileInfo = profile_info(frequencyInfo, amplitudeInfo, phaseInfo)
        # info widgets
        nameLabel = QLabel(name, self)
        nameLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        deviceLabel = QLabel(device, self)
        deviceLabel.setAlignment(Qt.AlignCenter)
        channelLabel = QLabel(f"CH {channel}", self)
        channelLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # profile widgets
        self.profileWidgets: Dict[str, Union[QDoubleSpinBox, QCheckBox]] = {}
        profileGroupbox = QGroupBox("Profile", self)
        profileLayout = QVBoxLayout(profileGroupbox)
        profileInfoLayout = QHBoxLayout()
        for name_ in ("frequency", "amplitude", "phase"):
            # info = profileInfo[name_]
            info = 'hello!'
            spinbox = self.spinBoxWithInfo(info)
            self.profileWidgets[name_] = spinbox
            profileInfoLayout.addWidget(QLabel(f"{name_}:", self), alignment=Qt.AlignRight)
            profileInfoLayout.addWidget(spinbox)
        profileSetLayout = QHBoxLayout()
        switchingCheckbox = QCheckBox("Switch to this profile", self)
        switchingCheckbox.setChecked(True)
        self.profileWidgets["switching"] = switchingCheckbox
        profileSetLayout.addWidget(switchingCheckbox)
        profileButton = QPushButton("Set", self)
        profileSetLayout.addWidget(profileButton, alignment=Qt.AlignRight)
        profileLayout.addLayout(profileInfoLayout)
        profileLayout.addLayout(profileSetLayout)
        # attenuation widgets
        attenuationBox = QGroupBox("Attenuation", self)
        attenuationLayout = QHBoxLayout(attenuationBox)
        attenuationInfo = {"ndecimals": 1, "min": 0, "max": 31.5, "step": 0.5, "unit": "dB"}
        self.attenuationSpinbox = self.spinBoxWithInfo(attenuationInfo)
        self.attenuationSpinbox.setPrefix("-")
        attenuationButton = QPushButton("Set", self)
        attenuationLayout.addWidget(QLabel("attenuation:", self), alignment=Qt.AlignRight)
        attenuationLayout.addWidget(self.attenuationSpinbox)
        attenuationLayout.addWidget(attenuationButton, alignment=Qt.AlignRight)
        # switch button
        self.switchButton = QPushButton("OFF?", self)
        self.switchButton.setCheckable(True)
        # layout
        infoLayout = QHBoxLayout()
        infoLayout.addWidget(nameLabel)
        infoLayout.addWidget(deviceLabel)
        infoLayout.addWidget(channelLabel)
        layout = QVBoxLayout(self)
        layout.addLayout(infoLayout)
        layout.addWidget(profileGroupbox)
        layout.addWidget(attenuationBox)
        layout.addWidget(self.switchButton)
        # signal connection
        profileButton.clicked.connect(self._profileButtonClicked)
        attenuationButton.clicked.connect(self._attenuationButtonClicked)
        self.switchButton.clicked.connect(self._setSwitchButtonText)

    def spinBoxWithInfo(self, info: Mapping[str, Any]) -> QDoubleSpinBox:
        """Returns a spinbox with the given info.
        
        Args:
            See *Info arguments in self.__init__().
        """
        spinbox = QDoubleSpinBox(self)
        spinbox.setSuffix(info["unit"])
        spinbox.setMinimum(info["min"])
        spinbox.setMaximum(info["max"])
        spinbox.setDecimals(info["ndecimals"])
        spinbox.setSingleStep(info["step"])
        return spinbox

    @pyqtSlot()
    def _profileButtonClicked(self):
        """The profileButton is clicked.
        
        The profileSet signal is emitted with the current frequency, amplitude, phase,
        and switching.
        """
        frequencySpinbox = self.profileWidgets["frequency"]
        unit = {
            "Hz": 1,
            "kHz": 1e3,
            "MHz": 1e6
        }[frequencySpinbox.suffix()]
        frequency = frequencySpinbox.value() * unit
        amplitude = self.profileWidgets["amplitude"].value()
        phase = self.profileWidgets["phase"].value()
        switching = self.profileWidgets["switching"].isChecked()
        self.profileSet.emit(frequency, amplitude, phase, switching)

    @pyqtSlot()
    def _attenuationButtonClicked(self):
        """The attenuationButton is clicked.
        
        The attenuationSet signal is emitted with the current attenuation.
        """
        attenuation = self.attenuationSpinbox.value()
        self.attenuationSet.emit(attenuation)

    @pyqtSlot(bool)
    def _setSwitchButtonText(self, on: bool):
        """Sets the switchButton text.

        Args:
            on: Whether the switchButton is now checked or not.
        """
        if on:
            self.switchButton.setText("ON")
        else:
            self.switchButton.setText("OFF")
        self.switchClicked.emit(on)
        
if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    
    a = DDSControllerWidget('a','b','c')
    a.show()