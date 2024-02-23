# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 16:15:41 2020

@author: Modified by Jiyong Yu (Original work by Taehyun Kim)

Modified again by Jiyong Kang (Aug 2021).
"""

# Created for controlling triple DDS Board simultaneously

import collections
import math
import os.path

import protocol.basic as bp

class AD9912(bp.BasicProtocol):
    """This implements TrippleBoard_AD9912 device.

    This FPGA controls 3 DDS boards and each board has 2 channels. It uses
      BasicProtocol, hence it inherits protocol.basic.BasicProtocol.

    For more detailed information, see AD9912 manual.
    """

    def __init__(self, port_or_com, min_freq=10, max_freq=400):
        """
        Args:
            port_or_com: str or serial.Serial object that connects to the FPGA
              board. When it is None, a new Serial object is created with
              port=None.
            min_freq: Minimum frequency limit.
            max_freq: Maximum frequency limit.
        """
        super().__init__(port_or_com)
        self.min_freq = min_freq
        self.max_freq = max_freq
        
    def make_header_string(self, register_address, bytes_length, direction='W'):
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
    
    def FTW_Hz(self, freq):
        # make_header_string('0x01AB', 8)
        FTW_header = '61AB'
        y = int((2**48)*(freq/(10**9)))
        z = hex(y)[2:]
        FTW_body = (12-len(z))*'0' + z
        return FTW_header + FTW_body
    
    def make_9int_list(self, hex_string, ch1, ch2):
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
    
    def board_select(self, board_number):
        # Board selection among triple DDS board
        self._send_command(f'Board{board_number} Select')

    def set_frequency(self, freq_in_MHz, ch1, ch2):
        if not self.min_freq <= freq_in_MHz <= self.max_freq:
            raise ValueError(f'freq_in_MHz should be in '
                             f'[{self.min_freq}MHz, {self.max_freq}MHz]. '
                             f'{freq_in_MHz}MHz is given.')
            
        self._send_mod_BTF(
            self.make_9int_list(self.FTW_Hz(freq_in_MHz*1e6), ch1, ch2))
        self._send_command('WRITE DDS REG')
        # Update the buffered (mirrored) registers
        self._send_mod_BTF(self.make_9int_list('000501', ch1, ch2))
        self._send_command('WRITE DDS REG')

    def set_current(self, current, ch1, ch2):
        # DAC full-scale current
        # 1020 mVp-p (264*I_DAC_REF) => 670 mVp-p w/ FDB_IN
        #  270 mVp-p  (72*I_DAC_REF) => 180 mVp-p w/ FDB_IN
        if not 0 <= current <= 0x3ff:
            raise ValueError(f'current should be in [0 and 0x3ff({0x3ff})]. '
                             f'{current:x}({current}) is given.')
    
        hex_str = self.make_header_string(0x040C, 2) + f'{current:04x}'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2))
        self._send_command('WRITE DDS REG')
    
    def soft_reset(self, ch1, ch2):
        self._send_mod_BTF(
            self.make_9int_list(self.make_header_string(0, 1)+'3C', ch1, ch2))
        self._send_command('WRITE DDS REG')
        self._send_mod_BTF(
            self.make_9int_list(self.make_header_string(0, 1)+'18', ch1, ch2))
        self._send_command('WRITE DDS REG')
        
    def set_phase(self, phase, ch1, ch2):
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

    def power_down(self, ch1, ch2):
        # Digital powerdown
        hex_str = self.make_header_string(0x0010, 1)+'91'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2))
        self._send_command('WRITE DDS REG')

    def power_up(self, ch1, ch2):
        # Digital power-up. We don't turn on the ch2 HSTL trigger automatically
        hex_str = self.make_header_string(0x0010, 1)+'90'
        self._send_mod_BTF(self.make_9int_list(hex_str, ch1, ch2))
        self._send_command('WRITE DDS REG')