import os
import sys
import math
import gc

import pcraster as pcr

import virtualOS as vos
import groundwater_MODFLOW

import logging
logger = logging.getLogger(__name__)

'''
Created on May 20, 2015

@author: Edwin H. Sutanudjaja
'''
class ModflowCoupling(object):
    
    def __init__(self, configuration, currTimeStep):
        self._configuration = configuration
        self._modelTime = currTimeStep
        
        pcr.setclone(configuration.cloneMap)

        # read the ldd map
        self.lddMap = vos.netcdf2PCRobjCloneWithoutTime(configuration.modflowParameterOptions['channelNC'],'lddMap',\
                                                        configuration.cloneMap)
        # ensure ldd map is correct, and actually of type "ldd"
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
 
        # defining the landmask map
        if configuration.globalOptions['landmask'] != "None":
            self.landmask = vos.readPCRmapClone(\
            configuration.globalOptions['landmask'],
            configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'])
        else:
            self.landmask = pcr.defined(self.lddMap)
        
        # preparing the sub-model(s)         - Currently, there is only one sub-model. 
        self.createSubmodels()
         
    @property
    def configuration(self):
        return self._configuration
         
    def createSubmodels(self):

        # initializing sub modules
        self.modflow = groundwater_MODFLOW.GroundwaterModflow(self.configuration,\
                                                              self.landmask)
        
    def dumpState(self, outputDirectory, timeStamp = "Default"):

        # write all states to disk to facilitate restarting

        state = self.getState()
        
        groundWaterState = state['groundwater']
        
        # time stamp used as part of the file name:
        if timeStamp == "Default": timeStamp = str(self._modelTime.fulldate) 
        
        for variable, map in groundWaterState.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             timeStamp+".map",\
             outputDirectory)

    def getState(self):
        result = {}
        result['groundwater'] = self.modflow.getState()
        
        return result
        
    def update(self):
        logger.info("Updating model for time %s", self._modelTime)
        
        self.modflow.update(self._modelTime)

        # save/dump states at the end of the month or at the end of model simulation
        if self._modelTime.isLastDayOfMonth() or self._modelTime.isLastTimeStep():
            logger.info("Save or dump states to pcraster maps for time %s to the directory %s", self._modelTime, self._configuration.endStateDir)
            self.dumpState(self._configuration.endStateDir)

    def get_initial_heads(self):
        logger.info("Get initial head values (based on a steady-state simulation or a pre-defined pcraster map.")
        
        self.modflow.get_initial_heads()

        # save/dump states used as the initial conditions 
        logger.info("Save/dump states of the initial conitions used to pcraster maps to the directory %s", self._configuration.endStateDir)
        self.dumpState(outputDirectory = self._configuration.endStateDir,\
                             timeStamp = self._configuration.globalOptions['startTime']+".ini")


