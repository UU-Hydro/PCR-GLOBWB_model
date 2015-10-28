# main script for coupling PCR-GLOBWB and iGround
# outputs our writen in */netcdf/ ; note: this is only temporary dir

import os
import sys
import glob
import subprocess
import datetime
import calendar
import shutil

import pcraster as pcr

import currTimeStep as modelTime
import configuration
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

# get the full path of configuration/ini file given in the system argument
iniFileName = os.path.abspath(sys.argv[1])

# option for using detailed debugging
without_debug = False
try:
    if sys.argv[2] == "no_debug": without_debug = True
except:
    pass

# object to handle configuration/ini file
generalConfiguration = configuration.Configuration(iniFileName = iniFileName, \
                                                   debug_mode = False, \
                                                   no_modification = False)

# create the general/integrated/complete/final/merged output folder (contains all model results) 
generalOutputFolder = generalConfiguration.globalOptions['generalOutputFolder']
if os.path.exists(generalOutputFolder): shutil.rmtree(generalOutputFolder)
os.makedirs(generalOutputFolder)

# make log folder and initialize logging
logFileFolder = generalOutputFolder+"/log/"
print logFileFolder
try:
    os.makedirs(logFileFolder)
except:
    cmd = 'rm -r '+logFileFolder+'/*'
    vos.cmd_line(cmd, using_subprocess = False)
generalConfiguration.initialize_logging(logFileFolder)

logger.info('Preparing netcdf and states (output) folders.')
cmd = 'mkdir '+generalOutputFolder+'/merged'; vos.cmd_line(cmd, using_subprocess = without_debug)
cmd = 'mkdir '+generalOutputFolder+'/merged/netcdf/'; vos.cmd_line(cmd, using_subprocess = without_debug)
cmd = 'mkdir '+generalOutputFolder+'/merged/states/'; vos.cmd_line(cmd, using_subprocess = without_debug)

logger.info('Preparing monthly output (temporary) folder.')
pcrglobwbMonthlyOutputFolder = generalConfiguration.globalOptions['generalOutputFolder']+"/tmp/monthly/"
try:
    os.makedirs(pcrglobwbMonthlyOutputFolder)
except:
    cmd = 'rm -r '+pcrglobwbMonthlyOutputFolder+'/*'
    vos.cmd_line(cmd, using_subprocess = False)
    
# startDate and endDate; and initiating modelTime object
startDate = generalConfiguration.globalOptions['startTime']
endDate   = generalConfiguration.globalOptions['endTime']
modelTime = modelTime.ModelTime()
modelTime.getStartEndTimeSteps(startDate,endDate,False)

logger.info('Preparing/copying the (first) initial condition files.')
# - preparing the temporary folder to store initial conditions
temporary_initial_condition_folder = generalOutputFolder+"/tmp/ini/"
try:
    os.makedirs(temporary_initial_condition_folder)
except:
    # make sure that we can write to the_folder 
    cmd = 'chmod -R 755 '+temporary_initial_condition_folder+'/*'
    print cmd; vos.cmd_line(cmd, using_subprocess = False)
    # cleaning up the folder 
    cmd = 'rm -r '+temporary_initial_condition_folder+'/*'
    print cmd; vos.cmd_line(cmd, using_subprocess = False)
# - initial conditions files 
firstInitialConditionFiles  = generalConfiguration.globalOptions['firstInitialConditionFolder']+"/*"
initialConditionDate = datetime.datetime.strptime(str(startDate),'%Y-%m-%d') - datetime.timedelta(days=1)
firstInitialConditionFiles += str(initialConditionDate.strftime('%Y-%m-%d'))+".map"
firstInitialConditionFileList = glob.glob(firstInitialConditionFiles)
# - copying initial conditions to a temporary folder
for fileName in firstInitialConditionFileList: 
    newFileName = temporary_initial_condition_folder+"/"+str(os.path.basename(fileName)).replace(str(initialConditionDate.strftime('%Y-%m-%d')), "xxxx-xx-xx")
    cmd = 'cp '+fileName+' '+newFileName; vos.cmd_line(cmd, using_subprocess = without_debug)

logger.info("Creating the master ini file for PCR-GLOBWB runs.")
master_ini_file = generalOutputFolder+"/tmp/setup_pcrglobwb.ini"
# - cleaning up the temporaty folder (in order to make sure that we are using the correct/new ini file)
cmd = 'rm '+generalOutputFolder+'/tmp/*'
vos.cmd_line(cmd, using_subprocess = False)
# - copying and modifying ini file 
f1 = open(iniFileName, 'r'); f2 = open(master_ini_file, 'w')
for line in f1:f2.write(line.replace('GENERAL_TMP_OUTPUT_FOLDER', generalOutputFolder+"/tmp/ini/"))
f1.close(); f2.close()

# pcr-globwb clone areas (for pcr-globwb multiple runs)
clone_codes = list(set(generalConfiguration.globalOptions['cloneAreas'].split(",")))
if clone_codes[0] == "Global": clone_codes = ['M%02d'%i for i in range(1,54,1)]

for i_date in range(1, modelTime.nrOfTimeSteps+1):

    pcrglobwb_debug_option = "debug"
    if without_debug: pcrglobwb_debug_option = "no_debug"

       # command line for PCR-GLOBWB 
       cmd = ''
       i_clone = 0
       for clone_code in clone_codes:
          cmd += "python deterministic_runner_for_modflow_coupling.py "+master_ini_file+" "+pcrglobwb_debug_option+" "+starting_date+" "+modelTime.fulldate +" "+clone_code+" "+pcrglobwbMonthlyOutputFolder
          cmd = cmd+" & "
          i_clone += 1 

       # command line for modlow
       cmd += "python "
       cmd = cmd+" & "
       cmd = cmd+"wait"

       msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
