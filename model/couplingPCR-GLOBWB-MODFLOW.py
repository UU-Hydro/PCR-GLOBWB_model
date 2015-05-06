# main script for coupling PCR-GLOBWB and iGround
# outputs our writen in */netcdf/ ; note: this is only temporary dir

import os
import sys
import glob
import subprocess
import datetime
import calendar

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
try:
    os.makedirs(generalOutputFolder)
except:
    cmd = 'rm -r '+generalOutputFolder+'/*'
    vos.cmd_line(cmd, using_subprocess = False)

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

    # update time
    modelTime.update(i_date)
    
    # at the beginning of the month, save the starting date
    if modelTime.isFirstDayOfMonth():
        starting_date = modelTime.fulldate
    
    # at the end of the month, execute PCR-GLOBWB and MODFLOW
    if modelTime.isLastDayOfMonth():
        
       # execute PCR-GLOBWB
       msg = "Execute PCR-GLOBWB for "+starting_date+" "+modelTime.fulldate
       logger.info(msg)
       #
       pcrglobwb_debug_option = "debug"
       if without_debug: pcrglobwb_debug_option = "no_debug"
       #
       i_clone = 0
       for clone_code in clone_codes:
          if i_clone == 0: cmd = "python deterministic_runner_for_modflow_coupling.py "+master_ini_file+" "+pcrglobwb_debug_option+" "+starting_date+" "+modelTime.fulldate +" "+clone_code+" "+pcrglobwbMonthlyOutputFolder
          if i_clone > 0: cmd += "python deterministic_runner_for_modflow_coupling.py "+master_ini_file+" "+pcrglobwb_debug_option+" "+starting_date+" "+modelTime.fulldate +" "+clone_code+" "+pcrglobwbMonthlyOutputFolder
          cmd = cmd+" & "
          i_clone += 1 
          if i_clone == len(clone_codes): cmd = cmd+"wait"
       msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
       
       # merging end state pcraster maps over the areas 
       logger.info("Merging pcraster maps for the date "+modelTime.fulldate)
       # - cleaning up previous initial conditions
       cmd = 'rm '+temporary_initial_condition_folder+'/*'; 
       vos.cmd_line(cmd, using_subprocess = without_debug)
       # - merging pcraster maps
       cmd = 'python MCmergeMaps.py '+modelTime.fulldate+" "+pcrglobwbMonthlyOutputFolder+"/ "+temporary_initial_condition_folder+"/ 8 "+str(clone_codes)[1:-1].replace(" ","").replace("'","").replace('"',"")
       msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
       
       # - copying and moving/renaming files
       for fileName in glob.glob(temporary_initial_condition_folder+"/*.map"): 
           # - copying the files to the correct output directory
           cmd = 'cp '+fileName+' '+generalOutputFolder+'/merged/states/'+os.path.basename(fileName);
           msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
           # - renaming file names at the temporary folder of initial condition files
           newFileName = os.path.basename(fileName)
           newFileName = temporary_initial_condition_folder+"/"+newFileName.replace(modelTime.fulldate, "xxxx-xx-xx")
           cmd = 'mv '+fileName+' '+newFileName;
           msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
       
       # merging netcdf files over the areas 
       logger.info("Merging netcdf files over the areas for the date "+modelTime.fulldate)
       cmd = "python nc_basin_merge.py "+pcrglobwbMonthlyOutputFolder+"/ default 24 "+"'"+pcrglobwbMonthlyOutputFolder+"/"+clone_codes[0]+"/netcdf/*.nc"+"' "+str(clone_codes)[1:-1].replace(" ","").replace("'","").replace('"',"")
       msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)

       # merging netcdf files over the time
       logger.info("Merging netcdf files (over the time) from the date "+modelTime.fulldate)
       # - for the first month, just move the files to the correct directory
       if modelTime.monthIdx == 1:
           # - move the netcdf files 
           cmd = "mv "+pcrglobwbMonthlyOutputFolder+"/global/netcdf/*.nc"+" "+generalOutputFolder+"/merged/netcdf/"
           msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
           # - get the list of monthly netcdf output files
           netcdfFileNameList = glob.glob(generalOutputFolder+"/merged/netcdf/*.nc")
       # - for the other months, merge the netcdf files 
       else:
           for fileName in netcdfFileNameList:
               # - make sure that the previous temporary netcdf file has been removed
               cmd = "rm "+generalOutputFolder+"/tmp/temp.nc"
               vos.cmd_line(cmd, using_subprocess = False)
               # - merging (resulting a temporary file)
               baseFileName = os.path.basename(fileName)
               cmd = "cdo mergetime "+generalOutputFolder+"/merged/netcdf/"+baseFileName+" "+\
                                      pcrglobwbMonthlyOutputFolder+"/global/netcdf/"+baseFileName+" "+\
                                      generalOutputFolder+"/tmp/temp.nc"
               msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
               # - moving/renaming the temporary file
               cmd = "mv "+generalOutputFolder+"/tmp/temp.nc "+generalOutputFolder+"/merged/netcdf/"+baseFileName
               msg = "Call: "+cmd; logger.info(msg); vos.cmd_line(cmd, using_subprocess = without_debug)
               # - deleting temporary netcdf file
               cmd = "rm "+generalOutputFolder+"/tmp/temp.nc"

       #~ pietje
 
       # TODO:
       # - execute MODFLOW (globally)
       # - MODFLOW output states must be stored/added to generalOutputFolder+'/merged/states/'
       # - MODFLOW netcdf files  must be stored/added to generalOutputFolder+'/merged/netcdf/'
       
       #~ pietje
##~ 
#       #~ # execute MODFLOW
#       #~ cmd = "python MODFLOW_3.py " +starting_date+" "+modelTime.fulldate
#       #~ print(cmd)
#       #~ os.system(cmd)
#        #~ 
#       #~ # merge the netcdf file
#       #~ # for first month just move the file 
#       #~ if modelTime.fulldate == lastDateofFirstMonth:  
#           #~ # make directory
#           #~ try:
#               #~ os.makedirs(outputFolder)
#           #~ except:
#               #~ pass
#           #~ # - get the list of monthly output files
#           #~ fileNameListMF = glob.glob(os.path.join(pcrglobwbMonthlyOutputFolder,"*MF.nc"))
#           #~ for i in range(0,len(fileNameListMF)):
#               #~ fileNameListMF[i] = os.path.basename(fileNameListMF[i])
#               #~ print fileNameListMF[i]
#           #~ # - move the files
#           #~ cmd = "mv "+pcrglobwbMonthlyOutputFolder+"/*MF.nc "+outputFolder
#           #~ print(cmd)
#           #~ cOut,err = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
#           #~ os.system(cmd) 
#       #~ else:
#	   #~ # merge the netcdf file
#           #~ for i in range(0,len(fileNameListMF)):
#               #~ # - merging process
#               #~ cmd = "cdo mergetime "+outputFolder+"/"+fileNameListMF[i]+" "+pcrglobwbMonthlyOutputFolder+"/"+fileNameListMF[i]+" "+outputFolder+"/temp.nc"
#               #~ print(cmd)
#               #~ cOut,err = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
#               #~ os.system(cmd)
#               #~ # - rename the file
#               #~ cmd = "mv "+outputFolder+"/temp.nc "+outputFolder+"/"+fileNameListMF[i]
#               #~ print(cmd)
#               #~ cOut,err = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
#               #~ os.system(cmd)                 
#       #~ 
#       #~ # MODFLOW moving initial condition to temporary ini directory; remaning is not needed
#       #~ # (this are the MF.map files reported now in netcdf dir --> better to report this in states)  # FIX THIS
#       #~ cmd = "mv "+"/scratch/inge/test/netcdf/*MF.map /scratch/inge/test/ini/"
#       #~ print(cmd)
#       #~ os.system(cmd)
#        #~ 
#       #~ # PCR-GLOBWB copying the initial condition to a temporary ini directory
#       #~ cmd = "cp "+"/scratch/inge/test/states/*"+str(modelTime.fulldate)+"*.map /scratch/inge/test/ini/"
#       #~ print(cmd)
#       #~ cOut,err = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
#       #~ os.system(cmd)
#       #~ # rename the file names:
#       #~ date_for_initial_maps = modelTime.fulldate
#       #~ cmd = "for f in /scratch/inge/test/ini/*"+date_for_initial_maps+"*; do mv -v ""$f"" $(echo ""$f"" | tr '"+date_for_initial_maps+"' 'xx'); done"
#       #~ print(cmd)
#       #~ 
#       #~ cOut,err = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
#       #~ os.system(cmd)
#
#       
