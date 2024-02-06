# -*- coding: utf-8 -*-
"""
Created on Sat Jul  1 13:57:25 2023

@author: Junho Jeonng
version: v1.1

Note: 
    v1.0: The "each" wrapper class creates a QTimer object, which is wasteful from the perspective of resources.
          Given that the user interacts with a single QSliderbar at a time, QTimer can be shared.
    v1.1: It inherits a QTimer from the outside. If the QTimer is declared as a None object, it creates one.
          If you call the wrapper class, then it returns the qslider object, which can be used to create a GUI.
"""
from PyQt5.QtCore import QObject, pyqtSignal


debug = True

class QSliderSlow(QObject):
    """
    This class wrapper enables a slow interaciton of the QSliderBar.
    Inputs: 
        qslider: an existing qslider (that you want to eanble the slow interaction, which is you already created in the script or on the gui.)
        method: a method that you want to execute when the value of the qslider is changed. The method must take an input of the value delta.
        sig_interval: The minimum interaction time in seconds. 0.5s is the default value
        debug: a debug flag that prints the value of the qslider when it is True.
    """
    
    sig_value_delta = pyqtSignal(int)
    
    def __init__(self, qslider=None, pressed=None, released=None, sig_interval=0.5, debug=False, qtimer=None):
        super().__init__()
        
        self.qslider = qslider
        self.pressedMethod = pressed
        self.releasedMethod = released
        
        self.debug = debug
        
        if not self.qslider:
            from PyQt5.QtWidgets import QSliderBar
            self.qslider = QSliderBar()
            print("No qsliderbar is inherited. It automatically created one.")
        
        self.qslider.sliderPressed.connect(self._pressedEvent)
        self.qslider.sliderReleased.connect(self._releasedEvent)
        
        self.sig_interval = sig_interval
        
        if qtimer:
            self.delay_timer = qtimer
        else:
            from PyQt5.QtCore import QTimer
            self.delay_timer = QTimer()
            
        self.setInterval(self.sig_interval)
        self.delay_timer.timeout.connect(self._executeFunction)
        
        self.previous_value = 0
        self.sig_value_delta.connect(self.pressedMethod)
        
    def __call__(self):
        return self.qslider
                
    @property
    def isActivated(self):
        return self.delay_timer.isActive()

        
    def setInterval(self, interval):
        self.sig_interval = interval
        self.delay_timer.setInterval( int(self.sig_interval*1000) )
        
    def _pressedEvent(self):
        self.delay_timer.start()
        
    def _releasedEvent(self):
        self.delay_timer.stop()
        self._executeFunction()
        if self.releasedMethod:
            self.releasedMethod()
        
    def _executeFunction(self, *args):
        self.sig_value_delta.emit(self.qslider.value() - self.previous_value)
        self.previous_value = self.qslider.value()
        if self.debug:
            self._printValue()
        
    def _printValue(self):
        print(self.qslider.value())
        
    