#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

from configuration import Configuration
from currTimeStep import ModelTime
from reporting import Reporting
from spinUp import SpinUp
import pcraster as pcr

from pcrglobwb import PCRGlobWB

logger = logging.getLogger(__name__)

class DeterministicRunner(DynamicModel):

    def __init__(self, configuration, modelTime, initialState = None):
        DynamicModel.__init__(self)

        self.modelTime = modelTime        
        self.model = PCRGlobWB(configuration, modelTime, initialState)
        self.reporting = Reporting(configuration, self.model, modelTime)
        
    def initial(self):
        #self.model.landSurface.parameters.kSatUpp = self.model.landSurface.parameters.kSatUpp*0.1
        #self.model.landSurface.parameters.kSatLow = self.model.landSurface.parameters.kSatLow*0.1
        #self.model.groundwater.recessionCoeff = pcr.min(1.0000,self.model.groundwater.recessionCoeff*10.0)
        pass

    def dynamic(self):

        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        # update model (will pick up current model time from model time object)
        
        self.model.read_forcings()
        self.model.update(report_water_balance=True)
        

        #do any needed reporting for this time step        
        self.reporting.report()

def main():
    initial_state = None
    configuration = Configuration()
    
    spin_up = SpinUp(configuration)                   # object for spin_up
    
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

