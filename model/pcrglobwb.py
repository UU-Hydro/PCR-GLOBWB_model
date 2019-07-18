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
import shutil
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
        
        # defining catchment areas
        self.catchment_class = 1.0
        
        # number of upperSoilLayers:
        self.numberOfSoilLayers = int(configuration.landSurfaceOptions['numberOfUpperSoilLayers'])

        # preparing sub-modules
        self.createSubmodels(initialState)
        
        # option for debugging to PCR-GLOBWB version 1.0
        self.debug_to_version_one = False
        if configuration.debug_to_version_one: self.debug_to_version_one = True
        if self.debug_to_version_one:
            
            # preparing initial folder directory
            self.directory_for_initial_maps = vos.getFullPath("initials/", self.configuration.mapsDir)
            if os.path.exists(self.directory_for_initial_maps): shutil.rmtree(self.directory_for_initial_maps)
            os.makedirs(self.directory_for_initial_maps)
            
            # dump the initial state
            self.dumpState(self.directory_for_initial_maps, "initial")

         
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
        
    def dumpState(self, outputDirectory, specific_date_string = None):
        #write all state to disk to facilitate restarting

        if specific_date_string == None: specific_date_string = str(self._modelTime.fulldate)
        
        state = self.getState()
        
        landSurfaceState = state['landSurface']
        
        for coverType, coverTypeState in list(landSurfaceState.items()):
            for variable, map in list(coverTypeState.items()):
                vos.writePCRmapToDir(\
                map,\
                 str(variable)+"_"+coverType+"_"+
                 specific_date_string+".map",\
                 outputDirectory)
                
        groundWaterState = state['groundwater']
        for variable, map in list(groundWaterState.items()):
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             specific_date_string+".map",\
             outputDirectory)

        routingState = state['routing']
        for variable, map in list(routingState.items()):
            vos.writePCRmapToDir(\
             map,\
             str(variable)+"_"+
             specific_date_string+".map",\
             outputDirectory)
        
    def calculateAndDumpMonthlyValuesForMODFLOW(self, outputDirectory, timeStamp = "Default"):

        logger.debug('Calculating (accumulating and averaging) and dumping some monthly variables for the MODFLOW input.')
        
        if self._modelTime.day == 1 or self._modelTime.timeStepPCR == 1:
            
            self.variables = {}
            
            self.variables['monthly_discharge_cubic_meter_per_second'] = pcr.ifthen(self.routing.landmask, pcr.max(0.0, self.routing.disChanWaterBody))
            self.variables['groundwater_recharge_meter_per_day'] = pcr.ifthen(self.routing.landmask, self.landSurface.gwRecharge)
            self.variables['groundwater_abstraction_meter_per_day'] = pcr.ifthen(self.routing.landmask, self.landSurface.totalGroundwaterAbstraction)
        
        self.variables['monthly_discharge_cubic_meter_per_second'] += pcr.ifthen(self.routing.landmask, pcr.max(0.0, self.routing.disChanWaterBody))
        self.variables['groundwater_recharge_meter_per_day'] += pcr.ifthen(self.routing.landmask, self.landSurface.gwRecharge)
        self.variables['groundwater_abstraction_meter_per_day'] += pcr.ifthen(self.routing.landmask, self.landSurface.totalGroundwaterAbstraction)
        
        if self._modelTime.isLastDayOfMonth():

            # averaging monthly discharge, groundwater recharge and groundwater abstraction
            number_of_days = min(self._modelTime.day, self._modelTime.timeStepPCR)
            self.variables['monthly_discharge_cubic_meter_per_second'] = self.variables['monthly_discharge_cubic_meter_per_second'] / number_of_days # unit: m3/s
            self.variables['groundwater_recharge_meter_per_day'] = self.variables['groundwater_recharge_meter_per_day'] / number_of_days             # unit: m/day
            self.variables['groundwater_abstraction_meter_per_day'] = self.variables['groundwater_abstraction_meter_per_day'] / number_of_days       # unit: m/day
        
            # channel storage at the last day of the month
            self.variables['channel_storage_cubic_meter'] = pcr.ifthen(self.routing.landmask, self.routing.channelStorage)                           # unit: m/day

            # time stamp used as part of the file name:
            if timeStamp == "Default": timeStamp = str(self._modelTime.fulldate) 
            
            logger.info('Dumping some monthly variables for the MODFLOW input.')

            for variable, map in list(self.variables.items()):
                vos.writePCRmapToDir(\
                 map,\
                 str(variable)+"_"+
                 timeStamp+".map",\
                 outputDirectory)
            
    def resume(self):
        #restore state from disk. used when restarting
        pass


    #FIXME: implement
    def setState(self, state):
        logger.error("cannot set state")

        
    def report_summary(self, landWaterStoresAtBeginning, landWaterStoresAtEnd,\
                             surfaceWaterStoresAtBeginning, surfaceWaterStoresAtEnd):

        # set total to 0 on first day of the year                             
        if self._modelTime.doy == 1 or self._modelTime.isFirstTimestep():

            # set all accumulated variables to zero

            self.precipitationAcc  = pcr.ifthen(self.landmask, pcr.scalar(0.0)) 

            for var in self.landSurface.fluxVars: vars(self)[var+'Acc'] = pcr.ifthen(self.landmask, pcr.scalar(0.0))            

            self.baseflowAcc                  = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            self.surfaceWaterInfAcc           = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            self.runoffAcc                    = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.unmetDemandAcc               = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            self.waterBalanceAcc              = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.absWaterBalanceAcc           = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            # non irrigation water use (unit: m) 
            self.nonIrrigationWaterUseAcc     = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            
            # non irrigation return flow to water body and water body evaporation (unit: m) 
            self.nonIrrReturnFlowAcc          = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.waterBodyEvaporationAcc      = pcr.ifthen(self.landmask, pcr.scalar(0.0))

            # surface water input/loss volume (m3) and outgoing volume (m3) at pits 
            self.surfaceWaterInputAcc         = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            self.dischargeAtPitAcc            = pcr.ifthen(self.landmask, pcr.scalar(0.0))
            
            # also save the storages at the first day of the year (or the first time step)
            # - land surface storage (unit: m)
            self.storageAtFirstDay            = pcr.ifthen(self.landmask, landWaterStoresAtBeginning)
            # - channel storages (unit: m3)
            self.channelVolumeAtFirstDay      = pcr.ifthen(self.landmask, surfaceWaterStoresAtBeginning)
            
        # accumulating until the last day of the year:
        self.precipitationAcc   += self.meteo.precipitation
        for var in self.landSurface.fluxVars: vars(self)[var+'Acc'] += vars(self.landSurface)[var]            

        self.baseflowAcc         += self.groundwater.baseflow

        self.surfaceWaterInfAcc  += self.groundwater.surfaceWaterInf
        
        self.runoffAcc           += self.routing.runoff
        self.unmetDemandAcc      += self.groundwater.unmetDemand

        self.waterBalance = \
          (landWaterStoresAtBeginning - landWaterStoresAtEnd +\
           self.meteo.precipitation + self.landSurface.irrGrossDemand + self.groundwater.surfaceWaterInf -\
           self.landSurface.actualET - self.routing.runoff - self.groundwater.nonFossilGroundwaterAbs)

        self.waterBalanceAcc    += self.waterBalance
        self.absWaterBalanceAcc += pcr.abs(self.waterBalance)

        # consumptive water use for non irrigation demand (m)
        self.nonIrrigationWaterUseAcc += self.routing.nonIrrWaterConsumption 
        
        self.waterBodyEvaporationAcc  += self.routing.waterBodyEvaporation

        self.surfaceWaterInputAcc     += self.routing.local_input_to_surface_water  # unit: m3
        self.dischargeAtPitAcc        += self.routing.outgoing_volume_at_pits       # unit: m3
        
        if self._modelTime.isLastDayOfYear() or self._modelTime.isLastTimeStep():
            
            logger.info("")
            msg = 'The following summary values do not include storages in surface water bodies (lake, reservoir and channel storages).'
            logger.info(msg)                        # TODO: Improve these water balance checks. 

            totalCellArea = vos.getMapTotal(pcr.ifthen(self.landmask, self.routing.cellArea))
            msg = 'Total area = %e km2'\
                    % (totalCellArea/1e6)
            logger.info(msg)

            deltaStorageOneYear = vos.getMapVolume( \
                                     pcr.ifthen(self.landmask,landWaterStoresAtBeginning) - \
                                     pcr.ifthen(self.landmask,self.storageAtFirstDay),
                                     self.routing.cellArea)
            msg = 'Delta total storage days 1 to %i in %i = %e km3 = %e mm'\
                % (    int(self._modelTime.doy),\
                       int(self._modelTime.year),\
                       deltaStorageOneYear/1e9,\
                       deltaStorageOneYear*1000/totalCellArea)
            logger.info(msg)

            variableList = ['precipitation',
                            'baseflow',
                            'surfaceWaterInf',
                            'runoff',
                            'unmetDemand']
            variableList += self.landSurface.fluxVars
            variableList += ['waterBalance','absWaterBalance','irrigationEvaporationWaterUse','nonIrrigationWaterUse']                

            # consumptive water use for irrigation (unit: m)
            self.irrigationEvaporationWaterUseAcc = vos.getValDivZero(self.irrGrossDemandAcc,\
                                                           self.precipitationAcc + self.irrGrossDemandAcc) * self.actualETAcc

            for var in variableList:
                volume = vos.getMapVolume(\
                            self.__getattribute__(var + 'Acc'),\
                            self.routing.cellArea)

                #~ # an eperiment: To test an improved version of map total - still need to be tested 
                #~ if var == "actSurfaceWaterAbstract" or var == "allocSurfaceWaterAbstract":
                    #~ volume = vos.getMapTotalHighPrecisionButOnlyForPositiveValues(self.__getattribute__(var + 'Acc') * self.routing.cellArea)

                msg = 'Accumulated %s days 1 to %i in %i = %e km3 = %e mm'\
                    % (var,int(self._modelTime.doy),\
                           int(self._modelTime.year),volume/1e9,volume*1000/totalCellArea)    # TODO: Calculation does not always start from day 1.
                logger.info(msg)

            logger.info("")
            msg = 'The following summary is for surface water bodies.'
            logger.info(msg) 

            deltaChannelStorageOneYear = vos.getMapTotal( \
                                         pcr.ifthen(self.landmask,surfaceWaterStoresAtEnd) - \
                                         pcr.ifthen(self.landmask,self.channelVolumeAtFirstDay))
            msg = 'Delta surface water storage days 1 to %i in %i = %e km3 = %e mm'\
                % (    int(self._modelTime.doy),\
                       int(self._modelTime.year),\
                       deltaChannelStorageOneYear/1e9,\
                       deltaChannelStorageOneYear*1000/totalCellArea)
            logger.info(msg)
            
            variableList = ['waterBodyEvaporation']
            for var in variableList:
                volume = vos.getMapVolume(\
                            self.__getattribute__(var + 'Acc'),\
                            self.routing.cellArea)
                msg = 'Accumulated %s days 1 to %i in %i = %e km3 = %e mm'\
                    % (var,int(self._modelTime.doy),\
                           int(self._modelTime.year),volume/1e9,volume*1000/totalCellArea)
                logger.info(msg)


            # surface water balance check 
            surfaceWaterInputTotal = vos.getMapTotal(self.surfaceWaterInputAcc)
            msg = 'Accumulated %s days 1 to %i in %i = %e km3 = %e mm'\
                    % ("surfaceWaterInput",int(self._modelTime.doy),\
                           int(self._modelTime.year),surfaceWaterInputTotal/1e9,surfaceWaterInputTotal*1000/totalCellArea)
            logger.info(msg)

            dischargeAtPitTotal = vos.getMapTotal(self.dischargeAtPitAcc)
            msg = 'Accumulated %s days 1 to %i in %i = %e km3 = %e mm'\
                    % ("dischargeAtPitTotal",int(self._modelTime.doy),\
                           int(self._modelTime.year),dischargeAtPitTotal/1e9,      dischargeAtPitTotal*1000/totalCellArea)
            logger.info(msg)

            surfaceWaterBalance = deltaChannelStorageOneYear - surfaceWaterInputTotal + dischargeAtPitTotal  
            msg = 'Accumulated %s days 1 to %i in %i = %e km3 = %e mm'\
                    % ("surfaceWaterBalance",int(self._modelTime.doy),\
                           int(self._modelTime.year),surfaceWaterBalance/1e9,      surfaceWaterBalance*1000/totalCellArea)
            logger.info(msg)
            
                
        
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
        
    
    def totalLandWaterStores(self):
        # unit: m, not including surface water bodies
        
        
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
    
    def totalSurfaceWaterStores(self):
        # unit: m3, only surface water bodies
        
        return pcr.ifthen(self.landmask, self.routing.channelStorage)

    def checkLandSurfaceWaterBalance(self, storesAtBeginning, storesAtEnd):
        
        # for the entire stores from snow + interception + soil + groundwater, but excluding river/routing
        # 
        # - incoming fluxes (unit: m)
        precipitation   = pcr.ifthen(self.landmask, self.meteo.precipitation)
        irrGrossDemand  = pcr.ifthen(self.landmask, self.landSurface.irrGrossDemand)
        surfaceWaterInf = pcr.ifthen(self.landmask, self.groundwater.surfaceWaterInf)
        # 
        # - outgoing fluxes (unit: m)
        actualET                = pcr.ifthen(self.landmask, self.landSurface.actualET)
        runoff                  = pcr.ifthen(self.landmask, self.routing.runoff)
        nonFossilGroundwaterAbs = pcr.ifthen(self.landmask, self.groundwater.nonFossilGroundwaterAbs)   
        # 
        vos.waterBalanceCheck([precipitation,surfaceWaterInf,irrGrossDemand],\
                              [actualET,runoff,nonFossilGroundwaterAbs],\
                              [storesAtBeginning],\
                              [storesAtEnd],\
                              'all stores (snow + interception + soil + groundwater), but except river/routing',\
                               True,\
                               self._modelTime.fulldate,threshold=1e-3)
    
    def read_forcings(self):
        logger.info("Reading forcings for time %s", self._modelTime)
        self.meteo.read_forcings(self._modelTime)
    
    def update(self, report_water_balance = False):
        logger.info("Updating model for time %s", self._modelTime)
        
        if (report_water_balance):
            landWaterStoresAtBeginning    = self.totalLandWaterStores()    # not including surface water bodies
            surfaceWaterStoresAtBeginning = self.totalSurfaceWaterStores()     

        self.meteo.update(self._modelTime)                                         
        self.landSurface.update(self.meteo, self.groundwater, self.routing, self._modelTime)      
        self.groundwater.update(self.landSurface, self.routing, self._modelTime)
        self.routing.update(self.landSurface, self.groundwater, self._modelTime, self.meteo)

        # save/dump states at the end of the year or at the end of model simulation
        if self._modelTime.isLastDayOfYear() or self._modelTime.isLastTimeStep():
            logger.info("Saving/dumping states to pcraster maps for time %s to the directory %s", self._modelTime, self._configuration.endStateDir)
            self.dumpState(self._configuration.endStateDir)

        # calculating and dumping some monthly values for the purpose of online coupling with MODFLOW:
        if self._configuration.online_coupling_between_pcrglobwb_and_modflow:
            self.calculateAndDumpMonthlyValuesForMODFLOW(self._configuration.mapsDir)
        
        if (report_water_balance):
            landWaterStoresAtEnd    = self.totalLandWaterStores()          # not including surface water bodies
            surfaceWaterStoresAtEnd = self.totalSurfaceWaterStores()     
            
            # water balance check for the land surface water part
            self.checkLandSurfaceWaterBalance(landWaterStoresAtBeginning, landWaterStoresAtEnd)
            
            # TODO: include water balance checks for the surface water part and combination of both land surface and surface water parts

            self.report_summary(landWaterStoresAtBeginning, landWaterStoresAtEnd,\
                                surfaceWaterStoresAtBeginning, surfaceWaterStoresAtEnd)

        if self._modelTime.isLastDayOfMonth():
            # make an empty file to indicate that the calculation for this month has done
            filename = self._configuration.mapsDir + "/pcrglobwb_files_for_" + str(self._modelTime.fulldate)+"_are_ready.txt"
            if os.path.exists(filename): os.remove(filename)
            open(filename, "w").close()    
