# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 17:16:41 2019

@author: JJH
JJH Editted.
"""

#%%
import sys
import os
new_path = os.path.dirname(__file__) + '\\..'
if not (new_path in sys.path):
    sys.path.append(new_path)
#%%
#new_path = "Q:/Experiment_Scripts/Chamber_1S_UNITED_TEST/Reinforcement_Learning_v0_01/value_calulcation_libraries" + '\\..'
sys.path.append("Q://Experiment_Scripts/Chamber_1S_SNU/Sequencer Library/v4_01/python/")

from SequencerProgram_v1_07 import SequencerProgram, reg
import SequencerUtility_v1_01 as su
from ArtyS7_v1_02 import ArtyS7
import HardwareDefinition_1S_test2 as hd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import datetime
import pickle
from scipy.optimize import curve_fit

data_dir = os.path.dirname(__file__) +'/data/'
# data_dir = "Q:/Experiment_Scripts/Chamber_1S_UNITED_TEST/Reinforcement_Learning_v0_01/value_calulcation_libraries" +'/data/'
custom_file_name = '_174_frerquency_460_weak_cooling'
RF_freq = 23.7581  # MHz



def func(x, a, b, c):
    return a*np.cos(x+b)+c
   
class RF_phase_correlation():
    
    stopwatch_time_resolution = 1.25    # [ns]
    
    def __init__(self,
                 success_number = 50000,
                 N = 1,                 # max_run_time = N * success_number
                 T_N = 3,               # Save the data for T_N RF period
                 port = 'COM4', 
                 RF_freq = 23.835       # [MHz]
                 ):

        self.success_number = success_number
        self.N = N
        self.T_N = T_N
        self.port = port
        self.RF_freq = RF_freq
        self.RF_period = int(1000 / self.stopwatch_time_resolution / self.RF_freq / 3)* 3
        self.max_time_diff_to_record = self.RF_period * self.T_N
        self.waiting_time_for_stopwatch = int((self.RF_period + self.max_time_diff_to_record)/8)
        
        self.run_counter_R = reg[0]
        self.run_counter_2_R = reg[1]
        self.sw_flags_R = reg[2]
        self.pulse_trigger_timing_R = reg[3]
        self.PMT1_timing_R = reg[4]
        self.time_diff_R = reg[5]
        self.success_counter_R = reg[6]
        
        self.setup_RF_correlation_program()
        
    def setup_RF_correlation_program(self):

        self.s = SequencerProgram()
        self.s.load_immediate(reg[11], 0) # Reset value for the momery initialization
        self.s.load_immediate(reg[10], 0)
        
        self.s.memory_initialization = \
        \
        self.s.store_word_to_memory(reg[10], reg[11])
        self.s.add(reg[10], reg[10], 1)
        self.s.branch_if_less_than('memory_initialization', reg[10], self.max_time_diff_to_record)
        
        #Reset run_number
        self.s.load_immediate(self.run_counter_R, 0, 'reg[0] will be used for run number')
        self.s.load_immediate(self.run_counter_2_R, 0, 'reg[1] will be used for run number')
        self.s.load_immediate(self.success_counter_R, self.success_number, 'reg[6] will be used for success number')
        
        # Start stopwatches
        self.s.repeat = \
        \
        self.s.trigger_out([hd.PMT1_stopwatch_reset , hd.pulse_trigger_stopwatch_reset, ], 'Reset stopwatches')
        self.s.nop() # Between reset and start of the stopwatches, add at least one clock
        self.s.trigger_out([hd.PMT1_stopwatch_start, hd.pulse_trigger_stopwatch_start, ], 'Start stopwatches')
        
        
        self.s.wait_n_clocks(self.waiting_time_for_stopwatch-3, 'Waiting time is compensated for single shot input')
        
        # Collect the result of stopwatch measurements
        self.s.read_counter(self.sw_flags_R,              hd.Trigger_level, 'Read status of stopwatches')                                     # hd.Trigger_level = counter[14]
        self.s.read_counter(self.pulse_trigger_timing_R,  hd.pulse_trigger_stopwatch_result, 'Read pulse trigger stopwatch result')           # hd.pulse_trigger_stopwatch_result = counter[10]
        self.s.read_counter(self.PMT1_timing_R,           hd.PMT1_stopwatch_result, 'Read PMT1 stopwatch result')                             # hd.PMT1_stopwatch_result = counter[7]
        
        
        # The following types of check can be removed, but here they are included for
        # debugging purpose
        
        # Check if pulse_trigger has arrived
        self.s.branch_if_equal_with_mask('check_PMT1_triggered', self.sw_flags_R, \
            1 << hd.pulse_trigger_stopwatch_stopped_TLI , 1 << hd.pulse_trigger_stopwatch_stopped_TLI)
        self.s.jump('decide_repeat')
        
        
        # Check if PMT1 trigger is detected
        self.s.check_PMT1_triggered = \
        \
        self.s.branch_if_equal_with_mask('check_if_pulse_trigger_arrived_before_PMT1', self.sw_flags_R, \
            1 << hd.PMT1_stopwatch_stopped_TLI, 1 << hd.PMT1_stopwatch_stopped_TLI)
        self.s.jump('decide_repeat')
        
        
        # Check if pulse trigger arrived before PMT1
        self.s.check_if_pulse_trigger_arrived_before_PMT1 = \
        \
        self.s.branch_if_less_than('calculate_time_difference', self.pulse_trigger_timing_R, self.PMT1_timing_R)
        self.s.jump('decide_repeat')
        
        
        # Calculate time difference and decide whether it lies between the desired range
        self.s.calculate_time_difference = \
        \
        self.s.subtract(self.time_diff_R, self.PMT1_timing_R, self.pulse_trigger_timing_R)
        self.s.branch_if_less_than('store_time_difference', self.time_diff_R, self.max_time_diff_to_record)
        self.s.jump('decide_repeat')
        
        
        self.s.store_time_difference = \
        \
        self.s.subtract(self.success_counter_R, self.success_counter_R, 1, 'success_counter--')
        self.s.load_word_from_memory(reg[10], self.time_diff_R)
        self.s.add(reg[10], reg[10], 1)
        self.s.store_word_to_memory(self.time_diff_R, reg[10])
        
        # Decide whether we will repeat running
        self.s.decide_repeat = \
        \
        self.s.branch_if_less_than('transfer_statistics', self.success_counter_R, 1)
        self.s.add(self.run_counter_2_R, self.run_counter_2_R, 1, 'run_counter_2_R++')
        self.s.branch_if_less_than('repeat', self.run_counter_2_R, self.success_number)
        self.s.load_immediate(self.run_counter_2_R, 0, 'reg[5] reset')
        self.s.add(self.run_counter_R, self.run_counter_R, 1, 'run_counter_R++')
        self.s.branch_if_less_than('repeat', self.run_counter_R, self.N)
        
        
        # Transfer the statistics
        # We will read three values stored in the consecutive address and write them into FIFO
        self.s.transfer_statistics = \
        \
        self.s.load_immediate(reg[10], 0, 'reg[10] is used as address pointer and counter')
        self.s.transfer_repeat = \
        \
        self.s.load_word_from_memory(reg[11], reg[10])
        self.s.add(reg[10], reg[10], 1)
        self.s.load_word_from_memory(reg[12], reg[10])
        self.s.add(reg[10], reg[10], 1)
        self.s.load_word_from_memory(reg[13], reg[10])
        self.s.add(reg[10], reg[10], 1)
        self.s.write_to_fifo(reg[11], reg[12], reg[13], 100)
        self.s.branch_if_less_than('transfer_repeat', reg[10], self.max_time_diff_to_record)
        
        self.s.stop()

        print("setup_RF_correlation_program is completed")
        

    def run(self):
        #if 'sequencer' in vars(): # To close the previously opened device when re-running the script with "F5"
        #    sequencer.close()
        self.sequencer = ArtyS7(self.port)
        self.sequencer.check_version(hd.HW_VERSION)
        self.s.program(show=False, target=self.sequencer)
        self.sequencer.auto_mode()
        self.sequencer.send_command('START SEQUENCER')
        
        start_time = time.time()
        while(self.sequencer.sequencer_running_status() == 'running'):
            time.sleep(1)
        end_time = time.time()
        
        test_time = end_time - start_time
        self.arrival_time = []
        data_count = self.sequencer.fifo_data_length()
        if data_count:
            self.data = self.sequencer.read_fifo_data(data_count)
            for each in self.data:
                self.arrival_time += each[0:3]
    
            
            print("Test time = %d sec" % test_time)
            print('Overall trial =', self.N * self.success_number)
            print('Successful trial =',sum(self.arrival_time))
        
        print(self.arrival_time)
        self.sequencer.flush_Output_FIFO()
        self.sequencer.close()
        
        minmax_normalization = 1
        return [self.arrival_time, minmax_normalization]
    
    def data_fitting(self, arrival_time):
        """
        This functions fits the data to a sine function and retunrs optimized prameters, covariances and visibility.
        """
        x_fit = np.arange(1, len(arrival_time))/len(arrival_time)*2*np.pi
        popt, pcov = curve_fit(func, x_fit, arrival_time[1:len(arrival_time)])

        visibility = abs(popt[0]/popt[2])
        
        x = np.arange(len(arrival_time))
        x_data = x[1:len(arrival_time)]*1.25
        y_data = arrival_time
        
        y_fit =  func(x_fit, *popt)
        #return popt, pcov, visibility
        return x_data, y_data, x_fit, y_fit, visibility

    def plot_data(self, arrival_time, popt, figure_view = False):
        if not figure_view: plt.ioff()
        else:               plt.ion()
        
        x = np.arange(len(arrival_time))
        fig, axs = plt.subplots(1, 1, tight_layout=True)
        axs.bar(x*1.25, arrival_time)
        x_fit = np.arange(1, len(arrival_time))/len(arrival_time)*2*np.pi
        axs.plot = plt.plot(x[1:len(arrival_time)]*1.25, func(x_fit, *popt), color='r')
        axs.set_title('Photon arrival time distribution w.r.t. pulse picker trigger output')
        axs.set_xlabel('PMT arrival time w.r.t. pulse picker trigger output (ns)')
        axs.set_ylabel('Number of event')
        
        time_header = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
        freq_header = '%0.4f_MHz' %  self.RF_freq
        
        fig.savefig(data_dir + time_header + freq_header + custom_file_name + '.png', dpi=150)
        
        return
        
    def save_data(self, arrivial_time):
        x = np.arange(len(arrivial_time)) * self.stopwatch_time_resolution
        y = arrivial_time
        
        description = "x_data is the time data with the resolution of 1.25 ns, y_data is the number of events.\
                       they are already arranged. if you want to plot the result, simply plt.plot(x_data, y_data).\
                       I saved the plotter as a reference for the plot during the experiment."
        
        pkl_data = { 'x_data': x, 'y_data': y, 'description': description, 'freq': self.RF_freq, 'time_resol': '%0.3f ns' % self.stopwatch_time_resolution }
        csv_data = pd.DataFrame(y, index=x)
        
        time_header = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
        freq_header = '%0.4f_MHz' %  self.RF_freq
        
        with open (data_dir + time_header + freq_header + custom_file_name + '.pkl', 'wb') as fw:
            pickle.dump(pkl_data, fw)
            
        csv_data.to_csv(data_dir + time_header + freq_header + custom_file_name + '.csv', mode='w', header=False)
        
        return
        
            
#%%
if __name__ == '__main__':
    RF_program = RF_phase_correlation(success_number = 20000, N = 20000, T_N = 1, RF_freq = RF_freq)
    #mm_list = []
    for i in range(1):
        [data, minmax_normalization] = RF_program.run()
        #print(data)
        #mm_list.append(minmax_normalization)
        #print('minmax =', minmax_normalization)
        popt, pcov, visibility = RF_program.data_fitting(data)
        
        RF_program.plot_data(data)
        RF_program.save_data(data)
        
    #print(mm_list)
    
"""
import threading
t = threading.Thread(target=RF_program.run)
t.start()

import time
def my_stopper(timeout):
    timeout
    while timeout > 0:
        time.sleep(1)
        timeout -= 1
        if RF_program.sequencer.sequencer_running_status() == 'running':
            print(timeout)
        else:
            print("RF_program looks good")
            break
    print('stopping')
    RF_program.sequencer.stop_sequencer()
    print('stopped.')
   
t2 = threading.Thread(target=my_stopper, args=[5])
t2.start()

t.join()
t2.join()
#time.sleep(2)
#RF_program.sequencer.flush_Output_FIFO()
#RF_program.sequencer.close()
print("\n ion lost\n")
"""