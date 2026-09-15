#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import datetime
import glob
import shutil

import pcraster as pcr
from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

from configuration_for_modflow import Configuration
from currTimeStep import ModelTime

try:
    from reporting_for_modflow import Reporting
except:
    pass

try:
    from modflow import ModflowCoupling
except:
    pass

import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

import disclaimer

class DeterministicRunner(DynamicModel):

    def __init__(self, configuration, modelTime, system_argument = None):
        DynamicModel.__init__(self)

        self.number_of_clones   = configuration.globalMergingAndModflowOptions['number_of_clones']
        self.cellsize_in_arcsec = configuration.globalMergingAndModflowOptions['cellsize_in_arcsec']       
        self.xmin               = configuration.globalMergingAndModflowOptions['xmin']                    
        self.ymin               = configuration.globalMergingAndModflowOptions['ymin']
        self.xmax               = configuration.globalMergingAndModflowOptions['xmax']
        self.ymax               = configuration.globalMergingAndModflowOptions['ymax']

        # model time object
        self.modelTime = modelTime        
        
        # make the configuration available for the other method/function
        self.configuration = configuration

        # indicating whether this run includes modflow or merging processes
        self.include_merging_or_modflow = True
        # - For the standard PCR-GLOBWB 5arcmin runs, only the "Global" and "part_one" runs include modflow or merging processes 
        if "cloneAreas" in list(self.configuration.globalOptions.keys()) and\
            self.configuration.globalOptions['cloneAreas'] == "part_two": self.include_merging_or_modflow = False
        
        if self.include_merging_or_modflow:
        
            # netcdf merging options
            self.netcdf_format = self.configuration.mergingOutputOptions['formatNetCDF']
            self.zlib_option   = self.configuration.mergingOutputOptions['zlib']
            
            # output files/variables that will be merged
            nc_report_list = ["outDailyTotNC",
                              "outMonthTotNC", "outMonthAvgNC", "outMonthEndNC", "outMonthMaxNC", 
                              "outAnnuaTotNC", "outAnnuaAvgNC", "outAnnuaEndNC", "outAnnuaMaxNC"]
            for nc_report_type in nc_report_list:
                vars(self)[nc_report_type] = self.configuration.mergingOutputOptions[nc_report_type]
        

        # model and reporting objects, required for runs with modflow
        if self.configuration.online_coupling_between_pcrglobwb_and_modflow:
            self.model     = ModflowCoupling(configuration, modelTime)
            self.reporting = Reporting(configuration, self.model, modelTime)


        # somehow you need to set the clone map as the dynamic framework needs it (and the "self.model" is not always created) 
        pcr.setclone(self.configuration.cloneMap)
        
        

    def initial(self): 
        
        # get or prepare the initial condition for groundwater head 
        if self.configuration.online_coupling_between_pcrglobwb_and_modflow:
            self.model.get_initial_heads()

    def dynamic(self):

        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        # update/calculate model and daily merging, and report ONLY at the last day of the month
        if self.modelTime.isLastDayOfMonth():
            
            # wait until all pcrglobwb model runs are done
            pcrglobwb_is_ready = False
            self.count_check = 0
            while pcrglobwb_is_ready == False:
                if datetime.datetime.now().second == 14 or\
                   datetime.datetime.now().second == 29 or\
                   datetime.datetime.now().second == 34 or\
                   datetime.datetime.now().second == 49:\
                   pcrglobwb_is_ready = self.check_pcrglobwb_status()
                
            # merging netcdf files at daily resolution
            start_date = '%04i-%02i-01' %(self.modelTime.year, self.modelTime.month)             # TODO: Make it flexible for a run starting not on the 1st January.
            end_date   = self.modelTime.fulldate
            self.merging_netcdf_files("outDailyTotNC", start_date, end_date)
            
            # for runs with modflow
            if self.configuration.online_coupling_between_pcrglobwb_and_modflow:
                
                # merging pcraster maps that are needed for MODFLOW calculation
                msg = "Merging pcraster map files that are needed for the MODFLOW calculation."
                logger.info(msg)
                cmd = 'python3 '+ self.configuration.path_of_this_module + "/merge_pcraster_maps.py " + str(self.modelTime.fulldate) + " " +\
                                                                                                        str(self.configuration.main_output_directory)+"/ maps 8 "+\
                                                                                                        str("Global")
                vos.cmd_line(cmd, using_subprocess = False)

                # cleaning up unmerged files (not tested yet)
                clean_up_pcraster_maps = False
                if self.configuration.mergingOutputOptions["delete_unmerged_pcraster_maps"] == "True": clean_up_pcraster_maps = True                    # TODO: FIXME: This is NOT working yet.
                if clean_up_pcraster_maps:                                                                                    
                    files_to_be_removed = glob.glob(str(self.configuration.main_output_directory) + "/M*/maps/*" + str(self.modelTime.fulldate) + "*")
                    for f in files_to_be_removed: 
                        print(f)
                        os.remove(f)

                # update MODFLOW model (It will pick up current model time from the modelTime object)
                self.model.update()
                # reporting is only done at the end of the month
                self.reporting.report()


        # merging initial conditions (pcraster maps) of PCR-GLOBWB
        if self.modelTime.isLastDayOfYear():

        # ~ # - for Ulysses we have to do it on every month
        # ~ if self.modelTime.isLastDayOfMonth():

            msg = "Merging pcraster map files belonging to initial conditions."
            logger.info(msg)

            # ~ # - for a global extent 
            # ~ cmd = 'python '+ self.configuration.path_of_this_module + "/merge_pcraster_maps.py " + str(self.modelTime.fulldate) + " " +\
                                                                                                   # ~ str(self.configuration.main_output_directory)+"/ states 8 "+\
                                                                                                   # ~ str("Global")
            # ~ # - for Ulysses: 
            # ~ # example: python3 merge_pcraster_maps_6_arcmin_ulysses.py ${END_DATE} ${MAIN_OUTPUT_DIR} states 2 Global 71 False
            # ~ cmd =     'python3 '+ self.configuration.path_of_this_module + "/merge_pcraster_maps_6_arcmin_ulysses.py " + str(self.modelTime.fulldate) + " " +\
                                                                                                                         # ~ str(self.configuration.main_output_directory)+"/ states 32 "+\
                                                                                                                         # ~ str("Global 71 False")

            # - for general (e.g. africa extent, europe, etc)
            cmd =     'python3 '+ self.configuration.path_of_this_module + "/merge_pcraster_maps_general.py " + str(self.modelTime.fulldate) + " " +\
                                                                                                                str(self.configuration.main_output_directory)+"/ states 32 "+\
                                                                                                                str(self.number_of_clones  ) + " "  +\
                                                                                                                str("defined")               + " "  +\
                                                                                                                str(self.cellsize_in_arcsec) + " "  +\
                                                                                                                str(self.xmin              ) + " "  +\
                                                                                                                str(self.ymin              ) + " "  +\
                                                                                                                str(self.xmax              ) + " "  +\
                                                                                                                str(self.ymax              ) + " "

            print(cmd)

            # ~ pietje
            
            # ~ vos.cmd_line(cmd, using_subprocess = False)
            os.system(cmd)
            
            
            # cleaning up unmerged files (not tested yet)
            clean_up_pcraster_maps = False
            if "delete_unmerged_pcraster_maps" in list(self.configuration.mergingOutputOptions.keys()) and self.configuration.mergingOutputOptions["delete_unmerged_pcraster_maps"] == "True": clean_up_pcraster_maps = True                    # TODO: FIXME: This is NOT working yet.
            if clean_up_pcraster_maps:                                                                                    
                files_to_be_removed = glob.glob(str(self.configuration.main_output_directory) + "/M*/states/*" + str(self.modelTime.fulldate) + "*")
                for f in files_to_be_removed:
                    print(f)
                    os.remove(f)


        # monthly and annual merging
        if self.modelTime.isLastDayOfYear():

            # merging netcdf files at monthly resolutions
            start_date = '%04i-01-31' %(self.modelTime.year)                  # TODO: Make it flexible for a run starting not on the 1st January.
            self.merging_netcdf_files("outMonthTotNC", start_date, end_date)
            self.merging_netcdf_files("outMonthAvgNC", start_date, end_date)
            self.merging_netcdf_files("outMonthEndNC", start_date, end_date)
            self.merging_netcdf_files("outMonthMaxNC", start_date, end_date)

            # merging netcdf files at annual resolutions
            start_date = '%04i-12-31' %(self.modelTime.year)                  # TODO: Make it flexible for a run starting not on the 1st January.
            end_date   = self.modelTime.fulldate
            self.merging_netcdf_files("outAnnuaTotNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaAvgNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaEndNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaMaxNC", start_date, end_date)


        # make an empty file indicating that merging process is done 
        if self.modelTime.isLastDayOfMonth() or self.modelTime.isLastDayOfYear():

            outputDirectory = str(self.configuration.main_output_directory) + "/global/maps/"
            if os.path.exists(outputDirectory) == False: os.makedirs(outputDirectory) 
            filename = outputDirectory + "/merged_files_for_" + str(self.modelTime.fulldate)+"_are_ready.txt"
            if os.path.exists(filename): os.remove(filename)
            open(filename, "w").close()    


    def merging_netcdf_files(self, nc_report_type, start_date, end_date, max_number_of_cores = 20):

        if str(vars(self)[nc_report_type]) != "None":
        
            netcdf_files_that_will_be_merged = vars(self)[nc_report_type]
            
            msg = "Merging netcdf files for the files/variables: " + netcdf_files_that_will_be_merged
            logger.info(msg)
            
            # ~ cmd = 'python '+ self.configuration.path_of_this_module + "/merge_netcdf.py " + str(self.configuration.main_output_directory) + " " +\
                                                                                            # ~ str(self.configuration.main_output_directory) + "/global/netcdf/ "+\
                                                                                            # ~ str(nc_report_type)  + " " +\
                                                                                            # ~ str(start_date) + " " +\
                                                                                            # ~ str(end_date)   + " " +\
                                                                                            # ~ str(netcdf_files_that_will_be_merged) + " " +\
                                                                                            # ~ str(self.netcdf_format)  + " "  +\
                                                                                            # ~ str(self.zlib_option  )  + " "  +\
                                                                                            # ~ str(max_number_of_cores) + " "  +\
                                                                                            # ~ str("Global")  + " "
            
            # ~ # - for Ulysses:
            # ~ # example: python3 merge_netcdf_6_arcmin_ulysses.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/global/netcdf outDailyTotNC ${STARTING_DATE} ${END_DATE} ulyssesQrRunoff,ulyssesDischarge NETCDF4 False 12 Global default_lats
            # ~ cmd =     'python3 '+ self.configuration.path_of_this_module + "/merge_netcdf_6_arcmin_ulysses.py " + str(self.configuration.main_output_directory) + " " +\
                                                                                                                  # ~ str(self.configuration.main_output_directory) + "/global/netcdf/ "+\
                                                                                                                  # ~ str(nc_report_type)  + " " +\
                                                                                                                  # ~ str(start_date) + " " +\
                                                                                                                  # ~ str(end_date)   + " " +\
                                                                                                                  # ~ str(netcdf_files_that_will_be_merged) + " " +\
                                                                                                                  # ~ str(self.netcdf_format)  + " "  +\
                                                                                                                  # ~ str(self.zlib_option  )  + " "  +\
                                                                                                                  # ~ str(max_number_of_cores) + " "  +\
                                                                                                                  # ~ str("Global default_lats")  + " "

            # - for general:
            cmd =     'python3 '+ self.configuration.path_of_this_module + "/merge_netcdf_general.py " + str(self.configuration.main_output_directory) + " " +\
                                                                                                         str(self.configuration.main_output_directory) + "/global/netcdf/ "+\
                                                                                                         str(nc_report_type)  + " " +\
                                                                                                         str(start_date) + " " +\
                                                                                                         str(end_date)   + " " +\
                                                                                                         str(netcdf_files_that_will_be_merged) + " " +\
                                                                                                         str(self.netcdf_format)  + " "  +\
                                                                                                         str(self.zlib_option  )  + " "  +\
                                                                                                         str(max_number_of_cores) + " "  +\
                                                                                                         str(self.number_of_clones  ) + " "  +\
                                                                                                         str("defined")               + " "  +\
                                                                                                         str(self.cellsize_in_arcsec) + " "  +\
                                                                                                         str(self.xmin              ) + " "  +\
                                                                                                         str(self.ymin              ) + " "  +\
                                                                                                         str(self.xmax              ) + " "  +\
                                                                                                         str(self.ymax              ) + " "

            msg = "Using the following command line: " + cmd
            logger.info(msg)
            
            # ~ vos.cmd_line(cmd, using_subprocess = False)
            os.system(cmd)


    def check_pcrglobwb_status(self):

        # ~ if self.configuration.globalOptions['cloneAreas'] == "Global" or \
           # ~ self.configuration.globalOptions['cloneAreas'] == "part_one":
            # ~ clone_areas = ['M%02d'%i for i in range(1,53+1,1)]
        
        # ~ # for the Ulysses project
        # ~ elif self.configuration.globalOptions['cloneAreas'] == "GlobalUlysses":
            # ~ clone_areas = ['M%07d'%i for i in range(1,71+1,1)]
        
        # ~ else:
            # ~ clone_areas = list(set(self.configuration.globalOptions['cloneAreas'].split(",")))

        clone_areas = ['M%07d'%i for i in range(1, int(self.number_of_clones) + 1, 1)]
        
        for clone_area in clone_areas:
            status_file = str(self.configuration.main_output_directory) + "/" +str(clone_area) + "/maps/pcrglobwb_files_for_" + str(self.modelTime.fulldate) + "_are_ready.txt"
            msg = 'Waiting for the file: '+status_file
            if self.count_check == 1: logger.info(msg)
            if self.count_check < 7:
                #~ logger.debug(msg)		# INACTIVATE THIS AS THIS MAKE A HUGE DEBUG (dbg) FILE
                self.count_check += 1
            status = os.path.exists(status_file)

            # ~ # for debugging
            # ~ status = True

            if status == False: return status
            if status: self.count_check = 0            
                    
        print(status)
        
        return status

def modify_ini_file(original_ini_file,
                    system_argument): 

    # created by Edwin H. Sutanudjaja on August 2020 for the Ulysses project
    
    # open and read ini file
    file_ini = open(original_ini_file, "rt")
    file_ini_content = file_ini.read()
    file_ini.close()
    
    # system argument for replacing outputDir (-mod) ; this is always required
    main_output_dir = system_argument[system_argument.index("-mod") + 1]
    file_ini_content = file_ini_content.replace("MAIN_OUTPUT_DIR", main_output_dir)
    msg = "The output folder 'outputDir' is set based on the system argument (-mod): " + main_output_dir
    print(msg)
    
    # optional system arguments for modifying startTime (-sd) and endTime (-ed)
    if "-sd" in system_argument:
        starting_date = system_argument[system_argument.index("-sd") + 1]
        file_ini_content = file_ini_content.replace("STARTING_DATE", starting_date)
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
        file_ini_content = file_ini_content.replace("MAIN_INITIAL_STATE_FOLDER", main_initial_state_folder)
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
        file_ini_content = file_ini_content.replace("PRECIPITATION_FORCING_FILE", precipitation_forcing_file)
        msg = "The precipitation forcing file 'precipitationNC' is set based on the system argument (-pff): " + precipitation_forcing_file
        print(msg)
    if "-tff" in system_argument:
        temperature_forcing_file = system_argument[system_argument.index("-tff") + 1]
        file_ini_content = file_ini_content.replace("TEMPERATURE_FORCING_FILE", temperature_forcing_file)
        msg = "The temperature forcing file 'temperatureNC' is set based on the system argument (-tff): " + temperature_forcing_file
        print(msg)
    if "-rpetff" in system_argument:
        ref_pot_et_forcing_file = system_argument[system_argument.index("-rpetff") + 1]
        file_ini_content = file_ini_content.replace("REF_POT_ET_FORCING_FILE", ref_pot_et_forcing_file)
        msg = "The reference potential ET forcing file 'refETPotFileNC' is set based on the system argument (-tff): " + ref_pot_et_forcing_file
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


def main():
    
    # print disclaimer
    disclaimer.print_disclaimer()

    # get the full path of configuration/ini file given in the system argument
    iniFileName   = os.path.abspath(sys.argv[1])
    
    # modify ini file and return it in a new location 
    if "-mod" in sys.argv:
        iniFileName = modify_ini_file(original_ini_file = iniFileName, \
                                      system_argument = sys.argv)

    # debug option
    debug_mode = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "debug" or sys.argv[2] == "debug_parallel": debug_mode = True
    
    # options to perform steady state calculation (for modflow)
    steady_state_only = False
    if len(sys.argv) > 3: 
        if sys.argv[3] == "steady-state-only": steady_state_only = True
    
    # object to handle configuration/ini file
    configuration = Configuration(iniFileName = iniFileName, \
                                  debug_mode = debug_mode, \
                                  steady_state_only = steady_state_only)      

    # timeStep info: year, month, day, doy, hour, etc
    currTimeStep = ModelTime() 
    
    # Running the deterministic_runner
    currTimeStep.getStartEndTimeSteps(configuration.globalOptions['startTime'],
                                      configuration.globalOptions['endTime'])
    logger.info('Model run starts.')
    deterministic_runner = DeterministicRunner(configuration, currTimeStep)
    
    dynamic_framework = DynamicFramework(deterministic_runner,currTimeStep.nrOfTimeSteps)
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()

if __name__ == '__main__':
    # print disclaimer
    disclaimer.print_disclaimer(with_logger = True)
    sys.exit(main())
