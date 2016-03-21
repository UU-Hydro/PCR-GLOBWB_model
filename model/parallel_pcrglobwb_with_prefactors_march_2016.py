#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import glob
import datetime

import pcraster as pcr

import configuration
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

# get the configuration/ini file given in the system argument
iniFileName = os.path.abspath(sys.argv[1])

# option for debuging and paralelization 
debug_option = "parallel"
if len(sys.argv) > 2: debug_option = str(sys.argv[2]) 

# object to handle configuration/ini file
generalConfiguration = configuration.Configuration(iniFileName = iniFileName, debug_mode = False, no_modification = False)

# clean any files exists on the ouput directory
clean_previous_output = True
if clean_previous_output and os.path.exists(generalConfiguration.globalOptions['outputDir']): shutil.rmtree(generalConfiguration.globalOptions['outputDir'])

# make log folder and initialize logging
generalOutputFolder = generalConfiguration.globalOptions['outputDir']
logFileFolder = generalOutputFolder + "/global/log/"
if os.path.exists(logFileFolder): shutil.rmtree(logFileFolder)
os.makedirs(logFileFolder)
generalConfiguration.initialize_logging(logFileFolder)

# copy ini file to the log folder:
timestamp = datetime.datetime.now()
logger.info('Copying ini file to the folder %s', logFileFolder)
shutil.copy(iniFileName, logFileFolder + \
                         os.path.basename(iniFileName) + '_' +  str(timestamp.isoformat()).replace(":",".") + '.ini')

# make global output maps directory (it will contain a "maps" directory that will contain merged pcraster maps)
global_maps_folder = generalConfiguration.globalOptions['outputDir']+"/global/maps/"
if os.path.exists(global_maps_folder): shutil.rmtree(global_maps_folder)
os.makedirs(global_maps_folder)

# make the backup of these python scripts to a specific backup folder and go to the backup folder
scriptDir = generalConfiguration.globalOptions['outputDir'] + "/global/scripts/"
logger.info('Making the backup of the python scripts used to the folder %s', scriptDir)
if os.path.exists(scriptDir): shutil.rmtree(scriptDir)
os.makedirs(scriptDir)
path_of_this_module = os.path.abspath(os.path.dirname(__file__))
# working/starting directory where all script files are used
for filename in glob.glob(os.path.join(path_of_this_module, '*.py')):
    shutil.copy(filename, scriptDir)
os.chdir(scriptDir)    

# pcr-globwb clone areas (for pcr-globwb multiple runs)
clone_codes = list(set(generalConfiguration.globalOptions['cloneAreas'].split(",")))
if clone_codes[0] == "Global": clone_codes = ['M%02d'%i for i in range(1,54,1)]

# TODO: command lines to run a steady state of MODFLOW (NOT FINISHED YET)
#~ if ("globalModflowOptions" in generalConfiguration.allSections) and\
   #~ (generalConfiguration.globalModflowOptions['online_coupling_between_pcrglobwb_and_moflow'] == "True") and\
   #~ (generalConfiguration.modflowTransientInputOptions['usingPredefinedInitialHead'] == "False"):
    #~ logger.info('Performing a steady state groundwater model to estimate initial conditions for MODFLOW')
    #~ cmd += "python deterministic_runner_for_monthly_merging_and_modflow.py " + iniFileName +" "+debug_option +" steady-state-only"
    #~ vos.cmd_line(cmd, using_subprocess = False)      

# command line(s) for PCR-GLOBWB 
logger.info('Running transient PCR-GLOBWB with/without MODFLOW ')
i_clone = 0
cmd = ''
for clone_code in clone_codes:

   cmd += "python deterministic_runner_glue_with_parallel_option_march_2016.py " + iniFileName +" "+\
                                                                                   debug_option +" "+\
                                                                                   clone_code +" "
   cmd = cmd + " & "
   i_clone += 1


# command line(s) for MODFLOW       
if generalConfiguration.online_coupling_between_pcrglobwb_and_moflow:

   logger.info('Also with MODFLOW')
   
   cmd += "python deterministic_runner_for_monthly_merging_and_modflow.py " + iniFileName +" "+debug_option +" transient"

   cmd = cmd + " & "       


# don't foget to add the following line
cmd = cmd + "wait"       

print cmd

# execute PCR-GLOBWB and MODFLOW
vos.cmd_line(cmd, using_subprocess = False)      
