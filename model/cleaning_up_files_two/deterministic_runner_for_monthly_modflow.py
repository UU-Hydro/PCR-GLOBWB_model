#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import datetime

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
        
        self.steady_state_only = configuration.steady_state_only
        
        # make the configuration available for the other method/function
        self.configuration = configuration
        
    def initial(self): 
        
        # get or prepare the initial condition for groundwater head 
        self.model.get_initial_heads()
        
        if self.steady_state_only: sys.exit() 

    def dynamic(self):

        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        # update/calculate model and report ONLY at the last day of the month
        if self.modelTime.isLastDayOfMonth():
            
            # wait until all pcrglobwb model runs are done
            pcrglobwb_is_ready = False
            self.count_check = 0
            while pcrglobwb_is_ready == False and self.configuration.online_coupling_between_pcrglobwb_and_moflow:
                if datetime.datetime.now().second == 7 or\
                   datetime.datetime.now().second == 10 or\
                   datetime.datetime.now().second == 16 or\
                   datetime.datetime.now().second == 6:\
                   pcrglobwb_is_ready = self.check_pcrglobwb_status()
                
            # merging pcraster maps that are needed to run modflow
            if self.configuration.online_coupling_between_pcrglobwb_and_moflow:
                cmd = 'python '+ self.configuration.path_of_this_module + "/merge_pcr_maps_for_modflow.py " + str(self.modelTime.fulldate) + " " +\
                                                                                                              str(self.configuration.main_output_directory)+"/ default 8 "+\
                                                                                                              str(self.configuration.globalOptions['cloneAreas'])
                vos.cmd_line(cmd, using_subprocess = False)
                
                # cleaning up unmerged files (not tested yet)
                clean_up_pcraster_maps = False
                if clean_up_pcraster_maps:                                                                                    
                    files_to_be_removed = glob.glob(str(self.configuration.main_output_directory) + "/M*/maps/*" + str(self.modelTime.fulldate) + "*")
                    for f in files_to_be_removed: os.remove(f)
                    
                vos.cmd_line(cmd, using_subprocess = False)

            # update MODFLOW model (It will pick up current model time from the modelTime object)
            self.model.update()
            # reporting is only done at the end of the month
            self.reporting.report()

    def check_pcrglobwb_status(self):

        if self.configuration.globalOptions['cloneAreas'] == "Global":
            clone_areas = ['M%02d'%i for i in range(1,53+1,1)]
        else:
            clone_areas = list(set(self.configuration.globalOptions['cloneAreas'].split(",")))
        for clone_area in clone_areas:
            status_file = str(self.configuration.main_output_directory)+"/"+str(clone_area)+"/maps/pcrglobwb_files_for_"+str(self.modelTime.fulldate)+"_are_ready.txt"
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
        if sys.argv[2] == "debug": debug_mode = True
    
    # option to perform steady state calculation only
    steady_state_only = False
    if len(sys.argv) > 3:
        if sys.argv[3] == "steady-state": steady_state_only = True
    
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

