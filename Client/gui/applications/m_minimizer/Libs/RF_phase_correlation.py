# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 17:16:41 2019

@author: JJH
JJH Editted.
"""

from SequencerProgram_v1_07 import SequencerProgram, reg
import SequencerUtility_v1_01 as su
from ArtyS7_v1_02 import ArtyS7
import HardwareDefinition_SNU_v4_02 as hd

RF_FREQ = 23758  # kHz
SUCCESS_NUMBER = 50000
N = 50000
T_N = 1

rf_freq = RF_FREQ/1000


stopwatch_time_resolution = 1.25
RF_period = int(1000 / stopwatch_time_resolution / rf_freq / 3)* 3
max_time_diff_to_record = RF_period * T_N
waiting_time_for_stopwatch = int((RF_period + max_time_diff_to_record)/8)


run_counter_R = reg[0]
run_counter_2_R = reg[1]
sw_flags_R = reg[2]
pulse_trigger_timing_R = reg[3]
PMT_timing_R = reg[4]
time_diff_R = reg[5]
success_counter_R = reg[6]

s = SequencerProgram()
s.load_immediate(reg[11], 0) # Reset value for the momery initialization
s.load_immediate(reg[10], 0)
        
s.memory_initialization = \
\
s.store_word_to_memory(reg[10], reg[11])
s.add(reg[10], reg[10], 1)
s.branch_if_less_than('memory_initialization', reg[10], max_time_diff_to_record)
        
#Reset run_number
s.load_immediate(run_counter_R, 0, 'reg[0] will be used for run number')
s.load_immediate(run_counter_2_R, 0, 'reg[1] will be used for run number')
s.load_immediate(success_counter_R, SUCCESS_NUMBER, 'reg[6] will be used for success number')
        
# Start stopwatches
s.repeat = \
\
s.trigger_out([hd.PMT_stopwatch_reset , hd.pulse_trigger_stopwatch_reset, ], 'Reset stopwatches')
s.nop() # Between reset and start of the stopwatches, add at least one clock
s.trigger_out([hd.PMT_stopwatch_start, hd.pulse_trigger_stopwatch_start, ], 'Start stopwatches')
            
s.wait_n_clocks(waiting_time_for_stopwatch-3, 'Waiting time is compensated for single shot input')
        
# Collect the result of stopwatch measurements
s.read_counter(sw_flags_R,              hd.Trigger_level, 'Read status of stopwatches')                                     # hd.Trigger_level = counter[14]
s.read_counter(pulse_trigger_timing_R,  hd.pulse_trigger_stopwatch_result, 'Read pulse trigger stopwatch result')           # hd.pulse_trigger_stopwatch_result = counter[10]
s.read_counter(PMT_timing_R,           hd.PMT_stopwatch_result, 'Read PMT stopwatch result')                             # hd.PMT_stopwatch_result = counter[7]
        
        
        # The following types of check can be removed, but here they are included for
        # debugging purpose
        
        # Check if pulse_trigger has arrived
s.branch_if_equal_with_mask('check_PMT_triggered', sw_flags_R, 1 << hd.pulse_trigger_stopwatch_stopped_TLI , 1 << hd.pulse_trigger_stopwatch_stopped_TLI)
s.jump('decide_repeat')
        
        
# Check if PMT trigger is detected
s.check_PMT_triggered = \
\
s.branch_if_equal_with_mask('check_if_pulse_trigger_arrived_before_PMT', sw_flags_R, 1 << hd.PMT_stopwatch_stopped_TLI, 1 << hd.PMT_stopwatch_stopped_TLI)
s.jump('decide_repeat')
        
        
# Check if pulse trigger arrived before PMT
s.check_if_pulse_trigger_arrived_before_PMT = \
\
s.branch_if_less_than('calculate_time_difference', pulse_trigger_timing_R, PMT_timing_R)
s.jump('decide_repeat')
        
        
# Calculate time difference and decide whether it lies between the desired range
s.calculate_time_difference = \
\
s.subtract(time_diff_R, PMT_timing_R, pulse_trigger_timing_R)
s.branch_if_less_than('store_time_difference', time_diff_R, max_time_diff_to_record)
s.jump('decide_repeat')

s.store_time_difference = \
\
s.subtract(success_counter_R, success_counter_R, 1, 'success_counter--')
s.load_word_from_memory(reg[10], time_diff_R)
s.add(reg[10], reg[10], 1)
s.store_word_to_memory(time_diff_R, reg[10])

# Decide whether we will repeat running
s.decide_repeat = \
\
s.branch_if_less_than('transfer_statistics', success_counter_R, 1)
s.add(run_counter_2_R, run_counter_2_R, 1, 'run_counter_2_R++')
s.branch_if_less_than('repeat', run_counter_2_R, SUCCESS_NUMBER)
s.load_immediate(run_counter_2_R, 0, 'reg[5] reset')
s.add(run_counter_R, run_counter_R, 1, 'run_counter_R++')
s.branch_if_less_than('repeat', run_counter_R, N)

# Transfer the statistics
# We will read three values stored in the consecutive address and write them into FIFO
s.transfer_statistics = \
\
s.load_immediate(reg[10], 0, 'reg[10] is used as address pointer and counter')
s.transfer_repeat = \
\
s.load_word_from_memory(reg[11], reg[10])
s.add(reg[10], reg[10], 1)
s.load_word_from_memory(reg[12], reg[10])
s.add(reg[10], reg[10], 1)
s.load_word_from_memory(reg[13], reg[10])
s.add(reg[10], reg[10], 1)
s.write_to_fifo(reg[11], reg[12], reg[13], 100)
s.branch_if_less_than('transfer_repeat', reg[10], max_time_diff_to_record)
        
s.stop()