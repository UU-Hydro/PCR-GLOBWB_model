#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Edwin H. Sutanudjaja, Rens van Beek, Niko Wanders, Yoshihide Wada, 
# Joyce H. C. Bosmans, Niels Drost, Ruud J. van der Ent, Inge E. M. de Graaf, Jannis M. Hoch, 
# Kor de Jong, Derek Karssenberg, Patricia López López, Stefanie Peßenteiner, Oliver Schmitz, 
# Menno W. Straatsma, Ekkamol Vannametee, Dominik Wisser, and Marc F. P. Bierkens
# Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

import disclaimer

# print disclaimer
disclaimer.print_disclaimer()

# get the configuration/ini file given in the system argument
iniFileName = os.path.abspath(sys.argv[1])

# option for debuging and paralelization 
debug_option = "parallel"
if len(sys.argv) > 2: debug_option = str(sys.argv[2]) 

# object to handle configuration/ini file
generalConfiguration = configuration.Configuration(iniFileName = iniFileName, debug_mode = False, no_modification = False)

clean_previous_output = True
if generalConfiguration.globalOptions['cloneAreas'] == "part_one" or\
   generalConfiguration.globalOptions['cloneAreas'] == "part_two":
    clean_previous_output = False

# clean any files exists on the ouput directory (this can be done for global runs)
if clean_previous_output and os.path.exists(generalConfiguration.globalOptions['outputDir']): shutil.rmtree(generalConfiguration.globalOptions['outputDir'])

# make log folder and initialize logging
generalOutputFolder = generalConfiguration.globalOptions['outputDir']
logFileFolder = generalOutputFolder + "/global/log/"
if os.path.exists(logFileFolder) and clean_previous_output:  
    shutil.rmtree(logFileFolder)
    os.makedirs(logFileFolder)
if os.path.exists(logFileFolder) == False: 
    os.makedirs(logFileFolder)
generalConfiguration.initialize_logging(logFileFolder)

# copy ini file to the log folder:
timestamp = datetime.datetime.now()
logger.info('Copying ini file to the folder %s', logFileFolder)
targetIniFileName = logFileFolder + \
                         os.path.basename(iniFileName) + '_' +  str(timestamp.isoformat()).replace(":",".") + '.ini'
shutil.copy(iniFileName, targetIniFileName)
# - and use it as the master file
iniFileName = targetIniFileName

# change the content of configuration file, based on the system arguments
iniFileName = modify_ini_file(iniFileName, sys.argv)


# make global output maps directory (it will contain a "maps" directory that will contain merged pcraster maps)
global_maps_folder = generalConfiguration.globalOptions['outputDir']+"/global/maps/"
if os.path.exists(global_maps_folder):
    shutil.rmtree(global_maps_folder)
    os.makedirs(global_maps_folder)
else:
    os.makedirs(global_maps_folder)

# make the backup of these python scripts to a specific backup folder and go to the backup folder
scriptDir = generalConfiguration.globalOptions['outputDir'] + "/global/scripts/"
if generalConfiguration.globalOptions['cloneAreas'] == "part_one" or\
   generalConfiguration.globalOptions['cloneAreas'] == "part_two":
    scriptDir = scriptDir + "/" + generalConfiguration.globalOptions['cloneAreas'] + "/"
logger.info('Making the backup of the python scripts used to the folder %s', scriptDir)
if os.path.exists(scriptDir): shutil.rmtree(scriptDir)
os.makedirs(scriptDir)
path_of_this_module = os.path.abspath(os.path.dirname(__file__))
# working/starting directory where all script files are used
for filename in glob.glob(os.path.join(path_of_this_module, '*.py')):
    shutil.copy(filename, scriptDir)
os.chdir(scriptDir)    


# option to include merging process:
with_merging_or_modflow = True
# - in the ini file, we can also skip merging (e.g. for runs with spin-ups): 


# Note that for parallel runs with spin-up, we cannot do any merging and/or combine them with modflow 
if float(generalConfiguration.globalOptions['maxSpinUpsInYears']) > 0:
    msg = "The run is set with some spin-ups. We can NOT combine this with merging processes and modflow calculation. "
    logger.warning(msg)
    logger.warning(msg)
    logger.warning(msg)
    logger.warning(msg)
    logger.warning(msg)
    if "with_merging" in list(generalConfiguration.globalOptions.keys()) and generalConfiguration.globalOptions["with_merging"] == "False":
        with_merging_or_modflow = False
    else:
        msg = "You set this run (with spin-ups) either with modflow or merging processes. That is not possible."
        logger.warning(msg)
        sys.exit()


# pcr-globwb clone areas (for pcr-globwb multiple runs)
clone_codes = list(set(generalConfiguration.globalOptions['cloneAreas'].split(",")))
#
# - for one global run (that should be using a fat node):
if clone_codes[0] == "Global": 
    clone_codes = ['M%02d'%i for i in range(1,54,1)]
#
# - using two (thick) nodes:
if clone_codes[0] == "part_one": 
    #
    # the relative big ones
    clone_codes  = ["M17","M19","M26","M13","M18","M20","M05","M03","M21","M46","M27","M49","M16","M44","M52","M25","M09","M08","M11","M42","M12","M39"]
    #~ # - and plus one of the two smallest ones
    #~ clone_codes += ["M29"]
    #~ # - and plus two of the smallest ones 
    #~ clone_codes += ["M30","M29"]
    #
    #
if clone_codes[0] == "part_two": 
    #
    # the relative small ones
    clone_codes = ["M07","M15","M38","M48","M40","M41","M22","M14","M23","M51","M04","M06","M10","M02","M45","M35","M47","M50","M24","M01","M36","M53","M33","M43","M34","M37","M31","M32","M28","M30","M29"]
    #~ # the relative small ones minus one of the the two smallest ones
    #~ clone_codes = ["M07","M15","M38","M48","M40","M41","M22","M14","M23","M51","M04","M06","M10","M02","M45","M35","M47","M50","M24","M01","M36","M53","M33","M43","M34","M37","M31","M32","M28","M30"]
    #~ # the relative small ones minus two of the smallest ones
    #~ clone_codes = ["M07","M15","M38","M48","M40","M41","M22","M14","M23","M51","M04","M06","M10","M02","M45","M35","M47","M50","M24","M01","M36","M53","M33","M43","M34","M37","M31","M32","M28"]
    #
    # TODO: Improve the selection of clones for part two, something likes: clones_part_two = clones_all - clones_part_one
    #
    # the execution of merging and modflow processes are done in another node
    with_merging_or_modflow = False


# command line(s) for PCR-GLOBWB 
logger.info('Running transient PCR-GLOBWB with/without MODFLOW ')
i_clone = 0
cmd = ''
for clone_code in clone_codes:

   cmd += "python deterministic_runner_glue_with_parallel_and_modflow_options.py " + iniFileName  + " " + debug_option + " " + clone_code + " "
   cmd = cmd + " & "
   i_clone += 1


# Note that for runs with spin-up, we should not combine it with modflow 


# command line(s) for merging and MODFLOW processes:       
if with_merging_or_modflow:

   logger.info('Also with merging and/or MODFLOW processes ')
   
   cmd += "python deterministic_runner_for_monthly_modflow_and_merging.py " + iniFileName +" "+debug_option +" transient"

   cmd = cmd + " & "       


# don't foget to add the following line
cmd = cmd + "wait"       

print(cmd)
msg = "Call: "+str(cmd)
logger.debug(msg)


# execute PCR-GLOBWB and MODFLOW
vos.cmd_line(cmd, using_subprocess = False)      


def modify_ini_file(original_ini_file,
                    system_argument): 

    # open and read ini file
    file_ini = open(original_ini_file, "rt")
    file_ini_content = file_ini.read()
    file_ini.close()
    
    # system argument for replacing outputDir (-mod) ; this is always required
    main_output_dir = system_argument[system_argument.index("-mod") + 1]
    file_ini_content = file_ini_content.replace("OUTPUT_FOLDER", main_output_dir)
    msg = "The output folder 'outputDir' is set based on the system argument (-mod): " + main_output_dir
    print(msg)

    # optional system arguments for modifying startTime (-sd) and endTime (-ed)
    if "-sd" in system_argument:
        starting_date = system_argument[system_argument.index("-sd") + 1]
        file_ini_content = file_ini_content.replace("START_DATE", starting_date)
        msg = "The starting date 'startTime' is set based on the system argument (-sd): " + starting_date
        print(msg)
    if "-ed" in system_argument:
        end_date = system_argument[system_argument.index("-ed") + 1]
        file_ini_content = file_ini_content.replace("END_DATE", end_date)
        msg = "The end date 'END_DATE' is set based on the system argument (-ed): " + end_date
        print(msg)
        
    # optional system arguments for initial condition files
    # - main initial state folder
    if "-misd" in system_argument:
        main_initial_state_folder = system_argument[system_argument.index("-misd") + 1]        
        file_ini_content = file_ini_content.replace("INITIAL_CONDITION_FOLDER", main_initial_state_folder)
        msg = "The main folder for all initial states is set based on the system argument (-misd): " + main_initial_state_folder
        print(msg)
    # - date for initial states 
    if "-dfis" in system_argument:
        date_for_initial_states = system_argument[system_argument.index("-dfis") + 1]        
        file_ini_content = file_ini_content.replace("DATE_FOR_INITIAL_STATES", date_for_initial_states)
        msg = "The date for all initial state files is set based on the system argument (-dfis): " + date_for_initial_states
        print(msg)
    
    # optional system argument for modifying forcing files
    if "-pff" in system_argument:
        precipitation_forcing_file = system_argument[system_argument.index("-pff") + 1]
        file_ini_content = file_ini_content.replace("PRE_FILE", precipitation_forcing_file)
        msg = "The precipitation forcing file 'precipitationNC' is set based on the system argument (-pff): " + precipitation_forcing_file
        print(msg)
    if "-tff" in system_argument:
        temperature_forcing_file = system_argument[system_argument.index("-tff") + 1]
        file_ini_content = file_ini_content.replace("TMP_FILE", temperature_forcing_file)
        msg = "The temperature forcing file 'temperatureNC' is set based on the system argument (-tff): " + temperature_forcing_file
        print(msg)
    if "-rpetff" in system_argument:
        ref_pot_et_forcing_file = system_argument[system_argument.index("-rpetff") + 1]
        file_ini_content = file_ini_content.replace("ET0_FILE", ref_pot_et_forcing_file)
        msg = "The reference potential ET forcing file 'refETPotFileNC' is set based on the system argument (-tff): " + ref_pot_et_forcing_file
        print(msg)

    if "-radff" in system_argument:
        rad_forcing_file = system_argument[system_argument.index("-radff") + 1]
        file_ini_content = file_ini_content.replace("RAD_FILE", rad_forcing_file)
        msg = "The radiation forcing file 'RAD_FILE' is set based on the system argument (-radff): " + rad_forcing_file
        print(msg)

    if "-tmp_annavg_ff" in system_argument:
        tmp_annavg_ff    = system_argument[system_argument.index("-tmp_annavg_ff") + 1]
        file_ini_content = file_ini_content.replace("TMP_ANNUAL_AVG_FILE", tmp_annavg_ff)
        msg = "The file 'TMP_ANNUAL_AVG_FILE' is set based on the system argument (-tmp_annavg_ff): " + TMP_ANNUAL_AVG_FILE
        print(msg)

    if "-irr_fl" in system_argument:
        irr_fl = system_argument[system_argument.index("irr_fl") + 1]
        file_ini_content = file_ini_content.replace("IRRIGATION_AREA_FILE", irr_fl)
        msg = "The 'IRRIGATION_AREA_FILE' is set based on the system argument (-irr_fl): " + irr_fl
        print(msg)

    if "-dom_fl" in system_argument:
        dom_fl = system_argument[system_argument.index("dom_fl") + 1]
        file_ini_content = file_ini_content.replace("DOM_WATER_DEMAND_FILE", dom_fl)
        msg = "The 'DOM_WATER_DEMAND_FILE' is set based on the system argument (-dom_fl): " + dom_fl
        print(msg)

    if "-ind_fl" in system_argument:
        ind_fl = system_argument[system_argument.index("ind_fl") + 1]
        file_ini_content = file_ini_content.replace("IND_WATER_DEMAND_FILE", ind_fl)
        msg = "The 'IND_WATER_DEMAND_FILE' is set based on the system argument (-ind_fl): " + ind_fl
        print(msg)

    # NUMBER_OF_SPINUP_YEARS
    if "-num_of_sp_years" in system_argument:
        number_of_spinup_years = system_argument[system_argument.index("-num_of_sp_years") + 1]
        file_ini_content = file_ini_content.replace("NUMBER_OF_SPINUP_YEARS", number_of_spinup_years)
        msg = "The number_of_spinup_years is set based on the system argument (-num_of_sp_years): " + number_of_spinup_years
        print(msg)

    # folder for saving original and modified ini files
    folder_for_ini_files = os.path.join(main_output_dir, "ini_files")
    
   # create folder
    if os.path.exists(folder_for_ini_files): shutil.rmtree(folder_for_ini_files)
    os.makedirs(folder_for_ini_files)
    
    # save/copy the original ini file
    shutil.copy(original_ini_file, os.path.join(folder_for_ini_files, os.path.basename(original_ini_file) + ".original"))

    # save the new ini file
    new_ini_file_name = os.path.join(folder_for_ini_files, os.path.basename(original_ini_file) + ".modified_and_used")
    new_ini_file = open(new_ini_file_name, "w")
    new_ini_file.write(file_ini_content)
    new_ini_file.close()
            
    return new_ini_file_name
