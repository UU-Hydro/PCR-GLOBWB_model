import os
import sys
import math
import gc

import pcraster as pcr

import virtualOS as vos
import meteo
import landSurface
import groundwater
import routing


import logging
logger = logging.getLogger(__name__)

'''
Created on May 20, 2015

@author: Edwin H. Sutanudjaja
'''
class ModflowOfflineCoupling(object):
    
    def __init__(self, configuration, currTimeStep, initialState = None):
        self._configuration = configuration
        self._modelTime = currTimeStep
        
        pcr.setclone(configuration.cloneMap)

        # read the ldd map
        self.lddMap = vos.readPCRmapClone(\
                  configuration.routingOptions['lddMap'],
                  configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'],True)
        # ensure ldd map is correct, and actually of type "ldd"
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
 
        # defining the landmask map
        if configuration.globalOptions['landmask'] != "None":
            self.landmask = vos.readPCRmapClone(\
            configuration.globalOptions['landmask'],
            configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'])
        else:
            self.landmask = pcr.defined(self.lddMap)
        
        self.createSubmodels(initialState)
         
    @property
    def configuration(self):
        return self._configuration
         
    def createSubmodels(self, initialState):

        # initializing sub modules
        self.meteo = meteo.Meteo(self._configuration,self.landmask,initialState)
        self.landSurface = landSurface.LandSurface(self._configuration,self.landmask,initialState)
        self.groundwater = groundwater.Groundwater(self._configuration,self.landmask,initialState)
        self.routing = routing.Routing(self._configuration, initialState, self.lddMap)
 
    def dumpState(self, outputDirectory):
        #write all state to disk to facilitate restarting

        state = self.getState()
        
        groundWaterState = state['groundwater']
        for variable, map in groundWaterState.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             str(self._modelTime.fulldate)+".map",\
             outputDirectory)

    def getState(self):
        result = {}
        result['groundwater'] = self.groundwater.getState()
        
        return result
        
    def update(self, report_water_balance=False):
        logger.info("updating model for time %s", self._modelTime)
        
        self.groundwater.update(self.landSurface,self.routing,self._modelTime)
        self.routing.update(self.landSurface,self.groundwater,self._modelTime,self.meteo)

        # save/dump states at the end of the year or at the end of model simulation
        if self._modelTime.isLastDayOfYear() or self._modelTime.isLastTimeStep():
            logger.info("save/dump states to pcraster maps for time %s to the directory %s", self._modelTime, self._configuration.endStateDir)
            self.dumpState(self._configuration.endStateDir)

        if (report_water_balance):
            landWaterStoresAtEnd    = self.totalLandWaterStores()          # not including surface water bodies
            surfaceWaterStoresAtEnd = self.totalSurfaceWaterStores()     
            
            # water balance check for the land surface water part
            self.checkLandSurfaceWaterBalance(landWaterStoresAtBeginning, landWaterStoresAtEnd)
            
            # TODO: include water balance checks for the surface water part and combination of both land surface and surface water parts

            self.report_summary(landWaterStoresAtBeginning, landWaterStoresAtEnd,\
                                surfaceWaterStoresAtBeginning, surfaceWaterStoresAtEnd)
