# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 08:11:03 2021

@author: JHJeong
"""
from quiqcl_device.rfsrc import AD9912

class AD9912_w_VVA(AD9912):
    
    def __init__(self, port_or_com, min_freq=10, max_freq=400):
        super().__init__(port_or_com, min_freq, max_freq)
        if port_or_com == "":
            port_or_com = self._get_my_com_port(port_or_com)
        
        self.com_port = com_port
                
    def openDevice(self):
        if self._connected:
            raise RuntimeError ("The device is alrady open!")
        else:
            self._fpga = ArtyS7(self.com_port)
            self._connected = True
            self._fpga.print_idn()    
        
            dna_string = self._fpga.read_DNA()
            print('FPGA DNA string:', dna_string)
            
            for board in range(2):
                self._setActualCurrent(board+1, 1, 1, 0)
    
    def closeDevice(self):
        self._fpga.close()
        self._connected = False
     
    def setCurrent(self, board, ch1, ch2, current):
        """
        This function changes the output voltage of the DAC, which controls the attenuation using VVA.
        The non-linear value of the DDS is fixed to 0.
        
        Note that the output voltage value is 3 times smaller because of the hardware configuration.
        For example, If you set 3 V output, then it actually emits 1 V.
        
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
        if current < self.min_current or current > self.max_current:
            raise ValueError ("Tthe current vlaue must be between %d and %d" % (self.min_current, self.max_current))
        voltage = self._getVoltageFromCurrent(current)
        dac_channel_idx = 2*(board-1)
        chip_idx = dac_channel_idx // 4
        channel_idx = dac_channel_idx % 4
        print(chip_idx)
        print(channel_idx)
        print(voltage)
        if ch1:
            self._voltage_register_update(chip_idx, channel_idx, voltage)
        if ch2:
            self._voltage_register_update(chip_idx, channel_idx+1, voltage)
            
        self._load_dac()
     
    def setFrequency(self, board, ch1, ch2, freq_in_MHz):
        """
        This function changes the output frequency of the given channels of the given board.
        The frequency should be in MHz.
        """
        if (freq_in_MHz < self.min_freq_in_MHz) or (freq_in_MHz > self.max_freq_in_MHz):
            raise ValueError ('Error in set_frequency: frequency should be between %d and %d MHz' % (self.min_freq_in_MHz, self.max_freq_in_MHz))
        self._board_select(board)

        self._fpga.send_mod_BTF_int_list(self._make_9int_list(self._FTW_Hz(freq_in_MHz*1e6), ch1, ch2))
        self._fpga.send_command('WRITE DDS REG')
        self._fpga.send_mod_BTF_int_list(self._make_9int_list('000501', ch1, ch2)) # Update the buffered (mirrored) registers
        self._fpga.send_command('WRITE DDS REG')
        
    def powerDown(self, board, ch1, ch2):
        """
        This function completely suppresses the output power of the channels of the given board.
        """
        self._board_select(board)
        # DDS board power down
        self._fpga.send_mod_BTF_int_list(self._make_9int_list(self._make_header_string(0x0010, 1)+'91', ch1, ch2))
        self._fpga.send_command('WRITE DDS REG')
        # DAC to maximum attenuation
        self.setCurrent(board, ch1, ch2, 0)
        
    def powerUp(self, board, ch1, ch2):
        """
        This function let the DDS board generate a RF wave.
        Because of the 1-dB compression issue of the LN amplifiers, the current of the board is initialized to 0.
        """
        # DAC to 0 V for safety.
        self.setCurrent(board, ch1, ch2, 0)
        
        self._board_select(board)
        # Digital power-up. We don't turn on the ch2 HSTL trigger automatically
        self._fpga.send_mod_BTF_int_list(self._make_9int_list(self._make_header_string(0x0010, 1)+'90', ch1, ch2))
        self._fpga.send_command('WRITE DDS REG')
        # Set the current of the DAC output to 0. Compression issue.
        self._setActualCurrent(board, ch1, ch2, 0)

    def _setActualCurrent(self, board, ch1, ch2, current):
        """
        This function changes the output power of the given channels of the given board.
        """
        if (current < self.min_current) or (current > self.max_current):
            raise ValueError ('Error in set_current: current should be between %d and %d' % (self.min_current, self.max_current))
        self._board_select(board)
        
        self._fpga.send_mod_BTF_int_list(self._make_9int_list(self._make_header_string(0x040C, 2)+('%04x' % current), ch1, ch2)) 
        self._fpga.send_command('WRITE DDS REG')


    def _board_select(self, board_num):
        # Board selection among triple DDS board
        assert isinstance(board_num, int), "The board_number should be an integer number."
        self._fpga.send_command('Board%d Select' % board_num)
      
    def _FTW_Hz(self, freq):
        # make_header_string('0x01AB', 8)
        FTW_header = "61AB"
        y = int((2**48)*(freq/(10**9)))
        z = hex(y)[2:]
        FTW_body = (12-len(z))*"0"+z
        return FTW_header + FTW_body

    def _make_9int_list(self, hex_string, ch1, ch2):
        hex_string_length = len(hex_string)
        byte_length = (hex_string_length // 2)
        if hex_string_length % 2 != 0:
            print('Error in make_int_list: hex_string cannot be odd length')
            raise ValueError()
            
        int_list = [(ch1 << 5) + (ch2 << 4) + byte_length]
        for n in range(byte_length):
            int_list.append(int(hex_string[2*n:2*n+2], 16))
        for n in range(8-byte_length):
            int_list.append(0)
        return int_list

    def _make_header_string(self, register_address, bytes_length, direction='W'):
        if direction == 'W':
            MSB = 0
        elif direction == 'R':
            MSB = 1
        else:
            print('Error in make_header: unknown direction (%s). ' % direction, \
                  'direction should be either \'W\' or \'R\'.' )
            raise ValueError()
            
        if type(register_address) == str:
            address = int(register_address, 16)
        elif type(register_address) == int:
            address = register_address
        else:
            print('Error in make_header: unknown register address type (%s). ' % type(register_address), \
                  'register_address should be either hexadecimal string or integer' )
            raise ValueError()
            
        if (bytes_length < 1) or (bytes_length > 8):
            print('Error in make_header: length should be between 1 and 8.' )
            raise ValueError()
        elif bytes_length < 4:
            W1W0 = bytes_length - 1
        else:
            W1W0 = 3
        
        print(MSB, W1W0, address)
        header_value = (MSB << 15) + (W1W0 << 13) + address
        return ('%04X' % header_value)
    
    def _voltage_register_update(self, chip, channel, voltage, bipolar=True, v_ref=7.5):
        if bipolar:
            input_code = int(65536/(4*v_ref)*voltage)
            if (input_code < -32768) or (input_code > 32767):
                raise ValueError('Error in voltage_out: voltage is out of range')
        
            code = (input_code + 65536) % 65536
        else:
            if voltage < 0:
                raise ValueError('Error in voltage_out: voltage cannot be negative with unipolar setting')
            elif voltage > 17.5:
                raise ValueError('Error in voltage_out: voltage cannot be larger than 17.5 V')
                
            code = int(65536/(4*v_ref)*voltage)
            if (code > 65535):
                raise ValueError('Error in voltage_out: voltage is out of range')

        #print('Code:', code)
        message = [1<<chip, 0x04+channel, code // 256, code % 256]
            
        self._fpga.send_mod_BTF_int_list(message)
        self._fpga.send_command('WRITE DAC REG')
    
    def _load_dac(self):
        #dac.send_mod_BTF_int_list([0xff,0x00, 0x40, 0x3C])
        #dac.send_command('WRITE REG')
        self._fpga.send_command('LDAC')
    
    
    def _get_my_com_port(self, ser_num=""):
        """
        This function finds and returns the comport that matches with the given serial number.
        
        If nothing matches, it raises a Runtime error.
        """
        from serial.tools.list_ports import comports
        for dev in comports():
            if dev.serial_number == ser_num:
                return dev.device
           
        raise RuntimeError("No comport that matches with the given serial_number has been found.")
        
    def _getVoltageFromCurrent(self, current):
        """
        This functions scales the current value to adequate voltage.
        Note that the current cannot be exceed 1000.
        """
        if current > 1000:
            current = 1000
        voltage = current/200 + 1
        return voltage
        
if __name__ == "__main__":
    my_dds = AD9912_w_VVA(ser_num="210352B0BE0AB")