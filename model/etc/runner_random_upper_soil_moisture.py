#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

import pcraster as pcr

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

        self.model.read_forcings()
        self.model.update(report_water_balance=True)

        # get observation data
        sattelite_satDegUpp000005 = self.get_satDegUpp000005_from_observation()
        
        # set upper soil moisture state based on observation data
        self.set_satDegUpp000005(sattelite_satDegUpp000005)                            

        # do any needed reporting for this time step        
        self.reporting.report()

    def get_satDegUpp000005_from_observation(self):

        # assumption for observation values
        # - this should be replaced by values from the ECV soil moisture value (sattelite data)
        # - uncertainty should be included here
        # - note that the value should be between 0.0 and 1.0
        observed_satDegUpp000005 = pcr.min(1.0,\
                                   pcr.max(0.0,\
                                   pcr.normal(pcr.boolean(1)) + 1.0))
        return observed_satDegUpp000005                           

    def set_satDegUpp000005(self, observed_satDegUpp000005):

        # ratio between observation and model
        ratio_between_observation_and_model = pcr.ifthenelse(self.model.landSurface.satDegUpp000005> 0.0, 
                                                             observed_satDegUpp000005 / \
                                                             self.model.landSurface.satDegUpp000005, 0.0) 
        
        # updating upper soil states for all lad cover types
        for coverType in self.model.landSurface.coverTypes:
            
            # correcting upper soil state (storUpp000005)
            self.model.landSurface.landCoverObj[coverType].storUpp000005 *= ratio_between_observation_and_model
            
            # if model value = 0.0, storUpp000005 is calculated based on storage capacity (model parameter) and observed saturation degree   
            self.model.landSurface.landCoverObj[coverType].storUpp000005  = pcr.ifthenelse(self.model.landSurface.satDegUpp000005 > 0.0,\
                                                                                           self.model.landSurface.landCoverObj[coverType].storUpp000005,\
                                                                                           observed_satDegUpp000005 * self.model.landSurface.parameters.storCapUpp000005) 


def main():
    initial_state = None
    
    configuration = Configuration(sys.argv)    # object to handle configuration or ini file; ini file is taken from system/comand line agurment
    spin_up = SpinUp(configuration)            # object for spin_up
    
    currTimeStep = ModelTime() # timeStep info: year, month, day, doy, hour, etc
    
    # spinningUp
    noSpinUps = int(configuration.globalOptions['maxSpinUpsInYears'])
    if noSpinUps > 0:
        
        logger.info('Spin-Up #Total Years: '+str(noSpinUps))

        spinUpRun = 0 ; has_converged = False
        while spinUpRun < noSpinUps and has_converged == False:
            spinUpRun += 1
            currTimeStep.getStartEndTimeStepsForSpinUp(
                    configuration.globalOptions['startTime'],
                    spinUpRun, noSpinUps)
            logger.info('Spin-Up Run No. '+str(spinUpRun))
            deterministic_runner = DeterministicRunner(configuration, currTimeStep, initial_state)
            
            all_state_begin = deterministic_runner.model.getAllState() 
            
            dynamic_framework = DynamicFramework(deterministic_runner,currTimeStep.nrOfTimeSteps)
            dynamic_framework.setQuiet(True)
            dynamic_framework.run()
            
            all_state_end = deterministic_runner.model.getAllState() 
            
            has_converged = spin_up.checkConvergence(all_state_begin, all_state_end, spinUpRun, deterministic_runner.model.routing.cellArea)
            
            initial_state = deterministic_runner.model.getState()
    #
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

