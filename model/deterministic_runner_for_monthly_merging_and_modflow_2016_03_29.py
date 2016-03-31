#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import glob

from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

from configuration_for_modflow import Configuration
from currTimeStep import ModelTime
from reporting_for_modflow import Reporting

from modflow import ModflowCoupling

import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

class DeterministicRunner(DynamicModel):

    def __init__(self, configuration, modelTime):
        DynamicModel.__init__(self)

        self.modelTime = modelTime        
        self.model = ModflowCoupling(configuration, modelTime)

        self.reporting = Reporting(configuration, self.model, modelTime)
        
        # option for steady-state simulation:
        self.steady_state_only = configuration.steady_state_only
        
        # make the configuration available for the other method/function
        self.configuration = configuration
        
        # indicating whether this run includes modflow or merging processes
        # - Only the "Global" and "part_one" runs include modflow or merging processes 
        self.include_merging_or_modflow = True
        if self.configuration.globalOptions['cloneAreas'] == "part_two": self.include_merging_or_modflow = False
        
        if self.include_merging_or_modflow:
        
            # netcdf merging options
            self.netcdf_format = self.configuration.mergingOutputOptions['formatNetCDF']
            self.zlib_option   = self.configuration.mergingOutputOptions['zlib']
            
            # output files/variables that will be merged
            nc_report_list = ["outDailyTotNC",
                              "outMonthTotNC", "outMonthAvgNC", "outMonthEndNC",
                              "outAnnuaTotNC", "outAnnuaAvgNC", "outAnnuaEndNC" ]
            for nc_report_type in nc_report_list:
                vars(self)[nc_report_type] = self.configuration.mergingOutputOptions[nc_report_type]
        
    def initial(self): 
        
        # get or prepare the initial condition for groundwater head 
        self.model.get_initial_heads()
        
        if self.steady_state_only: sys.exit() 

    def dynamic(self):

        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        # update/calculate model and daily merging, and report ONLY at the last day of the month
        if self.modelTime.isLastDayOfMonth():
            
            # wait until all pcrglobwb model runs are done
            pcrglobwb_is_ready = False
            self.count_check = 0
            while pcrglobwb_is_ready == False and self.configuration.online_coupling_between_pcrglobwb_and_moflow:
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
            if self.configuration.online_coupling_between_pcrglobwb_and_moflow:
                cmd = 'python '+ self.configuration.path_of_this_module + "/merge_pcraster_maps.py " + str(self.modelTime.fulldate) + " " +\
                                                                                                       str(self.configuration.main_output_directory)+"/ default 8 "+\
                                                                                                       str("Global")
                vos.cmd_line(cmd, using_subprocess = False)
                
                # cleaning up unmerged files (not tested yet)
                clean_up_pcraster_maps = False
                if self.configuration.mergingOutputOptions["delete_unmerged_pcraster_maps"] == "True": clean_up_pcraster_maps = True                    # TODO: FIXME: This is NOT working yet.
                if clean_up_pcraster_maps:                                                                                    
                    files_to_be_removed = glob.glob(str(self.configuration.main_output_directory) + "/M*/maps/*" + str(self.modelTime.fulldate) + "*")
                    for f in files_to_be_removed: os.remove(f)
                    
                vos.cmd_line(cmd, using_subprocess = False)

                # update MODFLOW model (It will pick up current model time from the modelTime object)
                self.model.update()
                # reporting is only done at the end of the month
                self.reporting.report()

        # monthly and annual merging
        if self.modelTime.isLastDayOfYear():

            # merging netcdf files at monthly resolutions
            start_date = '%04i-01-31' %(self.modelTime.year)                  # TODO: Make it flexible for a run starting not on the 1st January.
            self.merging_netcdf_files("outMonthTotNC", start_date, end_date)
            self.merging_netcdf_files("outMonthAvgNC", start_date, end_date)
            self.merging_netcdf_files("outMonthEndNC", start_date, end_date)

            # merging netcdf files at annual resolutions
            start_date = '%04i-12-31' %(self.modelTime.year)                  # TODO: Make it flexible for a run starting not on the 1st January.
            end_date   = self.modelTime.fulldate
            self.merging_netcdf_files("outAnnuaTotNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaAvgNC", start_date, end_date)
            self.merging_netcdf_files("outAnnuaEndNC", start_date, end_date)


        # make an empty file indicating that merging process is done 
        if self.modelTime.isLastDayOfMonth() or self.modelTime.isLastDayOfYear():

            outputDirectory = str(self.configuration.main_output_directory) + "/global/netcdf/"
            filename = outputDirectory + "/merged_netcdf_files_for_" + str(self._modelTime.fulldate)+"_are_ready.txt"
            if os.path.exists(filename): os.remove(filename)
            open(filename, "w").close()    


    def merging_netcdf_files(self, nc_report_type, start_date, end_date, max_number_of_cores = 20):

        if str(vars(self)[nc_report_type]) != "None":
        
            netcdf_files_that_will_be_merged = vars(self)[nc_report_type]
            
            msg = "Merging netcdf files for the files/variables: " + netcdf_files_that_will_be_merged
            logger.info(msg)
            
            cmd = 'python '+ self.configuration.path_of_this_module + "/merge_netcdf.py " + str(self.configuration.main_output_directory) + " " +\
                                                                                            str(self.configuration.main_output_directory) + "/global/netcdf/ "+\
                                                                                            str(nc_report_type)  + " " +\
                                                                                            str(start_date) + " " +\
                                                                                            str(end_date)   + " " +\
                                                                                            str(netcdf_files_that_will_be_merged) + " " +\
                                                                                            str(self.netcdf_format)  + " "  +\
                                                                                            str(self.zlib_option  )  + " "  +\
                                                                                            str(max_number_of_cores) + " "  +\
                                                                                            str("Global")  + " "
            
            msg = "Using the following command line: " + cmd
            logger.info(msg)
            
            vos.cmd_line(cmd, using_subprocess = False)

    def check_pcrglobwb_status(self):

        if self.configuration.globalOptions['cloneAreas'] == "Global" or \
           self.configuration.globalOptions['cloneAreas'] == "part_one":
            clone_areas = ['M%02d'%i for i in range(1,53+1,1)]
        else:
            clone_areas = list(set(self.configuration.globalOptions['cloneAreas'].split(",")))
        for clone_area in clone_areas:
            status_file = str(self.configuration.globalOptions['outputDir'])+"/"+str(clone_area)+"/maps/pcrglobwb_files_for_"+str(self.modelTime.fulldate)+"_are_ready.txt"
            msg = 'Waiting for the file: '+status_file
            if self.count_check < 7:
                logger.debug(msg)
                self.count_check += 1
            status = os.path.exists(status_file)
            if status == False: return status
            if status: self.count_check = 0            
                    
        print status
        
        return status

def main():
    
    # get the full path of configuration/ini file given in the system argument
    iniFileName   = os.path.abspath(sys.argv[1])
    
    # debug option
    debug_mode = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "debug" or sys.argv[2] == "debug_parallel": debug_mode = True
    
    # options to perform steady state calculation
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
    sys.exit(main())

