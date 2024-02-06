"""
Created on Nov 21, 2021
@author: Junho Jeong
"""
from SequencerProgram_v1_07 import SequencerProgram, reg
import SequencerUtility_v1_01 as su
from ArtyS7_v1_02 import ArtyS7
import HardwareDefinition_SNU_v4_02 as hd

NUMBER_OF_AVERAGE = 3000
INIT_TIME_IN_US = 150
DETECTION_TIME_IN_US = 150
MICROWAVE_TIME_IN_US = 50

s = SequencerProgram()
s.load_immediate(reg[0], 0, 'reg[0]: microwave_time')
s.load_immediate(reg[1], 0, 'reg[1]: measurement_index')

s.repeat_run = \
\
s.load_immediate(reg[2], 0, 'reg[2]: number_of_photons')
s.load_immediate(reg[5], 0, 'reg[5]: pre-cooling_time')
s.load_immediate(reg[6], MICROWAVE_TIME_IN_US, 'reg[6]: microwave_time')

s.set_output_port(hd.external_control_port, [(hd.EOM_7G_1_out, 1), (hd.EOM_7G_2_out, 1), (hd.AOM_out, 1)], 'Start Cooling')
s.repeat_1ms = \
\
s.wait_n_clocks(50000-3-2, 'Cooling for 0.5 ms')
s.add(reg[5], reg[5], 1, 'reg[5]++')
s.branch_if_less_than('repeat_1ms', reg[5], 4, 'Wait for 2 ms')

s.set_output_port(hd.external_control_port, [(hd.EOM_7G_1_out, 0), (hd.EOM_7G_2_out, 0), (hd.EOM_2G_out, 1)], 'Start Initialization')
s.wait_n_clocks( int(INIT_TIME_IN_US*100 - 3 ), 'Initialization')
s.set_output_port(hd.external_control_port, [(hd.AOM_out, 0),(hd.EOM_2G_out, 0)], 'End Initialization')
s.wait_n_clocks(270, 'Wait for the AOM completely off, 2.7 us')

s.repeat_microwave = \
\
s.branch_if_equal('skip_microwave', reg[6], 0, 'Microwave is off when reg[6] is 0')
s.set_output_port(hd.external_control_port, [(hd.MW_out, 1)], 'Start Qubit control')
s.wait_n_clocks( int(MICROWAVE_TIME_IN_US*100-7), 'microwave_out')
s.set_output_port(hd.external_control_port, [(hd.MW_out, 0)], 'End Qubit control')
s.wait_n_clocks(10, 'Wait until MW is completely off')

s.skip_microwave = \
\
s.set_output_port(hd.external_control_port, [(hd.AOM_out, 1)], 'Start Detection')
s.wait_n_clocks(250, 'Wait for AOM ON')
s.trigger_out([hd.PMT_counter_reset], 'Reset single counter')
s.nop()
s.set_output_port(hd.counter_control_port, [(hd.PMT_counter_enable, 1)], 'Start counter')
s.wait_n_clocks( int(DETECTION_TIME_IN_US*100-3), 'Detection time')
s.set_output_port(hd.counter_control_port, [(hd.PMT_counter_enable, 0)], 'Stop counter')
s.read_counter(reg[2], hd.PMT_counter_result)
s.write_to_fifo(reg[0], reg[1], reg[2], 15, 'Save to fifo')

s.set_output_port(hd.external_control_port, [(hd.EOM_7G_1_out, 1), (hd.EOM_7G_2_out, 1), (hd.AOM_out, 1)], 'Resume Cooling')

s.add(reg[1], reg[1], 1)
s.branch_if_less_than('repeat_run', reg[1], NUMBER_OF_AVERAGE, 'Repeat')

s.stop()