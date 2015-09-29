#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

from configuration import Configuration
from currTimeStep import ModelTime
from reporting import Reporting
from spinUp import SpinUp

from pcrglobwb import PCRGlobWB

import logging
logger = logging.getLogger(__name__)

class DeterministicRunner(DynamicModel):

    def __init__(self, configuration, modelTime, initialState = None):
        DynamicModel.__init__(self)

        self.modelTime = modelTime        
        self.model = PCRGlobWB(configuration, modelTime, initialState)
        self.reporting = Reporting(configuration, self.model, modelTime)
        
    def initial(self): 
        pass

    def dynamic(self):

        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        # update model (will pick up current model time from model time object)
        
        self.model.read_forcings()
        self.model.update(report_water_balance=False)     # for coupling with MODFLOW, the water balance check is turned off 
                                                          # as the water balance check ignores the contribution of lateral flow

        # do any needed reporting for this time step        
        self.reporting.report()

def main():
    
    # get the full path of configuration/ini file given in the system argument
    iniFileName   = os.path.abspath(sys.argv[1])
    
    # debug option
    debug_mode = False
    if len(sys.argv) > 2: 
        if sys.argv[2] == "debug": debug_mode = True
    
    # object to handle configuration/ini file
    configuration = Configuration(iniFileName = iniFileName, \
                                  debug_mode = debug_mode, \
                                  no_modification = False)      

    # modify startTime and endTime based on the given system argurments 
    # startTime = 1960-01-01
    # endTime   = 1960-02-31
    configuration.globalOptions['startTime'] = sys.argv[3]
    configuration.globalOptions['endTime']   = sys.argv[4]

    # change the clone and landmask
    configuration.globalOptions["cloneMap"]  = configuration.globalOptions["cloneMap"].replace("CLONE_MULTIPLE", str(sys.argv[5]))
    configuration.globalOptions["landmask"]  = configuration.globalOptions["landmask"].replace("CLONE_MULTIPLE", str(sys.argv[5]))

    # change the output directory
    configuration.globalOptions["outputDir"] = configuration.globalOptions["outputDir"].replace("CLONE_MULTIPLE", str(sys.argv[5]))
    configuration.globalOptions["outputDir"] = configuration.globalOptions["outputDir"].replace("MONTHLY_OUTPUT_FOLDER", str(sys.argv[6]))

    # set configuration
    configuration.set_configuration()
    
    # timeStep info: year, month, day, doy, hour, etc
    currTimeStep = ModelTime() 
    
    # NOTE: # NO spinningUp, good/reasonable initial conditions must be provided from files.   
    initial_state = None
    
    # Running the deterministic_runner (excluding DA scheme)
    currTimeStep.getStartEndTimeSteps(configuration.globalOptions['startTime'],
                                      configuration.globalOptions['endTime'])
    
    logger.info('Transient simulation run started.')
    deterministic_runner = DeterministicRunner(configuration, currTimeStep, initial_state)
    
    dynamic_framework = DynamicFramework(deterministic_runner,currTimeStep.nrOfTimeSteps)
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()

if __name__ == '__main__':
    sys.exit(main())

