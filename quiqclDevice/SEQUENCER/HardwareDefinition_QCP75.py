# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 07:59:12 2018

@author: Junho Jeong

According to the given mapping, we will add alias for each pin
"""

from HardwareDefinition_v4_02 import *

HW_VERSION = ""

# Input port pin mapping
# For input pin, there will be only one driver
input_mapping = {'jb_2': 'PMT',
                 'jb_4': 'PMT2', 
                 'ja_2': 'PMT3'}

# Output port pin mapping
# For output pin, there might be more than one device controlled by the output pin
output_mapping = {'EOM_2G': 'jb_7', 'EOM_7G_1': 'jb_1', 'EOM_7G_2': 'jb_3', 'AOM1': 'jb_5', 'MW': 'ja_3', 'AOM2': 'ja_1', "TEST": "jd_3"}
description = {'EOM_2G': 'Initialization beam',
               'EOM_7G_1': 'Cooling sideband',
               'EOM_7G_2': 'Cooling sideband',
               'AOM1': 'Turning beam on/off',
               'MW': 'Turing MW on/off',
               'AOM2': 'Cooling beam for 170',
               'TEST': 'Test pin for jd_3'}

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
