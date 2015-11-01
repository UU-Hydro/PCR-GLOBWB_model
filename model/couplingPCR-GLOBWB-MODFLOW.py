# main script for coupling PCR-GLOBWB and iGround
# outputs our writen in */netcdf/ ; note: this is only temporary dir

import os
import sys
import shutil

import pcraster as pcr

import configuration
import virtualOS as vos

# get the full path of configuration/ini file given in the system argument
iniFileName = os.path.abspath(sys.argv[1])

# option for using debugging # TODO
pcrglobwb_debug_option = str(sys.argv[2])

# object to handle configuration/ini file
generalConfiguration = configuration.Configuration(iniFileName = iniFileName, debug_mode = False, no_modification = False)

# create the output folder 
generalOutputFolder = generalConfiguration.globalOptions['outputDir']
if os.path.exists(generalOutputFolder): shutil.rmtree(generalOutputFolder)
os.makedirs(generalOutputFolder)

# make log folder and initialize logging
logFileFolder = generalOutputFolder+"/global_log/"
if os.path.exists(logFileFolder): shutil.rmtree(logFileFolder)
os.makedirs(logFileFolder)
generalConfiguration.initialize_logging(logFileFolder)

# make the global folder that will contain merged pcraster maps
globalOutputFolder = generalOutputFolder+"/global/"
if os.path.exists(globalOutputFolder): shutil.rmtree(globalOutputFolder)
os.makedirs(globalOutputFolder)

# pcr-globwb clone areas (for pcr-globwb multiple runs)
clone_codes = list(set(generalConfiguration.globalOptions['cloneAreas'].split(",")))
if clone_codes[0] == "Global": clone_codes = ['M%02d'%i for i in range(1,54,1)]

# command lines for PCR-GLOBWB 
i_clone = 0
cmd = ''
for clone_code in clone_codes:

   cmd += "python deterministic_runner_glue_coupled_to_modflow.py " + iniFileName +" "+\
                                                                      pcrglobwb_debug_option +" "+\
                                                                      clone_code +\
                                                                      "1.00 0.00 0.00 1.00"
   cmd = cmd+" & "
   i_clone += 1

# command line for MODFLOW       
cmd += "python "       
cmd = cmd+" & "       

# don't foget to add line
cmd = cmd+"wait"       

# execute PCR-GLOBWB and MODFLOW
vos,cmd_line(cmd, using_subprocess = True)      
