"""
Created on Nov 21, 2021
@author: Junho Jeong
"""

from SequencerProgram_v1_07 import SequencerProgram, reg
import SequencerUtility_v1_01 as su
from ArtyS7_v1_02 import ArtyS7
import HardwareDefinition_SNU_v4_02 as hd

T_100us = 10000-3-2
EXPOSURE_TIME_IN_MS = 1
NUM_REPEAT = 50

s = SequencerProgram()
s.load_immediate(reg[0], 0, 'reg[0]: measurement number')

s.repeat_measurement = \
\
s.load_immediate(reg[1], 0, 'reg[1]: exposure time so far, in units of 1us')
s.trigger_out([hd.PMT_counter_reset], 'Reset single counter')
s.set_output_port(hd.counter_control_port, [(hd.PMT_counter_enable, 1), ], 'Start counter')

s.continue_exposure = \
\
s.wait_n_clocks(T_100us, 'Wait for 100 * 10 ns = 1us unconditionally')
s.add(reg[1], reg[1], 1)
s.branch_if_less_than('continue_exposure', reg[1], EXPOSURE_TIME_IN_MS)

s.set_output_port(hd.counter_control_port, [(hd.PMT_counter_enable, 0), ], 'Stop counter')

s.read_counter(reg[2], hd.PMT_counter_result)
s.write_to_fifo(reg[0], reg[1], reg[2], 10, '[measurement number, exposure time in us, PMT count')

s.add(reg[0], reg[0], 1, 'measurement number++')
s.branch_if_less_than('repeat_measurement', reg[0], NUM_REPEAT)
s.stop()