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
import math
import types

from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
from ncConverter import *

import waterBodies

class Routing(object):
    
    #TODO: remove
    def getPseudoState(self):
        result = {}
        return result

    #TODO: remove
    def getVariables(self, names):
        result = {}
        return result

    def getState(self):
        result = {}
        
        result['timestepsToAvgDischarge']  = self.timestepsToAvgDischarge    # day 

        result['channelStorage']           = self.channelStorage             #  m3     ; channel storage, including lake and reservoir storage 
        result['readAvlChannelStorage']    = self.readAvlChannelStorage      #  m3     ; readily available channel storage that can be extracted to satisfy water demand
        result['avgDischargeLong']         = self.avgDischarge               #  m3/s   ;  long term average discharge
        result['m2tDischargeLong']         = self.m2tDischarge               # (m3/s)^2
        
        result['avgBaseflowLong']          = self.avgBaseflow                #  m3/s   ;  long term average baseflow
        result['riverbedExchange']         = self.riverbedExchange           #  m3/day : river bed infiltration (from surface water bdoies to groundwater)
        
        result['waterBodyStorage']            = self.waterBodyStorage        #  m3     ; storages of lakes and reservoirs            # values given are per water body id (not per cell)
        result['avgLakeReservoirOutflowLong'] = self.avgOutflow              #  m3/s   ; long term average lake & reservoir outflow  # values given are per water body id (not per cell)
        result['avgLakeReservoirInflowShort'] = self.avgInflow               #  m3/s   ; short term average lake & reservoir inflow  # values given are per water body id (not per cell)

        result['avgDischargeShort']        = self.avgDischargeShort          #  m3/s   ; short term average discharge 

        # This variable needed only for kinematic wave methods (i.e. kinematicWave and simplifiedKinematicWave)
        result['subDischarge']             = self.subDischarge               #  m3/s   ; sub-time step discharge (needed for kinematic wave methods/approaches)

        return result

    def __init__(self,iniItems,initialConditions,lddMap):
        object.__init__(self)

        self.lddMap = lddMap

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']

        # option to activate water balance check
        self.debugWaterBalance = True
        if iniItems.routingOptions['debugWaterBalance'] == "False":
            self.debugWaterBalance = False

        self.method = iniItems.routingOptions['routingMethod']

        # option to include lakes and reservoirs                    
        self.includeWaterBodies = True
        if 'includeWaterBodies' in iniItems.routingOptions.keys(): 
            if iniItems.routingOptions['includeWaterBodies'] == "False" or\
               iniItems.routingOptions['includeWaterBodies'] == "None":
                self.includeWaterBodies = False

        # local drainage direction:
        self.lddMap = vos.readPCRmapClone(iniItems.routingOptions['lddMap'],
                                              self.cloneMap,self.tmpDir,self.inputDir,True)
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        self.lddMap = pcr.lddrepair(self.lddMap)

        # landmask:
        if iniItems.globalOptions['landmask'] != "None":
           self.landmask = vos.readPCRmapClone(\
           iniItems.globalOptions['landmask'],
           self.cloneMap,self.tmpDir,self.inputDir)
        else:   	
           self.landmask = pcr.defined(self.lddMap)
        self.landmask = pcr.ifthen(pcr.defined(self.lddMap), self.landmask)
        self.landmask = pcr.cover(self.landmask, pcr.boolean(0))   

        # ldd mask 
        self.lddMap = pcr.lddmask(self.lddMap, self.landmask)

        # cell area (unit: m2)
        self.cellArea = vos.readPCRmapClone(\
                  iniItems.routingOptions['cellAreaMap'],
                  self.cloneMap,self.tmpDir,self.inputDir)

        # model resolution in arc-degree unit
        self.cellSizeInArcDeg = vos.getMapAttributes(self.cloneMap,"cellsize")  

        # maximum number of days (timesteps) to calculate long term average flow values (default: 5 years = 5 * 365 days = 1825)
        self.maxTimestepsToAvgDischargeLong  = 1825.

        # maximum number of days (timesteps) to calculate short term average values (default: 1 month = 1 * 30 days = 30)
        self.maxTimestepsToAvgDischargeShort = 30.                            

        routingParameters = ['gradient','manningsN']
        for var in routingParameters:
            input = iniItems.routingOptions[str(var)]
            vars(self)[var] = vos.readPCRmapClone(input,\
                             self.cloneMap,self.tmpDir,self.inputDir)

        # parameters needed to estimate channel dimensions/parameters   
        # - used in the method/function 'getRoutingParamAvgDischarge' 
        self.eta = 0.25
        self.nu  = 0.40
        self.tau = 8.00
        self.phi = 0.58

        # option to use minimum channel width (m)
        self.minChannelWidth = pcr.scalar(0.0)
        if "minimumChannelWidth" in iniItems.routingOptions.keys():
            if iniItems.routingOptions['minimumChannelWidth'] != "None":\
               self.minChannelWidth = pcr.cover(vos.readPCRmapClone(\
                                      iniItems.routingOptions['minimumChannelWidth'],
                                      self.cloneMap,self.tmpDir,self.inputDir), 0.0)
        
        # option to use constant/pre-defined channel width (m)
        self.predefinedChannelWidth = None
        if "constantChannelWidth" in iniItems.routingOptions.keys():
            if iniItems.routingOptions['constantChannelWidth'] != "None":\
               self.predefinedChannelWidth = pcr.cover(vos.readPCRmapClone(\
                                             iniItems.routingOptions['constantChannelWidth'],
                                             self.cloneMap,self.tmpDir,self.inputDir), 0.0)

        # option to use constant/pre-defined channel depth (m)
        self.predefinedChannelDepth = None
        if "constantChannelDepth" in iniItems.routingOptions.keys():
            if iniItems.routingOptions['constantChannelDepth'] != "None":\
               self.predefinedChannelDepth = pcr.cover(vos.readPCRmapClone(\
                                             iniItems.routingOptions['constantChannelDepth'],
                                             self.cloneMap,self.tmpDir,self.inputDir), 0.0)
        

        # an assumption for broad sheet flow in kinematic wave methods/approaches        
        self.beta = 0.6 
        
        # channelLength = approximation of channel length (unit: m)
        # This is approximated by cell diagonal. 
        cellSizeInArcMin    =  self.cellSizeInArcDeg*60.
        verticalSizeInMeter =  cellSizeInArcMin*1852.                            
        #
        self.cellLengthFD  = ((self.cellArea/verticalSizeInMeter)**(2)+\
                                            (verticalSizeInMeter)**(2))**(0.5) 
        self.channelLength = self.cellLengthFD
        # 
        # channel length (unit: m) 
        if "channelLength" in iniItems.routingOptions.keys():
            if iniItems.routingOptions['channelLength'] != "None":\
               self.channelLength = pcr.cover(
                                    vos.readPCRmapClone(\
                                    iniItems.routingOptions['channelLength'],
                                    self.cloneMap,self.tmpDir,self.inputDir), self.channelLength)
        
        # dist2celllength in m/arcDegree (needed in the accuTravelTime function): 
        nrCellsDownstream  = pcr.ldddist(self.lddMap,\
                                         self.lddMap == 5,1.)
        distanceDownstream = pcr.ldddist(self.lddMap,\
                                         self.lddMap == 5,\
                                         self.channelLength)
        channelLengthDownstream = \
                (self.channelLength + distanceDownstream)/\
                (nrCellsDownstream + 1)                 # unit: m
        self.dist2celllength  = channelLengthDownstream /\
                                  self.cellSizeInArcDeg # unit: m/arcDegree  

        # the channel gradient must be >= minGradient 
        minGradient   = 0.00005   # 0.000005
        self.gradient = pcr.max(minGradient,\
                        pcr.cover(self.gradient, minGradient))

        # initiate/create WaterBody class
        self.WaterBodies = waterBodies.WaterBodies(iniItems,self.landmask)

        # crop evaporation coefficient for surface water bodies
        self.no_zero_crop_water_coefficient = True
        if iniItems.routingOptions['cropCoefficientWaterNC'] == "None":
            self.no_zero_crop_water_coefficient = False
        else:
            self.fileCropKC = vos.getFullPath(\
                     iniItems.routingOptions['cropCoefficientWaterNC'],\
                     self.inputDir)

        # courantNumber criteria for numerical stability in kinematic wave methods/approaches
        self.courantNumber = 0.50

        # empirical values for minimum number of sub-time steps:
        design_flood_speed = 5.00 # m/s
        design_length_of_sub_time_step   = pcr.cellvalue(
                                           pcr.mapminimum(
                                           self.courantNumber * self.channelLength / design_flood_speed),1)[0]
        self.limit_num_of_sub_time_steps = np.ceil(
                                           vos.secondsPerDay() / design_length_of_sub_time_step)
        #
        # minimum number of sub-time steps: 24 ; hourly resolution as used in Van Beek et al. (2011) 
        self.limit_num_of_sub_time_steps = max(24.0, self.limit_num_of_sub_time_steps) 
                
        # minimum number of a sub time step based on the configuration/ini file:  
        if 'maxiumLengthOfSubTimeStep' in iniItems.routingOptions.keys():
            maxiumLengthOfSubTimeStep = float(iniItems.routingOptions['maxiumLengthOfSubTimeStep'])
            minimum_number_of_sub_time_step  = np.ceil(
                                               vos.secondsPerDay() / maxiumLengthOfSubTimeStep )
            self.limit_num_of_sub_time_steps = max(\
                                               minimum_number_of_sub_time_step, \
                                               self.limit_num_of_sub_time_steps)                                 
        # 
        self.limit_num_of_sub_time_steps = np.int(self.limit_num_of_sub_time_steps)
        
        # critical water height (m) used to select stable length of sub time step in kinematic wave methods/approaches
        self.critical_water_height = 0.25;	# used in Van Beek et al. (2011)

        # assumption for the minimum fracwat value used for calculating water height
        self.min_fracwat_for_water_height = 0.001 # dimensionless
        
        # assumption for minimum crop coefficient for surface water bodies 
        self.minCropWaterKC = 0.00
        if 'minCropWaterKC' in iniItems.routingOptions.keys():
            self.minCropWaterKC = float(iniItems.routingOptions['minCropWaterKC'])
        
        # get the initialConditions
        self.getICs(iniItems, initialConditions)
        
        # flood plain options:
        #################################################################################
        self.floodPlain = iniItems.routingOptions['dynamicFloodPlain'] == "True"
        if self.floodPlain:

            logger.info("Flood plain extents can vary during the simulation.")
            
            # get ManningsN for the flood plain areas
            input = iniItems.routingOptions['floodplainManningsN']
            self.floodplainManN = vos.readPCRmapClone(input,\
                                 self.cloneMap, self.tmpDir, self.inputDir)

            # reduction parameter of smoothing interval and error threshold
            self.reductionKK = 0.5
            if 'reductionKK' in iniItems.routingOptions.keys():
               self.reductionKK= float(iniItems.routingOptions['reductionKK'])
            self.criterionKK = 40.0
            if 'criterionKK' in iniItems.routingOptions.keys():
               self.criterionKK= float(iniItems.routingOptions['criterionKK'])

            # get relative elevation (above floodplain) profile per grid cell (including smoothing parameters)
            self.nrZLevels, self.areaFractions, self.relZ, self.floodVolume, self.kSlope, self.mInterval = \
                            self.getElevationProfile(iniItems)

            # get bankfull capacity (unit: m3)
            self.predefinedBankfullCapacity = None
            self.usingFixedBankfullCapacity = False
            if iniItems.routingOptions['bankfullCapacity'] != "None" :
            
                self.usingFixedBankfullCapacity = True
                self.predefinedBankfullCapacity = vos.readPCRmapClone(iniItems.routingOptions['bankfullCapacity'],\
                                                                          self.cloneMap, self.tmpDir, self.inputDir)
            else:  
                msg = "The bankfull channel storage capacity is NOT defined in the configuration file. "
            
                if isinstance(self.predefinedChannelWidth, types.NoneType) or\
                   isinstance(self.predefinedChannelDepth, types.NoneType):
            
                    msg += "The bankfull capacity is estimated from average discharge (5 year long term average)."

                else:

                    msg += "The bankfull capacity is estimated from the given channel depth and channel width."
                    self.usingFixedBankfullCapacity = True
                    self.predefinedBankfullCapacity = self.estimateBankfullCapacity(self.predefinedChannelWidth,\
                                                                                    self.predefinedChannelDepth)
            
                logger.info(msg)
            
            # covering the value
            self.predefinedBankfullCapacity = pcr.cover(self.predefinedBankfullCapacity, 0.0)    

        # zero fracwat assumption (used for debugging to the version 1)
        self.zeroFracWatAllAndAlways = False
        if iniItems.debug_to_version_one: self.zeroFracWatAllAndAlways = True
        
        # initiate old style reporting                                  # This is still very useful during the 'debugging' process. 
        self.initiate_old_style_routing_reporting(iniItems)

    def getICs(self,iniItems,iniConditions = None):

        if iniConditions == None:

            # read initial conditions from pcraster maps listed in the ini file (for the first time step of the model; when the model just starts)
            
            self.timestepsToAvgDischarge = vos.readPCRmapClone(iniItems.routingOptions['timestepsToAvgDischargeIni'] ,self.cloneMap,self.tmpDir,self.inputDir)  
            
            self.channelStorage          = vos.readPCRmapClone(iniItems.routingOptions['channelStorageIni']          ,self.cloneMap,self.tmpDir,self.inputDir)
            self.readAvlChannelStorage   = vos.readPCRmapClone(iniItems.routingOptions['readAvlChannelStorageIni']   ,self.cloneMap,self.tmpDir,self.inputDir) 
            self.avgDischarge            = vos.readPCRmapClone(iniItems.routingOptions['avgDischargeLongIni']        ,self.cloneMap,self.tmpDir,self.inputDir) 
            self.m2tDischarge            = vos.readPCRmapClone(iniItems.routingOptions['m2tDischargeLongIni']        ,self.cloneMap,self.tmpDir,self.inputDir) 
            self.avgBaseflow             = vos.readPCRmapClone(iniItems.routingOptions['avgBaseflowLongIni']         ,self.cloneMap,self.tmpDir,self.inputDir) 
            self.riverbedExchange        = vos.readPCRmapClone(iniItems.routingOptions['riverbedExchangeIni']        ,self.cloneMap,self.tmpDir,self.inputDir) 
            
            # New initial condition variable introduced in the version 2.0.2: avgDischargeShort 
            self.avgDischargeShort       = vos.readPCRmapClone(iniItems.routingOptions['avgDischargeShortIni']       ,self.cloneMap,self.tmpDir,self.inputDir) 

            # Initial conditions needed for kinematic wave methods
            self.subDischarge            = vos.readPCRmapClone(iniItems.routingOptions['subDischargeIni'],self.cloneMap,self.tmpDir,self.inputDir)  

        else:              

            # read initial conditions from the memory

            self.timestepsToAvgDischarge = iniConditions['routing']['timestepsToAvgDischarge']              
                                                                   
            self.channelStorage          = iniConditions['routing']['channelStorage']
            self.readAvlChannelStorage   = iniConditions['routing']['readAvlChannelStorage']
            self.avgDischarge            = iniConditions['routing']['avgDischargeLong']
            self.m2tDischarge            = iniConditions['routing']['m2tDischargeLong']
            self.avgBaseflow             = iniConditions['routing']['avgBaseflowLong']
            self.riverbedExchange        = iniConditions['routing']['riverbedExchange']
            self.avgDischargeShort       = iniConditions['routing']['avgDischargeShort']
            
            self.subDischarge            = iniConditions['routing']['subDischarge']
            
        self.channelStorage        = pcr.ifthen(self.landmask, pcr.cover(self.channelStorage,        0.0))
        self.readAvlChannelStorage = pcr.ifthen(self.landmask, pcr.cover(self.readAvlChannelStorage, 0.0))
        self.avgDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.avgDischarge,          0.0))
        self.m2tDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.m2tDischarge,          0.0))
        self.avgDischargeShort     = pcr.ifthen(self.landmask, pcr.cover(self.avgDischargeShort,     0.0))
        self.avgBaseflow           = pcr.ifthen(self.landmask, pcr.cover(self.avgBaseflow,           0.0))
        self.riverbedExchange      = pcr.ifthen(self.landmask, pcr.cover(self.riverbedExchange,      0.0))
        self.subDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.subDischarge ,         0.0))

        self.readAvlChannelStorage = pcr.min(self.readAvlChannelStorage, self.channelStorage)
        self.readAvlChannelStorage = pcr.max(self.readAvlChannelStorage, 0.0)

        # make sure that timestepsToAvgDischarge is consistent (or the same) for the entire map:
        try:
            self.timestepsToAvgDischarge = pcr.mapmaximum(self.timestepsToAvgDischarge)
        except:    
            pass # We have to use 'try/except' because 'pcr.mapmaximum' cannot handle scalar value

        # for netcdf reporting, we have to make sure that timestepsToAvgDischarge is spatial and scalar (especially while performing pcr2numpy operations)
        self.timestepsToAvgDischarge = pcr.spatial(pcr.scalar(self.timestepsToAvgDischarge))
        self.timestepsToAvgDischarge = pcr.ifthen(self.landmask, self.timestepsToAvgDischarge)

        # Initial conditions needed for water bodies:
        # - initial short term average inflow (m3/s) and 
        #           long term average outflow (m3/s)
        if iniConditions == None:
            # read initial conditions from pcraster maps listed in the ini file (for the first time step of the model; when the model just starts)
            self.avgInflow  = vos.readPCRmapClone(iniItems.routingOptions['avgLakeReservoirInflowShortIni'],self.cloneMap,self.tmpDir,self.inputDir)
            self.avgOutflow = vos.readPCRmapClone(iniItems.routingOptions['avgLakeReservoirOutflowLongIni'],self.cloneMap,self.tmpDir,self.inputDir)
            if not isinstance(iniItems.routingOptions['waterBodyStorageIni'],types.NoneType):
                self.waterBodyStorage = vos.readPCRmapClone(iniItems.routingOptions['waterBodyStorageIni'], self.cloneMap,self.tmpDir,self.inputDir)
                self.waterBodyStorage = pcr.ifthen(self.landmask, pcr.cover(self.waterBodyStorage, 0.0))
            else:
                self.waterBodyStorage = None
        else:
            # read initial conditions from the memory
            self.avgInflow        = iniConditions['routing']['avgLakeReservoirInflowShort']
            self.avgOutflow       = iniConditions['routing']['avgLakeReservoirOutflowLong']
            self.waterBodyStorage = iniConditions['routing']['waterBodyStorage']

        
        self.avgInflow  = pcr.ifthen(self.landmask, pcr.cover(self.avgInflow , 0.0))
        self.avgOutflow = pcr.ifthen(self.landmask, pcr.cover(self.avgOutflow, 0.0))
        if not isinstance(self.waterBodyStorage, types.NoneType):
            self.waterBodyStorage = pcr.ifthen(self.landmask, pcr.cover(self.waterBodyStorage, 0.0))


    def estimateBankfullDischarge(self, bankfullWidth, factor = 4.8):

        # bankfull discharge (unit: m3/s)
        # - from Lacey formula: P = B = 4.8 * (Qbf)**0.5

        bankfullDischarge = (bankfullWidth / factor ) ** (2.0)
        
        return bankfullDischarge

    def estimateBankfullDepth(self, bankfullDischarge):

        # bankfull depth (unit: m)
        # - from the Manning formula 
        # - assuming rectangular channel 
        
        bankfullDepth = self.manningsN * ((bankfullDischarge)**(0.50))
        bankfullDepth = bankfullDepth / (4.8 * ((self.gradient)**(0.50)))
        bankfullDepth = bankfullDepth**(3.0/5.0)

        return bankfullDepth

    def estimateBankfullCapacity(self, width, depth, minWidth = 5.0, minDepth = 1.0):

        # bankfull capacity (unit: m3)
        bankfullCapacity = pcr.max(minWidth, width) * \
                           pcr.max(minDepth, depth) * \
                           self.channelLength
        
        return bankfullCapacity                   

    def getElevationProfile(self, iniItems):

        # get the profile of relative elevation above the floodplain (per grid cell)

        # output: dictionaries kSlope, mInterval, relZ and floodVolume with the keys iCnt (index, dimensionless)
        # - nrZLevels                     : number of intervals/levels
        # - areaFractions (dimensionless) : percentage/fraction of flooded/innundated area
        # - relZ (m)                      : relative elevation above floodplain 
        # - floodVolume (m3)              : flood volume above the channel bankfull capacity 
        # - kSlope (dimensionless)        : slope used during the interpolation
        # - mInterval (m3)                : smoothing interval (used in the interpolation) 
        
        msg = 'Get the profile of relative elevation (relZ, unit: m) !!!'
        logger.info(msg)

        relativeElevationFileNC = None # TODO define relative elevation files in a netdf file.
        if relativeElevationFileNC != None: 
            pass # TODO: using a netcdf file 

        if relativeElevationFileNC == None: 

            relZFileName = vos.getFullPath(iniItems.routingOptions['relativeElevationFiles'],\
                                           iniItems.globalOptions['inputDir'])

            # a dictionary contains areaFractions (dimensionless): fractions of flooded/innundated areas  
            areaFractions = map(float, iniItems.routingOptions['relativeElevationLevels'].split(','))
            # number of levels/intervals
            nrZLevels     = len(areaFractions)
            # - TODO: Read areaFractions and nrZLevels automatically. 
            
        ########################################################################################################
        #
        # patch elevations: those that are part of sills are updated on the basis of the floodplain gradient
        # using local distances deltaX per increment upto z[N] and the sum over sills
        # - fill all lists (including smoothing interval and slopes)

        relZ = [0.] * nrZLevels
        for iCnt in range(0, nrZLevels):
            
            if relativeElevationFileNC == None: 
                inputName = relZFileName %(areaFractions[iCnt] * 100)
                relZ[iCnt] = vos.readPCRmapClone(inputName, 
                                                 self.cloneMap, self.tmpDir, self.inputDir)
            if relativeElevationFileNC != None: 
                pass # TODO: using a netcdf file

            # covering elevation values
            relZ[iCnt] = pcr.ifthen(self.landmask, pcr.cover(relZ[iCnt], 0.0))

            # make sure that relZ[iCnt] >= relZ[iCnt-1] (added by Edwin)
            if iCnt > 0: relZ[iCnt] = pcr.max(relZ[iCnt], relZ[iCnt-1])
        
        # - minimum slope of floodplain 
        #   being defined as the longest sill, 
        #   first used to retrieve longest cumulative distance 
        deltaX = [self.cellArea**0.5] * nrZLevels
        deltaX[0] = 0.0
        sumX = deltaX[:]
        minSlope = 0.0
        for iCnt in range(nrZLevels):
            if iCnt < nrZLevels-1:
                deltaX[iCnt] = (areaFractions[iCnt+1]**0.5 - areaFractions[iCnt]**0.5) * deltaX[iCnt]
            else:
                deltaX[iCnt] = (1.0 - areaFractions[iCnt-1]**0.5)*deltaX[iCnt]
            if iCnt > 0:
                sumX[iCnt] = pcr.ifthenelse(relZ[iCnt] == relZ[iCnt-1], sumX[iCnt-1] + deltaX[iCnt], 0.0)
                minSlope   = pcr.ifthenelse(relZ[iCnt] == relZ[iCnt-1], pcr.max( sumX[iCnt], minSlope), minSlope)
        # - the maximum value for the floodplain slope is channel gradient (flow velocity is slower in the floodplain)
        minSlope = pcr.min(self.gradient, 0.5* pcr.max(deltaX[1], minSlope)**-1.)
        
        # - add small increment to elevations to each sill (except in the case of lakes, #TODO: verify this)
        for iCnt in range(nrZLevels):
            relZ[iCnt] = relZ[iCnt] + sumX[iCnt] * pcr.ifthenelse(relZ[nrZLevels-1] > 0., minSlope, 0.0)
            # make sure that relZ[iCnt] >= relZ[iCnt-1] (added by Edwin)
            if iCnt > 0: relZ[iCnt] = pcr.max(relZ[iCnt], relZ[iCnt-1])
        #
        ########################################################################################################


        ########################################################################################################
        # - set slope and smoothing interval between dy= y(i+1)-y(i) and dx= x(i+1)-x(i)
        #   on the basis of volume
        #
        floodVolume = [0.] * (nrZLevels)      # volume (unit: m3)
        mInterval   = [0.] * (nrZLevels)      # smoothing interval (unit: m3)
        kSlope      = [0.] * (nrZLevels)      # slope (dimensionless) 
        #
        for iCnt in range(1, nrZLevels):
            floodVolume[iCnt] = floodVolume[iCnt-1] + \
                                0.5 * (areaFractions[iCnt] + areaFractions[iCnt-1]) * \
                                      (relZ[iCnt] - relZ[iCnt-1]) * self.cellArea
            kSlope[iCnt-1] = (areaFractions[iCnt] - areaFractions[iCnt-1])/\
                              pcr.max(0.001, floodVolume[iCnt] - floodVolume[iCnt-1])
        for iCnt in range(1, nrZLevels):
            if iCnt < (nrZLevels-1):
                mInterval[iCnt] = 0.5 * self.reductionKK * pcr.min(floodVolume[iCnt+1] - floodVolume[iCnt], \
                                                                   floodVolume[iCnt] - floodVolume[iCnt-1])
            else:
                mInterval[iCnt] = 0.5 * self.reductionKK *(floodVolume[iCnt] - floodVolume[iCnt-1])
        #
        ########################################################################################################
        
        return nrZLevels, areaFractions, relZ, floodVolume, kSlope, mInterval


    def getRoutingParamAvgDischarge(self, avgDischarge, dist2celllength = None):
        # obtain routing parameters based on average (longterm) discharge
        # output: channel dimensions and 
        #         characteristicDistance (for accuTravelTime input)
        
        yMean = self.eta * pow (avgDischarge, self.nu ) # avgDischarge in m3/s
        wMean = self.tau * pow (avgDischarge, self.phi)
 
        wMean =   pcr.max(wMean,0.01) # average flow width (m) - this could be used as an estimate of channel width (assuming rectangular channels)
        wMean = pcr.cover(wMean,0.01)
        yMean =   pcr.max(yMean,0.01) # average flow depth (m) - this should NOT be used as an estimate of channel depth
        yMean = pcr.cover(yMean,0.01)
        
        # option to use constant channel width (m)
        if not isinstance(self.predefinedChannelWidth,types.NoneType):\
           wMean = pcr.cover(self.predefinedChannelWidth, wMean)
        #
        # minimum channel width (m)
        wMean = pcr.max(self.minChannelWidth, wMean)

        return (yMean, wMean)

    def getCharacteristicDistance(self, yMean, wMean):

        # Manning's coefficient:
        usedManningsN = self.manningsN

        # corrected Manning's coefficient: 
        if self.floodPlain:

            # wetted perimeter
            flood_only_wetted_perimeter = self.floodDepth * (2.0) + \
                                          pcr.max(0.0, self.innundatedFraction*self.cellArea/self.channelLength - self.channelWidth)
            channel_only_wetted_perimeter = \
                        pcr.min(self.channelDepth, vos.getValDivZero(self.channelStorage, self.channelLength*self.channelWidth, 0.0)) * 2.0 + \
                        self.channelWidth
            # total channel wetted perimeter (unit: m)
            channel_wetted_perimeter = channel_only_wetted_perimeter + \
                                         flood_only_wetted_perimeter
            # minimum channel wetted perimeter = 10 cm
            channel_wetted_perimeter = pcr.max(0.1, channel_wetted_perimeter)                             

            usedManningsN = ((channel_only_wetted_perimeter/channel_wetted_perimeter) *      self.manningsN**(1.5) + \
                             (  flood_only_wetted_perimeter/channel_wetted_perimeter) * self.floodplainManN**(1.5))**(2./3.)
        
        # characteristicDistance (dimensionless)
        # - This will be used for accutraveltimeflux & accutraveltimestate
        # - discharge & storage = accutraveltimeflux & accutraveltimestate
        # - discharge = the total amount of material flowing through the cell (m3/s)
        # - storage   = the amount of material which is deposited in the cell (m3)
        #
        characteristicDistance = \
             ( (yMean *   wMean)/ \
               (wMean + 2*yMean) )**(2./3.) * \
              ((self.gradient)**(0.5))/ \
                usedManningsN * \
                vos.secondsPerDay()                                     # meter/day

        characteristicDistance = \
         pcr.max((self.cellSizeInArcDeg)*0.000000001,\
                 characteristicDistance/self.dist2celllength)           # arcDeg/day
        
        # charateristicDistance for each lake/reservoir:
        lakeReservoirCharacteristicDistance = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                              pcr.areaaverage(characteristicDistance, self.WaterBodies.waterBodyIds))
        #
        # - make sure that all outflow will be released outside lakes and reservoirs
        outlets = pcr.cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyOut) > 0, pcr.boolean(1)), pcr.boolean(0))
        distance_to_outlets = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                              pcr.ldddist(self.lddMap, outlets, pcr.scalar(1.0)))
        #~ lakeReservoirCharacteristicDistance = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                              #~ pcr.max(distance_to_outlets + pcr.downstreamdist(self.lddMap)*1.50, lakeReservoirCharacteristicDistance))
        lakeReservoirCharacteristicDistance = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                              pcr.max(distance_to_outlets + pcr.downstreamdist(self.lddMap)*2.50, lakeReservoirCharacteristicDistance))
        lakeReservoirCharacteristicDistance = pcr.areamaximum(lakeReservoirCharacteristicDistance, self.WaterBodies.waterBodyIds)
        #
        # TODO: calculate lakeReservoirCharacteristicDistance while obtaining lake & reservoir parameters
        
        characteristicDistance = pcr.cover(lakeReservoirCharacteristicDistance, characteristicDistance)                      
        
        # PS: In accutraveltime function: 
        #     If characteristicDistance (velocity) = 0 then:
        #     - accutraveltimestate will give zero 
        #     - accutraveltimeflux will be very high 
        
        # TODO: Consider to use downstreamdist function.
        
        # current solution: using the function "roundup" to ignore 
        #                   zero and very small values 
        characteristicDistance = \
         pcr.roundup(characteristicDistance*100.)/100.      # arcDeg/day
        
        # and set minimum value of characteristicDistance:
        characteristicDistance = pcr.cover(characteristicDistance, 0.1*self.cellSizeInArcDeg)
        characteristicDistance = pcr.max(0.100*self.cellSizeInArcDeg, characteristicDistance) # TODO: check what the minimum distance for accutraveltime function

        return characteristicDistance

    def accuTravelTime(self):
        		
        # accuTravelTime ROUTING OPERATIONS
        ##############n############################################################################################################

        # route only non negative channelStorage (otherwise stay):
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        self.channelStorage           = pcr.max(0.0, self.channelStorage)
        
        # also at least 1.0 m3 of water will stay - this is to minimize numerical errors due to float_32 pcraster implementations
        channelStorageThatWillNotMove += self.channelStorage - pcr.rounddown(self.channelStorage)
        self.channelStorage            = pcr.rounddown(self.channelStorage) 
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForAccuTravelTime = pcr.max(0.0, self.channelStorage)
        channelStorageForAccuTravelTime = pcr.cover(channelStorageForAccuTravelTime,0.0)       # TODO: check why do we have to use the "cover" operation?

        characteristicDistance = self.getCharacteristicDistance(self.yMean, self.wMean)

        # estimating channel discharge (m3/day)
        self.Q = pcr.accutraveltimeflux(self.lddMap,\
                                        channelStorageForAccuTravelTime,\
                                        pcr.max(0.0, characteristicDistance))
        self.Q = pcr.cover(self.Q, 0.0)
        # for very small velocity (i.e. characteristicDistanceForAccuTravelTime), discharge can be missing value.
        # see: http://sourceforge.net/p/pcraster/bugs-and-feature-requests/543/
        #      http://karssenberg.geo.uu.nl/tt/TravelTimeSpecification.htm
        #
        # and make sure that no negative discharge
        self.Q = pcr.max(0.0, self.Q)                                    # unit: m3/day        

        # updating channelStorage (after routing)
        self.channelStorage = pcr.accutraveltimestate(self.lddMap,\
                              channelStorageForAccuTravelTime,\
                              pcr.max(0.0, characteristicDistance)) # unit: m3

        # return channelStorageThatWillNotMove to channelStorage:
        self.channelStorage += channelStorageThatWillNotMove             # unit: m3

        # for non kinematic wave approaches, set subDishcarge Q in m3/s
        self.subDischarge = self.Q / vos.secondsPerDay()
        self.subDischarge = pcr.ifthen(self.landmask, self.subDischarge)
         

    def estimate_length_of_sub_time_step(self): 

        # estimate the length of sub-time step (unit: s):
        # - the shorter is the better
        # - estimated based on the initial or latest sub-time step discharge (unit: m3/s)
        # 
        length_of_sub_time_step = pcr.ifthenelse(self.subDischarge > 0.0, 
                                  self.water_height * self.dynamicFracWat * self.cellArea / \
                                  self.subDischarge, vos.secondsPerDay())
        # TODO: Check this logic with Rens!                           

        # determine the number of sub time steps (based on Rens van Beek's method)
        #
        critical_condition = (length_of_sub_time_step < vos.secondsPerDay())  & \
                             (self.water_height > self.critical_water_height) & \
                             (self.lddMap != pcr.ldd(5))
        #
        number_of_sub_time_steps = vos.secondsPerDay() /\
                                   pcr.cover(
                                   pcr.areaminimum(\
                                   pcr.ifthen(critical_condition, \
                                              length_of_sub_time_step),self.landmask),\
                                             vos.secondsPerDay()/self.limit_num_of_sub_time_steps)   
        number_of_sub_time_steps = 1.25 * number_of_sub_time_steps + 1
        number_of_sub_time_steps = pcr.roundup(number_of_sub_time_steps)
        #
        number_of_loops = max(1.0, pcr.cellvalue(pcr.mapmaximum(number_of_sub_time_steps),1)[1])     # minimum number of sub_time_steps = 1 
        number_of_loops = int(max(self.limit_num_of_sub_time_steps, number_of_loops))
        
        # actual length of sub-time step (s)
        length_of_sub_time_step = vos.secondsPerDay() / number_of_loops

        return (length_of_sub_time_step, number_of_loops)                               

    def simplifiedKinematicWave(self): 
        """
        The 'simplifiedKinematicWave':
        1. First, assume that all local fluxes has been added to 'channelStorage'. This is done outside of this function/method.
        2. Then, the 'channelStorage' is routed by using 'pcr.kinematic function' with 'lateral_inflow' = 0.0.
        """

        ##########################################################################################################################
        
        # TODO: REMOVE THIS METHOD AS THIS IS IRRELEVANT. 

        logger.info("Using the simplifiedKinematicWave method ! ")
        
        # route only non negative channelStorage (otherwise stay):
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # estimate of water height (m)
        # - needed to estimate the length of sub-time step and 
        #     also to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
        self.water_height = channelStorageForRouting /\
                           (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)

        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = self.estimate_length_of_sub_time_step()

        for i_loop in range(number_of_loops):
            
            msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
            logger.info(msg)
            
            # alpha parameter and initial discharge variable needed for kinematic wave
            alpha, dischargeInitial = \
                   self.calculate_alpha_and_initial_discharge_for_kinematic_wave(channelStorageForRouting, \
                                                                                 self.water_height, \
                                                                                 self.innundatedFraction, self.floodDepth)
            
            # at the lake/reservoir outlets, use the discharge of water bofy outflow
            waterBodyOutflowInM3PerSec = pcr.cover(
                                         pcr.ifthen(\
                                         self.WaterBodies.waterBodyOut,\
                                         self.WaterBodies.waterBodyOutflow), 0.0) / vos.secondsPerDay()
            waterBodyOutflowInM3PerSec = pcr.ifthen(\
                                         pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, \
                                         waterBodyOutflowInM3PerSec)
            dischargeInitial = pcr.cover(waterBodyOutflowInM3PerSec, dischargeInitial)                             

            # discharge (m3/s) based on kinematic wave approximation
            #~ logger.debug('start pcr.kinematic')
            self.subDischarge = pcr.kinematic(self.lddMap, dischargeInitial, 0.0, 
                                              alpha, self.beta, \
                                              1, length_of_sub_time_step, self.channelLength)
            self.subDischarge = pcr.cover(self.subDischarge, 0.0)
            self.subDischarge = pcr.max(0.0, pcr.cover(self.subDischarge, 0.0))
            #~ logger.debug('done')
            
            # make sure that we do not get negative channel storage
            self.subDischarge = pcr.min(self.subDischarge * length_of_sub_time_step, \
                                pcr.max(0.0, channelStorageForRouting + pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step)))/length_of_sub_time_step
            
            # update channelStorage (m3)
            storage_change_in_volume  = pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step) - \
                                                                  self.subDischarge * length_of_sub_time_step 
            channelStorageForRouting += storage_change_in_volume 
            #
            # route only non negative channelStorage (otherwise stay):
            channelStorageThatWillNotMove += pcr.ifthenelse(channelStorageForRouting < 0.0, channelStorageForRouting, 0.0)
            channelStorageForRouting       = pcr.max(0.000, channelStorageForRouting)
            
            # update flood fraction and flood depth
            self.inundatedFraction, self.floodDepth = self.returnInundationFractionAndFloodDepth(channelStorageForRouting)
            
            # update dynamicFracWat: fraction of surface water bodies (dimensionless) including lakes and reservoirs
            # - lake and reservoir surface water fraction
            self.dynamicFracWat = pcr.cover(\
                             pcr.min(1.0, self.WaterBodies.fracWat), 0.0)
            # - fraction of channel (including its excess above bankfull capacity) 
            self.dynamicFracWat += pcr.max(0.0, 1.0 - self.dynamicFracWat) * pcr.max(self.channelFraction, self.innundatedFraction)
            # - maximum value of dynamicFracWat is 1.0
            self.dynamicFracWat = pcr.ifthen(self.landmask, pcr.min(1.0, self.dynamicFracWat))

            # estimate water_height for the next loop
            # - needed to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
            self.water_height = channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)
            # TODO: Check whether the usage of dynamicFracWat provides any problems?

            # total discharge_volume (m3) until this present i_loop
            if i_loop == 0: discharge_volume = pcr.scalar(0.0)
            discharge_volume += self.subDischarge * length_of_sub_time_step

        # channel discharge (m3/day) = self.Q
        self.Q = discharge_volume

        # updating channelStorage (after routing)
        self.channelStorage = channelStorageForRouting

        # return channelStorageThatWillNotMove to channelStorage:
        self.channelStorage += channelStorageThatWillNotMove 

    def update(self,landSurface,groundwater,currTimeStep,meteo):

        logger.info("routing in progress")

        # waterBodies: 
        # - get parameters at the beginning of each year or simulation
        # - note that the following function should be called first, specifically because  
        #   we have to define initial conditions at the beginning of simulaution, 
        #
        if currTimeStep.timeStepPCR == 1:
            initial_conditions_for_water_bodies = self.getState()
            self.WaterBodies.getParameterFiles(currTimeStep,\
                                               self.cellArea,\
                                               self.lddMap,\
                                               initial_conditions_for_water_bodies)               # the last line is for the initial conditions of lakes/reservoirs

        if (currTimeStep.doy == 1) and (currTimeStep.timeStepPCR > 1):
            self.WaterBodies.getParameterFiles(currTimeStep,\
                                               self.cellArea,\
                                               self.lddMap)
        #
        if self.includeWaterBodies == False:
            self.WaterBodies.waterBodyIds = pcr.ifthen(self.landmask, pcr.nominal(-1))            # ignoring all lakes and reservoirs 
        
        # downstreamDemand (m3/s) for reservoirs 
        # - this one must be called before updating timestepsToAvgDischarge
        # - estimated based on environmental flow discharge 
        self.downstreamDemand = self.estimate_discharge_for_environmental_flow(self.channelStorage)
        
        # get routing/channel parameters/dimensions (based on avgDischarge)
        # and estimating water bodies fraction ; this is needed for calculating evaporation from water bodies
        self.yMean, self.wMean = \
                self.getRoutingParamAvgDischarge(self.avgDischarge)
         
        # channel width (unit: m)
        self.channelWidth = self.wMean
        
        # channel depth (unit: m)
        self.channelDepth = pcr.max(0.0, self.yMean)
        #
        # option to use constant channel depth (m)
        if not isinstance(self.predefinedChannelDepth, types.NoneType):\
           self.channelDepth = pcr.cover(self.predefinedChannelDepth, self.channelDepth)

        # channel bankfull capacity (unit: m3)
        if self.floodPlain: 
            if self.usingFixedBankfullCapacity:
                self.channelStorageCapacity = self.predefinedBankfullCapacity
            else:
                self.channelStorageCapacity = self.estimateBankfullCapacity(self.channelWidth, \
                                                                            self.channelDepth)
                        
        # fraction of channel (dimensionless)
        # - mininum inundated fraction
        self.channelFraction = pcr.max(0.0, pcr.min(1.0,\
                               self.channelWidth * self.channelLength / (self.cellArea)))
        
        # fraction of innundation due to flood (dimensionless) and flood/innundation depth (m)
        self.innundatedFraction, self.floodDepth = self.returnInundationFractionAndFloodDepth(self.channelStorage)
                                
        # fraction of surface water bodies (dimensionless) including lakes and reservoirs
        # - lake and reservoir surface water fraction
        self.dynamicFracWat = pcr.cover(\
                         pcr.min(1.0, self.WaterBodies.fracWat), 0.0)
        # - fraction of channel (including its excess above bankfull capacity) 
        self.dynamicFracWat += pcr.max(0.0, 1.0 - self.dynamicFracWat) * pcr.max(self.channelFraction, self.innundatedFraction)
        # - maximum value of dynamicFracWat is 1.0
        self.dynamicFracWat = pcr.ifthen(self.landmask, pcr.min(1.0, self.dynamicFracWat))
        
        # routing methods
        if self.method == "accuTravelTime" or self.method == "simplifiedKinematicWave": \
           self.simple_update(landSurface, groundwater, currTimeStep, meteo)
        #
        if self.method == "kinematicWave": \
           self.kinematic_wave_update(landSurface, groundwater, currTimeStep, meteo)                 
        # NOTE that this method require abstraction from fossil groundwater.
        
        # infiltration from surface water bodies (rivers/channels, as well as lakes and/or reservoirs) to groundwater bodies
        # - this exchange fluxes will be handed in the next time step
        # - in the future, this will be the interface between PCR-GLOBWB & MODFLOW (based on the difference between surface water levels & groundwater heads)
        #
        self.calculate_exchange_to_groundwater(groundwater, currTimeStep) 

        # volume water released in pits (losses: to the ocean / endorheic basin)
        self.outgoing_volume_at_pits = pcr.ifthen(self.landmask,
                                       pcr.cover(
                                       pcr.ifthen(self.lddMap == pcr.ldd(5), self.Q), 0.0))
        # TODO: accumulate water in endorheic basins that are considered as lakes/reservoirs
                
        # estimate volume of water that can be extracted for abstraction in the next time step
        self.readAvlChannelStorage = pcr.max(0.0, self.estimate_available_volume_for_abstraction(self.channelStorage))
        
        # old-style reporting                             
        self.old_style_routing_reporting(currTimeStep)                 # TODO: remove this one


    def calculate_potential_evaporation(self,landSurface,currTimeStep,meteo,definedDynamicFracWat = None):

        if self.no_zero_crop_water_coefficient == False: self.waterKC = 0.0
        
        # potential evaporation from water bodies
        # current principle: 
        # - if landSurface.actualET < waterKC * meteo.referencePotET * self.fracWat
        #   then, we add more evaporation
        #
        if (currTimeStep.day == 1) or (currTimeStep.timeStepPCR == 1) and self.no_zero_crop_water_coefficient:
            waterKC = vos.netcdf2PCRobjClone(self.fileCropKC,'kc', \
                               currTimeStep.fulldate, useDoy = 'month',\
                                       cloneMapFileName = self.cloneMap)
            self.waterKC = pcr.ifthen(self.landmask,\
                           pcr.cover(waterKC, 0.0))
            self.waterKC = pcr.max(self.minCropWaterKC, self.waterKC)
            
        # potential evaporation from water bodies (m/day)) - reduced by evaporation that has been calculated in the landSurface module
        waterBodyPotEvapOvesSurfaceWaterArea = pcr.ifthen(self.landmask, \
                                               pcr.max(0.0,\
                                               self.waterKC * meteo.referencePotET -\
                                               landSurface.actualET ))              # These values are NOT over the entire cell area.
        
        # potential evaporation from water bodies over the entire cell area (m/day)
        if definedDynamicFracWat == None: dynamicFracWat = self.dynamicFracWat
        waterBodyPotEvap = pcr.max(0.0, waterBodyPotEvapOvesSurfaceWaterArea * dynamicFracWat)
        return waterBodyPotEvap

    def calculate_evaporation(self,landSurface,groundwater,currTimeStep,meteo):

        # calculate potential evaporation from water bodies OVER THE ENTIRE CELL AREA (m/day) ; not only over surface water bodies
        self.waterBodyPotEvap = self.calculate_potential_evaporation(landSurface,currTimeStep,meteo)
        
        # evaporation volume from water bodies (m3)
        # - not limited to available channelStorage 
        volLocEvapWaterBody = self.waterBodyPotEvap * self.cellArea
        # - limited to available channelStorage
        volLocEvapWaterBody = pcr.min(\
                              pcr.max(0.0,self.channelStorage), volLocEvapWaterBody)

        # update channelStorage (m3) after evaporation from water bodies
        self.channelStorage = self.channelStorage -\
                              volLocEvapWaterBody
        self.local_input_to_surface_water -= volLocEvapWaterBody
        
        # evaporation (m) from water bodies                             
        self.waterBodyEvaporation = volLocEvapWaterBody / self.cellArea
        self.waterBodyEvaporation = pcr.ifthen(self.landmask, self.waterBodyEvaporation)

    def calculate_exchange_to_groundwater(self,groundwater,currTimeStep):

        if self.debugWaterBalance:\
           preStorage = self.channelStorage                            # unit: m3

        # riverbed infiltration (m3/day):
        #
        # - current implementation based on Inge's principle (later, will be based on groundater head (MODFLOW) and can be negative)
        # - happening only if 0.0 < baseflow < total_groundwater_abstraction
        # - total_groundwater_abstraction: from fossil and non fossil
        # - infiltration rate will be based on aquifer saturated conductivity
        # - limited to fracWat
        # - limited to available channelStorage
        # - this infiltration will be handed to groundwater in the next time step
        # - References: de Graaf et al. (2014); Wada et al. (2012); Wada et al. (2010)
        # - TODO: This concept should be IMPROVED. 
        #
        if groundwater.useMODFLOW:
        
            # river bed exchange have been calculated within the MODFLOW (via baseflow variable)
            
            self.riverbedExchange = pcr.scalar(0.0)
        
        else:
        
            riverbedConductivity  = groundwater.riverBedConductivity        # unit: m/day
            riverbedConductivity  = pcr.min(0.1, riverbedConductivity)      # maximum conductivity is 0.1 m/day (as recommended by Marc Bierkens: resistance = 1 day for 0.1 m river bed thickness)
            total_groundwater_abstraction = pcr.max(0.0, groundwater.nonFossilGroundwaterAbs + groundwater.fossilGroundwaterAbstr)   # unit: m
            self.riverbedExchange = pcr.max(0.0,\
                                    pcr.min(pcr.max(0.0,self.channelStorage),\
                                    pcr.ifthenelse(groundwater.baseflow > 0.0, \
                                    pcr.ifthenelse(total_groundwater_abstraction > groundwater.baseflow, \
                                    riverbedConductivity * self.dynamicFracWat * self.cellArea, \
                                    0.0), 0.0)))
            self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)                         
            factor = 0.25 # to avoid flip flop
            self.riverbedExchange = pcr.min(self.riverbedExchange, (1.0-factor)*pcr.max(0.0,self.channelStorage))                                                             
            self.riverbedExchange = pcr.ifthenelse(self.channelStorage < 0.0, 0.0, self.riverbedExchange)
            self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)
            self.riverbedExchange = pcr.ifthen(self.landmask, self.riverbedExchange)
            
        # update channelStorage (m3) after riverbedExchange (m3)
        self.channelStorage  -= self.riverbedExchange
        self.local_input_to_surface_water -= self.riverbedExchange

        if self.debugWaterBalance:\
           vos.waterBalanceCheck([pcr.scalar(0.0)],\
                                 [self.riverbedExchange/self.cellArea],\
                                 [           preStorage/self.cellArea],\
                                 [  self.channelStorage/self.cellArea],\
                                   'channelStorage after surface water infiltration',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-4)


    def simple_update(self,landSurface,groundwater,currTimeStep,meteo):

        # updating timesteps to calculate long and short term statistics values of avgDischarge, avgInflow, avgOutflow, etc.
        self.timestepsToAvgDischarge += 1.

        if self.debugWaterBalance:\
           preStorage = self.channelStorage                                                         # unit: m3

        # the following variable defines total local change (input) to surface water storage bodies # unit: m3 
        # - only local processes; therefore not considering any routing processes
        self.local_input_to_surface_water = pcr.scalar(0.0)          # initiate the variable, start from zero

        # runoff from landSurface cells (unit: m/day)
        self.runoff = landSurface.landSurfaceRunoff +\
                      groundwater.baseflow   
        
        # update channelStorage (unit: m3) after runoff
        self.channelStorage += self.runoff * self.cellArea
        self.local_input_to_surface_water += self.runoff * self.cellArea

        # update channelStorage (unit: m3) after actSurfaceWaterAbstraction 
        self.channelStorage -= landSurface.actSurfaceWaterAbstract * self.cellArea
        self.local_input_to_surface_water -= landSurface.actSurfaceWaterAbstract * self.cellArea

        # reporting channelStorage after surface water abstraction (unit: m3)
        self.channelStorageAfterAbstraction = pcr.ifthen(self.landmask, self.channelStorage) 

        # return flow from (m) non irrigation water demand
        # - calculated in the landSurface.py module 
        nonIrrReturnFlowVol   = landSurface.nonIrrReturnFlow*self.cellArea
        self.channelStorage  += nonIrrReturnFlowVol
        self.local_input_to_surface_water += nonIrrReturnFlowVol

        # water consumption for non irrigation water demand (m) - this water is removed from the system/water balance
        self.nonIrrWaterConsumption = pcr.max(0.0,\
                                      landSurface.nonIrrGrossDemand - \
                                      landSurface.nonIrrReturnFlow)
        
        # calculate evaporation from water bodies - this will return self.waterBodyEvaporation (unit: m)
        self.calculate_evaporation(landSurface, groundwater, currTimeStep, meteo)
        
        if self.debugWaterBalance:\
           vos.waterBalanceCheck([self.runoff,\
                                  landSurface.nonIrrReturnFlow],\
                                 [landSurface.actSurfaceWaterAbstract,self.waterBodyEvaporation],\
                                 [           preStorage/self.cellArea],\
                                 [  self.channelStorage/self.cellArea],\
                                   'channelStorage (unit: m) before lake/reservoir outflow',\
                                  True,\
                                  currTimeStep.fulldate,threshold=5e-3)
        
        # LAKE AND RESERVOIR OPERATIONS
        ##########################################################################################################################
        if self.debugWaterBalance: \
           preStorage = self.channelStorage                                  # unit: m3

        # at cells where lakes and/or reservoirs defined, move channelStorage to waterBodyStorage
        #
        storageAtLakeAndReservoirs = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                               self.channelStorage)
        storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs,0.0)
        #
        # - move only non negative values and use rounddown values
        storageAtLakeAndReservoirs = pcr.max(0.00, pcr.rounddown(storageAtLakeAndReservoirs))
        self.channelStorage -= storageAtLakeAndReservoirs                    # unit: m3

        # update waterBodyStorage (inflow, storage and outflow)
        self.WaterBodies.update(storageAtLakeAndReservoirs,\
                                self.timestepsToAvgDischarge,\
                                self.maxTimestepsToAvgDischargeShort,\
                                self.maxTimestepsToAvgDischargeLong,\
                                currTimeStep,\
                                self.avgDischarge,\
                                vos.secondsPerDay(),\
                                self.downstreamDemand)

        # waterBodyStorage (m3) after outflow:                               # values given are per water body id (not per cell)
        self.waterBodyStorage = pcr.ifthen(self.landmask,
                                self.WaterBodies.waterBodyStorage)
        
        # transfer outflow from lakes and/or reservoirs to channelStorages
        waterBodyOutflow = pcr.cover(\
                           pcr.ifthen(\
                           self.WaterBodies.waterBodyOut,
                           self.WaterBodies.waterBodyOutflow), 0.0)          # unit: m3/day
        
        if self.method == "accuTravelTime":
            # distribute outflow to water body storage
            # - this is to avoid 'waterBodyOutflow' skipping cells 
            # - this is done by distributing waterBodyOutflow within lake/reservoir cells 
            #
            waterBodyOutflow = pcr.areaaverage(waterBodyOutflow, self.WaterBodies.waterBodyIds)
            waterBodyOutflow = pcr.ifthen(\
                               pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                               waterBodyOutflow)                                 
        self.waterBodyOutflow = pcr.cover(waterBodyOutflow, 0.0)             # unit: m3/day

        # update channelStorage (m3) after waterBodyOutflow (m3)
        self.channelStorage += self.waterBodyOutflow
        # Note that local_input_to_surface_water does not include waterBodyOutflow
        
        if self.debugWaterBalance:\
           vos.waterBalanceCheck([self.waterBodyOutflow/self.cellArea],\
                                 [storageAtLakeAndReservoirs/self.cellArea],\
                                 [           preStorage/self.cellArea],\
                                 [  self.channelStorage/self.cellArea],\
                                   'channelStorage (unit: m) after lake reservoir/outflow fluxes (errors here are most likely due to pcraster implementation in float_32)',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-3)

        # ROUTING OPERATION:
        ##########################################################################################################################
        # - this will return new self.channelStorage (but still without waterBodyStorage)
        # - also, this will return self.Q which is channel discharge in m3/day
        #
        if self.method == "accuTravelTime":          self.accuTravelTime() 		
        if self.method == "simplifiedKinematicWave": self.simplifiedKinematicWave() 		
        #
        #
        # channel discharge (m3/s): for current time step
        #
        self.discharge = self.Q / vos.secondsPerDay()
        self.discharge = pcr.max(0., self.discharge)                   # reported channel discharge cannot be negative
        self.discharge = pcr.ifthen(self.landmask, self.discharge)
        #
        self.disChanWaterBody = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                                pcr.areamaximum(self.discharge,self.WaterBodies.waterBodyIds))
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)
        #
        self.disChanWaterBody = pcr.max(0.,self.disChanWaterBody)      # reported channel discharge cannot be negative
        #
        #
        ##########################################################################################################################

        # calculate the statistics of long and short term flow values
        self.calculate_statistics(groundwater)
        
        # return waterBodyStorage to channelStorage  
        self.channelStorage = self.return_water_body_storage_to_channel(self.channelStorage)

    def calculate_alpha_and_initial_discharge_for_kinematic_wave(self, channelStorage, water_height, innundatedFraction, floodDepth): 

        # calculate alpha (dimensionless), which is the roughness coefficient 
        # - for kinewatic wave (see: http://pcraster.geo.uu.nl/pcraster/4.0.0/doc/manual/op_kinematic.html)
        # - based on wetted area (m2) and wetted perimeter (m), as well as self.beta (dimensionless)
        # - assuming rectangular channel
        # - flood innundated areas with 

        # channel wetted area (m2)
        # - the minimum wetted area is: water height x channel width (Edwin introduce this) 
        # - channel wetted area is mainly based on channelStorage and channelLength (Rens's approach)
        channel_wetted_area = water_height * self.channelWidth
        channel_wetted_area = pcr.max(channel_wetted_area,\
                                      channelStorage / self.channelLength)

        # wetted perimeter
        flood_only_wetted_perimeter = floodDepth * (2.0) + \
                                      pcr.max(0.0, innundatedFraction*self.cellArea/self.channelLength - self.channelWidth)
        channel_only_wetted_perimeter = \
                    pcr.min(self.channelDepth, vos.getValDivZero(channelStorage, self.channelLength*self.channelWidth, 0.0)) * 2.0 + \
                    self.channelWidth
        # total channel wetted perimeter (unit: m)
        channel_wetted_perimeter = channel_only_wetted_perimeter + \
                                     flood_only_wetted_perimeter
        # minimum channel wetted perimeter = 10 cm
        channel_wetted_perimeter = pcr.max(0.1, channel_wetted_perimeter)                             
            
        # corrected Manning's coefficient: 
        if self.floodPlain:
            usedManningsN = ((channel_only_wetted_perimeter/channel_wetted_perimeter) *      self.manningsN**(1.5) + \
                             (  flood_only_wetted_perimeter/channel_wetted_perimeter) * self.floodplainManN**(1.5))**(2./3.)
        else:
            usedManningsN = self.manningsN
        
        # alpha (dimensionless) and initial estimate of channel discharge (m3/s)
        #
        alpha = (usedManningsN*channel_wetted_perimeter**(2./3.)*self.gradient**(-0.5))**self.beta  # dimensionless
        dischargeInitial = pcr.ifthenelse(alpha > 0.0,\
                                         (channel_wetted_area / alpha)**(1.0/self.beta), 0.0)       # unit: m3
        
        return (alpha, dischargeInitial)    

    def calculate_alpha_and_initial_discharge_for_kinematic_wave_OLD(self, channelStorage = None): 

        # calculate alpha (dimensionless), which is the roughness coefficient 
        # - for kinewatic wave (see: http://pcraster.geo.uu.nl/pcraster/4.0.0/doc/manual/op_kinematic.html)
        # - based on wetted area (m2) and wetted perimeter (m), as well as self.beta (dimensionless)
        # - assuming rectangular channel

        # Manning's coefficient:
        usedManningsN = self.manningsN
        
        # channel wetted area (m2)
        # - alternative 1: based on channelStorage and channelLength (Rens's approach)
        channel_wetted_area = self.water_height * self.channelWidth
        # - alternative 2: the minimum wetted are is: water height x channel width (Edwin introduce this) 
        channel_wetted_area = pcr.max(channel_wetted_area,\
                                      channelStorage / self.channelLength)                          # unit: m2

        # channel wetted perimeter (m)
        channel_wetted_perimeter = 2.0*channel_wetted_area/self.channelWidth + self.channelWidth    # unit: m  

        # flood fraction (dimensionless) and flood depth (unit: m)
        floodFraction = pcr.scalar(0.0)
        floodDepth    = pcr.scalar(0.0)
        
        if self.floodPlain:
            
            # return flood fraction and flood/innundation depth above the flood plain
            floodFraction, floodDepth = self.returnInundationFractionAndFloodDepth(channelStorage)
            
            # wetted perimeter
            flood_only_wetted_perimeter   = pcr.max(0.0, floodFraction*self.cellArea/self.channelLength - self.channelWidth) + \
                                                         floodDepth * (2.0)
            channel_only_wetted_perimeter = \
                    self.channelWidth + \
                    2.0 * pcr.min(self.channelDepth, channelStorage/(self.channelLength*self.channelWidth))
            #
            channel_wetted_perimeter = channel_only_wetted_perimeter + flood_only_wetted_perimeter   # unit: m
            
            # corrected Manning's coefficient: 
            usedManningsN = ((channel_only_wetted_perimeter/channel_wetted_perimeter) *      self.manningsN**(1.5) + \
                             (  flood_only_wetted_perimeter/channel_wetted_perimeter) * self.floodplainManN**(1.5))**(2./3.)
        
        # alpha (dimensionless) and estimate of channel discharge (m3/s)
        #
        alpha = (usedManningsN*channel_wetted_perimeter**(2./3.)*self.gradient**(-0.5))**self.beta  # dimensionless
        dischargeInitial = pcr.ifthenelse(alpha > 0.0,\
                                         (channel_wetted_area / alpha)**(1.0/self.beta), 0.0)       # unit: m3
        
        return (alpha, dischargeInitial, floodFraction, floodDepth)    

    def integralLogisticFunction(self,x):
        
        # returns a tupple of two values holding the integral of the logistic functions of (x) and (-x)
       
        logInt=pcr.ln(pcr.exp(-x)+1)

        return logInt,x+logInt
        
    def returnInundationFractionAndFloodDepth(self, channelStorage):
        
        # flood/innundation depth above the flood plain (unit: m)
        floodDepth = 0.0
        
        # channel and flood innundated fraction (dimensionless, the minimum value is channelFraction)
        inundatedFraction = self.channelFraction
        
        if self.floodPlain:

            msg = 'Calculate channel inundated fraction and flood inundation depth above the floodplain.'
            logger.info(msg)
            
            # given the flood channel volume: channelStorage
            # - return the flooded fraction and the associated water height
            # - using a logistic smoother near intersections (K&K, 2007)
        
            # flood/innundation/excess volume (excess above the bankfull capacity, unit: m3)
            excessVolume = pcr.max(0.0, channelStorage - self.channelStorageCapacity)
            
            # find the match on the basis of the shortest distance 
            # to the available intersections or steps
            #
            deltaXMin = self.floodVolume[self.nrZLevels-1]
            y_i  =  pcr.scalar(1.0)                                          
            k    = [pcr.scalar(0.0)]*2
            mInt =  pcr.scalar(0.0)
            for iCnt in range(self.nrZLevels-1,0,-1):
                # - find x_i for current volume and update match if applicable
                #   also update slope and intercept
                deltaX    = excessVolume - self.floodVolume[iCnt]
                mask      = pcr.abs(deltaX) < pcr.abs(deltaXMin)
                deltaXMin = pcr.ifthenelse(mask, deltaX, deltaXMin)
                y_i  = pcr.ifthenelse(mask, self.areaFractions[iCnt], y_i)
                k[0] = pcr.ifthenelse(mask, self.kSlope[iCnt-1], k[0])
                k[1] = pcr.ifthenelse(mask, self.kSlope[iCnt], k[1])
                mInt = pcr.ifthenelse(mask, self.mInterval[iCnt], mInt)
        
            # all values returned, process data: calculate scaled deltaX and smoothed function
            # on the basis of the integrated logistic functions PHI(x) and 1-PHI(x)
            #
            deltaX = deltaXMin
            deltaXScaled = pcr.ifthenelse(deltaX < 0.,pcr.scalar(-1.),1.)*\
                           pcr.min(self.criterionKK,pcr.abs(deltaX/pcr.max(1.,mInt)))
            logInt = self.integralLogisticFunction(deltaXScaled)
        
            # compute fractional inundated/flooded area
            inundatedFraction = pcr.ifthenelse(excessVolume > 0.0,\
                                             pcr.ifthenelse(pcr.abs(deltaXScaled) < self.criterionKK,\
                                                            y_i-k[0]*mInt*logInt[0]+k[1]*mInt*logInt[1],\
                                                            y_i+pcr.ifthenelse(deltaX < 0.,k[0],k[1])*deltaX), 0.0)
            # - minimum value is channelFraction
            inundatedFraction = pcr.max(self.channelFraction, inundatedFraction)
            # - maximum value is 1.0
            inundatedFraction = pcr.max(0.,pcr.min(1.0, inundatedFraction))                  # dimensionless
            
            # calculate flooded/inundated depth (unit: m) above the floodplain 
            #_- it will be zero if excessVolume == 0 
            floodDepth  = pcr.ifthenelse(inundatedFraction > 0., \
                          excessVolume/(pcr.max(self.min_fracwat_for_water_height, inundatedFraction)*self.cellArea),0.)  # unit: m
            # - maximum flood depth
            max_flood_depth = 25.0
            floodDepth  = pcr.max(0.0, pcr.min(max_flood_depth, floodDepth))
            
        return inundatedFraction, floodDepth

    def return_water_body_storage_to_channel(self, channelStorage):

        # return waterBodyStorage to channelStorage  
        #
        waterBodyStorageTotal = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areaaverage(\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyStorage),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)) + \
         pcr.areatotal(pcr.cover(\
         pcr.ifthen(self.landmask,channelStorage), 0.0),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)))
        waterBodyStoragePerCell = \
         waterBodyStorageTotal*\
                       self.cellArea/\
         pcr.areatotal(pcr.cover(\
         self.cellArea, 0.0),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))
        waterBodyStoragePerCell = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         waterBodyStoragePerCell)                                                      # unit: m3
        #
        channelStorage = pcr.cover(waterBodyStoragePerCell, channelStorage)            # unit: m3
        channelStorage = pcr.ifthen(self.landmask, channelStorage)
        return channelStorage

    def kinematic_wave_update(self, landSurface, groundwater, currTimeStep, meteo): 

        logger.info("Using the fully kinematic wave method! ")

        # updating timesteps to calculate long and short term statistics 
        # values of avgDischarge, avgInflow, avgOutflow, etc.
        self.timestepsToAvgDischarge += 1.

        # the following variable defines total local change (input) to surface water storage bodies # unit: m3 
        # - only local processes; therefore not considering any routing processes
        self.local_input_to_surface_water = pcr.scalar(0.0)             # initiate the variable, start from zero

        # For simplification, surface water abstraction 
        #                     is done outside the sub daily time steps.
        #
        # update channelStorage (unit: m3) after actSurfaceWaterAbstraction 
        self.channelStorage -= landSurface.actSurfaceWaterAbstract * self.cellArea
        self.local_input_to_surface_water -= landSurface.actSurfaceWaterAbstract * self.cellArea
        #
        # reporting channelStorage after surface water abstraction (unit: m3)
        self.channelStorageAfterAbstraction = pcr.ifthen(self.landmask, self.channelStorage) 

        
        # return flow from (m) non irrigation water demand
        # - calculated in the landSurface.py module: landSurface.nonIrrReturnFlow

        # water consumption for non irrigation water demand (m) - this water is removed from the system/water balance
        self.nonIrrWaterConsumption = pcr.max(0.0,\
                                      landSurface.nonIrrGrossDemand - \
                                      landSurface.nonIrrReturnFlow)

        # runoff from landSurface cells (unit: m/day)                   
        self.runoff = landSurface.landSurfaceRunoff +\
                      groundwater.baseflow                              # values are over the entire cell area
        

        # LAKE AND RESERVOIR OPERATIONS
        ##########################################################################################################################
        #
        # at cells where lakes and/or reservoirs defined, move channelStorage to waterBodyStorage
        storageAtLakeAndReservoirs = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                               self.channelStorage)
        storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs,0.0)
        #
        # - move only non negative values and use rounddown values
        storageAtLakeAndReservoirs = pcr.max(0.00, pcr.rounddown(storageAtLakeAndReservoirs))
        self.channelStorage -= storageAtLakeAndReservoirs                    # unit: m3
        #
        # update waterBodyStorage (inflow, storage and outflow)
        self.WaterBodies.update(storageAtLakeAndReservoirs,\
                                self.timestepsToAvgDischarge,\
                                self.maxTimestepsToAvgDischargeShort,\
                                self.maxTimestepsToAvgDischargeLong,\
                                currTimeStep,\
                                self.avgDischarge,\
                                vos.secondsPerDay(),\
                                self.downstreamDemand)
        # - waterBodyStorage (m3) after outflow:                             # values given are per water body id (not per cell)
        self.waterBodyStorage = pcr.ifthen(self.landmask,
                                self.WaterBodies.waterBodyStorage)
        # outflow from lakes and/or reservoirs at lake/reservoir outlet cells
        waterBodyOutflow = pcr.cover(\
                           pcr.ifthen(\
                           self.WaterBodies.waterBodyOut,
                           self.WaterBodies.waterBodyOutflow), 0.0)          # unit: m3/day

        # route only non negative channelStorage (otherwise stay):
        # - note that, the following includes storages in 
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # estimate of water height (m)
        # - needed to estimate the length of sub-time step and 
        #     also to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
        self.water_height = channelStorageForRouting /\
                           (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)

        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = self.estimate_length_of_sub_time_step()

        #######################################################################################################################
        for i_loop in range(number_of_loops):
            
            msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
            logger.info(msg)
            
            # initiating accumulated values:
            if i_loop == 0:
                acc_local_input_to_surface_water    = pcr.scalar(0.0)   # unit: m3                            
                acc_water_body_evaporation_volume   = pcr.scalar(0.0)   # unit: m3
                acc_discharge_volume                = pcr.scalar(0.0)   # unit: m3
                

            if self.debugWaterBalance:\
                preStorage = pcr.ifthen(self.landmask,\
                             channelStorageForRouting)
                
            # update channelStorageForRouting after runoff and return flow from non irrigation demand
            channelStorageForRouting          += (self.runoff + landSurface.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3
            acc_local_input_to_surface_water  += (self.runoff + landSurface.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3

            # potential evaporation within the sub-time step ; unit: m, values are over the entire cell area 
            #
            water_body_potential_evaporation   = self.calculate_potential_evaporation(landSurface,currTimeStep,meteo) *\
                                                 length_of_sub_time_step/vos.secondsPerDay()
            # - accumulating potential evaporation
            if i_loop == 0:
                self.waterBodyPotEvap = pcr.scalar(0.0)
            self.waterBodyPotEvap += water_body_potential_evaporation                                 
            
            # update channelStorageForRouting after evaporation
            water_body_evaporation_volume      = pcr.min(pcr.max(channelStorageForRouting, 0.0), \
                                                 water_body_potential_evaporation * self.cellArea * length_of_sub_time_step/vos.secondsPerDay())
            channelStorageForRouting          -= water_body_evaporation_volume
            acc_local_input_to_surface_water  -= water_body_evaporation_volume
            acc_water_body_evaporation_volume += water_body_evaporation_volume
            
            if self.debugWaterBalance:\
                vos.waterBalanceCheck([self.runoff * length_of_sub_time_step/vos.secondsPerDay(), \
                                       landSurface.nonIrrReturnFlow * length_of_sub_time_step/vos.secondsPerDay()],\
                                      [water_body_evaporation_volume/self.cellArea],\
                                      [preStorage/self.cellArea],\
                                      [channelStorageForRouting/self.cellArea],\
                                       'channelStorageForRouting',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-5)

            # alpha parameter and initial discharge variable needed for kinematic wave
            alpha, dischargeInitial = \
                   self.calculate_alpha_and_initial_discharge_for_kinematic_wave(channelStorageForRouting, \
                                                                                 self.water_height, \
                                                                                 self.innundatedFraction, self.floodDepth)
            
            # discharge (m3/s) based on kinematic wave approximation
            #~ logger.debug('start pcr.kinematic')
            self.subDischarge = pcr.kinematic(self.lddMap, dischargeInitial, 0.0, 
                                              alpha, self.beta, \
                                              1, length_of_sub_time_step, self.channelLength)
            self.subDischarge = pcr.max(0.0, pcr.cover(self.subDischarge, 0.0))
            #~ logger.debug('done')
            
            # the kinematic wave is implemented only for channels (not to lakes and reservoirs)
            # - set discharge to zero for lakes and reservoirs:
            self.subDischarge = pcr.cover(\
                                pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., pcr.scalar(0.0)), self.subDischarge)
            
            # make sure that we do not get negative channel storage
            self.subDischarge = pcr.min(self.subDischarge * length_of_sub_time_step, \
                                pcr.max(0.0, channelStorageForRouting + pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step)))/length_of_sub_time_step

            # update channelStorage (m3)
            storage_change_in_volume  = pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step) - self.subDischarge * length_of_sub_time_step 
            channelStorageForRouting += storage_change_in_volume 
            
            if self.debugWaterBalance:\
                vos.waterBalanceCheck([self.runoff * length_of_sub_time_step/vos.secondsPerDay(), \
                                       landSurface.nonIrrReturnFlow * length_of_sub_time_step/vos.secondsPerDay(),\
                                       storage_change_in_volume/self.cellArea],\
                                      [water_body_evaporation_volume/self.cellArea],\
                                      [preStorage/self.cellArea - storageAtLakeAndReservoirs/self.cellArea],\
                                      [channelStorageForRouting/self.cellArea],\
                                       'channelStorageForRouting (after routing, without lakes/reservoirs)',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-4)

            # transfer outflow from lakes and/or reservoirs
            # - update channelStorage (m3) after waterBodyOutflow (m3)
            channelStorageForRouting += pcr.upstream(self.lddMap, waterBodyOutflow) * length_of_sub_time_step/vos.secondsPerDay()
            # Note that local_input_to_surface_water does not include waterBodyOutflow
           # - at the lake/reservoir outlets, add the discharge of water body outflow
            waterBodyOutflowInM3PerSec = pcr.ifthen(\
                                         self.WaterBodies.waterBodyOut,
                                         self.WaterBodies.waterBodyOutflow) / length_of_sub_time_step
            self.subDischarge = self.subDischarge + \
                                pcr.cover(waterBodyOutflowInM3PerSec, 0.0)                             
            self.subDischarge = pcr.ifthen(self.landmask, self.subDischarge)


            # total discharge_volume (m3) until this present i_loop
            acc_discharge_volume += self.subDischarge * length_of_sub_time_step

            # route only non negative channelStorage (otherwise stay):
            channelStorageThatWillNotMove += pcr.ifthenelse(channelStorageForRouting < 0.0, channelStorageForRouting, 0.0)
            channelStorageForRouting       = pcr.max(0.000, channelStorageForRouting)

            # update flood fraction and flood depth
            self.inundatedFraction, self.floodDepth = self.returnInundationFractionAndFloodDepth(channelStorageForRouting)
            
            # update dynamicFracWat: fraction of surface water bodies (dimensionless) including lakes and reservoirs
            # - lake and reservoir surface water fraction
            self.dynamicFracWat = pcr.cover(\
                             pcr.min(1.0, self.WaterBodies.fracWat), 0.0)
            # - fraction of channel (including its excess above bankfull capacity) 
            self.dynamicFracWat += pcr.max(0.0, 1.0 - self.dynamicFracWat) * pcr.max(self.channelFraction, self.innundatedFraction)
            # - maximum value of dynamicFracWat is 1.0
            self.dynamicFracWat = pcr.ifthen(self.landmask, pcr.min(1.0, self.dynamicFracWat))

            # estimate water_height for the next loop
            # - needed to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
            self.water_height = channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)
            # TODO: Check whether the usage of dynamicFracWat provides any problems?

        #######################################################################################################################
        
        # evaporation (m/day)
        self.waterBodyEvaporation = water_body_evaporation_volume / self.cellArea
        
        # local input to surface water (m3)
        self.local_input_to_surface_water += acc_local_input_to_surface_water

        # channel discharge (m3/day) = self.Q
        self.Q = acc_discharge_volume

        # return waterBodyStorage to channelStorage  
        channelStorageForRouting = self.return_water_body_storage_to_channel(channelStorageForRouting)

        # updating channelStorage (after routing)
        self.channelStorage = channelStorageForRouting

        # return channelStorageThatWillNotMove to channelStorage:
        self.channelStorage += channelStorageThatWillNotMove         
        
        # channel discharge (m3/s): for current time step
        #
        self.discharge = self.Q / vos.secondsPerDay()
        self.discharge = pcr.max(0., self.discharge)                   # reported channel discharge cannot be negative
        self.discharge = pcr.ifthen(self.landmask, self.discharge)
        #
        self.disChanWaterBody = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                                pcr.areamaximum(self.discharge,self.WaterBodies.waterBodyIds))
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)
        #
        self.disChanWaterBody = pcr.max(0.,self.disChanWaterBody)      # reported channel discharge cannot be negative

        # calculate the statistics of long and short term flow values
        self.calculate_statistics(groundwater)

    def kinematic_wave_update_not_working(self, landSurface,groundwater,currTimeStep,meteo): 

        logger.info("Using the fully kinematic wave method! ")

        # updating timesteps to calculate long and short term statistics 
        # values of avgDischarge, avgInflow, avgOutflow, etc.
        self.timestepsToAvgDischarge += 1.

        # the following variable defines total local change (input) to surface water storage bodies # unit: m3 
        # - only local processes; therefore not considering any routing processes
        self.local_input_to_surface_water = pcr.scalar(0.0)             # initiate the variable, start from zero

        # For simplification, surface water abstraction 
        #                     is done outside the sub daily time steps.
        #
        # update channelStorage (unit: m3) after actSurfaceWaterAbstraction 
        self.channelStorage -= landSurface.actSurfaceWaterAbstract * self.cellArea
        self.local_input_to_surface_water -= landSurface.actSurfaceWaterAbstract * self.cellArea
        #
        # reporting channelStorage after surface water abstraction (unit: m3)
        self.channelStorageAfterAbstraction = pcr.ifthen(self.landmask, self.channelStorage) 

        
        # return flow from (m) non irrigation water demand
        # - calculated in the landSurface.py module: landSurface.nonIrrReturnFlow

        # water consumption for non irrigation water demand (m) - this water is removed from the system/water balance
        self.nonIrrWaterConsumption = pcr.max(0.0,\
                                      landSurface.nonIrrGrossDemand - \
                                      landSurface.nonIrrReturnFlow)

        # runoff from landSurface cells (unit: m/day)                   
        self.runoff = landSurface.landSurfaceRunoff +\
                      groundwater.baseflow                              # values are over the entire cell area
        
        # route only non negative channelStorage (otherwise stay):
        # - note that, the following includes storages in 
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # estimate of water height (m)
        # - needed to estimate the length of sub-time step and 
        #     also to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
        self.water_height = channelStorageForRouting /\
                           (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)

        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = self.estimate_length_of_sub_time_step()

        #######################################################################################################################
        for i_loop in range(number_of_loops):
            
            msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
            logger.info(msg)
            
            # initiating accumulated values:
            if i_loop == 0:
                acc_local_input_to_surface_water    = pcr.scalar(0.0)   # unit: m3                            
                acc_water_body_evaporation_volume   = pcr.scalar(0.0)   # unit: m3
                acc_discharge_volume                = pcr.scalar(0.0)   # unit: m3
                

            if self.debugWaterBalance:\
                preStorage = pcr.ifthen(self.landmask,\
                             channelStorageForRouting)
                
            # update channelStorageForRouting after runoff and return flow from non irrigation demand
            channelStorageForRouting          += (self.runoff + landSurface.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3
            acc_local_input_to_surface_water  += (self.runoff + landSurface.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3

            # potential evaporation within the sub-time step ; unit: m, values are over the entire cell area 
            #
            water_body_potential_evaporation   = self.calculate_potential_evaporation(landSurface,currTimeStep,meteo) *\
                                                 length_of_sub_time_step/vos.secondsPerDay()
            # - accumulating potential evaporation
            if i_loop == 0:
                self.waterBodyPotEvap = pcr.scalar(0.0)
            self.waterBodyPotEvap += water_body_potential_evaporation                                 
            
            # update channelStorageForRouting after evaporation
            water_body_evaporation_volume      = pcr.min(pcr.max(channelStorageForRouting, 0.0), \
                                                 water_body_potential_evaporation * self.cellArea * length_of_sub_time_step/vos.secondsPerDay())
            channelStorageForRouting          -= water_body_evaporation_volume
            acc_local_input_to_surface_water  -= water_body_evaporation_volume
            acc_water_body_evaporation_volume += water_body_evaporation_volume
            
            if self.debugWaterBalance:\
                vos.waterBalanceCheck([self.runoff * length_of_sub_time_step/vos.secondsPerDay(), \
                                       landSurface.nonIrrReturnFlow * length_of_sub_time_step/vos.secondsPerDay()],\
                                      [water_body_evaporation_volume/self.cellArea],\
                                      [preStorage/self.cellArea],\
                                      [channelStorageForRouting/self.cellArea],\
                                       'channelStorageForRouting',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-5)

            # the kinematic wave is implemented only for channels (not to lakes and reservoirs)
            # at cells where lakes and/or reservoirs defined, move channelStorage to waterBodyStorage
            #
            storageAtLakeAndReservoirs = \
             pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                   channelStorageForRouting)
            storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs,0.0)
            #
            # - move only non negative values and use rounddown values
            storageAtLakeAndReservoirs = pcr.max(0.00, pcr.rounddown(storageAtLakeAndReservoirs))
            channelStorageForRouting -= storageAtLakeAndReservoirs               # unit: m3


            # alpha parameter and initial discharge variable needed for kinematic wave
            alpha, dischargeInitial = \
                   self.calculate_alpha_and_initial_discharge_for_kinematic_wave(channelStorageForRouting, \
                                                                                 self.water_height, \
                                                                                 self.innundatedFraction, self.floodDepth)
            
            # discharge (m3/s) based on kinematic wave approximation
            #~ logger.debug('start pcr.kinematic')
            self.subDischarge = pcr.kinematic(self.lddMap, dischargeInitial, 0.0, 
                                              alpha, self.beta, \
                                              1, length_of_sub_time_step, self.channelLength)
            self.subDischarge = pcr.max(0.0, pcr.cover(self.subDischarge, 0.0))
            #~ logger.debug('done')
            
            # set discharge to zero for lakes and reservoirs:
            self.subDischarge = pcr.cover(\
                                pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., pcr.scalar(0.0)), self.subDischarge)
            
            # make sure that we do not get negative channel storage
            self.subDischarge = pcr.min(self.subDischarge * length_of_sub_time_step, \
                                pcr.max(0.0, channelStorageForRouting + pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step)))/length_of_sub_time_step

            # update channelStorage (m3)
            storage_change_in_volume  = pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step) - self.subDischarge * length_of_sub_time_step 
            channelStorageForRouting += storage_change_in_volume 
            
            if self.debugWaterBalance:\
                vos.waterBalanceCheck([self.runoff * length_of_sub_time_step/vos.secondsPerDay(), \
                                       landSurface.nonIrrReturnFlow * length_of_sub_time_step/vos.secondsPerDay(),\
                                       storage_change_in_volume/self.cellArea],\
                                      [water_body_evaporation_volume/self.cellArea],\
                                      [preStorage/self.cellArea - storageAtLakeAndReservoirs/self.cellArea],\
                                      [channelStorageForRouting/self.cellArea],\
                                       'channelStorageForRouting (after routing, without lakes/reservoirs)',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-4)

            # lakes and reservoirs: update waterBodyStorage (inflow, storage and outflow)
            self.WaterBodies.update(storageAtLakeAndReservoirs,\
                                    self.timestepsToAvgDischarge,\
                                    self.maxTimestepsToAvgDischargeShort,\
                                    self.maxTimestepsToAvgDischargeLong,\
                                    currTimeStep,\
                                    self.avgDischarge,\
                                    length_of_sub_time_step,\
                                    self.downstreamDemand)

            # waterBodyStorage (m3) after outflow:                               # values given are per water body id (not per cell)
            self.waterBodyStorage = pcr.ifthen(self.landmask,
                                    self.WaterBodies.waterBodyStorage)
        
            # transfer outflow from lakes and/or reservoirs to channelStorages
            waterBodyOutflow = pcr.cover(\
                               pcr.ifthen(\
                               self.WaterBodies.waterBodyOut,
                               self.WaterBodies.waterBodyOutflow), 0.0)          # unit: m3

            # update channelStorage (m3) after waterBodyOutflow (m3)
            channelStorageForRouting += pcr.upstream(self.lddMap, waterBodyOutflow)
            # Note that local_input_to_surface_water does not include waterBodyOutflow

            # at the lake/reservoir outlets, add the discharge of water body outflow
            waterBodyOutflowInM3PerSec = pcr.ifthen(\
                                         self.WaterBodies.waterBodyOut,
                                         self.WaterBodies.waterBodyOutflow) / length_of_sub_time_step
            self.subDischarge = self.subDischarge + \
                                pcr.cover(waterBodyOutflowInM3PerSec, 0.0)                             
            self.subDischarge = pcr.ifthen(self.landmask, self.subDischarge)


            # total discharge_volume (m3) until this present i_loop
            acc_discharge_volume += self.subDischarge * length_of_sub_time_step

            # return waterBodyStorage to channelStorage  
            channelStorageForRouting = self.return_water_body_storage_to_channel(channelStorageForRouting)

            # route only non negative channelStorage (otherwise stay):
            channelStorageThatWillNotMove += pcr.ifthenelse(channelStorageForRouting < 0.0, channelStorageForRouting, 0.0)
            channelStorageForRouting       = pcr.max(0.000, channelStorageForRouting)

            # update flood fraction and flood depth
            self.inundatedFraction, self.floodDepth = self.returnInundationFractionAndFloodDepth(channelStorageForRouting)
            
            # update dynamicFracWat: fraction of surface water bodies (dimensionless) including lakes and reservoirs
            # - lake and reservoir surface water fraction
            self.dynamicFracWat = pcr.cover(\
                             pcr.min(1.0, self.WaterBodies.fracWat), 0.0)
            # - fraction of channel (including its excess above bankfull capacity) 
            self.dynamicFracWat += pcr.max(0.0, 1.0 - self.dynamicFracWat) * pcr.max(self.channelFraction, self.innundatedFraction)
            # - maximum value of dynamicFracWat is 1.0
            self.dynamicFracWat = pcr.ifthen(self.landmask, pcr.min(1.0, self.dynamicFracWat))

            # estimate water_height for the next loop
            # - needed to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
            self.water_height = channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)
            # TODO: Check whether the usage of dynamicFracWat provides any problems?

        #######################################################################################################################
        
        # evaporation (m/day)
        self.waterBodyEvaporation = water_body_evaporation_volume / self.cellArea
        
        # local input to surface water (m3)
        self.local_input_to_surface_water += acc_local_input_to_surface_water

        # channel discharge (m3/day) = self.Q
        self.Q = acc_discharge_volume

        # updating channelStorage (after routing)
        self.channelStorage = channelStorageForRouting

        # return channelStorageThatWillNotMove to channelStorage:
        self.channelStorage += channelStorageThatWillNotMove         
        
        # channel discharge (m3/s): for current time step
        #
        self.discharge = self.Q / vos.secondsPerDay()
        self.discharge = pcr.max(0., self.discharge)                   # reported channel discharge cannot be negative
        self.discharge = pcr.ifthen(self.landmask, self.discharge)
        #
        self.disChanWaterBody = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                                pcr.areamaximum(self.discharge,self.WaterBodies.waterBodyIds))
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)
        #
        self.disChanWaterBody = pcr.max(0.,self.disChanWaterBody)      # reported channel discharge cannot be negative

        # calculate the statistics of long and short term flow values
        self.calculate_statistics(groundwater)
        
    def calculate_statistics(self, groundwater):

        # short term average inflow (m3/s) and long term average outflow (m3/s) from lake and reservoirs
        self.avgInflow  = pcr.ifthen(self.landmask, pcr.cover(self.WaterBodies.avgInflow , 0.0)) 
        self.avgOutflow = pcr.ifthen(self.landmask, pcr.cover(self.WaterBodies.avgOutflow, 0.0))

        # short term and long term average discharge (m3/s)
        # - see: online algorithm on http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        #
        # - long term average disharge
        #
        dishargeUsed      = pcr.max(0.0, self.discharge)
        dishargeUsed      = pcr.max(dishargeUsed, self.disChanWaterBody)
        #
        deltaAnoDischarge = dishargeUsed - self.avgDischarge  
        self.avgDischarge = self.avgDischarge +\
                            deltaAnoDischarge/\
                            pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)
        self.avgDischarge = pcr.max(0.0, self.avgDischarge)                                    
        self.m2tDischarge = self.m2tDischarge + pcr.abs(deltaAnoDischarge*(dishargeUsed - self.avgDischarge))                             
        #
        # - short term average disharge
        #
        deltaAnoDischargeShort = dishargeUsed - self.avgDischargeShort  
        self.avgDischargeShort = self.avgDischargeShort +\
                                 deltaAnoDischargeShort/\
                                 pcr.min(self.maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)
        self.avgDischargeShort = pcr.max(0.0, self.avgDischargeShort)                         

        # long term average baseflow (m3/s) ; used as proxies for partitioning groundwater and surface water abstractions
        #
        baseflowM3PerSec = groundwater.baseflow * self.cellArea / vos.secondsPerDay()
        deltaAnoBaseflow = baseflowM3PerSec - self.avgBaseflow  
        self.avgBaseflow = self.avgBaseflow +\
                           deltaAnoBaseflow/\
                           pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)                
        self.avgBaseflow = pcr.max(0.0, self.avgBaseflow)

    def estimate_discharge_for_environmental_flow(self, channelStorage):

        # statistical assumptions:
        # - using z_score from the percentile 90
        z_score = 1.2816 
        #~ # - using z_score from the percentile 95
        #~ z_score = 1.645
        
        # long term variance and standard deviation of discharge values
        varDischarge = self.m2tDischarge / \
                       pcr.max(1.,\
                       pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)-1.)                             
                       # see: online algorithm on http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        stdDischarge = pcr.max(varDischarge**0.5, 0.0)
        
        # calculate minimum discharge for environmental flow (m3/s)
        minDischargeForEnvironmentalFlow = pcr.max(0.0, self.avgDischarge - z_score * stdDischarge)
        factor = 0.10 # to avoid flip flop
        minDischargeForEnvironmentalFlow = pcr.max(factor*self.avgDischarge, minDischargeForEnvironmentalFlow)   # unit: m3/s
        minDischargeForEnvironmentalFlow = pcr.max(0.0, minDischargeForEnvironmentalFlow)
        
        return minDischargeForEnvironmentalFlow


    def estimate_available_volume_for_abstraction(self, channelStorage, length_of_time_step = vos.secondsPerDay()):
        # input: channelStorage    in m3

        # estimate minimum discharge for environmental flow (m3/s)
        minDischargeForEnvironmentalFlow = self.estimate_discharge_for_environmental_flow(channelStorage)

        # available channelStorage that can be extracted for surface water abstraction
        readAvlChannelStorage  = pcr.max(0.0,channelStorage)
        
        # reduce readAvlChannelStorage if the average discharge < minDischargeForEnvironmentalFlow
        readAvlChannelStorage *= pcr.min(1.0,\
                                 vos.getValDivZero(pcr.max(0.0, pcr.min(self.avgDischargeShort, self.avgDischarge)), \
                                                                   minDischargeForEnvironmentalFlow, vos.smallNumber))
        
        # maintaining environmental flow if average discharge > minDischargeForEnvironmentalFlow            # TODO: Check why do we need this?
        readAvlChannelStorage = pcr.ifthenelse(self.avgDischargeShort < minDischargeForEnvironmentalFlow,
                                               readAvlChannelStorage,
                                               pcr.max(readAvlChannelStorage, \
                                               pcr.max(0.0,\
                                               self.avgDischargeShort - minDischargeForEnvironmentalFlow)*length_of_time_step))

        # maximum (precentage) of water can be abstracted from the channel - to avoid flip-flop
        maximum_percentage = 0.90
        readAvlChannelStorage = pcr.min(readAvlChannelStorage, \
                                        maximum_percentage*channelStorage)
        readAvlChannelStorage = pcr.max(0.0,\
                                        readAvlChannelStorage)
                                                
        # ignore small volume values - less than 0.1 m3
        readAvlChannelStorage = pcr.rounddown(readAvlChannelStorage*10.)/10.
        readAvlChannelStorage = pcr.ifthen(self.landmask, readAvlChannelStorage)
        
        return readAvlChannelStorage      # unit: m3

    def initiate_old_style_routing_reporting(self,iniItems):

        self.report = True
        try:
            self.outDailyTotNC = iniItems.routingOptions['outDailyTotNC'].split(",")
            self.outMonthTotNC = iniItems.routingOptions['outMonthTotNC'].split(",")
            self.outMonthAvgNC = iniItems.routingOptions['outMonthAvgNC'].split(",")
            self.outMonthEndNC = iniItems.routingOptions['outMonthEndNC'].split(",")
            self.outAnnuaTotNC = iniItems.routingOptions['outAnnuaTotNC'].split(",")
            self.outAnnuaAvgNC = iniItems.routingOptions['outAnnuaAvgNC'].split(",")
            self.outAnnuaEndNC = iniItems.routingOptions['outAnnuaEndNC'].split(",")
        except:
            self.report = False
        if self.report == True:
            # daily output in netCDF files:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            #
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_dailyTot.nc",\
                                                    var,"undefined")
            # MONTHly output in netCDF files:
            # - cummulative
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initiating monthlyVarTot (accumulator variable):
                    vars(self)[var+'MonthTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthTot.nc",\
                                                    var,"undefined")
            # - average
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # initiating monthlyTotAvg (accumulator variable)
                    vars(self)[var+'MonthTot'] = None
                    # initiating monthlyVarAvg:
                    vars(self)[var+'MonthAvg'] = None
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthAvg.nc",\
                                                    var,"undefined")
            # - last day of the month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthEnd.nc",\
                                                    var,"undefined")
            # YEARly output in netCDF files:
            # - cummulative
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:
                    # initiating yearly accumulator variable:
                    vars(self)[var+'AnnuaTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaTot.nc",\
                                                    var,"undefined")
            # - average
            if self.outAnnuaAvgNC[0] != "None":
                for var in self.outAnnuaAvgNC:
                    # initiating annualyVarAvg:
                    vars(self)[var+'AnnuaAvg'] = None
                    # initiating annualyTotAvg (accumulator variable)
                    vars(self)[var+'AnnuaTot'] = None
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaAvg.nc",\
                                                    var,"undefined")
            # - last day of the year
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaEnd.nc",\
                                                    var,"undefined")

    def old_style_routing_reporting(self,currTimeStep):

        if self.report == True:
            timeStamp = datetime.datetime(currTimeStep.year,\
                                          currTimeStep.month,\
                                          currTimeStep.day,\
                                          0)
            # writing daily output to netcdf files
            timestepPCR = currTimeStep.timeStepPCR
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_dailyTot.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var),vos.MV),\
                                         timeStamp,timestepPCR-1)

            # writing monthly output to netcdf files
            # -cummulative
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:

                    # introduce variables at the beginning of simulation or
                    #     reset variables at the beginning of the month
                    if currTimeStep.timeStepPCR == 1 or \
                       currTimeStep.day == 1:\
                       vars(self)[var+'MonthTot'] = pcr.scalar(0.0)

                    # accumulating
                    vars(self)[var+'MonthTot'] += vars(self)[var]

                    # reporting at the end of the month:
                    if currTimeStep.endMonth == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_monthTot.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var+'MonthTot'),\
                           vos.MV),timeStamp,currTimeStep.monthIdx-1)
            # -average
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # only if a accumulator variable has not been defined: 
                    if var not in self.outMonthTotNC: 

                        # introduce accumulator at the beginning of simulation or
                        #     reset accumulator at the beginning of the month
                        if currTimeStep.timeStepPCR == 1 or \
                           currTimeStep.day == 1:\
                           vars(self)[var+'MonthTot'] = pcr.scalar(0.0)
                        # accumulating
                        vars(self)[var+'MonthTot'] += vars(self)[var]

                    # calculating average & reporting at the end of the month:
                    if currTimeStep.endMonth == True:
                        vars(self)[var+'MonthAvg'] = vars(self)[var+'MonthTot']/\
                                                     currTimeStep.day  
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_monthAvg.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var+'MonthAvg'),\
                           vos.MV),timeStamp,currTimeStep.monthIdx-1)
            #
            # -last day of the month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    # reporting at the end of the month:
                    if currTimeStep.endMonth == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_monthEnd.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)

            # writing yearly output to netcdf files
            # -cummulative
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:

                    # introduce variables at the beginning of simulation or
                    #     reset variables at the beginning of the month
                    if currTimeStep.timeStepPCR == 1 or \
                       currTimeStep.doy == 1:\
                       vars(self)[var+'AnnuaTot'] = pcr.scalar(0.0)

                    # accumulating
                    vars(self)[var+'AnnuaTot'] += vars(self)[var]

                    # reporting at the end of the year:
                    if currTimeStep.endYear == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_annuaTot.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var+'AnnuaTot'),\
                           vos.MV),timeStamp,currTimeStep.annuaIdx-1)
            # -average
            if self.outAnnuaAvgNC[0] != "None":
                for var in self.outAnnuaAvgNC:
                    # only if a accumulator variable has not been defined: 
                    if var not in self.outAnnuaTotNC: 
                        # introduce accumulator at the beginning of simulation or
                        #     reset accumulator at the beginning of the year
                        if currTimeStep.timeStepPCR == 1 or \
                           currTimeStep.doy == 1:\
                           vars(self)[var+'AnnuaTot'] = pcr.scalar(0.0)
                        # accumulating
                        vars(self)[var+'AnnuaTot'] += vars(self)[var]
                    #
                    # calculating average & reporting at the end of the year:
                    if currTimeStep.endYear == True:
                        vars(self)[var+'AnnuaAvg'] = vars(self)[var+'AnnuaTot']/\
                                                     currTimeStep.doy  
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_annuaAvg.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var+'AnnuaAvg'),\
                           vos.MV),timeStamp,currTimeStep.annuaIdx-1)
            #
            # -last day of the year
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                    # reporting at the end of the year:
                    if currTimeStep.endYear == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                         str(var)+"_annuaEnd.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var),vos.MV),\
                                         timeStamp,currTimeStep.annuaIdx-1)

