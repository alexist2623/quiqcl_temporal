# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 16:32:25 2020

@author: hp
"""

from Arty_S7_v1_01 import ArtyS7
from DDS_Controller import AD9912 as dds
from ADS8698_v1_00 import ADS8698 as adc
import time
import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame
from scipy.optimize import curve_fit


class Raman_PID_Controller():
    def __init__(self, fpga, verbose=False):
        # FPGA connect and dds initialization
        self.fpga = fpga
        self.verbose = verbose
        self._sampling_rate = 20e3  # 20kHz by default
        self.min_freq = 0;
        self.max_freq = 500;
        self.dds = dds(self.fpga, self.min_freq, self.max_freq)
        
    def write_to_fpga(self, msg):
        self.fpga.send_command(msg)
    
    def read_from_fpga(self):
        if self.verbose:
            print(self.fpga.read_next_message());
    
    ##########################################
    # DDS
    ##########################################
    
    # Start dds state in FPGA (different from power_on, power_on just makes final output on)
    def dds_start(self):
        cmd = 'DDS START'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)
    
    # Stop dds state in FPGA (different from power_down, power_down just makes final output off)    
    def dds_stop(self):
        cmd = 'DDS STOP'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)
    
    def set_frequency(self, freq, index):
        """Sets the frequency profile corresponding to `index`.

        The frequency profile is a virtual profile, not the one in AD9910.
        In Raman_PID_Lock, many frequency profiles are connected to an actual
          DDS channel, and they can be switched by external TTL signals.
        Note that the additional frequency profile index must be equal to or
          greater than the number of actual channels to avoid confusion.
        Moreover, the frequency profile index must be the same as the actual
          channel index for the indices less than the number of actual channels,
          i.e., 0, 1, 2, 3 when there are two boards hence four channels.

        For power and phase, the index indicates the actual channel index, since
          they do not have such profiles.

        Args:
            freq: Desired frequency in MHz.
            index: Frequency profile index.
        """
        if (freq < self.min_freq) or (freq > self.max_freq):
            print('Error in set_frequency: frequency should be between' +  str(self.min_freq) + 'and' + str(self.max_freq) + 'MHz')
            raise ValueError(freq)
        
        self.dds_start()
        cmd = 'WRITE DDS REG'
        cmd_up = 'UPDATE'
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list(self.dds.FTW_Hz(freq*1e6), index))
        self.fpga.send_command(cmd)
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list('000501', index)) # Update the buffered (mirrored) registers
        self.fpga.send_command(cmd)

        if self.verbose:
            print("SET FREQ:", freq, index)
                
        
    def set_current(self, current, index):
        if (current < 0) or (current > 0x3ff):
            print('Error in set_current: current should be between 0 and 0x3ff')
            raise ValueError(current)
            
        self.dds_start()
        cmd = 'WRITE DDS REG'
        cmd_up = 'UPDATE'
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list(self.dds.make_header_string(0x040C, 2)+('%04x' % current), index)) 
        self.fpga.send_command(cmd)

        if self.verbose:
            print("SET CURRENT:", current, index)
    
    def set_phase(self, phase, index):
        # Convert phase into radian
        phase_rad = (np.pi / 180) * phase
        # Convert phase for DDS
        phase_dds = int(phase_rad * (2**14) / (2 * np.pi))
        
        self.dds_start()
        cmd = 'WRITE DDS REG'
        cmd_up = 'UPDATE'
        
        #  Phase value: 0000 ~ 3FFF
        if (phase_dds < 0) or (phase_dds > 2**14):
            print('Error in set_phase: phase should be between 0 and 360 (degree).')
            raise ValueError(phase)
            
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list(self.dds.make_header_string(0x01AD, 2)+('%04x' % phase_dds), index)) 
        self.fpga.send_command(cmd)
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list('000501', index)) # Update the buffered (mirrored) registers
        self.fpga.send_command(cmd)

        if self.verbose:
            print("SET PHASE:", phase, index)
    
    def power_down(self, index):
        # Digital powerdown
        self.dds_start()
        cmd = 'WRITE DDS REG'
        cmd_up = 'UPDATE'
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list(self.dds.make_header_string(0x0010, 1)+'91', index))
        self.fpga.send_command(cmd)
        if self.verbose:
            print('Power down:', index)
     
    def power_up(self, index):
        # Digital powerup
        self.dds_start()
        cmd = 'WRITE DDS REG'
        cmd_up = 'UPDATE'
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(self.dds.make_9int_list(self.dds.make_header_string(0x0010, 1)+'90', index))
        self.fpga.send_command(cmd)
        if self.verbose:
            print('Power up:', index)
    
    ##########################################
    # COMP control
    ##########################################
    
    def comp_start(self):
        cmd = 'COMP START'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)
        
        
    def comp_stop(self):
        cmd = 'COMP STOP'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)    
    
    def comp_set_K0(self,K0):
        cmd = 'COMPENSATOR K0'
        cmd_up = 'UPDATE'
        code = int(K0) & ((1 << 24) - 1)
        message = [code >> 16, (code >> 8) & 255, code & 255]
        
        # stop DDS 
        self.dds_stop()
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        
        # start DDS
        self.dds_start()
        
        if self.verbose:
            print(cmd)

    def comp_set_K1(self,K1):
        cmd = 'COMPENSATOR K1'
        cmd_up = 'UPDATE'
        code = int(K1) & ((1 << 24) - 1)
        message = [code >> 16, (code >> 8) & 255, code & 255]
        
        # stop DDS 
        self.dds_stop()
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        
        # start DDS
        self.dds_start()
        
        if self.verbose:
            print(cmd)   
        
    def comp_set_K2(self,K2):
        cmd = 'COMPENSATOR K2'
        cmd_up = 'UPDATE'
        code = int(K2) & ((1 << 24) - 1)
        message = [code >> 16, (code >> 8) & 255, code & 255]
        
        # stop DDS
        self.dds_stop()
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        
        # start DDS
        self.dds_start()
     
        if self.verbose:
            print(cmd)
    
    def comp_set(self, P, I, D):
        K0 = P + I + D
        K1 = P - I + 2 * D
        K2 = D
        
        self.comp_set_K0(K0)
        self.comp_set_K1(K1)
        self.comp_set_K2(K2)

    # Setting the setpoint of the comp Controller
    def comp_set_setpoint(self,code):
        cmd = 'COMP SETPOINT'
        cmd_up = 'UPDATE'
        code &= (1 << 24) - 1
        message = [code >> 16, (code >> 8) & 255, code & 255]
        
        # stop dds
        self.dds_stop()
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        
        # start dds
        self.dds_start()
        if self.verbose:
            print(message)
            print(cmd)

    def comp_set_comb_number(self, A1, B, C, A2):
        """Updates comb number for each AOM setup.

        Args:
            A1, B, C, A2: Desired new comb number for port A1, B, C, and A2,
              respectively. A1 and A2 are virtual channels, i.e., frequency
              profiles, which is physically connected to port A.
              If it is None or 255, it remains unchanged.
        """
        cmd = 'COMP COMB'
        cmd_up = 'UPDATE'
        message = [A1, B, C, A2]
        
        # stop dds
        self.dds_stop()

        for comb in message:
            if not (comb is None or 0 <= comb < 256):
                print(f'comp_set_comb_number: comb number must be None or an integer in 1 byte (0-255), but {comb} is given; this will be ignored.')
                return
            if comb == 255:
                print(f'comp_set_comb_number: comb=255 will not change the comb number.')
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list([255 if msg is None else msg
                                         for msg in message])
        self.fpga.send_command(cmd)
        
        # start dds
        self.dds_start()
        if self.verbose:
            print(message)
            print(cmd)

    def comp_set_harmonic_order(self, order):
        """Changes the harmonic order of the PD signal.

        Args:
            order: A natural number in range [1, 127] which divides the
              tracking error. In other words, the system tracks the harmonic
              signal of the repetition rate, i.e., the order-th peak in the
              Fourier domain. If it is greater than 127, it might act as a
              negative integer, but it is not intended hence not guaranteed
              to work properly. If it is zero, this command is ignored.
        """
        cmd = 'COMP HARMONICS'
        cmd_up = 'UPDATE'
        message = [order]
        
        # stop dds
        self.dds_stop()

        if not 0 <= order < 256:
            print(f'comp_set_harmonic_order: harmonic order must be fit in 1 byte (0-255), but {order} is given; this will be ignored.')
            return
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        
        # start dds
        self.dds_start()
        if self.verbose:
            print(message)
            print(cmd)
        
    def const_shoot(self):
        cmd='CONST SHOOT'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)    
    
    ##########################################
    # ADC
    ##########################################
    def adc_start(self, adc_ch = 0):
        if adc_ch<4:    
            ch_cmd = 0xC0+4 * adc_ch
        elif adc_ch < 8 and adc_ch >= 4:
            ch_cmd = 0xD0 + 4 * (adc_ch - 4)
        elif adc_ch == 8:
            ch_cmd = 0xE0
        else:
            print('error 내보내기, 잘못된 채널')            
        cmd='ADC START'
        cmd_up = 'UPDATE'
        message=[ch_cmd, 0]
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        
        if self.verbose:
            print(cmd)  
     
    
    def adc_stop(self):
        cmd='ADC STOP'
        cmd_up = 'UPDATE'
        
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        
        if self.verbose:
            print(cmd)   
    
    def adc_range_select(self, adc_ch = 0, option = 1):
        ch_cmd=((0x05+adc_ch)<<1)+1
        cmd='ADC RANGE'
        cmd_up = 'UPDATE'
        
        if option==1:
            option_cmd=0
        elif option==2:
            option_cmd=1
        elif option==3:
            option_cmd=2
        elif option==4:
            option_cmd=5
        elif option==5:
            option_cmd=6
                
        message=[ch_cmd, option_cmd]
        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)
        self.adc_start(adc_ch)
        
    def load_data(self, board, option = 1):
        """Loads the current data.

        Args:
            board: Board number to be read. If it is 1, the channels in the
              board 1 (TRACKING, COPROP) are loaded. Otherwise, the channels
              in the board 2 (RSB, BSB) are loaded.
            option: See adc_voltage_transform().

        Returns:
            A 3-tuple (adc voltage, frequency1, frequency2), where the
              frequencies are in MHz.
        """
        Fs = 10 ** 9; # Sampling frequency of DDS
        FTW_bit = 48; # Frequency tuning word uses 48 bit
        
        cmd_load=f'LOAD {board}'
        self.fpga.send_command(cmd_load)
        if self.verbose:
            print(cmd_load)
        
        adcv = self.fpga.read_next_message()
        if adcv[0] != '!':
            print('read_adc: Reply is not CMD type:', adcv)
            return False

        # For Analog output(18bit)
        adc_voltage = self.adc_voltage_transform(ord(adcv[1][0]), ord(adcv[1][1]), ord(adcv[1][2]), option) # modified!!
        
        # FTW1: PD Tracking frequency (board=1) or RSB AOM frequency (board=2)
        FTW_1 = (ord(adcv[1][3]) << 40) + (ord(adcv[1][4]) << 32) + (ord(adcv[1][5]) << 24) + (ord(adcv[1][6]) << 16) + (ord(adcv[1][7]) << 8) + (ord(adcv[1][8]))
        Freq_1_MHz = (FTW_1 * Fs) / ((2 ** FTW_bit) * (10 ** 6))
        
        # FTW2: COPROP AOM frequency (board=1) or BSB AOM frequency (board=2)
        FTW_2 = (ord(adcv[1][9]) << 40) + (ord(adcv[1][10]) << 32) + (ord(adcv[1][11]) << 24) + (ord(adcv[1][12]) << 16) + (ord(adcv[1][13]) << 8) + (ord(adcv[1][14]))
        Freq_2_MHz = (FTW_2 * Fs) / ((2 ** FTW_bit) * (10 ** 6))
        
        return (adc_voltage, Freq_1_MHz, Freq_2_MHz)
        
    # Transform ADC output style bitstring to voltage
    def adc_voltage_transform(self,v1,v2,v3,option):
        Vref=4.096
        
        if option == 2:
            bipolar = True
            Vrange = 1.25*Vref
            
        elif option == 3:
            bipolar = True
            Vrange = 0.625*Vref
            
        elif option == 4:
            bipolar = False
            Vrange = 2.5*Vref
            
        elif option == 5:
            bipolar = False
            Vrange = 1.25*Vref
            
        else:
            bipolar = True
            Vrange = 2.5*Vref
        
        if bipolar:
            resol=Vrange/2**17
            voltage=(((v1-128)<<10)+(v2<<2)+(v3 >> 6))*resol
        else:
            resol=Vrange/2**18
            voltage=((v1<<10)+(v2<<2)+(v3 >> 6))*resol #v3뒷부분 안나오게 바꿔야할듯 (수정완료!)

        return voltage
    
    def adc_voltage_i_transform(self,voltage, bipolar=True, v_ref=4.096, option=1):
        if bipolar:
            input_code = int(262144/(1.25*v_ref)*voltage)
            if (input_code < -131072) or (input_code > 131071):
                raise ValueError('Error in voltage_out: voltage is out of range')
        
            code = (input_code + 262144) % 262144
        else:
            if voltage < 0:
                raise ValueError('Error in voltage_out: voltage cannot be negative with unipolar setting')
            elif voltage > 262144:
                raise ValueError('Error in voltage_out: voltage cannot be larger than 17.5 V')
            code = int(262144/(v_ref*1.25)*voltage)
            
            if(code>262144):
                raise ValueError('Error in voltage_out: voltage is out of range')  
        if self.verbose:
            print('test:',code)
        return code
    
    
    #################### ADC Large data#################
    def fit_func(self, t, ampl, freq, phase, offset):
        return ampl * np.sin(2 * np.pi * freq * t + phase) + offset
    
    def adc_load_large_data(self,ch=0, option=1):
        cmd_load='LOAD LARGE'
        self.fpga.send_command(cmd_load)
        if self.verbose:
            print(cmd_load)

        adcv = self.fpga.read_next_message()
        
        N = 100 # Large data is array with length 100

        if adcv[0] != '#':   ##tx_buffer2
            print('read_adc: Reply is not CMD type:', adcv)
            return None
        
        mo_adcv = np.array(tuple(map(ord, adcv[1])))
        large_adcv = mo_adcv.reshape(N, 3) # Large data is array with length 100
        voltage_array = [self.adc_voltage_transform(v[0], v[1], v[2], option)
                         for v in large_adcv]
        
        # python plot 
        sampling_rate = self._sampling_rate
        Ts = 1 / sampling_rate
        xdata = np.linspace(Ts, N * Ts, N)
        
        plt.figure(figsize = (7, 7))
        plt.plot(xdata * 1e3, voltage_array,'ob', label='ADC data')
        
        # Fit function
        # Initial guess with fft
        freq_difference = None
        try:
            Y = np.fft.fft(voltage_array)/N
        except Exception as e:
            print(f"adc_load_large_data: failed to run fft: {e!r}")
        else:
            mY = np.abs(Y)
            locY = np.argmax(mY[1:]) + 1
            freq_guess = np.abs(np.fft.fftfreq(N, d=Ts)[locY])
            voltage_max, voltage_min = np.max(voltage_array), np.min(voltage_array)
            ampl_guess = (voltage_max - voltage_min) / 2
            offset_guess = (voltage_max + voltage_min) / 2
            # fit_func(t) = ampl * np.sin(2 * np.pi * freq * t + phase) + offset
            phase_guess = np.arcsin((voltage_array[0] - offset_guess) / ampl_guess) - 2 * np.pi * freq_guess * xdata[0]

            # Fit with initial guess
            try:
                popt, pcov = curve_fit(self.fit_func, xdata, voltage_array, [ampl_guess, freq_guess, phase_guess, offset_guess])
            except Exception as e:
                print(f"adc_load_large_data: failed to curve_fit: {e!r}")
            else:
                freq_difference = np.abs(popt[1]) # fitted frequency
                fit_xdata = np.linspace(min(xdata), max(xdata), 200)
                plt.plot(fit_xdata * 1e3, self.fit_func(fit_xdata, *popt), '--r', label = f'Fitted result, freq = {freq_difference:.2f} Hz')
        plt.title(f'ADC Data Read (sampling rate = {sampling_rate:.2f} Hz)')
        plt.xlabel('Time (ms)')
        plt.ylabel('ADC Voltage (V)')
        plt.legend(fontsize = 20)
        plt.legend(loc = 'upper right')
        plt.show()
        
        # making excel file
        df = DataFrame(tuple(enumerate(voltage_array)), columns=['time', 'voltage'])
        writer = pd.ExcelWriter('Manual lock ADC read.xlsx',engine='xlsxwriter')#writer instance
        df.to_excel(writer, sheet_name='Sheet1')#write to excel
        
        workbook=writer.book
        worksheet= writer.sheets['Sheet1']
        
        chart=workbook.add_chart({'type':'line'})#choose data
        
        chart.add_series({'values':'=Sheet1!$C$2:$C$101'})
        worksheet.insert_chart('D2',chart)
        chart.set_y_axis({'min': 2 * np.min(voltage_array), 'max': 2 * np.max(voltage_array)})

        writer.close()
        
        return freq_difference # return fitted frequency
        
    ##########################################
    # ETC
    ##########################################
    def const_shoot(self):
        cmd = 'CONST SHOOT'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)
        
    def user_sampling(self): # user defined sampling
        cmd = 'USER SAMPLING' 
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)

    def user_sampling_rate(self, rate):
        """Sets the sampling rate of the user defined sampling.

        We use simple clock down conversion for it, hence we need to calculate
          the number of cycles of the half of the sampling period.
        It uses 4 bytes to count the clock cycles, hence the half-period cycles
          should be in [1, 0xffffffff].

        Args:
            rate: Desired sampling rate in Hz. However, the sampling rate must
              satisfy: (main clock frequency) / (2*n), where the main clock
              frequency is 100MHz and n is a natural number. If the given
              sampling rate is not valid, the closest valid rateis selected.

        Retruns:
            Applied new sampling rate in Hz.
        """
        cmd = 'SAMPLING RATE'
        cmd_up = 'UPDATE'

        target_half_period = round(50e6 / rate)  # number of cycles
        clipped = max(1, target_half_period & 0xffffffff)  # clip
        message = [clipped >> 24, (clipped >> 16) & 0xff, (clipped >> 8) & 0xff, clipped & 0xff]

        self.fpga.send_command(cmd_up)
        self.fpga.send_mod_BTF_int_list(message)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(message)
            print(cmd)
        actual_rate = 50e6 / clipped
        self._sampling_rate = actual_rate
        return actual_rate
        
    def terminate_condition(self): # termnitate const_shoot and user_sampling
        cmd = 'TERM COND'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        if self.verbose:
            print(cmd)
    
    def normal_feedback(self, channel):
        """Sets the feedback direction to 'normal'.

        Args:
            channel: 1, 2, or 3. Each corresponds to the AOM DDS channel.
        """
        # turn off DDS 
        self.dds_stop()
        
        cmd = f'NORMAL {channel}'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        
        # turn on DDS 
        self.dds_start()
        if self.verbose:
            print(cmd)
        
    def reverse_feedback(self, channel):
        """Sets the feedback direction to 'reversed'.

        When the feedback direction is 'reversed', the compensation sign
          is opposite to that of the normal feedback direction configuration.

        Args:
            channel: 1, 2, or 3. Each corresponds to the AOM DDS channel.
        """
        # turn off DDS 
        self.dds_stop()
        
        cmd = f'REVERSE {channel}'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        
        # turn on DDS 
        self.dds_start()
        if self.verbose:
            print(cmd)
        
    def single_pass(self, channel):
        """Sets the AOM path configuration to 'single pass'.

        Args:
            channel: 1, 2, or 3. Each corresponds to the AOM DDS channel.
        """
        # turn off DDS
        self.dds_stop()
        
        cmd = f'SINGLE PASS {channel}'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        
        # turn on DDS
        self.dds_start()
        if self.verbose:
            print(cmd)
        
    def double_pass(self, channel):
        """Sets the AOM path configuration to 'double pass'.

        When the AOM path is 'double pass', the compensation value is
          divided by 2 since the beam passes through the AOM twice, hence
          the frequency change is applied twice.

        Args:
            channel: 1, 2, or 3. Each corresponds to the AOM DDS channel.
        """
        # turn off DDS
        self.dds_stop()
        
        cmd = f'DOUBLE PASS {channel}'
        cmd_up = 'UPDATE'
        self.fpga.send_command(cmd_up)
        self.fpga.send_command(cmd)
        
        # turn on DDS
        self.dds_start()
        if self.verbose:
            print(cmd)
        
    def read_freuquency(self):
        cmd_load='LOAD LARGE'
        self.fpga.send_command(cmd_load)
        if self.verbose:
            print(cmd_load)
            print(self.fpga.read_next_message())
        

class RamanPIDDDS:
    """A individual DDS wrapper to implement the rfsrc interface."""
    def __init__(self, pid, board, channel):
        """
        Args:
            pid: Raman_PID_Controller object.
            board: Board index - 1 or 2.
            channel: Channel index - 1 or 2.
        """
        self.pid = pid
        self.board = board
        self.channel = channel
        self._output_enabled = False
        self._freq = None
        self._power = None
        self._phase = None

    
if __name__ == '__main__':
    if 'fpga' in vars(): # To close the previously opened device when re-running the script with "F5"
        fpga.close()
    fpga = ArtyS7('COM6') 
    fpga.print_idn()
    
    dna_string = fpga.read_DNA() 
    print('FPGA DNA string:', dna_string)

    pid = Raman_PID_Controller(fpga)    
    
"""
pid.adc_range_select()
pid.set_current(1023, 1, 1)
pid.set_frequency(360.0000, 1, 0) 
pid.set_frequency(143.0000, 0, 1)
pid.reverse_feedback()
pid.user_sampling()

pid.comp_set(50000, 1000, 0)
pid.comp_start()
pid.comp_stop()

pid.comp_set_setpoint(code = 0b100000000000000000)

pid.load_data()
pid.adc_load_large_data()

for i in range(1, 5):
    pid.load_data()
    time.sleep(0.5)

pid.terminate_condition()

pid.power_down(1, 1)
pid.power_up(1, 1)
pid.normal_feedback()

"""    
    
    
    