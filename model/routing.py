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

#PCR-GLOBWB2 and DynQual routing.
#@authors (PCR-GLOBWB2): Edwin H. Sutanudjaja
#@authors (DynQual)    : Edward R. Jones, Niko Wanders

import os
import types
import math
import types
import itertools

from six.moves import map
from copy import deepcopy
from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
from ncConverter import *

import waterBodies

class Routing(object):
    
    def getPseudoState(self):
        result = {}
        return result

    def getVariables(self, names):
        result = {}
        return result
    
    def getState(self):
        result = {}
        
        # Hydrology elements
        result['timestepsToAvgDischarge']    = self.timestepsToAvgDischarge #  day 
        result['channelStorage']             = self.channelStorage          #  m3     ; channel storage, including lake and reservoir storage
        result['readAvlChannelStorage']      = self.readAvlChannelStorage   #  m3     ; readily available channel storage that can be extracted to satisfy water demand
        result['avgDischargeLong']           = self.avgDischarge            #  m3/s   ; long term average discharge
        result['m2tDischargeLong']           = self.m2tDischarge            # (m3/s)^2
        result['avgBaseflowLong']             = self.avgBaseflow              #  m3/s   ; long term average baseflow
        result['riverbedExchange']           = self.riverbedExchange        #  m3/day ; river bed infiltration (from surface water bdoies to groundwater)
        result['waterBodyStorage']           = self.waterBodyStorage        #  m3     ; storages of lakes and reservoirs           # values given are per water body id (not per cell)
        result['avgLakeReservoirOutflowLong'] = self.avgOutflow               #  m3/s   ; long term average lake & reservoir outflow  # values given are per water body id (not per cell)
        result['avgLakeReservoirInflowShort'] = self.avgInflow                #  m3/s   ; short term average lake & reservoir inflow  # values given are per water body id (not per cell)
        result['avgDischargeShort']          = self.avgDischargeShort       #  m3/s   ; short term average discharge
        result['subDischarge']               = self.subDischarge            #  m3/s   ; sub-time step discharge (needed for kinematic wave methods/approaches: i.e. 'kinematicWave' and 'simplifiedKinematicWave')
        
        # QUAlloc
        # for long-term water availability
        if self.using_qualloc:
            result['discharge']              = self.discharge               #  m3/s   ; discharge
            result['runoff']                  = self.runoff                   #  m/day  ; total runoff
        
        # DynQual [added by EdGab]
        # for irrigation return flows
        if self.quality:
            result['avg_irrGrossDemand']     = self.avg_irrGrossDemand      #  m/day  ; average irrigation gross demand    
            result['avg_netLqWaterToSoil']   = self.avg_netLqWaterToSoil    #  m/day  ; average net liquid transferred to the soil
        else:
            logger.info("Irrigation return flows not estimated")
        
        # Water quality elements
        if self.quality:
            result['waterTemperature']        = self.waterTemp              #  K           ; water temperature
            result['salinity']                = self.salinity               #  mg L-1      ; TDS concentration
            result['organic']                 = self.organic                #  mg L-1      ; BOD concentration
            result['pathogen']                = self.pathogen               #  cfu 100mL-1 ; FC concentration
            
            result['iceThickness']            = self.iceThickness           #  m      ; ice thickness
            result['routedTDS']               = self.routedTDS              #  g TDS  ; routed TDS load (for conversion to salinity pollution in mg/L)
            result['routedBOD']               = self.routedBOD              #  g BOD  ; routed BOD load (for conversion to organic pollution mg/L)
            result['routedFC']                = self.routedFC               #  cfu    ; routed FC load (for conversion to pathogen pollution in cfu/100mL)
            
            if self.offlineRun == False and self.calculateLoads and self.loadsPerSector:
                #- Route pollutants individually per sector (for analysis of sectoral contributions)
                #Domestic sector
                result['routedDomTDS']        = self.routedDomTDS           #  g TDS
                result['routedDomBOD']        = self.routedDomBOD           #  g BOD 
                result['routedDomFC']         = self.routedDomFC            #  10^6 cfu   
                #Manufacturing sector
                result['routedManTDS']        = self.routedManTDS           #  g TDS
                result['routedManBOD']        = self.routedManBOD           #  g BOD 
                result['routedManFC']         = self.routedManFC            #  10^6 cfu
                #Urban surface runoff
                result['routedUSRTDS']        = self.routedUSRTDS           #  g TDS
                result['routedUSRBOD']        = self.routedUSRBOD           #  g BOD 
                result['routedUSRFC']         = self.routedUSRFC            #  10^6 cfu
                #Intensive livestock
                result['routedintLivBOD']     = self.routedintLivBOD        #  g BOD 
                result['routedintLivFC']      = self.routedintLivFC         #  10^6 cfu
                #Extensive livestock
                result['routedextLivBOD']     = self.routedextLivBOD        #  g BOD 
                result['routedextLivFC']      = self.routedextLivFC         #  10^6 cfu
                #Irrigation
                result['routedIrrTDS']        = self.routedIrrTDS           #  g TDS
            else:
                logger.info("Water quality elements per sector not simulated")
        else:
            logger.info("Water quality elements not simulated")
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
        if 'includeWaterBodies' in list(iniItems.routingOptions.keys()): 
            if iniItems.routingOptions['includeWaterBodies'] == "False" or\
               iniItems.routingOptions['includeWaterBodies'] == "None":
                self.includeWaterBodies = False
        
        # [added by Gab] dictionary of sectors evaluated
        self.includeSectors = {}
        self.includeSectors['industry'] = False
        self.includeSectors['manufacture'] = False
        if iniItems.waterDemandOptions['includeIndustryWaterDemand'] == "True":
            self.includeSectors['industry'] = True
        elif iniItems.waterDemandOptions['includeManufactureWaterDemand'] == "True":
            self.includeSectors['manufacture'] = True
        
        # [added by EdGab] it seems like these variables are not used
        self.includeLakes = True
        self.includeReservoirs =  True
        
        # local drainage direction
        self.lddMap = vos.readPCRmapClone(\
                          iniItems.routingOptions['lddMap'],
                          self.cloneMap, self.tmpDir, self.inputDir, True)
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        self.lddMap = pcr.lddrepair(self.lddMap)
        
        # landmask
        if iniItems.globalOptions['landmask'] != "None":
           self.landmask = vos.readPCRmapClone(\
                               iniItems.globalOptions['landmask'],
                               self.cloneMap, self.tmpDir, self.inputDir)
        else:
           self.landmask = pcr.defined(self.lddMap)
        self.landmask = pcr.ifthen(pcr.defined(self.lddMap), self.landmask)
        self.landmask = pcr.cover(self.landmask, pcr.boolean(0))   
        
        # ldd mask 
        self.lddMap = pcr.lddmask(self.lddMap, self.landmask)
        
        # cell area (unit: m2)
        self.cellArea = vos.readPCRmapClone(\
                            iniItems.routingOptions['cellAreaMap'],
                            self.cloneMap, self.tmpDir, self.inputDir)
        
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
                                  self.cloneMap, self.tmpDir, self.inputDir)
        
        # parameters needed to estimate channel dimensions/parameters   
        # - used in the method/function 'getRoutingParamAvgDischarge' 
        self.eta = 0.25
        self.nu  = 0.40
        self.tau = 8.00
        self.phi = 0.58
        
        # option to use minimum channel width (m)
        self.minChannelWidth = pcr.scalar(0.0)
        if "minimumChannelWidth" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions['minimumChannelWidth'] != "None":\
               self.minChannelWidth = pcr.cover(vos.readPCRmapClone(\
                                      iniItems.routingOptions['minimumChannelWidth'],
                                      self.cloneMap,self.tmpDir,self.inputDir), 0.0)
        
        # option to use constant/pre-defined channel width (m)
        self.predefinedChannelWidth = None
        if "constantChannelWidth" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions['constantChannelWidth'] != "None":\
               # [EdGab: this variable was called 'constantChannelWidth']
               self.predefinedChannelWidth = pcr.cover(vos.readPCRmapClone(\
                                             iniItems.routingOptions['constantChannelWidth'],
                                             self.cloneMap,self.tmpDir,self.inputDir), 0.0)
        
        # option to use constant/pre-defined channel depth (m)
        self.predefinedChannelDepth = None
        if "constantChannelDepth" in list(iniItems.routingOptions.keys()):
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
                                            (verticalSizeInMeter)**(2))\
                                                                 **(0.5) 
        self.channelLength = self.cellLengthFD
        # 
        # channel length (unit: m) 
        if "channelLength" in list(iniItems.routingOptions.keys()):
            if iniItems.routingOptions['channelLength'] != "None":\
               self.channelLength = pcr.cover(
                                    vos.readPCRmapClone(\
                                    iniItems.routingOptions['channelLength'],
                                    self.cloneMap, self.tmpDir, self.inputDir), self.channelLength)
        
        # dist2celllength in m/arcDegree (needed in the accuTravelTime function): 
        nrCellsDownstream  = pcr.ldddist(self.lddMap,\
                                         pcr.nominal(self.lddMap) == 5, 1.)
        distanceDownstream = pcr.ldddist(self.lddMap,\
                                         pcr.nominal(self.lddMap) == 5,\
                                         self.channelLength)
        channelLengthDownstream = \
                (self.channelLength + distanceDownstream)/\
                (nrCellsDownstream + 1)                 # unit: m
        self.dist2celllength  = channelLengthDownstream /\
                                  self.cellSizeInArcDeg # unit: m/arcDegree
        
        self.distance_to_pit = 0.5 * self.channelLength + distanceDownstream
        
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
        if 'maxiumLengthOfSubTimeStep' in list(iniItems.routingOptions.keys()):
            maxiumLengthOfSubTimeStep = float(iniItems.routingOptions['maxiumLengthOfSubTimeStep'])
            minimum_number_of_sub_time_step  = np.ceil(
                                               vos.secondsPerDay() / maxiumLengthOfSubTimeStep )
            self.limit_num_of_sub_time_steps = max(\
                                               minimum_number_of_sub_time_step, \
                                               self.limit_num_of_sub_time_steps)                                 
        # 
        self.limit_num_of_sub_time_steps = int(self.limit_num_of_sub_time_steps)
        
        # critical water height (m) used to select stable length of sub time step in kinematic wave methods/approaches
        self.critical_water_height = 0.25;  # used in Van Beek et al. (2011)
        
        # assumption for the minimum fracwat value used for calculating water height
        self.min_fracwat_for_water_height = 0.001 # dimensionless
        self.max_water_height = 50000000
        
        # assumption for minimum crop coefficient for surface water bodies 
        self.minCropWaterKC = 0.00
        if 'minCropWaterKC' in list(iniItems.routingOptions.keys()):
            self.minCropWaterKC = float(iniItems.routingOptions['minCropWaterKC'])
        
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
            if 'reductionKK' in list(iniItems.routingOptions.keys()):
               self.reductionKK= float(iniItems.routingOptions['reductionKK'])
            self.criterionKK = 40.0
            if 'criterionKK' in list(iniItems.routingOptions.keys()):
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
            
                if (
                    self.predefinedChannelWidth is None
                    or self.predefinedChannelDepth is None
                ):
                    msg += "The bankfull capacity is estimated from average discharge (5 year long term average)."
                else:
                    msg += "The bankfull capacity is estimated from the given channel depth and channel width."
                    self.usingFixedBankfullCapacity = True
                    self.predefinedBankfullCapacity = self.estimateBankfullCapacity(self.predefinedChannelWidth,\
                                                                                    self.predefinedChannelDepth)
            
                logger.info(msg)
            
            # covering the value
            self.predefinedBankfullCapacity = pcr.cover(self.predefinedBankfullCapacity, pcr.spatial(pcr.scalar(0.0)))    

        # zero fracwat assumption (used for debugging to the version 1)
        self.zeroFracWatAllAndAlways = False
        if iniItems.debug_to_version_one: self.zeroFracWatAllAndAlways = True
        
        # option to limit flood depth (to get rid of unrealistic flood depth)
        self.maxFloodDepth = None
        if 'maxFloodDepth' in list(iniItems.routingOptions.keys()):
            self.maxFloodDepth = vos.readPCRmapClone(iniItems.routingOptions['maxFloodDepth'], self.cloneMap, self.tmpDir, self.inputDir)
        
        # DynQual
        self.quality = False
        if 'quality' in iniItems.routingOptions.keys() and \
           iniItems.routingOptions['quality'] == "True":
          self.quality = True
          logger.info("Water quality modelling initiated.")
        else:
          logger.info("Water quality modelling not initiated.")
        
        print("waterTemperature =",self.quality)
        print("Salinity = ", self.quality)
        print("Organic = ", self.quality)
        print("Dissolved oxygen = ", self.quality)
        print("Pathogen = ", self.quality)
        
        if self.quality:
            
            #Define discharge threshold for estimating concentrations
            self.WQ_discharge_threshold = 0.1 #default of 0.1 m3 s-1
            if 'WQ_discharge_threshold' in iniItems.routingOptions.keys():
                self.WQ_discharge_threshold = float(iniItems.routingOptions['WQ_discharge_threshold'])
            
            ###-Water temperature parameters and file paths
            self.iceThresTemp= pcr.scalar(273.15) # threshold temperature for snowmelt (degK)
            self.densityWater= 1000.0 # density of water [kg/m3]
            self.latentHeatVapor= pcr.scalar(2.5e6) # latent heat of vaporization [J/kg]
            self.latentHeatFusion= pcr.scalar(3.34e5) # latent heat of fusion [J/kg]
            self.specificHeatWater= pcr.scalar(4190.0) # specific heat of water [J/kg/degC]
            self.heatTransferWater= pcr.scalar(20.0) # heat transfer coefficient for water [W/m2/degC]
            self.heatTransferIce= pcr.scalar(8.0) # heat transfer coefficient for ice [W/m2/degC]
            self.albedoWater= pcr.scalar(0.15) # albedo of water [-]
            self.albedoSnow= pcr.scalar(0.50) # albedo of snow and ice [-]         
            self.deltaTPrec= pcr.scalar(1.5) #-energy balance, proxy for temperature of groundwater store: mean annual temperature and reduction in the temperature for falling rain 
            
            self.radCon= 0.25
            self.radSlope= 0.50
            self.stefanBoltzman= 5.67e-8 # [W/m2/K]
            self.maxThresTemp = pcr.scalar(322.15) # max river temperature set to 322.15 K (or 50C)
            
            self.maxIceThickness= 3.0
            self.deltaIceThickness = 0.0

            if iniItems.meteoOptions['sunhoursTable'] != "Default":
                self.sunFracTBL = vos.getFullPath(iniItems.meteoOptions['sunhoursTable'], self.inputDir) #convert cloud cover to sunshine hours (Doornkamp & Pruitt)
            else:               
                self.sunFracTBL = vos.getFullPath("sunhoursfrac.tbl", os.path.abspath(os.path.dirname( __file__ )))
                msg = "Using the default sunhoursfrac.tbl stored on " + self.sunFracTBL
                logger.info(msg) # - sunshine fraction table

            #- Paths to (additional) meterological variables
            self.cloudFileNC = vos.getFullPath(iniItems.meteoOptions['cloudcoverNC'], self.inputDir)
            self.radFileNC = vos.getFullPath(iniItems.meteoOptions['radiationNC'], self.inputDir)
            self.vapFileNC = vos.getFullPath(iniItems.meteoOptions['vaporNC'], self.inputDir)
            self.annualTFileNC = vos.getFullPath(iniItems.meteoOptions['annualAvgTNC'], self.inputDir)
            self.maxIceThickness= 3.0
            self.deltaIceThickness = 0.0
              
            #- Paths to powerplant data
            self.TlmaxNC = vos.getFullPath(iniItems.routingOptions["TlmaxNC"], self.inputDir)
            self.powerplants_fwNC = vos.getFullPath(iniItems.routingOptions["powerplants_fwNC"], self.inputDir)
            self.powerplants_fwfixedNC = vos.getFullPath(iniItems.routingOptions["powerplants_fwfixedNC"], self.inputDir)
            self.powerplants_swNC = vos.getFullPath(iniItems.routingOptions["powerplants_swNC"], self.inputDir)             
            
            ###-Salinity parameters and file paths
            self.backgroundSalinityNC = vos.getFullPath(iniItems.routingOptions['backgroundSalinity'], self.inputDir) #Background TDS concentration (mg l-1)
            self.backgroundSalinity   = vos.netcdf2PCRobjCloneWithoutTime(self.backgroundSalinityNC,"bgTDS",self.cloneMap) # mg l-1
                  
            ###-Organic parameters and file paths
            self.k_BOD = pcr.scalar(0.35)     #first-order degradation coefficient at 20C (van Vliet et al., 2021)
            self.watertempcorrection_BOD = pcr.scalar(1.047)     #temperature correction (van Vliet et al., 2021; Wen et al., 2017)
            
            ###-Dissolved oxygen parameters and file paths
            self.elevation_path = vos.getFullPath(iniItems.landSurfaceOptions['topographyNC'],self.inputDir) #elevation data
            self.elevation = vos.netcdf2PCRobjCloneWithoutTime(self.elevation_path,'dem_average', self.cloneMap, True, None, self.inputDir) #read elevation data
            
            ###-Fecal coliform parameters and file paths
            
            #Temperature dependent decay
            self.darkinactivation_FC = pcr.scalar(0.82)        #days-1; Reder et al., (2015)
            self.watertempcorrection_FC = pcr.scalar(1.07)     #Reder et al., (2015)
            
            #Solar radiation dependent decay
            self.tss = vos.readPCRmapClone(iniItems.routingOptions['TSSmap'],self.cloneMap,self.tmpDir,self.inputDir) #Total suspended solids (from Beusen et al., 2005)
            self.sunlightinactivation_FC = pcr.scalar(0.0068)     #m2 w-1     #Reder et al., (2015) 
            self.attenuation_FC = 0.0931 * self.tss + 0.881       #m-1; Reder et al., (2015)
            
            #Sedimentation
            self.threshold_FC_settlingdepth = pcr.scalar(0.5) #m ; stream depth must exceed 50cm in order for sedimentation to occur
            self.settlingvelocity_FC = pcr.scalar(1.656)    #m/day; Reder et al., (2015)
            
            #- Options required for offline runs
            if iniItems.routingOptions['offlineRun'] == "True":
                self.offlineRun = True
                logger.info("DynQual running in offline configuration")
                
                #Baseflow, interflow and direct runoff required for offline DynQual runs.
                self.baseflowNC = vos.getFullPath(iniItems.routingOptions['baseflowNC'], self.inputDir)
                self.interflowNC = vos.getFullPath(iniItems.routingOptions['interflowNC'], self.inputDir)
                self.directRunoffNC = vos.getFullPath(iniItems.routingOptions['directRunoffNC'], self.inputDir)
                    
                if iniItems.routingOptions['calculateLoads'] == "True":
                    logger.info("WARNING: Cannot calculate pollutant loadings in offline configuration.")
                    logger.info("Switch to online configuration or prescribe loadings directly.")
            
            else:
                self.offlineRun = False
                logger.info("DynQual running online")
             
            # For calculating loadings within model runs   
            if iniItems.routingOptions['calculateLoads'] == "True" and self.offlineRun == False:
                self.calculateLoads = True
                logger.info("Loadings calculated within model run.")
                
                if iniItems.routingOptions['loadsPerSector'] == "True":
                    self.loadsPerSector = True
                    logger.info("Option to report loads per sector enabled")
                else:
                    self.loadsPerSector = False
                
            else:
                self.calculateLoads = False
                self.loadsPerSector = False
                logger.info("Loadings are prescribed (i.e. akin to a forcing) to the model")
            
            if self.calculateLoads:
                
                ###File pathways and constant pollutant loading input data
                
                #Domestic
                self.PopulationNC = vos.getFullPath(iniItems.routingOptions["PopulationNC"], self.inputDir) #gridded population, annual, 5 arc-min (Lange & Geiger, 2020)
                self.Dom_ExcrLoadNC = vos.getFullPath(iniItems.routingOptions["Dom_ExcrLoadNC"], self.inputDir) #average (regional) excretion rates:
                self.DomTDS_ExcrLoad = vos.netcdf2PCRobjCloneWithoutTime(self.Dom_ExcrLoadNC,"Dom_Fixed_TDSload",self.cloneMap) # g/capita/day
                self.DomBOD_ExcrLoad = vos.netcdf2PCRobjCloneWithoutTime(self.Dom_ExcrLoadNC,"Dom_Fixed_BODload",self.cloneMap) # g/capita/day
                self.DomFC_ExcrLoad = vos.netcdf2PCRobjCloneWithoutTime(self.Dom_ExcrLoadNC,"Dom_Fixed_FCload",self.cloneMap)   # cfu/capita/day
                
                #Manufacturing
                self.Man_EfflConcNC = vos.getFullPath(iniItems.routingOptions["Man_EfflConcNC"], self.inputDir) #average (regional) man effluent concentrations:
                self.ManTDS_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.Man_EfflConcNC,"Man_Fixed_TDSload",self.cloneMap) # mg/L [i.e. g/m3]
                self.ManBOD_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.Man_EfflConcNC,"Man_Fixed_BODload",self.cloneMap) # mg/L [i.e. g/m3] 
                self.ManFC_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.Man_EfflConcNC,"Man_Fixed_FCload",self.cloneMap)   # cfu/100ml                
                
                #Urban suface runoff          
                self.UrbanFractionNC = vos.getFullPath(iniItems.routingOptions["UrbanFractionNC"], self.inputDir) #ratio 0 (no urban) - 1 (all urban)
                self.USR_EfflConcNC = vos.getFullPath(iniItems.routingOptions["USR_EfflConcNC"], self.inputDir) #average (regional) USR effluent concentration:
                self.USRTDS_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.USR_EfflConcNC,"USR_Fixed_TDSload",self.cloneMap) # mg/L [i.e. g/m3]
                self.USRBOD_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.USR_EfflConcNC,"USR_Fixed_BODload",self.cloneMap) # mg/L [i.e. g/m3]
                self.USRFC_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.USR_EfflConcNC,"USR_Fixed_FCload",self.cloneMap)   # cfu/100ml 
                
                #Livestock
                self.LivPopulationNC = vos.getFullPath(iniItems.routingOptions["LivPopulationNC"], self.inputDir) #Gridded livestock populations, 2010, 5 arc-min (Gilbert et al., 2018)
                self.Liv_ExcrLoadNC = vos.getFullPath(iniItems.routingOptions["Liv_ExcrLoadNC"], self.inputDir)  #average (regional) excretion rates:
                self.Bufallo_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"bufallo_BODload",self.cloneMap) # g/stock/day
                self.Chicken_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"chicken_BODload",self.cloneMap) # g/stock/day
                self.Cow_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"cow_BODload",self.cloneMap) # g/stock/day
                self.Duck_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"duck_BODload",self.cloneMap) # g/stock/day
                self.Goat_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"goat_BODload",self.cloneMap) # g/stock/day
                self.Horse_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"horse_BODload",self.cloneMap) # g/stock/day
                self.Pig_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"pig_BODload",self.cloneMap) # g/stock/day
                self.Sheep_BODload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"sheep_BODload",self.cloneMap) # g/stock/day
                self.Bufallo_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"bufallo_FCload",self.cloneMap) # cfu/stock/day
                self.Chicken_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"chicken_FCload",self.cloneMap) # cfu/stock/day
                self.Cow_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"cow_FCload",self.cloneMap) # cfu/stock/day
                self.Duck_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"duck_FCload",self.cloneMap) # cfu/stock/day
                self.Goat_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"goat_FCload",self.cloneMap) # cfu/stock/day
                self.Horse_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"horse_FCload",self.cloneMap) # cfu/stock/day
                self.Pig_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"pig_FCload",self.cloneMap) # cfu/stock/day
                self.Sheep_FCload = vos.netcdf2PCRobjCloneWithoutTime(self.Liv_ExcrLoadNC,"sheep_FCload",self.cloneMap) # cfu/stock/day
                
                #Irrigation
                self.Irr_EfflConcNC = vos.getFullPath(iniItems.routingOptions["Irr_EfflConcNC"], self.inputDir) #average soil concentration averaged over the topsoil and subsoil 
                self.IrrTDS_EfflConc = vos.netcdf2PCRobjCloneWithoutTime(self.Irr_EfflConcNC,"soil_TDS",self.cloneMap) # mg/L
                                                    
                #Wastewater pathways and removal efficiencies (treatment [tertiary, secondary, primary], collected but untreated, basic sanitation, open defecation, direct)
                self.WWtPlantsNC = vos.getFullPath(iniItems.routingOptions["WWtPlantsNC"], self.inputDir)
            
            else:
            #- Path to (non-natural) TDS, BOD, FC loading inputs
                self.TDSloadNC = vos.getFullPath(iniItems.routingOptions["TDSloadNC"], self.inputDir)
                self.BODloadNC = vos.getFullPath(iniItems.routingOptions["BODloadNC"], self.inputDir)
                self.FCloadNC = vos.getFullPath(iniItems.routingOptions["FCloadNC"], self.inputDir)
        
        # QUAlloc
        self.using_qualloc = False
        if 'using_qualloc' in iniItems.waterManagementOptions and \
           iniItems.waterManagementOptions['using_qualloc'] == "True":
            self.using_qualloc = True
        
        # get the initialConditions
        # [EdGab: consider moving this line to the top of the function]
        self.getICs(iniItems, initialConditions)
        
        # initiate old style reporting
        # This is still very useful during the 'debugging' process. 
        self.initiate_old_style_routing_reporting(iniItems)

    def getICs(self,iniItems,iniConditions = None):

        if iniConditions == None:
            logger.info("Reading initial conditions from pcraster maps listed in the .ini file")
            # read initial conditions from pcraster maps listed in the ini file (for the first time step of the model; when the model just starts)
            self.timestepsToAvgDischarge = vos.readPCRmapClone(iniItems.routingOptions['timestepsToAvgDischargeIni'] ,self.cloneMap,self.tmpDir,self.inputDir)
            
            self.channelStorage          = vos.readPCRmapClone(iniItems.routingOptions['channelStorageIni']          ,self.cloneMap,self.tmpDir,self.inputDir)
            self.readAvlChannelStorage   = vos.readPCRmapClone(iniItems.routingOptions['readAvlChannelStorageIni']   ,self.cloneMap,self.tmpDir,self.inputDir)
            self.avgDischarge            = vos.readPCRmapClone(iniItems.routingOptions['avgDischargeLongIni']        ,self.cloneMap,self.tmpDir,self.inputDir)
            self.m2tDischarge            = vos.readPCRmapClone(iniItems.routingOptions['m2tDischargeLongIni']        ,self.cloneMap,self.tmpDir,self.inputDir)
            self.avgBaseflow             = vos.readPCRmapClone(iniItems.routingOptions['avgBaseflowLongIni']           ,self.cloneMap,self.tmpDir,self.inputDir)
            self.riverbedExchange        = vos.readPCRmapClone(iniItems.routingOptions['riverbedExchangeIni']        ,self.cloneMap,self.tmpDir,self.inputDir)
            
            # New initial condition variable introduced in the version 2.0.2: avgDischargeShort 
            self.avgDischargeShort       = vos.readPCRmapClone(iniItems.routingOptions['avgDischargeShortIni']       ,self.cloneMap,self.tmpDir,self.inputDir)

            # Initial conditions needed for kinematic wave methods
            self.subDischarge            = vos.readPCRmapClone(iniItems.routingOptions['subDischargeIni']            ,self.cloneMap,self.tmpDir,self.inputDir)
            
            # Initial conditions needed for coupling with QUAlloc
            if self.using_qualloc:
                self.discharge          = vos.readPCRmapClone(iniItems.routingOptions['dischargeIni']                ,self.cloneMap,self.tmpDir,self.inputDir)
                self.runoff              = vos.readPCRmapClone(iniItems.routingOptions['totalRunoffIni']               ,self.cloneMap,self.tmpDir,self.inputDir)
                #self.avgChannelStorage   = vos.readPCRmapClone(iniItems.routingOptions['avgChannelStorageIni']       ,self.cloneMap,self.tmpDir,self.inputDir)
                #self.avgTotalRunoff      = vos.readPCRmapClone(iniItems.routingOptions['avgTotalRunoffIni']           ,self.cloneMap,self.tmpDir,self.inputDir)
                #self.avgStorGroundwater  = vos.readPCRmapClone(iniItems.routingOptions['avgStorGroundwaterIni']      ,self.cloneMap,self.tmpDir,self.inputDir)
            
            # Initial conditions needed for water quality module
            if self.quality:
                self.waterTemp    = vos.readPCRmapClone(iniItems.routingOptions['waterTemperatureIni'],self.cloneMap,self.tmpDir,self.inputDir)
                self.iceThickness   = vos.readPCRmapClone(iniItems.routingOptions['iceThicknessIni'],self.cloneMap,self.tmpDir,self.inputDir)
                self.routedTDS = vos.readPCRmapClone(iniItems.routingOptions['routedTDSIni'],self.cloneMap,self.tmpDir,self.inputDir) #initial conditions for salinity pollution
                self.routedBOD = vos.readPCRmapClone(iniItems.routingOptions['routedBODIni'],self.cloneMap,self.tmpDir,self.inputDir) #initial conditions for organic pollution
                self.routedFC = vos.readPCRmapClone(iniItems.routingOptions['routedFCIni'],self.cloneMap,self.tmpDir,self.inputDir) #initial conditions for pathogen pollution
                
                self.salinity = vos.readPCRmapClone(iniItems.routingOptions['salinityIni'],self.cloneMap,self.tmpDir,self.inputDir) #initial conditions for salinity pollution
                self.organic  = vos.readPCRmapClone(iniItems.routingOptions['organicIni'],self.cloneMap,self.tmpDir,self.inputDir)  #initial conditions for organic pollution
                self.pathogen = vos.readPCRmapClone(iniItems.routingOptions['pathogenIni'],self.cloneMap,self.tmpDir,self.inputDir) #initial conditions for pathogen pollution
                
                # Initial conditions for calculating average irrigation demand and net liquid transferred to the soil for irrigation return flow calculations
                if self.calculateLoads and self.offlineRun == False:
                    self.avg_irrGrossDemand   = vos.readPCRmapClone(iniItems.routingOptions['avg_irrGrossDemandIni'],self.cloneMap,self.tmpDir,self.inputDir)      
                    self.avg_netLqWaterToSoil = vos.readPCRmapClone(iniItems.routingOptions['avg_netLqWaterToSoilIni'], self.cloneMap,self.tmpDir,self.inputDir)
                    
                    # Per water quality sector
                    if self.loadsPerSector:
                        self.routedDomTDS = vos.readPCRmapClone(iniItems.routingOptions['routedDomTDSIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedDomBOD = vos.readPCRmapClone(iniItems.routingOptions['routedDomBODIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedDomFC = vos.readPCRmapClone(iniItems.routingOptions['routedDomFCIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedManTDS = vos.readPCRmapClone(iniItems.routingOptions['routedManTDSIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedManBOD = vos.readPCRmapClone(iniItems.routingOptions['routedManBODIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedManFC = vos.readPCRmapClone(iniItems.routingOptions['routedManFCIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedUSRTDS = vos.readPCRmapClone(iniItems.routingOptions['routedUSRTDSIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedUSRBOD = vos.readPCRmapClone(iniItems.routingOptions['routedUSRBODIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedUSRFC = vos.readPCRmapClone(iniItems.routingOptions['routedUSRFCIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedintLivBOD = vos.readPCRmapClone(iniItems.routingOptions['routedintLivBODIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedintLivFC = vos.readPCRmapClone(iniItems.routingOptions['routedintLivFCIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedextLivBOD = vos.readPCRmapClone(iniItems.routingOptions['routedextLivBODIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedextLivFC = vos.readPCRmapClone(iniItems.routingOptions['routedextLivFCIni'],self.cloneMap,self.tmpDir,self.inputDir)
                        self.routedIrrTDS = vos.readPCRmapClone(iniItems.routingOptions['routedIrrTDSIni'],self.cloneMap,self.tmpDir,self.inputDir)
        
        else:
            logger.info("Reading initial conditions from memory.")
            # read initial conditions from the memory
            self.timestepsToAvgDischarge = iniConditions['routing']['timestepsToAvgDischarge']
            
            self.channelStorage          = iniConditions['routing']['channelStorage']
            self.readAvlChannelStorage   = iniConditions['routing']['readAvlChannelStorage']
            self.avgDischarge            = iniConditions['routing']['avgDischargeLong']
            self.m2tDischarge            = iniConditions['routing']['m2tDischargeLong']
            self.avgBaseflow              = iniConditions['routing']['avgBaseflowLong']
            self.riverbedExchange        = iniConditions['routing']['riverbedExchange']
            self.avgDischargeShort       = iniConditions['routing']['avgDischargeShort']
            
            self.subDischarge            = iniConditions['routing']['subDischarge']
            
            # QUAlloc
            # Initial conditions needed for coupling with QUAlloc
            if self.using_qualloc:
                self.discharge           = iniConditions['routing']['discharge']
                self.runoff               = iniConditions['routing']['runoff']
                #self.avgChannelStorage       = iniConditions['routing']['avgChannelStorage']
                #self.avgTotalRunoff           = iniConditions['routing']['avgTotalRunoff']
                #self.avgStorGroundwater      = iniConditions['routing']['avgStorGroundwater']
            
            # DynQual
            # Initial conditions needed for water quality module
            if self.quality:
                self.waterTemp               = iniConditions['routing']['waterTemperature']
                self.iceThickness            = iniConditions['routing']['iceThickness']
                self.routedTDS               = iniConditions['routing']['routedTDS']
                self.routedBOD               = iniConditions['routing']['routedBOD']
                self.routedFC                = iniConditions['routing']['routedFC']
                
                self.salinity                = iniConditions['routing']['salinity']
                self.organic                 = iniConditions['routing']['organic']
                self.pathogen                = iniConditions['routing']['pathogen']
                
                # Initial conditions for calculating average irrigation demand and net liquid transferred to the soil for irrigation return flow calculations                
                if self.calculateLoads and self.offlineRun == False:
                    self.avg_irrGrossDemand   = iniConditions['routing']['avg_irrGrossDemand']
                    self.avg_netLqWaterToSoil = iniConditions['routing']['avg_netLqWaterToSoil']
                    
                    #Per water quality sector
                    if self.loadsPerSector:
                        self.routedDomTDS    = iniConditions['routing']['routedDomTDS']
                        self.routedDomBOD    = iniConditions['routing']['routedDomBOD']
                        self.routedDomFC     = iniConditions['routing']['routedDomFC']
                        self.routedManTDS    = iniConditions['routing']['routedManTDS']
                        self.routedManBOD    = iniConditions['routing']['routedManBOD'] 
                        self.routedManFC     = iniConditions['routing']['routedManFC']
                        self.routedUSRTDS    = iniConditions['routing']['routedUSRTDS']
                        self.routedUSRBOD    = iniConditions['routing']['routedUSRBOD']
                        self.routedUSRFC     = iniConditions['routing']['routedUSRFC']
                        self.routedintLivBOD = iniConditions['routing']['routedintLivBOD']
                        self.routedintLivFC  = iniConditions['routing']['routedintLivFC']
                        self.routedextLivBOD = iniConditions['routing']['routedextLivBOD']
                        self.routedextLivFC  = iniConditions['routing']['routedextLivFC']
                        self.routedIrrTDS    = iniConditions['routing']['routedIrrTDS']
        
        # Get values associated with landmask
        self.channelStorage        = pcr.ifthen(self.landmask, pcr.cover(self.channelStorage,        0.0))
        self.readAvlChannelStorage = pcr.ifthen(self.landmask, pcr.cover(self.readAvlChannelStorage, 0.0))
        self.avgDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.avgDischarge,          0.0))
        self.m2tDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.m2tDischarge,          0.0))
        self.avgDischargeShort     = pcr.ifthen(self.landmask, pcr.cover(self.avgDischargeShort,     0.0))
        self.avgBaseflow            = pcr.ifthen(self.landmask, pcr.cover(self.avgBaseflow,            0.0))
        self.riverbedExchange      = pcr.ifthen(self.landmask, pcr.cover(self.riverbedExchange,      0.0))
        self.subDischarge          = pcr.ifthen(self.landmask, pcr.cover(self.subDischarge ,         0.0))
        
        self.readAvlChannelStorage = pcr.min(self.readAvlChannelStorage, self.channelStorage)
        self.readAvlChannelStorage = pcr.max(self.readAvlChannelStorage, 0.0)
        
        # QUAlloc
        if self.using_qualloc:
            self.discharge = pcr.ifthen(self.landmask, pcr.cover(self.discharge, 0.0))
            self.runoff     = pcr.ifthen(self.landmask, pcr.cover(self.runoff,     0.0))
            #self.avgChannelStorage  = pcr.ifthen(self.landmask, pcr.cover(self.avgChannelStorage,     0.0))
            #self.avgTotalRunoff      = pcr.ifthen(self.landmask, pcr.cover(self.avgTotalRunoff,         0.0))
            #self.avgStorGroundwater = pcr.ifthen(self.landmask, pcr.cover(self.avgStorGroundwater,    0.0))
        
        # DynQual
        if self.quality:
            self.waterTemp    = pcr.ifthen(self.landmask, pcr.cover(self.waterTemp, 0.0))
            self.iceThickness = pcr.ifthen(self.landmask, pcr.cover(self.iceThickness , 0.0))
            self.DO = (1-0.0001148*self.elevation)*exp(-139.34411+(157570.1)/(self.waterTemp)-(66423080.)/(self.waterTemp**2)+(12438000000.)/(self.waterTemp**3)-(862194900000.)/(self.waterTemp**4))
            self.channelStorageTimeBefore = self.channelStorage      
            self.totEW = self.channelStorage * self.waterTemp*self.specificHeatWater * self.densityWater
            self.temp_water_height = yMean = self.eta * pow (self.avgDischarge, self.nu)
            self.routedTDS = pcr.ifthen(self.landmask, pcr.cover(self.routedTDS, 0.0))
            self.routedBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedBOD, 0.0))
            self.routedFC = pcr.ifthen(self.landmask, pcr.cover(self.routedFC,  0.0))
            self.salinity = pcr.ifthen(self.landmask, pcr.cover(self.salinity, 0.0))
            self.organic  = pcr.ifthen(self.landmask, pcr.cover(self.organic, 0.0))
            self.pathogen = pcr.ifthen(self.landmask, pcr.cover(self.pathogen,  0.0))
            
            #Per water quality sector
            if self.calculateLoads and self.offlineRun == False: 
                self.avg_irrGrossDemand   = pcr.ifthen(self.landmask, pcr.cover(self.avg_irrGrossDemand, 0.0))
                self.avg_netLqWaterToSoil = pcr.ifthen(self.landmask, pcr.cover(self.avg_netLqWaterToSoil, 0.0))
                
                if self.loadsPerSector:          
                    self.routedDomTDS = pcr.ifthen(self.landmask, pcr.cover(self.routedDomTDS, 0.0))
                    self.routedDomBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedDomBOD, 0.0))
                    self.routedDomFC = pcr.ifthen(self.landmask, pcr.cover(self.routedDomFC, 0.0))
                    self.routedManTDS = pcr.ifthen(self.landmask, pcr.cover(self.routedManTDS, 0.0))
                    self.routedManBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedManBOD, 0.0))
                    self.routedManFC = pcr.ifthen(self.landmask, pcr.cover(self.routedManFC, 0.0))
                    self.routedUSRTDS = pcr.ifthen(self.landmask, pcr.cover(self.routedUSRTDS, 0.0))
                    self.routedUSRBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedUSRBOD, 0.0))
                    self.routedUSRFC = pcr.ifthen(self.landmask, pcr.cover(self.routedUSRFC, 0.0))
                    self.routedintLivBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedintLivBOD, 0.0))
                    self.routedintLivFC = pcr.ifthen(self.landmask, pcr.cover(self.routedintLivFC, 0.0))
                    self.routedextLivBOD = pcr.ifthen(self.landmask, pcr.cover(self.routedextLivBOD, 0.0))
                    self.routedextLivFC = pcr.ifthen(self.landmask, pcr.cover(self.routedextLivFC, 0.0))
                    self.routedIrrTDS = pcr.ifthen(self.landmask, pcr.cover(self.routedIrrTDS, 0.0))
        
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
            if iniItems.routingOptions['waterBodyStorageIni'] is not None:
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
        if self.waterBodyStorage is not None:
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
            areaFractions = list(map(float, str(iniItems.routingOptions['relativeElevationLevels']).split(',')))
            print(areaFractions)
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
        if self.predefinedChannelWidth is not None:
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
        outlets = pcr.cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyOut) > 0, pcr.spatial(pcr.boolean(1))), pcr.spatial(pcr.boolean(0)))
        distance_to_outlets = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                              pcr.ldddist(self.lddMap, outlets, pcr.scalar(1.0)))
        
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

    def simplifiedKinematicWave(self, meteo, landSurface, groundwater): 
        """
        The 'simplifiedKinematicWave':
        1. First, assume that all local fluxes has been added to 'channelStorage'. This is done outside of this function/method.
        2. Then, the 'channelStorage' is routed by using 'pcr.kinematic function' with 'lateral_inflow' = 0.0.
        """

        ##########################################################################################################################
        
        logger.info("Using the simplifiedKinematicWave method!")
        
        # route only non negative channelStorage (otherwise stay):
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # estimate of water height (m)
        # - needed to estimate the length of sub-time step and 
        #     also to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
        self.water_height = pcr.min(self.max_water_height, \
                                    channelStorageForRouting /\
                                    (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea))

        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = self.estimate_length_of_sub_time_step()

        for i_loop in range(number_of_loops):
            
            #msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
            #logger.info(msg)
            
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
            
            # [added by EdGab]
            if self.quality:
                self.channelStorageNow = pcr.max(0.0, channelStorageForRouting)
                self.qualityRouting(length_of_sub_time_step)
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
        
        # [added by EdGab] set a water height for the first time-step
        if currTimeStep.timeStepPCR == 1:
            _, self.water_height = self.returnFloodedFraction(self.channelStorage)
        
        # option to use constant channel depth (m)
        if self.predefinedChannelDepth is not None:
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

        if self.floodPlain:
            # riverine flood volume (m3)
            # - assume/simplify that lakes/reservoir cells never flooded
            self.floodInundationVolume = pcr.ifthenelse(
                pcr.cover(self.WaterBodies.waterBodyIds, 0) == 0,
                pcr.max(0.0, self.channelStorage - self.channelStorageCapacity),
                0.0,
            )
            #
            # - ignore small floods with small or not significant inundation fractions:
            self.floodInundationVolume = pcr.ifthenelse(
                self.dynamicFracWat > self.min_fracwat_for_water_height,
                self.floodInundationVolume,
                0.0,
            )
            self.floodInundationVolume = pcr.cover(self.floodInundationVolume, 0.0)
            self.floodInundationVolume = pcr.max(
                0.0, pcr.min(self.channelStorage, self.floodInundationVolume)
            )
            self.floodInundationVolume = pcr.ifthen(
                self.landmask, self.floodInundationVolume
            )

        # lake and reservoir fraction
        self.dynamicFracWat_excluding_flooding  = pcr.cover(\
                                                           pcr.min(1.0, self.WaterBodies.fracWat), 0.0)
        # - plus fraction of channel (excluding its excess above bankfull capacity) 
        self.dynamicFracWat_excluding_flooding += pcr.max(0.0, 1.0 - self.dynamicFracWat_excluding_flooding) * pcr.max(self.channelFraction, 0.0)
        # - fraction of lake and reservoir, as well as channel, but excluding flood
        self.dynamicFracWat_excluding_flooding  = pcr.ifthen(self.landmask, pcr.min(1.0, self.dynamicFracWat_excluding_flooding))

        # TODO: Calculate flood fraction 

        # estimate volume of water that can be extracted for abstraction in the next time step
        self.readAvlChannelStorage = pcr.max(0.0, self.estimate_available_volume_for_abstraction(self.channelStorage))
        
        # water body balance check
        self.waterBodyBalance = self.WaterBodies.waterBodyBalance
        
        # total runoff (m) from local land surface runoff and local changes in water bodies 
        self.totalRunoff = self.local_input_to_surface_water / self.cellArea
        
        # calculate the statistics of long and short term flow values
        self.calculate_statistics(groundwater, landSurface)
        
        # old-style reporting
        self.old_style_routing_reporting(currTimeStep)                 # TODO: remove this one


    def calculate_potential_evaporation(self,landSurface,currTimeStep,meteo,definedDynamicFracWat = None):

        if self.no_zero_crop_water_coefficient == False: self.waterKC = 0.0
        
        # potential evaporation from water bodies
        # current principle: 
        # - if landSurface.actualET < waterKC * meteo.referencePotET * self.fracWat
        #   then, we add more evaporation
        #
        if ((currTimeStep.day == 1) or (currTimeStep.timeStepPCR == 1)) and self.no_zero_crop_water_coefficient:
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
        
        # remaining potential evaporation (m) from water bodies
        self.remainWaterBodyPotEvap = pcr.max(0.0, self.waterBodyPotEvap - self.waterBodyEvaporation)

    def calculate_evaporation_routing_only(self,currTimeStep,meteo):

        # calculate potential evaporation from water bodies OVER THE ENTIRE CELL AREA (m/day) ; not only over surface water bodies
        self.waterBodyPotEvap = self.calculate_potential_evaporation_routing_only(currTimeStep,meteo)
        
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


    def return_flows_to_wastewater_treatment_plants(self, currTimeStep, landSurface):
        
        # wastewater treatment plants: IDs
        self.WWt_plantID = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC, \
                                 'plant_id',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True,\
                                 specificFillValue = None) #wastewater treatment plant [point] locations
        self.WWt_plantID = pcr.nominal(self.WWt_plantID)
        
        # wastewater treatment plants: service areas
        self.WWt_zoneID = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,\
                                 'zone_id',\
                                 str(currTimeStep.fulldate),\
                                 useDoy = None,\
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True,\
                                 specificFillValue = None) #wastewater treatment plant service zones
        self.WWt_zoneID = pcr.nominal(self.WWt_zoneID)
        
        # define return flow as sum of domestic and manufacturing return flows only
        self.nonIrrReturnFlow = landSurface.nonIrrReturnFlowVolumePerSector['domestic'] + \
                                landSurface.nonIrrReturnFlowVolumePerSector['manufacture']
        
        # re-direction of return flow to the water treatment plants locations
        self.nonIrrReturnFlow = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.nonIrrReturnFlow,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID,  # Accumulate water over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.nonIrrReturnFlow,
                                   0), 
                    self.WWt_zoneID 
                ),  # Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #m3 day
        
        # return flow from non irrigation water demand
        # - calculated in the landSurface.py module
        # (units: m3)
        self.nonIrrReturnFlow = self.nonIrrReturnFlow + \
                                landSurface.nonIrrReturnFlowVolumePerSector['livestock'] + \
                                landSurface.nonIrrReturnFlowVolumePerSector['thermoelectric'] + \
                                landSurface.nonIrrReturnFlowVolumePerSector['industry']



    def simple_update(self, landSurface, groundwater, currTimeStep, meteo):
        
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
        
        # re-direction of return flow to the water treatment plants locations (unit: m3)
        if self.quality and self.calculateLoads:
            self.return_flows_to_wastewater_treatment_plants(currTimeStep, landSurface)
        else:
            self.nonIrrReturnFlow = landSurface.nonIrrReturnFlowVolume
        
        # include return flows to channel storage (unit: m3)
        self.channelStorage  += self.nonIrrReturnFlow
        self.local_input_to_surface_water += self.nonIrrReturnFlow
        
        # calculate evaporation from water bodies - this will return self.waterBodyEvaporation (unit: m)
        self.calculate_evaporation(landSurface, groundwater, currTimeStep, meteo)
        
        if self.debugWaterBalance:\
           vos.waterBalanceCheck([self.runoff,\
                                  self.nonIrrReturnFlow / self.cellArea],\
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
        storageAtLakeAndReservoirs = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                               self.channelStorage)
        storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs,0.0)
        
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
        
        if self.quality:
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
        
        if self.quality:
            # Input data provided at daily resolution, unless otherwise adjusted in function
            self.readExtensiveMeteo(currTimeStep)
            
            # Input data for pollutant loadings typically provided at monthly resolution
            if currTimeStep.day == 1:
                #self.readPowerplantData(currTimeStep)
                
                if self.calculateLoads:
                    self.readPollutantLoadingsInputData(currTimeStep)  
            
            # Pollutant loadings calculated (or read in) at daily resolution, unless otherwise adjusted in function
            if self.calculateLoads:
                self.calculatePollutantLoadings(currTimeStep,landSurface,groundwater)
            else:
                self.readPollutantLoadings(currTimeStep)  
            
            #self.calculatePowerplantDemands(currTimeStep)
            self.powerplants_fw_rf = landSurface.water_demand.water_demand_thermoelectric.powerplants_fw_rf
            self.min_Tlmax_dTlmax  = landSurface.water_demand.water_demand_thermoelectric.min_Tlmax_dTlmax
            self.PowTwload = pcr.cover(self.powerplants_fw_rf * self.specificHeatWater * self.densityWater * self.min_Tlmax_dTlmax, 0.) #heat dumps from water-temperature dependent powerplants (J s-1)
            
            self.channelStorageTimeBefore = pcr.max(0.0, self.channelStorage)
            self.qualityLocal(meteo, landSurface, groundwater, currTimeStep)
            self.qualityWaterBody()
        
        # ROUTING OPERATION:
        ##########################################################################################################################
        # - this will return new self.channelStorage (but still without waterBodyStorage)
        # - also, this will return self.Q which is channel discharge in m3/day
        if self.method == "accuTravelTime":          self.accuTravelTime()      
        if self.method == "simplifiedKinematicWave": self.simplifiedKinematicWave(meteo, landSurface, groundwater)
        #
        # channel discharge (m3/s): for current time step
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
        ##########################################################################################################################
        
        if self.quality:
            self.qualityWaterBodyAverage(currTimeStep)    
        
        # return waterBodyStorage to channelStorage  
        self.channelStorage = self.return_water_body_storage_to_channel(self.channelStorage)
        
        if self.quality:
            self.estimate_concentrations()


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

    def returnInundationFractionAndFloodDepth(self, channelStorage):
        
        # flood/innundation depth above the flood plain (unit: m)
        floodDepth = 0.0
        
        # channel and flood innundated fraction (dimensionless, the minimum value is channelFraction)
        inundatedFraction = self.channelFraction
        
        if self.floodPlain:
            
            #msg = 'Calculate channel inundated fraction and flood inundation depth above the floodplain.'
            #logger.info(msg)
            
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
            inundatedFraction = pcr.max(0.,pcr.min(1.0, inundatedFraction))  # dimensionless
            
            # calculate flooded/inundated depth (unit: m) above the floodplain 
            #_- it will be zero if excessVolume == 0 
            floodDepth  = pcr.ifthenelse(inundatedFraction > 0., \
                          excessVolume/(pcr.max(self.min_fracwat_for_water_height, inundatedFraction)*self.cellArea),0.)  # unit: m
            
            # - maximum flood depth
            if self.maxFloodDepth is not None:
                floodDepth = pcr.max(0.0, pcr.min(self.maxFloodDepth, floodDepth))
        
        return inundatedFraction, floodDepth

    def return_water_body_storage_to_channel(self, channelStorage):
        
        # return waterBodyStorage to channelStorage  
        waterBodyStorageTotal = \
             pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                        pcr.areaaverage(\
                                        pcr.ifthen(self.landmask,self.WaterBodies.waterBodyStorage),\
                                        pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)) + \
                        pcr.areatotal(\
                                      pcr.cover(pcr.ifthen(self.landmask,channelStorage), 0.0),\
                                      pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)))
        #
        waterBodyStoragePerCell = \
             waterBodyStorageTotal * self.cellArea /\
             pcr.areatotal(pcr.cover(self.cellArea, 0.0),\
                           pcr.ifthen(self.landmask,\
                                      self.WaterBodies.waterBodyIds))
        #
        waterBodyStoragePerCell = \
             pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                        waterBodyStoragePerCell)                                        # unit: m3
        #
        channelStorage = pcr.ifthen(self.landmask,\
                                    pcr.cover(waterBodyStoragePerCell,channelStorage))  # unit: m3
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
        
        # runoff from landSurface cells (unit: m/day)
        self.runoff = landSurface.landSurfaceRunoff +\
                      groundwater.baseflow                              # values are over the entire cell area
        
        # route only non negative channelStorage (otherwise stay):
        # - note that, the following includes storages in 
        channelStorageThatWillNotMove = pcr.ifthenelse(self.channelStorage < 0.0, self.channelStorage, 0.0)
        
        # channelStorage that will be given to the ROUTING operation:
        channelStorageForRouting = pcr.max(0.0, self.channelStorage)                              # unit: m3
        
        # estimate of water height (m)
        # - here it is needed to estimate the length of sub-time step
        self.water_height = channelStorageForRouting /\
                           (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)
        
        # estimate the length of sub-time step (unit: s):
        length_of_sub_time_step, number_of_loops = self.estimate_length_of_sub_time_step()
        
        #######################################################################################################################
        for i_loop in range(number_of_loops):
            
            msg = "sub-daily time step "+str(i_loop+1)+" from "+str(number_of_loops)
            logger.info(msg)
            
            if self.debugWaterBalance:\
                preStorage = pcr.ifthen(self.landmask,\
                                        channelStorageForRouting)
            
            # initiating accumulated values:
            if i_loop == 0:
                acc_local_input_to_surface_water    = pcr.scalar(0.0)   # unit: m3
                acc_water_body_evaporation_volume   = pcr.scalar(0.0)   # unit: m3
                acc_discharge_volume                = pcr.scalar(0.0)   # unit: m3
            
            # update channelStorageForRouting after runoff and return flow from non irrigation demand
            channelStorageForRouting          += (self.runoff + landSurface.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3
            acc_local_input_to_surface_water  += (self.runoff + landSurface.nonIrrReturnFlow) * \
                                                  self.cellArea * length_of_sub_time_step/vos.secondsPerDay()  # unit: m3
            
            # potential evaporation within the sub-time step ; unit: m, values are over the entire cell area 
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
                                       'channelStorageForRouting (local fluxes)',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-5)
            
            # at cells where lakes or reservoirs defined, move channelStorageForRouting (m3) to waterBodyStorage
            storageAtLakeAndReservoirs = \
             pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                                   channelStorageForRouting)
            storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs, 0.0)
            
            # - move only non negative values and use rounddown values
            storageAtLakeAndReservoirs = pcr.max(0.00, pcr.rounddown(storageAtLakeAndReservoirs))
            channelStorageForRouting = pcr.max(0.0, channelStorageForRouting - storageAtLakeAndReservoirs)
            
            # update waterBodyStorage (inflow, storage and outflow)
            self.WaterBodies.update(storageAtLakeAndReservoirs,\
                                    self.timestepsToAvgDischarge,\
                                    self.maxTimestepsToAvgDischargeShort,\
                                    self.maxTimestepsToAvgDischargeLong,\
                                    currTimeStep,\
                                    self.avgDischarge,\
                                    length_of_sub_time_step,\
                                    self.downstreamDemand)
            
            # - waterBodyOutflow (m3/length_of_sub_time_step) from lakes or reservoirs at outlet cells
            waterBodyOutflow = pcr.cover(\
                               pcr.ifthen(\
                               self.WaterBodies.waterBodyOut,
                               self.WaterBodies.waterBodyOutflow), 0.0)
            waterBodyOutflow = pcr.ifthen(self.landmask, waterBodyOutflow)
            
            # - waterBodyOutflow in m3/s at lake/reservoir outlet cells
            waterBodyOutflowInM3PerSec = waterBodyOutflow / length_of_sub_time_step
            
            # - waterBodyStorage (m3) after outflow (values given are per water body id (not per cell))
            self.waterBodyStorage = pcr.ifthen(self.landmask, self.WaterBodies.waterBodyStorage)
            
            # update channelStorage (m3) after waterBodyOutflow (m3) - Note that local_input_to_surface_water does not include waterBodyOutflow.            
            # - update channelStorage (m3)  - after waterBodyOutflow (m3)
            #~ storage_change_in_volume = waterBodyOutflow                                                 # NOT CORRECT
            #~ storage_change_in_volume = pcr.upstream(self.lddMap, waterBodyOutflow) - waterBodyOutflow   # NOT CORRECT
            storage_change_in_volume    = pcr.upstream(self.lddMap, waterBodyOutflow)                      # PS: I think this is the correct one. 
            channelStorageForRouting   += storage_change_in_volume 
            
            # estimate of water height (m)
            # - here it is needed to estimate the channel wetted area (for the calculation of alpha and dischargeInitial)
            # - this water height is only for the one in channels (it does not include the one for lake and reservoirs)
            self.water_height = channelStorageForRouting /\
                               (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)
            # PS: Disactivate this line gives negative channelStorage (most likely due too high water heights in lakes and reservoirs).                  
                               
            
            # alpha parameter and initial/estimate discharge variable - needed for kinematic wave calculation 
            alpha, dischargeInitial = \
                   self.calculate_alpha_and_initial_discharge_for_kinematic_wave(channelStorageForRouting, \
                                                                                 self.water_height, \
                                                                                 self.innundatedFraction, self.floodDepth) 
            
            # for lakes and reservoir outlet cells, set discharge estimate (dischargeInitial) to waterBodyOutflowInM3PerSec
            dischargeInitial = pcr.cover(\
                               pcr.ifthen(\
                               self.WaterBodies.waterBodyOut, waterBodyOutflowInM3PerSec), dischargeInitial)
            
            # also for the ones with zero channelStorageForRouting
            dischargeInitial = pcr.ifthenelse(channelStorageForRouting > 0.0, dischargeInitial, 0.0)
            
            # discharge estimate (dischargeInitial) in m3/s
            dischargeInitial = pcr.cover(dischargeInitial, 0.0)
            dischargeInitial = pcr.ifthen(self.landmask, dischargeInitial)
            
            # discharge (m3/s) based on the KINEMATIC WAVE approximation
            self.subDischarge = pcr.kinematic(self.lddMap, dischargeInitial, 0.0, 
                                              alpha, self.beta, \
                                              1, length_of_sub_time_step, self.channelLength)
            self.subDischarge = pcr.max(0.0, pcr.cover(self.subDischarge, 0.0))
            
            # for lakes and reservoir cells, set discharge to zero
            self.subDischarge = pcr.cover(\
                                pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., pcr.scalar(0.0)), self.subDischarge)
            
            # make sure that we do not get negative channel storage
            self.subDischarge = pcr.min(self.subDischarge * length_of_sub_time_step, \
                                pcr.max(0.0, channelStorageForRouting + pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step)))/length_of_sub_time_step
            
            # update channelStorage (m3) after lateral flows in channels
            storage_change_in_volume  = pcr.upstream(self.lddMap, self.subDischarge * length_of_sub_time_step) - self.subDischarge * length_of_sub_time_step 
            channelStorageForRouting += storage_change_in_volume
            
            # return waterBodyStorage to channelStorage
            channelStorageForRouting = self.return_water_body_storage_to_channel(channelStorageForRouting)
            
            # include waterBodyOutflowInM3PerSec to subDischarge
            self.subDischarge += waterBodyOutflowInM3PerSec
            self.subDischarge = pcr.ifthen(self.landmask, self.subDischarge)
            
            # total discharge_volume (m3) until this present i_loop
            acc_discharge_volume += self.subDischarge * length_of_sub_time_step
            
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
            
            # for the next calculation and loop, route only non negative channelStorage
            channelStorageThatWillNotMove += pcr.ifthenelse(channelStorageForRouting < 0.0, channelStorageForRouting, 0.0)
            channelStorageForRouting       = pcr.max(0.000, channelStorageForRouting)
            
            # estimate water_height
            # - this water height includes the one for lake and reservoirs
            self.water_height = pcr.max(0.0, channelStorageForRouting) / (pcr.max(self.min_fracwat_for_water_height, self.dynamicFracWat) * self.cellArea)
        
        #######################################################################################################################
        
        # evaporation (m/day)
        self.waterBodyEvaporation = acc_water_body_evaporation_volume / self.cellArea
        
        # local input to surface water (m3)
        self.local_input_to_surface_water += acc_local_input_to_surface_water

        # channel discharge (m3/day) = self.Q
        self.Q = acc_discharge_volume

        # updating channelStorage (after routing)
        self.channelStorage = channelStorageForRouting

        # return channelStorageThatWillNotMove to channelStorage:
        self.channelStorage += channelStorageThatWillNotMove
        
        # channel discharge (m3/s): for current time step
        self.discharge = self.Q / vos.secondsPerDay()
        self.discharge = pcr.max(0., self.discharge)                   # reported channel discharge cannot be negative
        self.discharge = pcr.ifthen(self.landmask, self.discharge)
        
        self.disChanWaterBody = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                                pcr.areamaximum(self.discharge,self.WaterBodies.waterBodyIds))
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)
        
        self.disChanWaterBody = pcr.max(0.,self.disChanWaterBody)      # reported channel discharge cannot be negative


    def calculate_statistics(self, groundwater, landSurface):
        
        # short term average inflow (m3/s) and long term average outflow (m3/s) from lake and reservoirs
        self.avgInflow  = pcr.ifthen(self.landmask, pcr.cover(self.WaterBodies.avgInflow , 0.0)) 
        self.avgOutflow = pcr.ifthen(self.landmask, pcr.cover(self.WaterBodies.avgOutflow, 0.0))
        
        # short term and long term average discharge (m3/s)
        # - see: online algorithm on http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        
        # - long term average disharge
        dishargeUsed      = pcr.max(0.0, self.discharge)
        dishargeUsed      = pcr.max(dishargeUsed, self.disChanWaterBody)
        
        deltaAnoDischarge = dishargeUsed - self.avgDischarge  
        self.avgDischarge = self.avgDischarge +\
                            deltaAnoDischarge/\
                            pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)
        self.avgDischarge = pcr.max(0.0, self.avgDischarge)
        self.m2tDischarge = self.m2tDischarge + pcr.abs(deltaAnoDischarge*(dishargeUsed - self.avgDischarge))
        
        # - short term average discharge
        deltaAnoDischargeShort = dishargeUsed - self.avgDischargeShort  
        self.avgDischargeShort = self.avgDischargeShort + \
                                 deltaAnoDischargeShort/ \
                                 pcr.min(self.maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)
        self.avgDischargeShort = pcr.max(0.0, self.avgDischargeShort)                         
        
        # long term average baseflow (m3/s)
        # (used as proxies for partitioning groundwater and surface water abstractions)
        baseflowM3PerSec = groundwater.baseflow * self.cellArea / vos.secondsPerDay()
        
        deltaAnoBaseflow = baseflowM3PerSec - self.avgBaseflow  
        self.avgBaseflow = self.avgBaseflow + \
                           deltaAnoBaseflow/ \
                           pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)                
        self.avgBaseflow = pcr.max(0.0, self.avgBaseflow)
        
        # DynQual
        # average irrigation water that is allocated from the last 30 days (needed for online runs where loadings are calculated in loop)
        if self.quality:
            if self.calculateLoads and self.offlineRun == False:
                # calculate average irrigation gross demands from the last 30 days
                irrGrossDemand= deepcopy(landSurface.irrGrossDemand)
                deltaAno_irrGrossDemand = pcr.max(0.0, irrGrossDemand) - self.avg_irrGrossDemand
                self.avg_irrGrossDemand = self.avg_irrGrossDemand +\
                                          deltaAno_irrGrossDemand/\
                                          pcr.min(30.0, self.timestepsToAvgDischarge)
                self.avg_irrGrossDemand = pcr.max(0.0, self.avg_irrGrossDemand)
            
                # average netLqWaterToSoil from the last 30 days
                deltaAno_netLqWaterToSoil = pcr.max(0.0, landSurface.netLqWaterToSoil) - self.avg_netLqWaterToSoil
                self.avg_netLqWaterToSoil = self.avg_netLqWaterToSoil +\
                                            deltaAno_netLqWaterToSoil/\
                                            pcr.min(30.0, self.timestepsToAvgDischarge)
                self.avg_netLqWaterToSoil = pcr.max(0.0, self.avg_netLqWaterToSoil)
        
        # QUAlloc
        #if self.using_qualloc:
        #    # average channel storage 
        #    deltaChannelStorage    = self.channelStorage - self.avgChannelStorage
        #    self.avgChannelStorage = self.avgChannelStorage + \
        #                                  deltaChannelStorage/ \
        #                                  pcr.min(self.maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)
        #    self.avgChannelStorage = pcr.max(0.0, self.avgChannelStorage)
        #    
        #    # average total runoff
        #    deltaTotalRunoff    = self.totalRunoff - self.avgTotalRunoff
        #    self.avgTotalRunoff = self.avgTotalRunoff + \
        #                              deltaTotalRunoff/ \
        #                              pcr.min(self.maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)
        #    self.avgTotalRunoff = pcr.max(0.0, self.avgTotalRunoff)
        #    
        #    # average groundwater storage
        #    deltaStorGroundwater    = groundwater.storGroundwater - self.avgStorGroundwater
        #    self.avgStorGroundwater = self.avgStorGroundwater + \
        #                                   deltaStorGroundwater/ \
        #                                   pcr.min(self.maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)
        #    self.avgStorGroundwater = pcr.max(0.0, self.avgStorGroundwater)


    def estimate_discharge_for_environmental_flow(self, channelStorage):
        
        # statistical assumptions:
        # - using z_score from the percentile 90
        z_score = 1.2816
        # - using z_score from the percentile 95
        #z_score = 1.645
        
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
        # input: channelStorage (units: m3)
        
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
        
        # maximum (percentage) of water can be abstracted from the channel - to avoid flip-flop
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
        if self.quality: 
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
        #Read meteorological input directly from netCDF files
        if currTimeStep.day == 1:
            self.cloudCover = vos.netcdf2PCRobjClone(\
                                     self.cloudFileNC,'cld',\
                                     str(currTimeStep.fulldate), 
                                     useDoy = "monthly",
                                      cloneMapFileName=self.cloneMap,\
                                      LatitudeLongitude = True,specificFillValue = -999.)/pcr.scalar(100)
            
            self.vaporPressure = vos.netcdf2PCRobjClone(\
                                     self.vapFileNC,'vap',\
                                     str(currTimeStep.fulldate), 
                                     useDoy = "monthly",
                                      cloneMapFileName=self.cloneMap,\
                                      LatitudeLongitude = True,specificFillValue = -999.)
            
            self.annualT = vos.netcdf2PCRobjClone(\
                                             self.annualTFileNC,'tas',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = "yearly",
                                              cloneMapFileName=self.cloneMap,\
                                              LatitudeLongitude = True,specificFillValue = -999.) + pcr.scalar(273.15)
        
        self.radiation =  vos.netcdf2PCRobjClone(\
                                 self.radFileNC,'rsds',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = "daily",
                                 cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = -999.)
        
        #-vapour pressure, used to return atmospheric emissivity [-]                          
        self.atmosEmis= pcr.scalar(1.0) #pcr.min(1.,(0.53+0.0065*(self.vaporPressure)**0.5)*(1.+0.4*self.cloudCover))
        cld1= pcr.roundoff(10*self.cloudCover+0.5)
        cld0= cld1-1
        sun0= pcr.lookupscalar(self.sunFracTBL, cld0)
        deltaSun= (pcr.lookupscalar(self.sunFracTBL,cld1)-sun0)/(cld1-cld0)
        sunFrac= sun0+(10*self.cloudCover-cld0)*deltaSun
        radFrac= self.radCon+self.radSlope*sunFrac
        self.rsw= radFrac*self.radiation


    def readExtensiveHydro(self, currTimeStep):
        
        # Read hydrological input directly from netCDF files (daily timestep)
        self.baseflow = vos.netcdf2PCRobjClone(\
                                  self.baseflowNC,"baseflow",\
                                  str(currTimeStep.fulldate),
                                  useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)
        self.baseflow = pcr.ifthen(self.landmask,self.baseflow)
        
        self.interflowTotal = vos.netcdf2PCRobjClone(\
                                        self.interflowNC,"interflow",\
                                        str(currTimeStep.fulldate),
                                        useDoy = None,
                                        cloneMapFileName=self.cloneMap,\
                                        LatitudeLongitude = True)
        self.interflowTotal = pcr.ifthen(self.landmask,self.interflowTotal)
                                          
        self.directRunoff = vos.netcdf2PCRobjClone(\
                                  self.directRunoffNC, "direct_runoff",\
                                  str(currTimeStep.fulldate),
                                  useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)
        self.directRunoff = pcr.ifthen(self.landmask,self.directRunoff)
                                               
        self.runoff = self.directRunoff + self.interflowTotal + self.baseflow


#    def readPowerplantData(self, currTimeStep):
#                 
#        logger.info("reading in (annual) powerplant data")
#        
#        # freshwater plants (with a water temperature dependency)
#        self.powerplants_fw_capacity =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'capacity',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_ntotal =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'ntotal',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        self.powerplants_fw_nelec =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'nelec',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_alpha =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'alpha',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_beta =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'beta',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_omega =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'omega',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_EZ =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'EZ',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_gamma =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'gamma',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_lambda =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'lambda',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fw_ratio =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwNC,'con_ratio',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        # freshwater plants (without a water temperature dependency)
#        self.powerplants_fwfixed_capacity =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwfixedNC,'capacity',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fwfixed_q =  vos.netcdf2PCRobjClone(\
#                                    self.powerplants_fwfixedNC,'withdrawals',\
#                                    str(currTimeStep.fulldate), 
#                                    useDoy = "yearly",
#                                    cloneMapFileName=self.cloneMap,\
#                                     LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_fwfixed_ratio =  vos.netcdf2PCRobjClone(\
#                                              self.powerplants_fwfixedNC,'con_ratio',\
#                                              str(currTimeStep.fulldate), 
#                                              useDoy = "yearly",
#                                              cloneMapFileName=self.cloneMap,\
#                                               LatitudeLongitude = True,specificFillValue = None)
#        
#        # seawater plants
#        self.powerplants_sw_capacity =  vos.netcdf2PCRobjClone(\
#                                         self.powerplants_swNC,'capacity',\
#                                         str(currTimeStep.fulldate), 
#                                         useDoy = "yearly",
#                                         cloneMapFileName=self.cloneMap,\
#                                          LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_sw_q =  vos.netcdf2PCRobjClone(\
#                                         self.powerplants_swNC,'withdrawals',\
#                                         str(currTimeStep.fulldate), 
#                                         useDoy = "yearly",
#                                         cloneMapFileName=self.cloneMap,\
#                                          LatitudeLongitude = True,specificFillValue = None)
#        
#        self.powerplants_sw_ratio =  vos.netcdf2PCRobjClone(\
#                                         self.powerplants_swNC,'con_ratio',\
#                                         str(currTimeStep.fulldate), 
#                                         useDoy = "yearly",
#                                         cloneMapFileName=self.cloneMap,\
#                                          LatitudeLongitude = True,specificFillValue = None)
#        
#        # Poweplant demand factors
#        self.dTlmax = pcr.scalar(7.)
#        self.Tlmax =  vos.netcdf2PCRobjClone(\
#                       self.TlmaxNC,'waterTemperature',\
#                       str(currTimeStep.fulldate), 
#                       useDoy = "yearly",
#                       cloneMapFileName=self.cloneMap,\
#                        LatitudeLongitude = True,specificFillValue = None)


#    def calculatePowerplantDemands(self, currTimeStep):
#        
#        ###freshwater plants (with a water temperature dependency)
#        
#        #demands considering only dTlmax
#        self.powerplants_fw_qmin = self.powerplants_fw_capacity * 1e6 * ((1- self.powerplants_fw_ntotal)/ self.powerplants_fw_nelec) * (((1-self.powerplants_fw_alpha) * (1-self.powerplants_fw_beta) * self.powerplants_fw_omega * self.powerplants_fw_EZ)/ (self.densityWater * self.specificHeatWater * self.dTlmax)) #minimum demands (i.e. only considering deltaTlmax)
#        
#        #demands considering simulated river water temperature
#        self.min_Tlmax_dTlmax = pcr.max(pcr.min(self.Tlmax - self.waterTemp, self.dTlmax),1.) #calculate min of Tlmax (max allowed temperature) - triver (water temperature). Returns minimum value of 1 (i.e. water can always be warmed by 1K as a minimum).
#        
#        self.powerplants_fw_q = self.powerplants_fw_capacity * 1e6 * ((1- self.powerplants_fw_ntotal)/ self.powerplants_fw_nelec) * (((1-self.powerplants_fw_alpha) * (1-self.powerplants_fw_beta) * self.powerplants_fw_omega * self.powerplants_fw_EZ)/ (self.densityWater * self.specificHeatWater * self.min_Tlmax_dTlmax))
#        self.powerplants_fw_rf = self.powerplants_fw_q * (1 - self.powerplants_fw_ratio) #power return flows (m3 s-1)
#        self.PowTwload = pcr.cover(self.powerplants_fw_rf * self.specificHeatWater * self.densityWater * self.min_Tlmax_dTlmax, 0.) #heat dumps from water-temperature dependent powerplants (J s-1)
#        
#        ###freshwater plants (without a water temperature dependency)
#        self.powerplants_fwfixed_q = self.powerplants_fwfixed_q #freshwater demands for power prescribed by Lohrmann et al., (2019)
#        self.powerplants_fwfixed_rf = self.powerplants_fwfixed_q * (1 - self.powerplants_fwfixed_ratio) #power return flows (to freshwater) prescribed by Lohrmann et al., (2019)
#        
#        ###seawater plants
#        self.powerplants_sw_q = self.powerplants_sw_q #seawater demands for power prescribed by Lohrmann et al., (2019)
#        self.powerplants_sw_rf = self.powerplants_sw_q * (1 - self.powerplants_sw_ratio) #power return flows (to seawater) prescribed by Lohrmann et al., (2019)


    def readPollutantLoadingsInputData(self, currTimeStep):
        logger.info("Loading input data required to calculate pollutant loadings")
        
        #Domestic
        self.Population = vos.netcdf2PCRobjClone(\
                                 self.PopulationNC,'Population',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True,specificFillValue = None) #input pathway for gridded population file (5 arc-mins)    
        
        #Urban surface runoff
        self.urban_area_fraction = vos.netcdf2PCRobjClone(\
                                             self.UrbanFractionNC,'urban_fraction',\
                                             str(currTimeStep.fulldate), 
                                             useDoy = None,
                                             cloneMapFileName=self.cloneMap,\
                                             LatitudeLongitude = True,specificFillValue = None) #fraction urban area (0-1)
        self.urban_area_fraction = pcr.cover(self.urban_area_fraction,0) #if urban fraction missing (e.g. for lakes), make 0
        
        #Livestock
        self.BufalloPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'BufalloPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for bufallo population (5 arc-mins)
        self.BufalloPopulation = pcr.cover(self.BufalloPopulation,0.)
        
        self.ChickenPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'ChickenPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for chicken population (5 arc-mins)
        self.ChickenPopulation = pcr.cover(self.ChickenPopulation,0.)
        
        self.CowPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'CowPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for cow population (5 arc-mins)
        self.CowPopulation = pcr.cover(self.CowPopulation,0.)
        
        self.DuckPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'DuckPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for duck population (5 arc-mins)                 
        self.DuckPopulation = pcr.cover(self.DuckPopulation,0.)
        
        self.GoatPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'GoatPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for goat population (5 arc-mins)  
        self.GoatPopulation = pcr.cover(self.GoatPopulation,0.)
        
        self.HorsePopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'HorsePop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for horse population (5 arc-mins)  
        self.HorsePopulation = pcr.cover(self.HorsePopulation,0.)
        
        self.PigPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'PigPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for pig population (5 arc-mins)  
        self.PigPopulation = pcr.cover(self.PigPopulation,0.)
        
        self.SheepPopulation = vos.netcdf2PCRobjClone(\
                                 self.LivPopulationNC,'SheepPop',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True,specificFillValue = None) #input pathway for sheep population (5 arc-mins)            
        self.SheepPopulation = pcr.cover(self.SheepPopulation,0.)
        
        #Calculate livestock densities accounting for livestock units (Wen et al., 2018)
        self.cellArea_km2    = self.cellArea/1000000. #convert m2 to km2
        self.LivDensityThres = pcr.scalar(25.)
        
        self.BufalloDensity = self.BufalloPopulation / self.cellArea_km2
        self.ChickenDensity = (self.ChickenPopulation * 0.01) / self.cellArea_km2
        self.CowDensity     = self.CowPopulation / self.cellArea_km2
        self.DuckDensity    = (self.DuckPopulation * 0.01) / self.cellArea_km2
        self.GoatDensity    = (self.GoatPopulation * 0.1) / self.cellArea_km2
        self.HorseDensity   = self.HorsePopulation / self.cellArea_km2
        self.PigDensity     = (self.PigPopulation * 0.3) / self.cellArea_km2
        self.SheepDensity   = (self.SheepPopulation * 0.1) / self.cellArea_km2
        
        #Wastewater treatment plants
        #self.WWt_plantID = vos.netcdf2PCRobjClone(\
        #                         self.WWtPlantsNC,'plant_id',\
        #                         str(currTimeStep.fulldate), 
        #                         useDoy = None,
        #                         cloneMapFileName=self.cloneMap,\
        #                         LatitudeLongitude = True, specificFillValue = None) #wastewater treatment plant [point] locations
        #self.WWt_plantID = pcr.nominal(self.WWt_plantID)
        #
        #self.WWt_zoneID = vos.netcdf2PCRobjClone(\
        #                         self.WWtPlantsNC,'zone_id',\
        #                         str(currTimeStep.fulldate), 
        #                         useDoy = None,
        #                         cloneMapFileName=self.cloneMap,\
        #                         LatitudeLongitude = True, specificFillValue = None) #wastewater treatment plant service zones
        #self.WWt_zoneID = pcr.nominal(self.WWt_zoneID)
        
        self.WWt_ct = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,'WW_ct',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True, specificFillValue = None) #proportion of wastewater that is collected and subsequently treated
        
        self.WWt_bs = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,'WW_bs',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True, specificFillValue = None) #country-level fraction of uncollected wastewater that is open defecation
        
        self.WWt_od = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,'WW_od',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True, specificFillValue = None) #country-level fraction of uncollected wastewater that is open defecation
        
        self.WWt_TDS_removal = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,'TDS_removal',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True, specificFillValue = None) #proportion of TDS removed at each wastewater treatment plant   
        
        self.WWt_BOD_removal = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,'BOD_removal',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True, specificFillValue = None) #proportion of BOD removed at each wastewater treatment plant    
        
        self.WWt_FC_removal = vos.netcdf2PCRobjClone(\
                                 self.WWtPlantsNC,'FC_removal',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True, specificFillValue = None) #proportion of FC removed at each wastewater treatment plant                                                                             


    def calculatePollutantLoadings(self, currTimeStep, landSurface, groundwater):
        #calculate pollutant loadings directly
        logger.info("Calculating pollutant loadings")
        
        self.frac_surfaceRunoff = vos.getValDivZero( landSurface.directRunoff, \
                                                    (landSurface.landSurfaceRunoff + groundwater.baseflow)) #Fraction of direct runoff directly from PCR-GLOBWB (direct runoff / total runoff), used for transporting pollution from open defecation and extensive livestock.
        
        ###---Pollution associated with municipal wastewater (domestic, manufacturing and urban surface runoff---###
        
        ###Gross domestic loadings: Gridded population (capita) * per Capita excretion rate [g/capita/day; cfu/capita/day]
        self.Dom_TDSload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            (self.Population * self.DomTDS_ExcrLoad * self.WWt_bs) + 
            (self.Population * self.DomTDS_ExcrLoad * self.WWt_od * self.frac_surfaceRunoff),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.Population * self.DomTDS_ExcrLoad,
                                   0), 
                    self.WWt_zoneID 
                ) * (1 - (self.WWt_TDS_removal * self.WWt_ct)), #Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day        
        
        self.Dom_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            (self.Population * self.DomBOD_ExcrLoad * self.WWt_bs) + 
            (self.Population * self.DomBOD_ExcrLoad * self.WWt_od * self.frac_surfaceRunoff),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.Population * self.DomBOD_ExcrLoad,
                                   0), 
                    self.WWt_zoneID 
                ) * (1 - (self.WWt_BOD_removal * self.WWt_ct)), #Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day            
        
        self.Dom_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            (self.Population * (self.DomFC_ExcrLoad/1000000.) * self.WWt_bs) + 
            (self.Population * (self.DomFC_ExcrLoad/1000000.) * self.WWt_od * self.frac_surfaceRunoff),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.Population * (self.DomFC_ExcrLoad/1000000.),
                                   0), 
                    self.WWt_zoneID 
                ) * (1 - (self.WWt_FC_removal * self.WWt_ct)), #Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #million cfu/day
        
        ###Gross manufacturing loadings: Manufacturing wastewater [m3/day] * average manufacturing effluent concentration [mg/L; cfu/100ml]
        #self.ManWWp = self.IndustryReturnFlowVol #manufacturing flows, assumed based on split made in Jones et al., 2021, now are "Industry return flows"
        if self.includeSectors['industry']:
            self.ManWWp = landSurface.nonIrrReturnFlowVolumePerSector['industry']
        elif self.includeSectors['manufacture']:
            self.ManWWp = landSurface.nonIrrReturnFlowVolumePerSector['manufacture']
        
        self.Man_TDSload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.ManWWp * self.ManTDS_EfflConc ,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.ManWWp * self.ManTDS_EfflConc,
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_TDS_removal * self.WWt_ct)), #Removal at wastewater treatment plant.
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day
        
        self.Man_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.ManWWp * self.ManBOD_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.ManWWp * self.ManBOD_EfflConc,
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_BOD_removal * self.WWt_ct)), #Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day  
        
        self.Man_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.ManWWp * (self.ManFC_EfflConc /100.),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.ManWWp * (self.ManFC_EfflConc / 100.),
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_FC_removal * self.WWt_ct)), #Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #million cfu/day          
        
        
        ###Gross urban surface runoff loadings: USR return flow [m3/day] * average USR effluent concentration [mg/L; cfu/100ml] 
        self.USR_RF = landSurface.directRunoff * self.urban_area_fraction * self.cellArea #m3 day

        self.USR_TDSload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.USR_RF * self.USRTDS_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.USR_RF * self.USRTDS_EfflConc,
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_TDS_removal * self.WWt_ct)), #Removal at wastewater treatment plant
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day  

        self.USR_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.USR_RF * self.USRBOD_EfflConc,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.USR_RF * self.USRBOD_EfflConc,
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_BOD_removal * self.WWt_ct)),
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day  
        
        self.USR_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.USR_RF * (self.USRFC_EfflConc /100.),
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.USR_RF * (self.USRFC_EfflConc/100.),
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_FC_removal * self.WWt_ct)),
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #million cfu/day         
        
                     
        ###---Pollution associated with livestock (intensive and extensive---###
        #BOD
        self.intLiv_Bufallo_BODload = pcr.ifthenelse(self.BufalloDensity > self.LivDensityThres, self.BufalloPopulation * self.Bufallo_BODload, 0.0)
        self.intLiv_Chicken_BODload = pcr.ifthenelse(self.ChickenDensity > self.LivDensityThres, self.ChickenPopulation * self.Chicken_BODload, 0.0)
        self.intLiv_Cow_BODload     = pcr.ifthenelse(self.CowDensity > self.LivDensityThres, self.CowPopulation * self.Cow_BODload, 0.0)
        self.intLiv_Duck_BODload    = pcr.ifthenelse(self.DuckDensity > self.LivDensityThres, self.DuckPopulation * self.Duck_BODload, 0.0)
        self.intLiv_Goat_BODload    = pcr.ifthenelse(self.GoatDensity > self.LivDensityThres, self.GoatPopulation * self.Goat_BODload, 0.0)
        self.intLiv_Horse_BODload   = pcr.ifthenelse(self.HorseDensity > self.LivDensityThres, self.HorsePopulation * self.Horse_BODload, 0.0)
        self.intLiv_Pig_BODload     = pcr.ifthenelse(self.PigDensity > self.LivDensityThres, self.PigPopulation * self.Pig_BODload, 0.0)
        self.intLiv_Sheep_BODload   = pcr.ifthenelse(self.SheepDensity > self.LivDensityThres, self.SheepPopulation * self.Sheep_BODload, 0.0)
                
        self.intLiv_BODload = self.intLiv_Bufallo_BODload + self.intLiv_Chicken_BODload + self.intLiv_Cow_BODload +\
                              self.intLiv_Duck_BODload + self.intLiv_Goat_BODload + self.intLiv_Horse_BODload + self.intLiv_Pig_BODload + self.intLiv_Sheep_BODload #g/day        
        
        self.intLiv_BODload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.intLiv_BODload * self.frac_surfaceRunoff,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.intLiv_BODload,
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_BOD_removal * self.WWt_ct)) * self.frac_surfaceRunoff,
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #g/day        

        self.extLiv_Bufallo_BODload = pcr.ifthenelse(self.BufalloDensity <= self.LivDensityThres, self.BufalloPopulation * self.Bufallo_BODload, 0.0)
        self.extLiv_Chicken_BODload = pcr.ifthenelse(self.ChickenDensity <= self.LivDensityThres, self.ChickenPopulation * self.Chicken_BODload, 0.0)
        self.extLiv_Cow_BODload = pcr.ifthenelse(self.CowDensity <= self.LivDensityThres, self.CowPopulation * self.Cow_BODload, 0.0)
        self.extLiv_Duck_BODload = pcr.ifthenelse(self.DuckDensity <= self.LivDensityThres, self.DuckPopulation * self.Duck_BODload, 0.0)
        self.extLiv_Goat_BODload = pcr.ifthenelse(self.GoatDensity <= self.LivDensityThres, self.GoatPopulation * self.Goat_BODload, 0.0)
        self.extLiv_Horse_BODload = pcr.ifthenelse(self.HorseDensity <= self.LivDensityThres, self.HorsePopulation * self.Horse_BODload, 0.0)
        self.extLiv_Pig_BODload = pcr.ifthenelse(self.PigDensity <= self.LivDensityThres, self.PigPopulation * self.Pig_BODload, 0.0)
        self.extLiv_Sheep_BODload = pcr.ifthenelse(self.SheepDensity <= self.LivDensityThres, self.SheepPopulation * self.Sheep_BODload, 0.0)

        self.extLiv_BODload = (self.extLiv_Bufallo_BODload + self.extLiv_Chicken_BODload + self.extLiv_Cow_BODload +\
                                      self.extLiv_Duck_BODload + self.extLiv_Goat_BODload + self.extLiv_Horse_BODload + self.extLiv_Pig_BODload + self.extLiv_Sheep_BODload) *\
                                      self.frac_surfaceRunoff #g/day

        #FC
        self.intLiv_Bufallo_FCload = pcr.ifthenelse(self.BufalloDensity > self.LivDensityThres, self.BufalloPopulation * self.Bufallo_FCload, 0.0)
        self.intLiv_Chicken_FCload = pcr.ifthenelse(self.ChickenDensity > self.LivDensityThres, self.ChickenPopulation * self.Chicken_FCload, 0.0)
        self.intLiv_Cow_FCload     = pcr.ifthenelse(self.CowDensity > self.LivDensityThres, self.CowPopulation * self.Cow_FCload, 0.0)
        self.intLiv_Duck_FCload    = pcr.ifthenelse(self.DuckDensity > self.LivDensityThres, self.DuckPopulation * self.Duck_FCload, 0.0)
        self.intLiv_Goat_FCload    = pcr.ifthenelse(self.GoatDensity > self.LivDensityThres, self.GoatPopulation * self.Goat_FCload, 0.0)
        self.intLiv_Horse_FCload   = pcr.ifthenelse(self.HorseDensity > self.LivDensityThres, self.HorsePopulation * self.Horse_FCload, 0.0)
        self.intLiv_Pig_FCload     = pcr.ifthenelse(self.PigDensity > self.LivDensityThres, self.PigPopulation * self.Pig_FCload, 0.0)
        self.intLiv_Sheep_FCload   = pcr.ifthenelse(self.SheepDensity > self.LivDensityThres, self.SheepPopulation * self.Sheep_FCload, 0.0)
        
        self.intLiv_FCload = (self.intLiv_Bufallo_FCload + self.intLiv_Chicken_FCload + self.intLiv_Cow_FCload +\
                              self.intLiv_Duck_FCload + self.intLiv_Goat_FCload + self.intLiv_Horse_FCload + self.intLiv_Pig_FCload + self.intLiv_Sheep_FCload)\
                              / 1000000.
        
        self.intLiv_FCload = pcr.ifthenelse(
            self.WWt_zoneID == 0,  # Gridcells not in a wastewater treatment zone
            self.intLiv_FCload * self.frac_surfaceRunoff,
            pcr.ifthenelse(
                self.WWt_zoneID == self.WWt_plantID, #Accumulate loadings over wastewater treatment zone to plant location
                pcr.areatotal(
                    pcr.ifthenelse(self.WWt_zoneID != 0, 
                                   self.intLiv_FCload,
                                   0), 
                    self.WWt_zoneID 
                ) * (1- (self.WWt_FC_removal * self.WWt_ct)) * self.frac_surfaceRunoff,
                0.  # After accumulation, assign locations without a wastewater treatment plant as 0.
            )
        ) #million cfu/day        
        
        self.extLiv_Bufallo_FCload = pcr.ifthenelse(self.BufalloDensity <= self.LivDensityThres, self.BufalloPopulation * self.Bufallo_FCload, 0.0)
        self.extLiv_Chicken_FCload = pcr.ifthenelse(self.ChickenDensity <= self.LivDensityThres, self.ChickenPopulation * self.Chicken_FCload, 0.0)
        self.extLiv_Cow_FCload = pcr.ifthenelse(self.CowDensity <= self.LivDensityThres, self.CowPopulation * self.Cow_FCload, 0.0)
        self.extLiv_Duck_FCload = pcr.ifthenelse(self.DuckDensity <= self.LivDensityThres, self.DuckPopulation * self.Duck_FCload, 0.0)
        self.extLiv_Goat_FCload = pcr.ifthenelse(self.GoatDensity <= self.LivDensityThres, self.GoatPopulation * self.Goat_FCload, 0.0)
        self.extLiv_Horse_FCload = pcr.ifthenelse(self.HorseDensity <= self.LivDensityThres, self.HorsePopulation * self.Horse_FCload, 0.0)
        self.extLiv_Pig_FCload = pcr.ifthenelse(self.PigDensity <= self.LivDensityThres, self.PigPopulation * self.Pig_FCload, 0.0)
        self.extLiv_Sheep_FCload = pcr.ifthenelse(self.SheepDensity <= self.LivDensityThres, self.SheepPopulation * self.Sheep_FCload, 0.0)
        
        self.extLiv_FCload = ((self.extLiv_Bufallo_FCload + self.extLiv_Chicken_FCload + self.extLiv_Cow_FCload +\
                              self.extLiv_Duck_FCload + self.extLiv_Goat_FCload + self.extLiv_Horse_FCload + self.extLiv_Pig_FCload + self.extLiv_Sheep_FCload)\
                              / 1000000.) * self.frac_surfaceRunoff #million cfu/day
        
        
        ###---Pollution associated with irrigation---###
        #- Irrigation return flow (m3/day) * soil TDS (mg/L)
        #- Irrigation return flows calculated directly from PCR-GLOBWB (from direct runoff, interflow and baseflow)
        self.irr_rf_from_direct_runoff = landSurface.directRunoff * vos.getValDivZero(self.avg_irrGrossDemand, (self.avg_irrGrossDemand + self.avg_netLqWaterToSoil))
        self.irr_rf_from_interflow     = landSurface.interflowTotal * vos.getValDivZero(self.avg_irrGrossDemand, (self.avg_irrGrossDemand + self.avg_netLqWaterToSoil))
        self.irr_rf_from_baseflow     =  groundwater.baseflow * vos.getValDivZero(self.avg_irrGrossDemand, (self.avg_irrGrossDemand + self.avg_netLqWaterToSoil))

        self.Irr_RF = (self.irr_rf_from_direct_runoff +\
                       self.irr_rf_from_interflow +\
                       self.irr_rf_from_baseflow) * self.cellArea  # - total irirgation return flow in volume units (m3 day-1) 
        self.Irr_TDSload = self.Irr_RF * self.IrrTDS_EfflConc #g/day
        
        ###---Pollution associated by human activities combined---###
        self.TDSload = (self.Dom_TDSload + self.Man_TDSload + self.USR_TDSload + self.Irr_TDSload) #g day-1
        self.BODload = (self.Dom_BODload + self.Man_BODload + self.USR_BODload + self.intLiv_BODload + self.extLiv_BODload) #g day-1
        self.FCload = (self.Dom_FCload + self.Man_FCload + self.USR_FCload + self.intLiv_FCload + self.extLiv_FCload) #million cfu day-1
        
    def readPollutantLoadings(self, currTimeStep):
        #Use pre-calculated pollutant loadings
        logger.info("Reading loadings directly")        
        
        # read TDS loadings (combined for all sectoral activities)
        self.TDSload = vos.netcdf2PCRobjClone(\
                                 self.TDSloadNC,'TDSload',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True)
        self.TDSload = pcr.ifthen(self.landmask, self.TDSload)

        #read BOD loadings (combined for all sectoral activities)
        self.BODload = vos.netcdf2PCRobjClone(\
                                 self.BODloadNC,'BODload',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True)							 
        self.BODload = pcr.ifthen(self.landmask, self.BODload)
        
        #read FC loadings (combined for all sectoral activities)
        self.FCload = vos.netcdf2PCRobjClone(\
                                 self.FCloadNC,'FCload',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                 cloneMapFileName=self.cloneMap,\
                                 LatitudeLongitude = True)                                   
        self.FCload = pcr.ifthen(self.landmask, self.FCload)
                
    def qualityLocal(self, meteo, landSurface, groundwater, currTimeStep, timeSec=vos.secondsPerDay()):
        
        ###Water temperature
        # Surface water energy fluxes [W/m2]
        # within the current time step
        # Ice formation evaluated prior to routing to account for loss
        # in water height, vertical change in energy evaluated,
        # warming capped to increase to air temperature
        
        #Define constants & variables
        self.temperatureKelvin = meteo.temperature + pcr.scalar(273.15)
        landRunoff = self.runoff
        self.correctPrecip = pcr.scalar(0.0)
        self.dynamicFracWatBeforeRouting = self.dynamicFracWat
        
        #Calculate land temperature considering runoff fractions
        landT = pcr.cover(
            landSurface.directRunoff / landRunoff * pcr.max(self.iceThresTemp + 0.1, self.temperatureKelvin - self.deltaTPrec) +
            landSurface.interflowTotal / landRunoff * pcr.max(self.iceThresTemp + 0.1, self.temperatureKelvin) +
            groundwater.baseflow / landRunoff * pcr.max(self.iceThresTemp + 5.0, self.annualT),
            self.temperatureKelvin
        )
      
        #Heat transfer calculations (ice and water)
        iceHeatTransfer = self.heatTransferWater * (self.temperatureKelvin - self.iceThresTemp)
        waterHeatTransfer = self.heatTransferIce * (self.iceThresTemp - self.waterTemp)
        
        #Check for presence of ice
        noIce = pcr.ifthenelse(
            self.iceThickness > 0, pcr.boolean(0),
            pcr.ifthenelse(
                ((iceHeatTransfer - waterHeatTransfer) < 0) & (self.temperatureKelvin < self.iceThresTemp),
                pcr.boolean(0), pcr.boolean(1)
            )
        )
        
        #Update water heat transfer based on ice presence
        waterHeatTransfer = pcr.ifthenelse(
            noIce, self.heatTransferWater * (self.temperatureKelvin - self.waterTemp), waterHeatTransfer
        )
        
        #Radiative heat transfer calculations
        radiativHeatTransfer = (1 - pcr.ifthenelse(noIce, self.albedoWater, self.albedoSnow)) * self.rsw
        radiativHeatTransfer -= self.stefanBoltzman * (pcr.ifthenelse(noIce, self.waterTemp, self.iceThresTemp) ** 4 - self.atmosEmis * self.temperatureKelvin ** 4)
        
        #Advected energy due to precipitation and inflow
        advectedEnergyPrecip = pcr.max(0, self.correctPrecip) * pcr.max(self.iceThresTemp + 0.1, self.temperatureKelvin - self.deltaTPrec) * self.specificHeatWater * self.densityWater / timeSec
        advectedEnergyInflow = (1 - self.dynamicFracWat) / self.dynamicFracWat * landRunoff * landT * self.specificHeatWater * self.densityWater / timeSec
        advectedEnergyInflow -= landSurface.actSurfaceWaterAbstract / self.dynamicFracWat * self.waterTemp * self.specificHeatWater * self.densityWater / timeSec
        
        #Ice formation and thickness calculation
        diceHeatTransfer = pcr.ifthenelse(noIce, 0, iceHeatTransfer - waterHeatTransfer + radiativHeatTransfer)
        self.deltaIceThickness = -diceHeatTransfer * timeSec / (self.densityWater * self.latentHeatFusion)
        self.deltaIceThickness = pcr.max(-self.iceThickness, self.deltaIceThickness)
        self.deltaIceThickness = pcr.min(self.deltaIceThickness, pcr.max(0, self.maxIceThickness - self.iceThickness))
        
        #Returning direct gain over water surface
        watQ = pcr.ifthenelse(self.temperatureKelvin >= self.iceThresTemp, pcr.max(0, self.correctPrecip) - self.waterBodyEvaporation / self.dynamicFracWat, 0)
        self.waterBodyEvaporation = pcr.ifthenelse(self.temperatureKelvin >= self.iceThresTemp, self.waterBodyEvaporation, 0)  # TODO move
        
        #Vertical gains/losses calculation
        deltaIceThickness_melt = pcr.max(0, -self.deltaIceThickness)
        verticalGain = (watQ + (landRunoff - landSurface.actSurfaceWaterAbstract) / (self.dynamicFracWat) + deltaIceThickness_melt)
        
        #Water storage change
        dtotStorLoc = verticalGain
        totStorLoc = self.channelStorageTimeBefore / (self.dynamicFracWat * self.cellArea) - dtotStorLoc
        totStorLoc = self.return_water_body_storage_to_channel(self.channelStorageTimeBefore) / (self.dynamicFracWat * self.cellArea) - dtotStorLoc
        
        #Calculate energy in channel
        self.totEW = totStorLoc * self.waterTemp * self.specificHeatWater * self.densityWater
        dtotStorLoc = pcr.max(-totStorLoc, dtotStorLoc)
        
        #Latent heat flux and advected energy for water evaporation
        latentHeat = -self.waterBodyEvaporation / self.dynamicFracWat * self.densityWater * self.latentHeatVapor / timeSec
        advectedEnergyPrecip += deltaIceThickness_melt * self.iceThresTemp * self.specificHeatWater * self.densityWater / timeSec
        
        #Estimate total energy change
        totEWC = totStorLoc * self.specificHeatWater * self.densityWater
        dtotEWC = dtotStorLoc * self.specificHeatWater * self.densityWater
        dtotEWLoc = (waterHeatTransfer + pcr.scalar(noIce) * (radiativHeatTransfer + latentHeat)) * timeSec
        dtotEWAdv = (advectedEnergyInflow + advectedEnergyPrecip) * timeSec
        
        dtotEWLoc = pcr.min(dtotEWLoc, pcr.max(0, totEWC * self.temperatureKelvin - self.totEW) + pcr.ifthenelse(dtotStorLoc > 0, pcr.max(0, dtotEWC * self.temperatureKelvin - dtotEWAdv), 0))
        dtotEWLoc = pcr.ifthenelse(self.waterTemp > self.temperatureKelvin, pcr.min(0, dtotEWLoc), dtotEWLoc)
        dtotEWLoc = pcr.max(dtotEWLoc, pcr.min(0, (totEWC + dtotEWC) * pcr.max(self.temperatureKelvin, self.iceThresTemp + 0.1) - (self.totEW + dtotEWAdv)))
        
        #Update water height, energy and water temperature
        self.temp_water_height = pcr.max(1e-16, totStorLoc + dtotStorLoc)
        self.totEW = pcr.max(0, self.totEW + dtotEWLoc + dtotEWAdv)
        
        if currTimeStep.timeStepPCR != 1: #temporary fix for error in water temperature simulation in first timestep.
            self.waterTemp = pcr.ifthenelse(
                self.temp_water_height > self.critical_water_height,
                self.totEW / self.temp_water_height / (self.specificHeatWater * self.densityWater),
                self.temperatureKelvin
            )
        self.waterTemp = min(pcr.ifthenelse(self.waterTemp < self.iceThresTemp + 0.1, self.iceThresTemp + 0.1, self.waterTemp),self.maxThresTemp)               
        self.waterTemp_C = self.waterTemp - pcr.scalar(273.15)   #water temperature in gridcell in C
        
        ###BOD (non-conservative; function of water temperature only)
        #---Temperature dependent decay parameters
        self.BODdecay_temperature = cover(self.k_BOD*(self.watertempcorrection_BOD**(self.waterTemp_C - 20)),0.0)
        
        ###FC (non-conservative; function of temperature, solar radiation and sedimentation)      
        #---Temperature dependent decay parameters
        self.FCdecay_temperature = cover(self.darkinactivation_FC * (self.watertempcorrection_FC**(self.waterTemp_C - 20)),0.0)
        
        #---Solar radiation dependent decay parameters
        self.water_height_pathogen = pcr.max(self.water_height, 0.1) #set minimum water depth of 0.1m for decay coefficients        
        self.FCdecay_solarradiation = cover(self.sunlightinactivation_FC * (self.rsw/ (self.attenuation_FC * self.water_height_pathogen))*(1-(exp(-(self.attenuation_FC * self.water_height_pathogen)))),0.0)
        
        #---Sedimentation parameters
        self.FCdecay_sedimentation = pcr.ifthenelse(self.water_height_pathogen > self.threshold_FC_settlingdepth, cover(self.settlingvelocity_FC / self.water_height,0.0), 0)  #day -1
  
    def qualityRouting(self, timeSec):
        
        channelTransFrac = cover(pcr.max(pcr.min((self.subDischarge * timeSec) / self.channelStorageTimeBefore, 1.0),0.0), 0.0)

        #Energy (for water temperature) routing 
        #self.volumeEW = self.volumeEW + (self.PowTwload * timeSec) # Add heat effluents from power plants (J s-1 * s)
        dtotEWLat= channelTransFrac*self.volumeEW
        self.volumeEW = (self.volumeEW +pcr.upstream(self.lddMap,dtotEWLat)-dtotEWLat)

        #Salinity (TDS) routing
        self.routedTDS = self.routedTDS + (self.TDSload *(timeSec/ vos.secondsPerDay()))
        dTDSLat = channelTransFrac*self.routedTDS
        self.routedTDS = (self.routedTDS +pcr.upstream(self.lddMap,dTDSLat)-dTDSLat)        
        
        if self.loadsPerSector:
            self.routedDomTDS = self.routedDomTDS + (self.Dom_TDSload *(timeSec/ vos.secondsPerDay()))
            dDomTDSLat = channelTransFrac*self.routedDomTDS
            self.routedDomTDS = (self.routedDomTDS +pcr.upstream(self.lddMap,dDomTDSLat)-dDomTDSLat) 
            
            self.routedManTDS = self.routedManTDS + (self.Man_TDSload *(timeSec/ vos.secondsPerDay()))
            dManTDSLat = channelTransFrac*self.routedManTDS
            self.routedManTDS = (self.routedManTDS +pcr.upstream(self.lddMap,dManTDSLat)-dManTDSLat)
            
            self.routedUSRTDS = self.routedUSRTDS + (self.USR_TDSload *(timeSec/ vos.secondsPerDay()))
            dUSRTDSLat = channelTransFrac*self.routedUSRTDS
            self.routedUSRTDS = (self.routedUSRTDS +pcr.upstream(self.lddMap,dUSRTDSLat)-dUSRTDSLat)
            
            self.routedIrrTDS = self.routedIrrTDS + (self.Irr_TDSload *(timeSec/ vos.secondsPerDay()))
            dIrrTDSLat = channelTransFrac*self.routedIrrTDS
            self.routedIrrTDS = (self.routedIrrTDS +pcr.upstream(self.lddMap,dIrrTDSLat)-dIrrTDSLat)

        #Organic (BOD) routing
        self.routedBOD = self.routedBOD + (self.BODload *(timeSec/ vos.secondsPerDay()))
        dBODLat = channelTransFrac*self.routedBOD
        self.BODdecay = exp(-(self.BODdecay_temperature)*(timeSec/ vos.secondsPerDay()))
        self.routedBOD = (self.routedBOD +pcr.upstream(self.lddMap,dBODLat)-dBODLat) * self.BODdecay

        if self.loadsPerSector:          
            self.routedDomBOD = self.routedDomBOD + (self.Dom_BODload *(timeSec/ vos.secondsPerDay()))
            dDomBODLat = channelTransFrac*self.routedDomBOD
            self.routedDomBOD = (self.routedDomBOD +pcr.upstream(self.lddMap,dDomBODLat)-dDomBODLat) * self.BODdecay
            
            self.routedManBOD = self.routedManBOD + (self.Man_BODload *(timeSec/ vos.secondsPerDay()))
            dManBODLat = channelTransFrac*self.routedManBOD
            self.routedManBOD = (self.routedManBOD +pcr.upstream(self.lddMap,dManBODLat)-dManBODLat) * self.BODdecay
            
            self.routedUSRBOD = self.routedUSRBOD + (self.USR_BODload *(timeSec/ vos.secondsPerDay()))
            dUSRBODLat = channelTransFrac*self.routedUSRBOD
            self.routedUSRBOD = (self.routedUSRBOD +pcr.upstream(self.lddMap,dUSRBODLat)-dUSRBODLat) * self.BODdecay
            
            self.routedintLivBOD = self.routedintLivBOD + (self.intLiv_BODload *(timeSec/ vos.secondsPerDay()))
            dintLivBODLat = channelTransFrac*self.routedintLivBOD
            self.routedintLivBOD = (self.routedintLivBOD +pcr.upstream(self.lddMap,dintLivBODLat)-dintLivBODLat) * self.BODdecay
            
            self.routedextLivBOD = self.routedextLivBOD + (self.extLiv_BODload *(timeSec/ vos.secondsPerDay()))
            dextLivBODLat = channelTransFrac*self.routedextLivBOD
            self.routedextLivBOD = (self.routedextLivBOD +pcr.upstream(self.lddMap,dextLivBODLat)-dextLivBODLat) * self.BODdecay
     
        #Pathogen (FC) routing
        self.routedFC = self.routedFC + (self.FCload *(timeSec/ vos.secondsPerDay()))
        dFCLat = channelTransFrac*self.routedFC
        self.FCdecay = exp(-(self.FCdecay_temperature + self.FCdecay_solarradiation + self.FCdecay_sedimentation)*(timeSec/ vos.secondsPerDay()))
        self.routedFC = (self.routedFC +pcr.upstream(self.lddMap,dFCLat)-dFCLat) * self.FCdecay

        if self.loadsPerSector:          
            self.routedDomFC = self.routedDomFC + (self.Dom_FCload *(timeSec/ vos.secondsPerDay()))
            dDomFCLat = channelTransFrac*self.routedDomFC
            self.routedDomFC = (self.routedDomFC +pcr.upstream(self.lddMap,dDomFCLat)-dDomFCLat) * self.FCdecay
            
            self.routedManFC = self.routedManFC + (self.Man_FCload *(timeSec/ vos.secondsPerDay()))
            dManFCLat = channelTransFrac*self.routedManFC
            self.routedManFC = (self.routedManFC +pcr.upstream(self.lddMap,dManFCLat)-dManFCLat) * self.FCdecay
            
            self.routedUSRFC = self.routedUSRFC + (self.USR_FCload *(timeSec/ vos.secondsPerDay()))
            dUSRFCLat = channelTransFrac*self.routedUSRFC
            self.routedUSRFC = (self.routedUSRFC +pcr.upstream(self.lddMap,dUSRFCLat)-dUSRFCLat) * self.FCdecay
            
            self.routedintLivFC = self.routedintLivFC + (self.intLiv_FCload *(timeSec/ vos.secondsPerDay()))
            dintLivFCLat = channelTransFrac*self.routedintLivFC
            self.routedintLivFC = (self.routedintLivFC +pcr.upstream(self.lddMap,dintLivFCLat)-dintLivFCLat) * self.FCdecay
            
            self.routedextLivFC = self.routedextLivFC + (self.extLiv_FCload *(timeSec/ vos.secondsPerDay()))
            dextLivFCLat = channelTransFrac*self.routedextLivFC
            self.routedextLivFC = (self.routedextLivFC +pcr.upstream(self.lddMap,dextLivFCLat)-dextLivFCLat) * self.FCdecay
      
        
    def qualityWaterBody(self):
        
        lakeTransFrac = pcr.max(pcr.min((self.WaterBodies.waterBodyOutflow) / (self.waterBodyStorageTimeBefore), 1.0),0.0)
        lakeTransFrac = cover(ifthen(self.WaterBodies.waterBodyOut, lakeTransFrac), 0.0)
        
        #Water temperature (amount of energy in water body)
        energyTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.totEW * self.dynamicFracWat * self.cellArea),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.totEW * self.dynamicFracWat * self.cellArea)
        self.volumeEW = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., energyTotal*lakeTransFrac),energyTotal)
        self.remainingVolumeEW = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * energyTotal), 0.0)
        
        #Salinity (amount of TDS in water body)
        wbTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.routedTDS),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedTDS)
        self.routedTDS = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbTDSTotal*lakeTransFrac),wbTDSTotal)        
        self.wbRemainingTDS = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbTDSTotal), 0.0)
        
        if self.loadsPerSector:
            wbDomTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedDomTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedDomTDS)
            self.routedDomTDS = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbDomTDSTotal*lakeTransFrac),wbDomTDSTotal)
            self.wbRemainingDomTDS = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbDomTDSTotal), 0.0)
            
            wbManTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedManTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedManTDS)
            self.routedManTDS = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbManTDSTotal*lakeTransFrac),wbManTDSTotal)
            self.wbRemainingManTDS = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbManTDSTotal), 0.0)
            
            wbUSRTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedUSRTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedUSRTDS)
            self.routedUSRTDS = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbUSRTDSTotal*lakeTransFrac),wbUSRTDSTotal)
            self.wbRemainingUSRTDS = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbUSRTDSTotal), 0.0)
            
            wbIrrTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedIrrTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedIrrTDS)
            self.routedIrrTDS = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbIrrTDSTotal*lakeTransFrac),wbIrrTDSTotal)
            self.wbRemainingIrrTDS = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbIrrTDSTotal), 0.0)
            
        #Organic (amount of BOD in water body)
        wbBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.routedBOD),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedBOD)
        self.routedBOD = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbBODTotal*lakeTransFrac),wbBODTotal)
        self.wbRemainingBOD = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbBODTotal), 0.0)

        if self.loadsPerSector: 
            wbDomBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedDomBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedDomBOD)
            self.routedDomBOD = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbDomBODTotal*lakeTransFrac),wbDomBODTotal)
            self.wbRemainingDomBOD = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbDomBODTotal), 0.0)
            
            wbManBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedManBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedManBOD)
            self.routedManBOD = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbManBODTotal*lakeTransFrac),wbManBODTotal)
            self.wbRemainingManBOD = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbManBODTotal), 0.0)
            
            wbUSRBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedUSRBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedUSRBOD)
            self.routedUSRBOD = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbUSRBODTotal*lakeTransFrac),wbUSRBODTotal)
            self.wbRemainingUSRBOD = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbUSRBODTotal), 0.0)
            
            wbintLivBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedintLivBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedintLivBOD)
            self.routedintLivBOD = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbintLivBODTotal*lakeTransFrac),wbintLivBODTotal)
            self.wbRemainingintLivBOD = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbintLivBODTotal), 0.0)
            
            wbextLivBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedextLivBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedextLivBOD)
            self.routedextLivBOD = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbextLivBODTotal*lakeTransFrac),wbextLivBODTotal)
            self.wbRemainingextLivBOD = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbextLivBODTotal), 0.0)
        
        #Pathogen (amount of FC in water body)
        wbFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.routedFC),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedFC)
        self.routedFC = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbFCTotal*lakeTransFrac),wbFCTotal)
        self.wbRemainingFC = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbFCTotal), 0.0)
        
        if self.loadsPerSector:
            wbDomFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedDomFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedDomFC)
            self.routedDomFC = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbDomFCTotal*lakeTransFrac),wbDomFCTotal)
            self.wbRemainingDomFC = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbDomFCTotal), 0.0)
            
            wbManFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedManFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedManFC)
            self.routedManFC = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbManFCTotal*lakeTransFrac),wbManFCTotal)
            self.wbRemainingManFC = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbManFCTotal), 0.0)
            
            wbUSRFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedUSRFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedUSRFC)
            self.routedUSRFC = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbUSRFCTotal*lakeTransFrac),wbUSRFCTotal)
            self.wbRemainingUSRFC = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbUSRFCTotal), 0.0)
            
            wbintLivFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedintLivFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedintLivFC)
            self.routedintLivFC = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbintLivFCTotal*lakeTransFrac),wbintLivFCTotal)
            self.wbRemainingintLivFC = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbintLivFCTotal), 0.0)
            
            wbextLivFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedextLivFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedextLivFC)
            self.routedextLivFC = cover(ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0., wbextLivFCTotal*lakeTransFrac),wbextLivFCTotal)
            self.wbRemainingextLivFC = cover(ifthen(self.WaterBodies.waterBodyOut, (1-lakeTransFrac) * wbextLivFCTotal), 0.0)

    def qualityWaterBodyAverage(self,currTimeStep):
                
        #Water temperature (amount of energy averaged over water body)
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
        
        if currTimeStep.timeStepPCR == 1:
            logger.info("Issue with estimating water temperature in first timestep: retrieving water temperature from initial condition")
        else:
            self.waterTemp = pcr.ifthenelse(
                self.temp_water_height > self.critical_water_height,
                self.totEW / self.temp_water_height / (self.specificHeatWater * self.densityWater),
                self.temperatureKelvin
            )
        
        self.waterTemp = min(pcr.ifthenelse(self.waterTemp < self.iceThresTemp + 0.1, self.iceThresTemp + 0.1, self.waterTemp), self.maxThresTemp)
        self.waterTemp_C = self.waterTemp - pcr.scalar(273.15)   #water temperature in gridcell in C
        
        #Salinity (TDS averaged over water body)
        wbTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.routedTDS + self.wbRemainingTDS),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedTDS)        
        self.routedTDS = cover(wbTDSTotal * self.cellArea \
          /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbTDSTotal)
                
        if self.loadsPerSector:        
            wbDomTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedDomTDS + self.wbRemainingDomTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedDomTDS)
            self.routedDomTDS = cover(wbDomTDSTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbDomTDSTotal)
            
            wbManTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedManTDS + self.wbRemainingManTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedManTDS)
            self.routedManTDS = cover(wbManTDSTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbManTDSTotal)
            
            wbUSRTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedUSRTDS + self.wbRemainingUSRTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedUSRTDS)
            self.routedUSRTDS = cover(wbUSRTDSTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbUSRTDSTotal)
            
            wbIrrTDSTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedIrrTDS + self.wbRemainingIrrTDS),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedIrrTDS)
            self.routedIrrTDS = cover(wbIrrTDSTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbIrrTDSTotal)
        
        #Organic (BOD averaged over water body)
        wbBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.routedBOD + self.wbRemainingBOD),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedBOD)
        self.routedBOD = cover(wbBODTotal * self.cellArea \
          /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbBODTotal)

        if self.loadsPerSector:        
            wbDomBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedDomBOD +self.wbRemainingDomBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedDomBOD)
            self.routedDomBOD = cover(wbDomBODTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbDomBODTotal)
            
            wbManBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedManBOD +self.wbRemainingManBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedManBOD)
            self.routedManBOD = cover(wbManBODTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbManBODTotal)
            
            wbUSRBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedUSRBOD + self.wbRemainingUSRBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedUSRBOD)
            self.routedUSRBOD = cover(wbUSRBODTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbUSRBODTotal)
            
            wbintLivBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedintLivBOD + self.wbRemainingintLivBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedintLivBOD)
            self.routedintLivBOD = cover(wbintLivBODTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbintLivBODTotal)
            
            wbextLivBODTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedextLivBOD + self.wbRemainingextLivBOD),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedextLivBOD)
            self.routedextLivBOD = cover(wbextLivBODTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbextLivBODTotal)
        
        #Pathogen (FC averaged over water body)
        wbFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areatotal(pcr.ifthen(self.landmask,self.routedFC + self.wbRemainingFC),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedFC)
        self.routedFC = cover(wbFCTotal * self.cellArea \
          /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbFCTotal)
        
        if self.loadsPerSector:        
            wbDomFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedDomFC + self.wbRemainingDomFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedDomFC)
            self.routedDomFC = cover(wbDomFCTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbDomFCTotal)
            
            wbManFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedManFC +self.wbRemainingManFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedManFC)
            self.routedManFC = cover(wbManFCTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbManFCTotal)
            
            wbUSRFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedUSRFC +self.wbRemainingUSRFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedUSRFC)
            self.routedUSRFC = cover(wbUSRFCTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbUSRFCTotal)
            
            wbintLivFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedintLivFC +self.wbRemainingintLivFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedintLivFC)
            self.routedintLivFC = cover(wbintLivFCTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbintLivFCTotal)
            
            wbextLivFCTotal = cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
             pcr.areatotal(pcr.ifthen(self.landmask,self.routedextLivFC +self.wbRemainingextLivFC),\
             pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))), self.routedextLivFC)
            self.routedextLivFC = cover(wbextLivFCTotal * self.cellArea \
              /pcr.areatotal(pcr.cover(self.cellArea, 0.0),pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)), wbextLivFCTotal)                        
            
    def estimate_concentrations(self):
        
        # Channel storage with discharge constraint for estimating in-stream concentrations        
        self.channelStorage_Qthres = pcr.ifthenelse(pcr.cover(self.disChanWaterBody,vos.MV) > self.WQ_discharge_threshold, self.channelStorage, vos.MV)
        
        ###---Total dissolved solids concentrations (salinity indicator)
        self.salinity = pcr.ifthenelse(self.channelStorage_Qthres != vos.MV, self.routedTDS / self.channelStorage_Qthres, vos.MV) #non-natural salinity in mg/L
        self.salinity = pcr.ifthenelse(self.salinity != vos.MV, self.salinity + self.backgroundSalinity,self.backgroundSalinity)  # +background salinity
         
        ###---Biological oxygen demand concentrations (organic indicator)
        self.organic = pcr.ifthenelse(self.channelStorage_Qthres != vos.MV, self.routedBOD / self.channelStorage_Qthres, vos.MV) #in mg/l        
                    
        ###---Estimate dissolved oxygen concentration: Streeter-Phelps equation---###
        self.organic_for_DO = pcr.ifthenelse(self.channelStorage > 0.1, self.routedBOD / self.channelStorage, 0.)  # BOD concentration in mg/l [TODO ED..just make self.organic?]
        self.k1 = self.BODdecay_temperature * self.organic_for_DO
        self.DOsat = (1-0.0001148*self.elevation)*exp(-139.34411+(157570.1)/(self.waterTemp)-(66423080.)/(self.waterTemp**2)+(12438000000.)/(self.waterTemp**3)-(862194900000.)/(self.waterTemp**4)) # oxygen saturation in mg/l
        self.velocity = self.avgDischarge / (self.yMean * self.wMean) # velocity assuming rectangular channel (m/s)
        self.k2 = 3.93 * (self.velocity ** 0.5) / (self.yMean ** 1.5) # reaeration rate in /d (O'Connor and Dobbins, 1958)
        self.k2 = pcr.ifthenelse(self.k2 > 1.5, 1.5, pcr.ifthenelse(self.k2 < 0.4, 0.4, self.k2))
        self.dissolved_oxygen = pcr.ifthenelse(self.DO - self.k1 + self.k2 * (self.DOsat - self.DO) < 0.0, 0.0, self.DO - self.k1 + self.k2 * (self.DOsat - self.DO)) # DO concentration in mg/l           
        ###---Fecal coliform concentrations (pathogen indicator)
        self.pathogen = pcr.ifthenelse(self.channelStorage_Qthres != vos.MV, self.routedFC * 100. / self.channelStorage_Qthres, vos.MV) # in cfu/100ml
