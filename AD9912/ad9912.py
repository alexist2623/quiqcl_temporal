# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 16:15:41 2020

@author: Modified by Jiyong Yu (Original work by Taehyun Kim)

Modified again by Jiyong Kang (Aug 2021).

Modified again by Jeonghyun Park (Feb 2024).
"""

# Created for controlling triple DDS Board simultaneously

import collections
import math
import os.path

import protocol.basic as bp
from util import *

class AD9912(bp.BasicProtocol):
    """This implements TrippleBoard_AD9912 device.

    This FPGA controls 3 DDS boards and each board has 2 channels. It uses
      BasicProtocol, hence it inherits protocol.basic.BasicProtocol.

    For more detailed information, see AD9912 manual.
    """

    def __init__(self, 
                 port_or_com : str, 
                 min_freq : float =10, 
                 max_freq : float =400):
        """
        Args:
            port_or_com: str or serial.Serial object that connects to the FPGA
              board. When it is None, a new Serial object is created with
              port=None.
            min_freq: Minimum frequency limit.
            max_freq: Maximum frequency limit.
        """
        super().__init__(port_or_com)
        self.min_freq : float = min_freq
        self.max_freq : float = max_freq
        
    def make_header_string(self, 
                           register_address : int, 
                           bytes_length : int, 
                           direction : str='W'):
        """Makes header string following the protocol.

        Args:
            register_address: Register address in hexadecimal string or int.
            bytes_length: Byte count in int. It should be in range [1, 8].
            direction: 'W' for write, 'R' for read.

        Returns:
            Header string made by given arguments.
        """
        if direction == 'W':
            MSB = 0
        elif direction == 'R':
            MSB = 1
        else:
            raise ValueError(f'Unknown direction: {direction}. '
                             f'Expected W or R.')
            
        if isinstance(register_address, str):
            address = int(register_address, 16)
        elif isinstance(register_address, int):
            address = register_address
        else:
            raise TypeError(f'Unknown register_address type: '
                            f'{type(register_address)}. Expected str ot int.')
            
        if not 1 <= bytes_length <= 8:
            raise ValueError(f'bytes_length should be in [1, 8]. '
                             f'{bytes_length} is given.')
        elif bytes_length < 4:
            W1W0 = bytes_length - 1
        else:
            W1W0 = 3
        
        # print(MSB, W1W0, address)
        header_value = (MSB << 15) + (W1W0 << 13) + address
        return f'{header_value:04X}'
    
    def FTW_Hz(self, 
               freq : float):
        # make_header_string('0x01AB', 8)
        FTW_header = '61AB'
        y = int((2**48)*(freq/(10**9)))
        z = hex(y)[2:]
        FTW_body = (12-len(z))*'0' + z
        return FTW_header + FTW_body
    
    def make_9int_list(self, 
                       hex_string : str, 
                       ch1 : bool, 
                       ch2 : bool):
        hex_string_length = len(hex_string)
        byte_length = (hex_string_length // 2)
        if hex_string_length % 2 != 0:
            raise ValueError(f'hex_string should have even length. '
                             f'{hex_string_length} is given.')
        
        int_list = [(ch1 << 5) + (ch2 << 4) + byte_length]
        for n in range(0, 2*byte_length, 2):
            int_list.append(int(hex_string[n:n+2], 16))
        for n in range(8-byte_length):
            int_list.append(0)
        
        return int_list
    
    def board_select(self, 
                     board_number : str):
        # Board selection among triple DDS board
        self._send_command(f'Board{board_number} Select')

    def set_frequency(self, freq_in_MHz, ch1, ch2):
        if not self.min_freq <= freq_in_MHz <= self.max_freq:
            raise ValueError(f'freq_in_MHz should be in '
                             f'[{self.min_freq}MHz, {self.max_freq}MHz]. '
                             f'{freq_in_MHz}MHz is given.')
            
        self._send_mod_BTF(
            self.make_9int_list(self.FTW_Hz(freq_in_MHz*1e6), ch1, ch2)
            )
        self._send_command('WRITE DDS REG')
        # Update the buffered (mirrored) registers
        self._send_mod_BTF(self.make_9int_list('000501', ch1, ch2))
        self._send_command('WRITE DDS REG')

    def set_current(self, 
                    current : float, 
                    ch1 : bool, 
                    ch2 : bool):
        # DAC full-scale current
        # 1020 mVp-p (264*I_DAC_REF) => 670 mVp-p w/ FDB_IN
        #  270 mVp-p  (72*I_DAC_REF) => 180 mVp-p w/ FDB_IN
        if not 0 <= current <= 0x3ff:
            raise ValueError(f'current should be in [0 and 0x3ff({0x3ff})]. '
                             f'{current:x}({current}) is given.')
    
        hex_str = self.make_header_string(0x040C, 2) + f'{current:04x}'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2))
        self._send_command('WRITE DDS REG')
    
    def soft_reset(self, 
                   ch1 : bool, 
                   ch2 : bool):
        self._send_mod_BTF(
            self.make_9int_list(self.make_header_string(0, 1)+'3C', ch1, ch2))
        self._send_command('WRITE DDS REG')
        self._send_mod_BTF(
            self.make_9int_list(self.make_header_string(0, 1)+'18', ch1, ch2))
        self._send_command('WRITE DDS REG')
        
    def set_phase(self, 
                  phase : float, 
                  ch1 : bool, 
                  ch2 : bool):
        # Convert phase into radian
        phase_rad = (math.pi / 180) * phase
        # Convert phase for DDS
        phase_dds = int(phase_rad * (2**14) / (2 * math.pi))
        
        #  Phase value: 0000 ~ 3FFF
        if not 0 <= phase_dds <= 0x3fff:
            raise ValueError(f'phase should be in [0, 360) (degree). '
                             f'{phase} is given (converted={phase_dds:x}).')

        hex_str = self.make_header_string(0x01AD, 2) + f'{phase_dds:04x}'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2)) 
        self._send_command('WRITE DDS REG')
        # Update the buffered (mirrored) registers
        self._send_mod_BTF(self.make_9int_list('000501', ch1, ch2))
        self._send_command('WRITE DDS REG')

    def power_down(self, 
                   ch1 : bool, 
                   ch2 : bool):
        # Digital powerdown
        hex_str = self.make_header_string(0x0010, 1)+'91'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2))
        self._send_command('WRITE DDS REG')

    def power_up(self, 
                 ch1 : bool, 
                 ch2 : bool):
        # Digital power-up. We don't turn on the ch2 HSTL trigger automatically
        hex_str = self.make_header_string(0x0010, 1)+'90'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2))
        self._send_command('WRITE DDS REG')
        
class AD9912_w_VVA(AD9912):
    
    def __init__(self, port_or_com : str,
                 min_current : float,
                 max_current : float,
                 min_voltage : float,
                 max_voltage : float,
                 min_freq : float =10, 
                 max_freq : float =400):
        super().__init__(port_or_com, min_freq, max_freq)
        self.min_current : float = min_current
        self.max_current : float = max_current
        self.min_voltage : float = min_voltage
        self.max_voltage : float = max_voltage
                
    def setCurrent(self, 
                   board : str, 
                   ch1 : str, 
                   ch2 : str, 
                   current : float) -> None:
        """
        This function changes the output voltage of the DAC, which controls 
        the attenuation using VVA. The non-linear value of the DDS is fixed 
        to 0.
        
        Note that the output voltage value is 3 times smaller because of the 
        hardware configuration. For example, If you set 3 V output, then it 
        actually emits 1 V.
        
        Approximated values are
            - 0.00 V: maximum attenuation, 60 dB
            - 1.25 V: 50 dB
            - 1.37 V: 40 dB
            - 2.15 V: 20 dB
            - 5.00 V: 10 dB
            - 9.00 V:  5 dB
            
        It follows
            - Atten. = 0.0252*(Voltage**2) - 2.2958*(Voltage) + 52.893
        """
        self.checkCurrentBound(current)
        voltage = self.getVoltageFromCurrent(current)
        dac_channel_idx = 2*(board-1)
        chip_idx = dac_channel_idx // 4
        channel_idx = dac_channel_idx % 4
        if ch1:
            self.voltage_register_update(chip_idx, channel_idx, voltage)
        if ch2:
            self.voltage_register_update(chip_idx, channel_idx+1, voltage)
            
        self.load_dac()
     
    def _setActualCurrent(self, 
                          board : str, 
                          ch1 : bool, 
                          ch2 : bool, 
                          current : int) -> None:
        """
        This function changes the output power of the given channels of the 
        given board.
        """
        self.checkCurrentBound(current)
        self.board_select(board)
        
        self._send_mod_BTF(
            self._make_9int_list(
                self._make_header_string(0x040C, 2)\
                +('%04x' % current), ch1, ch2
                )
            ) 
        self._send_command('WRITE DDS REG')
    
    def voltage_register_update(self, 
                                chip : int, 
                                channel : int, 
                                voltage : float, 
                                bipolar : bool = True, 
                                v_ref : float = 7.5):
        if bipolar:
            input_code = int(65536/(4*v_ref)*voltage)
            if (input_code < -32768) or (input_code > 32767): 
                raise ValueError('Error in voltage_out: voltage is out of range')
            code = (input_code + 65536) % 65536
        else:
            if voltage < 0: 
                raise ValueError('Error in voltage_out: voltage cannot be \
                                 negative with unipolar setting')
            elif voltage > 17.5: 
                raise ValueError('Error in voltage_out: voltage cannot be \
                                 larger than 17.5 V')
            code = int(65536/(4*v_ref)*voltage)
            if (code > 65535): 
                raise ValueError('Error in voltage_out: voltage is out of range')
        message = [1<<chip, 0x04+channel, code // 256, code % 256]
        self._send_mod_BTF(message)
        self._send_command('WRITE DAC REG')
    
    def load_dac(self) -> None:
        self._send_command('LDAC')
    
    def getVoltageFromCurrent(self, 
                              current : int) -> None:
        """
        This functions scales the current value to adequate voltage.
        Note that the current cannot be exceed 1000.
        """
        if current > 1000: current = 1000
        voltage = current/200 + 1
        return voltage
    
    def checkCurrentBound(self,
                          current : float) -> None:
        if (current < self.min_current) or (current > self.max_current):
            raise ValueError ('Error in set_current: current should be between \
                              %d and %d' % (self.min_current, self.max_current))
