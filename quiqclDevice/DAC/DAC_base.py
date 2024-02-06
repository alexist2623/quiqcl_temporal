# -*- coding: utf-8 -*-

class DAC_Abstract():    

    """
    This class is an interface for interacting with DAC devices.

    - Every class implementing DAC device should inherit this class.
    - Note that exceptions may occur in each method depending on devices.
    
    """
    _is_opened = False
    _num_channel = 0
    _voltage_range = [0, 0]
    _voltage_list = [0]
    
    def openDevice(self):
        """
        Connect to the device.
        """
        not_implemented('openDevice', self)
        
    def closeDevice(self):
        """
        Disconnect to the device.
        """
        not_implemented('closeDevice', self)
        
    def resetDevice(self):
        """
        Reset all the voltages to 0.
        """
        not_implemented('resetDevice', self)
    
    def setVoltage(self, channel, voltage):
        """
        Set the output voltage of the given channel.
        """
        not_implemented('setVoltage', self)

    def readVoltage(self, channel):
        """
        Read the output voltage of the given channel
        """
        not_implemented('readVoltage', self)
    
def not_implemented(func, obj):
    """Raises NotImplementedError with the given function name.

    This is a helper function, which is NOT included in RFSource class.
    """
    raise NotImplementedError("method '{}' is not supported on device '{}'"
                              .format(func, obj.__class__.__name__))