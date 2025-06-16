#!/usr/bin/env python
#  -*- coding: utf-8 -*-
#
# Module to create configuration files from a bash file when a global
# parallel run is intended

###########
# Modules #
###########
import os, sys

###########
# Process #
###########
#
# fetching data
original_ini_file = sys.argv[1]
system_argument  = sys.argv[2:]
    
# open and read configuration file
file_ini = open(original_ini_file, "rt")
file_ini_content = file_ini.read()
file_ini.close()

# system argument for replacing clone_code
clone_code = "M" + system_argument[system_argument.index("-mod") - 1]
file_ini_content = file_ini_content.replace("CLONE_CODE", clone_code)

# system argument for replacing outputDir (-mod)
qualloc_output_dir = system_argument[system_argument.index("-mod") + 1]
file_ini_content = file_ini_content.replace("QUALLOC_OUTPUT_DIR", qualloc_output_dir)
msg = "The output folder 'outputpath' is set based on the system argument (-mod): " + qualloc_output_dir
print(msg)

# optional system arguments for modifying startTime (-sd) and endTime (-ed)
if "-sd" in system_argument:
    start_date = system_argument[system_argument.index("-sd") + 1]
    file_ini_content = file_ini_content.replace("START_DATE", start_date)
    msg = "The starting date 'startyear' is set based on the system argument (-sd): " + start_date
    print(msg)
if "-ed" in system_argument:
    end_date = system_argument[system_argument.index("-ed") + 1]
    file_ini_content = file_ini_content.replace("END_DATE", end_date)
    msg = "The end date 'endyear' is set based on the system argument (-ed): " + end_date
    print(msg)
    
# optional system arguments for initial condition files
# - main initial state folder
if "-isd" in system_argument:
    initial_state_folder = system_argument[system_argument.index("-isd") + 1]
    file_ini_content = file_ini_content.replace("INITIAL_STATE_FOLDER", initial_state_folder)
    msg = "The main folder for all initial states is set based on the system argument (-isd): " + initial_state_folder
    print(msg)

# - date for initial states 
if "-dfis" in system_argument:
    date_for_initial_states = system_argument[system_argument.index("-dfis") + 1]        
    file_ini_content = file_ini_content.replace("DATE_FOR_INITIAL_STATES", date_for_initial_states)
    msg = "The date for all initial state files is set based on the system argument (-dfis): " + date_for_initial_states
    print(msg)

# folder for saving original and modified ini files
new_ini_file_name = f'{original_ini_file.split(".")[0]}_{clone_code}.cfg' 

# create folder
if os.path.isfile(new_ini_file_name): os.remove(new_ini_file_name)
print(new_ini_file_name)

# save the new ini file
new_ini_file = open(new_ini_file_name, "w")
new_ini_file.write(file_ini_content)
new_ini_file.close()
