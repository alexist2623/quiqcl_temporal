# -*- coding: utf-8 -*-
"""
Created on Thu May 20 17:31:08 2021

@author: thkim
"""
import random
import time

class DummyLaser:
    def __init__(self, laser_name, initial_frequency):
        self.volt_to_freq_ratio = 0.0001
        self.laser_name = laser_name
        self.frequency = initial_frequency

        # Error model
        self.charScale = 0.000005 #1e-6
        self.lastAccessTime = -1
        self.driftSlope = 0
        
    def set_by_DAC_voltage(self, voltage):
        # print("set by dac voltage called - voltage before set freq :", self.frequency)
        self.setFrequency(self.frequency + (voltage-1.25) * self.volt_to_freq_ratio, time.time())
        # print("set by dac voltage returned - voltage after set freq :", self.frequency)

    ### Return frequency with error applied    
    def getFrequency(self):
        # print("getFrequency called with", str(self.frequency))
        currentTime = time.time()
        self.setFrequency(self.frequency + self.getError(currentTime), currentTime)
        # print("getFrequency returned with", str(self.frequency))
        return self.frequency
    
    ### Update frequency and lastAccessTime
    def setFrequency(self, newFreq, accessTime):
        self.frequency = newFreq
        self.lastAccessTime = accessTime

    def getError(self, currentTime):
        dice = random.random()
        
        ### first measurement or too long time passed after the last measurement
        ### re-determine the drift slope
        if(self.lastAccessTime == -1 or currentTime-self.lastAccessTime > 60):
            self.driftSlope = (6*random.random() - 3) * self.charScale  # -0.00003 ~ 0.00003
            return self.charScale * random.random() * 0.001

        ### apply drift model
        else:
            ### change drift model with 1% probability
            if(dice < 0.05):
                self.driftSlope = (6*random.random() - 3) * self.charScale  # -0.00003 ~ 0.00003
            return (currentTime - self.lastAccessTime) * self.driftSlope
        
    
# PRINT "[i] : [current_frequency]" for debuggin
def main():
    dummylaser = DummyLaser('369nm', 320.57197)
    for i in range(0, 2999):
        print(str(i), dummylaser.getFrequency())
        i += 1
        time.sleep(0.05)

if __name__ == '__main__':
    main()
    
        
        