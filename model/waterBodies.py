#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Ludovicus P. H. (Rens) van Beek, Edwin H. Sutanudjaja, Yoshihide Wada,
# Joyce H. C. Bosmans, Niels Drost, Inge E. M. de Graaf, Kor de Jong, Patricia Lopez Lopez,
# Stefanie Pessenteiner, Oliver Schmitz, Menno W. Straatsma, Niko Wanders, Dominik Wisser,
# and Marc F. P. Bierkens,
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
import types

from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)


import virtualOS as vos

class WaterBodies(object):

    def __init__(self, iniItems, landmask, onlyNaturalWaterBodies = False, lddMap = None):
        object.__init__(self)

        # clone map file names, temporary directory and global/absolute path of input directory
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        self.iniItems = iniItems
                
        # local drainage direction:
        if isinstance(lddMap, types.NoneType):
            self.lddMap = vos.readPCRmapClone(iniItems.routingOptions['lddMap'],
                                                  self.cloneMap,self.tmpDir,self.inputDir,True)
            self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
            self.lddMap = pcr.lddrepair(self.lddMap)
        else:    
            self.lddMap = lddMap

        # the following is needed for a modflowOfflineCoupling run
        if 'modflowOfflineCoupling' in iniItems.globalOptions.keys() and iniItems.globalOptions['modflowOfflineCoupling'] == "True" and 'routingOptions' not in iniItems.allSections: 
            logger.info("The 'routingOptions' are not defined in the configuration ini file. We will adopt them from the 'modflowParameterOptions'.")
            iniItems.routingOptions = iniItems.modflowParameterOptions


        # option to activate water balance check
        self.debugWaterBalance = True
        if 'debugWaterBalance' in iniItems.routingOptions.keys() and iniItems.routingOptions['debugWaterBalance'] == "False":
            self.debugWaterBalance = False
        
        # option to perform a run with only natural lakes (without reservoirs)
        self.onlyNaturalWaterBodies = onlyNaturalWaterBodies
        if "onlyNaturalWaterBodies" in iniItems.routingOptions.keys() and iniItems.routingOptions['onlyNaturalWaterBodies'] == "True":
            logger.info("Using only natural water bodies identified in the year 1900. All reservoirs in 1900 are assumed as lakes.")
            self.onlyNaturalWaterBodies  = True
            self.dateForNaturalCondition = "1900-01-01"                  # The run for a natural condition should access only this date.   
        
        # names of files containing water bodies parameters
        if iniItems.routingOptions['waterBodyInputNC'] == str(None):
            self.useNetCDF = False
            self.fracWaterInp    = iniItems.routingOptions['fracWaterInp']
            self.waterBodyIdsInp = iniItems.routingOptions['waterBodyIds']
            self.waterBodyTypInp = iniItems.routingOptions['waterBodyTyp']
            self.resMaxCapInp    = iniItems.routingOptions['resMaxCapInp']
            self.resSfAreaInp    = iniItems.routingOptions['resSfAreaInp']
        else:
            self.useNetCDF = True
            self.ncFileInp       = vos.getFullPath(\
                                   iniItems.routingOptions['waterBodyInputNC'],\
                                   self.inputDir)

        # minimum width (m) used in the weir formula  # TODO: define minWeirWidth based on the GLWD, GRanD database and/or bankfull discharge formula 
        self.minWeirWidth = 10.

        # lower and upper limits at which reservoir release is terminated and 
        #                        at which reservoir release is equal to long-term average outflow
        # - default values
        self.minResvrFrac = 0.10
        self.maxResvrFrac = 0.75
        # - from the ini file
        if "minResvrFrac" in iniItems.routingOptions.keys():
            minResvrFrac = iniItems.routingOptions['minResvrFrac']
            self.minResvrFrac = vos.readPCRmapClone(minResvrFrac,
                                                    self.cloneMap, self.tmpDir, self.inputDir)
        if "maxResvrFrac" in iniItems.routingOptions.keys():
            maxResvrFrac = iniItems.routingOptions['maxResvrFrac']
            self.maxResvrFrac = vos.readPCRmapClone(maxResvrFrac,
                                                    self.cloneMap, self.tmpDir, self.inputDir)


    def getParameterFiles(self,currTimeStep,cellArea,ldd,\
                               initial_condition_dictionary = None,\
                               currTimeStepInDateTimeFormat = False):

        # parameters for Water Bodies: fracWat              
        #                              waterBodyIds
        #                              waterBodyOut
        #                              waterBodyArea 
        #                              waterBodyTyp
        #                              waterBodyCap
        
        # cell surface area (m2) and ldd
        self.cellArea = cellArea
        ldd = pcr.ifthen(self.landmask, ldd)
        
        # date used for accessing/extracting water body information
        if currTimeStepInDateTimeFormat:
            date_used = currTimeStep
            year_used = currTimeStep.year
        else:
            date_used = currTimeStep.fulldate
            year_used = currTimeStep.year
        if self.onlyNaturalWaterBodies == True:
            date_used = self.dateForNaturalCondition
            year_used = self.dateForNaturalCondition[0:4] 
        
        # fracWat = fraction of surface water bodies (dimensionless)
        self.fracWat = pcr.scalar(0.0)
        
        if self.useNetCDF:
            self.fracWat = vos.netcdf2PCRobjClone(self.ncFileInp,'fracWaterInp', \
                           date_used, useDoy = 'yearly',\
                           cloneMapFileName = self.cloneMap)
        else:
            self.fracWat = vos.readPCRmapClone(\
                           self.fracWaterInp+str(year_used)+".map",
                           self.cloneMap,self.tmpDir,self.inputDir)
        
        self.fracWat = pcr.cover(self.fracWat, 0.0)
        self.fracWat = pcr.max(0.0,self.fracWat)
        self.fracWat = pcr.min(1.0,self.fracWat)
        
        self.waterBodyIds  = pcr.nominal(0)    # waterBody ids
        self.waterBodyOut  = pcr.boolean(0)    # waterBody outlets
        self.waterBodyArea = pcr.scalar(0.)    # waterBody surface areas

        # water body ids
        if self.useNetCDF:
            self.waterBodyIds = vos.netcdf2PCRobjClone(self.ncFileInp,'waterBodyIds', \
                                date_used, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)
        else:
            self.waterBodyIds = vos.readPCRmapClone(\
                self.waterBodyIdsInp+str(year_used)+".map",\
                self.cloneMap,self.tmpDir,self.inputDir,False,None,True)
        #
        self.waterBodyIds = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0.,\
                            pcr.nominal(self.waterBodyIds))    

        # water body outlets (correcting outlet positions)
        wbCatchment = pcr.catchmenttotal(pcr.scalar(1),ldd)
        self.waterBodyOut = pcr.ifthen(wbCatchment ==\
                            pcr.areamaximum(wbCatchment, \
                            self.waterBodyIds),\
                            self.waterBodyIds) # = outlet ids           # This may give more than two outlets, particularly if there are more than one cells that have largest upstream areas      
        # - make sure that there is only one outlet for each water body 
        self.waterBodyOut = pcr.ifthen(\
                            pcr.areaorder(pcr.scalar(self.waterBodyOut), \
                            self.waterBodyOut) == 1., self.waterBodyOut)
        self.waterBodyOut = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0.,\
                            self.waterBodyOut)
        
        # TODO: Please also consider endorheic lakes!                    

        # correcting water body ids
        self.waterBodyIds = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0.,\
                            pcr.subcatchment(ldd,self.waterBodyOut))
        
        # boolean map for water body outlets:   
        self.waterBodyOut = pcr.ifthen(\
                            pcr.scalar(self.waterBodyOut) > 0.,\
                            pcr.boolean(1))

        # reservoir surface area (m2):
        if self.useNetCDF:
            resSfArea = 1000. * 1000. * \
                        vos.netcdf2PCRobjClone(self.ncFileInp,'resSfAreaInp', \
                        date_used, useDoy = 'yearly',\
                        cloneMapFileName = self.cloneMap)
        else:
            resSfArea = 1000. * 1000. * vos.readPCRmapClone(
                   self.resSfAreaInp+str(year_used)+".map",\
                   self.cloneMap,self.tmpDir,self.inputDir)
        resSfArea = pcr.areaaverage(resSfArea,self.waterBodyIds)                        
        resSfArea = pcr.cover(resSfArea,0.)                        

        # water body surface area (m2): (lakes and reservoirs)
        self.waterBodyArea = pcr.max(pcr.areatotal(\
                             pcr.cover(\
                             self.fracWat*self.cellArea, 0.0), self.waterBodyIds),
                             pcr.areaaverage(\
                             pcr.cover(resSfArea, 0.0) ,       self.waterBodyIds))
        self.waterBodyArea = pcr.ifthen(self.waterBodyArea > 0.,\
                             self.waterBodyArea)
                                
        # correcting water body ids and outlets (exclude all water bodies with surfaceArea = 0)
        self.waterBodyIds = pcr.ifthen(self.waterBodyArea > 0.,
                            self.waterBodyIds)               
        self.waterBodyOut = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                   self.waterBodyOut)

        # water body types:
        # - 2 = reservoirs (regulated discharge)
        # - 1 = lakes (weirFormula)
        # - 0 = non lakes or reservoirs (e.g. wetland)
        self.waterBodyTyp = pcr.nominal(0)
        
        if self.useNetCDF:
            self.waterBodyTyp = vos.netcdf2PCRobjClone(self.ncFileInp,'waterBodyTyp', \
                                date_used, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)
        else:
            self.waterBodyTyp = vos.readPCRmapClone(
                self.waterBodyTypInp+str(year_used)+".map",\
                self.cloneMap,self.tmpDir,self.inputDir,False,None,True)

        # excluding wetlands (waterBodyTyp = 0) in all functions related to lakes/reservoirs 
        #
        self.waterBodyTyp = pcr.ifthen(\
                            pcr.scalar(self.waterBodyTyp) > 0,\
                            pcr.nominal(self.waterBodyTyp))    
        self.waterBodyTyp = pcr.ifthen(\
                            pcr.scalar(self.waterBodyIds) > 0,\
                            pcr.nominal(self.waterBodyTyp))    
        self.waterBodyTyp = pcr.areamajority(self.waterBodyTyp,\
                                             self.waterBodyIds)     # choose only one type: either lake or reservoir                  
        self.waterBodyTyp = pcr.ifthen(\
                            pcr.scalar(self.waterBodyTyp) > 0,\
                            pcr.nominal(self.waterBodyTyp))    
        self.waterBodyTyp = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                   self.waterBodyTyp)

        # correcting lakes and reservoirs ids and outlets
        self.waterBodyIds = pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0,
                                                  self.waterBodyIds)               
        self.waterBodyOut = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0,
                                                  self.waterBodyOut)

        # reservoir maximum capacity (m3):
        self.resMaxCap = pcr.scalar(0.0)
        self.waterBodyCap = pcr.scalar(0.0)

        if self.useNetCDF:
            self.resMaxCap = 1000. * 1000. * \
                             vos.netcdf2PCRobjClone(self.ncFileInp,'resMaxCapInp', \
                             date_used, useDoy = 'yearly',\
                             cloneMapFileName = self.cloneMap)
        else:
            self.resMaxCap = 1000. * 1000. * vos.readPCRmapClone(\
                self.resMaxCapInp+str(year_used)+".map", \
                self.cloneMap,self.tmpDir,self.inputDir)

        self.resMaxCap = pcr.ifthen(self.resMaxCap > 0,\
                                    self.resMaxCap)
        self.resMaxCap = pcr.areaaverage(self.resMaxCap,\
                                         self.waterBodyIds)
                                         
        # water body capacity (m3): (lakes and reservoirs)
        self.waterBodyCap = pcr.cover(self.resMaxCap,0.0)               # Note: Most of lakes have capacities > 0.
        self.waterBodyCap = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                   self.waterBodyCap)
                                               
        # correcting water body types:                                  # Reservoirs that have zero capacities will be assumed as lakes.
        self.waterBodyTyp = \
                 pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                       self.waterBodyTyp) 
        self.waterBodyTyp = pcr.ifthenelse(self.waterBodyCap > 0.,\
                                           self.waterBodyTyp,\
                 pcr.ifthenelse(pcr.scalar(self.waterBodyTyp) == 2,\
                                           pcr.nominal(1),\
                                           self.waterBodyTyp)) 

        # final corrections:
        self.waterBodyTyp = pcr.ifthen(self.waterBodyArea > 0.,\
                                       self.waterBodyTyp)                     # make sure that all lakes and/or reservoirs have surface areas
        self.waterBodyTyp = \
                 pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                       self.waterBodyTyp)                     # make sure that only types 1 and 2 will be considered in lake/reservoir functions
        self.waterBodyIds = pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                            self.waterBodyIds)                                # make sure that all lakes and/or reservoirs have ids
        self.waterBodyOut = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.,\
                                                  self.waterBodyOut)          # make sure that all lakes and/or reservoirs have outlets
        
        
        # for a natural run (self.onlyNaturalWaterBodies == True) 
        # which uses only the year 1900, assume all reservoirs are lakes
        if self.onlyNaturalWaterBodies == True and date_used == self.dateForNaturalCondition:
            logger.info("Using only natural water bodies identified in the year 1900. All reservoirs in 1900 are assumed as lakes.")
            self.waterBodyTyp = \
             pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                        pcr.nominal(1))                         
        
        # check that all lakes and/or reservoirs have types, ids, surface areas and outlets:
        test = pcr.defined(self.waterBodyTyp) & pcr.defined(self.waterBodyArea) &\
               pcr.defined(self.waterBodyIds) & pcr.boolean(pcr.areamaximum(pcr.scalar(self.waterBodyOut), self.waterBodyIds))
        a,b,c = vos.getMinMaxMean(pcr.cover(pcr.scalar(test), 1.0) - pcr.scalar(1.0))
        threshold = 1e-3
        if abs(a) > threshold or abs(b) > threshold:
            logger.warning("Missing information in some lakes and/or reservoirs.")

        # at the beginning of simulation period (timeStepPCR = 1)
        # - we have to define/get the initial conditions 
        #
        if initial_condition_dictionary != None and currTimeStep.timeStepPCR == 1:
            self.getICs(initial_condition_dictionary)
        
        # For each new reservoir (introduced at the beginning of the year)
        # initiating storage, average inflow and outflow
        # PS: THIS IS NOT NEEDED FOR OFFLINE MODFLOW RUN! 
        #
        try:
            self.waterBodyStorage = pcr.cover(self.waterBodyStorage,0.0)
            self.avgInflow        = pcr.cover(self.avgInflow ,0.0)
            self.avgOutflow       = pcr.cover(self.avgOutflow,0.0)
            self.waterBodyStorage = pcr.ifthen(self.landmask, self.waterBodyStorage)
            self.avgInflow        = pcr.ifthen(self.landmask, self.avgInflow       )
            self.avgOutflow       = pcr.ifthen(self.landmask, self.avgOutflow      )
        except:
            # PS: FOR OFFLINE MODFLOW RUN!
            pass
        # TODO: Remove try and except    

        # cropping only in the landmask region:
        self.fracWat           = pcr.ifthen(self.landmask, self.fracWat         )
        self.waterBodyIds      = pcr.ifthen(self.landmask, self.waterBodyIds    ) 
        self.waterBodyOut      = pcr.ifthen(self.landmask, self.waterBodyOut    )
        self.waterBodyArea     = pcr.ifthen(self.landmask, self.waterBodyArea   )
        self.waterBodyTyp      = pcr.ifthen(self.landmask, self.waterBodyTyp    )  
        self.waterBodyCap      = pcr.ifthen(self.landmask, self.waterBodyCap    )

    def getICs(self,initial_condition):

        avgInflow  = initial_condition['avgLakeReservoirInflowShort']  
        avgOutflow = initial_condition['avgLakeReservoirOutflowLong'] 
        #
        if not isinstance(initial_condition['waterBodyStorage'],types.NoneType):
            # read directly 
            waterBodyStorage = initial_condition['waterBodyStorage']
        else:
            # calculate waterBodyStorage at cells where lakes and/or reservoirs are defined
            #
            storageAtLakeAndReservoirs = pcr.cover(\
             pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., initial_condition['channelStorage']), 0.0)
            #
            # - move only non negative values and use rounddown values
            storageAtLakeAndReservoirs = pcr.max(0.00, pcr.rounddown(storageAtLakeAndReservoirs))
            #
            # lake and reservoir storages = waterBodyStorage (m3) ; values are given for the entire lake / reservoir cells
            waterBodyStorage = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., \
                                          pcr.areatotal(storageAtLakeAndReservoirs,\
                                                        self.waterBodyIds))
        
        self.avgInflow        = pcr.cover(avgInflow , 0.0)              # unit: m3/s 
        self.avgOutflow       = pcr.cover(avgOutflow, 0.0)              # unit: m3/s
        self.waterBodyStorage = pcr.cover(waterBodyStorage, 0.0)        # unit: m3

        self.avgInflow        = pcr.ifthen(self.landmask, self.avgInflow)
        self.avgOutflow       = pcr.ifthen(self.landmask, self.avgOutflow)
        self.waterBodyStorage = pcr.ifthen(self.landmask, self.waterBodyStorage)                                            

    def update(self,newStorageAtLakeAndReservoirs,\
                              timestepsToAvgDischarge,\
                           maxTimestepsToAvgDischargeShort,\
                           maxTimestepsToAvgDischargeLong,\
                           currTimeStep,\
                           avgChannelDischarge,\
                           length_of_time_step = vos.secondsPerDay(),\
                           downstreamDemand = None):

        if self.debugWaterBalance:\
           preStorage = self.waterBodyStorage    # unit: m
     
        self.timestepsToAvgDischarge = timestepsToAvgDischarge          # TODO: include this one in "currTimeStep"     
        
        # obtain inflow (and update storage)
        self.moveFromChannelToWaterBody(\
         newStorageAtLakeAndReservoirs,\
             timestepsToAvgDischarge,\
             maxTimestepsToAvgDischargeShort,\
             length_of_time_step)
        
        # calculate outflow (and update storage)
        self.getWaterBodyOutflow(\
             maxTimestepsToAvgDischargeLong,\
             avgChannelDischarge,\
             length_of_time_step,\
             downstreamDemand)
        
        if self.debugWaterBalance:\
           vos.waterBalanceCheck([          pcr.cover(self.inflow/self.waterBodyArea,0.0)],\
                                 [pcr.cover(self.waterBodyOutflow/self.waterBodyArea,0.0)],\
                                 [           pcr.cover(preStorage/self.waterBodyArea,0.0)],\
                                 [pcr.cover(self.waterBodyStorage/self.waterBodyArea,0.0)],\
                                   'WaterBodyStorage (unit: m)',\
                                  True,\
                                  currTimeStep.fulldate,threshold=5e-3)

    def moveFromChannelToWaterBody(self,\
                                   newStorageAtLakeAndReservoirs,\
                                   timestepsToAvgDischarge,\
                                   maxTimestepsToAvgDischargeShort,\
                                   length_of_time_step = vos.secondsPerDay()):
        
        # new lake and/or reservoir storages (m3)
        newStorageAtLakeAndReservoirs = pcr.cover(\
                                        pcr.areatotal(newStorageAtLakeAndReservoirs,\
                                                      self.waterBodyIds),0.0)

        # incoming volume (m3)
        self.inflow = newStorageAtLakeAndReservoirs - self.waterBodyStorage
        
        # TODO: Please check whether this inflow term includes evaporation loss?
        
        # inflowInM3PerSec (m3/s)                                       
        self.inflowInM3PerSec = self.inflow / length_of_time_step

        # updating (short term) average inflow (m3/s) ; 
        # - needed to constrain lake outflow:
        #
        temp = pcr.max(1.0, pcr.min(maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge - 1.0 + length_of_time_step / vos.secondsPerDay()))
        deltaInflow = self.inflowInM3PerSec - self.avgInflow  
        R = deltaInflow * ( length_of_time_step / vos.secondsPerDay() ) / temp
        self.avgInflow = self.avgInflow + R                
        self.avgInflow = pcr.max(0.0, self.avgInflow)
        #
        # for the reference, see the "weighted incremental algorithm" in http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance                        

        # updating waterBodyStorage (m3)
        self.waterBodyStorage = newStorageAtLakeAndReservoirs

    def getWaterBodyOutflow(self,\
                            maxTimestepsToAvgDischargeLong,\
                            avgChannelDischarge,\
                            length_of_time_step = vos.secondsPerDay(),\
                            downstreamDemand = None):

        # outflow in volume from water bodies with lake type (m3): 
        lakeOutflow = self.getLakeOutflow(avgChannelDischarge,length_of_time_step)  
             
        # outflow in volume from water bodies with reservoir type (m3): 
        if isinstance(downstreamDemand, types.NoneType): downstreamDemand = pcr.scalar(0.0)
        reservoirOutflow = self.getReservoirOutflow(avgChannelDischarge,length_of_time_step,downstreamDemand)  

        # outgoing/release volume from lakes and/or reservoirs
        self.waterBodyOutflow = pcr.cover(reservoirOutflow, lakeOutflow)  
        
        # make sure that all water bodies have outflow:
        self.waterBodyOutflow = pcr.max(0.,
                                pcr.cover(self.waterBodyOutflow,0.0))

        # limit outflow to available storage
        factor = 0.25  # to avoid flip flop 
        self.waterBodyOutflow = pcr.min(self.waterBodyStorage * factor,\
                                        self.waterBodyOutflow)                    # unit: m3
        # use round values 
        self.waterBodyOutflow = pcr.rounddown(self.waterBodyOutflow/1.)*1.        # unit: m3
        
        # outflow rate in m3 per sec
        waterBodyOutflowInM3PerSec = self.waterBodyOutflow / length_of_time_step  # unit: m3/s

        # updating (long term) average outflow (m3/s) ; 
        # - needed to constrain/maintain reservoir outflow:
        #
        temp = pcr.max(1.0, pcr.min(maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge - 1.0 + length_of_time_step / vos.secondsPerDay()))
        deltaOutflow    = waterBodyOutflowInM3PerSec - self.avgOutflow
        R = deltaOutflow * ( length_of_time_step / vos.secondsPerDay() ) / temp
        self.avgOutflow = self.avgOutflow + R                
        self.avgOutflow = pcr.max(0.0, self.avgOutflow)
        #
        # for the reference, see the "weighted incremental algorithm" in http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance                        

        # update waterBodyStorage (after outflow):
        self.waterBodyStorage = self.waterBodyStorage -\
                                self.waterBodyOutflow
        self.waterBodyStorage = pcr.max(0.0, self.waterBodyStorage)                        

    def weirFormula(self,waterHeight,weirWidth): # output: m3/s
        sillElev  = pcr.scalar(0.0) 
        weirCoef  = pcr.scalar(1.0)
        weirFormula = \
         (1.7*weirCoef*pcr.max(0,waterHeight-sillElev)**1.5) *\
             weirWidth # m3/s
        return (weirFormula)

    def getLakeOutflow(self,\
        avgChannelDischarge,length_of_time_step = vos.secondsPerDay()):

        # waterHeight (m): temporary variable, a function of storage:
        minWaterHeight = 0.001 # (m) Rens used 0.001 m as the limit # this is to make sure there is always lake outflow,    
                                                                    # but it will be still limited by available self.waterBodyStorage 
        waterHeight = pcr.cover(
                      pcr.max(minWaterHeight, \
                      (self.waterBodyStorage - \
                      pcr.cover(self.waterBodyCap, 0.0))/\
                      self.waterBodyArea),0.)

        # weirWidth (m) : 
        # - estimated from avgOutflow (m3/s) using the bankfull discharge formula
        # 
        avgOutflow = self.avgOutflow
        avgOutflow = pcr.ifthenelse(\
                     avgOutflow > 0.,\
                     avgOutflow,
                     pcr.max(avgChannelDischarge,self.avgInflow,0.001))            # This is needed when new lakes/reservoirs introduced (its avgOutflow is still zero).
        avgOutflow = pcr.areamaximum(avgOutflow,self.waterBodyIds)             	
        #
        bankfullWidth = pcr.cover(\
                        pcr.scalar(4.8) * \
                        ((avgOutflow)**(0.5)),0.)
        weirWidthUsed = bankfullWidth
        weirWidthUsed = pcr.max(weirWidthUsed,self.minWeirWidth)                   # TODO: minWeirWidth based on the GRanD database
        weirWidthUsed = pcr.cover(
                        pcr.ifthen(\
                        pcr.scalar(self.waterBodyIds) > 0.,\
                        weirWidthUsed),0.0)

        # avgInflow <= lakeOutflow (weirFormula) <= waterBodyStorage
        lakeOutflowInM3PerSec = pcr.max(\
                                self.weirFormula(waterHeight,weirWidthUsed),\
                                self.avgInflow)                                    # unit: m3/s
        
        # estimate volume of water relased by lakes
        lakeOutflow = lakeOutflowInM3PerSec * length_of_time_step                  # unit: m3
        lakeOutflow = pcr.min(self.waterBodyStorage, lakeOutflow)
        #
        lakeOutflow = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., lakeOutflow)
        lakeOutflow = pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 1, lakeOutflow)
        
        # TODO: Consider endorheic lake/basin. No outflow for endorheic lake/basin!

        return (lakeOutflow) 

    def getReservoirOutflow(self,\
        avgChannelDischarge,length_of_time_step,downstreamDemand):

        # avgOutflow (m3/s)
        avgOutflow = self.avgOutflow
        # The following is needed when new lakes/reservoirs introduced (its avgOutflow is still zero).
        #~ # - alternative 1
        #~ avgOutflow = pcr.ifthenelse(\
                     #~ avgOutflow > 0.,\
                     #~ avgOutflow,
                     #~ pcr.max(avgChannelDischarge, self.avgInflow, 0.001))
        # - alternative 2
        avgOutflow = pcr.ifthenelse(\
                     avgOutflow > 0.,\
                     avgOutflow,
                     pcr.max(avgChannelDischarge, self.avgInflow))
        avgOutflow = pcr.ifthenelse(\
                     avgOutflow > 0.,\
                     avgOutflow, pcr.downstream(self.lddMap, avgOutflow))
        avgOutflow = pcr.areamaximum(avgOutflow,self.waterBodyIds)             	

        # calculate resvOutflow (m2/s) (based on reservoir storage and avgDischarge): 
        # - using reductionFactor in such a way that:
        #   - if relativeCapacity < minResvrFrac : release is terminated
        #   - if relativeCapacity > maxResvrFrac : longterm average
        reductionFactor = \
         pcr.cover(\
         pcr.min(1.,
         pcr.max(0., \
          self.waterBodyStorage - self.minResvrFrac*self.waterBodyCap)/\
             (self.maxResvrFrac - self.minResvrFrac)*self.waterBodyCap),0.0)
        #
        resvOutflow = reductionFactor * avgOutflow * length_of_time_step                      # unit: m3

        # maximum release <= average inflow (especially during dry condition)
        resvOutflow  = pcr.max(0, pcr.min(resvOutflow, self.avgInflow * length_of_time_step)) # unit: m3                                          

        # downstream demand (m3/s)
        # reduce demand if storage < lower limit
        reductionFactor  = vos.getValDivZero(downstreamDemand, self.minResvrFrac*self.waterBodyCap, vos.smallNumber)
        reductionFactor  = pcr.cover(reductionFactor, 0.0)
        downstreamDemand = pcr.min(
                           downstreamDemand,
                           downstreamDemand*reductionFactor)
        # resvOutflow > downstreamDemand
        resvOutflow  = pcr.max(resvOutflow, downstreamDemand * length_of_time_step)           # unit: m3       

        # floodOutflow: additional release if storage > upper limit
        ratioQBankfull = 2.3
        estmStorage  = pcr.max(0.,self.waterBodyStorage - resvOutflow)
        floodOutflow = \
           pcr.max(0.0, estmStorage - self.waterBodyCap) +\
           pcr.cover(\
           pcr.max(0.0, estmStorage - self.maxResvrFrac*\
                                      self.waterBodyCap)/\
              ((1.-self.maxResvrFrac)*self.waterBodyCap),0.0)*\
           pcr.max(0.0,ratioQBankfull*avgOutflow* vos.secondsPerDay()-\
                                      resvOutflow)
        floodOutflow = pcr.max(0.0,
                       pcr.min(floodOutflow,\
                       estmStorage - self.maxResvrFrac*\
                                     self.waterBodyCap*0.75)) # maximum limit of floodOutflow: bring the reservoir storages only to 3/4 of upper limit capacities
        
        # update resvOutflow after floodOutflow
        resvOutflow  = pcr.cover(resvOutflow , 0.0) +\
                       pcr.cover(floodOutflow, 0.0)                                            

        # maximum release if storage > upper limit : bring the reservoir storages only to 3/4 of upper limit capacities
        resvOutflow  = pcr.ifthenelse(self.waterBodyStorage > 
                       self.maxResvrFrac*self.waterBodyCap,\
                       pcr.min(resvOutflow,\
                       pcr.max(0,self.waterBodyStorage - \
                       self.maxResvrFrac*self.waterBodyCap*0.75)),
                       resvOutflow)                                            

        # if storage > upper limit : resvOutflow > avgInflow
        resvOutflow  = pcr.ifthenelse(self.waterBodyStorage > 
                       self.maxResvrFrac*self.waterBodyCap,\
                       pcr.max(0.0, resvOutflow, self.avgInflow),
                       resvOutflow)                                            
        
        # resvOutflow < waterBodyStorage
        resvOutflow = pcr.min(self.waterBodyStorage, resvOutflow)
        
        resvOutflow = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., resvOutflow)
        resvOutflow = pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 2, resvOutflow)
        return (resvOutflow) # unit: m3  
