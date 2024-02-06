# -*- coding: utf-8 -*-
"""
Base Switch Test script
"""
#%%
import sys
import os, time
import datetime

from SequencerProgram_v1_08 import SequencerProgram, reg
import SequencerUtility_v1_03 as su
from ArtyS7_v1_02 import ArtyS7
import HardwareDefinition_QCP75 as hd

out_list = []

s=SequencerProgram()

s.set_output_port(hd.external_control_port, [(hd.AOM1_out, 1), ])

s.stop()
#%%

if __name__ == '__main__':
    if 'sequencer' in vars(): # To close the previously opened device when re-running the script with "F5"
        sequencer.close()
    sequencer = ArtyS7('COM4')
    sequencer.check_version(hd.HW_VERSION)
    s.program(show=False, target=sequencer)
    sequencer.auto_mode()

    sequencer.start_sequencer()
    
    # while (sequencer.sequencer_running_status() == 'running'):
    #     time.sleep(0.01)
    
    sequencer.close()