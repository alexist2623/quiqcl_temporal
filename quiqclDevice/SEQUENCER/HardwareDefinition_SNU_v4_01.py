# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 07:59:12 2018

@author: 1109282

According to the given mapping, we will add alias for each pin
"""

from HardwareDefinition_v4_01 import *

# Input port pin mapping
# For input pin, there will be only one driver
input_mapping = {'jb_0': 'shutter_control', 'jb_2': 'PMT1', 'ja_2': 'pulse_trigger'}

# Output port pin mapping
# For output pin, there might be more than one device controlled by the output pin
output_mapping = {'Microwave_12_6GHz': 'ja_3', \
                  'EOM_14_7GHz' : 'jb_1', \
                  'EOM_2_1GHz_off'  : 'jb_3', \
                  'AOM_200_205MHz': 'jb_5', \
                  'AOM_off' : 'jb_7', \
                  'external_trigger' : 'ja_6',\
				  'Raman_global_off' : 'ja_1', \
				  'Raman_R1_R2' : 'ja_4', \
				  'Raman_C_R_off' : 'ja_0',
				  'Raman_indiv_off' : 'ja_7'
				  }

#refer to HardwareDefinition_v4_01 for manual mode mapping
manual_output_mapping = {'Microwave_12_6GHz': 17, \
                  'EOM_14_7GHz' : 19, \
                  'EOM_2_1GHz_off'  : 20, \
                  'AOM_200_205MHz': 21, \
                  'AOM_off' : 22, \
                  'external_trigger' : 27,\
                  'Raman_global_off' : 24,\
				  'Raman_R1_R2' : 25,\
				  'Raman_C_R_off' : 23,
				  'Raman_indiv_off' : 18
				  }
   
# Switch connection - map the toggle (enable / disable) to the physical TTL (1 / 0): value = [enable TTL, disable TTL]  
true_TTL = {'Microwave_12_6GHz': [1, 0], \
            'EOM_14_7GHz' : [1, 0], \
            'EOM_2_1GHz_off'  : [1, 0], \
            'AOM_200_205MHz': [1, 0], \
            'AOM_off' : [1, 0], \
            'external_trigger' : [1, 0],
            'Raman_global_off' : [1, 0],\
            'Raman_R1_R2' : [1, 0], \
            'Raman_C_R_off' : [1, 0], \
			'Raman_indiv_off' : [1, 0]
			}   # AOM_200_205MHz - 1 : 205 MHz, 0 : 200 MHz 

# Output port configuration
C1_phase_shifter_port = 2
C2_phase_shifter_port = 3
    
var_dict = globals()
var_list = list(var_dict.keys())

for each_var in var_list:
    for (pin_name, mapping_name) in input_mapping.items():
        pin_name += '_'
        mapping_name += '_'
        index_found = each_var.find(pin_name)
        if index_found == -1:
            continue
        if index_found != 0:
            print('There is a variable (%s) whose name contains %s in the middle' \
                  % (each_var, pin_name))
            continue
        new_var_name = mapping_name + each_var[len(pin_name):]
        var_dict[new_var_name] = var_dict[each_var]

    for (mapping_name, pin_name) in output_mapping.items():
        pin_name += '_'
        mapping_name += '_'
        index_found = each_var.find(pin_name)
        if index_found == -1:
            continue
        if index_found != 0:
            print('There is a variable (%s) whose name contains %s in the middle' \
                  % (each_var, pin_name))
            continue
        new_var_name = mapping_name + each_var[len(pin_name):]
        var_dict[new_var_name] = var_dict[each_var]
