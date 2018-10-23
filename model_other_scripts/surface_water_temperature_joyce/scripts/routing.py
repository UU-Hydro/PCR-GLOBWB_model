#!/usr/bin/ python
# -*- coding: utf-8 -*-

import os
import types
import math

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
        
        if self.waterTemperature:
          result['waterTemperature']        = self.waterTemp                   #  C      ; water temperature
          result['iceThickness']        = self.iceThickness                    #  C      ; water temperature
        
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

        # TODO: 26 Feb 2014, EdeltaIceThicknessn found that reasonable runs are only found 
        # if all of these options = True.                    
        self.includeWaterBodies = True
        self.includeLakes = True
        self.includeReservoirs =  True

        # local drainage direction:
        self.lddMap = vos.readPCRmapClone(\
                  iniItems.routingOptions['lddMap'],
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

        self.cellArea = vos.readPCRmapClone(\
                  iniItems.routingOptions['cellAreaMap'],
                  self.cloneMap,self.tmpDir,self.inputDir)

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
        self.eta = 0.25
        self.nu  = 0.40
        self.tau = 8.00
        self.phi = 0.58

        # option to use minimum channel width (m)
        self.minChannelWidth = pcr.scalar(0.0)
        if "minimumChannelWidth" in iniItems.routingOptions.keys():
            if iniItems.routingOptions['minimumChannelWidth'] != "None":\
               self.minChannelWidth = vos.readPCRmapClone(\
                                      iniItems.routingOptions['minimumChannelWidth'],
                                      self.cloneMap,self.tmpDir,self.inputDir)
        
        # option to use constant channel width (m)
        self.constantChannelWidth = None
        if "constantChannelWidth" in iniItems.routingOptions.keys():
            if iniItems.routingOptions['constantChannelWidth'] != "None":\
               self.constantChannelWidth = vos.readPCRmapClone(\
                                           iniItems.routingOptions['constantChannelWidth'],
                                           self.cloneMap,self.tmpDir,self.inputDir)

        # an assumption for broad sheet flow in kinematic wave methods/approaches        
        self.beta = 0.6 

        # cellLength (m) is approximated cell diagonal   
        #
        cellSizeInArcMin    =  self.cellSizeInArcDeg*60.
        verticalSizeInMeter =  cellSizeInArcMin*1852.                            
        #
        self.cellLengthFD = ((self.cellArea/verticalSizeInMeter)**(2)+\
                                           (verticalSizeInMeter)**(2))\
                                                                **(0.5) 
        nrCellsDownstream  = pcr.ldddist(self.lddMap,\
                                         self.lddMap == 5,1.)
        distanceDownstream = pcr.ldddist(self.lddMap,\
                                         self.lddMap == 5,\
                                         self.cellLengthFD)
        channelLengthDownstream = \
                (self.cellLengthFD + distanceDownstream)/\
                (nrCellsDownstream + 1)                 # unit: m
        self.dist2celllength  = channelLengthDownstream /\
                                  self.cellSizeInArcDeg # unit: m/arcDegree  

        # the channel gradient must be >= minGradient 
        minGradient   = 0.00001
        self.gradient = pcr.max(minGradient,\
                        pcr.cover(self.gradient, minGradient))

        # initiate/create WaterBody class
        self.WaterBodies = waterBodies.WaterBodies(iniItems,self.landmask)

        self.fileCropKC = vos.getFullPath(\
                     iniItems.routingOptions['cropCoefficientWaterNC'],\
                     self.inputDir)

        # courantNumber criteria for numerical stability in kinematic wave methods/approaches
        self.courantNumber = 0.50

        # empirical values for minimum number of sub-time steps:
        design_flood_speed = 5.00 # m/s
        design_length_of_sub_time_step   = pcr.cellvalue(
                                           pcr.mapminimum(
                                           self.courantNumber * self.cellLengthFD / design_flood_speed),1)[0]
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
        self.critical_water_height = 0.25;					                                                          # used in Van Beek et al. (2011)

        # assumption for the minimum fracwat value used for calculating water height
        self.min_fracwat_for_water_height = 0.01
        self.max_water_height = 50000000
        
        # assumption for minimum crop coefficient for surface water bodies 
        self.minCropWaterKC = 0.00
        if 'minCropWaterKC' in iniItems.routingOptions.keys():
            self.minCropWaterKC = float(iniItems.routingOptions['minCropWaterKC'])
            
        self.floodPlain = iniItems.routingOptions['dynamicFloodPlain'] == "True"
        
        if self.floodPlain:
            # get the elevation profile per grid cell
            self.relZFileName= iniItems.routingOptions['relativeElevationFiles']
            self.areaFractions= iniItems.routingOptions['relativeElevationLevels']
            self.areaFractions = map(float, self.areaFractions.split(','))
            self.nrZLevels = len(self.areaFractions)
            # reduction parameter of smoothing interval and error threshold
            self.reductionKK= float(iniItems.routingOptions['reductionKK'])
            self.criterionKK= float(iniItems.routingOptions['criterionKK'])
            self.floodplainManN= float(iniItems.routingOptions['floodplainManningsN'])
            self.channelStorageCapacity = vos.readPCRmapClone(iniItems.routingOptions['maxChannelCapacity'],self.cloneMap,self.tmpDir,self.inputDir)
            self.channelLength = vos.readPCRmapClone(iniItems.routingOptions['channelLength'],self.cloneMap,self.tmpDir,self.inputDir)
            self.channelDepth = vos.readPCRmapClone(iniItems.routingOptions['channelDepth'],self.cloneMap,self.tmpDir,self.inputDir)
            self.channelGradient = vos.readPCRmapClone(iniItems.routingOptions['channelGradient'],self.cloneMap,self.tmpDir,self.inputDir)
            self.lddMap = vos.readPCRmapClone(iniItems.routingOptions['channelLDD'],self.cloneMap,self.tmpDir,self.inputDir, True)
            self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
            self.lddMap = pcr.lddrepair(self.lddMap)
            self.lddMap = pcr.lddmask(self.lddMap, self.landmask)

            self.channelStorageCapacity = ifthen(self.landmask, pcr.cover(self.channelStorageCapacity, 0.0))
            self.channelLength = ifthen(self.landmask, pcr.cover(self.channelLength, 0.0))
            self.channelDepth = ifthen(self.landmask, pcr.cover(self.channelDepth, 0.0))
            self.channelGradient = ifthen(self.landmask, pcr.cover(self.channelGradient, 0.0))
            self.channelGradient = pcr.max(self.channelGradient, 0.00005)
            pcr.report(self.channelStorageCapacity, "channelStorageCapacity.map")
            pcr.report(self.channelLength, "channelLength.map")
            pcr.report(self.channelDepth, "channelDepth.map")
            pcr.report(self.channelGradient, "channelGradient.map")


            #-patch elevations: those that are part of sills are updated on the basis of the floodplain gradient
            # using local distances deltaX per increment upto z[N] and the sum over sills
            #-fill all lists including smoothing interval and slopes
            self.relZ= [0.]*self.nrZLevels
            for iCnt in range(1,self.nrZLevels):
                inputName = self.relZFileName %(self.areaFractions[iCnt]*100)
                self.relZ[iCnt] = vos.readPCRmapClone(inputName,self.cloneMap,self.tmpDir,self.inputDir)
                pcr.report(self.relZ[iCnt], "elev"+str(iCnt)+".map")
                self.relZ[iCnt] = ifthen(self.landmask, pcr.cover(self.relZ[iCnt], 0.0))
                pcr.report(self.relZ[iCnt], "Covelev"+str(iCnt)+".map")
            #-minimum slope of floodplain, being defined as the longest sill, first used to retrieve
            # longest cumulative distance 
            deltaX= [self.cellArea**0.5]*self.nrZLevels
            deltaX[0]= 0.
            sumX= deltaX[:]
            minSlope= 0.
            for iCnt in range(self.nrZLevels):
                if iCnt < self.nrZLevels-1:
                    deltaX[iCnt]= (self.areaFractions[iCnt+1]**0.5-self.areaFractions[iCnt]**0.5)*deltaX[iCnt]
                else:
                    deltaX[iCnt]= (1.-self.areaFractions[iCnt-1]**0.5)*deltaX[iCnt]
                if iCnt > 0:
                    sumX[iCnt]= pcr.ifthenelse(self.relZ[iCnt] == self.relZ[iCnt-1],sumX[iCnt-1]+deltaX[iCnt],0.)
                    minSlope= pcr.ifthenelse(self.relZ[iCnt] == self.relZ[iCnt-1],\
                        pcr.max(sumX[iCnt],minSlope),minSlope)
            minSlope= pcr.min(self.gradient,0.5*pcr.max(deltaX[1],minSlope)**-1.)
            #-add small increment to elevations to each sill except in the case of lakes
            for iCnt in range(self.nrZLevels):
                self.relZ[iCnt]= self.relZ[iCnt]+sumX[iCnt]*pcr.ifthenelse(self.relZ[self.nrZLevels-1] > 0.,\
                    minSlope,0.)
            #-set slope and smoothing interval between dy= y(i+1)-y(i) and dx= x(i+1)-x(i)
            # on the basis of volume
            #-slope and smoothing interval
            self.kSlope=  [0.]*(self.nrZLevels)
            self.mInterval= [0.]*(self.nrZLevels)
            self.floodVolume= [0.]*(self.nrZLevels)
            for iCnt in range(1,self.nrZLevels):
                self.floodVolume[iCnt]= self.floodVolume[iCnt-1]+\
                    0.5*(self.areaFractions[iCnt]+self.areaFractions[iCnt-1])*\
                    (self.relZ[iCnt]-self.relZ[iCnt-1])*self.cellArea
                self.kSlope[iCnt-1]= (self.areaFractions[iCnt]-self.areaFractions[iCnt-1])/\
                    pcr.max(0.001,self.floodVolume[iCnt]-self.floodVolume[iCnt-1])
            for iCnt in range(1,self.nrZLevels):
                if iCnt < (self.nrZLevels-1):
                    self.mInterval[iCnt]= 0.5*self.reductionKK*pcr.min(self.floodVolume[iCnt+1]-self.floodVolume[iCnt],\
                        self.floodVolume[iCnt]-self.floodVolume[iCnt-1])
                else:
                    self.mInterval[iCnt]= 0.5*self.reductionKK*(self.floodVolume[iCnt]-self.floodVolume[iCnt-1])        

        self.waterTemperature = iniItems.routingOptions['waterTemperature'] == "True"
        
        if self.waterTemperature:
            #-constants for the energy balance
            # threshold temperature for snowmelt (degC)
            # density of water [kg/m3]
            # latent heat of vaporization [J/kg]
            # latent heat of fusion [J/kg]
            # specific heat of water [J/kg/degC]
            # heat transfer coefficient for water [W/m2/degC]
            # heat transfer coefficient for ice [W/m2/degC]
            # albedo of water [-]
            # albedo of snow and ice [-]	  
            self.iceThresTemp= pcr.scalar(273.15)
            self.densityWater= 1000.0
            self.latentHeatVapor= pcr.scalar(2.5e6)
            self.latentHeatFusion= pcr.scalar(3.34e5)
            self.specificHeatWater= pcr.scalar(4190.0)
            self.heatTransferWater= pcr.scalar(20.0)
            self.heatTransferIce= pcr.scalar(8.0)
            self.albedoWater= pcr.scalar(0.15)
            self.albedoSnow= pcr.scalar(0.50)
            #-energy balance, proxy for temperature of groundwater store: mean annual temperature
            # and reduction in the temperature for falling rain            
            self.deltaTPrec= pcr.scalar(1.5)
            #-table to convert cloud cover to sunshine hours
            # and constants to calculate radiation according to
            # Doornkamp & Pruitt
            self.sunFracTBL= iniItems.meteoOptions['sunhoursTable']            
            self.radCon= 0.25
            self.radSlope= 0.50
            #-stefan-boltzman constant [W/m2/K]
            self.stefanBoltzman= 5.67e-8

            #- Path to cloudcover file
            self.cloudFileNC = iniItems.meteoOptions['cloudcoverNC']
            self.radFileNC = iniItems.meteoOptions['radiationNC']
            self.vapFileNC = iniItems.meteoOptions['vaporNC']
            self.annualTNC = iniItems.meteoOptions['annualAvgTNC']
            self.maxIceThickness= 3.0
            self.deltaIceThickness = 0.0
                    
        # get the initialConditions
        self.getICs(iniItems, initialConditions)
        
        # initiate old style reporting                                  # TODO: remove this!
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

            if self.waterTemperature:
                # Initial conditions needed for temperature module
                self.waterTemp               = vos.readPCRmapClone(iniItems.routingOptions['waterTemperatureIni'],self.cloneMap,self.tmpDir,self.inputDir)
                self.iceThickness               = vos.readPCRmapClone(iniItems.routingOptions['iceThicknessIni'],self.cloneMap,self.tmpDir,self.inputDir)

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

            if self.waterTemperature:
                self.waterTemp               = iniConditions['routing']['waterTemperature']
                self.iceThickness            = iniConditions['routing']['iceThickness']
            
        self.channelStorage        = pcr.ifthen(self.landmask, pcr.cover(self.channelStorage,        0.0))
        self.readAvlChannelStorage = pcr.ifthen(self.landmask, pcr.cover(self.readAvlChannelStorage, 0.0))
        self.avgDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.avgDischarge,          0.0))
        self.m2tDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.m2tDischarge,          0.0))
        self.avgDischargeShort     = pcr.ifthen(self.landmask, pcr.cover(self.avgDischargeShort,     0.0))
        self.avgBaseflow           = pcr.ifthen(self.landmask, pcr.cover(self.avgBaseflow,           0.0))
        self.riverbedExchange      = pcr.ifthen(self.landmask, pcr.cover(self.riverbedExchange,      0.0))
        self.subDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.subDischarge ,         0.0))
        if self.floodPlain:
	  self.subDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.subDischarge ,         0.0))

        self.readAvlChannelStorage = pcr.min(self.readAvlChannelStorage, self.channelStorage)
        self.readAvlChannelStorage = pcr.max(self.readAvlChannelStorage, 0.0)

        if self.waterTemperature:
            self.waterTemp             = pcr.ifthen(self.landmask, pcr.cover(self.waterTemp ,         0.0))
            self.iceThickness          = pcr.ifthen(self.landmask, pcr.cover(self.iceThickness ,         0.0))
            self.channelStorageTimeBefore = self.channelStorage
            self.totEW = self.channelStorage * self.waterTemp*self.specificHeatWater * self.densityWater
            self.temp_water_height = yMean = self.eta * pow (self.avgDischarge, self.nu)
        
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
                self.waterBodyStorage = vos.readPCRmapClone(iniItems.routingOptions['waterBodyStorageIni'],self.cloneMap,self.tmpDir,self.inputDir)
                self.waterBodyStorage = pcr.ifthen(self.landmask, self.waterBodyStorage)
            else:
                self.waterBodyStorage = None
        else:
            # read initial conditions from the memory
            self.avgInflow        = iniConditions['routing']['avgLakeReservoirInflowShort']
            self.avgOutflow       = iniConditions['routing']['avgLakeReservoirOutflowLong']
            self.waterBodyStorage = iniConditions['routing']['waterBodyStorage']


    def getRoutingParamAvgDischarge(self, avgDischarge, dist2celllength):
        # obtain routing parameters based on average (longterm) discharge
        # output: channel dimensions and 
        #         characteristicDistance (for accuTravelTime input)
        
        yMean = self.eta * pow (avgDischarge, self.nu ) # avgDischarge in m3/s
        wMean = self.tau * pow (avgDischarge, self.phi)
 
        # option to use constant channel width (m)
        if not isinstance(self.constantChannelWidth,types.NoneType):\
           wMean = pcr.cover(self.constantChannelWidth, wMean)

        # minimum channel width (m)
        wMean = pcr.max(self.minChannelWidth, wMean)

        yMean =   pcr.max(yMean,0.01) # channel depth (m)
        wMean =   pcr.max(wMean,0.01) # channel width (m)
        yMean = pcr.cover(yMean,0.01)
        wMean = pcr.cover(wMean,0.01)

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
                self.manningsN * \
                vos.secondsPerDay()                         #  meter/day

        characteristicDistance = \
         pcr.max((self.cellSizeInArcDeg)*0.000000001,\
                 characteristicDistance/dist2celllength)    # arcDeg/day
        
        # charateristicDistance for each lake/reservoir:
        lakeReservoirCharacteristicDistance = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                              pcr.areaaverage(characteristicDistance, self.WaterBodies.waterBodyIds))
        #
        # - make sure that all outflow will be released outside lakes and reservoirs
        outlets = pcr.cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyOut) > 0, pcr.boolean(1)), pcr.boolean(0))
        distance_to_outlets = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                              pcr.ldddist(self.lddMap, outlets, pcr.scalar(1.0)))
        lakeReservoirCharacteristicDistance = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                              pcr.max(distance_to_outlets + pcr.downstreamdist(self.lddMap)*1.50, lakeReservoirCharacteristicDistance))
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

        return (yMean, wMean, characteristicDistance)
        

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

        # estimating channel discharge (m3/day)
        self.Q = pcr.accutraveltimeflux(self.lddMap,\
                                        channelStorageForAccuTravelTime,\
                                        self.characteristicDistance)
        self.Q = pcr.cover(self.Q, 0.0)
        # for very small velocity (i.e. characteristicDistanceForAccuTravelTime), discharge can be missing value.
        # see: http://sourceforge.net/p/pcraster/bugs-and-feature-requests/543/
        #      http://karssenberg.geo.uu.nl/tt/TravelTimeSpecification.htm
        #
        # and make sure that no negative discharge
        self.Q = pcr.max(0.0, self.Q)                                   # unit: m3/day        

        # updating channelStorage (after routing)
        #
        # - alternative 1: using accutraveltimestate
        self.channelStorage = pcr.accutraveltimestate(self.lddMap,\
                              channelStorageForAccuTravelTime,\
                              self.characteristicDistance)              # unit: m3

        #~ # - alternative 2: using the calculated Q (Can we do this?)
        #~ storage_change_in_volume  = pcr.upstream(self.lddMap, self.Q) - self.Q
        #~ channelStorageForRouting += storage_change_in_volume 

        # return channelStorageThatWillNotMove to channelStorage:
        self.channelStorage += channelStorageThatWillNotMove            # unit: m3

        # for non kinematic wave approach, set subDishcarge to missing values
        self.subDischarge = pcr.scalar(vos.MV) 

    def estimate_length_of_sub_time_step(self): 

        # estimate the length of sub-time step (unit: s):
        # - the shorter is the better
        # - estimated based on the initial or latest sub-time step discharge (unit: m3/s)
        #
        length_of_sub_time_step = pcr.ifthenelse(self.subDischarge > 0.0, 
                                  self.water_height * self.dynamicFracWat * self.cellArea / self.subDischarge, vos.secondsPerDay())

        # determine the number of sub time steps (based on Rens van Beek's method - check this method with him)
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

    def simplifiedKinematicWave(self, meteo, landSurface, groundwater): 
        """
        The 'simplifiedKinematicWave':
        1. First, assume that all local fluxes has been added to 'channelStorage'. This is done outside of this function/method.
        2. Then, the 'channelStorage' is routed by using 'pcr.kinematic function' with 'lateral_inflow' = 0.0.
        """

        ##########################################################################################################################

        logger.info("Using the simplifiedKinematicWave method ! ")
        
        # route only non negative channelStorage (otherwise stay):
        self.channelStorage = self.channelStorage
        
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # water height (m)
        self.water_height = pcr.min(self.max_water_height, channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea))
        self.iniWater = self.water_height
        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = \
          self.estimate_length_of_sub_time_step()
              
        for i_loop in range(number_of_loops):
            
            if (i_loop + 1)%10 == 0:
                msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
                logger.info(msg)
            
            if self.floodPlain:
                self.dynamicFracWat, self.water_height, alpha, dischargeInitial = self.kinAlphaComposite(channelStorageForRouting)
                self.dynamicFracWat = pcr.min(pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat),1.0)
            else:    
                #alpha parameter and initial discharge variable needed for kinematic wave
                alpha, dischargeInitial = self.calculate_alpha_and_initial_discharge_for_kinematic_wave() 

            # at the lake/reservoir outlets, use the discharge of water bofy outflow
            waterBodyOutflowInM3PerSec = pcr.ifthen(\
                                         self.WaterBodies.waterBodyOut,
                                         self.WaterBodies.waterBodyOutflow) / vos.secondsPerDay()
            waterBodyOutflowInM3PerSec = pcr.ifthen(\
                                         pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                                         pcr.cover(waterBodyOutflowInM3PerSec,0.0))                                         
            dischargeInitial = pcr.cover(waterBodyOutflowInM3PerSec, dischargeInitial)                             

            # discharge (m3/s) based on kinematic wave approximation
            #logger.info('start pcr.kinematic')
            self.subDischarge = pcr.kinematic(self.lddMap, dischargeInitial, 0.0, 
                                              alpha, self.beta, \
                                              1, length_of_sub_time_step, self.cellLengthFD)
            #logger.info('done')
            
            # update channelStorage (m3)
            storage_change_in_volume  = pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step) - self.subDischarge * length_of_sub_time_step 
            channelStorageForRouting += storage_change_in_volume 
            #
            # route only non negative channelStorage (otherwise stay):
            channelStorageThatWillNotMove += pcr.ifthenelse(channelStorageForRouting < 0.0, channelStorageForRouting, 0.0)
            channelStorageForRouting       = pcr.max(0.000, channelStorageForRouting)
            #
            # update water_height (this will be passed to the next loop)
            if self.floodPlain != True:
                self.water_height = pcr.min(self.max_water_height, channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea))

            # total discharge_volume (m3) until this present i_loop
            if i_loop == 0: discharge_volume = pcr.scalar(0.0)
            discharge_volume += self.subDischarge * length_of_sub_time_step
            
            if self.waterTemperature:
                # updating channelStorage (after routing)
                self.channelStorageNow = pcr.max(0.0, channelStorageForRouting)
                
                self.energyRouting(length_of_sub_time_step)
                
                self.channelStorageTimeBefore = pcr.max(0.0, self.channelStorageNow)


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
                                               self.cellLengthFD,\
                                               self.cellSizeInArcDeg,\
                                               initial_conditions_for_water_bodies)               # the last line is for the initial conditions of lakes/reservoirs

        if (currTimeStep.doy == 1) and (currTimeStep.timeStepPCR > 1):
            self.WaterBodies.getParameterFiles(currTimeStep,\
                                               self.cellArea,\
                                               self.lddMap,\
                                               self.cellLengthFD,\
                                               self.cellSizeInArcDeg)
        #
        #self.WaterBodies.waterBodyIds = pcr.ifthen(self.landmask, pcr.nominal(-1)) #TODO
        # downstreamDemand (m3/s) for reservoirs 
        # - this one must be called before updating timestepsToAvgDischarge
        # - estimated based on environmental flow discharge 
        self.downstreamDemand = self.estimate_discharge_for_environmental_flow(self.channelStorage)
        
        # get routing/channel parameters/dimensions (based on avgDischarge)
        # and estimating water bodies fraction ; this is needed for calculating evaporation from water bodies
        # 
        self.yMean, self.wMean, self.characteristicDistance = \
                self.getRoutingParamAvgDischarge(self.avgDischarge,\
                self.dist2celllength)
        # 
        channelFraction = pcr.max(0.0, pcr.min(1.0,\
                          self.wMean * self.cellLengthFD / (self.cellArea)))
        self.channelFraction = channelFraction
        if currTimeStep.timeStepPCR == 1:
            if self.floodPlain:
                self.dynamicFracWat, self.water_height = self.returnFloodedFraction(self.channelStorage)
                self.dynamicFracWat = pcr.min(pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat),1.0)
            else: 
                self.dynamicFracWat = pcr.max(channelFraction, self.WaterBodies.fracWat)
            self.dynamicFracWat = pcr.ifthen(self.landmask, self.dynamicFracWat)
        
        # routing methods
        if self.method == "accuTravelTime" or self.method == "simplifiedKinematicWave": \
           self.simple_update(landSurface,groundwater,currTimeStep,meteo)
        #
        if self.method == "kinematicWave": \
           self.kinematic_wave_update(landSurface,groundwater,currTimeStep,meteo)                 
        # NOTE that this method require abstraction from fossil groundwater.
        
        # infiltration from surface water bodies (rivers/channels, as well as lakes and/or reservoirs) to groundwater bodies
        # - this exchange fluxes will be handed in the next time step
        # - in the future, this will be the interface between PCR-GLOBWB & MODFLOW (based on the difference between surface water levels & groundwater heads)
        #
        self.calculate_exchange_to_groundwater(groundwater,currTimeStep) 

        # volume water released in pits (losses: to the ocean / endorheic basin)
        self.outgoing_volume_at_pits = pcr.ifthen(self.landmask,
                                       pcr.cover(
                                       pcr.ifthen(self.lddMap == pcr.ldd(5), self.Q), 0.0))
        #
        # TODO: accumulate water in endorheic basins that are considered as lakes/reservoirs
        
        # estimate volume of water that can be extracted for abstraction in the next time step
        self.readAvlChannelStorage = self.estimate_available_volume_for_abstraction(self.channelStorage)
        
        # old-style reporting                             
        self.old_style_routing_reporting(currTimeStep)                 # TODO: remove this one

    def calculate_potential_evaporation(self,landSurface,currTimeStep,meteo):

        # potential evaporation from water bodies
        # current principle: 
        # - if landSurface.actualET < waterKC * meteo.referencePotET * self.fracWat
        #   then, we add more evaporation
        #
        if (currTimeStep.day == 1) or (currTimeStep.timeStepPCR == 1):
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
        waterBodyPotEvap = waterBodyPotEvapOvesSurfaceWaterArea * self.dynamicFracWat
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

        # remaining potential evaporation (m) from water bodies
        self.remainWaterBodyPotEvap = pcr.max(0.0, self.waterBodyPotEvap - self.waterBodyEvaporation)
        
    def calculate_extra_evaporation(self):
		# limited to self.remainWaterBodyPotEvap: remaining potential evaporation (m) from water bodies

        # evaporation volume from water bodies (m3) - limited to available channelStorage
        volLocEvapWaterBody = pcr.min(\
                              pcr.max(0.0,self.channelStorage),
                              self.remainWaterBodyPotEvap * self.dynamicFracWat * self.cellArea)

        # update channelStorage (m3) after evaporation from water bodies
        self.channelStorage = self.channelStorage -\
                              volLocEvapWaterBody
        self.local_input_to_surface_water -= volLocEvapWaterBody
        
        # update evaporation (m) from water bodies                             
        self.waterBodyEvaporation += volLocEvapWaterBody / self.cellArea

        # remaining potential evaporation (m) from water bodies
        self.remainWaterBodyPotEvap = pcr.max(0.0, self.remainWaterBodyPotEvap - volLocEvapWaterBody / self.cellArea)

    def calculate_exchange_to_groundwater(self,groundwater,currTimeStep):

        if self.debugWaterBalance:\
           preStorage = self.channelStorage                            # unit: m3

        # riverbed infiltration (m3/day):
        #
        # - current implementation based on Inge's principle (later, will be based on groundater head (MODFLOW) and can be negative)
        # - happening only if 0.0 < baseflow < total_groundwater_abstraction
        # - total_groundwater_abstraction = groundwater.nonFossilGroundwaterAbs + groundwater.unmetDemand
        # - infiltration rate will be based on aquifer saturated conductivity
        # - limited to fracWat
        # - limited to available channelStorage
        # - this infiltration will be handed to groundwater in the next time step
        # - References: de Graaf et al. (2014); Wada et al. (2012); Wada et al. (2010)
        # - TODO: This concept should be IMPROVED. 
        #
        riverbedConductivity  = groundwater.kSatAquifer # unit: m/day
        total_groundwater_abstraction = pcr.max(0.0, groundwater.nonFossilGroundwaterAbs + groundwater.unmetDemand)   # unit: m
        self.riverbedExchange = pcr.max(0.0,\
                                pcr.min(pcr.max(0.0,self.channelStorage),\
                                pcr.ifthenelse(groundwater.baseflow > 0.0, \
                                pcr.ifthenelse(total_groundwater_abstraction > groundwater.baseflow, \
                                riverbedConductivity * self.dynamicFracWat * self.cellArea, \
                                0.0), 0.0)))
        self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)                         
        factor = 0.05 # to avoid flip flop
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


    def reduce_unmet_demand(self,landSurface,groundwater,currTimeStep):

        logger.info("Reducing unmetDemand by allowing extra surface water abstraction.")

        extra_surface_water_abstraction = pcr.scalar(0.0)
        reduction_for_unmetDemand       = pcr.scalar(0.0)
        
        # estimate channel storage that can be extracted (unit: m3)
        self.readAvlChannelStorage = self.estimate_available_volume_for_abstraction(self.channelStorage)
        
        # potential_unmet_demand (unit: m) 
        potential_unmet_demand = landSurface.totalPotentialGrossDemand -\
                                 landSurface.allocSurfaceWaterAbstract -\
                                 groundwater.allocNonFossilGroundwater

        if self.debugWaterBalance:
            test = pcr.ifthen(potential_unmet_demand < 0.0, potential_unmet_demand)
            a,b,c = vos.getMinMaxMean(pcr.scalar(test),True)
            threshold = 1e-3
            if abs(a) > threshold or abs(b) > threshold:
                logger.info("WARNING !!!!! Water Balance Error. There is negative unmetDemand ... Min %f Max %f Mean %f" %(a,b,c))

        if landSurface.usingAllocSegments == False and landSurface.limitAbstraction == False:
        
            logger.info("Surface water abstraction is only to satisfy local demand. No network.")
            
            # reduction_for_unmetDemand
            reduction_for_unmetDemand = pcr.min(self.readAvlChannelStorage / self.cellArea, \
                                                potential_unmet_demand)                           # unit: m

            # actual extra surface water abstraction in meter 
            extra_surface_water_abstraction = pcr.ifthen(self.landmask, reduction_for_unmetDemand)
                                                
            
        if landSurface.usingAllocSegments == True and landSurface.limitAbstraction == False:
        
            # TODO: Assuming that there is also network for distributing groundwater abstractions.
            # Notes: Incorporating distribution network of groundwater source is possible only if limitAbstraction = False.  

            logger.info("Using allocation to reduce unmetDemand.")

            # gross/potential demand volume in each cell (unit: m3) - ignore small values (less than 1 m3)
            cellVolGrossDemand = pcr.rounddown(
                                 potential_unmet_demand*self.cellArea)
            
            # demand in each segment/zone (unit: m3)
            segTtlGrossDemand  = pcr.areatotal(cellVolGrossDemand, landSurface.allocSegments)
            
            # total available water volume in each cell - ignore small values (less than 1 m3)
            cellAvlWater = pcr.rounddown(pcr.max(0.00, self.readAvlChannelStorage))
            
            # total available surface water volume in each segment/zone  (unit: m3)
            segAvlWater  = pcr.areatotal(cellAvlWater, landSurface.allocSegments)
            
            # total actual extra surface water abstraction volume in each segment/zone (unit: m3)
            # - limited to available water
            segActWaterAbs = pcr.min(segAvlWater, segTtlGrossDemand)
            
            # actual extra surface water abstraction volume in each cell (unit: m3)
            volActWaterAbstract = vos.getValDivZero(\
                                  cellAvlWater, segAvlWater, vos.smallNumber) * \
                                  segActWaterAbs                                                 
            volActWaterAbstract = pcr.min(cellAvlWater,volActWaterAbstract)                               # unit: m3
            
            # actual extra surface water abstraction in meter 
            extra_surface_water_abstraction    = pcr.ifthen(self.landmask, volActWaterAbstract) /\
                                                                             self.cellArea                # unit: m

            # allocation extra surface water abstraction volume to each cell (unit: m3)
            extraVolAllocSurfaceWaterAbstract  = vos.getValDivZero(\
                                                 cellVolGrossDemand, segTtlGrossDemand, vos.smallNumber) *\
                                                 segActWaterAbs                                           # unit: m3 
            # reduction for unmetDemand (unit: m)
            reduction_for_unmetDemand = pcr.ifthen(self.landmask, 
                                        extraVolAllocSurfaceWaterAbstract / self.cellArea)                # unit: m
            
            if self.debugWaterBalance:
    
                abstraction = pcr.cover(pcr.areatotal(volActWaterAbstract              , landSurface.allocSegments)/landSurface.segmentArea, 0.0)
                allocation  = pcr.cover(pcr.areatotal(extraVolAllocSurfaceWaterAbstract, landSurface.allocSegments)/landSurface.segmentArea, 0.0)
            
                vos.waterBalanceCheck([pcr.ifthen(self.landmask,abstraction)],\
                                      [pcr.ifthen(self.landmask, allocation)],\
                                      [pcr.scalar(0.0)],\
                                      [pcr.scalar(0.0)],\
                                      'extra surface water abstraction - allocation per zone/segment (PS: Error here may be caused by rounding error.)' ,\
                                       True,\
                                       "",threshold=5e-4)

        # correcting surface water abstraction 
        landSurface.actSurfaceWaterAbstract   += extra_surface_water_abstraction                # unit: m
            
        # update channelStorage (m3) after extra_surface_water_abstraction
        self.channelStorage = self.channelStorage -\
                              extra_surface_water_abstraction * self.cellArea
        self.local_input_to_surface_water -= extra_surface_water_abstraction * self.cellArea

        # correcting surface water allocation after reduction of unmetDemand
        landSurface.allocSurfaceWaterAbstract += reduction_for_unmetDemand                      # unit: m

        # recalculating unmetDemand (m)
        groundwater.unmetDemand =  landSurface.totalPotentialGrossDemand -\
                                   landSurface.allocSurfaceWaterAbstract -\
                                   groundwater.allocNonFossilGroundwater

        if self.debugWaterBalance:

            test = pcr.ifthen(groundwater.unmetDemand < 0.0, groundwater.unmetDemand)
            a,b,c = vos.getMinMaxMean(pcr.scalar(test),True)
            threshold = 1e-3
            if abs(a) > threshold or abs(b) > threshold:
                logger.info("WARNING !!!!! Water Balance Error. There is negative unmetDemand ... Min %f Max %f Mean %f" %(a,b,c))

    def simple_update(self,landSurface,groundwater,currTimeStep,meteo):

        # updating timesteps to calculate long and short term statistics values of avgDischarge, avgInflow, avgOutflow, etc.
        self.timestepsToAvgDischarge += 1.

        if self.debugWaterBalance:\
           preStorage = self.channelStorage                                                        # unit: m3

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
        self.nonIrrReturnFlow = landSurface.nonIrrReturnFlowFraction*\
                                landSurface.nonIrrGrossDemand          # m
        nonIrrReturnFlowVol   = self.nonIrrReturnFlow*self.cellArea
        self.channelStorage  += nonIrrReturnFlowVol
        self.local_input_to_surface_water += nonIrrReturnFlowVol

        # water consumption for non irrigation water demand (m) - this water is removed from the water balance
        self.nonIrrWaterConsumption = landSurface.nonIrrGrossDemand - \
                                      self.nonIrrReturnFlow
        # 
        # Note that in case of limitAbstraction = True ; landSurface.nonIrrGrossDemand has been reduced by available water                               
        
        # calculate evaporation from water bodies - this will return self.waterBodyEvaporation (unit: m)
        self.calculate_evaporation(landSurface,groundwater,currTimeStep,meteo)
        
        if self.debugWaterBalance:\
           vos.waterBalanceCheck([self.runoff,\
                                  self.nonIrrReturnFlow],\
                                 [landSurface.actSurfaceWaterAbstract,self.waterBodyEvaporation],\
                                 [           preStorage/self.cellArea],\
                                 [  self.channelStorage/self.cellArea],\
                                   'channelStorage (unit: m) before lake/reservoir outflow',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-4)
        
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
        self.waterBodyStorage = self.WaterBodies.waterBodyStorage
        
        if self.waterTemperature:    
            self.waterBodyStorageTimeBefore = self.waterBodyStorage + self.WaterBodies.waterBodyOutflow
            self.waterBodyOutFlowDay = pcr.cover(\
                           pcr.ifthen(\
                           self.WaterBodies.waterBodyOut,
                           self.WaterBodies.waterBodyOutflow), 0.0)  
        
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

        if self.waterTemperature:
            if currTimeStep.day == 1:
                self.readExtensiveMeteo(currTimeStep)
            self.channelStorageTimeBefore = pcr.max(0.0, self.channelStorage)
            self.energyLocal(meteo, landSurface, groundwater)
            self.energyWaterBody()
                                  
        # ROUTING OPERATION:
        ##########################################################################################################################
        # - this will return new self.channelStorage (but still without waterBodyStorage)
        # - also, this will return self.Q which is channel discharge in m3/day
        #
        if self.method == "accuTravelTime":          self.accuTravelTime() 		
        if self.method == "simplifiedKinematicWave": self.simplifiedKinematicWave(meteo, landSurface, groundwater) 		
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
        
        self.allow_extra_evaporation_and_abstraction = False # This option is still EXPERIMENTAL (and not recommended)
        if self.allow_extra_evaporation_and_abstraction:\
           self.update_with_extra_evaporation_and_unmet_demand_reduction()

        if self.waterTemperature:
            self.energyWaterBodyAverage()           
           
        # return waterBodyStorage to channelStorage  
        self.channelStorage = self.return_water_body_storage_to_channel(self.channelStorage)

    def update_with_extra_evaporation_and_unmet_demand_reduction(self): 
        # This function is still EXPERIMENTAL (and not recommended)

        # add extra evaporation
        self.calculate_extra_evaporation()
        # reduce fossil groundwater storage abstraction (unmetDemand)
        if groundwater.limitAbstraction == False: self.reduce_unmet_demand(landSurface,groundwater,currTimeStep) 

    def calculate_alpha_and_initial_discharge_for_kinematic_wave(self): 

        # calculate alpha (dimensionless), which is the roughness coefficient 
        # - for kinewatic wave (see: http://pcraster.geo.uu.nl/pcraster/4.0.0/doc/manual/op_kinematic.html)
        # - based on wetted area (m2) and wetted perimeter (m), as well as self.beta (dimensionless)
        # - assuming rectangular channel with channel_width = self.wMean and channel_length = self.dist2celllength
        #
        if self.waterTemperature: 
            manIce= pcr.max(self.manningsN,\
              0.0493*pcr.max(0.01,self.channelStorage/(self.dynamicFracWat*self.cellArea))**\
              (-0.23)*self.iceThickness**0.57)
            manningsWithIce= (0.5*(self.manningsN**1.5+manIce**1.5))**(2./3.)
            wetA= self.channelStorage/self.cellLengthFD
            wetP= 2.*wetA/self.wMean+self.wMean
            alpha= (manningsWithIce*wetP**(2./3.)*self.gradient**-0.5)**self.beta
            #TODO alpha = (self.manningsN*wetP**(2./3.)*self.gradient**(-0.5))**self.beta            
        else:
            channel_wetted_area      =   self.water_height * self.wMean                                  # unit: m2
            channel_wetted_perimeter = 2*self.water_height + self.wMean                                  # unit: m  
        #
        
            alpha = (self.manningsN*channel_wetted_perimeter**(2./3.)*self.gradient**(-0.5))**self.beta  # dimensionless
        
        # estimate of channel discharge (m3/s) based on water height
        #
        dischargeInitial = pcr.ifthenelse(alpha > 0.0,\
                                         (self.water_height * self.wMean / alpha)**(1/self.beta),0.0)
        return (alpha, dischargeInitial)    


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

    def kinematic_wave_update(self, landSurface,groundwater,currTimeStep,meteo): 

        logger.info("Using the fully kinematic wave method! ")

        # updating timesteps to calculate long and short term statistics 
        # values of avgDischarge, avgInflow, avgOutflow, etc.
        self.timestepsToAvgDischarge += 1.

        # runoff from landSurface cells (unit: m/day)                   
        self.runoff = landSurface.landSurfaceRunoff +\
                      groundwater.baseflow                              # values are over the entire cell area
        
        # return flow from non irrigation water demand (unit: m/day)    
        self.nonIrrReturnFlow = landSurface.nonIrrReturnFlowFraction*\
                                landSurface.nonIrrGrossDemand           # values are over the entire cell area
        #
        # Note that in case of limitAbstraction = True ; landSurface.nonIrrGrossDemand has been reduced by available water                               
        # 
        # water consumption for non irrigation water demand (m/day) ; this water is removed from the system
        self.nonIrrWaterConsumption = landSurface.nonIrrGrossDemand - \
                                      self.nonIrrReturnFlow             # values are over the entire cell area

        # potential evaporation (unit: m/day)
        self.waterBodyPotEvap = \
         self.calculate_potential_evaporation(landSurface,currTimeStep,\
                                              meteo)                    # values are over the entire cell area

        # surface_water_demand (unit: m/day) 
        # - this is based on landSurface.totalPotentialGrossDemand
        # - the 'landSurface.actSurfaceWaterAbstract' and 'landSurface.allocSurfaceWaterAbstract' will be corrected
        # - however, the "groundwater.nonFossilGroundwaterAbs" and "groundwater.allocNonFossilGroundwater" should remain the same
        # - consequently, the "groundwater.unmetDemand" will be corrected
        #
        surface_water_demand = landSurface.totalPotentialGrossDemand -\
                               groundwater.allocNonFossilGroundwater

        # route only non negative channelStorage (otherwise stay):
        # - note that, the following includes storages in 
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # water height (m)
        self.water_height = pcr.min(self.max_water_height, channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea))
        
        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = \
          self.estimate_length_of_sub_time_step()

        #######################################################################################################################
        for i_loop in range(number_of_loops):
            
            msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
            logger.info(msg)
            
            # initiating accumulated values:
            if i_loop == 0:
                acc_local_input_to_surface_water    = pcr.scalar(0.0)   # unit: m3                            
                acc_water_body_evaporation_volume   = pcr.scalar(0.0)   # unit: m3
                acc_water_body_abstraction_volume   = pcr.scalar(0.0)   # unit: m3
                acc_water_body_allocation_volume    = pcr.scalar(0.0)   # unit: m3
                acc_discharge_volume                = pcr.scalar(0.0)   # unit: m3

            if self.debugWaterBalance:\
                preStorage = pcr.ifthen(self.landmask,\
                             channelStorageForRouting)
                
            # update channelStorageForRouting after runoff and return flow from non irrigation demand
            channelStorageForRouting          += (self.runoff + self.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3
            acc_local_input_to_surface_water  += (self.runoff + self.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3

            # update channelStorageForRouting after evaporation
            water_body_evaporation_volume      = pcr.min(channelStorageForRouting, \
                                                         self.waterBodyPotEvap * self.cellArea * length_of_sub_time_step/vos.secondsPerDay())
            channelStorageForRouting          -= water_body_evaporation_volume
            acc_local_input_to_surface_water  -= water_body_evaporation_volume
            acc_water_body_evaporation_volume += water_body_evaporation_volume
            
            if self.debugWaterBalance:\
                vos.waterBalanceCheck([self.runoff * length_of_sub_time_step/vos.secondsPerDay(), \
                                       self.nonIrrReturnFlow * length_of_sub_time_step/vos.secondsPerDay()],\
                                      [water_body_evaporation_volume/self.cellArea],\
                                      [preStorage/self.cellArea],\
                                      [channelStorageForRouting/self.cellArea],\
                                       'channelStorageForRouting (before abstraction/allocation)',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-5)

            # surface water abstraction and it allocation to meet surface water demand 
            #
            # - potential abstraction during this sub time step
            pot_surface_water_abstract_volume = pcr.rounddown(
                                                surface_water_demand * \
                                                self.cellArea * length_of_sub_time_step/vos.secondsPerDay())         # unit: m3
            #
            # - available_water (m3) for abstraction (during thus sub time step)
            # - note that this includes storage in lakes and/resevoirs
            available_water_volume = pcr.rounddown(
                                     self.estimate_available_volume_for_abstraction(channelStorageForRouting))       # unit: m3
            available_water_volume = pcr.max(0.0, available_water_volume) 
            #
            # - initiating abstraction and allocation variables (unit: m3)
            water_body_abstraction_volume = pcr.scalar(0.0)
            water_body_allocation_volume  = pcr.scalar(0.0)
            #
            ###########################################

            if landSurface.limitAbstraction == True and\
              (landSurface.includeIrrigation or landSurface.domesticWaterDemandOption or landSurface.industrycWaterDemandOption):
        
                msg  = "\n"
                msg += "\n"
                msg += "=================================================================================================================="
                msg += "\n"
                msg += "ERROR!! The option fully kinematicWave cannot be used for a run with water demand that has limitAbstraction = True"
                msg += "\n"
                msg += "=================================================================================================================="
                msg += "\n"
                msg += "\n"
                msg += "\n"
                logger.info(msg)
                water_body_abstraction_volume = None
                water_body_allocation_volume  = None

            if landSurface.usingAllocSegments == False and landSurface.limitAbstraction == False and\
              (landSurface.includeIrrigation or landSurface.domesticWaterDemandOption or landSurface.industryWaterDemandOption):
        
                logger.info("Surface water abstraction is only to satisfy local demand. No network.")
                
                # surface water abstraction 
                water_body_abstraction_volume = pcr.min(available_water_volume, pot_surface_water_abstract_volume)   # unit: m3
                
                # allocating surface water abstraction to surface water demand (no network)                          # unit: m3
                water_body_allocation_volume  = water_body_abstraction_volume
            #
            if landSurface.usingAllocSegments == True and landSurface.limitAbstraction == False and \
              (landSurface.includeIrrigation or landSurface.domesticWaterDemandOption or landSurface.industrycWaterDemandOption):

                logger.info("Using surface water allocation.")

                # gross/potential demand volume in each cell (unit: m3)
                cellVolGrossDemand = pot_surface_water_abstract_volume
            
                # demand in each segment/zone (unit: m3)
                segTtlGrossDemand  = pcr.areatotal(cellVolGrossDemand, landSurface.allocSegments)
            
                # total available water volume in each cell - ignore small values (less than 1 m3)
                cellAvlWater = pcr.max(0.00, available_water_volume)
                cellAvlWater = pcr.rounddown(cellAvlWater)
            
                # total available surface water volume in each segment/zone  (unit: m3)
                segAvlWater  = pcr.areatotal(cellAvlWater, landSurface.allocSegments)
                segAvlWater  = pcr.max(0.00,  segAvlWater)
            
                # total actual surface water abstraction volume in each segment/zone (unit: m3)
                #
                # - not limited to available water - ignore small values (less than 1 m3)
                segActWaterAbs = pcr.rounddown(segTtlGrossDemand)
                # 
                # - limited to available water
                segActWaterAbs = pcr.min(segAvlWater, segActWaterAbs)
            
                # surface water abstraction in each cell (unit: m3)
                volActWaterAbstract = vos.getValDivZero(\
                                      cellAvlWater, segAvlWater, vos.smallNumber) * \
                                      segActWaterAbs                                                 
                water_body_abstraction_volume = pcr.min(cellAvlWater,volActWaterAbstract)
            
                # allocation surface water abstraction volume to each cell (unit: m3)
                water_body_allocation_volume = vos.getValDivZero(\
                                               cellVolGrossDemand, segTtlGrossDemand, vos.smallNumber)*\
                                               segActWaterAbs 

                if self.debugWaterBalance:
    
                    abstraction = pcr.cover(pcr.areatotal(water_body_abstraction_volume, landSurface.allocSegments)/landSurface.segmentArea, 0.0)
                    allocation  = pcr.cover(pcr.areatotal(water_body_allocation_volume , landSurface.allocSegments)/landSurface.segmentArea, 0.0)
            
                    vos.waterBalanceCheck([pcr.ifthen(self.landmask,abstraction)],\
                                          [pcr.ifthen(self.landmask, allocation)],\
                                          [pcr.scalar(0.0)],\
                                          [pcr.scalar(0.0)],\
                                          'extra surface water abstraction - allocation per zone/segment (PS: Error here may be caused by rounding error.)' ,\
                                           True,\
                                           "",threshold=5e-5)

            # - update channelStorageForRouting after abstraction
            channelStorageForRouting          -= water_body_abstraction_volume   # unit: m3
            acc_water_body_abstraction_volume += water_body_abstraction_volume   # unit: m3
            acc_water_body_allocation_volume  += water_body_allocation_volume                                   

            # lakes and reservoirs
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

            # update waterBodyStorage (inflow, storage and outflow)
            self.WaterBodies.update(storageAtLakeAndReservoirs,\
                                    self.timestepsToAvgDischarge,\
                                    self.maxTimestepsToAvgDischargeShort,\
                                    self.maxTimestepsToAvgDischargeLong,\
                                    currTimeStep,\
                                    self.avgDischarge,\
                                    length_of_sub_time_step,\
                                    self.downstreamDemand)

            # waterBodyStorage (m3) after outflow:                               # values given are per water body id (not per cell)
            self.waterBodyStorage = self.WaterBodies.waterBodyStorage

            if self.waterTemperature:    
                self.waterBodyStorageTimeBefore = self.waterBodyStorage + self.WaterBodies.waterBodyOutflow
                self.waterBodyOutFlowDay = pcr.cover(\
                           pcr.ifthen(\
                           self.WaterBodies.waterBodyOut,
                           self.WaterBodies.waterBodyOutflow), 0.0)             
            
            # transfer outflow from lakes and/or reservoirs to channelStorages
            waterBodyOutflow = pcr.cover(\
                               pcr.ifthen(\
                               self.WaterBodies.waterBodyOut,
                               self.WaterBodies.waterBodyOutflow), 0.0)          # unit: m3
            
            # update channelStorage (m3) after waterBodyOutflow (m3)
            channelStorageForRouting += waterBodyOutflow
            # Note that local_input_to_surface_water does not include waterBodyOutflow

            if self.floodPlain:
                self.dynamicFracWat, self.water_height, alpha, dischargeInitial = self.kinAlphaComposite(channelStorageForRouting)
                self.dynamicFracWat = pcr.min(pcr.max(self.dynamicFracWat, self.WaterBodies.fracWat), 1.0)
            else:    
                #alpha parameter and initial discharge variable needed for kinematic wave
                alpha, dischargeInitial = self.calculate_alpha_and_initial_discharge_for_kinematic_wave()
                
            if self.waterTemperature:
                self.waterBodyEvaporation = water_body_evaporation_volume/self.cellArea
                if currTimeStep.day == 1:
                    self.readExtensiveMeteo(currTimeStep)
                self.channelStorageTimeBefore = pcr.max(0.0, channelStorageForRouting)
                self.energyLocal(meteo, landSurface, groundwater, timeSec= length_of_sub_time_step)
                self.energyWaterBody()                
            
            # at the lake/reservoir outlets, use the discharge of water body outflow
            waterBodyOutflowInM3PerSec = pcr.ifthen(\
                                         self.WaterBodies.waterBodyOut,
                                         self.WaterBodies.waterBodyOutflow) / length_of_sub_time_step
            dischargeInitial = pcr.max(pcr.cover(waterBodyOutflowInM3PerSec, dischargeInitial), 0.0)
            dischargeInitial = pcr.ifthen(self.landmask, dischargeInitial)
            
            # discharge (m3/s) based on kinematic wave approximation
            logger.info('start pcr.kinematic')
            self.subDischarge = pcr.kinematic(self.lddMap, dischargeInitial, 0.0, 
                                              alpha, self.beta, \
                                              1, length_of_sub_time_step, self.cellLengthFD)
            logger.info('done')
            
            # update channelStorage (m3)
            storage_change_in_volume  = pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step) - self.subDischarge * length_of_sub_time_step 
            channelStorageForRouting += storage_change_in_volume
            
            if self.waterTemperature:
                # updating channelStorage (after routing)                
                self.channelStorageNow = pcr.max(0.0, channelStorageForRouting)
                
                self.energyRouting(length_of_sub_time_step)
                              
                self.energyWaterBodyAverage()
                
                channelStorageForRouting = self.channelStorageNow
                
                self.channelStorageTimeBefore = pcr.max(0.0, self.channelStorageNow)                
            
            if self.debugWaterBalance:\
                vos.waterBalanceCheck([self.runoff * length_of_sub_time_step/vos.secondsPerDay(), \
                                       self.nonIrrReturnFlow * length_of_sub_time_step/vos.secondsPerDay(),\
                                       waterBodyOutflow/self.cellArea,\
                                       storage_change_in_volume/self.cellArea],\
                                      [water_body_evaporation_volume/self.cellArea,\
                                       water_body_abstraction_volume/self.cellArea,\
                                       self.deltaIceThickness * self.dynamicFracWat],\
                                      [preStorage/self.cellArea - storageAtLakeAndReservoirs/self.cellArea],\
                                      [channelStorageForRouting/self.cellArea],\
                                       'channelStorageForRouting (after routing, without lakes/reservoirs)',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-4)

            # total discharge_volume (m3) until this present i_loop
            acc_discharge_volume += self.subDischarge * length_of_sub_time_step

            # return waterBodyStorage to channelStorage  
            channelStorageForRouting = self.return_water_body_storage_to_channel(channelStorageForRouting)

            # route only non negative channelStorage (otherwise stay):
            channelStorageThatWillNotMove += pcr.ifthenelse(channelStorageForRouting < 0.0, channelStorageForRouting, 0.0)
            channelStorageForRouting       = pcr.max(0.000, channelStorageForRouting)
                
            # update water_height (this will be passed to the next loop)
            if self.floodPlain == False:
                self.water_height = pcr.min(self.max_water_height, channelStorageForRouting / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea))
            
            
		
        #######################################################################################################################
        
        # evaporation (m/day)
        self.waterBodyEvaporation = water_body_evaporation_volume / self.cellArea
        self.remainWaterBodyPotEvap = self.waterBodyPotEvap - self.waterBodyEvaporation
        
        # local input to surface water (m3)
        self.local_input_to_surface_water = acc_local_input_to_surface_water

        # surface water abstraction (unit: m/day)
        landSurface.actSurfaceWaterAbstract = acc_water_body_abstraction_volume / self.cellArea
        
        # surface water allocation (unit: m/day) 
        landSurface.allocSurfaceWaterAbstract = acc_water_body_allocation_volume / self.cellArea
        
        # unmetDemand (unit: m/day)
        groundwater.unmetDemand = landSurface.totalPotentialGrossDemand -\
                                  landSurface.allocSurfaceWaterAbstract -\
                                  groundwater.allocNonFossilGroundwater
        # Note that this must be positive (otherwise, it indicates water balance errors)
        
        if self.debugWaterBalance:
            test = pcr.ifthen(groundwater.unmetDemand < 0.0, groundwater.unmetDemand)
            a,b,c = vos.getMinMaxMean(pcr.scalar(test),True)
            threshold = 1e-3
            if abs(a) > threshold or abs(b) > threshold:
                logger.info("WARNING !!!!! Water balance errors. There is negative unmetDemand ... Min %f Max %f Mean %f" %(a,b,c))

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
        # - long term average diadvectedEnergyPreciprge
        #
        diadvectedEnergyPreciprgeUsed      = pcr.max(0.0, self.discharge)
        diadvectedEnergyPreciprgeUsed      = pcr.max(diadvectedEnergyPreciprgeUsed, self.disChanWaterBody)
        #
        deltaAnoDischarge = diadvectedEnergyPreciprgeUsed - self.avgDischarge  
        self.avgDischarge = self.avgDischarge +\
                            deltaAnoDischarge/\
                            pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)
        self.avgDischarge = pcr.max(0.0, self.avgDischarge)                                    
        self.m2tDischarge = self.m2tDischarge + pcr.abs(deltaAnoDischarge*(diadvectedEnergyPreciprgeUsed - self.avgDischarge))                             
        #
        # - short term average diadvectedEnergyPreciprge
        #
        deltaAnoDischargeShort = diadvectedEnergyPreciprgeUsed - self.avgDischargeShort  
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

        # long term variance and standard deviation of discharge values
        varDischarge = self.m2tDischarge / \
                       pcr.max(1.,\
                       pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)-1.)                             
                       # see: online algorithm on http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        stdDischarge = pcr.max(varDischarge**0.5, 0.0)
        
        # calculate minimum discharge for environmental flow (m3/s)
        minDischargeForEnvironmentalFlow = pcr.max(0.001, self.avgDischarge - 3.5*stdDischarge)
        factor = 0.10 # to avoid flip flop
        minDischargeForEnvironmentalFlow = pcr.max(factor*self.avgDischarge, minDischargeForEnvironmentalFlow)   # unit: m3/s
        return minDischargeForEnvironmentalFlow


    def estimate_available_volume_for_abstraction(self, channelStorage):
        # input: channelStorage    in m3

        # estimate minimum discharge for environmental flow (m3/s)
        minDischargeForEnvironmentalFlow = self.estimate_discharge_for_environmental_flow(channelStorage)
        
        # available channelStorage that can be extracted for surface water abstraction
        readAvlChannelStorage = pcr.max(0.0,channelStorage)                                                             
        
        # safety factor to reduce readAvlChannelStorage
        safety_factor = vos.getValDivZero(pcr.max(0.0, pcr.min(self.avgDischargeShort, self.avgDischarge)), \
                                          minDischargeForEnvironmentalFlow, vos.smallNumber)
        safety_factor = pcr.min(1.00, pcr.max(0.00, safety_factor))
        readAvlChannelStorage = safety_factor * pcr.max(0.0, readAvlChannelStorage)                                                             

        # ignore small volume values - less than 1 m3
        readAvlChannelStorage = pcr.rounddown(readAvlChannelStorage*1.)/1.
        readAvlChannelStorage = pcr.ifthen(self.landmask, readAvlChannelStorage)
        return readAvlChannelStorage       # unit: m3

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

    def returnFloodedFraction(self,channelStorage):
        #-returns the flooded fraction given the flood volume and the associated water height
        # using a logistic smoother near intersections (K&K, 2007)
        #-find the match on the basis of the shortest distance to the available intersections or steps
        deltaXMin= self.floodVolume[self.nrZLevels-1]
        y_i= pcr.scalar(1.)
        k= [pcr.scalar(0.)]*2
        mInt= pcr.scalar(0.)
        for iCnt in range(self.nrZLevels-1,0,-1):
            #-find x_i for current volume and update match if applicable
            # also update slope and intercept
            deltaX= channelStorage-self.floodVolume[iCnt]
            mask= pcr.abs(deltaX) < pcr.abs(deltaXMin)
            deltaXMin= pcr.ifthenelse(mask,deltaX,deltaXMin)
            y_i= pcr.ifthenelse(mask,self.areaFractions[iCnt],y_i)
            k[0]= pcr.ifthenelse(mask,self.kSlope[iCnt-1],k[0])
            k[1]= pcr.ifthenelse(mask,self.kSlope[iCnt],k[1])
            mInt= pcr.ifthenelse(mask,self.mInterval[iCnt],mInt)
        #-all values returned, process data: calculate scaled deltaX and smoothed function
        # on the basis of the integrated logistic functions PHI(x) and 1-PHI(x)
        deltaX= deltaXMin
        deltaXScaled= pcr.ifthenelse(deltaX < 0.,pcr.scalar(-1.),1.)*\
            pcr.min(self.criterionKK,pcr.abs(deltaX/pcr.max(1.,mInt)))
        logInt= self.integralLogisticFunction(deltaXScaled)
        #-compute fractional flooded area and flooded depth
        floodedFraction= pcr.ifthenelse(channelStorage > 0.,\
            pcr.ifthenelse(pcr.abs(deltaXScaled) < self.criterionKK,\
            y_i-k[0]*mInt*logInt[0]+k[1]*mInt*logInt[1],\
            y_i+pcr.ifthenelse(deltaX < 0.,k[0],k[1])*deltaX),0.)
        floodedFraction= pcr.max(0.,pcr.min(1.,floodedFraction))
        floodDepth= pcr.ifthenelse(floodedFraction > 0.,channelStorage/(floodedFraction*self.cellArea),0.)
        floodDepth = pcr.min(self.max_water_height, floodDepth)
        #floodedFraction = pcr.ifthen(self.landmask, pcr.cover(floodedFraction , 0.0))
        #floodDepth = pcr.ifthen(self.landmask, pcr.cover(floodDepth , 0.0))
        return floodedFraction, floodDepth

    def integralLogisticFunction(self,x):
        #-returns a tupple of two values holding the integral of the logistic functions
        # of (x) and (-x)
        logInt=pcr.ln(pcr.exp(-x)+1)
        return logInt,x+logInt

    def kinAlphaStatic(self,channelStorage):
        #-given the total water storage in the cell, returns the Q-A relationiceHeatTransferp
        # for the kinematic wave and required parameters using a static floodplain extent
        if self.waterTemperature: 
            manIce= pcr.max(self.manningsN,\
              0.0493*pcr.max(0.01,self.channelStorage/(self.dynamicFracWat*self.cellArea))**\
              (-0.23)*self.iceThickness**0.57)
            manningsWithIce= (0.5*(self.manningsN**1.5+manIce**1.5))**(2./3.)
            wetA= self.channelStorage/self.channelLength
            wetP= 2.*wetA/self.wMean+self.wMean
            alphaQ = (manningsWithIce*wetP**(2./3.)*self.channelGradient**-0.5)**self.beta
        else:
            wetA= channelStorage/self.channelLength
            wetP= 2.*wetA/self.wMean+self.wMean
            alphaQ= (self.manningsN*wetP**(2./3.)*self.channelGradient**-0.5)**self.beta	  
        #-returning variable of interest: flooded fraction, cross-sectional area
        # and alphaQ
        dischargeInitial = pcr.ifthenelse(alphaQ > 0.0,(wetA / alphaQ)**(1/self.beta),0.0)    
        return alphaQ, dischargeInitial

    def kinAlphaDynamic(self,channelStorage):
        #-given the total water storage in the cell, returns the Q-A relationiceHeatTransferp
        # for the kinematic wave and required parameters
        floodVol= pcr.max(0,channelStorage-self.channelStorageCapacity)
        floodFrac, floodZ= self.returnFloodedFraction(floodVol)
        channelFraction = pcr.max(0.0, pcr.min(1.0,\
             self.wMean * self.cellLengthFD / (self.cellArea)))
        floodFrac += channelFraction
        #-wetted perimeter, cross-sectional area and
        # corresponding mannings' n
        wetA= channelStorage/self.channelLength
        #-wetted perimeter, alpha and composite manning's n
        wetPFld= pcr.max(0.,floodFrac*self.cellArea/self.channelLength-\
            self.wMean)+2.*floodZ
        wetPCh= self.wMean+\
            2.*pcr.min(self.channelDepth,channelStorage/(self.channelLength*self.wMean))
        wetP= wetPFld+wetPCh
        manQ= (wetPCh/wetP*self.manningsN**1.5+\
            wetPFld/wetP*self.floodplainManN**1.5)**(2./3.)
        alphaQ= (manQ*wetP**(2./3.)*self.channelGradient**-0.5)**self.beta        
        # estimate of channel discharge (m3/s) based on water height
        #
        dischargeInitial = pcr.ifthenelse(alphaQ > 0.0,(wetA / alphaQ)**(1/self.beta),0.0)
        #-returning variables of interest: flooded fraction, cross-sectional area
        # and alphaQ
        return floodFrac,floodZ,alphaQ, dischargeInitial

    def kinAlphaComposite(self,channelStorage):
        #-given the total water storage and the mask specifying the occurrence of
        # floodplain conditions, retrns the Q-A relationiceHeatTransferp for the kinematic
        # wave and the associated parameters
        mask = pcr.boolean(1)
        #floodplainStorage= channelStorage
        floodFrac, floodZ, dynamicAlphaQ, dynamicDischargeInitial= self.kinAlphaDynamic(channelStorage)
        staticAlphaQ, staticDischargeInitial = self.kinAlphaStatic(channelStorage)
        floodFrac= pcr.ifthenelse(mask,floodFrac,0.)
        floodZ= pcr.ifthenelse(mask,floodZ,0.)
        alphaQ= pcr.ifthenelse(mask,dynamicAlphaQ,staticAlphaQ)
        dischargeInitial= pcr.ifthenelse(mask,dynamicDischargeInitial,staticDischargeInitial)
        return floodFrac,floodZ,alphaQ, dischargeInitial

    def readExtensiveMeteo(self, currTimeStep):
        self.cloudCover = vos.netcdf2PCRobjClone(\
                                 self.cloudFileNC,'cld',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)/pcr.scalar(100)
                                  
        endYear = int(np.ceil(currTimeStep.year/10.)*10.)
        startYear = endYear - 9
        if self.radFileNC.find("hist") == -1:
          if endYear == 2010:
            startYear = 2006
            if self.radFileNC.lower().find("hadgem2") != -1:
              startYear = 2005
          if endYear > 2099:
            endYear = 2099
        else:
          print "History"
          if endYear == 2010:
            endYear = 2005
          if self.radFileNC.lower().find("hadgem2") != -1 and startYear == 2001:
            endYear = 2004
        if 'rsds' in str(self.radFileNC):
            self.radFile = "%s%d-%d.nc" %(self.radFileNC, startYear, endYear)
            self.radiation =  vos.netcdf2PCRobjClone(\
                                 self.radFile,'rsdsAdjust',\
                                 str(currTimeStep.fulldate),
                                 useDoy=None, 
                                 cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)
        else:
            self.radiation =  vos.netcdf2PCRobjClone(\
                                 self.radFileNC,'RSW',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = "month",
                                 cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)        

        self.vaporPressure = vos.netcdf2PCRobjClone(\
                                 self.vapFileNC,'vap',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)

        if 'ERA-Interim' in str(self.annualTNC):
           self.annualT = vos.netcdf2PCRobjCloneWithoutTime(self.annualTNC,'temperature',self.cloneMap) + pcr.scalar(273.15)
        else:
           self.annualT = vos.netcdf2PCRobjClone(\
                                 self.annualTNC,'tas',\
                                 str(currTimeStep.fulldate),
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)

        #-vapour pressure, used to return atmospheric emissivity [-]                          
        self.atmosEmis= pcr.scalar(1.0) #pcr.min(1.,(0.53+0.0065*(self.vaporPressure)**0.5)*(1.+0.4*self.cloudCover))
        cld1= pcr.roundoff(10*self.cloudCover+0.5)
        cld0= cld1-1
        sun0= pcr.lookupscalar(self.sunFracTBL, cld0)
        deltaSun= (pcr.lookupscalar(self.sunFracTBL,cld1)-sun0)/(cld1-cld0)
        sunFrac= sun0+(10*self.cloudCover-cld0)*deltaSun
        radFrac= self.radCon+self.radSlope*sunFrac
        #radFrac is used when RSW is used (top of atmosphere radiation). Set to 1 if RSDS (surface downward solar radiation) is used
        if 'rsds' in str(self.radFileNC):
            radFrac = 1.
        self.rsw= radFrac*self.radiation        
        
    def energyLocal(self, meteo, landSurface, groundwater, timeSec = vos.secondsPerDay()):
        #-surface water energy fluxes [W/m2]
        # within the current time step
        #-ice formation evaluated prior to routing to account for loss
        # in water height, vertical change in energy evaluated,
        # warming capped to increase to air temperature
        # noIce:    boolean variable indicating the absence of ice,
        #           false when ice is present or when the flux to the
        #           ice layer is negative, indicating growth
        # SHI:      surface energy flux (heat transfer phi) of ice (+: melt)
        # SHW:      heat transfer to surface water
        # SHR:      heat transfer due to short and longwave radiation
        # SHA:      advected energy due to rain or snow
        # SHQ:      advected energy due to lateral inflow
        # SHL:      latent heat flux, based on actual open water evaporation
        #           to be evaluated when actual evap is known
        
        self.temperatureKelvin = meteo.temperature + pcr.scalar(273.15)
        landRunoff = self.runoff
        self.correctPrecip = pcr.scalar(0.0)
        self.dynamicFracWatBeforeRouting = self.dynamicFracWat
        
        landT= pcr.cover(landSurface.directRunoff/landRunoff*pcr.max(self.iceThresTemp+0.1,self.temperatureKelvin-self.deltaTPrec)+\
           landSurface.interflowTotal/landRunoff*pcr.max(self.iceThresTemp+0.1,self.temperatureKelvin)+\
           groundwater.baseflow/landRunoff*pcr.max(self.iceThresTemp+5.0,self.annualT),self.temperatureKelvin)
  
        iceHeatTransfer = self.heatTransferIce * (self.temperatureKelvin - self.iceThresTemp)
        waterHeatTransfer = self.heatTransferIce * (self.iceThresTemp - self.waterTemp)
        noIce = pcr.ifthenelse(self.iceThickness > 0,pcr.boolean(0),\
          pcr.ifthenelse(((iceHeatTransfer-waterHeatTransfer) < 0) & (self.temperatureKelvin < self.iceThresTemp),\
          pcr.boolean(0),pcr.boolean(1)))
        waterHeatTransfer = pcr.ifthenelse(noIce, self.heatTransferWater * (self.temperatureKelvin - self.waterTemp), waterHeatTransfer)
        radiativHeatTransfer = (1 - pcr.ifthenelse(noIce, self.albedoWater, self.albedoSnow)) * self.rsw
        radiativHeatTransfer = radiativHeatTransfer - self.stefanBoltzman * (pcr.ifthenelse(noIce,\
          self.waterTemp, self.iceThresTemp)**4 - self.atmosEmis * self.temperatureKelvin**4)
        advectedEnergyPrecip = pcr.max(0,self.correctPrecip) *\
          pcr.max(self.iceThresTemp+0.1,self.temperatureKelvin-self.deltaTPrec)*self.specificHeatWater*self.densityWater/timeSec
        advectedEnergyInflow = (1-self.dynamicFracWat)/self.dynamicFracWat * landRunoff * landT * self.specificHeatWater * self.densityWater / timeSec
        advectedEnergyInflow -= landSurface.actSurfaceWaterAbstract/self.dynamicFracWat * self.waterTemp * self.specificHeatWater * self.densityWater / timeSec
        #-ice formation
        # DSHI:     net flux for ice layer [W/m2]
        # wi:       thickness of ice cover [m]
        # wh:       available water height
        # deltaIceThickness:      change in thickness per day, melt negative
        #diceHeatTransfer= pcr.ifthenelse(noIce,0,iceHeatTransfer-waterHeatTransfer+advectedEnergyPrecip+radiativHeatTransfer)
        diceHeatTransfer= pcr.ifthenelse(noIce,0,iceHeatTransfer-waterHeatTransfer+radiativHeatTransfer)
        self.deltaIceThickness = -diceHeatTransfer * timeSec / (self.densityWater * self.latentHeatFusion)
        self.deltaIceThickness = pcr.max(-self.iceThickness,self.deltaIceThickness)
        self.deltaIceThickness = pcr.min(self.deltaIceThickness, pcr.max(0,self.maxIceThickness-self.iceThickness))
        #-returning direct gain over water surface
        watQ= pcr.ifthenelse(self.temperatureKelvin >= self.iceThresTemp,pcr.max(0,self.correctPrecip) - self.waterBodyEvaporation/self.dynamicFracWat,0)
        #watQ= pcr.ifthenelse(self.temperatureKelvin >= self.iceThresTemp,self.waterBodyEvaporation/self.dynamicFracWat,0)
        self.waterBodyEvaporation= pcr.ifthenelse(self.temperatureKelvin >= self.iceThresTemp,self.waterBodyEvaporation,0) # TODO move

        #-returning vertical gains/losses [m3] over lakes and channels
        # given their corresponding area
        deltaIceThickness_melt= pcr.max(0,-self.deltaIceThickness)
        #landQCont= pcr.max(0,landFrac/watFrac*landQ)
        verticalGain = (watQ+(landRunoff-landSurface.actSurfaceWaterAbstract)/(self.dynamicFracWat)+deltaIceThickness_melt)
        #channeldStor = verticalGain ### only ice in river
        #lakedStor = self.dynamicFracWat * verticalGain

        #self.waterBodies.waterBodyStorage = pcr.max(0.0, self.waterBodies.waterBodyStorage - lakedStor)
        #self.channelStorage = pcr.max(0.0, self.channelStorage - channeldStor)

        #-net cumulative input for mass balance check [m3]
        #self.dtotStor= channeldStor
        #-change in water storage due to vertical change only
        # used to limit heating and cooling of surface water
        dtotStorLoc= verticalGain
        totStorLoc = self.channelStorageTimeBefore/(self.dynamicFracWat*self.cellArea)-dtotStorLoc
        totStorLoc = self.return_water_body_storage_to_channel(self.channelStorageTimeBefore) / (self.dynamicFracWat*self.cellArea)-dtotStorLoc
        self.totEW = totStorLoc*self.waterTemp*self.specificHeatWater*self.densityWater
        dtotStorLoc = pcr.max(-totStorLoc,dtotStorLoc)
        
        #-latent heat flux due to evapotranspiration [W/m2]
        # and advected energy due to ice melt included here
        # to account for correction in water storage
        latentHeat= -self.waterBodyEvaporation/self.dynamicFracWat*self.densityWater*self.latentHeatVapor/timeSec
        advectedEnergyPrecip= advectedEnergyPrecip+deltaIceThickness_melt*self.iceThresTemp*self.specificHeatWater*self.densityWater/timeSec

        totEWC= totStorLoc * self.specificHeatWater * self.densityWater
        dtotEWC= dtotStorLoc * self.specificHeatWater * self.densityWater
        dtotEWLoc= (waterHeatTransfer + pcr.scalar(noIce) * (radiativHeatTransfer+latentHeat))*timeSec
        dtotEWAdv= (advectedEnergyInflow + pcr.scalar(noIce) * advectedEnergyPrecip)*timeSec
        dtotEWLoc= pcr.min(dtotEWLoc,\
          pcr.max(0,totEWC*self.temperatureKelvin-self.totEW)+pcr.ifthenelse(dtotStorLoc > 0,\
          pcr.max(0,dtotEWC*self.temperatureKelvin-dtotEWAdv),0))
        dtotEWLoc= pcr.ifthenelse(self.waterTemp > self.temperatureKelvin,\
          pcr.min(0,dtotEWLoc),dtotEWLoc)
        dtotEWLoc= pcr.max(dtotEWLoc,\
          pcr.min(0,(totEWC+dtotEWC)*pcr.max(self.temperatureKelvin,self.iceThresTemp+.1)-(self.totEW+dtotEWAdv)))
        #-change in energy storage and resulting temperature
        self.totEW= pcr.max(0,self.totEW+dtotEWLoc+dtotEWAdv)
        self.temp_water_height = pcr.max(1e-16,totStorLoc + dtotStorLoc)
        
        self.waterTemp= pcr.ifthenelse(self.temp_water_height > self.critical_water_height,\
          self.totEW/self.temp_water_height/(self.specificHeatWater*self.densityWater),self.temperatureKelvin)        
        self.waterTemp= pcr.ifthenelse(self.waterTemp < self.iceThresTemp+0.1,self.iceThresTemp+0.1,self.waterTemp)
        
    def energyRouting(self, timeSec):
      
        channelTransFrac = cover(pcr.max(pcr.min((self.subDischarge * timeSec) / self.channelStorageTimeBefore, 1.0),0.0), 0.0)

        dtotEWLat= channelTransFrac*self.volumeEW
        self.volumeEW = (self.volumeEW +pcr.upstream(self.lddMap,dtotEWLat)-dtotEWLat)

    def energyWaterBody(self):
      
        lakeTransFrac = pcr.max(pcr.min((self.WaterBodies.waterBodyOutflow) / (self.waterBodyStorageTimeBefore), 1.0),0.0)
        lakeTransFrac = cover(ifthen(self.WaterBodies.waterBodyOut, lakeTransFrac), 0.0)
    
        energyTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.totEW * self.dynamicFracWat * self.cellArea),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.totEW * self.dynamicFracWat * self.cellArea)
        self.volumeEW = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., energyTotal*lakeTransFrac),energyTotal)
        self.remainingVolumeEW = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * energyTotal), 0.0)

    def energyWaterBodyAverage(self):
      
        self.totalVolumeEW = self.volumeEW + self.remainingVolumeEW

        energyTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.totalVolumeEW),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.totalVolumeEW)
             
        energyAverageLakeCell = cover(energyTotal * self.cellArea \
          /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), energyTotal)
        self.totEW = cover(energyAverageLakeCell /(self.dynamicFracWat * self.cellArea), 1e-16)
            
        self.temp_water_height = self.return_water_body_storage_to_channel(self.channelStorageNow)/(self.dynamicFracWat * self.cellArea)
      
        iceReductionFactor = ifthen(self.landmask, cover(self.dynamicFracWatBeforeRouting/self.dynamicFracWat,1.0))
        
        self.deltaIceThickness = iceReductionFactor * self.deltaIceThickness
        self.deltaIceThickness= pcr.min(self.deltaIceThickness,self.temp_water_height)
        
        self.iceThickness = iceReductionFactor * self.iceThickness

        self.iceThickness= pcr.max(0,self.iceThickness+(self.deltaIceThickness+pcr.ifthenelse(self.temperatureKelvin >= self.iceThresTemp,0,self.correctPrecip)))
        self.iceThickness= pcr.ifthenelse((self.iceThickness <= 0.001) & (self.deltaIceThickness < 0),0,self.iceThickness)
        self.channelStorageNow = self.channelStorageNow - self.deltaIceThickness * self.dynamicFracWat * self.cellArea        
        
        self.waterTemp= pcr.ifthenelse(self.temp_water_height > self.critical_water_height,\
          self.totEW/self.temp_water_height/(self.specificHeatWater*self.densityWater),self.temperatureKelvin)
        self.waterTemp= pcr.ifthenelse(self.waterTemp < self.iceThresTemp+0.1,self.iceThresTemp+0.1,self.waterTemp)
