#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

import pcraster as pcr

import configuration
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

# get the configuration/ini file given in the system argument
iniFileName = os.path.abspath(sys.argv[1])

# option for debugging
debug_option = str(sys.argv[2])

# object to handle configuration/ini file
generalConfiguration = configuration.Configuration(iniFileName = iniFileName, debug_mode = False, no_modification = False)

# make log folder and initialize logging
generalOutputFolder = generalConfiguration.globalOptions['outputDir']
logFileFolder = generalOutputFolder+"/global_log/"
if os.path.exists(logFileFolder): shutil.rmtree(logFileFolder)
os.makedirs(logFileFolder)
generalConfiguration.initialize_logging(logFileFolder)

# pcr-globwb clone areas (for pcr-globwb multiple runs)
clone_codes = list(set(generalConfiguration.globalOptions['cloneAreas'].split(",")))
if clone_codes[0] == "Global": clone_codes = ['M%02d'%i for i in range(1,54,1)]

# TODO: run a steady state modflow to estimate the initial values for relativeGroundwaterHead, storGroundwater and baseflow

# command lines for PCR-GLOBWB 
i_clone = 0
cmd = ''
for clone_code in clone_codes:

   cmd += "python deterministic_runner_glue_coupled_to_modflow.py " + iniFileName +" "+\
                                                                      debug_option +" "+\
                                                                      clone_code +" "+\
                                                                      "-0.25 0.00 1.00"+" "
   cmd = cmd+" & "
   i_clone += 1

#~ # command line for MODFLOW       
#~ cmd += "python "       
#~ cmd = cmd+" & "       

# don't foget to add the following line
cmd = cmd + "wait"       

print cmd

# execute PCR-GLOBWB and MODFLOW
vos.cmd_line(cmd, using_subprocess = False)      
