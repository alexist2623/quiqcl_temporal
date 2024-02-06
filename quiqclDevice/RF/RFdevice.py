"""
Created on Aug 26, 2021.
@author: Jiyong Kang
@Editor: Kyungmin Lee
@Editor: Junho Jeong
This file includes concrete classes implementing actual or virtual RF source device.
Included classes:
    - Windfreak SynthNV(SerialPortRFSource)
"""

import serial, math
import numpy as np
from RFbase import SerialPortRFSource, SocketRFSource


def requires_connection(func):
    """Decorator that checks the connection before calling func.
    Raises:
        RuntimeError - the func is called without connection.
    """
    def wrapper(self, *args, **kwargs):
        if self.is_connected:
            return func(self, *args, **kwargs)
        else:
            raise RuntimeError('{} is called with no connection.'
                               .format(func.__name__))
    return wrapper

def check_range(val, min_, max_, label=None):
    """Checks the given value fits in the range [min_, max_].
    Raises:
        ValueError - val does not fit in the range.
    """
    if val > max_ or val < min_:
        raise ValueError('{}{} is out of range: min={}, max={}.'
                         .format('' if label is None else label + '=',
                                 val, min_, max_))


class WindfreakTech(SerialPortRFSource):
    """
    This class is for Windfreak Tech rf devices which is used for sideband generator.
    All the commands and behaviours are currently based on serial communication manual.

    - Default units
        - power:        dBm
        - frequency:    Hz
        - attenuator:   dBm
    """
    def __init__(self, min_power, max_power, min_freq, max_freq, port=None):
        """
        The serial port can be assigned later by set_port(port_name).
        """
        super().__init__(min_power, max_power, min_freq, max_freq,
                         port=port, baudrate=9600, bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO)
        self.__power = min_power

    def find_nearest_idx(self, array, value):
        return (np.abs(array - value)).argmin()
     
    
class SynthNV(WindfreakTech):
    """
    Power range: [0 63] for [-13.49, +18.55] dBm
    Frequency range: [34e6, 4.5e9] Hz
    """
    def __init__(self, port=None, min_power=-13.49, max_power=18.55, 
                 min_freq=34e6, max_freq=4.5e9):
        assert min_power >= -13.49, 'min_power should be at least 0(-13.49dBm).'
        assert max_power <= 18.55, 'max_power should be at most 63(18.55dBm).'
        assert min_freq >= 34e6, 'min_frequency should be at least 34MHz.'
        assert max_freq <= 4.5e9, 'max_frequency shuold be at most 4500MHz.'
        assert min_power <= max_power, 'min_power is greater than max_power.'
        assert min_freq <= max_freq, 'min_frequency is greater than max_frequency.'
        self.__output_mapping()
        super().__init__(min_power, max_power, min_freq, max_freq, port=port)

    def __output_mapping(self):
        # Possible output number for power/freq/phase
        self._num_power = 1
        self._num_freq = 1
        self._num_phase = 1
        self._output_mapping = {
            'power':{0:'Single'},
            'freq':{0:'Single'},
            'phase':{0:'Single'}
            }
        self._num_channels = 1
        self.__power_dbm_list = np.linspace(-13.49, 18.35, 64)
        
        
    @requires_connection
    def enableOutput(self, output_type:int=0):
        """Enables the output by applying the power as self.__power.
        Raises:
            AssertError - power must be set before enabling the output.
        """
        self.__send_command('o1')
        
        
    @requires_connection
    def disableOutput(self, output_type:int=0):
        """Simply applies the power to be zero.
        """
        self.__send_command('o0')
        
        
    @property
    def power_dbm_list(self):
        return self.__power_dbm_list

        
    @requires_connection
    def setPower(self, power: float, output_type:int=0):
        """Sends the command only if the output is currently enabled.
        Raises:
            ValueError - power is out of range.
        """
        check_range(power, self.min_power, self.max_power, 'power')

        power = round(power, 2)
        self.__power_idx = self.find_nearest_idx(self.__power_dbm_list, power)
        self.__power = self.__power_dbm_list[self.__power_idx]
        self.__send_command('a{}'.format(self.__power_idx))
        
    @requires_connection
    def setFrequency(self, freq: float, output_type:int=0):
        """
        Raises:
            ValueError - freq is out of range.
        """
        freq = round(freq, 1)
        check_range(freq, self.min_frequency, self.max_frequency, 'frequency')
        self.__send_command('f{:.2f}'.format(freq/1e6)) # Synth take freq in MHz
        
        
    @requires_connection
    def setPhase(self, phase: float, output_type:int=0):
        raise ValueError ("This function is not supported for this device (synthNV).")
        
    @requires_connection
    def getPower(self, output_type:int=0) -> float:
        """Caution: this may return None when the output has been disabled
        during the whole connection and the power has never been set.
        """
        power = self.__query_command('a?')
        self.__power_idx = int(power)
        self.__power = self.__power_dbm_list[self.__power_idx]
        
        return round(self.__power,2)
    
    @requires_connection
    def setChannel(self, chan):
        raise NotImplementedError ("SynthNV does not support multiple channels.")
        
    @requires_connection
    def getFrequency(self, output_type:int=0) -> float:
        freq = self.__query_command('f?') # Return MHz scale
        return int(float(freq) * 1e6) # Turn to Hz
    
    @requires_connection
    def getPhase(self, output_type:int=0) -> float:
        raise ValueError ("SynthNV does not support phase settings.")

    @requires_connection
    def is_output_enabled(self, output_type:int=0) -> bool:
        return '1' == self.__query_command('o?')
    
    @requires_connection
    def lockFrequency(self, external_flag=0, ext_ref_freq=10e6):
        """
        External source: 0, internal source: 1
        """
        self.__send_command("x%d" % (not external_flag))

    @requires_connection
    def is_locked(self) -> bool:
        """
        External source: 0, internal source: 1
        """
        return "0" == self.__query_command("x?")
    
    def __send_command(self, cmd: str) -> bool:
        """Sends command in the device protocol, such as terminators, etc.
        This private method simply appends a space and a terminator.
        The device does not take the command if there is no space in front
        of the terminator.
        """
        return self._send_command(cmd + "\n", encoding='ascii')

    def __query_command(self, cmd: str, size=1, trim=True):
        """Sends command and receives the response, through the device
        protocol.
        This private method simply appends a space and a terminator at the
        end of the command, just like self.__send_command does.
        """
        return self._query_command(cmd + "\n", encoding='ascii',
                                   terminator='\n', size=size, trim=trim)
        
        
class SynthHD(WindfreakTech):
    """
    Power range: [0 63] for [-50, +20] dBm 0.001dB resolution
    Frequency range: [10e6, 15e9] Hz 0.1Hz resolution
    """
    def __init__(self, port=None, min_power=-50, max_power=20, 
                 min_freq=10e6, max_freq=15e9):
        assert min_power >= -50, 'min_power should be at least -50dBm.'
        assert max_power <= 20, 'max_power should be at most 20dBm.'
        assert min_freq >= 10e6, 'min_frequency should be at least 34MHz.'
        assert max_freq <= 15e9, 'max_frequency shuold be at most 4500MHz.'
        assert min_power <= max_power, 'min_power is greater than max_power.'
        assert min_freq <= max_freq, 'min_frequency is greater than max_frequency.'
        self.__output_mapping()
        self.__phase = [0, 0]
        self._num_channels = 2
        super().__init__(min_power, max_power, min_freq, max_freq, port=port)

 
    def __output_mapping(self):
        # Possible output number for power/freq/phase
        self._num_power = 2
        self._num_freq = 2
        self._num_phase = 2
        self._output_mapping = {
            'power':{0:'Channel A', 1:'Channel B'},
            'freq':{0:'Channel A', 1:'Channel B'},
            'phase':{0:'Channel A', 1:'Channel B'}
            }
        
    @requires_connection
    def enableOutput(self, output_type:int=0):
        """Enables the output by applying the power as self.__power.
        Raises:
            AssertError - power must be set before enabling the output.
        """
        self.setChannel(output_type)
        self.__send_command('E1r1')
        
        
    @requires_connection
    def disableOutput(self, output_type:int=0):
        """Simply applies the power to be zero.
        """
        self.setChannel(output_type)
        self.__send_command('E0r0')
        
    @property
    def power_dbm_list(self):
        return [self.__power]

        
    @requires_connection
    def setPower(self, power: float, output_type:int=0):
        """Sends the command only if the output is currently enabled.
        Raises:
            ValueError - power is out of range.
        """
        self.setChannel(output_type)
        power = round(power, 2)
        self.__power = power
        self.__send_command('W{:.2f}'.format(power))
        
    @requires_connection
    def setFrequency(self, freq: float, output_type:int=0):
        """
        Raises:
            ValueError - freq is out of range.
        """
        self.setChannel(output_type)
        freq = round(freq, 1)
        check_range(freq, self.min_frequency, self.max_frequency, 'frequency')
        self.__send_command('f{:.2f}'.format(freq/1e6)) # Synth take freq in MHz
        
    @requires_connection
    def setPhase(self, phase: float, output_type:int=0):
        self.setChannel(output_type)
        net_phase = float(phase % 360)
        self.__phase[output_type] = net_phase
        self.__send_command('~{:.2f}'.format(net_phase))
        
        
    @requires_connection
    def getPower(self, output_type:int=0) -> float:
        """Caution: this may return None when the output has been disabled
        during the whole connection and the power has never been set.
        """
        self.setChannel(output_type)
        power = self.__query_command('W?')
        self.__power = float(power)
        return round(self.__power,2)
    
    @requires_connection
    def getFrequency(self, output_type:int=0) -> float:
        self.setChannel(output_type)
        freq = self.__query_command('f?') # Return MHz scale
        return int(float(freq) * 1e6) # Turn to Hz
    
    @requires_connection
    def setChannel(self, chan):
        if chan == 'A' or chan == 'a' or chan == 0:
            self.__send_command('C0')
        elif chan == 'B' or chan == 'b' or chan == 1:
            self.__send_command('C1')
        else:
            raise ValueError ('Wrong Channel Index')
            
    @requires_connection
    def getChannel(self) -> int:
        if self.device_name == 'HD':
            chan = self.__query_command('C?') # 0(A) or 1(B)
            return chan
        else:
            raise Warning ("This device does not support multiple channels (%s)." % self.device_name)
            return 0
        
    @requires_connection
    def getPhase(self, output_type:int=0) -> float:
        return self.__phase[output_type]

    @requires_connection
    def is_output_enabled(self, output_type:int=0) -> bool:
        self.setChannel(output_type)
        return '1' == self.__query_command('r?')
    
    
    @requires_connection
    def lockFrequency(self, external_flag=0, ext_ref_freq=10e6):
        """
        External source: 0, internal source: 1
        The reference frequency should be either 27 MHz or 10 MHz.
        """
        if not external_flag:
            if ext_ref_freq == 10e6:
                external_flag = 2
            elif ext_ref_freq == 27e6:
                external_flag = 1
            else:
                raise Warning("An unknown frequency of the internal reference is detected! (%d)" % (int(ext_ref_freq)))
            
        if external_flag:
            external_flag = 0
        self.__send_command("x%d" % (external_flag))

    @requires_connection
    def is_locked(self) -> bool:
        """
        External source: 0, internal source: 1
        """
        return "0" == self.__query_command("x?")
    
    def __send_command(self, cmd: str) -> bool:
        """Sends command in the device protocol, such as terminators, etc.
        This private method simply appends a space and a terminator.
        The device does not take the command if there is no space in front
        of the terminator.
        """
        return self._send_command(cmd + "\n", encoding='ascii')

    def __query_command(self, cmd: str, size=1, trim=True):
        """Sends command and receives the response, through the device
        protocol.
        This private method simply appends a space and a terminator at the
        end of the command, just like self.__send_command does.
        """
        return self._query_command(cmd + "\n", encoding='ascii',
                                   terminator='\n', size=size, trim=trim)
    



class APSYNxxx(SocketRFSource):
    """
    This class is for APSYN series devices, which are high frequency signal generators
    from AnaPico.
    All the commands and behaviours are currently based on 'Programmer’s Manual V2.03
    Signal Source Models'.
    Methods:
        - enable/disable_output
        - is_output_enabled
        - set/getFrequency
        - set/getPhase
        - lockFrequency
        - is_locked
    """
    def __init__(
            self, min_power, max_power, min_freq, max_freq, tcp_ip="", tcp_port=""):
        """
        tcp_ip and tcp_port can be assigned later by setters.
        """
        super().__init__(min_power, max_power, min_freq, max_freq,
                         tcp_ip=tcp_ip, tcp_port=tcp_port)

    @requires_connection
    def enableOutput(self, output_type:int=0):
        self.__send_command(":OUTPut 1")

    @requires_connection
    def disableOutput(self, output_type:int=0):
        self.__send_command(":OUTPut 0")

    @requires_connection
    def is_output_enabled(self, output_type:int=0) -> bool:
        return "1" == self.__query_command(":OUTPut?")

    @requires_connection
    def setFrequency(self, freq: float, output_type:int=0):
        """
        Frequency unit: Hz
        Raises:
            ValueError - target frequency is out of range.
        """
        check_range(freq, self.min_frequency, self.max_frequency, "frequency")
        self.__send_command(f":FREQuency {freq:.2f}")


    @requires_connection
    def setPower(self, power: float, output_type:int=0):
        """
        APSYN power is not adjustable
        """
        pass
    
    @requires_connection
    def setPhase(self, phase: float, output_type:int=0):
        """
        Phase unit: degree
        """
        # Converts degree to radian
        phase_rad = (phase % 360) * math.pi / 180
        self.__send_command(f":PHASe {phase_rad:.2f}")

    @requires_connection
    def getFrequency(self, output_type:int=0) -> float:
        """
        Frequency unit: Hz
        """
        return float(self.__query_command(":FREQuency?"))

    @requires_connection
    def getPower(self, output_type:int=0):
        """
        APSYN power is fixed as 23dBm
        """
        return float(23)
    

    @requires_connection
    def getPhase(self, output_type:int=0) -> float:
        """
        Phase unit: degree
        """
        # Converts radian to degree
        return float(self.__query_command(":PHASe?")) * 180 / math.pi

    @requires_connection
    def lockFrequency(self, external_flag=0, ext_ref_freq=10e6):
        """
        Conveys the expected reference frequency value of an externally applied reference
        to the signal generator.
        Frequency range: 1MHz - 250MHz (default: 10MHz)
        Raises:
            ValueError - ext_ref_freq is out of range.
        """
        check_range(ext_ref_freq, 1e6, 250e6, "external reference frequency")
        if external_flag:
            self.__send_command("ROSC:SOUR EXT")
            self.__send_command(f":ROSCillator:EXTernal:FREQuency {ext_ref_freq:.0f}")
        else:
            self.__send_command("ROSC:SOUR INT")
        if self.is_locked():
            print("it is locked")
            self.__send_command("ROSC:OUTP %s" % "ON" if external_flag else "OFF")
            self.__send_command("ROSC:OUTP:FREQ %.0f" % ext_ref_freq)


    @requires_connection
    def is_locked(self) -> bool:
        return "EXT" == self.__query_command("ROSC:SOUR?")

    """
    Following two private methods are wrappers for the protected methods
    _send_command and _query_command, respectively.
    These are just for convenience of writing codes.
    """
    def __send_command(self, cmd: str) -> bool:
        """
        Sends command in the device protocol, such as terminators, etc.
        This private method simply appends a terminator.
        """
        return self._send_command(cmd + "\n", encoding="ascii")

    def __query_command(self, cmd: str, size=1, trim=True):
        """
        Sends command and receives the response, through the device
        protocol.
        This private method simply appends a terminator at the
        end of the command, just like self.__send_command does.
        """
        return self._query_command(
            cmd + "\n", encoding="ascii", terminator="\n", size=size, trim=trim)


class APSYN420(APSYNxxx):
    """
    This class implements a particular device, APSYN420, which is in the APSYNxxx series.
    Power is not adjustable(+23dBM).
    Frequency range: [0.01e9, 20.0e9] Hz
    Frequency resolution: 0.001Hz
    Phase resolution: 0.1 deg
    """
    def __init__(
            self, min_power=23.0, max_power=23.0, min_freq=10e6, max_freq=20.0e9, tcp_ip="", tcp_port=18):
        assert min_freq >= 10e6, "min_frequency should be at least 10MHz."
        assert max_freq <= 20.0e9, "max_frequency shuold be at most 20.0GHz."
        assert min_freq <= max_freq, "min_frequency is greater than max_frequency."
        self.__output_mapping()
        self._num_channels = 1
        self.tcp_port = tcp_port
        super().__init__(min_power, max_power, min_freq, max_freq, tcp_ip=tcp_ip, tcp_port=tcp_port)



    def __output_mapping(self):
        # Possible output number for power/freq/phase
        self._num_power = 1
        self._num_freq = 1
        self._num_phase = 1
        self._output_mapping = {
            'power':{0:'Single'},
            'freq':{0:'Single'},
            'phase':{0:'Single'}
            }


class SG38x(SocketRFSource):
    """
    This class is for SG38x series devices, which are high frequency signal
    generators from Stanford Research Systems(SRS).
    All the commands and behaviours are currently based on SG384 manual.
    Methods:
        - enable/disable_output
        - is_output_enabled
        - set/getPower
        - set/getFrequency
        - set/getPhase
    """
    def __init__(
            self, min_power, max_power, min_freq, max_freq, tcp_ip="", tcp_port=""):
        """
        tcp_ip and tcp_port can be assigned later by setters.
        """
        super().__init__(min_power, max_power, min_freq, max_freq,
                         tcp_ip=tcp_ip, tcp_port=tcp_port)
        
        
    @requires_connection
    def enableOutput(self, output_type:int=0):
        if output_type == 0: # BNC
            self.__send_command("ENBL 1")
        elif output_type == 1: # N-Type
            self.__send_command("ENBR 1")
        else:
            raise ValueError('Undefined output type')

    @requires_connection
    def disableOutput(self, output_type:int=0):
        if output_type == 0: # BNC
            self.__send_command("ENBL 0")
        elif output_type == 1: # N-Type
            self.__send_command("ENBR 0")
        else:
            raise ValueError('Undefined output type')

    @requires_connection
    def is_output_enabled(self, output_type:int=0) -> bool:
        if output_type == 0:
            return "1" == self.__query_command("ENBL ?")
        if output_type == 1:
            return "1" == self.__query_command("ENBR ?")

    @requires_connection
    def setPower(self, power: float, output_type:int=0):
        """
        Power unit: dBm
        output type: BNC(0) / N-Type(1)
        Raises:
            ValueError - power is out of range.
        """
        check_range(power, self.min_power, self.max_power, "power")
        if output_type == 0: # BNC
            self.__send_command("AMPL {:.2f}".format(power))
        elif output_type == 1: # N-Type
            self.__send_command("AMPR {:.2f}".format(power))
        else:
            raise ValueError('Undefined output type')
            
    @requires_connection
    def setFrequency(self, freq: float, output_type:int=0):
        """
        Frequency unit: Hz
        Raises:
            ValueError - frequency is out of range.
        """
        check_range(freq, self.min_frequency, self.max_frequency, "frequency")
        self.__send_command("FREQ {:.3f}".format(freq))

    @requires_connection
    def setPhase(self, phase: float, output_type:int=0):
        """
        Phase unit: degree
        Phase resolution:
            - DC to 100MHz -> 0.01
            - 100MHz to 1GHz -> 0.1
            - 1GHz to 8.1GHz -> 1
        """
        net_phase = phase % 360
        self.__send_command("PHAS {:.2f}".format(net_phase))

    @requires_connection
    def getPower(self, output_type:int=0) -> float:
        """
        Power unit: dBm
        output type: BNC(0) / N-Type(1)
        """
        if output_type == 0: # BNC
            return float(self.__query_command("AMPL ?"))
        elif output_type == 1: # N-Type
            return float(self.__query_command("AMPR ?"))
        else:
            raise ValueError('Undefined output type')
            
    @requires_connection
    def getFrequency(self, output_type:int=0) -> float:
        """
        Frequency unit: Hz
        """
        return float(self.__query_command("FREQ ?"))

    @requires_connection
    def getPhase(self, output_type:int=0) -> float:
        """
        Phase unit: degree
        """
        return float(self.__query_command("PHAS ?"))
    
    @requires_connection
    def lockFrequency(self, external_flag=0, ext_ref_freq=10e6):
        """
        It only support 10MHz lock.
        """
        if external_flag:
            self.__send_command("LOCK")
        else:
            self.__send_command("UNLK")

    @requires_connection
    def is_locked(self) -> bool:
        return "1" == self.__query_command("LOCK ?")

    def __send_command(self, cmd: str) -> bool:
        """
        Sends command in the device protocol, such as terminators, etc.
        This private method simply appends a terminator.
        """
        return self._send_command(cmd + "\n", encoding="ascii")

    def __query_command(self, cmd: str, size=1, trim=True):
        """
        Sends command and receives the response, through the device
        protocol.
        This private method simply appends a terminator at the
        end of the command, just like self.__send_command does.
        """
        return self._query_command(
            cmd + "\n", encoding="ascii", terminator="\r\n", size=size, trim=trim)


class SG384(SG38x):
    """
    This class implements a particular device, SG384, which is in the SG38x series.
    Power range (Type-N): [-110, +16.50] dBm to [-110, +13] dBm over 3GHz
    Power range (BNC): [-47, +13] dBm
    Power resolution 0.01 dBm
    Frequency range (Type-N): [950kHz, 4.050GHz]
    Frequency range (BNC): [DC, 62.5MHz]
    Frequency resolution: 0.000001 Hz (1uHz)
    ==> I Set Power & Frequency Range with narrower bound
    """
    def __init__(
            self, min_power=-47, max_power=13, min_freq=950e3, max_freq=62.5e6,
            tcp_ip="", tcp_port=5025):
        assert min_power >= -47, "min_power should be at least -47dBm."
        assert max_power <= 13, "max_power should be at most 16.50dBm."
        assert min_freq >= 950e3, "min_frequency should be at least 950kHz."
        assert max_freq <= 62.5e6, "max_frequency shuold be at most 62.5MHz."
        assert min_power <= max_power, "min_power is greater than max_power."
        assert min_freq <= max_freq, "min_frequency is greater than max_frequency."
        self.__output_mapping()
        self._num_channels = 2
        super().__init__(min_power, max_power, min_freq,
                         max_freq, tcp_ip=tcp_ip, tcp_port=tcp_port)
        self.tcp_port = tcp_port
        
    def __output_mapping(self):
        # Possible output number for power/freq/phase
        self._num_power = 2
        self._num_freq = 1
        self._num_phase = 1
        self._output_mapping = {
            'power':{0:'BNC', 1:'NTYPE'},
            'freq':{0:'Common'},
            'phase':{0:'Common'}
            }
        
        
        
class Dummy_RF(SocketRFSource):
    """
    This class is a dummy class that can simulate actual devices.
    """
    
    def __init__(self, min_power=-50, max_power=10, min_freq=10e6, max_freq=15e9, port="", tcp_ip="", tcp_port=5512, device_type=""):
        assert min_power >= -50, "min_power should be at least -50 dBm."
        assert max_power <= 10, "max_power should be at most 10 dBm."
        assert min_freq >= 10e6, "min_frequency should be at least 10 MHz."
        assert max_freq <= 15e9, "max_frequency shuold be at most 15 GHz."
        assert min_power <= max_power, "min_power is greater than max_power."
        assert min_freq <= max_freq, "min_frequency is greater than max_frequency."
        self.__output_dict = {0: False, 1: False}
        self.__power_dict = {0: False, 1: False}
        self.__freq_dict = {0: False, 1: False}
        self.__phase_dict = {0: False, 1: False}
        self.__connected = False
        super().__init__(min_power, max_power, min_freq,
                         max_freq, tcp_ip=tcp_ip, tcp_port=tcp_port)
        self._num_channels = 2
        
        parameter_list = ["min_power", "max_power", "min_frequency", "max_frequency"]
        self.device_type = device_type
        target_device = device_type.split("_")[0]
    
        target_class = self._getTemporaryClass(target_device)
        if target_class:
            for param in parameter_list:
                setattr(self, param, getattr(target_class, param))
                
        self._lock_flag = False
        
    @property
    def min_power(self):
        return self._min_power
    
    @min_power.setter
    def min_power(self, value):
        self._min_power = value
        
    @property
    def max_power(self):
        return self._max_power
    
    @max_power.setter
    def max_power(self, value):
        self._max_power = value
        
    @property
    def min_frequency(self):
        return self._min_freq
    
    @min_frequency.setter
    def min_frequency(self, value):
        self._min_freq = value
        
    @property
    def max_frequency(self):
        return self._max_freq
    
    @max_frequency.setter
    def max_frequency(self, value):
        self._max_freq = value
    
                
    def _getTemporaryClass(self, target_device=""):
        if target_device == "synthnv":
            target_class = SynthNV()
            self._num_channels = 1
        elif target_device == "synthhd":
            self._num_channels = 2
            target_class = SynthHD()
        elif target_device == "sg384":
            self._num_channels = 2
            target_class = SG384()
        elif target_device == "apsyn420":
            self._num_channels = 1
            target_class = APSYN420()
        else:
            target_class = None
            self._num_channels = 2
            
        return target_class
        

    def connect(self):
        """Connects to the device."""
        import random
        success = random.random()
        if success > 0.01: # It fails to connect once out of 100.
            self.__connected = True
            return 0
        else:
            return -1

    def disconnect(self):
        """Disconnects from the device."""
        self.__connected = False
        
    def is_connected(self):
        return self.__connected
        
    def enableOutput(self, output_type=0):
        """Enables the output of the device."""
        self.__output_dict[output_type] = True

    def disableOutput(self, output_type=0):
        """Disables the output of the device."""
        self.__output_dict[output_type] = False

    def is_output_enabled(self, output_type=0) -> bool:
        """Returns whether the device output is currently enabled."""
        return self.__output_dict[output_type]

    def setPower(self, power: float, output_type=0):
        """Applies power as given, in dBm."""
        self.__power_dict[output_type] = max(min(power, self.max_power), self.min_power)

    def setFrequency(self, freq: float, output_type=0):
        """Applies frequency as given, in Hz."""
        self.__freq_dict[output_type] = max(min(freq, self.max_frequency), self.min_frequency)

    def setPhase(self, phase: float, output_type=0):
        """Applies phase as given, in degrees."""
        self.__phase_dict[output_type] = phase

    def getPower(self, output_type=0) -> float:
        """Returns the current power of the output in dBm."""
        return self.__power_dict[output_type]

    def getFrequency(self, output_type=0) -> float:
        """Returns the current frequency of the output in Hz."""
        return self.__freq_dict[output_type]

    def getPhase(self, output_type=0) -> float:
        """Returns the current phase of the output in degrees."""
        return self.__phase_dict[output_type]

    def lockFrequency(self, external_flag=0, ext_ref_freq=10e6):
        self._lock_flag = external_flag

    def is_locked(self, output_type=0) -> bool:
        """Returns whether the current output is locked."""
        return self._lock_flag
    
    def _get_comport(self, serial_number):
        import random
        return "COM%d" % random.randint(1, 100)
