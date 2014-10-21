import os
import sys
import math
import gc
import logging

import pcraster as pcr

import virtualOS as vos
import meteo
import landSurface
import groundwater
import routing


logger = logging.getLogger(__name__)

'''
Created on Oct 25, 2013

@author: Niels Drost
'''
class PCRGlobWB(object):
    
    def __init__(self, configuration, currTimeStep, initialState = None):
        self._configuration = configuration
        self._modelTime = currTimeStep
        
        pcr.setclone(configuration.cloneMap)

        # Read the ldd map.
        self.lddMap = vos.readPCRmapClone(\
                  configuration.routingOptions['lddMap'],
                  configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'],True)
        #ensure ldd map is correct, and actually of type "ldd"
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
 
        if configuration.globalOptions['landmask'] != "None":
            self.landmask = vos.readPCRmapClone(\
            configuration.globalOptions['landmask'],
            configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'])
        else:
            self.landmask = pcr.defined(self.lddMap)
        
        # number of upperSoilLayers:
        self.numberOfSoilLayers = int(configuration.landSurfaceOptions['numberOfUpperSoilLayers'])

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
 
        # short name for every land cover type (needed for file name)
        self.shortNames = ['f','g','p','n']
        
        
    def dumpState(self, outputDirectory):
        #write all state to disk to facilitate restarting

        if outputDirectory == None:
            return
        
        state = self.getState()
        
        landSurfaceState = state['landSurface']
        
        for coverType, coverTypeState in landSurfaceState.iteritems():
            for variable, map in coverTypeState.iteritems():
                vos.writePCRmapToDir(\
                map,\
                 str(variable)+"_"+coverType+"_"+
                 str(self._modelTime.fulldate)+".map",\
                 outputDirectory)
                
        groundWaterState = state['groundwater']
        for variable, map in groundWaterState.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             str(self._modelTime.fulldate)+".map",\
             outputDirectory)

        routingState = state['routing']
        for variable, map in routingState.iteritems():
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             str(self._modelTime.fulldate)+".map",\
             outputDirectory)
        
    def resume(self):
        #restore state from disk. used when restarting
        pass


    #FIXME: implement
    def setState(self, state):
        logger.info("cannot set state")

        
    def report(self, storesAtBeginning, storesAtEnd):
        #report the state. which states are written when is based on the configuration

        #set total to 0 on first day of the year                             
        if self._modelTime.doy == 1 or self._modelTime.isFirstTimestep():

            # set all accumulated variables to zero
            self.precipitationAcc  = pcr.ifthen(self.landmask, pcr.scalar(0.0)) 

            for var in self.landSurface.fluxVars: vars(self)[var+'Acc'] = pcr.ifthen(self.landmask, pcr.scalar(0.0))            

            self.nonFossilGroundwaterAbsAcc   = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.allocNonFossilGroundwaterAcc = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.baseflowAcc                  = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            self.surfaceWaterInfAcc           = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            self.runoffAcc                    = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.unmetDemandAcc               = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            self.waterBalanceAcc              = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.absWaterBalanceAcc           = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            # also save the storage at the first day of the year (or the first time step)
            self.storageAtFirstDay  = pcr.ifthen(self.landmask, storesAtBeginning) 
            
        # accumulating until the last day of the year:
        self.precipitationAcc   += self.meteo.precipitation
        for var in self.landSurface.fluxVars: vars(self)[var+'Acc'] += vars(self.landSurface)[var]            

        self.nonFossilGroundwaterAbsAcc += self.groundwater.nonFossilGroundwaterAbs
        self.allocNonFossilGroundwaterAcc += self.groundwater.allocNonFossilGroundwater
        self.baseflowAcc         += self.groundwater.baseflow

        self.surfaceWaterInfAcc += self.groundwater.surfaceWaterInf
        
        self.runoffAcc           += self.routing.runoff
        self.unmetDemandAcc      += self.groundwater.unmetDemand

        self.waterBalance = \
          (storesAtBeginning - storesAtEnd +\
           self.meteo.precipitation + self.landSurface.irrGrossDemand + self.groundwater.surfaceWaterInf -\
           self.landSurface.actualET - self.routing.runoff - self.groundwater.nonFossilGroundwaterAbs)

        self.waterBalanceAcc    =    self.waterBalanceAcc + self.waterBalance
        self.absWaterBalanceAcc = self.absWaterBalanceAcc + pcr.abs(self.waterBalance)

        if self._modelTime.isLastDayOfYear():
            self.dumpState(self._configuration.endStateDir)
            
            msg = 'The following waterBalance checks assume fracWat = 0 for all cells (not including surface water bodies).'
            logging.getLogger("model").info(msg)                        # TODO: Improve these water balance checks. 

            totalCellArea = vos.getMapTotal(pcr.ifthen(self.landmask,self.routing.cellArea))
            msg = 'Total area = %e km2'\
                    % (totalCellArea/1e6)
            logging.getLogger("model").info(msg)

            deltaStorageOneYear = vos.getMapVolume( \
                                     pcr.ifthen(self.landmask,storesAtEnd) - \
                                     pcr.ifthen(self.landmask,self.storageAtFirstDay),
                                     self.routing.cellArea)
            msg = 'Delta total storage days 1 to %i in %i = %e km3 = %e mm'\
                % (    int(self._modelTime.doy),\
                       int(self._modelTime.year),\
                       deltaStorageOneYear/1e9,\
                       deltaStorageOneYear*1000/totalCellArea)
            logging.getLogger("model").info(msg)

            # reporting the endStates at the end of the Year:
            variableList = ['precipitation',
                            'nonFossilGroundwaterAbs',
                            'allocNonFossilGroundwater',
                            'baseflow',
                            'surfaceWaterInf',
                            'runoff',
                            'unmetDemand']
            variableList += self.landSurface.fluxVars
            variableList += ['waterBalance','absWaterBalance']                

            for var in variableList:
                volume = vos.getMapVolume(\
                            self.__getattribute__(var + 'Acc'),\
                            self.routing.cellArea)
                msg = 'Accumulated %s days 1 to %i in %i = %e km3 = %e mm'\
                    % (var,int(self._modelTime.doy),\
                           int(self._modelTime.year),volume/1e9,volume*1000/totalCellArea)
                logging.getLogger("model").info(msg)
        
    def getState(self):
        result = {}
        
        result['landSurface'] = self.landSurface.getState()
        result['groundwater'] = self.groundwater.getState()
        result['routing'] = self.routing.getState()
        
        return result
        
    def getPseudoState(self):
        result = {}
        
        result['landSurface'] = self.landSurface.getPseudoState()
        result['groundwater'] = self.groundwater.getPseudoState()
        result['routing'] = self.routing.getPseudoState()
        
        return result
    
    def getAllState(self):
        result = {}
        
        result['landSurface'] = self.landSurface.getState()
        result['landSurface'].update(self.landSurface.getPseudoState())
        
        result['groundwater']= self.groundwater.getState()
        result['groundwater'].update(self.groundwater.getPseudoState())
        
        result['routing'] = self.routing.getState()
        result['routing'].update(self.routing.getPseudoState())
        
        return result
        
    
    def totalLandStores(self):
        
        if self.numberOfSoilLayers == 2: total = \
                self.landSurface.interceptStor  +\
                self.landSurface.snowFreeWater  +\
                self.landSurface.snowCoverSWE   +\
                self.landSurface.topWaterLayer  +\
                self.landSurface.storUpp        +\
                self.landSurface.storLow        +\
                self.groundwater.storGroundwater

        if self.numberOfSoilLayers == 3: total = \
                self.landSurface.interceptStor  +\
                self.landSurface.snowFreeWater  +\
                self.landSurface.snowCoverSWE   +\
                self.landSurface.topWaterLayer  +\
                self.landSurface.storUpp000005  +\
                self.landSurface.storUpp005030  +\
                self.landSurface.storLow030150  +\
                self.groundwater.storGroundwater
        
        total = pcr.ifthen(self.landmask, total)
        
        return total
    
    def checkWaterBalance(self, storesAtBeginning, storesAtEnd):
		# for the entire modules: snow + interception + soil + groundwater + waterDemand
		# except: river/routing 

        irrGrossDemand  = pcr.ifthen(self.landmask,\
                                self.landSurface.irrGrossDemand)        # unit: m

        nonIrrGrossDemand = \
                           pcr.ifthen(self.landmask,\
                                self.landSurface.nonIrrGrossDemand)     # unit: m

        precipitation   = pcr.ifthen(self.landmask,\
                                     self.meteo.precipitation)          # unit: m

        surfaceWaterInf =  pcr.ifthen(self.landmask,\
                                      self.groundwater.surfaceWaterInf)
        
        surfaceWaterAbstraction = \
                           pcr.ifthen(self.landmask,\
                                      self.landSurface.actSurfaceWaterAbstract)                                     
        
        nonFossilGroundwaterAbs = pcr.ifthen(self.landmask,self.groundwater.nonFossilGroundwaterAbs)   

        unmetDemand      = pcr.ifthen(self.landmask,\
                                      self.groundwater.unmetDemand)                                   # PS: We assume that unmetDemand is extracted (only) to satisfy local demand.

        runoff           = pcr.ifthen(self.landmask,self.routing.runoff)
        
        actualET         = pcr.ifthen(self.landmask,\
                                      self.landSurface.actualET)

        vos.waterBalanceCheck([precipitation,surfaceWaterInf,irrGrossDemand],\
                              [actualET,runoff,nonFossilGroundwaterAbs],\
                              [storesAtBeginning],\
                              [storesAtEnd],\
                              'all modules (including water demand), but except river/routing',\
                               True,\
                               self._modelTime.fulldate,threshold=1e-3)

        
        if self.landSurface.usingAllocSegments:

            allocSurfaceWaterAbstract = \
                           pcr.ifthen(self.landmask,\
                                      self.landSurface.allocSurfaceWaterAbstract)

            allocNonFossilGroundwaterAbs = \
                           pcr.ifthen(self.landmask,\
                                      self.groundwater.allocNonFossilGroundwater)

            allocUnmetDemand = unmetDemand                           # PS: We assume that unmetDemand is extracted (only) to satisfy local demand.

            segTotalDemand = pcr.areatotal( pcr.cover((irrGrossDemand+nonIrrGrossDemand)           * self.routing.cellArea, 0.0), self.landSurface.allocSegments) / self.landSurface.segmentArea
            
            segAllocSurfaceWaterAbstract    = pcr.areatotal( pcr.cover(allocSurfaceWaterAbstract   * self.routing.cellArea, 0.0), self.landSurface.allocSegments) / self.landSurface.segmentArea

            segAllocNonFossilGroundwaterAbs = pcr.areatotal( pcr.cover(allocNonFossilGroundwaterAbs * self.routing.cellArea, 0.0), self.landSurface.allocSegments) / self.landSurface.segmentArea

            segAllocUnmetDemand             = pcr.areatotal( pcr.cover(allocUnmetDemand * self.routing.cellArea, 0.0), self.landSurface.allocSegments) / self.landSurface.segmentArea
            
            vos.waterBalanceCheck([segTotalDemand],\
                                  [segAllocSurfaceWaterAbstract,segAllocNonFossilGroundwaterAbs,segAllocUnmetDemand],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)],\
                                  'Water balance error in water allocation (per zone). Note that error here is most likely due to rounding error (32 bit implementation of pcraster)',\
                                   True,\
                                   self._modelTime.fulldate,threshold=5e-3)
        else:    
            
            vos.waterBalanceCheck([irrGrossDemand,nonIrrGrossDemand],\
                                  [surfaceWaterAbstraction,nonFossilGroundwaterAbs,unmetDemand],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)],\
                                  'Water balance error in water allocation.',\
                                   True,\
                                   self._modelTime.fulldate,threshold=1e-3)
    
    def read_forcings(self):
        logger.info("reading forcings for time %s", self._modelTime)
        self.meteo.read_forcings(self._modelTime)
    
    def update(self, report_water_balance=False):
        logger.info("updating model to time %s", self._modelTime)
        
        if (report_water_balance):
            storesAtBeginning = self.totalLandStores()

        self.meteo.update(self._modelTime)                                         
        self.landSurface.update(self.meteo,self.groundwater,self.routing,self._modelTime)      
        self.groundwater.update(self.landSurface,self.routing,self._modelTime)
        self.routing.update(self.landSurface,self.groundwater,self._modelTime,self.meteo)

        if (report_water_balance):
            storesAtEnd = self.totalLandStores()
            self.checkWaterBalance(storesAtBeginning, storesAtEnd)
        
        if (report_water_balance):    
            self.report(storesAtBeginning, storesAtEnd)
