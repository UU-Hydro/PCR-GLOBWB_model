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

import re
import types

import netCDF4 as nc
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
from ncConverter import *

class LandCover(object):

    def __init__(self,iniItems,nameOfSectionInIniFile,soil_and_topo_parameters,landmask,irrigationEfficiency,usingAllocSegments = False):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        self.iniItems = iniItems
        
        # number of soil layers:
        self.numberOfSoilLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])

        # soil and topo parameters
        self.parameters = soil_and_topo_parameters
        
        # configuration for a certain land cover type
        self.iniItemsLC = iniItems.__getattribute__(nameOfSectionInIniFile)
        self.name = self.iniItemsLC['name']

        # limitAbstraction
        self.limitAbstraction = False
        if iniItems.landSurfaceOptions['limitAbstraction'] == "True": self.limitAbstraction = True
        
        # if using MODFLOW, limitAbstraction must be True (the abstraction cannot exceed storGroundwater)
        if "useMODFLOW" in iniItems.groundwaterOptions.keys():
            if iniItems.groundwaterOptions["useMODFLOW"] == "True": self.limitAbstraction = True
        
        # includeIrrigation
        self.includeIrrigation = False
        if iniItems.landSurfaceOptions['includeIrrigation'] == "True": self.includeIrrigation = True
        
        # irrigation efficiency map (dimensionless)
        self.irrigationEfficiency = irrigationEfficiency

        # interception module type
        # - "Original" is principally the same as defined in van Beek et al., 2014 (default)
        # - "Modified" is with a modification by Edwin Sutanudjaja: extending interception definition, using totalPotET for the available energy  
        self.interceptionModuleType = "Original"
        if "interceptionModuleType" in self.iniItemsLC.keys():
            if self.iniItemsLC['interceptionModuleType'] == "Modified":
                msg = 'Using the "Modified" version of the interception module (i.e. extending interception definition, using totalPotET for the available energy for the interception process).'
                logger.info(msg)
                self.interceptionModuleType = "Modified"            
            else:
                if self.iniItemsLC['interceptionModuleType'] != "Original":
                    msg = 'The interceptionModuleType '+self.iniItemsLC['interceptionModuleType']+' is NOT known.'
                    logger.info(msg)
                msg = 'The "Original" interceptionModuleType is used.'
                logger.info(msg)
        
        # minimum interception capacity (only used if interceptionModuleType == "Modified", extended interception definition)
        self.minInterceptCap = 0.0
        if self.interceptionModuleType == "Original" and "minInterceptCap" in self.iniItemsLC.keys():
            msg = 'As the "Original" interceptionModuleType is used, the "minInterceptCap" value is ignored. The interception scope is only "canopy".'
            logger.warning(msg)
        if self.interceptionModuleType == "Modified":
            self.minInterceptCap = vos.readPCRmapClone(self.iniItemsLC['minInterceptCap'], self.cloneMap,
                                                       self.tmpDir, self.inputDir)
        
        #~ # option to assume surface water as the first priority/alternative for water source - STILL NOT USED
        #~ self.surfaceWaterPriority = False
        
        # option to activate water balance check
        self.debugWaterBalance = True
        if self.iniItemsLC['debugWaterBalance'] == "False": self.debugWaterBalance = False

        # Improved Arno Scheme's method:
        # - In the "Original" work of van Beek et al., 2011 there is no "directRunoff reduction"
        # - However, later (20 April 2011), Rens van Beek introduce this reduction, particularly to maintain soil saturation. This is currently the "Default" method. 
        self.improvedArnoSchemeMethod = "Default"
        if "improvedArnoSchemeMethod" in iniItems.landSurfaceOptions.keys():
            self.improvedArnoSchemeMethod = iniItems.landSurfaceOptions['improvedArnoSchemeMethod']
            if self.improvedArnoSchemeMethod == "Original": logger.warning("Using the old/original approach of Improved Arno Scheme. No reduction for directRunoff.")

        # In the original oldcalc script of Rens (2 layer model), the percolation percUpp (P1) can be negative
        # - To avoid this, Edwin changed few lines (see the method updateSoilStates)
        self.allowNegativePercolation = False
        if 'allowNegativePercolation' in self.iniItemsLC.keys() and self.iniItemsLC['allowNegativePercolation'] == "True":
            msg  = 'Allowing negative values of percolation percUpp (P1), as done in the oldcalc script of PCR-GLOBWB 1.0. \n'
            msg += 'Note that this option is only relevant for the two layer soil model.'
            logger.warning(msg)
            self.allowNegativePercolation = True
        
        # In the original oldcalc script of Rens, there is a possibility that rootFraction/transpiration is only defined in the bottom layer, while no root in upper layer(s) 
        # - To avoid this, Edwin changed few lines (see the methods 'scaleRootFractionsFromTwoLayerSoilParameters' and 'estimateTranspirationAndBareSoilEvap')
        self.usingOriginalOldCalcRootTranspirationPartitioningMethod = False
        if 'usingOriginalOldCalcRootTranspirationPartitioningMethod' in self.iniItemsLC.keys() and self.iniItemsLC['usingOriginalOldCalcRootTranspirationPartitioningMethod'] == "True":
            msg  = 'Using the original rootFraction/transpiration as defined in the oldcalc script of PCR-GLOBWB 1.0. \n'
            msg += 'There is a possibility that rootFraction/transpiration is only defined in the bottom layer, while no root in upper layer(s).'
            logger.warning(msg)
            self.usingOriginalOldCalcRootTranspirationPartitioningMethod = True

        # get snow module type and its parameters:
        self.snowModuleType = self.iniItemsLC['snowModuleType']
        snowParams      = ['freezingT',
                           'degreeDayFactor',
                           'snowWaterHoldingCap',
                           'refreezingCoeff']
        for var in snowParams:
            input = self.iniItemsLC[str(var)]
            vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)
            vars(self)[var] = pcr.spatial(pcr.scalar(vars(self)[var]))
        

        # initialization some variables
        self.fractionArea        = None           # area (m2) of a certain land cover type ; will be assigned by the landSurface module
        self.naturalFracVegCover = None           # fraction (-) of natural area over (entire) cell ; will be assigned by the landSurface module
        self.irrTypeFracOverIrr  = None           # fraction (m2) of a certain irrigation type over (only) total irrigation area ; will be assigned by the landSurface module
        
        # previous fractions of land cover (needed for transfering states when land cover fraction (annualy) changes
        self.previousFracVegCover = None

        # number of soil layers (two or three)
        self.numberOfLayers = self.parameters.numberOfLayers

        # an option to introduce changes of land cover parameters (not only fracVegCover)
        self.noAnnualChangesInLandCoverParameter = True
        if 'annualChangesInLandCoverParameters' in iniItems.landSurfaceOptions.keys():
            if iniItems.landSurfaceOptions['annualChangesInLandCoverParameters'] == "True": self.noAnnualChangesInLandCoverParameter = False
        
        # get land cover parameters that are fixed for the entire simulation
        if self.noAnnualChangesInLandCoverParameter: 
            if self.numberOfLayers == 2: 
                self.fracVegCover, self.arnoBeta, self.rootZoneWaterStorageMin, self.rootZoneWaterStorageRange, \
                                   self.maxRootDepth, self.adjRootFrUpp, self.adjRootFrLow = \
                                   self.get_land_cover_parameters() 
            if self.numberOfLayers == 3: 
                self.fracVegCover, self.arnoBeta, self.rootZoneWaterStorageMin, self.rootZoneWaterStorageRange, \
                                   self.maxRootDepth, self.adjRootFrUpp000005, self.adjRootFrUpp005030, self.adjRootFrLow030150 = \
                                   self.get_land_cover_parameters()
            # estimate parameters while transpiration is being halved
            self.calculateParametersAtHalfTranspiration()
            # calculate TAW for estimating irrigation gross demand
            if self.includeIrrigation: self.calculateTotAvlWaterCapacityInRootZone()

        # get additional land cover parameters (ALWAYS fixed for the entire simulation)
        landCovParamsAdd = ['minTopWaterLayer',
                            'minCropKC']
        for var in landCovParamsAdd:
            input = self.iniItemsLC[str(var)]
            vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)
            if input != "None":\
               vars(self)[var] = pcr.cover(vars(self)[var],0.0)                                

        # get additional parameter(s) for irrigation areas (ALWAYS fixed for the entire simulation)
        if self.includeIrrigation:
             # - cropDeplFactor (dimesionless, crop depletion factor while irrigation is being applied), needed for NON paddy irrigation areas
             if self.iniItemsLC['name'].startswith('irr') and self.name != "irrPaddy":
                 self.cropDeplFactor = vos.readPCRmapClone(self.iniItemsLC['cropDeplFactor'], self.cloneMap, \
                                                           self.tmpDir, self.inputDir)
             # - infiltration/percolation losses for paddy fields
             if self.name == 'irrPaddy' or self.name == 'irr_paddy':\
                 self.design_percolation_loss = self.estimate_paddy_infiltration_loss(self.iniItemsLC)
        
        # water allocation zones:
        self.usingAllocSegments = usingAllocSegments # water allocation option:
        if self.usingAllocSegments:
        
            # cellArea (unit: m2)                         # TODO: If possible, integrate this one with the one coming from the routing module
            cellArea = vos.readPCRmapClone(\
              iniItems.routingOptions['cellAreaMap'],
              self.cloneMap, self.tmpDir, self.inputDir)
            cellArea = pcr.ifthen(self.landmask, cellArea)                  

            # reading the allocation zone file
            self.allocSegments = vos.readPCRmapClone(\
             iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater'],
             self.cloneMap,self.tmpDir,self.inputDir,isLddMap=False,cover=None,isNomMap=True)
            self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)
            self.allocSegments = pcr.clump(self.allocSegments)
        
            # extrapolate it 
            self.allocSegments = pcr.cover(self.allocSegments, \
                                           pcr.windowmajority(self.allocSegments, 0.5))
            self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)
            
            # clump it and cover the rests with cell ids 
            self.allocSegments = pcr.clump(self.allocSegments)
            cell_ids = pcr.mapmaximum(pcr.scalar(self.allocSegments)) + pcr.scalar(100.0) + pcr.uniqueid(pcr.boolean(1.0))
            self.allocSegments = pcr.cover(self.allocSegments, pcr.nominal(cell_ids))                               
            self.allocSegments = pcr.clump(self.allocSegments)
            self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)
        
            # zonal/segment areas (unit: m2)
            self.segmentArea = pcr.areatotal(pcr.cover(cellArea, 0.0), self.allocSegments)
            self.segmentArea = pcr.ifthen(self.landmask, self.segmentArea)

        # option to prioritize local sources before abstracting water from neighboring cells
        self.prioritizeLocalSourceToMeetWaterDemand = iniItems.landSurfaceOptions['prioritizeLocalSourceToMeetWaterDemand'] == "True"
        if self.prioritizeLocalSourceToMeetWaterDemand:
            msg = "Local water sources are first used before abstracting water from neighboring cells"
            logger.info(msg)
        
        # option to give the priority in satisfying sectoral water demands:   
        if "prioritizeDomesticThenIndutrialThenLivestock" not in iniItems.landSurfaceOptions.keys():
            msg  = "The option 'prioritizeDomesticThenIndutrialThenLivestock' is not defined in the landSurfaceOptions. \n"
            msg += "This run assumes False."
            logger.info(msg)
            iniItems.landSurfaceOptions['prioritizeDomesticThenIndutrialThenLivestock'] = "False"
        self.prioritizeDomesticThenIndutrialThenLivestock = iniItems.landSurfaceOptions['prioritizeDomesticThenIndutrialThenLivestock'] == "True"
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            msg = "Priority order in satisfying sectoral water demands: 1) Domestic; 2) Industry; 3) Livestock; 4) Agriculture/Irrigation"
            logger.info(msg)
        
        self.doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity = False
        if 'doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity' in self.iniItems.groundwaterOptions.keys() and\
            self.iniItems.groundwaterOptions['doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity'] == "True":
            logger.info('Groundwater pumping capacity should not limit groundwater abstraction to meet domestic, industrial and livestock water demand.')
            self.doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity = True

        self.optimizeSurfaceWaterBasedOnRatioOfBaseflowDischargeAllocationScheme = False
        if 'optimizeSurfaceWaterBasedOnRatioOfBaseflowDischargeAllocationScheme' in self.iniItems.landSurfaceOptions.keys() and\
            self.iniItems.landSurfaceOptions['optimizeSurfaceWaterBasedOnRatioOfBaseflowDischargeAllocationScheme'] == "True":
            logger.info('Surface water use will be optimized based on ratio of baseflow and discharge allocation scheme.')
            self.optimizeSurfaceWaterBasedOnRatioOfBaseflowDischargeAllocationScheme = True
        
        # get the names of cropCoefficient files:
        self.cropCoefficientNC = vos.getFullPath(self.iniItemsLC['cropCoefficientNC'], self.inputDir)

        
        # get the file names of interceptCap and coverFraction files:
        if 'interceptCapNC' in self.iniItemsLC.keys() and 'coverFractionNC' in self.iniItemsLC.keys():
            self.interceptCapNC = vos.getFullPath(\
                       self.iniItemsLC['interceptCapNC'], self.inputDir)
            self.coverFractionNC = vos.getFullPath(\
                      self.iniItemsLC['coverFractionNC'], self.inputDir)
        else:
			msg = 'The netcdf files for interceptCapNC (interception capacity) and/or coverFraction (canopy cover fraction) are NOT defined for the landCover type: ' + self.name + '\n'
			msg = 'This run assumes zero canopy interception capacity for this run, UNLESS minInterceptCap (minimum interception capacity) is bigger than zero.' + '\n'
			logger.warning(msg)
			self.coverFractionNC = None               
			self.interceptCapNC  = None

        # for reporting: output in netCDF files:
        self.report = True
        try:
            self.outDailyTotNC = self.iniItemsLC['outDailyTotNC'].split(",")
            self.outMonthTotNC = self.iniItemsLC['outMonthTotNC'].split(",")
            self.outMonthAvgNC = self.iniItemsLC['outMonthAvgNC'].split(",")
            self.outMonthEndNC = self.iniItemsLC['outMonthEndNC'].split(",")
        except:
            self.report = False
        if self.report:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            # prepare the netCDF objects and files:
            if self.outDailyTotNC[0] != "None":    
                for var in self.outDailyTotNC:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/" + \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                     "dailyTot.nc",\
                                     var,"undefined")
        
            # monthly output in netCDF files:
            # - cummulative
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initiating monthlyVarTot (accumulator variable):
                    vars(self)[var+'Tot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                                "monthTot.nc",\
                                                    var,"undefined")
            # - average
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # initiating monthlyVarAvg:
                    vars(self)[var+'Avg'] = None
                    # initiating monthlyTotAvg (accumulator variable)
                    vars(self)[var+'Tot'] = None
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                                "monthAvg.nc",\
                                                    var,"undefined")
            # - last day of the month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                                "monthEnd.nc",\
                                                    var,"undefined")


    def updateIrrigationWaterEfficiency(self,currTimeStep):
        #-RvB: irrigation water efficiency
        # this reads in the irrigation water efficiency from the configuration file
        # at the start of each calendar year - it can optionally handle netCDF files,
        # PCRaster maps or values

        var = 'irrigationWaterEfficiency'

        if var in self.iniItemsLC.keys() or 'irrigationEfficiency' in self.iniItemsLC.keys() and (self.iniItemsLC['name'].startswith('irr')):

            msg = "Irrigation efficiency is set based on the file defined in the landCoverOptions."
            
            if 'irrigationWaterEfficiency' in self.iniItemsLC.keys():
                self.iniItemsLC[var] = self.iniItemsLC['irrigationWaterEfficiency']

            input = self.iniItemsLC[var]

            try:
            				# static input
            				self.irrigationEfficiency = vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)
            except:
            				# dynamic input
            				if 'nc' in os.path.splitext(input)[1]:
            					#-netCDF file
            					ncFileIn = vos.getFullPath(input,self.inputDir)
            					self.irrigationEfficiency = vos.netcdf2PCRobjClone(ncFileIn,var, \
                           currTimeStep, useDoy = 'yearly',\
                           cloneMapFileName = self.cloneMap)
            				else:
            					#-assumed PCRaster file, add year and '.map' extension
            					input= input + '%04d.map' % currTimeStep.year
            					self.irrigationEfficiency = vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)
            
            # extrapolate efficiency map:                                                # TODO: Make a better extrapolation algorithm (considering cell size, etc.). 
            window_size = 1.25 * pcr.clone().cellSize()
            window_size = min(window_size, min(pcr.clone().nrRows(), pcr.clone().nrCols())*pcr.clone().cellSize())
            try:
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, window_size))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, window_size))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, window_size))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, window_size))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, window_size))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, 0.75))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, 1.00))
                self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, pcr.windowaverage(self.irrigationEfficiency, 1.50))
            except:                                                 
                pass

            self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency, 1.0)
            self.irrigationEfficiency = pcr.max(0.1, self.irrigationEfficiency)
            self.irrigationEfficiency = pcr.ifthen(self.landmask, self.irrigationEfficiency)

        else:

            msg = "Irrigation efficiency is set based on the file defined in the landSurfaceOptions (for irrigated land cover types only)."
        
        logger.info(msg)    


    def get_land_cover_parameters(self, date_in_string = None, get_only_fracVegCover = False):
   
        # obtain the land cover parameters 
        
        # list of model parameters that will be read
        landCovParams = ['minSoilDepthFrac', 'maxSoilDepthFrac',
                            'rootFraction1', 'rootFraction2',
                             'maxRootDepth',
                             'fracVegCover']
        # - and 'arnoBeta'

        # an option to return only fracVegCover
        if get_only_fracVegCover: landCovParams = ['fracVegCover']
        
        # set initial values to None
        lc_parameters = {}
        if get_only_fracVegCover == False: 
            for var in landCovParams+['arnoBeta']: lc_parameters[var] = None
        
        # get parameters that are fixed for the entire simulation:
        if date_in_string == None: 
            
            msg = 'Obtaining the land cover parameters that are fixed for the entire simulation.'
            logger.debug(msg)

            if self.iniItemsLC['landCoverMapsNC'] == str(None):
                # using pcraster maps
                landCoverPropertiesNC = None
                for var in landCovParams:
                    input = self.iniItemsLC[str(var)]
                    lc_parameters[var] = vos.readPCRmapClone(input, self.cloneMap,
                                                             self.tmpDir, self.inputDir)
                    if input != "None":
                        lc_parameters[var] = pcr.cover(lc_parameters[var], 0.0)                                
            else:
                # using netcdf file
                landCoverPropertiesNC = vos.getFullPath(\
                                        self.iniItemsLC['landCoverMapsNC'], self.inputDir)
                for var in landCovParams:
                    lc_parameters[var] = pcr.cover(vos.netcdf2PCRobjCloneWithoutTime(\
                                                   landCoverPropertiesNC, var, \
                                                   cloneMapFileName = self.cloneMap), 0.0)

            # The parameter arnoBeta for the Improved Arno's scheme:
            # - There are three ways in defining arnoBeta. The ranks below indicate their priority:
            #   1. defined as a pcraster map file or a uniform scalar value (i.e. self.iniItemsLC['arnoBeta'])
            #   2. included in the netcdf file (i.e. self.iniItemsLC['landCoverMapsNC'])
            #   3. approximated from the minSoilDepthFrac and maxSoilDepthFrac

            lc_parameters['arnoBeta'] = None
            if 'arnoBeta' not in self.iniItemsLC.keys() and get_only_fracVegCover == False: self.iniItemsLC['arnoBeta'] = "None" 

            # - option one (top priority): using a pcraster file
            if self.iniItemsLC['arnoBeta'] != "None" and get_only_fracVegCover == False: 
                
                logger.debug("The parameter arnoBeta: "+str(self.iniItemsLC['arnoBeta']))
                lc_parameters['arnoBeta'] = vos.readPCRmapClone(self.iniItemsLC['arnoBeta'], self.cloneMap,\
                                                                self.tmpDir, self.inputDir)

            # - option two: included in the netcdf file
            if isinstance(lc_parameters['arnoBeta'], types.NoneType) and landCoverPropertiesNC != None and get_only_fracVegCover == False:   
                                    
                if vos.checkVariableInNC(landCoverPropertiesNC, "arnoBeta"):
                    
                    logger.debug("The parameter arnoBeta is defined in the netcdf file "+str(self.iniItemsLC['arnoBeta']))
                    lc_parameters['arnoBeta'] = vos.netcdf2PCRobjCloneWithoutTime(landCoverPropertiesNC, 'arnoBeta', self.cloneMap)
                                        
            # - option three: approximated from the minSoilDepthFrac and maxSoilDepthFrac
            if isinstance(lc_parameters['arnoBeta'], types.NoneType) and get_only_fracVegCover == False:
   
                logger.debug("The parameter arnoBeta is approximated from the minSoilDepthFrac and maxSoilDepthFrac values.")
                
                # make sure that maxSoilDepthFrac >= minSoilDepthFrac:
                # - Note that maxSoilDepthFrac is needed only for calculating arnoBeta,
                #   while minSoilDepthFrac is needed not only for arnoBeta, but also for rootZoneWaterStorageMin
                lc_parameters['maxSoilDepthFrac'] = pcr.max(lc_parameters['maxSoilDepthFrac'], lc_parameters['minSoilDepthFrac']) 
            
                # estimating arnoBeta from the values of maxSoilDepthFrac and minSoilDepthFrac.
                lc_parameters['arnoBeta'] = pcr.max(0.001,\
                 (lc_parameters['maxSoilDepthFrac']-1.)/(1.-lc_parameters['minSoilDepthFrac'])+\
                                           self.parameters.orographyBeta-0.01)   # Rens's line: BCF[TYPE]= max(0.001,(MAXFRAC[TYPE]-1)/(1-MINFRAC[TYPE])+B_ORO-0.01)
            

        # get landCovParams that (annualy) changes
        # - files provided in netcdf files
        if date_in_string != None: 

            msg = 'Obtaining the land cover parameters (from netcdf files) for the year/date: '+str(date_in_string)
            logger.debug(msg)
            
            if get_only_fracVegCover:
                landCovParams = ['fracVegCover']
            else:
                landCovParams += ['arnoBeta']
            
            for var in landCovParams:
                
                # read parameter values from the ncFile mentioned in the ini/configuration file 
                ini_option = self.iniItemsLC[var+'NC']
                
                if ini_option.endswith(vos.netcdf_suffixes): 
                    netcdf_file = vos.getFullPath(ini_option, self.inputDir)
                    lc_parameters[var] = pcr.cover(
                                         vos.netcdf2PCRobjClone(netcdf_file,var, \
                                                                date_in_string, useDoy = 'yearly',\
                                                                cloneMapFileName = self.cloneMap), 0.0)
                else:                                                
                    # reading parameters from pcraster maps or scalar values
                    try:
                        lc_parameters[var] = pcr.cover(
                                             pcr.spatial(
                                             vos.readPCRmapClone(ini_option, self.cloneMap,\
                                                                 self.tmpDir, self.inputDir)), 0.0)
                    except:
                        lc_parameters[var] = vos.readPCRmapClone(ini_option, self.cloneMap,\
                                                                 self.tmpDir, self.inputDir)

            # if not defined, arnoBeta would be approximated from the minSoilDepthFrac and maxSoilDepthFrac
            if get_only_fracVegCover == False and\
               isinstance(lc_parameters['arnoBeta'], types.NoneType):

                logger.debug("The parameter arnoBeta is approximated from the minSoilDepthFrac and maxSoilDepthFrac values.")

                # make sure that maxSoilDepthFrac >= minSoilDepthFrac:
                # - Note that maxSoilDepthFrac is needed only for calculating arnoBeta,
                #   while minSoilDepthFrac is needed not only for arnoBeta, but also for rootZoneWaterStorageMin
                lc_parameters['maxSoilDepthFrac'] = pcr.max(lc_parameters['maxSoilDepthFrac'], lc_parameters['minSoilDepthFrac']) 
            
                # estimating arnoBeta from the values of maxSoilDepthFrac and minSoilDepthFrac
                lc_parameters['arnoBeta'] = pcr.max(0.001,\
                 (lc_parameters['maxSoilDepthFrac']-1.)/(1.-lc_parameters['minSoilDepthFrac'])+\
                                           self.parameters.orographyBeta-0.01)   # Rens's line: BCF[TYPE]= max(0.001,(MAXFRAC[TYPE]-1)/(1-MINFRAC[TYPE])+B_ORO-0.01)

        # limit 0.0 <= fracVegCover <= 1.0
        fracVegCover = pcr.cover(lc_parameters['fracVegCover'], 0.0)
        fracVegCover = pcr.max(0.0, fracVegCover)
        fracVegCover = pcr.min(1.0, fracVegCover)
        
        if get_only_fracVegCover:
            return pcr.ifthen(self.landmask, fracVegCover)
        
        
        # WMIN (unit: m): minimum local soil water capacity within the grid-cell
        rootZoneWaterStorageMin = lc_parameters['minSoilDepthFrac'] * \
                               self.parameters.rootZoneWaterStorageCap          # This is WMIN in the oldcalc script.
        
        # WMAX - WMIN (unit: m)
        rootZoneWaterStorageRange = \
                               self.parameters.rootZoneWaterStorageCap -\
                                               rootZoneWaterStorageMin

        # the parameter arnoBeta (dimensionless)
        arnoBeta = pcr.max(0.001, lc_parameters['arnoBeta'])
        arnoBeta = pcr.cover(arnoBeta, 0.001)
        
        # maxium root depth
        maxRootDepth = lc_parameters['maxRootDepth']
        
        # saving also minSoilDepthFrac and maxSoilDepthFrac (only for debugging purpose)
        self.minSoilDepthFrac = lc_parameters['minSoilDepthFrac']
        self.maxSoilDepthFrac = lc_parameters['maxSoilDepthFrac']
        
        # saving also rootFraction1 and rootFraction2 (only for debugging purpose)
        self.rootFraction1 = lc_parameters['rootFraction1']
        self.rootFraction2 = lc_parameters['rootFraction2']

        if self.numberOfLayers == 2 and get_only_fracVegCover == False:
            
            # scaling root fractions
            adjRootFrUpp, adjRootFrLow = \
                   self.scaleRootFractionsFromTwoLayerSoilParameters(lc_parameters['rootFraction1'], lc_parameters['rootFraction2'])
            
            # provide all land cover parameters
            return pcr.ifthen(self.landmask, fracVegCover), \
                   pcr.ifthen(self.landmask, arnoBeta), \
                   pcr.ifthen(self.landmask, rootZoneWaterStorageMin), \
                   pcr.ifthen(self.landmask, rootZoneWaterStorageRange), \
                   pcr.ifthen(self.landmask, maxRootDepth), \
                   pcr.ifthen(self.landmask, adjRootFrUpp), \
                   pcr.ifthen(self.landmask, adjRootFrLow) \

        if self.numberOfLayers == 3 and get_only_fracVegCover == False: 
                
            # scaling root fractions
            adjRootFrUpp000005, adjRootFrUpp005030, adjRootFrLow030150 = \
                   self.scaleRootFractionsFromTwoLayerSoilParameters(lc_parameters['rootFraction1'], lc_parameters['rootFraction2'])
            
            # provide all land cover parameters
            return pcr.ifthen(self.landmask, fracVegCover), \
                   pcr.ifthen(self.landmask, arnoBeta), \
                   pcr.ifthen(self.landmask, rootZoneWaterStorageMin), \
                   pcr.ifthen(self.landmask, rootZoneWaterStorageRange), \
                   pcr.ifthen(self.landmask, maxRootDepth), \
                   pcr.ifthen(self.landmask, adjRootFrUpp000005), \
                   pcr.ifthen(self.landmask, adjRootFrUpp005030), \
                   pcr.ifthen(self.landmask, adjRootFrLow030150) \


    def estimate_paddy_infiltration_loss(self, iniPaddyOptions):
        
        # Due to compaction infiltration/percolation loss rate can be much smaller than original soil saturated conductivity
        # - Wada et al. (2014) assume it will be 10 times smaller
        if self.numberOfLayers == 2:\
           design_percolation_loss = self.parameters.kSatUpp/10.           # unit: m/day 
        if self.numberOfLayers == 3:\
           design_percolation_loss = self.parameters.kSatUpp000005/10.     # unit: m/day 

        # However, it can also be much smaller especially in well-puddled paddy fields and should avoid salinization problems.
        # - Default minimum and maximum percolation loss values based on FAO values Reference: http://www.fao.org/docrep/s2022e/s2022e08.htm
        min_percolation_loss = 0.006
        max_percolation_loss = 0.008 
        # - Minimum and maximum percolation loss values given in the ini or configuration file:
        if 'minPercolationLoss' in iniPaddyOptions.keys() and iniPaddyOptions['minPercolationLoss'] != "None":
            min_percolation_loss = vos.readPCRmapClone(iniPaddyOptions['minPercolationLoss'], self.cloneMap, 	
                                                       self.tmpDir, self.inputDir)
        if 'maxPercolationLoss' in iniPaddyOptions.keys() and iniPaddyOptions['maxPercolationLoss'] != "None":
            min_percolation_loss = vos.readPCRmapClone(iniPaddyOptions['maxPercolationLoss'], self.cloneMap, 	
                                                       self.tmpDir, self.inputDir)
        # - percolation loss at paddy fields (m/day)
        design_percolation_loss = pcr.max(min_percolation_loss, \
                                  pcr.min(max_percolation_loss, design_percolation_loss))
        # - if soil condition is already 'good', we will use its original infiltration/percolation rate
        if self.numberOfLayers == 2:\
           design_percolation_loss = pcr.min(self.parameters.kSatUpp      , design_percolation_loss) 
        if self.numberOfLayers == 3:\
           design_percolation_loss = pcr.min(self.parameters.kSatUpp000005, design_percolation_loss)
        
        # PS: The 'design_percolation_loss' is the maximum loss occuring in paddy fields.
        return design_percolation_loss      

    def scaleRootFractionsFromTwoLayerSoilParameters(self, rootFraction1, rootFraction2):
                                         
        # covering rootFraction1 and rootFraction2
        rootFraction1 = pcr.cover(rootFraction1, 0.0)
        rootFraction2 = pcr.cover(rootFraction2, 0.0)
        
        if self.numberOfLayers == 2: 
            # root fractions
            rootFracUpp = (0.30/0.30) * rootFraction1
            rootFracLow = (1.20/1.20) * rootFraction2
            adjRootFrUpp = vos.getValDivZero(rootFracUpp, (rootFracUpp + rootFracLow))
            adjRootFrLow = vos.getValDivZero(rootFracLow, (rootFracUpp + rootFracLow))       
                                                                                            # RFW1[TYPE]= RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE]);
                                                                                            # RFW2[TYPE]= RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE]);
            # if not defined, put everything in the first layer:
            if self.usingOriginalOldCalcRootTranspirationPartitioningMethod == False:
                adjRootFrUpp = pcr.max(0.0, pcr.min(1.0, pcr.cover(adjRootFrUpp,1.0))) 
                adjRootFrLow = pcr.max(0.0, pcr.scalar(1.0) - adjRootFrUpp)
            
            return adjRootFrUpp, adjRootFrLow 

        if self.numberOfLayers == 3: 
            # root fractions
            rootFracUpp000005 = 0.05/0.30 * rootFraction1
            rootFracUpp005030 = 0.25/0.30 * rootFraction1
            rootFracLow030150 = 1.20/1.20 * rootFraction2
            adjRootFrUpp000005 = vos.getValDivZero(rootFracUpp000005, (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150))
            adjRootFrUpp005030 = vos.getValDivZero(rootFracUpp005030, (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150))
            adjRootFrLow030150 = vos.getValDivZero(rootFracLow030150, (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150))
            #
            # if not defined, put everything in the first layer:
            if self.usingOriginalOldCalcRootTranspirationPartitioningMethod == False:
                adjRootFrUpp000005 = pcr.max(0.0, pcr.min(1.0, pcr.cover(adjRootFrUpp000005, 1.0))) 
                adjRootFrUpp005030 = pcr.max(0.0, pcr.ifthenelse(adjRootFrUpp000005 < 1.0, pcr.min(adjRootFrUpp005030, pcr.scalar(1.0) - adjRootFrUpp000005), 0.0)) 
                adjRootFrLow030150 = pcr.max(0.0, pcr.scalar(1.0) - (adjRootFrUpp000005 + adjRootFrUpp005030)) 

            return adjRootFrUpp000005, adjRootFrUpp005030, adjRootFrLow030150 


    def scaleRootFractionsOLD(self):
                                         
        if self.numberOfLayers == 2: 
            # root fractions
            rootFracUpp = (0.30/0.30) * self.rootFraction1
            rootFracLow = (1.20/1.20) * self.rootFraction2
            self.adjRootFrUpp = rootFracUpp / (rootFracUpp + rootFracLow)
            self.adjRootFrLow = rootFracLow / (rootFracUpp + rootFracLow)       # RFW1[TYPE]= RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE]);
            #                                                                   # RFW2[TYPE]= RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE]);
            # if not defined, put everything in the first layer:
            self.adjRootFrUpp = pcr.min(1.0, pcr.cover(self.adjRootFrUpp,1.0)) 
            self.adjRootFrLow = pcr.scalar(1.0) - self.adjRootFrUpp 

        if self.numberOfLayers == 3: 
            # root fractions
            rootFracUpp000005 = 0.05/0.30 * self.rootFraction1
            rootFracUpp005030 = 0.25/0.30 * self.rootFraction1
            rootFracLow030150 = 1.20/1.20 * self.rootFraction2
            self.adjRootFrUpp000005 = rootFracUpp000005 / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)
            self.adjRootFrUpp005030 = rootFracUpp005030 / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)
            self.adjRootFrLow030150 = rootFracLow030150 / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)
            #
            # if not defined, put everything in the first layer:
            self.adjRootFrUpp000005 = pcr.min(1.0, pcr.cover(self.adjRootFrUpp000005, 1.0)) 
            self.adjRootFrUpp005030 = pcr.ifthenelse(self.adjRootFrUpp000005 < 1.0, self.adjRootFrUpp005030, 0.0) 
            self.adjRootFrLow030150 = pcr.scalar(1.0) - (self.adjRootFrUpp000005 + self.adjRootFrUpp005030) 

    def scaleRootFractionsAlternativeOLD(self):
                                         
        if self.numberOfLayers == 2: 
            # root fractions
            rootFracUpp = (0.30/0.30) * self.rootFraction1
            rootFracLow = (1.20/1.20) * self.rootFraction2
            self.adjRootFrUpp = pcr.ifthenelse(rootFracUpp + rootFracLow > 0.0, pcr.min(1.0, rootFracUpp/(rootFracUpp + rootFracLow)), 0.0)
            self.adjRootFrLow = pcr.ifthenelse(rootFracUpp + rootFracLow > 0.0, pcr.min(1.0, rootFracLow/(rootFracUpp + rootFracLow)), 0.0)      
                                                                                
                                                                                # original Rens's line: # weighed root fractions
                                                                                #                        RFW1[TYPE]= if(RFRAC1[TYPE]+RFRAC2[TYPE] > 0,
                                                                                #                        	min(1.0,RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])),0.0);
                                                                                #                        RFW2[TYPE]= if(RFRAC1[TYPE]+RFRAC2[TYPE] > 0.0,
                                                                                #                        	min(1.0,RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE])),0.0);

        if self.numberOfLayers == 3: 
            # root fractions
            rootFracUpp000005 = 0.05/0.30 * self.rootFraction1
            rootFracUpp005030 = 0.25/0.30 * self.rootFraction1
            rootFracLow030150 = 1.20/1.20 * self.rootFraction2
            self.adjRootFrUpp000005 = pcr.ifthenelse(rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150 > 0.0, pcr.min(1.0, rootFracUpp000005/(rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)), 0.0)
            self.adjRootFrUpp005030 = pcr.ifthenelse(rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150 > 0.0, pcr.min(1.0, rootFracUpp005030/(rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)), 0.0)
            self.adjRootFrLow030150 = pcr.ifthenelse(rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150 > 0.0, pcr.min(1.0, rootFracLow030150/(rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)), 0.0)

    def calculateParametersAtHalfTranspiration(self):

        # average soil parameters at which actual transpiration is halved

        if self.numberOfLayers == 2: 

            #~ self.effSatAt50 = \
                             #~ (self.parameters.storCapUpp * \
                                  #~ self.adjRootFrUpp * \
                             #~ (self.parameters.matricSuction50/self.parameters.airEntryValueUpp)**\
                                                     #~ (-1./self.parameters.poreSizeBetaUpp)  +\
                              #~ self.parameters.storCapLow * \
                                  #~ self.adjRootFrLow * \
                             #~ (self.parameters.matricSuction50/self.parameters.airEntryValueLow)**\
                                                     #~ (-1./self.parameters.poreSizeBetaLow)) /\
                         #~ (self.parameters.storCapUpp*self.adjRootFrUpp +\
                          #~ self.parameters.storCapLow*self.adjRootFrLow )     

            #~ self.effPoreSizeBetaAt50 = (\
                          #~ self.parameters.storCapUpp*self.adjRootFrUpp*\
                                       #~ self.parameters.poreSizeBetaUpp +\
                          #~ self.parameters.storCapLow*self.adjRootFrLow*\
                                       #~ self.parameters.poreSizeBetaLow) / (\
                         #~ (self.parameters.storCapUpp*self.adjRootFrUpp +\
                          #~ self.parameters.storCapLow*self.adjRootFrLow ))    

                                                                             # Rens's original line (version 1.1): THEFF_50[TYPE]= (SC1[TYPE]*RFW1[TYPE]*(PSI_50/PSI_A1[TYPE])**(-1/BCH1[TYPE]) +
                                                                             #                                                      SC2[TYPE]*RFW2[TYPE]*(PSI_50/PSI_A2[TYPE])**(-1/BCH2[TYPE])) /
                                                                             #                                                     (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]);
                                                                             #
                                                                             # Rens's modified line (version 1.2): THEFF_50[TYPE]= if(RFW1[TYPE]+RFW2[TYPE] > 0,   
                                                                             #                                         (SC1[TYPE]*RFW1[TYPE]*(PSI_50/PSI_A1[TYPE])**(-1/BCH1[TYPE])+
                                                                             #                                         SC2[TYPE]*RFW2[TYPE]*(PSI_50/PSI_A2[TYPE])**(-1/BCH2[TYPE]))/
                                                                             #                                         (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]),0.5);
            
                                                                             # Rens's original liner (version 1.1): BCH_50 = (SC1[TYPE]*RFW1[TYPE]*BCH1[TYPE]+SC2[TYPE]*RFW2[TYPE]*BCH2[TYPE])/
                                                                             #                                               (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]);
                                                                             #
                                                                             # Rens's original lines (version 1.1): BCH_50= if(RFW1[TYPE]+RFW2[TYPE] > 0,(SC1[TYPE]*RFW1[TYPE]*BCH1[TYPE]+SC2[TYPE]*RFW2[TYPE]*BCH2[TYPE])/
                                                                             #                                                                           (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]),0.5*(BCH1[TYPE]+BCH2[TYPE]));


            denominator = (self.parameters.storCapUpp*self.adjRootFrUpp +
                           self.parameters.storCapLow*self.adjRootFrLow )

            self.effSatAt50 = pcr.ifthenelse(denominator > 0.0,\
                             (self.parameters.storCapUpp * \
                                  self.adjRootFrUpp * \
                             (self.parameters.matricSuction50/self.parameters.airEntryValueUpp)**\
                                                     (-1./self.parameters.poreSizeBetaUpp)  +\
                              self.parameters.storCapLow * \
                                  self.adjRootFrLow * \
                             (self.parameters.matricSuction50/self.parameters.airEntryValueLow)**\
                                                     (-1./self.parameters.poreSizeBetaLow)) /\
                         (self.parameters.storCapUpp*self.adjRootFrUpp +\
                          self.parameters.storCapLow*self.adjRootFrLow ), 0.5)     
            
            self.effPoreSizeBetaAt50 = pcr.ifthenelse(denominator > 0.0,\
                         (self.parameters.storCapUpp*self.adjRootFrUpp*\
                                       self.parameters.poreSizeBetaUpp +\
                          self.parameters.storCapLow*self.adjRootFrLow*\
                                       self.parameters.poreSizeBetaLow) / (\
                         (self.parameters.storCapUpp*self.adjRootFrUpp +\
                          self.parameters.storCapLow*self.adjRootFrLow )), 0.5*(self.parameters.poreSizeBetaUpp + self.parameters.poreSizeBetaLow))    
                                                                             
                                                                             

        if self.numberOfLayers == 3: 
        
            #~ self.effSatAt50 = (self.parameters.storCapUpp000005 * \
                                   #~ self.adjRootFrUpp000005 * \
                              #~ (self.parameters.matricSuction50/self.parameters.airEntryValueUpp000005)**\
                                                      #~ (-1./self.parameters.poreSizeBetaUpp000005) +\
                               #~ self.parameters.storCapUpp005030 * \
                                   #~ self.adjRootFrUpp005030 * \
                              #~ (self.parameters.matricSuction50/self.parameters.airEntryValueUpp000005)**\
                                                      #~ (-1./self.parameters.poreSizeBetaUpp000005) +\
                               #~ self.parameters.storCapLow030150 * \
                                   #~ self.adjRootFrLow030150 * \
                              #~ (self.parameters.matricSuction50/self.parameters.airEntryValueLow030150)**\
                                                      #~ (-1./self.parameters.poreSizeBetaLow030150) /\
                         #~ (self.parameters.storCapUpp000005*self.adjRootFrUpp000005 +\
                          #~ self.parameters.storCapUpp005030*self.adjRootFrUpp005030 +\
                          #~ self.parameters.storCapLow030150*self.adjRootFrLow030150 ))

            #~ self.effPoreSizeBetaAt50 = (\
                          #~ self.parameters.storCapUpp000005*self.adjRootFrUpp000005*\
                                             #~ self.parameters.poreSizeBetaUpp000005 +\
                          #~ self.parameters.storCapUpp005030*self.adjRootFrUpp005030*\
                                             #~ self.parameters.poreSizeBetaUpp005030 +\
                          #~ self.parameters.storCapLow030150*self.adjRootFrLow030150*\
                                             #~ self.parameters.poreSizeBetaLow030150) / \
                         #~ (self.parameters.storCapUpp000005*self.adjRootFrUpp000005 +\
                          #~ self.parameters.storCapUpp005030*self.adjRootFrUpp005030 +\
                          #~ self.parameters.storCapLow030150*self.adjRootFrLow030150 )

            denominator = (self.parameters.storCapUpp000005*self.adjRootFrUpp000005 +
                           self.parameters.storCapUpp005030*self.adjRootFrUpp005030 +
                           self.parameters.storCapLow030150*self.adjRootFrLow030150 )

            self.effSatAt50 = pcr.ifthenelse(denominator > 0.0,\
                              (self.parameters.storCapUpp000005 * \
                                   self.adjRootFrUpp000005 * \
                              (self.parameters.matricSuction50/self.parameters.airEntryValueUpp000005)**\
                                                      (-1./self.parameters.poreSizeBetaUpp000005) +\
                               self.parameters.storCapUpp005030 * \
                                   self.adjRootFrUpp005030 * \
                              (self.parameters.matricSuction50/self.parameters.airEntryValueUpp000005)**\
                                                      (-1./self.parameters.poreSizeBetaUpp000005) +\
                               self.parameters.storCapLow030150 * \
                                   self.adjRootFrLow030150 * \
                              (self.parameters.matricSuction50/self.parameters.airEntryValueLow030150)**\
                                                      (-1./self.parameters.poreSizeBetaLow030150) /\
                         (self.parameters.storCapUpp000005*self.adjRootFrUpp000005 +\
                          self.parameters.storCapUpp005030*self.adjRootFrUpp005030 +\
                          self.parameters.storCapLow030150*self.adjRootFrLow030150 )), 0.5)

            self.effPoreSizeBetaAt50 = pcr.ifthenelse(denominator > 0.0,\
                         (self.parameters.storCapUpp000005*self.adjRootFrUpp000005*\
                                             self.parameters.poreSizeBetaUpp000005 +\
                          self.parameters.storCapUpp005030*self.adjRootFrUpp005030*\
                                             self.parameters.poreSizeBetaUpp005030 +\
                          self.parameters.storCapLow030150*self.adjRootFrLow030150*\
                                             self.parameters.poreSizeBetaLow030150) / \
                         (self.parameters.storCapUpp000005*self.adjRootFrUpp000005 +\
                          self.parameters.storCapUpp005030*self.adjRootFrUpp005030 +\
                          self.parameters.storCapLow030150*self.adjRootFrLow030150 ), 0.5 * (0.5*(self.parameters.poreSizeBetaUpp000005 + \
                                                                                                  self.parameters.poreSizeBetaUpp005030) + self.parameters.poreSizeBetaLow030150))

        # I don't think that we need the following items.
        self.effSatAt50 = pcr.cover(self.effSatAt50, 0.5)
        if self.numberOfLayers == 2: self.effPoreSizeBetaAt50 = pcr.cover(self.effPoreSizeBetaAt50, 0.5*(self.parameters.poreSizeBetaUpp + self.parameters.poreSizeBetaLow))    
        if self.numberOfLayers == 3: self.effPoreSizeBetaAt50 = pcr.cover(self.effPoreSizeBetaAt50, 0.5 * (0.5*(self.parameters.poreSizeBetaUpp000005 + \
                                                                                                                self.parameters.poreSizeBetaUpp005030) + self.parameters.poreSizeBetaLow030150))
        
        # crop only to the landmask region
        self.effSatAt50 = pcr.ifthen(self.landmask, self.effSatAt50)
        self.effPoreSizeBetaAt50 = pcr.ifthen(self.landmask, self.effPoreSizeBetaAt50)

    def calculateTotAvlWaterCapacityInRootZone(self):

        # total water capacity in the root zone (upper soil layers)
        # Note: This is dependent on the land cover type.

        if self.numberOfLayers == 2: 

            self.totAvlWater = \
                               (pcr.max(0.,\
                               self.parameters.effSatAtFieldCapUpp - self.parameters.effSatAtWiltPointUpp))*\
                               (self.parameters.satVolMoistContUpp -   self.parameters.resVolMoistContUpp )*\
                        pcr.min(self.parameters.thickUpp,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                               self.parameters.effSatAtFieldCapLow - self.parameters.effSatAtWiltPointLow))*\
                               (self.parameters.satVolMoistContLow -   self.parameters.resVolMoistContLow )*\
                        pcr.min(self.parameters.thickLow,\
                        pcr.max(self.maxRootDepth-self.parameters.thickUpp,0.))      # Edwin modified this line. Edwin uses soil thickness thickUpp and thickLow (instead of storCapUpp and storCapLow). 
                                                                                     # And Rens support this. 
            self.totAvlWater = pcr.min(self.totAvlWater, \
                            self.parameters.storCapUpp + self.parameters.storCapLow)

        if self.numberOfLayers == 3: 

            self.totAvlWater = \
                               (pcr.max(0.,\
                               self.parameters.effSatAtFieldCapUpp000005 - self.parameters.effSatAtWiltPointUpp000005))*\
                               (self.parameters.satVolMoistContUpp000005 -   self.parameters.resVolMoistContUpp000005 )*\
                        pcr.min(self.parameters.thickUpp000005,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                               self.parameters.effSatAtFieldCapUpp005030 - self.parameters.effSatAtWiltPointUpp005030))*\
                               (self.parameters.satVolMoistContUpp005030 -   self.parameters.resVolMoistContUpp005030 )*\
                        pcr.min(self.parameters.thickUpp005030,\
                        pcr.max(self.maxRootDepth-self.parameters.thickUpp000005))  + \
                               (pcr.max(0.,\
                               self.parameters.effSatAtFieldCapLow030150 - self.parameters.effSatAtWiltPointLow030150))*\
                               (self.parameters.satVolMoistContLow030150 -   self.parameters.resVolMoistContLow030150 )*\
                        pcr.min(self.parameters.thickLow030150,\
                        pcr.max(self.maxRootDepth-self.parameters.thickUpp005030,0.)) 
            #
            self.totAvlWater = pcr.min(self.totAvlWater, \
                               self.parameters.storCapUpp000005 + \
                               self.parameters.storCapUpp005030 + \
                               self.parameters.storCapLow030150)

        
    def getICsLC(self,iniItems,iniConditions = None):

        if self.numberOfLayers == 2: 
        
            # List of state and flux variables:
            initialVars  = ['interceptStor',
                            'snowCoverSWE','snowFreeWater',
                            'topWaterLayer',
                            'storUpp',
                            'storLow',
                            'interflow']
            for var in initialVars:
                if iniConditions == None:
                    input = self.iniItemsLC[str(var)+'Ini']
                    vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                    self.tmpDir,self.inputDir)
                    vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                else:
                    vars(self)[var] = iniConditions[str(var)]
                vars(self)[var] = pcr.ifthen(self.landmask,vars(self)[var])

        if self.numberOfLayers == 3: 

            # List of state and flux variables:
            initialVars  = ['interceptStor',
                            'snowCoverSWE','snowFreeWater',
                            'topWaterLayer',
                            'storUpp000005','storUpp005030',
                            'storLow030150',
                            'interflow']
            for var in initialVars:
                if iniConditions == None:
                    input = self.iniItemsLC[str(var)+'Ini']
                    vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                    self.tmpDir,self.inputDir,
                                                    cover = 0.0)
                    vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                else:
                    vars(self)[var] = iniConditions[str(var)]
                vars(self)[var] = pcr.ifthen(self.landmask,vars(self)[var])

    def updateLC(self,meteo,groundwater,routing,\
                 capRiseFrac,\
                 nonIrrGrossDemandDict,swAbstractionFractionDict,\
                 currTimeStep,\
                 allocSegments,\
                 desalinationWaterUse,\
                 groundwater_pumping_region_ids,\
                 regionalAnnualGroundwaterAbstractionLimit):

        # get land cover parameters at the first day of the year or the first day of the simulation
        if self.noAnnualChangesInLandCoverParameter == False and\
           (currTimeStep.timeStepPCR == 1 or currTimeStep.doy == 1): 
            if self.numberOfLayers == 2: 
                self.fracVegCover, self.arnoBeta, self.rootZoneWaterStorageMin, self.rootZoneWaterStorageRange, \
                                   self.maxRootDepth, self.adjRootFrUpp, self.adjRootFrLow = \
                                   self.get_land_cover_parameters(currTimeStep.fulldate) 
            if self.numberOfLayers == 3: 
                self.fracVegCover, self.arnoBeta, self.rootZoneWaterStorageMin, self.rootZoneWaterStorageRange, \
                                   self.maxRootDepth, self.adjRootFrUpp000005, self.adjRootFrUpp005030, self.adjRootFrLow030150 = \
                                   self.get_land_cover_parameters(currTimeStep.fulldate)
            # estimate parameters while transpiration is being halved
            self.calculateParametersAtHalfTranspiration()
            # calculate TAW for estimating irrigation gross demand
            if self.includeIrrigation: self.calculateTotAvlWaterCapacityInRootZone()

        # calculate total PotET (based on meteo and cropKC)
        self.getPotET(meteo,currTimeStep) 
        
        # calculate interception evaporation flux (m/day) and update interception storage (m)
        self.interceptionUpdate(meteo, currTimeStep)    	 

        # calculate snow melt (or refreezing)
        if self.snowModuleType  == "Simple": self.snowMeltHBVSimple(meteo,currTimeStep)
        # TODO: Define other snow modules

        # calculate qDR & qSF & q23 (and update storages)
        self.upperSoilUpdate(meteo, \
                             groundwater, \
                             routing, \
                             capRiseFrac, \
                             nonIrrGrossDemandDict, 
                             swAbstractionFractionDict,\
                             currTimeStep, \
                             allocSegments, \
                             desalinationWaterUse, \
                             groundwater_pumping_region_ids,regionalAnnualGroundwaterAbstractionLimit)

        # saturation degrees (needed only for reporting):
        if self.numberOfSoilLayers == 2:
            self.satDegUpp = vos.getValDivZero(\
                  self.storUpp, self.parameters.storCapUpp,\
                  vos.smallNumber,0.)
            self.satDegUpp = pcr.ifthen(self.landmask, self.satDegUpp)
            self.satDegLow = vos.getValDivZero(\
                  self.storLow, self.parameters.storCapLow,\
                  vos.smallNumber,0.)
            self.satDegLow = pcr.ifthen(self.landmask, self.satDegLow)

            self.satDegUppTotal = self.satDegUpp
            self.satDegLowTotal = self.satDegLow

        if self.numberOfSoilLayers == 3:
            self.satDegUpp000005 = vos.getValDivZero(\
                  self.storUpp000005, self.parameters.storCapUpp000005,\
                  vos.smallNumber,0.)
            self.satDegUpp000005 = pcr.ifthen(self.landmask, self.satDegUpp000005)
            self.satDegUpp005030 = vos.getValDivZero(\
                  self.storUpp005030, self.parameters.storCapUpp005030,\
                  vos.smallNumber,0.)
            self.satDegUpp005030 = pcr.ifthen(self.landmask, self.satDegUpp005030)
            self.satDegLow030150 = vos.getValDivZero(\
                  self.storLow030150, self.parameters.storCapLow030150,\
                  vos.smallNumber,0.)
            self.satDegLow030150 = pcr.ifthen(self.landmask, self.satDegLow030150)

            self.satDegUppTotal  = vos.getValDivZero(\
                  self.storUpp000005 + self.storUpp005030,\
                  self.parameters.storCapUpp000005 + \
                  self.parameters.storCapUpp005030,\
                  vos.smallNumber,0.)
            self.satDegUppTotal = pcr.ifthen(self.landmask, self.satDegUppTotal)
            self.satDegLowTotal = self.satDegLow030150
        
        if self.report == True:
            # writing Output to netcdf files
            # - daily output:
            timeStamp = datetime.datetime(currTimeStep.year,\
                                          currTimeStep.month,\
                                          currTimeStep.day,\
                                          0)
            timestepPCR = currTimeStep.timeStepPCR
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.data2NetCDF(str(self.outNCDir)+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                     "dailyTot.nc",\
                                     var,\
                      pcr.pcr2numpy(self.__getattribute__(var),vos.MV),\
                                     timeStamp,timestepPCR-1)
        
            # writing monthly output to netcdf files
            # -cummulative
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # introduce variables at the beginning of simulation:
                    if currTimeStep.timeStepPCR == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                    # reset variables at the beginning of the month
                    if currTimeStep.day == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                    # accumulating
                    vars(self)[var+'Tot'] += vars(self)[var]
                    # reporting at the end of the month:
                    if currTimeStep.endMonth == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                         "monthTot.nc",\
                                      var,\
                          pcr.pcr2numpy(self.__getattribute__(var+'Tot'),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)
            # -average
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # only if a accumulator variable has not been defined: 
                    if var not in self.outMonthTotNC: 
                        # introduce accumulator variables at the beginning of simulation:
                        if currTimeStep.timeStepPCR == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                        # reset variables at the beginning of the month
                        if currTimeStep.day == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                        # accumulating
                        vars(self)[var+'Tot'] += vars(self)[var]
                    # calculating average and reporting at the end of the month:
                    if currTimeStep.endMonth == True:
                        vars(self)[var+'Avg'] = vars(self)[var+'Tot'] /\
                                                currTimeStep.day  
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                         "monthAvg.nc",\
                                         var,\
                          pcr.pcr2numpy(self.__getattribute__(var+'Avg'),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)
            # -last day of the month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    # reporting at the end of the month:
                    if currTimeStep.endMonth == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                         "monthEnd.nc",\
                                         var,\
                          pcr.pcr2numpy(self.__getattribute__(var),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)


    def getPotET(self, meteo, currTimeStep):

        # get crop coefficient:
        cropKC = pcr.cover(
                 vos.netcdf2PCRobjClone(self.cropCoefficientNC,'kc', \
                                    currTimeStep.fulldate, useDoy = 'daily_seasonal',\
                                    cloneMapFileName = self.cloneMap), 0.0)
        self.inputCropKC = cropKC                                               # This line is needed for debugging. (Can we remove this?)
        self.cropKC = pcr.max(cropKC, self.minCropKC)                                

        # calculate potential ET (unit: m/day)
        self.totalPotET = pcr.ifthen(self.landmask,\
                                     self.cropKC * meteo.referencePotET)

        # calculate potential bare soil evaporation and transpiration (unit: m/day)
        self.potBareSoilEvap  = pcr.ifthen(self.landmask,\
                                self.minCropKC * meteo.referencePotET)
        self.potTranspiration = pcr.max(0.0, \
                                pcr.ifthen(self.landmask,\
                                self.totalPotET - self.potBareSoilEvap))
    
        if self.debugWaterBalance:
            vos.waterBalanceCheck([self.totalPotET],\
                                  [self.potBareSoilEvap, self.potTranspiration],\
                                  [],\
                                  [],\
                                  'partitioning potential evaporation',\
                                  True,\
                                  currTimeStep.fulldate,threshold=5e-4)

    def interceptionUpdate(self, meteo, currTimeStep):
        
        if self.debugWaterBalance:
            prevStates = [self.interceptStor]
       
        # get interceptCap:
        interceptCap  = pcr.scalar(self.minInterceptCap)
        coverFraction = pcr.scalar(1.0)
        if self.interceptCapNC != None and self.coverFractionNC != None:
            interceptCap = \
                     pcr.cover(
                     vos.netcdf2PCRobjClone(self.interceptCapNC,\
                                    'interceptCapInput',\
                                     currTimeStep.fulldate, useDoy = 'daily_seasonal',\
                                     cloneMapFileName = self.cloneMap), 0.0)
            self.interceptCapInput = interceptCap                        # This line is needed for debugging. 
            coverFraction = \
                     pcr.cover(
                     vos.netcdf2PCRobjClone(self.coverFractionNC,\
                                    'coverFractionInput',\
                                     currTimeStep.fulldate, useDoy = 'daily_seasonal',\
                                     cloneMapFileName = self.cloneMap), 0.0)
            coverFraction = pcr.cover(coverFraction, 0.0)
            interceptCap = coverFraction * interceptCap                  # original Rens line: ICC[TYPE] = CFRAC[TYPE]*INTCMAX[TYPE];                                

        # canopy/cover fraction over the entire cell area (unit: m2)
        self.coverFraction = coverFraction

        # Edwin added the following line to extend the interception definition.
        self.interceptCap = pcr.max(interceptCap, self.minInterceptCap) 
        
        # throughfall = surplus above the interception storage threshold 
        if self.interceptionModuleType == "Modified":
            # extended interception definition/scope (not only canopy)
            self.throughfall   = pcr.max(0.0, self.interceptStor + \
                                              meteo.precipitation - \
                                              self.interceptCap)         # original Rens line: PRP = (1-CFRAC[TYPE])*PRPTOT+max(CFRAC[TYPE]*PRPTOT+INTS_L[TYPE]-ICC[TYPE],0) 
                                                                         # Edwin modified this line to extend the interception scope (not only canopy interception).
        if self.interceptionModuleType == "Original":
            # only canopy interception (not only canopy)
            self.throughfall   = (1.0 - coverFraction) * meteo.precipitation +\
                          pcr.max(0.0,  coverFraction  * meteo.precipitation + self.interceptStor - self.interceptCap)

        # update interception storage after throughfall 
        self.interceptStor = pcr.max(0.0, self.interceptStor + \
                                     meteo.precipitation - \
                                     self.throughfall)                   # original Rens line: INTS_L[TYPE] = max(0,INTS_L[TYPE]+PRPTOT-PRP)
         
        # partitioning throughfall into snowfall and liquid Precipitation:
        estimSnowfall = pcr.ifthenelse(meteo.temperature < self.freezingT, \
                                       meteo.precipitation, 0.0)         
                                                                         # original Rens line: SNOW = if(TA<TT,PRPTOT,0)
                                                                         # But Rens put it in his "meteo" module in order to allow snowfallCorrectionFactor (SFCF).
        # - snowfall (m/day)
        self.snowfall = estimSnowfall * \
              vos.getValDivZero(self.throughfall, meteo.precipitation, \
              vos.smallNumber)                                           # original Rens line: SNOW = SNOW*if(PRPTOT>0,PRP/PRPTOT,0)                                      
        # - liquid precipitation (m/day)
        self.liquidPrecip = pcr.max(0.0,\
                                    self.throughfall - self.snowfall)    # original Rens line: PRP = PRP-SNOW

        # potential interception flux (m/day)
        # - this is depending on 'interceptionModuleType' 
        if self.interceptionModuleType == 'Original': 
            # only canopy interception
            self.potInterceptionFlux = self.potTranspiration                       
        if self.interceptionModuleType == 'Modified': 
            # extended interception definition/scope (not only canopy)
            self.potInterceptionFlux = self.totalPotET        # added by Edwin to extend the interception scope/definition

        
        # evaporation from intercepted water (based on potInterceptionFlux)
        # - based on Van Beek et al. (2011)
        self.interceptEvap = pcr.min(self.interceptStor, \
                                     self.potInterceptionFlux * \
             (vos.getValDivZero(self.interceptStor, self.interceptCap, \
              vos.smallNumber, 0.) ** (2.00/3.00)))                      
                                                                         # EACT_L[TYPE]= min(INTS_L[TYPE],(T_p[TYPE]*if(ICC[TYPE]>0,INTS_L[TYPE]/ICC[TYPE],0)**(2/3)))
        #~ # - Edwin simplify it
        #~ self.interceptEvap = pcr.min(self.interceptStor, self.potInterceptionFlux)                      
                                     
        # update interception storage 
        self.interceptStor = pcr.max(0.0, \
                             self.interceptStor - self.interceptEvap)    # INTS_L[TYPE]= INTS_L[TYPE]-EACT_L[TYPE]
        
        # update potBareSoilEvap and potTranspiration after interceptEvap
        if self.interceptionModuleType == 'Modified':
            # fraction of potential bare soil evaporation and transpiration
            fracPotBareSoilEvap = pcr.max(0.0, pcr.min(1.0, \
                                  vos.getValDivZero(self.potBareSoilEvap, \
                                                    self.potBareSoilEvap + self.potTranspiration, vos.smallNumber)))
            fracPotTranspiration = pcr.scalar(1.0 - self.fracPotBareSoilEvap)
            # substract interceptEvap from potBareSoilEvap and potTranspiration
            self.potBareSoilEvap  = pcr.max(0.0, self.potBareSoilEvap  -\
                                    fracPotBareSoilEvap  * self.interceptEvap)
            self.potTranspiration = pcr.max(0.0, self.potTranspiration -\
                                    fracPotTranspiration * self.interceptEvap)   
                                                                                  # original Rens line: T_p[TYPE] = max(0,T_p[TYPE]-EACT_L[TYPE])
                                                                                  # Edwin modified this line to extend the interception scope/definition (not only canopy interception).
        if self.interceptionModuleType == 'Original': 
            self.potTranspiration = pcr.max(0.0, self.potTranspiration - self.interceptEvap)   
        
        # update actual evaporation (after interceptEvap) 
        self.actualET  = 0. # interceptEvap is the first flux in ET 
        self.actualET += self.interceptEvap

        if self.debugWaterBalance:
            vos.waterBalanceCheck([self.throughfall],\
                                  [self.snowfall, self.liquidPrecip],\
                                  [],\
                                  [],\
                                  'rain-snow-partitioning',\
                                  True,\
                                  currTimeStep.fulldate, threshold=1e-5)
            vos.waterBalanceCheck([meteo.precipitation],
                                  [self.throughfall, self.interceptEvap],
                                  prevStates,\
                                  [self.interceptStor],\
                                  'interceptStor',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-4)

    def interceptionUpdateOriginalVersion(self,meteo,currTimeStep):
        
        # TODO: Rewrite this method as defined by Rens. 
        
        #~ if self.debugWaterBalance:
            #~ prevStates = [self.interceptStor]
       #~ 
        #~ # get interceptCap:
        #~ interceptCap  = pcr.scalar(self.minInterceptCap)
        #~ coverFraction = pcr.scalar(1.0)
        #~ if self.coverFractionNC != None or  
        #~ 
        #~ 
        #~ not self.iniItemsLC['name'].startswith("irr"):                # This line assumes that no interception capacity for paddy and non paddy types
            #~ interceptCap = \
                     #~ pcr.cover(
                     #~ vos.netcdf2PCRobjClone(self.interceptCapNC,\
                                    #~ 'interceptCapInput',\
                                     #~ currTimeStep.fulldate, useDoy = 'daily_seasonal',\
                                     #~ cloneMapFileName = self.cloneMap), 0.0)
            #~ self.interceptCapInput = interceptCap                        # This line is needed for debugging. 
            #~ coverFraction = \
                     #~ pcr.cover(
                     #~ vos.netcdf2PCRobjClone(self.coverFractionNC,\
                                    #~ 'coverFractionInput',\
                                     #~ currTimeStep.fulldate, useDoy = 'daily_seasonal',\
                                     #~ cloneMapFileName = self.cloneMap), 0.0)
            #~ coverFraction = pcr.cover(coverFraction, 0.0)
            #~ interceptCap  = coverFraction * interceptCap                 # original Rens line: ICC[TYPE] = CFRAC[TYPE]*INTCMAX[TYPE];                                
        #~ self.interceptCap = interceptCap
        #~ 
        #~ # Edwin added this line to extend the interception definition (not only canopy interception)
        #~ self.interceptCap = pcr.max(self.interceptCap, self.minInterceptCap)  
        #~ 
        #~ # canopy/cover fraction over the entire cell area (unit: m2)
        #~ self.coverFraction = coverFraction
        #~ 
        #~ # throughfall (m/day)
        #~ self.throughfall   = (1.0 - coverFraction) * meteo.precipitation +\
                      #~ pcr.max(0.0,  coverFraction  * meteo.precipitation + self.interceptStor - self.interceptCap)              
                                                                         #~ # original Rens line: PRP = (1-CFRAC[TYPE])*PRPTOT+max(CFRAC[TYPE]*PRPTOT+INTS_L[TYPE]-ICC[TYPE],0) 
        #~ 
        #~ # make sure that throughfall is never negative
        #~ self.throughfall = pcr.max(0.0, self.throughfall)
        #~ 
        #~ # update interception storage after throughfall 
        #~ self.interceptStor = pcr.max(0.0, self.interceptStor + \
                                    #~ meteo.precipitation - \
                                    #~ self.throughfall)                    # original Rens line: INTS_L[TYPE] = max(0,INTS_L[TYPE]+PRPTOT-PRP)
         #~ 
        #~ # partitioning throughfall into snowfall and liquid Precipitation:
        #~ estimSnowfall = pcr.ifthenelse(meteo.temperature < self.freezingT, \
                                       #~ meteo.precipitation, 0.0)         # original Rens line: SNOW = if(TA<TT,PRPTOT,0)
                                                                         #~ # But Rens put it in his "meteo" module in order to allow snowfallCorrectionFactor (SFCF).
        #~ estimLiqPrec  = pcr.max(0.0, meteo.precipitation - estimSnowfall)
        #~ totalPrec     = estimSnowfall + estimLiqPrec
        #~ # - snowfall
        #~ self.snowfall = pcr.min(self.throughfall, estimSnowfall * pcr.ifthenelse(totalPrec > 0.0, self.throughfall/totalPrec, 0.0))
        #~ # - liquid throughfall passing the canopy
        #~ self.liquidPrecip = pcr.max(0.0,\
                                    #~ self.throughfall - self.snowfall)    # original Rens line: PRP = PRP-SNOW
#~ 
        #~ # potential interception flux (m/day)
        #~ self.potInterceptionFlux = self.potTranspiration                 # Rens only uses potTranspiration
        #~ 
        #~ # evaporation from intercepted water (based on potInterceptionFlux)
        #~ self.interceptEvap = pcr.min(self.interceptStor, \
                                     #~ self.potInterceptionFlux * \
             #~ pcr.ifthenelse(self.interceptCap > 0.0, (self.interceptStor/self.interceptCap), 0.0) ** (2.0/3.0))                      
                                                                         #~ # EACT_L[TYPE] = min(INTS_L[TYPE],(T_p[TYPE]*if(ICC[TYPE]>0,INTS_L[TYPE]/ICC[TYPE],0)**(2/3)))
        #~ 
        #~ # make sure evaporation does not exceed available enerrgy
        #~ self.interceptEvap = pcr.min(self.interceptEvap, self.potInterceptionFlux)
                                     #~ 
        #~ # update interception storage 
        #~ self.interceptStor = pcr.max(0.0, \
                             #~ self.interceptStor - self.interceptEvap)    # INTS_L[TYPE] = INTS_L[TYPE]-EACT_L[TYPE]
        #~ 
        #~ # update potTranspiration 
        #~ self.potTranspiration = pcr.max(0.0, self.potTranspiration - self.interceptEvap)  # original Rens line: T_p[TYPE]= max(0,T_p[TYPE]-EACT_L[TYPE])
#~ 
        #~ # update actual evaporation (after interceptEvap) 
        #~ self.actualET  = 0. # interceptEvap is the first flux in ET 
        #~ self.actualET += self.interceptEvap
#~ 
        #~ if self.debugWaterBalance:
            #~ vos.waterBalanceCheck([self.throughfall],\
                                  #~ [self.snowfall,self.liquidPrecip],\
                                  #~ [],\
                                  #~ [],\
                                  #~ 'rain-snow-partitioning',\
                                  #~ True,\
                                  #~ currTimeStep.fulldate,threshold=1e-5)
            #~ vos.waterBalanceCheck([meteo.precipitation],
                                  #~ [self.throughfall,self.interceptEvap],
                                  #~ prevStates,\
                                  #~ [self.interceptStor],\
                                  #~ 'interceptStor',\
                                  #~ True,\
                                  #~ currTimeStep.fulldate,threshold=1e-4)

        pass

    def snowMeltHBVSimple(self,meteo,currTimeStep):

        if self.debugWaterBalance:
            prevStates        = [self.snowCoverSWE,self.snowFreeWater]
            prevSnowCoverSWE  = self.snowCoverSWE
            prevSnowFreeWater = self.snowFreeWater

        # changes in snow cover: - melt ; + gain in snow or refreezing
        deltaSnowCover = \
            pcr.ifthenelse(meteo.temperature <= self.freezingT, \
            self.refreezingCoeff*self.snowFreeWater, \
           -pcr.min(self.snowCoverSWE, \
                    pcr.max(meteo.temperature - self.freezingT, 0.0) * \
                    self.degreeDayFactor)*1.0*1.0)                      # DSC[TYPE] = if(TA<=TT,CFR*SCF_L[TYPE],
                                                                        #                      -min(SC_L[TYPE],max(TA-TT,0)*CFMAX*Duration*timeslice()))
        #~ deltaSnowCover = \
            #~ pcr.ifthenelse(meteo.temperature > self.freezingT, -pcr.min(self.snowCoverSWE, \
                                                                #~ pcr.max(meteo.temperature - self.freezingT, 0.0) * \
                                                                #~ self.degreeDayFactor)*1.0*1.0, \
                                                                #~ self.refreezingCoeff*self.snowFreeWater)

        # update snowCoverSWE
        self.snowCoverSWE  = pcr.max(0.0, self.snowfall + deltaSnowCover + self.snowCoverSWE)                              
                                                                        # SC_L[TYPE] = max(0.0, SC_L[TYPE]+DSC[TYPE]+SNOW)

        # for reporting snow melt in m/day
        self.snowMelt = pcr.ifthenelse(deltaSnowCover < 0.0, deltaSnowCover * pcr.scalar(-1.0), pcr.scalar(0.0))

        # update snowFreeWater = liquid water stored above snowCoverSWE
        self.snowFreeWater = self.snowFreeWater - deltaSnowCover + \
                             self.liquidPrecip                          # SCF_L[TYPE] = SCF_L[TYPE]-DSC[TYPE]+PRP;
                                     
        # netLqWaterToSoil = net liquid transferred to soil
        self.netLqWaterToSoil = pcr.max(0., self.snowFreeWater - \
                 self.snowWaterHoldingCap * self.snowCoverSWE)          # Pn = max(0,SCF_L[TYPE]-CWH*SC_L[TYPE])
        
        # update snowFreeWater (after netLqWaterToSoil) 
        self.snowFreeWater    = pcr.max(0., self.snowFreeWater - \
                                            self.netLqWaterToSoil)      # SCF_L[TYPE] = max(0,SCF_L[TYPE]-Pn)

        # evaporation from snowFreeWater (based on potBareSoilEvap)
        self.actSnowFreeWaterEvap = pcr.min(self.snowFreeWater, \
                                            self.potBareSoilEvap)       # ES_a[TYPE] = min(SCF_L[TYPE],ES_p[TYPE])
                                       
        # update snowFreeWater and potBareSoilEvap
        self.snowFreeWater = pcr.max(0.0, \
                             self.snowFreeWater - self.actSnowFreeWaterEvap)  
                                                                        # SCF_L[TYPE]= SCF_L[TYPE]-ES_a[TYPE]
        self.potBareSoilEvap = pcr.max(0, \
                           self.potBareSoilEvap - self.actSnowFreeWaterEvap) 
                                                                        # ES_p[TYPE]= max(0,ES_p[TYPE]-ES_a[TYPE])

        # update actual evaporation (after evaporation from snowFreeWater) 
        self.actualET += self.actSnowFreeWaterEvap                      # EACT_L[TYPE]= EACT_L[TYPE]+ES_a[TYPE];

        if self.debugWaterBalance:
            vos.waterBalanceCheck([self.snowfall, self.liquidPrecip],
                                  [self.netLqWaterToSoil,\
                                   self.actSnowFreeWaterEvap],
                                   prevStates,\
                                  [self.snowCoverSWE, self.snowFreeWater],\
                                  'snow module',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)
            vos.waterBalanceCheck([self.snowfall, deltaSnowCover],\
                                  [pcr.scalar(0.0)],\
                                  [prevSnowCoverSWE],\
                                  [self.snowCoverSWE],\
                                  'snowCoverSWE',\
                                   True,\
                                   currTimeStep.fulldate,threshold=5e-4)
            vos.waterBalanceCheck([self.liquidPrecip],
                                  [deltaSnowCover, self.actSnowFreeWaterEvap, self.netLqWaterToSoil],
                                  [prevSnowFreeWater],\
                                  [self.snowFreeWater],\
                                  'snowFreeWater',\
                                   True,\
                                   currTimeStep.fulldate,threshold=5e-4)

    def getSoilStates(self):

        if self.numberOfLayers == 2: 

            # initial total soilWaterStorage
            self.soilWaterStorage = pcr.max(0.,\
                                        self.storUpp + \
                                        self.storLow )

            # effective degree of saturation (-)
            self.effSatUpp = pcr.max(0., self.storUpp/ self.parameters.storCapUpp)  # THEFF1= max(0,S1_L[TYPE]/SC1[TYPE]);
            self.effSatLow = pcr.max(0., self.storLow/ self.parameters.storCapLow)  # THEFF2= max(0,S2_L[TYPE]/SC2[TYPE]);
            self.effSatUpp = pcr.min(1., self.effSatUpp)
            self.effSatLow = pcr.min(1., self.effSatLow)
            self.effSatUpp = pcr.cover(self.effSatUpp, 1.0)
            self.effSatLow = pcr.cover(self.effSatLow, 1.0)
            
            # matricSuction (m)
            self.matricSuctionUpp = self.parameters.airEntryValueUpp*\
             (pcr.max(0.01,self.effSatUpp)**-self.parameters.poreSizeBetaUpp)
            self.matricSuctionLow = self.parameters.airEntryValueLow*\
             (pcr.max(0.01,self.effSatLow)**-self.parameters.poreSizeBetaLow)       # PSI1= PSI_A1[TYPE]*max(0.01,THEFF1)**-BCH1[TYPE]; 
                                                                                    # PSI2= PSI_A2[TYPE]*max(0.01,THEFF2)**-BCH2[TYPE]; 

            # kUnsat (m.day-1): unsaturated hydraulic conductivity
            #~ KUnSatUpp = pcr.max(0.,pcr.max(self.parameters.THEFF1_50,\
                                           #~ effSatUpp)**\
                         #~ self.parameters.campbellBeta1*self.parameters.KSat1)         # DW's code
            #~ KUnSatLow = pcr.max(0.,pcr.max(parameters.THEFF2_50,\
                                           #~ effSatLow)**\
                         #~ self.parameters.campbellBeta2*self.parameters.KSat2)         # DW's code
            # 
            self.kUnsatUpp = pcr.max(0.,(self.effSatUpp**\
                        self.parameters.campbellBetaUpp)*self.parameters.kSatUpp)        # original Rens's code: KTHEFF1= max(0,THEFF1**BCB1[TYPE]*KS1[TYPE])
            self.kUnsatLow = pcr.max(0.,(self.effSatLow**\
                        self.parameters.campbellBetaLow)*self.parameters.kSatLow)        # original Rens's code: KTHEFF2= max(0,THEFF2**BCB2[TYPE]*KS2[TYPE])
            self.kUnsatUpp = pcr.min(self.kUnsatUpp,self.parameters.kSatUpp)
            self.kUnsatLow = pcr.min(self.kUnsatLow,self.parameters.kSatLow)
            
            # kThVert (m.day-1) = unsaturated conductivity capped at field capacity
            # - exchange between layers capped at field capacity 
            self.kThVertUppLow  = pcr.min(\
                          pcr.sqrt(self.kUnsatUpp*self.kUnsatLow),\
                                  (self.kUnsatUpp*self.kUnsatLow* \
                                  self.parameters.kUnsatAtFieldCapUpp*\
                                  self.parameters.kUnsatAtFieldCapLow)**0.25)
                                                                                                 # KTHVERT = min(sqrt(KTHEFF1*KTHEFF2),(KTHEFF1*KTHEFF2*KTHEFF1_FC*KTHEFF2_FC)**0.25)
        
            # gradient for capillary rise (index indicating target store to its underlying store)
            self.gradientUppLow = pcr.max(0.0,\
                         (self.matricSuctionUpp-self.matricSuctionLow)*2./\
                         (self.parameters.thickUpp+self.parameters.thickLow)-pcr.scalar(1.0))
            self.gradientUppLow = pcr.cover(self.gradientUppLow, 0.0)                  
                                                                                                 # GRAD = max(0,2*(PSI1-PSI2)/(Z1[TYPE]+Z2[TYPE])-1);
             
            # readily available water in the root zone (upper soil layers)
            #~ readAvlWater     = \
                               #~ (pcr.max(0.,\
                                #~ effSatUpp        -self.parameters.THEFF1_WP))*\
                               #~ (parameters.satVolWC1 -parameters.resVolWC1) *\
                        #~ pcr.min(parameters.storCapUpp,self.maxRootDepth)  + \
                               #~ (pcr.max(0.,\
                                #~ effSatLow        -self.parameters.THEFF2_WP))*\
                               #~ (parameters.satVolWC2 -parameters.resVolWC2) *\
                        #~ pcr.min(parameters.storCapLow,\
                        #~ pcr.max(self.maxRootDepth-self.parameters.storCapUpp,0.)) # DW's code (using storCapUpp and storCapLow). Edwin does not agree with this.  
            #
            self.readAvlWater     = \
                               (pcr.max(0.,\
                                               self.effSatUpp - self.parameters.effSatAtWiltPointUpp))*\
                               (self.parameters.satVolMoistContUpp -   self.parameters.resVolMoistContUpp )*\
                        pcr.min(self.parameters.thickUpp,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                                               self.effSatLow - self.parameters.effSatAtWiltPointLow))*\
                               (self.parameters.satVolMoistContLow - self.parameters.resVolMoistContLow )*\
                        pcr.min(self.parameters.thickLow,\
                        pcr.max(self.maxRootDepth-self.parameters.thickUpp,0.))      # Edwin modified this line. Edwin uses soil thickness thickUpp & thickLow (instead of storCapUpp & storCapLow). 
                                                                                     # And Rens support this. 

        if self.numberOfLayers == 3: 

            # initial total soilWaterStorage
            self.soilWaterStorage = pcr.max(0.,\
                                        self.storUpp000005 + \
                                        self.storUpp005030 + \
                                        self.storLow030150 )

            # effective degree of saturation (-)
            self.effSatUpp000005 = pcr.max(0., self.storUpp000005/ self.parameters.storCapUpp000005)
            self.effSatUpp005030 = pcr.max(0., self.storUpp005030/ self.parameters.storCapUpp005030)
            self.effSatLow030150 = pcr.max(0., self.storLow030150/ self.parameters.storCapLow030150)
            self.effSatUpp000005 = pcr.min(1., self.effSatUpp000005)
            self.effSatUpp005030 = pcr.min(1., self.effSatUpp005030)
            self.effSatLow030150 = pcr.min(1., self.effSatLow030150)
        
            # matricSuction (m)
            self.matricSuctionUpp000005 = self.parameters.airEntryValueUpp000005*(pcr.max(0.01,self.effSatUpp000005)**-self.parameters.poreSizeBetaUpp000005)
            self.matricSuctionUpp005030 = self.parameters.airEntryValueUpp005030*(pcr.max(0.01,self.effSatUpp005030)**-self.parameters.poreSizeBetaUpp005030)
            self.matricSuctionLow030150 = self.parameters.airEntryValueLow030150*(pcr.max(0.01,self.effSatLow030150)**-self.parameters.poreSizeBetaLow030150)

            # kUnsat (m.day-1): unsaturated hydraulic conductivity
            self.kUnsatUpp000005 = pcr.max(0.,(self.effSatUpp000005**self.parameters.campbellBetaUpp000005)*self.parameters.kSatUpp000005)
            self.kUnsatUpp005030 = pcr.max(0.,(self.effSatUpp005030**self.parameters.campbellBetaUpp005030)*self.parameters.kSatUpp005030)
            self.kUnsatLow030150 = pcr.max(0.,(self.effSatLow030150**self.parameters.campbellBetaLow030150)*self.parameters.kSatLow030150)

            self.kUnsatUpp000005 = pcr.min(self.kUnsatUpp000005,self.parameters.kSatUpp000005)
            self.kUnsatUpp005030 = pcr.min(self.kUnsatUpp005030,self.parameters.kSatUpp005030)
            self.kUnsatLow030150 = pcr.min(self.kUnsatLow030150,self.parameters.kSatLow030150)
            
            # kThVert (m.day-1) = unsaturated conductivity capped at field capacity
            # - exchange between layers capped at field capacity 
            #   between Upp000005Upp005030
            self.kThVertUpp000005Upp005030  = pcr.min(\
                          pcr.sqrt(self.kUnsatUpp000005*self.kUnsatUpp005030),\
                                  (self.kUnsatUpp000005*self.kUnsatUpp005030* \
                   self.parameters.kUnsatAtFieldCapUpp000005*\
                   self.parameters.kUnsatAtFieldCapUpp005030)**0.25)
            #   between Upp005030Low030150
            self.kThVertUpp005030Low030150  = pcr.min(\
                          pcr.sqrt(self.kUnsatUpp005030*self.kUnsatLow030150),\
                                  (self.kUnsatUpp005030*self.kUnsatLow030150* \
                   self.parameters.kUnsatAtFieldCapUpp005030*\
                   self.parameters.kUnsatAtFieldCapLow030150)**0.25)
        
            # gradient for capillary rise (index indicating target store to its underlying store)
            #    between Upp000005Upp005030
            self.gradientUpp000005Upp005030 = pcr.max(0.,2.*\
                         (self.matricSuctionUpp000005-self.matricSuctionUpp005030)/\
                         (self.parameters.thickUpp000005+  self.parameters.thickUpp005030)-1.)
            #    between Upp005030Low030150
            self.gradientUpp005030Low030150 = pcr.max(0.,2.*\
                         (self.matricSuctionUpp005030-self.matricSuctionLow030150)/\
                         (self.parameters.thickUpp005030+  self.parameters.thickLow030150)-1.)
             
            # readily available water in the root zone (upper soil layers)
            self.readAvlWater = \
                               (pcr.max(0.,\
                                               self.effSatUpp000005 - self.parameters.effSatAtWiltPointUpp000005))*\
                               (self.parameters.satVolMoistContUpp000005 -   self.parameters.resVolMoistContUpp000005 )*\
                        pcr.min(self.parameters.thickUpp000005,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                                               self.effSatUpp005030 - self.parameters.effSatAtWiltPointUpp005030))*\
                               (self.parameters.satVolMoistContUpp005030 -   self.parameters.resVolMoistContUpp005030 )*\
                        pcr.min(self.parameters.thickUpp005030,\
                        pcr.max(self.maxRootDepth-self.parameters.thickUpp000005))  + \
                               (pcr.max(0.,\
                                               self.effSatLow030150 - self.parameters.effSatAtWiltPointLow030150))*\
                               (self.parameters.satVolMoistContLow030150 -   self.parameters.resVolMoistContLow030150 )*\
                        pcr.min(self.parameters.thickLow030150,\
                        pcr.max(self.maxRootDepth-self.parameters.thickUpp005030,0.))
                        
        # RvB: initialize satAreaFrac        
        self.satAreaFrac= None

    def calculateWaterDemand(self, nonIrrGrossDemandDict, \
                                   swAbstractionFractionDict, \
                                   groundwater, \
                                   routing, \
                                   allocSegments, \
                                   currTimeStep, \
                                   desalinationWaterUse,\
                                   groundwater_pumping_region_ids,\
                                   regionalAnnualGroundwaterAbstractionLimit):

        # irrigation water demand (unit: m/day) for paddy and non-paddy
        self.irrGrossDemand = pcr.scalar(0.)
        if (self.name == 'irrPaddy' or self.name == 'irr_paddy') and self.includeIrrigation:
            self.irrGrossDemand = \
                  pcr.ifthenelse(self.cropKC > 0.75, \
                     pcr.max(0.0,self.minTopWaterLayer - \
                                (self.topWaterLayer )), 0.)                # a function of cropKC (evaporation and transpiration),
                                                                           #               topWaterLayer (water available in the irrigation field)
            
        if (self.name == 'irrNonPaddy' or self.name == 'irr_non_paddy' or self.name ==  "irr_non_paddy_crops") and self.includeIrrigation:

            #~ adjDeplFactor = \
                     #~ pcr.max(0.1,\
                     #~ pcr.min(0.8,(self.cropDeplFactor + \
                                  #~ 40.*(0.005-self.totalPotET))))        # from Wada et al. (2014)
            adjDeplFactor = \
                     pcr.max(0.1,\
                     pcr.min(0.8,(self.cropDeplFactor + \
                                  0.04*(5.-self.totalPotET*1000.))))       # original formula based on Allen et al. (1998)
                                                                           # see: http://www.fao.org/docrep/x0490e/x0490e0e.htm#
            #
            #~ # alternative 1: irrigation demand (to fill the entire totAvlWater, maintaining the field capacity) - NOT USED
            #~ self.irrGrossDemand = \
                 #~ pcr.ifthenelse( self.cropKC > 0.20, \
                 #~ pcr.ifthenelse( self.readAvlWater < \
                                  #~ adjDeplFactor*self.totAvlWater, \
                #~ pcr.max(0.0,  self.totAvlWater-self.readAvlWater),0.),0.)  # a function of cropKC and totalPotET (evaporation and transpiration),
                                                                           #~ #               readAvlWater (available water in the root zone)
            
            # alternative 2: irrigation demand (to fill the entire totAvlWater, maintaining the field capacity, 
            #                                   but with the correction of totAvlWater based on the rooting depth)
            # - as the proxy of rooting depth, we use crop coefficient 
            self.irrigation_factor = pcr.ifthenelse(self.cropKC > 0.0,\
                                       pcr.min(1.0, self.cropKC / 1.0), 0.0)
            self.irrGrossDemand = \
                 pcr.ifthenelse( self.cropKC > 0.20, \
                 pcr.ifthenelse( self.readAvlWater < \
                                 adjDeplFactor*self.irrigation_factor*self.totAvlWater, \
                 pcr.max(0.0, self.totAvlWater*self.irrigation_factor-self.readAvlWater),0.),0.)

            # irrigation demand is implemented only if there is deficit in transpiration and/or evaporation
            deficit_factor = 1.00
            evaporationDeficit   = pcr.max(0.0, (self.potBareSoilEvap  + self.potTranspiration)*deficit_factor -\
                                   self.estimateTranspirationAndBareSoilEvap(returnTotalEstimation = True))
            transpirationDeficit = pcr.max(0.0, 
                                   self.potTranspiration*deficit_factor -\
                                   self.estimateTranspirationAndBareSoilEvap(returnTotalEstimation = True, returnTotalTranspirationOnly = True))
            deficit = pcr.max(evaporationDeficit, transpirationDeficit)
            #
            # treshold to initiate irrigation
            deficit_treshold = 0.20 * self.totalPotET
            need_irrigation = pcr.ifthenelse(deficit > deficit_treshold, pcr.boolean(1),\
                              pcr.ifthenelse(self.soilWaterStorage == 0.000, pcr.boolean(1), pcr.boolean(0)))
            need_irrigation = pcr.cover(need_irrigation, pcr.boolean(0.0))
            #
            self.irrGrossDemand = pcr.ifthenelse(need_irrigation, self.irrGrossDemand, 0.0)

            # demand is limited by potential evaporation for the next coming days
            # - objective: to avoid too high and unrealistic demand 
            max_irrigation_interval = 15.0
            min_irrigation_interval =  7.0
            irrigation_interval = pcr.min(max_irrigation_interval, \
                                  pcr.max(min_irrigation_interval, \
                                  pcr.ifthenelse(self.totalPotET > 0.0, \
                                  pcr.roundup((self.irrGrossDemand + pcr.max(self.readAvlWater, self.soilWaterStorage))/ self.totalPotET), 1.0)))
            # - irrigation demand - limited by potential evaporation for the next coming days
            self.irrGrossDemand = pcr.min(pcr.max(0.0,\
                                          self.totalPotET * irrigation_interval - pcr.max(self.readAvlWater, self.soilWaterStorage)),\
                                          self.irrGrossDemand)

            # assume that smart farmers do not irrigate higher than infiltration capacities
            if self.numberOfLayers == 2: self.irrGrossDemand = pcr.min(self.irrGrossDemand, self.parameters.kSatUpp)
            if self.numberOfLayers == 3: self.irrGrossDemand = pcr.min(self.irrGrossDemand, self.parameters.kSatUpp000005)

        # irrigation efficiency, minimum demand for start irrigating and maximum value to cap excessive demand 
        if self.includeIrrigation:

            # irrigation efficiency                                                               # TODO: Improve the concept of irrigation efficiency
            self.irrigationEfficiencyUsed  = pcr.min(1.0, pcr.max(0.10, self.irrigationEfficiency))
            # demand, including its inefficiency
            self.irrGrossDemand = pcr.cover(self.irrGrossDemand / pcr.min(1.0, self.irrigationEfficiencyUsed), 0.0)
            
            # the following irrigation demand is not limited to available water
            self.irrGrossDemand = pcr.ifthen(self.landmask, self.irrGrossDemand)
            
            # reduce irrGrossDemand by netLqWaterToSoil
            self.irrGrossDemand = pcr.max(0.0, self.irrGrossDemand - self.netLqWaterToSoil)
            
            # minimum demand for start irrigating
            minimum_demand = 0.005   # unit: m/day                                                   # TODO: set the minimum demand in the ini/configuration file.
            if self.name == 'irrPaddy' or\
               self.name == 'irr_paddy': minimum_demand = pcr.min(self.minTopWaterLayer, 0.025)      # TODO: set the minimum demand in the ini/configuration file.
            self.irrGrossDemand = pcr.ifthenelse(self.irrGrossDemand > minimum_demand, \
                                                 self.irrGrossDemand , 0.0)                          
                                                                                                     
            maximum_demand = 0.025  # unit: m/day                                                    # TODO: set the maximum demand in the ini/configuration file.  
            if self.name == 'irrPaddy' or\
               self.name == 'irr_paddy': maximum_demand = pcr.min(self.minTopWaterLayer, 0.025)      # TODO: set the minimum demand in the ini/configuration file.
            self.irrGrossDemand = pcr.min(maximum_demand, self.irrGrossDemand)                       
                                                                                                     
            # ignore small irrigation demand (less than 1 mm)                                        
            self.irrGrossDemand = pcr.rounddown( self.irrGrossDemand *1000.)/1000.                   
                                                                                                     
            # irrigation demand is only calculated for areas with fracVegCover > 0                   # DO WE NEED THIS ? 
            self.irrGrossDemand = pcr.ifthenelse(self.fracVegCover >  0.0, self.irrGrossDemand, 0.0)

        # total irrigation gross demand (m) per cover types (not limited by available water)
        self.totalPotentialMaximumIrrGrossDemandPaddy    = 0.0
        self.totalPotentialMaximumIrrGrossDemandNonPaddy = 0.0
        if self.name == 'irrPaddy' or self.name == 'irr_paddy': self.totalPotentialMaximumIrrGrossDemandPaddy = self.irrGrossDemand
        if self.name == 'irrNonPaddy' or self.name == 'irr_non_paddy' or self.name == 'irr_non_paddy_crops': self.totalPotentialMaximumIrrGrossDemandNonPaddy = self.irrGrossDemand

        # non irrigation demand is only calculated for areas with fracVegCover > 0                   # DO WE NEED THIS ?
        nonIrrGrossDemandDict['potential_demand']['domestic']  = pcr.ifthenelse(self.fracVegCover > 0.0, nonIrrGrossDemandDict['potential_demand']['domestic'] , 0.0) 
        nonIrrGrossDemandDict['potential_demand']['industry']  = pcr.ifthenelse(self.fracVegCover > 0.0, nonIrrGrossDemandDict['potential_demand']['industry'] , 0.0)
        nonIrrGrossDemandDict['potential_demand']['livestock'] = pcr.ifthenelse(self.fracVegCover > 0.0, nonIrrGrossDemandDict['potential_demand']['livestock'], 0.0)
        

        # water demand values (m/day) NOT limited by available water - these values will not be reduced (if reported)
        # - domestic
        self.totalPotentialMaximumDomesticDemand   = nonIrrGrossDemandDict['potential_demand']['domestic']
        # - industry
        self.totalPotentialMaximumIndustryDemand   = nonIrrGrossDemandDict['potential_demand']['industry']
        # - livestock
        self.totalPotentialMaximumLivestockDemand  = nonIrrGrossDemandDict['potential_demand']['livestock']
        # - irrigation (excluding livestock)
        self.totalPotentialMaximumIrrGrossDemand   = self.irrGrossDemand                         
        # - totalGrossDemand (m/day): all sectors (not limited by available water) 
        self.totalPotentialMaximumGrossDemand      = self.irrGrossDemand + self.totalPotentialMaximumDomesticDemand +\
                                                                           self.totalPotentialMaximumIndustryDemand +\
                                                                           self.totalPotentialMaximumLivestockDemand

        # non irrigation water demand, including the livestock (not limited by available water)
        self.totalPotentialMaximumNonIrrGrossDemand = \
                                 nonIrrGrossDemandDict['potential_demand']['domestic'] +\
                                 nonIrrGrossDemandDict['potential_demand']['industry'] +\
                                 nonIrrGrossDemandDict['potential_demand']['livestock']
                                                      
        
        # Abstraction and Allocation of DESALINATED WATER
        # ##################################################################################################################
        # - desalination water to satisfy water demand
        if self.usingAllocSegments: # using zone/segments at which networks are defined (as defined in the landSurface options)
        #  
            logger.debug("Allocation of supply from desalination water.")
        #  
            volDesalinationAbstraction, volDesalinationAllocation = \
              vos.waterAbstractionAndAllocation(
              water_demand_volume = self.totalPotentialMaximumGrossDemand * routing.cellArea,\
              available_water_volume = pcr.max(0.00, desalinationWaterUse * routing.cellArea),\
              allocation_zones = allocSegments,\
              zone_area = self.segmentArea,\
              high_volume_treshold = None,\
              debug_water_balance = True,\
              extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
              landmask = self.landmask,
              ignore_small_values = False,
              prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
        #     
            self.desalinationAbstraction = volDesalinationAbstraction / routing.cellArea
            self.desalinationAllocation  = volDesalinationAllocation  / routing.cellArea
        #     
        else: 
        #     
            logger.debug("Supply from desalination water is only for satisfying local demand (no network).")
            self.desalinationAbstraction = pcr.min(desalinationWaterUse, self.totalPotentialMaximumGrossDemand)
            self.desalinationAllocation  = self.desalinationAbstraction
        #     
        self.desalinationAbstraction = pcr.ifthen(self.landmask, self.desalinationAbstraction)
        self.desalinationAllocation  = pcr.ifthen(self.landmask, self.desalinationAllocation)
        # ##################################################################################################################
        # - end of Abstraction and Allocation of DESALINATED WATER


        # water demand that have been satisfied (unit: m/day) - after desalination
        ################################################################################################################################
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            
            logger.debug("Desalinated water is prioritized to satisfy sectoral water demands with the following order: domestic, indutry, livestock and agriculture/irrigation.")
            
            # - 1st priority: domestic 
            satisfiedDomesticDemand   = pcr.min(self.totalPotentialMaximumDomesticDemand, \
                                                self.desalinationAllocation)
            # - 2nd priority: industry 
            satisfiedIndustryDemand   = pcr.min(self.totalPotentialMaximumIndustryDemand, \
                                                pcr.max(0.0, self.desalinationAllocation - satisfiedDomesticDemand))
            # - 3rd priority: livestock 
            satisfiedLivestockDemand  = pcr.min(self.totalPotentialMaximumLivestockDemand, \
                                                pcr.max(0.0, self.desalinationAllocation - satisfiedDomesticDemand - satisfiedIndustryDemand))
            
        else:

            logger.debug("Desalinated water is distributed proportionally based on sectoral water demand values.")
            
            # - domestic, industry and livestock
            satisfiedDomesticDemand   = self.desalinationAllocation * vos.getValDivZero(self.totalPotentialMaximumDomesticDemand,  self.totalPotentialMaximumGrossDemand)
            satisfiedIndustryDemand   = self.desalinationAllocation * vos.getValDivZero(self.totalPotentialMaximumIndustryDemand,  self.totalPotentialMaximumGrossDemand)
            satisfiedLivestockDemand  = self.desalinationAllocation * vos.getValDivZero(self.totalPotentialMaximumLivestockDemand, self.totalPotentialMaximumGrossDemand)
        
        # - aggriculture/irrigation (excluding livestock)
        satisfiedIrrigationDemand = pcr.min(self.totalPotentialMaximumIrrGrossDemand, \
                                            pcr.max(0.0, self.desalinationAllocation - satisfiedDomesticDemand - satisfiedIndustryDemand - satisfiedLivestockDemand))

        if self.debugWaterBalance:
            vos.waterBalanceCheck([satisfiedDomesticDemand, \
                                   satisfiedIndustryDemand, \
                                   satisfiedLivestockDemand, \
                                   satisfiedIrrigationDemand],\
                                  [self.desalinationAllocation],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'desalinatedWaterAllocationForAllSectors', True,\
                                   currTimeStep.fulldate,threshold=1e-4)

       
        # remaining gross demand (m/day) after desalination
        ################################################################################################################################
        # the remaining water demand per sector
        # - for domestic 
        remainingDomestic   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['domestic']  - satisfiedDomesticDemand)
        # - for industry 
        remainingIndustry   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['industry']  - satisfiedIndustryDemand)
        # - for livestock 
        remainingLivestock  = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['livestock'] - satisfiedLivestockDemand)
        # - for irrigation (excluding livestock)
        remainingIrrigation = pcr.max(0.0, self.irrGrossDemand - satisfiedIrrigationDemand) 
        # - total
        self.totalGrossDemandAfterDesalination = remainingDomestic + remainingIndustry + remainingLivestock + remainingIrrigation
        # - domestic and industry
        remainingIndustryDomestic = remainingDomestic + remainingIndustry
        # - irrigation and livestock
        remainingIrrigationLivestock = remainingLivestock + remainingIrrigation


        # Abstraction and Allocation of SURFACE WATER
        ##############################################################################################################################
        # calculate the estimate of surface water demand (considering by swAbstractionFractionDict)
        #
        # - for domestic and industrial
        swAbstractionFraction_industrial_domestic = pcr.min(swAbstractionFractionDict['max_for_non_irrigation'],\
                                                            swAbstractionFractionDict['estimate'])
        if not isinstance(swAbstractionFractionDict['non_irrigation'], types.NoneType):
            logger.debug('Set the predefined fraction of surface water source for satisfying domestic and industrial demand.')
            swAbstractionFraction_industrial_domestic = swAbstractionFractionDict['non_irrigation']
        #
        #~ pcr.aguila(swAbstractionFraction_industrial_domestic)
        #~ raw_input("Press Enter to continue...")
        #
        # -- domestic and industrial surface water demands - limited by swAbstractionFractionDict
        surface_water_demand_estimate = swAbstractionFraction_industrial_domestic * remainingIndustryDomestic
        #
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            estimatedRemainingDomestic = pcr.min(surface_water_demand_estimate, swAbstractionFraction_industrial_domestic * remainingDomestic)
        else:
            estimatedRemainingDomestic = surface_water_demand_estimate * vos.getValDivZero(remainingDomestic, remainingIndustryDomestic)
        estimatedRemainingIndustry = pcr.max(0.0, surface_water_demand_estimate - estimatedRemainingDomestic)
        #
        # -- for irrigation and livestock - limited by swAbstractionFractionDict
        # --- surface water source as priority if groundwater irrigation fraction is relatively low  
        surface_water_fraction_for_irrigation_and_livestock = \
           pcr.ifthenelse(swAbstractionFractionDict['irrigation'] >= swAbstractionFractionDict['treshold_to_maximize_irrigation_surface_water'],\
           1.0, swAbstractionFractionDict['irrigation'])
        surface_water_irrigation_and_livestock_demand_estimate = surface_water_fraction_for_irrigation_and_livestock * remainingIrrigationLivestock
        #
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            estimatedRemainingLivestock = pcr.min(surface_water_irrigation_and_livestock_demand_estimate, surface_water_fraction_for_irrigation_and_livestock * remainingLivestock)
        else:
            estimatedRemainingLivestock = surface_water_irrigation_and_livestock_demand_estimate * vos.getValDivZero(remainingLivestock, remainingIrrigationLivestock)
        estimatedRemainingIrrigation = pcr.max(0.0, surface_water_irrigation_and_livestock_demand_estimate - estimatedRemainingLivestock)
        #
        # --- update estimate of surface water demand withdrawal (unit: m/day)
        surface_water_demand_estimate += surface_water_irrigation_and_livestock_demand_estimate
        # --- prioritize surface water use in non productive aquifers that have limited groundwater supply
        #~ # ---- alternative 1 (particularly to sastisfy irrigation and livestock water demands, OLD method)
        #~ surface_water_demand_estimate = pcr.ifthenelse(groundwater.productive_aquifer, surface_water_demand_estimate,\
                                                                                       #~ pcr.max(surface_water_demand_estimate, 
                                                                                       #~ pcr.max(0.0, remainingIrrigationLivestock - \
                                                                                       #~ pcr.min(groundwater.avgAllocationShort, groundwater.avgAllocation))))
        # ---- alternative 2
        surface_water_demand_estimate = pcr.ifthenelse(groundwater.productive_aquifer, surface_water_demand_estimate,\
                                                                                       pcr.max(surface_water_demand_estimate, 
                                                                                       pcr.max(0.0, self.totalGrossDemandAfterDesalination - \
                                                                                       pcr.min(groundwater.avgAllocationShort, groundwater.avgAllocation))))
        # --- maximize/optimize surface water use in areas with the overestimation of groundwater supply 
        surface_water_demand_estimate += pcr.max(0.0, pcr.max(groundwater.avgAllocationShort, groundwater.avgAllocation) -\
               (1.0 - surface_water_fraction_for_irrigation_and_livestock) * (self.totalPotentialMaximumIrrGrossDemand + self.totalPotentialMaximumLivestockDemand) -\
               (1.0 - swAbstractionFraction_industrial_domestic) * (self.totalPotentialMaximumGrossDemand - (self.totalPotentialMaximumIrrGrossDemand + self.totalPotentialMaximumLivestockDemand)))
        #
        # -- total demand (unit: m/day) that should be allocated from surface water - limited by the remaining demand
        surface_water_demand_estimate = pcr.min(self.totalGrossDemandAfterDesalination, surface_water_demand_estimate)
        # --- distribute it proportionaly to estimated sectoral water demands 
        estimatedRemainingTotalDemand = estimatedRemainingDomestic  + estimatedRemainingIndustry + \
                                        estimatedRemainingLivestock + estimatedRemainingLivestock
        # --- Note that the proportional distribution MUST ALSO BE DONE for the case self.prioritizeDomesticThenIndutrialThenLivestock (as each sectoral demand) 
        remainingDomestic   = pcr.min(remainingDomestic  , surface_water_demand_estimate * vos.getValDivZero(estimatedRemainingDomestic  , estimatedRemainingTotalDemand))
        remainingIndustry   = pcr.min(remainingIndustry  , surface_water_demand_estimate * vos.getValDivZero(estimatedRemainingIndustry  , estimatedRemainingTotalDemand))
        remainingLivestock  = pcr.min(remainingLivestock , surface_water_demand_estimate * vos.getValDivZero(estimatedRemainingLivestock , estimatedRemainingTotalDemand))
        remainingIrrigation = pcr.min(remainingIrrigation, surface_water_demand_estimate * vos.getValDivZero(estimatedRemainingIrrigation, estimatedRemainingTotalDemand))
        # --- total 
        surface_water_demand = remainingDomestic  + remainingIndustry + \
                               remainingLivestock + remainingLivestock
        # NOTE that after this line, please do not use "surface_water_demand_estimate."
        #
        #~ # if surface water abstraction as the first priority - STILL NOT USED
        #~ if self.surfaceWaterPriority: surface_water_demand = self.totalGrossDemandAfterDesalination
        #
        if self.usingAllocSegments:      # using zone/segment at which supply network is defined
        #  
            logger.debug("Allocation of surface water abstraction.")
        #  
            volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = \
             vos.waterAbstractionAndAllocation(
             water_demand_volume = surface_water_demand * routing.cellArea,\
             available_water_volume = pcr.max(0.00, routing.readAvlChannelStorage),\
             allocation_zones = allocSegments,\
             zone_area = self.segmentArea,\
             high_volume_treshold = None,\
             debug_water_balance = True,\
             extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
             landmask = self.landmask,
             ignore_small_values = False,
             prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)

            self.actSurfaceWaterAbstract   = volActSurfaceWaterAbstract / routing.cellArea
            self.allocSurfaceWaterAbstract = volAllocSurfaceWaterAbstract / routing.cellArea
        #  
        else: 
            logger.debug("Surface water abstraction is only to satisfy local demand (no surface water network).")
            self.actSurfaceWaterAbstract   = pcr.min(routing.readAvlChannelStorage/routing.cellArea,\
                                                     surface_water_demand)                            # unit: m
            self.allocSurfaceWaterAbstract = self.actSurfaceWaterAbstract                             # unit: m   
        #  
        self.actSurfaceWaterAbstract   = pcr.ifthen(self.landmask, self.actSurfaceWaterAbstract)
        self.allocSurfaceWaterAbstract = pcr.ifthen(self.landmask, self.allocSurfaceWaterAbstract)
        ################################################################################################################################
        # - end of Abstraction and Allocation of SURFACE WATER

        
        # water demand that have been satisfied (unit: m/day) - after desalination and surface water supply
        ################################################################################################################################
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            
            logger.debug("Surface water is prioritized to satisfy sectoral water demands with the following order: domestic, indutry, livestock and agriculture/irrigation.")

            # - 1st priority: domestic 
            satisfiedDomesticDemandFromSurfaceWater   = pcr.min(remainingDomestic, \
                                                                self.allocSurfaceWaterAbstract)
            # - 2nd priority: industry 
            satisfiedIndustryDemandFromSurfaceWater   = pcr.min(remainingIndustry, \
                                                                pcr.max(0.0, self.allocSurfaceWaterAbstract - satisfiedDomesticDemandFromSurfaceWater))
            # - 3rd priority: livestock 
            satisfiedLivestockDemandFromSurfaceWater  = pcr.min(remainingLivestock, \
                                                                pcr.max(0.0, self.allocSurfaceWaterAbstract - satisfiedDomesticDemandFromSurfaceWater -\
                                                                                                              satisfiedIndustryDemandFromSurfaceWater))

        else:

            logger.debug("Surface water is distributed proportionally based on sectoral water demand values.")

            # - for domestic                                                                 
            satisfiedDomesticDemandFromSurfaceWater  = self.allocSurfaceWaterAbstract * vos.getValDivZero(remainingDomestic, \
                                                                                                          surface_water_demand)
            # - for industry
            satisfiedIndustryDemandFromSurfaceWater  = self.allocSurfaceWaterAbstract * vos.getValDivZero(remainingIndustry, \
                                                                                                          surface_water_demand)             
            # - for livestock
            satisfiedLivestockDemandFromSurfaceWater = self.allocSurfaceWaterAbstract * vos.getValDivZero(remainingLivestock, \
                                                                                                          surface_water_demand)             

        # - 4th priority: aggriculture/irrigation (excluding livestock)
        satisfiedIrrigationDemandFromSurfaceWater = pcr.min(remainingIrrigation, \
                                                            pcr.max(0.0, self.allocSurfaceWaterAbstract - satisfiedDomesticDemandFromSurfaceWater -\
                                                                                                          satisfiedIndustryDemandFromSurfaceWater -\
                                                                                                          satisfiedLivestockDemandFromSurfaceWater))

        # update satistfied demand after surface water allocaction 
        satisfiedDomesticDemand   += satisfiedDomesticDemandFromSurfaceWater
        satisfiedIndustryDemand   += satisfiedIndustryDemandFromSurfaceWater
        satisfiedLivestockDemand  += satisfiedLivestockDemandFromSurfaceWater
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromSurfaceWater

        if self.debugWaterBalance:
            vos.waterBalanceCheck([satisfiedDomesticDemand, \
                                   satisfiedIndustryDemand, \
                                   satisfiedLivestockDemand, \
                                   satisfiedIrrigationDemand],\
                                  [self.desalinationAllocation, self.allocSurfaceWaterAbstract],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'desalinatedWaterAllocationForAllSectors and surfaceWaterAllocationForAllSectors', True,\
                                   currTimeStep.fulldate,threshold=1e-4)


        ######################################################################################################################
        # water demand (unit: m) that must be satisfied by groundwater abstraction (not limited to available water)
        self.potGroundwaterAbstract = pcr.max(0.0, self.totalGrossDemandAfterDesalination - self.allocSurfaceWaterAbstract)
        ######################################################################################################################
        # water demand per sector 
        # - for domestic 
        remainingDomestic   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['domestic']  - satisfiedDomesticDemand)
        # - for industry 
        remainingIndustry   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['industry']  - satisfiedIndustryDemand)
        # - for livestock 
        remainingLivestock  = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['livestock'] - satisfiedLivestockDemand)
        # - for irrigation (excluding livestock)
        remainingIrrigation = pcr.max(0.0, self.irrGrossDemand - satisfiedIrrigationDemand) 
        # - total for livestock and irrigation
        remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
        # - total for industrial and domestic (excluding livestock)
        remainingIndustryDomestic    = remainingIndustry + remainingDomestic                                                     
        


        # Abstraction and Allocation of GROUNDWATER (fossil and non fossil)
        #########################################################################################################################
        # estimating groundwater water demand:
        # - demand for industrial and domestic sectors 
        #   (all remaining demand for these sectors should be satisfied)
        groundwater_demand_estimate = remainingIndustryDomestic
        # - demand for irrigation and livestock sectors
        #   (only part of them will be satisfied, as they may be too high due to the uncertainty in the irrigation scheme)
        irrigationLivestockGroundwaterDemand = pcr.min(remainingIrrigationLivestock, \
                                               pcr.max(0.0, \
                                               (1.0 - swAbstractionFractionDict['irrigation']) * (self.totalPotentialMaximumGrossDemand - (self.totalPotentialMaximumIrrGrossDemand + self.totalPotentialMaximumLivestockDemand)) ))
        #
        #~ pcr.aguila(swAbstractionFractionDict['irrigation'])
        #~ raw_input("Press Enter to continue...")
        #
        # - estimate of groundwater demand
        groundwater_demand_estimate += irrigationLivestockGroundwaterDemand
        #
        # - for the following condition, there should be no reduction for the remaining demands of domestic, industry and livestock 
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            groundwater_demand_estimate = pcr.max(remainingDomestic + remainingIndustry + remainingLivestock, groundwater_demand_estimate)


        #######################################################################################################
        # water demand that must be satisfied by groundwater abstraction (still not limited to available water)
        self.potGroundwaterAbstract = pcr.min(self.potGroundwaterAbstract, groundwater_demand_estimate)
        #######################################################################################################
        
        # constraining groundwater abstraction with the regional annual pumping capacity
        if groundwater.limitRegionalAnnualGroundwaterAbstraction:

            logger.debug('Total groundwater abstraction is limited by regional annual pumping capacity.')

            # estimate of total groundwater abstraction (m3) from the last 365 days:
            tolerating_days = 0.
            annualGroundwaterAbstraction = groundwater.avgAbstraction * routing.cellArea *\
                                           pcr.min(pcr.max(0.0, 365.0 - tolerating_days), routing.timestepsToAvgDischarge)
            # total groundwater abstraction (m3) from the last 365 days at the regional scale
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(pcr.cover(annualGroundwaterAbstraction, 0.0), groundwater_pumping_region_ids)

            #~ # reduction factor to reduce groundwater abstraction/demand
            #~ reductionFactorForPotGroundwaterAbstract = pcr.cover(\
                                                       #~ pcr.ifthenelse(regionalAnnualGroundwaterAbstractionLimit > 0.0,
                                                       #~ pcr.max(0.000, regionalAnnualGroundwaterAbstractionLimit -\
                                                                      #~ regionalAnnualGroundwaterAbstraction) /
                                                                      #~ regionalAnnualGroundwaterAbstractionLimit , 0.0), 0.0)

            #~ # reduced potential groundwater abstraction (after pumping capacity)
            #~ self.potGroundwaterAbstract = pcr.min(1.00, reductionFactorForPotGroundwaterAbstract) * self.potGroundwaterAbstract

            #~ # alternative: reduced potential groundwater abstraction (after pumping capacity) and considering the average recharge (baseflow)
            #~ potGroundwaterAbstract = pcr.min(1.00, reductionFactorForPotGroundwaterAbstract) * self.potGroundwaterAbstract
            #~ self.potGroundwaterAbstract = pcr.min(self.potGroundwaterAbstract, 
                                                       #~ potGroundwaterAbstract + pcr.max(0.0, routing.avgBaseflow / routing.cellArea))



            ########################################################################################################################################################################
            ################## NEW METHOD ##########################################################################################################################################
            # the remaining pumping capacity (unit: m3) at the regional scale
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.max(0.0, regionalAnnualGroundwaterAbstractionLimit - \
                                                                              regionalAnnualGroundwaterAbstraction)
            # considering safety factor (residence time in day-1)                                                                  
            remainingRegionalAnnualGroundwaterAbstractionLimit *= 0.33
            
            # the remaining pumping capacity (unit: m3) limited by self.potGroundwaterAbstract (at the regional scale)
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.min(remainingRegionalAnnualGroundwaterAbstractionLimit,\
                                                                         pcr.areatotal(self.potGroundwaterAbstract * routing.cellArea, groundwater_pumping_region_ids))
            
            # the remaining pumping capacity (unit: m3) at the pixel scale - downscaled using self.potGroundwaterAbstract
            remainingPixelAnnualGroundwaterAbstractionLimit = remainingRegionalAnnualGroundwaterAbstractionLimit * \
                vos.getValDivZero(self.potGroundwaterAbstract * routing.cellArea, pcr.areatotal(self.potGroundwaterAbstract * routing.cellArea, groundwater_pumping_region_ids))
                
            # reduced (after pumping capacity) potential groundwater abstraction/demand (unit: m) and considering the average recharge (baseflow) 
            self.potGroundwaterAbstract = pcr.min(self.potGroundwaterAbstract, \
                                      remainingPixelAnnualGroundwaterAbstractionLimit/routing.cellArea + pcr.max(0.0, routing.avgBaseflow / routing.cellArea))
            ################## end of NEW METHOD ###################################################################################################################################
            ########################################################################################################################################################################



            # always try to fulfil industrial, domestic, and livestock demands:
            if self.doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity:
                logger.debug('Groundwater pumping capacity should not limit (non-fossil) groundwater abstraction to meet domestic. industrial and livestock water demands.')
                self.potGroundwaterAbstract = pcr.max(remainingIndustryDomestic + remainingLivestock, self.potGroundwaterAbstract)
             
        else:

            logger.debug('NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction.')
        

        # Abstraction and Allocation of NON-FOSSIL GROUNDWATER
        # #############################################################################################################################
        # available storGroundwater (non fossil groundwater) that can be accessed (unit: m)
        readAvlStorGroundwater = pcr.cover(pcr.max(0.00, groundwater.storGroundwater), 0.0)
        # - considering maximum daily groundwater abstraction
        readAvlStorGroundwater = pcr.min(readAvlStorGroundwater, groundwater.maximumDailyGroundwaterAbstraction)

        # limit available storGroundwater in non-productive aquifer
        #~ # - alternative 1: ignore groundwater storage in non-productive aquifer 
        #~ readAvlStorGroundwater = pcr.ifthenelse(groundwater.productive_aquifer, readAvlStorGroundwater, 0.0)
        # - alternative 2: for non-productive aquifer, reduce readAvlStorGroundwater to the current recharge/baseflow rate
        readAvlStorGroundwater    = pcr.ifthenelse(groundwater.productive_aquifer, \
                                                   readAvlStorGroundwater, pcr.min(readAvlStorGroundwater, pcr.max(routing.avgBaseflow, 0.0)))
        
        # avoid the condition that the entire groundwater volume abstracted instantaneously
        readAvlStorGroundwater *= 0.75

        if groundwater.usingAllocSegments:

            logger.debug('Allocation of non fossil groundwater abstraction.')

            # TODO: considering aquifer productivity while doing the allocation (e.g. using aquifer transmissivity/conductivity)
            
            # non fossil groundwater abstraction and allocation in volume (unit: m3)
            volActGroundwaterAbstract, volAllocGroundwaterAbstract = \
             vos.waterAbstractionAndAllocation(
             water_demand_volume = self.potGroundwaterAbstract*routing.cellArea,\
             available_water_volume = pcr.max(0.00, readAvlStorGroundwater*routing.cellArea),\
             allocation_zones = groundwater.allocSegments,\
             zone_area = groundwater.segmentArea,\
             high_volume_treshold = None,\
             debug_water_balance = True,\
             extra_info_for_water_balance_reporting = str(currTimeStep.fulldate),  
             landmask = self.landmask,
             ignore_small_values = False,
             prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
            
            # non fossil groundwater abstraction and allocation in meter
            self.nonFossilGroundwaterAbs   = volActGroundwaterAbstract  / routing.cellArea 
            self.allocNonFossilGroundwater = volAllocGroundwaterAbstract/ routing.cellArea 

        else:
            
            logger.debug('Non fossil groundwater abstraction is only for satisfying local demand.')
            self.nonFossilGroundwaterAbs   = pcr.min(readAvlStorGroundwater, self.potGroundwaterAbstract) 
            self.allocNonFossilGroundwater = self.nonFossilGroundwaterAbs
        ################################################################################################################################
        # - end of Abstraction and Allocation of NON FOSSIL GROUNDWATER


        ################################################################################################################################
        # variable to reduce capillary rise in order to ensure there is always enough water to supply non fossil groundwater abstraction 
        self.reducedCapRise = self.nonFossilGroundwaterAbs                            
        # TODO: Check do we need this for runs with MODFLOW ???
        ################################################################################################################################


        
        # water demand that have been satisfied (unit: m/day) - after desalination, surface water and non-fossil groundwater supply 
        ################################################################################################################################
        if self.prioritizeDomesticThenIndutrialThenLivestock:
            
            logger.debug("Groundwater is prioritized to satisfy sectoral water demands with the following order: domestic, indutry, livestock and agriculture/irrigation.")
            
            # - 1st priority: domestic 
            satisfiedDomesticDemandFromNonFossilGroundwater   = pcr.min(self.allocNonFossilGroundwater, \
                                                                        remainingDomestic)
            # - 2nd priority: industry 
            satisfiedIndustryDemandFromNonFossilGroundwater   = pcr.min(pcr.max(0.0, self.allocNonFossilGroundwater - satisfiedDomesticDemandFromNonFossilGroundwater), \
                                                                        remainingIndustry)
            # - 3rd priority: livestock 
            satisfiedLivestockDemandFromNonFossilGroundwater  = pcr.min(pcr.max(0.0, self.allocNonFossilGroundwater - satisfiedDomesticDemandFromNonFossilGroundwater -\
                                                                                                                      satisfiedIndustryDemandFromNonFossilGroundwater), \
                                                                        remainingLivestock)

        else:

            # - for industrial and domestic demand (excluding livestock)
            satisfiedIndustryDomesticDemandFromNonFossilGroundwater = self.allocNonFossilGroundwater * vos.getValDivZero(remainingIndustryDomestic, groundwater_demand_estimate)
            # - for domestic                                                                 
            satisfiedDomesticDemandFromNonFossilGroundwater  = satisfiedIndustryDomesticDemandFromNonFossilGroundwater * vos.getValDivZero(remainingDomestic, remainingIndustryDomestic)
            # - for industry
            satisfiedIndustryDemandFromNonFossilGroundwater  = pcr.max(0.0, satisfiedIndustryDomesticDemandFromNonFossilGroundwater - satisfiedDomesticDemandFromNonFossilGroundwater)             
            #
            # - for irrigation and livestock water demand 
            satisfiedIrrigationLivestockDemandFromNonFossilGroundwater = self.allocNonFossilGroundwater * vos.getValDivZero(irrigationLivestockGroundwaterDemand, groundwater_demand_estimate)
            # - for livestock                                                                      
            satisfiedLivestockDemandFromNonFossilGroundwater = satisfiedIndustryDomesticDemandFromNonFossilGroundwater * vos.getValDivZero(remainingLivestock, remainingIrrigationLivestock)

        # aggriculture/irrigation (excluding livestock)
        satisfiedIrrigationDemandFromNonFossilGroundwater = pcr.min(remainingIrrigation, \
                                                                    pcr.max(0.0, self.allocNonFossilGroundwater - satisfiedDomesticDemandFromNonFossilGroundwater -\
                                                                                                                  satisfiedIndustryDemandFromNonFossilGroundwater -\
                                                                                                                  satisfiedLivestockDemandFromNonFossilGroundwater))

        # update satistfied demand after non fossil groundwater allocation
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromNonFossilGroundwater
        satisfiedLivestockDemand  += satisfiedLivestockDemandFromNonFossilGroundwater
        satisfiedDomesticDemand   += satisfiedDomesticDemandFromNonFossilGroundwater
        satisfiedIndustryDemand   += satisfiedIndustryDemandFromNonFossilGroundwater


        if self.debugWaterBalance:
            vos.waterBalanceCheck([satisfiedDomesticDemand, \
                                   satisfiedIndustryDemand, \
                                   satisfiedLivestockDemand, \
                                   satisfiedIrrigationDemand],\
                                  [self.desalinationAllocation, self.allocSurfaceWaterAbstract, self.allocNonFossilGroundwater],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'desalinatedWaterAllocationForAllSectors and surfaceWaterAllocationForAllSectors and (nonFossil) groundwaterAllocationForAllSectors', True,\
                                   currTimeStep.fulldate,threshold=1e-4)


        ######################################################################################################################
        ######################################################################################################################
        # water demand that still must be satisfied by fossil groundwater abstraction 
        # (unit: m, limited to potGroundwaterAbstract (e.g. pumping capacity), but still not limited to available water)
        self.potFossilGroundwaterAbstract = pcr.max(0.0, self.potGroundwaterAbstract - \
                                                         self.allocNonFossilGroundwater)
        ######################################################################################################################
        ######################################################################################################################


        # For a run using MODFLOW, the concept of fossil groundwater abstraction is abandoned (self.limitAbstraction == True):
        if groundwater.useMODFLOW or self.limitAbstraction:
            logger.debug('Fossil groundwater abstractions are NOT allowed')
            self.fossilGroundwaterAbstr = pcr.scalar(0.0)
            self.fossilGroundwaterAlloc = pcr.scalar(0.0)


        # Abstraction and Allocation of FOSSIL GROUNDWATER
        # #####################################################################################################################################

        if self.limitAbstraction == False:                              # TODO: For runs without any water use, we can exclude this. 
            
            logger.debug('Fossil groundwater abstractions are allowed.')
            
            # the remaining water demand (m/day) for all sectors - NOT limited to self.potFossilGroundwaterAbstract
            #####################################################################################################################
            # - for domestic 
            remainingDomestic   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['domestic']  - satisfiedDomesticDemand)
            # - for industry 
            remainingIndustry   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['industry']  - satisfiedIndustryDemand)
            # - for livestock 
            remainingLivestock  = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['livestock'] - satisfiedLivestockDemand)
            # - for irrigation (excluding livestock)
            remainingIrrigation = pcr.max(0.0, self.irrGrossDemand - satisfiedIrrigationDemand) 
            # - total for livestock and irrigation
            remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
            # - total for industrial and domestic (excluding livestock)
            remainingIndustryDomestic    = remainingIndustry + remainingDomestic
            # - remaining total demand
            remainingTotalDemand = remainingIrrigationLivestock + remainingIndustryDomestic                                                     


        # constraining fossil groundwater abstraction with regional pumping capacity
        if groundwater.limitRegionalAnnualGroundwaterAbstraction and self.limitAbstraction == False:

            logger.debug('Fossil groundwater abstraction is allowed, BUT limited by the regional annual pumping capacity.')

            # estimate of total groundwater abstraction (m3) from the last 365 days:
            # - considering abstraction from non fossil groundwater
            annualGroundwaterAbstraction += self.nonFossilGroundwaterAbs*routing.cellArea
            # at the regional scale
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(pcr.cover(annualGroundwaterAbstraction, 0.0), groundwater_pumping_region_ids)
            
            # fossil groundwater demand/asbtraction reduced by pumping capacity (unit: m/day)
            # - safety factor to avoid the remaining limit abstracted at once (due to overestimation of groundwater demand)
            safety_factor_for_fossil_abstraction = 1.00
            self.potFossilGroundwaterAbstract *= pcr.min(1.00,\
                                                 pcr.cover(\
                                                 pcr.ifthenelse(regionalAnnualGroundwaterAbstractionLimit > 0.0,
                                                 pcr.max(0.000, regionalAnnualGroundwaterAbstractionLimit * safety_factor_for_fossil_abstraction-\
                                                                regionalAnnualGroundwaterAbstraction) /
                                                                regionalAnnualGroundwaterAbstractionLimit , 0.0), 0.0))

            # always try to fulfil industrial, domestic, and livestock demands:
            if self.doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity:
                logger.debug('Groundwater pumping capacity should not limit (fossil) groundwater abstraction to meet domestic. industrial and livestock water demands.')
                self.potFossilGroundwaterAbstract = pcr.max(remainingIndustryDomestic + remainingLivestock, self.potFossilGroundwaterAbstract)


        if self.limitAbstraction == False:                              # TODO: For runs without any water use, we can exclude this. 


            ###############################################################################################################################
            # estimate the remaining total demand (unit: m/day) - LIMITED to self.potFossilGroundwaterAbstract
            ###############################################################################################################################
            correctedRemainingTotalDemand = pcr.min(self.potFossilGroundwaterAbstract, remainingTotalDemand)

            # the remaining industrial and domestic demand and livestock (unit: m/day) - limited to self.potFossilGroundwaterAbstract
            correctedRemainingIndustryDomesticLivestock = pcr.min(remainingIndustryDomestic + remainingLivestock, correctedRemainingTotalDemand)
            
            # the remaining irrigation demand limited to self.potFossilGroundwaterAbstract - limited to self.potFossilGroundwaterAbstract
            correctedRemainingIrrigation = pcr.min(remainingIrrigation, \
                                                   pcr.max(0.0, correctedRemainingTotalDemand - correctedRemainingIndustryDomesticLivestock))
            # - ignore small irrigation demand (less than 1 mm)
            correctedRemainingIrrigation = pcr.rounddown(correctedRemainingIrrigation*1000.)/1000.
            
            # the (corrected) remaining total demand (limited to self.potFossilGroundwaterAbstract)
            correctedRemainingTotalDemand = correctedRemainingIndustryDomesticLivestock + correctedRemainingIrrigation
            
            # the (corrected) remaining industrial and domestic demand (excluding livestock) - limited to self.potFossilGroundwaterAbstract
            correctedRemainingIndustryDomestic = pcr.min(remainingIndustryDomestic, correctedRemainingTotalDemand)

            # the remaining irrigation and livestock water demand - limited to self.potFossilGroundwaterAbstract
            correctedRemainingIrrigationLivestock = pcr.min(remainingIrrigationLivestock, \
                                                    pcr.max(0.0, correctedRemainingTotalDemand - correctedRemainingIndustryDomestic))
                                                  
            # the (corrected) remaining total demand (unit: m/day) - limited to self.potFossilGroundwaterAbstract
            correctedRemainingTotalDemand = correctedRemainingIrrigationLivestock + correctedRemainingIndustryDomestic
            
            # TODO: Do the water balance check: correctedRemainingIrrigationLivestock + correctedRemainingIndustryDomestic <= self.potFossilGroundwaterAbstract                                          

            # constrain the irrigation groundwater demand with groundwater source fraction
            # - this is to constrain that groundwater abstraction should (more less) follow (1 - swAbstractionFractionDict['irrigation']) 
            #~ # -- alternative 1: OLD method:
            #~ correctedRemainingIrrigationLivestock = pcr.min((1.0 - swAbstractionFractionDict['irrigation']) * remainingIrrigationLivestock,\
                                                             #~ correctedRemainingIrrigationLivestock) 
            #~ correctedRemainingIrrigationLivestock = pcr.max(0.0,\
             #~ pcr.min(correctedRemainingIrrigationLivestock,\
             #~ pcr.max(0.0, (self.totalPotentialMaximumIrrGrossDemand + self.totalPotentialMaximumLivestockDemand)) * (1.0 - swAbstractionFractionDict['irrigation']) - satisfiedIrrigationDemandFromNonFossilGroundwater))
            # -- alternative 2: NEW method, simplification as follows (only the second command of the alternative 1 is used)
            correctedRemainingIrrigationLivestock = pcr.max(0.0,\
             pcr.min(correctedRemainingIrrigationLivestock,\
             pcr.max(0.0, (self.totalPotentialMaximumIrrGrossDemand + self.totalPotentialMaximumLivestockDemand)) * (1.0 - swAbstractionFractionDict['irrigation']) - satisfiedIrrigationDemandFromNonFossilGroundwater))
            
            # ignore fossil groundwater abstraction in irrigation areas dominated by swAbstractionFractionDict['irrigation']
            correctedRemainingIrrigationLivestock = pcr.ifthenelse(\
                               swAbstractionFractionDict['irrigation'] >= swAbstractionFractionDict['treshold_to_minimize_fossil_groundwater_irrigation'], 0.0,\
                               correctedRemainingIrrigationLivestock)

            # reduce the fossil irrigation and livestock demands with enough supply of non fossil groundwater (in order to minimize unrealistic areas of fossil groundwater abstraction)
            # - supply from the average recharge (baseflow) and non fossil groundwater allocation 
            nonFossilGroundwaterSupply = pcr.max(pcr.max(0.0, routing.avgBaseflow) / routing.cellArea, \
                                                 groundwater.avgNonFossilAllocationShort, groundwater.avgNonFossilAllocation)  
            # - irrigation supply from the non fossil groundwater
            # -- as a proxy to distribute nonFossilGroundwaterSupply, we use the remaining demand values (philosophy: avoid reduction in areas with small remaining irrigation demands)
            nonFossilIrrigationGroundwaterSupply  = nonFossilGroundwaterSupply * vos.getValDivZero(remainingIrrigationLivestock, remainingTotalDemand)
            # - the corrected/reduced irrigation and livestock demand
            correctedRemainingIrrigationLivestock = pcr.max(0.0, correctedRemainingIrrigationLivestock - nonFossilIrrigationGroundwaterSupply)

            # the corrected remaining total demand (unit: m/day) - LIMITED to self.potFossilGroundwaterAbstract 
            # - total demand
            correctedRemainingTotalDemand = correctedRemainingIndustryDomestic + correctedRemainingIrrigationLivestock
            # - domestic and industry
            correctedRemainingDomestic = correctedRemainingIndustryDomestic * vos.getValDivZero(remainingDomestic, remainingDomestic + remainingIndustry)
            correctedRemainingIndustry = pcr.max(0.0, correctedRemainingIndustryDomestic - correctedRemainingDomestic)
            correctedRemainingIndustryDomestic = correctedRemainingDomestic + correctedRemainingIndustry
            # - livestock and irrigation
            correctedRemainingLivestock  = correctedRemainingIrrigationLivestock * vos.getValDivZero(remainingLivestock, remainingLivestock + remainingIrrigation)
            correctedRemainingIrrigation = pcr.max(0.0, correctedRemainingIrrigationLivestock - correctedRemainingLivestock)
            correctedRemainingIrrigationLivestock = correctedRemainingIrrigation + correctedRemainingLivestock                                                                                                                                             

            ###############################################################################################################################


            # water demand that must be satisfied by fossil groundwater abstraction           
            self.potFossilGroundwaterAbstract = pcr.min(self.potFossilGroundwaterAbstract, correctedRemainingTotalDemand)
            

            # always try to fulfil industrial, domestic, and livestock demands:
            if self.doNotLimitGroundwaterDomesticIndustrialLivestockDemandWithPumpingCapacity:
                logger.debug('There should be no limit groundwater abstraction limit to meet domestic, industrial and livestock water demands.')
                correctedRemainingDomestic   = remainingDomestic
                correctedRemainingIndustry   = remainingIndustry
                correctedRemainingLivestock  = remainingLivestock
                self.potFossilGroundwaterAbstract = pcr.max(correctedRemainingDomestic + correctedRemainingIndustry + correctedRemainingLivestock, \
                                                            self.potFossilGroundwaterAbstract)
                correctedRemainingIrrigation = pcr.max(0.0, self.potFossilGroundwaterAbstract - (correctedRemainingDomestic + correctedRemainingIndustry + correctedRemainingLivestock))
                
                correctedRemainingIrrigationLivestock = correctedRemainingIrrigation + correctedRemainingLivestock
                correctedRemainingIndustryDomestic = correctedRemainingDomestic + correctedRemainingIndustry 
                correctedRemainingTotalDemand = correctedRemainingIndustryDomestic + correctedRemainingIrrigationLivestock 
            

            if groundwater.limitFossilGroundwaterAbstraction == False and self.limitAbstraction == False:

                # Note: If limitFossilGroundwaterAbstraction == False, 
                #       allocation of fossil groundwater abstraction is not needed.  
                msg  = 'Fossil groundwater abstractions are without limit for satisfying local demand. '
                msg  = 'Allocation for fossil groundwater abstraction is NOT needed/implemented. '
                msg += 'However, the fossil groundwater abstraction rate still consider the maximumDailyGroundwaterAbstraction.'
                logger.debug(msg)
                
                # fossil groundwater abstraction (unit: m/day) 
                self.fossilGroundwaterAbstr = self.potFossilGroundwaterAbstract
                self.fossilGroundwaterAbstr = \
                 pcr.min(\
                 pcr.max(0.0, groundwater.maximumDailyGroundwaterAbstraction - self.nonFossilGroundwaterAbs), self.fossilGroundwaterAbstr)
                
                # fossil groundwater allocation (unit: m/day)
                self.fossilGroundwaterAlloc = self.fossilGroundwaterAbstr
        
            if groundwater.limitFossilGroundwaterAbstraction and self.limitAbstraction == False:

                logger.debug('Fossil groundwater abstractions are allowed, but with limit.')
                
                # accesible fossil groundwater (unit: m/day)
                readAvlFossilGroundwater = pcr.ifthenelse(groundwater.productive_aquifer, groundwater.storGroundwaterFossil, 0.0)
                # - residence time (day-1) or safety factor  (to avoid 'unrealistic' zero fossil groundwater)
                readAvlFossilGroundwater *= 0.10
                # - considering maximum daily groundwater abstraction
                readAvlFossilGroundwater = pcr.min(readAvlFossilGroundwater, groundwater.maximumDailyFossilGroundwaterAbstraction, \
                                           pcr.max(0.0, groundwater.maximumDailyGroundwaterAbstraction - self.nonFossilGroundwaterAbs))
                readAvlFossilGroundwater = pcr.max(pcr.cover(readAvlFossilGroundwater, 0.0), 0.0)                                           
                
                if groundwater.usingAllocSegments:
                
                    logger.debug('Allocation of fossil groundwater abstraction.')
                
                    # TODO: considering aquifer productivity while doing the allocation.

                    # fossil groundwater abstraction and allocation in volume (unit: m3)
                    volActGroundwaterAbstract, volAllocGroundwaterAbstract = \
                       vos.waterAbstractionAndAllocation(
                       water_demand_volume = self.potFossilGroundwaterAbstract*routing.cellArea,\
                       available_water_volume = pcr.max(0.00, readAvlFossilGroundwater*routing.cellArea),\
                       allocation_zones = groundwater.allocSegments,\
                       zone_area = groundwater.segmentArea,\
                       high_volume_treshold = None,\
                       debug_water_balance = True,\
                       extra_info_for_water_balance_reporting = str(currTimeStep.fulldate),  
                       landmask = self.landmask,
                       ignore_small_values = False,
                       prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
                    
                    # fossil groundwater abstraction and allocation in meter
                    self.fossilGroundwaterAbstr = volActGroundwaterAbstract  /routing.cellArea 
                    self.fossilGroundwaterAlloc = volAllocGroundwaterAbstract/routing.cellArea 
                
                else:
                    
                    logger.debug('Fossil groundwater abstraction is only for satisfying local demand. NO Allocation for fossil groundwater abstraction.')
                
                    self.fossilGroundwaterAbstr = pcr.min(pcr.max(0.0, readAvlFossilGroundwater), self.potFossilGroundwaterAbstract)
                    self.fossilGroundwaterAlloc = self.fossilGroundwaterAbstr 
        

            #~ # water demand that have been satisfied (m/day) - after desalination, surface water, non fossil groundwater & fossil groundwater
            #~ ################################################################################################################################
            #~ # from fossil groundwater, we should prioritize domestic and industrial water demand
            #~ prioritizeFossilGroundwaterForDomesticIndutrial = False                            # TODO: Define this in the configuration file.
            #~ if prioritizeFossilGroundwaterForDomesticIndutrial:
                #~ 
                #~ # - first priority: for industrial and domestic demand (excluding livestock)
                #~ satisfiedIndustryDomesticDemandFromFossilGroundwater = pcr.min(self.fossilGroundwaterAlloc, \
                                                                                 #~ remainingIndustryDomestic)
                #~ # - for domestic                                                                 
                #~ satisfiedDomesticDemand += satisfiedIndustryDomesticDemandFromFossilGroundwater * vos.getValDivZero(remainingDomestic, \
                                                                                                                 #~ remainingIndustryDomestic)
                #~ # - for industry
                #~ satisfiedIndustryDemand += satisfiedIndustryDomesticDemandFromFossilGroundwater * vos.getValDivZero(remainingIndustry, \
                                                                                                                 #~ remainingIndustryDomestic)             
                #~ # - for irrigation and livestock demand
                #~ satisfiedIrrigationLivestockDemandFromFossilGroundwater = pcr.max(0.0, self.fossilGroundwaterAlloc - \
                                                                                       #~ satisfiedIndustryDomesticDemandFromFossilGroundwater)
                #~ # - for irrigation
                #~ satisfiedIrrigationDemand += satisfiedIrrigationLivestockDemandFromFossilGroundwater * vos.getValDivZero(remainingIrrigation, \
                                                                                                                #~ remainingIrrigationLivestock)
                #~ # - for livestock
                #~ satisfiedLivestockDemand  += satisfiedIrrigationLivestockDemandFromFossilGroundwater * vos.getValDivZero(remainingLivestock, \
                                                                                                                #~ remainingIrrigationLivestock)
            


            # water demand that have been satisfied (unit: m/day) - after desalination, surface water and non-fossil groundwater supply 
            ################################################################################################################################
            if self.prioritizeDomesticThenIndutrialThenLivestock:
                
                logger.debug("Groundwater (fossil) is prioritized to satisfy sectoral water demands with the following order: domestic, indutry, livestock and agriculture/irrigation.")
                
                # - 1st priority: domestic 
                satisfiedDomesticDemandFromFossilGroundwater   = pcr.min(self.fossilGroundwaterAlloc, \
                                                                         correctedRemainingDomestic)
                # - 2nd priority: industry 
                satisfiedIndustryDemandFromFossilGroundwater   = pcr.min(pcr.max(0.0, self.fossilGroundwaterAlloc - satisfiedDomesticDemandFromFossilGroundwater), \
                                                                         correctedRemainingIndustry)
                # - 3rd priority: livestock 
                satisfiedLivestockDemandFromFossilGroundwater  = pcr.min(pcr.max(0.0, self.fossilGroundwaterAlloc - satisfiedDomesticDemandFromFossilGroundwater -\
                                                                                                                    satisfiedIndustryDemandFromFossilGroundwater), \
                                                                         correctedRemainingLivestock)
                # - 4th priority: aggriculture/irrigation (excluding livestock)
                satisfiedIrrigationDemandFromFossilGroundwater = pcr.min(pcr.max(0.0, self.fossilGroundwaterAlloc - satisfiedDomesticDemandFromFossilGroundwater -\
                                                                                                                    satisfiedIndustryDemandFromFossilGroundwater -\
                                                                                                                    satisfiedLivestockDemandFromFossilGroundwater), \
                                                                         correctedRemainingIrrigation)
                
                satisfiedIrrigationLivestockDemandFromFossilGroundwater = satisfiedIrrigationDemandFromFossilGroundwater + \
                                                                          satisfiedLivestockDemandFromFossilGroundwater
                
                satisfiedNonIrrDemandFromFossilGroundwater = satisfiedDomesticDemandFromFossilGroundwater + satisfiedIndustryDemandFromFossilGroundwater +\
                                                             satisfiedLivestockDemandFromFossilGroundwater
            
            
            else:
            
                # Distribute fossil water proportionaly based on the amount of each sector
                
                # - for irrigation and livestock water demand 
                satisfiedIrrigationLivestockDemandFromFossilGroundwater = self.fossilGroundwaterAlloc * \
                                                                          vos.getValDivZero(correctedRemainingIrrigationLivestock, correctedRemainingTotalDemand)
                # - for irrigation water demand, but not including livestock 
                satisfiedIrrigationDemandFromFossilGroundwater = satisfiedIrrigationLivestockDemandFromFossilGroundwater * \
                                                                 vos.getValDivZero(correctedRemainingIrrigation, correctedRemainingIrrigationLivestock)
                # - for non irrigation water demand: livestock, domestic and industry 
                satisfiedNonIrrDemandFromFossilGroundwater = pcr.max(0.0, self.fossilGroundwaterAlloc - satisfiedIrrigationDemandFromFossilGroundwater)
                # - for livestock                                                                      
                satisfiedLivestockDemandFromFossilGroundwater = pcr.max(0.0, satisfiedIrrigationLivestockDemandFromFossilGroundwater - \
                                                                             satisfiedIrrigationDemandFromFossilGroundwater)
                # - for industrial and domestic demand (excluding livestock)
                satisfiedIndustryDomesticDemandFromFossilGroundwater = pcr.max(0.0, self.fossilGroundwaterAlloc - \
                                                                                      satisfiedIrrigationLivestockDemandFromFossilGroundwater)
                # - for domestic                                                                 
                satisfiedDomesticDemandFromFossilGroundwater = satisfiedIndustryDomesticDemandFromFossilGroundwater * vos.getValDivZero(correctedRemainingDomestic, \
                                                                                                                      correctedRemainingIndustryDomestic)
                # - for industry
                satisfiedIndustryDemandFromFossilGroundwater = satisfiedIndustryDomesticDemandFromFossilGroundwater * vos.getValDivZero(correctedRemainingIndustry, \
                                                                                                                      correctedRemainingIndustryDomestic)             

        
        # update satistfied demand fossil groundwater allocation
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromFossilGroundwater
        satisfiedLivestockDemand  += satisfiedLivestockDemandFromFossilGroundwater
        satisfiedDomesticDemand   += satisfiedDomesticDemandFromFossilGroundwater
        satisfiedIndustryDemand   += satisfiedIndustryDemandFromFossilGroundwater


        if self.debugWaterBalance:
            vos.waterBalanceCheck([satisfiedDomesticDemand, \
                                   satisfiedIndustryDemand, \
                                   satisfiedLivestockDemand, \
                                   satisfiedIrrigationDemand],\
                                  [self.desalinationAllocation, self.allocSurfaceWaterAbstract, self.allocNonFossilGroundwater, self.fossilGroundwaterAlloc],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'desalinatedWaterAllocationForAllSectors and surfaceWaterAllocationForAllSectors and ALL groundwaterAllocationForAllSectors', True,\
                                   currTimeStep.fulldate,threshold=1e-4)


        # Use the default PCR-GLOBWB allocation scheme to use surface water for fulfiling the remaining demand
        extraSurfaceWaterAbstraction = 0.0
        extraSurfacWaterAllocation   = 0.0
        if self.optimizeSurfaceWaterBasedOnRatioOfBaseflowDischargeAllocationScheme: 

            # remaining water demand per sector 
            # - for domestic 
            remainingDomestic   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['domestic']  - satisfiedDomesticDemand)
            # - for industry 
            remainingIndustry   = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['industry']  - satisfiedIndustryDemand)
            # - for livestock 
            remainingLivestock  = pcr.max(0.0, nonIrrGrossDemandDict['potential_demand']['livestock'] - satisfiedLivestockDemand)
            # - for irrigation (excluding livestock)
            remainingIrrigation = pcr.max(0.0, self.irrGrossDemand - satisfiedIrrigationDemand) 
            # - remaining total demand
            remainingTotalDemand = remainingDomestic + remainingIndustry + remainingLivestock +\
                                   remainingIrrigation

            # Abstraction and Allocation of SURFACE WATER EXTRA
            ##############################################################################################################################
            
            # calculate the remaining surface water demand (m) - limited by swAbstractionFractionDict['estimate'] = ratio of discharge and baseflow
            remaining_surface_water_demand = pcr.min(remainingTotalDemand,\
                                                     swAbstractionFractionDict['estimate'] * self.totalPotentialMaximumGrossDemand)                                           
            # - remaining water demand per sector - limited by swAbstractionFractionDict['estimate'] 
            if self.prioritizeDomesticThenIndutrialThenLivestock:
                
                logger.debug("Extra surface water is prioritized to satisfy sectoral water demands with the following order: domestic, indutry, livestock and agriculture/irrigation.")
                
                remainingDomestic   = pcr.min(remainingDomestic,   remaining_surface_water_demand)
                remainingIndustry   = pcr.min(remainingIndustry,   pcr.max(0.0, remaining_surface_water_demand - remainingDomestic))
                remainingLivestock  = pcr.min(remainingLivestock,  pcr.max(0.0, remaining_surface_water_demand - remainingDomestic - remainingIndustry))
                remainingIrrigation = pcr.min(remainingIrrigation, pcr.max(0.0, remaining_surface_water_demand - remainingDomestic - remainingIndustry - \
                                                                                                                                     remainingLivestock))

            else:

                remainingDomestic   = remaining_surface_water_demand * vos.getValDivZero(remainingDomestic , remainingTotalDemand)
                remainingIndustry   = remaining_surface_water_demand * vos.getValDivZero(remainingIndustry , remainingTotalDemand)
                remainingLivestock  = remaining_surface_water_demand * vos.getValDivZero(remainingLivestock, remainingTotalDemand)
                remainingIrrigation = pcr.max(0.0, remaining_surface_water_demand - remainingDomestic -\
                                                                                    remainingIndustry -\
                                                                                    remainingLivestock)

            # - total for livestock and irrigation - limited by swAbstractionFractionDict['estimate']
            remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
            # - total for industrial and domestic (excluding livestock) - limited by swAbstractionFractionDict['estimate']
            remainingIndustryDomestic    = remainingIndustry + remainingDomestic
            # - total for all sectors - limited by swAbstractionFractionDict['estimate'] - this is the same as remaining_surface_water_demand
            remainingTotalDemand = remainingDomestic + remainingIndustry + remainingLivestock +\
                                   remainingIrrigation

        if self.debugWaterBalance:
            vos.waterBalanceCheck([remainingTotalDemand],\
                                  [remaining_surface_water_demand],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'partitioning remaining surface water demand', True,\
                                   currTimeStep.fulldate,threshold=1e-4)

            # calculate remaining available surface water (m3)
            remaining_available_surface_water_volume = pcr.max(0.0, routing.readAvlChannelStorage - volActSurfaceWaterAbstract * routing.cellArea)
            
            if self.usingAllocSegments:      # using zone/segment at which supply network is defined
            #  
                logger.debug("Allocation of extra surface water abstraction.")
            #  
                volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = \
                 vos.waterAbstractionAndAllocation(
                 water_demand_volume = remaining_surface_water_demand * routing.cellArea,\
                 available_water_volume = pcr.max(0.00, remaining_available_surface_water_volume),\
                 allocation_zones = allocSegments,\
                 zone_area = self.segmentArea,\
                 high_volume_treshold = None,\
                 debug_water_balance = True,\
                 extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
                 landmask = self.landmask,
                 ignore_small_values = False,
                 prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
    
                extraSurfaceWaterAbstraction = volActSurfaceWaterAbstract / routing.cellArea
                extraSurfacWaterAllocation   = volAllocSurfaceWaterAbstract / routing.cellArea
            #  
            else: 
                logger.debug("Extra surface water abstraction is only to satisfy local demand (no surface water network).")
                extraSurfaceWaterAbstraction   = pcr.min(remaining_available_surface_water_volume/routing.cellArea,\
                                                         remaining_surface_water_demand)                              # unit: m
                extraSurfacWaterAllocation     = extraSurfaceWaterAbstraction                                         # unit: m   
            #  
            extraSurfaceWaterAbstraction = pcr.ifthen(self.landmask, extraSurfaceWaterAbstraction)  
            extraSurfacWaterAllocation   = pcr.ifthen(self.landmask, extraSurfacWaterAllocation  )
            ################################################################################################################################
            # - end of Abstraction and Allocation of EXTRA SURFACE WATER
    
            # water demand that have been satisfied (unit: m/day) - after desalination and surface water supply
            ################################################################################################################################
            if self.prioritizeDomesticThenIndutrialThenLivestock:
                
                logger.debug("Extra surface water is prioritized to satisfy sectoral water demands with the following order: domestic, indutry, livestock and agriculture/irrigation.")
    
                # - 1st priority: domestic 
                satisfiedDomesticDemandFromExtraSurfaceWater   = pcr.min(extraSurfacWaterAllocation, \
                                                                         remainingDomestic)
                # - 2nd priority: industry 
                satisfiedIndustryDemandFromExtraSurfaceWater   = pcr.min(pcr.max(0.0, extraSurfacWaterAllocation - satisfiedDomesticDemandFromExtraSurfaceWater), \
                                                                         remainingIndustry)
                # - 3rd priority: livestock 
                satisfiedLivestockDemandFromExtraSurfaceWater  = pcr.min(pcr.max(0.0, extraSurfacWaterAllocation - satisfiedDomesticDemandFromExtraSurfaceWater -\
                                                                                                                   satisfiedIndustryDemandFromExtraSurfaceWater), \
                                                                         remainingLivestock)
                # - 4th priority: aggriculture/irrigation (excluding livestock)
                satisfiedIrrigationDemandFromExtraSurfaceWater = pcr.min(pcr.max(0.0, extraSurfacWaterAllocation - satisfiedDomesticDemandFromExtraSurfaceWater -\
                                                                                                                   satisfiedIndustryDemandFromExtraSurfaceWater -\
                                                                                                                   satisfiedLivestockDemandFromExtraSurfaceWater),
                                                                         remainingIrrigation)
                
                satisfiedIrrigationLivestockDemandFromExtraSurfaceWater = satisfiedIrrigationDemandFromExtraSurfaceWater + \
                                                                          satisfiedLivestockDemandFromExtraSurfaceWater
                
                satisfiedNonIrrDemandFromExtraSurfaceWater = satisfiedDomesticDemandFromExtraSurfaceWater + satisfiedIndustryDemandFromExtraSurfaceWater + \
                                                             satisfiedLivestockDemandFromExtraSurfaceWater
    
            else:
    
                # - for domestic:
                satisfiedDomesticDemandFromExtraSurfaceWater   = extraSurfacWaterAllocation * vos.getValDivZero(remainingDomestic,  remainingTotalDemand)
                # - for industry:
                satisfiedIndustryDemandFromExtraSurfaceWater   = extraSurfacWaterAllocation * vos.getValDivZero(remainingIndustry,  remainingTotalDemand)
                # - for livestock:
                satisfiedLivestockDemandFromExtraSurfaceWater  = extraSurfacWaterAllocation * vos.getValDivZero(remainingLivestock, remainingTotalDemand)
                # - for irrigation (excluding livesock)
                satisfiedIrrigationDemandFromExtraSurfaceWater = pcr.max(0.0, extraSurfacWaterAllocation - (satisfiedDomesticDemandFromExtraSurfaceWater +\
                                                                                                           satisfiedIndustryDemandFromExtraSurfaceWater +\
                                                                                                           satisfiedLivestockDemandFromExtraSurfaceWater))
                # - for irrigation and livestock water demand 
                satisfiedIrrigationLivestockDemandFromExtraSurfaceWater = satisfiedLivestockDemandFromExtraSurfaceWater + satisfiedIrrigationDemandFromExtraSurfaceWater
                # - for industrial and domestic demand (excluding livestock)
                satisfiedIndustryDomesticDemandFromExtraSurfaceWater  = satisfiedIndustryDemandFromExtraSurfaceWater + satisfiedDomesticDemandFromExtraSurfaceWater
    
            # update satistfied demand after surface water allocaction 
            satisfiedIrrigationDemand += satisfiedIrrigationDemandFromExtraSurfaceWater
            satisfiedLivestockDemand  += satisfiedLivestockDemandFromExtraSurfaceWater
            satisfiedDomesticDemand   += satisfiedDomesticDemandFromExtraSurfaceWater
            satisfiedIndustryDemand   += satisfiedIndustryDemandFromExtraSurfaceWater

        self.actSurfaceWaterAbstract   = self.actSurfaceWaterAbstract   + extraSurfaceWaterAbstraction
        self.allocSurfaceWaterAbstract = self.allocSurfaceWaterAbstract + extraSurfacWaterAllocation
        
        if self.debugWaterBalance:
            vos.waterBalanceCheck([satisfiedDomesticDemand, \
                                   satisfiedIndustryDemand, \
                                   satisfiedLivestockDemand, \
                                   satisfiedIrrigationDemand],\
                                  [self.desalinationAllocation, self.allocSurfaceWaterAbstract, self.allocNonFossilGroundwater, self.fossilGroundwaterAlloc],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'desalinatedWaterAllocationForAllSectors and surfaceWaterAllocationForAllSectors (including extraSurfacWaterAllocation) and ALL groundwaterAllocationForAllSectors', True,\
                                   currTimeStep.fulldate,threshold=1e-4)
        
        # water demand limited to available/allocated water
        self.totalPotentialGrossDemand = self.fossilGroundwaterAlloc +\
                                         self.allocNonFossilGroundwater +\
                                         self.allocSurfaceWaterAbstract +\
                                         self.desalinationAllocation

        # total groundwater abstraction and allocation (unit: m/day) 
        self.totalGroundwaterAllocation  = self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
        self.totalGroundwaterAbstraction = self.fossilGroundwaterAbstr + self.nonFossilGroundwaterAbs

        # irrigation water demand (excluding livestock) limited to available/allocated water (unit: m/day)
        self.irrGrossDemand = satisfiedIrrigationDemand                                  # not including livestock 
        
        # irrigation gross demand (m) per cover type (limited by available water)
        self.irrGrossDemandPaddy    = 0.0
        self.irrGrossDemandNonPaddy = 0.0
        if self.name == 'irrPaddy' or self.name == "irr_paddy": self.irrGrossDemandPaddy = self.irrGrossDemand
        if self.name == 'irrNonPaddy' or self.name == "irr_non_paddy" or self.name == "irr_non_paddy_crops": self.irrGrossDemandNonPaddy = self.irrGrossDemand

        # non irrigation water demand (including livestock) limited to available/allocated water (unit: m/day)
        self.nonIrrGrossDemand = pcr.max(0.0, \
                                 self.totalPotentialGrossDemand - self.irrGrossDemand)   # livestock, domestic and industry
        self.domesticWaterWithdrawal  = satisfiedDomesticDemand
        self.industryWaterWithdrawal  = satisfiedIndustryDemand
        self.livestockWaterWithdrawal = satisfiedLivestockDemand
        
        # return flow (unit: m/day) from non irrigation withdrawal (from domestic, industry and livestock)
        self.nonIrrReturnFlow = nonIrrGrossDemandDict['return_flow_fraction']['domestic'] * self.domesticWaterWithdrawal +\
                                nonIrrGrossDemandDict['return_flow_fraction']['industry'] * self.industryWaterWithdrawal +\
                                nonIrrGrossDemandDict['return_flow_fraction']['livestock']* self.livestockWaterWithdrawal
        #~ # - ignore very small return flow (less than 0.1 mm)
        #~ self.nonIrrReturnFlow = pcr.rounddown(self.nonIrrReturnFlow * 10000.)/10000.
        #~ self.nonIrrReturnFlow = pcr.min(self.nonIrrReturnFlow, self.nonIrrGrossDemand)                        

        if self.debugWaterBalance:
            vos.waterBalanceCheck([self.irrGrossDemand,\
                                   self.nonIrrGrossDemand],\
                                  [self.totalPotentialGrossDemand],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'waterAllocationForAllSectors',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
            vos.waterBalanceCheck([self.domesticWaterWithdrawal,\
                                   self.industryWaterWithdrawal,\
                                   self.livestockWaterWithdrawal],\
                                  [self.nonIrrGrossDemand],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'waterAllocationForNonIrrigationSectors',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
            vos.waterBalanceCheck([self.irrGrossDemand,\
                                   self.domesticWaterWithdrawal,\
                                   self.industryWaterWithdrawal,\
                                   self.livestockWaterWithdrawal],\
                                  [self.totalPotentialGrossDemand],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)] ,\
                                  'waterAllocationPerSector',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
        
        # TODO: Perform water balance checks for all sources: desalination, surface water, non-fossil groundwater and fossil groundwater 
        
        
        
                                 

    def calculateDirectRunoff(self):

        # topWaterLater is partitioned into directRunoff (and infiltration)
        self.directRunoff = self.improvedArnoScheme(\
                            iniWaterStorage = self.soilWaterStorage, \
                            inputNetLqWaterToSoil =  self.topWaterLayer, \
                            directRunoffReductionMethod = self.improvedArnoSchemeMethod)
        self.directRunoff = pcr.min(self.topWaterLayer, self.directRunoff)
        
        # Yet, we minimize directRunoff in the irrigation areas:
        if self.name.startswith('irr') and self.includeIrrigation: self.directRunoff = pcr.scalar(0.0)

        # update topWaterLayer (above soil) after directRunoff
        self.topWaterLayer = pcr.max(0.0, self.topWaterLayer - self.directRunoff)

    def improvedArnoScheme(self, iniWaterStorage, inputNetLqWaterToSoil, directRunoffReductionMethod = "Default"):

        # arnoBeta = BCF = b coefficient of soil water storage capacity distribution
        # 
        # WMIN = root zone water storage capacity, minimum values
        # WMAX = root zone water storage capacity, area-averaged values
        # W	   = actual water storage in root zone
        # WRANGE  = WMAX - WMIN
        # DW      = WMAX-W 
        # WFRAC   = DW/WRANGE ; WFRAC capped at 1
        # WFRACB  = DW/WRANGE raised to the power (1/(b+1))
        # SATFRAC =	fractional saturated area
        # WACT    = actual water storage within rootzone

        self.satAreaFracOld = self.satAreaFrac
        
        Pn = iniWaterStorage + \
             inputNetLqWaterToSoil                                      # Pn = W[TYPE]+Pn;
        Pn = Pn - pcr.max(self.rootZoneWaterStorageMin, \
                                    iniWaterStorage)                    # Pn = Pn-max(WMIN[TYPE],W[TYPE]);
        soilWaterStorage = pcr.ifthenelse(Pn < 0.,\
                                     self.rootZoneWaterStorageMin+Pn, \
             pcr.max(iniWaterStorage,self.rootZoneWaterStorageMin))     # W[TYPE]= if(Pn<0,WMIN[TYPE]+Pn,max(W[TYPE],WMIN[TYPE]));
        Pn = pcr.max(0.,Pn)                                             # Pn = max(0,Pn);
        #
        DW = pcr.max(0.0,self.parameters.rootZoneWaterStorageCap - \
                                         soilWaterStorage)              # DW = max(0,WMAX[TYPE]-W[TYPE]);
 
        #~ WFRAC = pcr.min(1.0,DW/self.rootZoneWaterStorageRange)          # WFRAC = min(1,DW/WRANGE[TYPE]);
        # modified by Edwin ; to solve problems with rootZoneWaterStorageRange = 0.0
        WFRAC = pcr.ifthenelse(self.rootZoneWaterStorageRange > 0.0, pcr.min(1.0,DW/self.rootZoneWaterStorageRange), 1.0)
        
        self.WFRACB = WFRAC**(1./(1.+self.arnoBeta))                    # WFRACB = WFRAC**(1/(1+BCF[TYPE]));
        #
        self.satAreaFrac = pcr.ifthenelse(self.WFRACB > 0.,\
                                       1.-self.WFRACB**self.arnoBeta,\
                                                  1.)                   # SATFRAC_L = if(WFRACB>0,1-WFRACB**BCF[TYPE],1);
        # make sure that 0.0 <= satAreaFrac <= 1.0
        self.satAreaFrac = pcr.min(self.satAreaFrac, 1.0)
        self.satAreaFrac = pcr.max(self.satAreaFrac, 0.0)
        
        actualW = (self.arnoBeta+1.0)*self.parameters.rootZoneWaterStorageCap - \
                   self.arnoBeta*self.rootZoneWaterStorageMin - \
                  (self.arnoBeta+1.0)*self.rootZoneWaterStorageRange*self.WFRACB       
                                                                        # WACT_L = (BCF[TYPE]+1)*WMAX[TYPE]- BCF[TYPE]*WMIN[TYPE]- (BCF[TYPE]+1)*WRANGE[TYPE]*WFRACB;

        
        directRunoffReduction = pcr.scalar(0.0)                         # as in the "Original" work of van Beek et al. (2011)   
        if directRunoffReductionMethod == "Default":
            if self.numberOfLayers == 2: directRunoffReduction = pcr.min(self.kUnsatLow,\
                                                                 pcr.sqrt(self.kUnsatLow*self.parameters.kUnsatAtFieldCapLow))
            if self.numberOfLayers == 3: directRunoffReduction = pcr.min(self.kUnsatLow030150,\
                                                                 pcr.sqrt(self.kUnsatLow030150*self.parameters.kUnsatAtFieldCapLow030150))
                                                                                                                         # Rens: # In order to maintain full saturation and     
                                                                                                                         # continuous groundwater recharge/percolation, 
                                                                                                                         # the amount of directRunoff may be reduced.  
                                                                                                                         # In this case, this reduction is estimated 
                                                                                                                         # based on (for two layer case) percLow = pcr.min(KUnSatLow,\ 
                                                                                                                         #                                         pcr.sqrt(self.parameters.KUnSatFC2*KUnSatLow))
        
        if directRunoffReductionMethod == "Modified":
            if self.numberOfLayers == 2: directRunoffReduction = pcr.min(self.kUnsatLow,\
                                                                 pcr.sqrt(self.kUnsatLow*self.parameters.kUnsatAtFieldCapLow))
            if self.numberOfLayers == 3: directRunoffReduction = pcr.min(self.kUnsatLow030150,\
                                                                 pcr.sqrt(self.kUnsatLow030150*self.parameters.kUnsatAtFieldCapLow030150))
            # the reduction of directRunoff (preferential flow groundwater) 
            # is only introduced if the soilWaterStorage near its saturation
            # - this is in order to maintain the saturation
            saturation_treshold = 0.999
            directRunoffReduction = pcr.ifthenelse(vos.getValDivZero(soilWaterStorage,self.parameters.rootZoneWaterStorageCap) > saturation_treshold, directRunoffReduction, 0.0)
        
        # directRunoff
        condition = (self.arnoBeta+pcr.scalar(1.))*self.rootZoneWaterStorageRange* self.WFRACB
        directRunoff = pcr.max(0.0, \
                          Pn -\
                      (self.parameters.rootZoneWaterStorageCap+directRunoffReduction-soilWaterStorage) + \
           pcr.ifthenelse(Pn >= condition,
                          pcr.scalar(0.0), \
                          self.rootZoneWaterStorageRange*(self.WFRACB-\
                          Pn / ((self.arnoBeta+1.)*\
                          self.rootZoneWaterStorageRange))**(self.arnoBeta+1.)))
                                                                        #    Q1_L[TYPE]= max(0,Pn-(WMAX[TYPE]+P2_L[TYPE]-W[TYPE])+
                                                                        #      if(Pn>=(BCF[TYPE]+1)*WRANGE[TYPE]*WFRACB, 0,
                                                                        #      WRANGE[TYPE]*(WFRACB-Pn/((BCF[TYPE]+1)*WRANGE[TYPE]))**(BCF[TYPE]+1))); #*
        # make sure that there is always value
        directRunoff = pcr.cover(directRunoff, 0.0)
        
        return directRunoff                                            

    def calculateOpenWaterEvap(self):

        # update topWaterLayer (above soil) 
        # - with netLqWaterToSoil and irrGrossDemand
        self.topWaterLayer += pcr.max(0.,self.netLqWaterToSoil + self.irrGrossDemand)

        # potential evaporation for openWaterEvap
        remainingPotETP = self.potBareSoilEvap + self.potTranspiration   # Edwin's principle: LIMIT = self.potBareSoilEvap +self.potTranspiration 
        # remainingPotETP = self.totalPotET                              # DW, RvB, and YW use self.totalPotETP
        
        # openWaterEvap is ONLY for evaporation from paddy field areas
        self.openWaterEvap = pcr.spatial(pcr.scalar(0.))

        if self.name == 'irrPaddy' or self.name == "irr_paddy":  # only open water evaporation from the paddy field
            self.openWaterEvap = \
             pcr.min(\
             pcr.max(0.,self.topWaterLayer), remainingPotETP)  
        
        # update potBareSoilEvap & potTranspiration (after openWaterEvap)
        # - CHECK; WHY DO WE USE COVER ABOVE? Edwin replaced them using the following lines:
        self.potBareSoilEvap  = pcr.cover(\
                                pcr.max(0.0, self.potBareSoilEvap -\
                                vos.getValDivZero(self.potBareSoilEvap, remainingPotETP)*self.openWaterEvap ), 0.0)      
        self.potTranspiration = pcr.cover(\
                                pcr.max(0.0, self.potTranspiration -\
                                vos.getValDivZero(self.potTranspiration, remainingPotETP)*self.openWaterEvap), 0.0)

        # update top water layer after openWaterEvap
        self.topWaterLayer = pcr.max(0.,self.topWaterLayer - self.openWaterEvap)
        
    def calculateInfiltration(self):

        # infiltration, limited with KSat1 and available water in topWaterLayer
        if self.numberOfLayers == 2:
            self.infiltration = pcr.min(self.topWaterLayer,self.parameters.kSatUpp)             # P0_L = min(P0_L,KS1*Duration*timeslice());

        if self.numberOfLayers == 3:
            self.infiltration = pcr.min(self.topWaterLayer,self.parameters.kSatUpp000005)       # P0_L = min(P0_L,KS1*Duration*timeslice());

        # for paddy, infiltration should consider percolation losses 
        if (self.name == 'irrPaddy' or self.name == "irr_paddy") and self.includeIrrigation:
            infiltration_loss = pcr.max(self.design_percolation_loss, 
                                ((1./self.irrigationEfficiencyUsed) - 1.) * self.topWaterLayer)
            self.infiltration = pcr.min(infiltration_loss, self.infiltration)

        # update top water layer after infiltration
        self.topWaterLayer = pcr.max(0.0,\
                             self.topWaterLayer - self.infiltration)

        # release excess topWaterLayer above minTopWaterLayer as additional direct runoff
        self.directRunoff += pcr.max(0.0,\
                             self.topWaterLayer - self.minTopWaterLayer)

        # update topWaterLayer after additional direct runoff
        self.topWaterLayer = pcr.min( self.topWaterLayer , \
                                      self.minTopWaterLayer)

    def estimateTranspirationAndBareSoilEvap(self, returnTotalEstimation = False, returnTotalTranspirationOnly = False):

        # TRANSPIRATION
        #
        # - fractions for distributing transpiration (based on rott fraction and actual layer storages)
        #
        if self.numberOfLayers == 2:
            dividerTranspFracs = pcr.max( 1e-9, self.adjRootFrUpp*self.storUpp +\
                                                self.adjRootFrLow*self.storLow )
            transpFracUpp = \
                pcr.ifthenelse((self.storUpp + self.storLow) > 0.,\
                               self.adjRootFrUpp*self.storUpp/ dividerTranspFracs, \
                               self.adjRootFrUpp)
            transpFracLow = \
                pcr.ifthenelse((self.storUpp + self.storLow) > 0.,\
                               self.adjRootFrLow*self.storLow/ dividerTranspFracs, \
                               self.adjRootFrLow)                                              #   WF1= if((S1_L[TYPE]+S2_L[TYPE])>0,RFW1[TYPE]*S1_L[TYPE]/
                                                                                               #    max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW1[TYPE]);
                                                                                               #   WF2= if((S1_L[TYPE]+S2_L[TYPE])>0,RFW2[TYPE]*S2_L[TYPE]/
                                                                                               #    max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW2[TYPE]);
        if self.numberOfLayers == 3:
            dividerTranspFracs = pcr.max( 1e-9, self.adjRootFrUpp000005*self.storUpp000005 +\
                                                self.adjRootFrUpp005030*self.storUpp005030 +\
                                                self.adjRootFrLow030150*self.storLow030150)
            transpFracUpp000005 = \
                pcr.ifthenelse((self.storUpp000005 + \
                                self.storUpp005030 + \
                                self.storLow030150) > 0.,\
                                self.adjRootFrUpp000005*self.storUpp000005/ dividerTranspFracs, \
                                self.adjRootFrUpp000005)
            transpFracUpp005030 = \
                pcr.ifthenelse((self.storUpp000005 + \
                                self.storUpp005030 + \
                                self.storLow030150) > 0.,\
                                self.adjRootFrUpp005030*self.storUpp005030/ dividerTranspFracs, \
                                self.adjRootFrUpp005030)
            transpFracLow030150 = \
                pcr.ifthenelse((self.storUpp000005 + \
                                self.storUpp005030 + \
                                self.storLow030150) > 0.,\
                                self.adjRootFrLow030150*self.storLow030150/ dividerTranspFracs, \
                                self.adjRootFrLow030150)

        relActTranspiration = pcr.scalar(1.0) # no reduction in case of returnTotalEstimation
        if returnTotalEstimation == False:
            # reduction factor for transpiration
            #
            # - relActTranspiration = fraction actual transpiration over potential transpiration 
            relActTranspiration = (self.parameters.rootZoneWaterStorageCap  + \
                       self.arnoBeta*self.rootZoneWaterStorageRange*(1.- \
                   (1.+self.arnoBeta)/self.arnoBeta*self.WFRACB)) / \
                                  (self.parameters.rootZoneWaterStorageCap  + \
                       self.arnoBeta*self.rootZoneWaterStorageRange*(1.- self.WFRACB))   # original Rens's line: 
                                                                                         # FRACTA[TYPE] = (WMAX[TYPE]+BCF[TYPE]*WRANGE[TYPE]*(1-(1+BCF[TYPE])/BCF[TYPE]*WFRACB))/
                                                                                         #                (WMAX[TYPE]+BCF[TYPE]*WRANGE[TYPE]*(1-WFRACB));
            relActTranspiration = (1.-self.satAreaFrac) / \
              (1.+(pcr.max(0.01,relActTranspiration)/self.effSatAt50)**\
                                           (self.effPoreSizeBetaAt50*pcr.scalar(-3.0)))  # original Rens's line:
                                                                                         # FRACTA[TYPE] = (1-SATFRAC_L)/(1+(max(0.01,FRACTA[TYPE])/THEFF_50[TYPE])**(-3*BCH_50));
        relActTranspiration = pcr.max(0.0, relActTranspiration)
        relActTranspiration = pcr.min(1.0, relActTranspiration)
        
        # an idea by Edwin - 23 March 2015: no transpiration reduction in irrigated areas:
        if self.name.startswith('irr') and self.includeIrrigation: relActTranspiration = pcr.scalar(1.0)
        

        #~ #######################################################################################################################################
        #~ # estimates of actual transpiration fluxes - OLD METHOD (not used anymore, after Rens provided his original script, 30 July 2015)
        #~ if self.numberOfLayers == 2:
            #~ actTranspiUpp = \
              #~ relActTranspiration*transpFracUpp*self.potTranspiration
            #~ actTranspiLow = \
              #~ relActTranspiration*transpFracLow*self.potTranspiration
        #~ if self.numberOfLayers == 3:
            #~ actTranspiUpp000005 = \
              #~ relActTranspiration*transpFracUpp000005*self.potTranspiration
            #~ actTranspiUpp005030 = \
              #~ relActTranspiration*transpFracUpp005030*self.potTranspiration
            #~ actTranspiLow030150 = \
              #~ relActTranspiration*transpFracLow030150*self.potTranspiration
        #~ #######################################################################################################################################
        

        # partitioning potential tranpiration (based on Rens's oldcalc script provided 30 July 2015)
        if self.numberOfLayers == 2:
            potTranspirationUpp = pcr.min(transpFracUpp*self.potTranspiration, self.potTranspiration)
            potTranspirationLow = pcr.max(0.0, self.potTranspiration - potTranspirationUpp)
        if self.numberOfLayers == 3:
            potTranspirationUpp000005 = pcr.min(transpFracUpp000005*self.potTranspiration, self.potTranspiration)
            potTranspirationUpp005030 = pcr.min(transpFracUpp005030*self.potTranspiration, pcr.max(0.0, self.potTranspiration - potTranspirationUpp000005))
            potTranspirationLow030150 = pcr.max(0.0, self.potTranspiration - potTranspirationUpp000005 - potTranspirationUpp005030)
            
        # estimate actual transpiration fluxes
        if self.numberOfLayers == 2:
            actTranspiUpp = pcr.cover(relActTranspiration*potTranspirationUpp, 0.0)
            actTranspiLow = pcr.cover(relActTranspiration*potTranspirationLow, 0.0)
        if self.numberOfLayers == 3:
            actTranspiUpp000005 = pcr.cover(relActTranspiration*potTranspirationUpp000005, 0.0)
            actTranspiUpp005030 = pcr.cover(relActTranspiration*potTranspirationUpp005030, 0.0)
            actTranspiLow030150 = pcr.cover(relActTranspiration*potTranspirationLow030150, 0.0)


        # BARE SOIL EVAPORATION
        #        
        # actual bare soil evaporation (potential) # no reduction in case of returnTotalEstimation
        actBareSoilEvap = self.potBareSoilEvap
        if self.numberOfLayers == 2 and returnTotalEstimation == False:
            actBareSoilEvap =     self.satAreaFrac * pcr.min(\
                                   self.potBareSoilEvap,self.parameters.kSatUpp) + \
                                  (1.-self.satAreaFrac)* pcr.min(\
                                   self.potBareSoilEvap,self.kUnsatUpp)            # ES_a[TYPE] =  SATFRAC_L *min(ES_p[TYPE],KS1[TYPE]*Duration*timeslice())+
                                                                                   #            (1-SATFRAC_L)*min(ES_p[TYPE],KTHEFF1*Duration*timeslice());
        if self.numberOfLayers == 3 and returnTotalEstimation == False:
            actBareSoilEvap =     self.satAreaFrac * pcr.min(\
                                   self.potBareSoilEvap,self.parameters.kSatUpp000005) + \
                                  (1.-self.satAreaFrac)* pcr.min(\
                                   self.potBareSoilEvap,self.kUnsatUpp000005)
        actBareSoilEvap = pcr.max(0.0, actBareSoilEvap)
        actBareSoilEvap = pcr.min(actBareSoilEvap,self.potBareSoilEvap) 
        actBareSoilEvap = pcr.cover(actBareSoilEvap, 0.0)                           

        # no bare soil evaporation in the inundated paddy field 
        if self.name == 'irrPaddy' or self.name == "irr_paddy":
            # no bare soil evaporation if topWaterLayer is above treshold
            #~ treshold = 0.0005 # unit: m ; 
            treshold = self.potBareSoilEvap + self.potTranspiration                # an idea by Edwin on 23 march 2015
            actBareSoilEvap = pcr.ifthenelse(self.topWaterLayer > treshold, 0.0, actBareSoilEvap)
        
        # return the calculated variables:
        if self.numberOfLayers == 2:
            if returnTotalEstimation:
                if returnTotalTranspirationOnly:
                    return actTranspiUpp+ actTranspiLow
                else:     
                    return actBareSoilEvap+ actTranspiUpp+ actTranspiLow
            else:
                return actBareSoilEvap, actTranspiUpp, actTranspiLow 
        if self.numberOfLayers == 3:
            if returnTotalEstimation:
                if returnTotalTranspirationOnly:
                    return actTranspiUpp000005+ actTranspiUpp005030+ actTranspiLow030150
                else:     
                    return actBareSoilEvap+ actTranspiUpp000005+ actTranspiUpp005030+ actTranspiLow030150
            else:
                return actBareSoilEvap, actTranspiUpp000005, actTranspiUpp005030, actTranspiLow030150

    def estimateSoilFluxes(self,capRiseFrac,groundwater):

        # Given states, we estimate all fluxes.
        ################################################################
        
        if self.numberOfLayers == 2:

            # - percolation from storUpp to storLow
            self.percUpp = self.kThVertUppLow * 1.
            self.percUpp = \
                 pcr.ifthenelse(     self.effSatUpp > self.parameters.effSatAtFieldCapUpp, \
                 pcr.min(pcr.max(0., self.effSatUpp - self.parameters.effSatAtFieldCapUpp)*self.parameters.storCapUpp, self.percUpp), self.percUpp) + \
                 pcr.max(0.,self.infiltration - \
                 (self.parameters.storCapUpp-self.storUpp))                 # original Rens's line:
                                                                            #   P1_L[TYPE] = KTHVERT*Duration*timeslice();
                                                                            #   P1_L[TYPE] = if(THEFF1 > THEFF1_FC[TYPE],min(max(0,THEFF1-THEFF1_FC[TYPE])*SC1[TYPE],
                                                                            #                P1_L[TYPE]),P1_L[TYPE])+max(0,P0_L[TYPE]-(SC1[TYPE]-S1_L[TYPE]));
            # - percolation from storLow to storGroundwater
            self.percLow = pcr.min(self.kUnsatLow, pcr.sqrt(\
                             self.kUnsatLow*self.parameters.kUnsatAtFieldCapLow))
                                                                            # original Rens's line:
                                                                            #    P2_L[TYPE] = min(KTHEFF2,sqrt(KTHEFF2*KTHEFF2_FC[TYPE]))*Duration*timeslice()
            
            # - capillary rise to storUpp from storLow
            self.capRiseUpp = \
             pcr.min(pcr.max(0.,\
                             self.parameters.effSatAtFieldCapUpp - \
                             self.effSatUpp)*self.parameters.storCapUpp,\
                            self.kThVertUppLow  * self.gradientUppLow)      # original Rens's line:
                                                                            #  CR1_L[TYPE] = min(max(0,THEFF1_FC[TYPE]-THEFF1)*SC1[TYPE],KTHVERT*GRAD*Duration*timeslice());

            # - capillary rise to storLow from storGroundwater (m)
            self.capRiseLow = 0.5*(self.satAreaFrac + capRiseFrac)*\
                                       pcr.min((1.-self.effSatLow)*\
                                      pcr.sqrt(self.parameters.kSatLow* \
                                                   self.kUnsatLow),\
                       pcr.max(0.0,self.parameters.effSatAtFieldCapLow- \
                                                   self.effSatLow)*\
                                            self.parameters.storCapLow)     # original Rens's line:
                                                                            #  CR2_L[TYPE] = 0.5*(SATFRAC_L+CRFRAC)*min((1-THEFF2)*sqrt(KS2[TYPE]*KTHEFF2)*Duration*timeslice(),
                                                                            #                max(0,THEFF2_FC[TYPE]-THEFF2)*SC2[TYPE]);

            # - no capillary rise from non productive aquifer
            self.capRiseLow = pcr.ifthenelse(groundwater.productive_aquifer,\
                                             self.capRiseLow, 0.0)
            
            # - interflow (m)
            percToInterflow = self.parameters.percolationImp*(\
                                     self.percUpp+self.capRiseLow-\
                                    (self.percLow+self.capRiseUpp))
            self.interflow = pcr.max(\
                              self.parameters.interflowConcTime*percToInterflow  +\
              (pcr.scalar(1.)-self.parameters.interflowConcTime)*self.interflow, 0.0)
            
        if self.numberOfLayers == 3:

            # - percolation from storUpp000005 to storUpp005030 (m)
            self.percUpp000005 = self.kThVertUpp000005Upp005030 * 1.
            self.percUpp000005 = \
                 pcr.ifthenelse(     self.effSatUpp000005 > self.parameters.effSatAtFieldCapUpp000005, \
                 pcr.min(pcr.max(0., self.effSatUpp000005 - self.parameters.effSatAtFieldCapUpp000005)*self.parameters.storCapUpp000005, self.percUpp000005), self.percUpp000005) + \
                 pcr.max(0.,self.infiltration - \
                 (self.parameters.storCapUpp000005-self.storUpp000005))

            # - percolation from storUpp005030 to storLow030150 (m)
            self.percUpp005030 = self.kThVertUpp005030Low030150 * 1.
            self.percUpp005030 = \
                 pcr.ifthenelse(     self.effSatUpp005030 > self.parameters.effSatAtFieldCapUpp005030, \
                 pcr.min(pcr.max(0., self.effSatUpp005030 - self.parameters.effSatAtFieldCapUpp005030)*self.parameters.storCapUpp005030, self.percUpp005030), self.percUpp005030) + \
                 pcr.max(0.,self.percUpp000005 - \
                 (self.parameters.storCapUpp005030-self.storUpp005030))

            # - percolation from storLow030150 to storGroundwater (m)
            self.percLow030150 = pcr.min(self.kUnsatLow030150,pcr.sqrt(\
                         self.parameters.kUnsatAtFieldCapLow030150*\
                                         self.kUnsatLow030150))

            # - capillary rise to storUpp000005 from storUpp005030 (m)
            self.capRiseUpp000005 = pcr.min(pcr.max(0.,\
                          self.parameters.effSatAtFieldCapUpp000005 - \
                                          self.effSatUpp000005)* \
                                   self.parameters.storCapUpp000005, \
                                self.kThVertUpp000005Upp005030* \
                               self.gradientUpp000005Upp005030)

            # - capillary rise to storUpp005030 from storLow030150 (m)
            self.capRiseUpp005030 = pcr.min(pcr.max(0.,\
                          self.parameters.effSatAtFieldCapUpp005030 - \
                                          self.effSatUpp005030)* \
                                   self.parameters.storCapUpp005030, \
                                self.kThVertUpp005030Low030150* \
                               self.gradientUpp005030Low030150)

            # - capillary rise to storLow030150 from storGroundwater (m)
            self.capRiseLow030150 = 0.5*(self.satAreaFrac + capRiseFrac)*\
                                 pcr.min((1.-self.effSatLow030150)*\
                                pcr.sqrt(self.parameters.kSatLow030150* \
                                             self.kUnsatLow030150),\
                 pcr.max(0.0,self.parameters.effSatAtFieldCapLow030150- \
                                             self.effSatLow030150)*\
                                      self.parameters.storCapLow030150)

            # - no capillary rise from non productive aquifer
            self.capRiseLow030150 = pcr.ifthenelse(groundwater.productive_aquifer,\
                                                   self.capRiseLow030150, 0.0)

            # - interflow (m)
            percToInterflow = self.parameters.percolationImp*(\
                                     self.percUpp005030+self.capRiseLow030150-\
                                    (self.percLow030150+self.capRiseUpp005030))
            self.interflow = pcr.max(\
                              self.parameters.interflowConcTime*percToInterflow  +\
              (pcr.scalar(1.)-self.parameters.interflowConcTime)*self.interflow, 0.0)


    def scaleAllFluxes(self, groundwater):

        # We re-scale all fluxes (based on available water).
        ########################################################################################################################################
        # 

        if self.numberOfLayers == 2:

            # scale fluxes (for Upp)
            ADJUST = self.actBareSoilEvap + self.actTranspiUpp + self.percUpp
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp + \
                                              self.infiltration) / ADJUST),0.)
            ADJUST = pcr.cover(ADJUST, 0.0)
            self.actBareSoilEvap = ADJUST*self.actBareSoilEvap
            self.percUpp         = ADJUST*self.percUpp                      
            self.actTranspiUpp   = ADJUST*self.actTranspiUpp                
                                                                            # original Rens's line:
                                                                            # ADJUST = ES_a[TYPE]+T_a1[TYPE]+P1_L[TYPE];
                                                                            # ADJUST = if(ADJUST>0,min(1,(max(0,S1_L[TYPE]+P0_L[TYPE]))/ADJUST),0);
                                                                            # ES_a[TYPE] = ADJUST*ES_a[TYPE];
                                                                            # T_a1[TYPE] = ADJUST*T_a1[TYPE];
                                                                            # P1_L[TYPE] = ADJUST*P1_L[TYPE];

            # scale fluxes (for Low)
            ADJUST = self.actTranspiLow + self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow + \
                                              self.percUpp)/ADJUST),0.)
            ADJUST = pcr.cover(ADJUST, 0.0)
            self.percLow       = ADJUST*self.percLow
            self.actTranspiLow = ADJUST*self.actTranspiLow
            self.interflow     = ADJUST*self.interflow                      
                                                                            # original Rens's line:
                                                                            # ADJUST = T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE];
                                                                            # ADJUST = if(ADJUST>0,min(1,max(S2_L[TYPE]+P1_L[TYPE],0)/ADJUST),0);
                                                                            # T_a2[TYPE] = ADJUST*T_a2[TYPE];
                                                                            # P2_L[TYPE] = ADJUST*P2_L[TYPE];
                                                                            # Q2_L[TYPE] = ADJUST*Q2_L[TYPE];

            # capillary rise to storLow is limited to available storGroundwater 
            # 
            # The following is for a conservative approach (used by Rens)
            #  - using fracVegCover as "safectyFactor".                     # EHS (02 Sep 2013): NOT NEEDED
            #~ self.capRiseLow = \
                             #~ pcr.min(self.fracVegCover*\
                             #~ groundwater.storGroundwater,\
                             #~ self.capRiseLow)                            # CR2_L[TYPE]= min(VEGFRAC[TYPE]*S3,CR2_L[TYPE])
            # 
            #~ #  - without fracVegCover (without safetyFactor)
            #~ self.capRiseLow = pcr.max(0.,\
                              #~ pcr.min(\
                              #~ groundwater.storGroundwater,self.capRiseLow))  # This line is not necessary. 
            # 
            # also limited with reducedCapRise 
            #
            self.capRiseLow = pcr.max(0.,\
                              pcr.min(\
                              pcr.max(0.,\
                              groundwater.storGroundwater-self.reducedCapRise),self.capRiseLow))

            # capillary rise to storUpp is limited to available storLow
            #
            estimateStorLowBeforeCapRise = pcr.max(0,self.storLow + self.percUpp - \
                                              (self.actTranspiLow + self.percLow + self.interflow ))
            self.capRiseUpp = pcr.min(\
                              estimateStorLowBeforeCapRise,self.capRiseUpp)     # original Rens's line: 
                                                                                #  CR1_L[TYPE] = min(max(0,S2_L[TYPE]+P1_L[TYPE]-(T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE])),CR1_L[TYPE])

        if self.numberOfLayers == 3:

            # scale fluxes (for Upp000005)
            ADJUST = self.actBareSoilEvap + self.actTranspiUpp000005 + self.percUpp000005
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp000005 + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap     = ADJUST*self.actBareSoilEvap
            self.percUpp000005       = ADJUST*self.percUpp000005
            self.actTranspiUpp000005 = ADJUST*self.actTranspiUpp000005
            
            # scale fluxes (for Upp005030)
            ADJUST = self.actTranspiUpp005030 + self.percUpp005030
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp005030 + \
                                              self.percUpp000005)/ ADJUST),0.)
            self.percUpp005030       = ADJUST*self.percUpp005030
            self.actTranspiUpp005030 = ADJUST*self.actTranspiUpp005030

            # scale fluxes (for Low030150)
            ADJUST = self.actTranspiLow030150 + self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow030150 + \
                                              self.percUpp005030)/ADJUST),0.)
            self.percLow030150       = ADJUST*self.percLow030150
            self.actTranspiLow030150 = ADJUST*self.actTranspiLow030150
            self.interflow           = ADJUST*self.interflow   

            # capillary rise to storLow is limited to available storGroundwater 
            # and also limited with reducedCapRise 
            #
            self.capRiseLow030150 = pcr.max(0.,\
                                    pcr.min(\
                                    pcr.max(0.,\
                                    groundwater.storGroundwater-\
                                    self.reducedCapRise),\
                                    self.capRiseLow030150))

            # capillary rise to storUpp005030 is limited to available storLow030150
            #
            estimateStorLow030150BeforeCapRise = pcr.max(0,self.storLow030150 + self.percUpp005030 - \
                                                    (self.actTranspiLow030150 + self.percLow030150 + self.interflow ))
            self.capRiseUpp005030 = pcr.min(\
                                    estimateStorLow030150BeforeCapRise,self.capRiseUpp005030)

            # capillary rise to storUpp000005 is limited to available storUpp005030
            #
            estimateStorUpp005030BeforeCapRise = pcr.max(0,self.storUpp005030 + self.percUpp000005 - \
                                                    (self.actTranspiUpp005030 + self.percUpp005030))
            self.capRiseUpp000005 = pcr.min(\
                                    estimateStorUpp005030BeforeCapRise,self.capRiseUpp000005)


    def scaleAllFluxesForIrrigatedAreas(self, groundwater):

        # for irrigation areas: interflow will be minimized                                                                                                                                        
        if self.name.startswith('irr'): self.interflow = 0.
        
        #~ # deep percolation should consider losses during application in non paddy areas                                                                                                                                        
        #~ if self.name == 'irrNonPaddy':
            #~ startingCropKC = 0.00
            #~ maxADJUST = 100.
            #~ if self.numberOfLayers == 2:
                #~ minimum_deep_percolation = pcr.min(self.potential_irrigation_loss, self.storLow)
                #~ deep_percolation = pcr.max(minimum_deep_percolation, \
                                           #~ self.percLow + self.interflow)
                #~ ADJUST = self.percLow + self.interflow
                #~ ADJUST = pcr.ifthenelse(ADJUST > 0., \
                         #~ pcr.min(maxADJUST,pcr.max(0.0, deep_percolation)/ADJUST),0.)
                #~ ADJUST = pcr.ifthenelse(self.cropKC > startingCropKC, ADJUST, 1.)
                #~ self.percLow   = ADJUST*self.percLow
                #~ self.interflow = ADJUST*self.interflow                      
            #~ if self.numberOfLayers == 3:
                #~ minimum_deep_percolation = pcr.min(self.potential_irrigation_loss, self.storLow030150)
                #~ deep_percolation = pcr.max(minimum_deep_percolation, \
                                           #~ self.percLow030150 + self.interflow)
                #~ ADJUST = self.percLow030150 + self.interflow
                #~ ADJUST = pcr.ifthenelse(ADJUST > 0., \
                         #~ pcr.min(maxADJUST,pcr.max(0.0, deep_percolation)/ADJUST),0.)
                #~ ADJUST = pcr.ifthenelse(self.cropKC > startingCropKC, ADJUST, 1.)
                #~ self.percLow030150 = ADJUST*self.percLow030150
                #~ self.interflow     = ADJUST*self.interflow                      

        #~ # idea on 9 May 2015
        #~ # deep percolation should consider losses during application in non paddy areas 
        #~ if self.name == "irrNonPaddy":
            #~ startingKC = 0.20   # starting crop coefficient indicate the growing season
            #~ if self.numberOfLayers == 2:
                #~ deep_percolation_loss = self.percLow
                #~ deep_percolation_loss = pcr.max(deep_percolation_loss, \
                                        #~ pcr.min(self.readAvlWater, self.storLow) * ((1./self.irrigationEfficiencyUsed) - 1.))
                #~ self.percLow = pcr.ifthenelse(self.cropKC > startingKC, deep_percolation_loss, \
                               #~ pcr.ifthenelse(self.cropKC < self.prevCropKC, self.percLow, deep_percolation_loss))
            #~ if self.numberOfLayers == 3:
                #~ deep_percolation_loss = self.percLow030150
                #~ deep_percolation_loss = pcr.max(deep_percolation_loss, \
                                        #~ pcr.min(self.readAvlWater, self.storLow030150) * ((1./self.irrigationEfficiencyUsed) - 1.))
                #~ self.percLow030150 = pcr.ifthenelse(self.cropKC > startingKC, deep_percolation_loss, \
                                     #~ pcr.ifthenelse(self.cropKC < self.prevCropKC, self.percLow030150, deep_percolation_loss))

        # idea on 16 June 2015
        # deep percolation should consider irrigation application losses 
        if self.name.startswith('irr'):
            
            startingKC = 0.20   # starting crop coefficient indicate the growing season
            
            if self.numberOfLayers == 2:
                deep_percolation_loss = self.percLow
                deep_percolation_loss = pcr.max(deep_percolation_loss, \
                                        pcr.max(0.0, self.storLow) * ((1./self.irrigationEfficiencyUsed) - 1.))
                self.percLow = pcr.ifthenelse(self.cropKC > startingKC, deep_percolation_loss, self.percLow)
            
            if self.numberOfLayers == 3:
                deep_percolation_loss = self.percLow030150
                deep_percolation_loss = pcr.max(deep_percolation_loss, \
                                        pcr.max(0.0, self.storLow030150) * ((1./self.irrigationEfficiencyUsed) - 1.))
                self.percLow030150 = pcr.ifthenelse(self.cropKC > startingKC, deep_percolation_loss, self.percLow030150)


        # idea on 24 June 2015
        # the total bare soil evaporation and deep percolation losses should be limited by irrigation efficiency and total transpiration 
        #~ if self.name.startswith('irr'):
            #~ 
            #~ # starting crop coefficient indicate the growing season
            #~ startingKC = 0.20   
#~ 
            #~ # estimate of total transpiration (unit: m)
            #~ if self.numberOfLayers == 2: total_transpiration = self.actTranspiUpp + self.actTranspiLow
            #~ if self.numberOfLayers == 3: total_transpiration = self.actTranspiUpp000005 +\
                                                               #~ self.actTranspiUpp005030 +\
                                                               #~ self.actTranspiLow030150
            #~ 
            #~ # potential/maximum irrigation loss (unit: m)
            #~ potential_irrigation_loss_from_soil = total_transpiration * ((1./self.irrigationEfficiencyUsed) - 1.)
            #~ # - some has evaporated through openWaterEvap (from paddy fields)
            #~ potential_irrigation_loss_from_soil = pcr.max(0.0, potential_irrigation_loss_from_soil - self.openWaterEvap)
            #~ 
            #~ # deep percolation loss as it is estimated (no reduction/changes)
            #~ if self.numberOfLayers == 2: deep_percolation_loss = self.percLow
            #~ if self.numberOfLayers == 3: deep_percolation_loss = self.percLow030150
#~ 
            #~ # bare soil evaporation (unit: m), limited by the (remaining) potential_irrigation_loss_from_soil and the estimate of deep percolation 
            #~ self.actBareSoilEvap = pcr.ifthenelse(self.cropKC > startingKC, \
                                   #~ pcr.min(self.actBareSoilEvap, \
                                   #~ pcr.max(0.0, potential_irrigation_loss_from_soil - deep_percolation_loss)), self.actBareSoilEvap)


        #~ # idea on 25 June 2015
        #~ # the minimum deep percolation losses is determined by irrigation efficiency and total transpiration 
        #~ if self.name.startswith('irr'):
            #~ 
            #~ # starting crop coefficient indicate the growing season
            #~ startingKC = 0.20   
#~ 
            #~ # estimate of total transpiration (unit: m)
            #~ if self.numberOfLayers == 2: total_transpiration = self.actTranspiUpp + self.actTranspiLow
            #~ if self.numberOfLayers == 3: total_transpiration = self.actTranspiUpp000005 +\
                                                               #~ self.actTranspiUpp005030 +\
                                                               #~ self.actTranspiLow030150
            #~ 
            #~ # potential/maximum irrigation loss (unit: m)
            #~ potential_irrigation_loss_from_soil = total_transpiration * ((1./self.irrigationEfficiencyUsed) - 1.)
            #~ # - some has evaporated through openWaterEvap (from paddy fields)
            #~ potential_irrigation_loss_from_soil = pcr.max(0.0, potential_irrigation_loss_from_soil - self.openWaterEvap)
            #~ 
            #~ # bare soil evaporation (unit: m), limited by the potential_irrigation_loss_from_soil 
            #~ self.actBareSoilEvap = pcr.ifthenelse(self.cropKC > startingKC, \
                                   #~ pcr.min(self.actBareSoilEvap, potential_irrigation_loss_from_soil), self.actBareSoilEvap)
#~ 
            #~ # minimum deep percolation loss is the (remaining) potential_irrigation_loss_from_soil
            #~ deep_percolation_loss = pcr.max(potential_irrigation_loss_from_soil - self.actBareSoilEvap)
            #~ if self.numberOfLayers == 2:
                #~ deep_percolation_loss = pcr.min(deep_percolation_loss, \
                                        #~ pcr.max(0.0, self.storLow) * ((1./self.irrigationEfficiencyUsed) - 1.))
                #~ self.percLow = pcr.ifthenelse(self.cropKC > startingKC, pcr.max(deep_percolation_loss, self.percLow), self.percLow)
            #~ if self.numberOfLayers == 3:
                #~ deep_percolation_loss = pcr.min(deep_percolation_loss, \
                                        #~ pcr.max(0.0, self.storLow030150) * ((1./self.irrigationEfficiencyUsed) - 1.))
                #~ self.percLow030150 = pcr.ifthenelse(self.cropKC > startingKC, pcr.max(deep_percolation_loss, self.percLow030150), self.percLow030150)

        
        # scale all fluxes based on available water
        # - alternative 1:
        self.scaleAllFluxes(groundwater)
        #~ # - alternative 2:
        #~ self.scaleAllFluxesOptimizeEvaporationTranspiration(groundwater)

    def scaleAllFluxesOptimizeEvaporationTranspiration(self, groundwater):

        # We re-scale all fluxes (based on available water).
        # - in irrigated areas, evaporation fluxes are priority
        # - percolation and interfflow losses depend on the remaining water
        ########################################################################################################################################

        # remaining total energy for evaporation fluxes:
        remainingPotET = self.potBareSoilEvap + self.potTranspiration
        
        # scaling all fluxes based on available water
        
        if self.numberOfLayers == 2:

            # scale fluxes (for Upp)
            # - potential transpiration will be used to boost the transpiration process
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap = ADJUST*self.actBareSoilEvap
            self.actTranspiUpp   = ADJUST*self.potTranspiration                
            #
            # - allowing more transpiration
            remainingPotET = pcr.max(0.0, remainingPotET -\
                                         (self.actBareSoilEvap + self.actTranspiUpp))
            extraTranspiration   = pcr.min(remainingPotET,\
                                   pcr.max(0.0, self.storUpp + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp))
            self.actTranspiUpp  += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)                                   
            #
            # - percolation fluxes depend on the remaining water
            self.percUpp         = pcr.min(self.percUpp,\
                                   pcr.max(0.0, self.storUpp + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp))
            
            # scale fluxes (for Low)
            # - remaining potential evaporation will be used to boost the transpiration process
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow + \
                                              self.percUpp)/ADJUST),0.)
            self.actTranspiLow = ADJUST*remainingPotET
            # - percolation and interflow fluxes depend on the remaining water
            ADJUST = self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow + \
                                              self.percUpp - self.actTranspiLow)/ADJUST),0.)
            self.percLow       = ADJUST*self.percLow
            self.interflow     = ADJUST*self.interflow                      

            # capillary rise to storLow is limited to available storGroundwater 
            # - also limited with reducedCapRise 
            self.capRiseLow = pcr.max(0.,\
                              pcr.min(\
                              pcr.max(0.,\
                              groundwater.storGroundwater-self.reducedCapRise),self.capRiseLow))

            # capillary rise to storUpp is limited to available storLow
            estimateStorLowBeforeCapRise = pcr.max(0,self.storLow + self.percUpp - \
                                              (self.actTranspiLow + self.percLow + self.interflow ))
            self.capRiseUpp = pcr.min(\
                              estimateStorLowBeforeCapRise,self.capRiseUpp)     # original Rens's line: 
                                                                                #  CR1_L[TYPE] = min(max(0,S2_L[TYPE]+P1_L[TYPE]-(T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE])),CR1_L[TYPE])

        if self.numberOfLayers == 3:

            # scale fluxes (for Upp000005)
            # - potential transpiration will be used to boost the transpiration process
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp000005 + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap     = ADJUST*self.actBareSoilEvap
            self.actTranspiUpp000005 = ADJUST*self.potTranspiration
            #
            # - allowing more transpiration
            remainingPotET = pcr.max(0.0, remainingPotET -\
                                         (self.actBareSoilEvap + self.actTranspiUpp000005))
            extraTranspiration   = pcr.min(remainingPotET,\
                                   pcr.max(0.0, self.storUpp000005 + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp000005))
            self.actTranspiUpp000005 += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)                                   
            #
            # - percolation fluxes depend on the remaining water
            self.percUpp000005   = pcr.min(self.percUpp000005,\
                                   pcr.max(0.0, self.storUpp000005 + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp000005))

            # scale fluxes (for Upp005030)
            # - remaining potential evaporation will be used to boost the transpiration process
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp005030 + \
                                              self.percUpp000005)/ADJUST),0.)
            self.actTranspiUpp005030 = ADJUST*remainingPotET
            # - percolation fluxes depend on the remaining water
            self.percUpp005030       = pcr.min(self.percUpp005030,\
                                       pcr.max(0.0, self.storUpp005030 + self.percUpp000005 - \
                                                    self.actTranspiUpp005030))

            # scale fluxes (for Low030150)
            # - remaining potential evaporation will be used to boost the transpiration process
            remainingPotET = pcr.max(0.0, remainingPotET - self.actTranspiUpp005030)
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow030150 + \
                                              self.percUpp005030)/ADJUST),0.)
            self.actTranspiLow030150 = ADJUST*remainingPotET
            # - percolation and interflow fluxes depend on the remaining water
            ADJUST = self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow030150 + \
                                              self.percUpp005030 - self.actTranspiLow030150)/ADJUST),0.)
            self.percLow030150       = ADJUST*self.percLow030150
            self.interflow           = ADJUST*self.interflow   

            # capillary rise to storLow is limited to available storGroundwater 
            # - also limited with reducedCapRise 
            #
            self.capRiseLow030150 = pcr.max(0.,\
                                    pcr.min(\
                                    pcr.max(0.,\
                                    groundwater.storGroundwater-\
                                    self.reducedCapRise),\
                                    self.capRiseLow030150))

            # capillary rise to storUpp005030 is limited to available storLow030150
            #
            estimateStorLow030150BeforeCapRise = pcr.max(0,self.storLow030150 + self.percUpp005030 - \
                                                    (self.actTranspiLow030150 + self.percLow030150 + self.interflow ))
            self.capRiseUpp005030 = pcr.min(\
                                    estimateStorLow030150BeforeCapRise,self.capRiseUpp005030)

            # capillary rise to storUpp000005 is limited to available storUpp005030
            #
            estimateStorUpp005030BeforeCapRise = pcr.max(0,self.storUpp005030 + self.percUpp000005 - \
                                                    (self.actTranspiUpp005030 + self.percUpp005030))
            self.capRiseUpp000005 = pcr.min(\
                                    estimateStorUpp005030BeforeCapRise,self.capRiseUpp000005)

    def scaleAllFluxesOptimizeEvaporationVersion27April2014(self, groundwater):

        # We re-scale all fluxes (based on available water).
        # - in irrigated areas, evaporation fluxes are priority
        # - percolation and interfflow losses depend on the remaining water
        ########################################################################################################################################

        # remaining total energy for evaporation fluxes:
        remainingPotET = self.potBareSoilEvap + self.potTranspiration
        
        # for irrigation areas: interflow will be minimized                                                                                                                                        
        if self.name.startswith('irr'): self.interflow = 0.                                                                                                                                        

        # an idea: deep percolation should consider losses during application in non paddy areas 
        #
        if self.name == 'irrNonPaddy':
            startingCropKC = 0.75
            minimum_deep_percolation = pcr.min(self.infiltration, self.potential_irrigation_loss)
            maxADJUST = 2.0
            #
            if self.numberOfLayers == 2:
                deep_percolation = pcr.max(minimum_deep_percolation, \
                                           self.percLow + self.interflow)
                ADJUST = self.percLow + self.interflow
                ADJUST = pcr.ifthenelse(ADJUST > 0., \
                         pcr.min(maxADJUST,pcr.max(0.0, deep_percolation)/ADJUST),0.)
                ADJUST = pcr.ifthenelse(self.cropKC > startingCropKC, ADJUST, 1.)
                self.percLow   = ADJUST*self.percLow
                self.interflow = ADJUST*self.interflow                      
            if self.numberOfLayers == 3:
                deep_percolation = pcr.max(minimum_deep_percolation, \
                                           self.percLow030150 + self.interflow)
                ADJUST = self.percLow030150 + self.interflow
                ADJUST = pcr.ifthenelse(ADJUST > 0., \
                         pcr.min(maxADJUST,pcr.max(0.0, deep_percolation)/ADJUST),0.)
                ADJUST = pcr.ifthenelse(self.cropKC > startingCropKC, ADJUST, 1.)
                self.percLow030150 = ADJUST*self.percLow030150
                self.interflow     = ADJUST*self.interflow                      

        
        
        # scaling all fluxes based on available water
        
        if self.numberOfLayers == 2:

            # scale fluxes (for Upp)
            # - potential transpiration will be used to boost the transpiration process
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap = ADJUST*self.actBareSoilEvap
            self.actTranspiUpp   = ADJUST*self.potTranspiration                
            #
            # - allowing more transpiration
            remainingPotET = pcr.max(0.0, remainingPotET -\
                                         (self.actBareSoilEvap + self.actTranspiUpp))
            extraTranspiration   = pcr.min(remainingPotET,\
                                   pcr.max(0.0, self.storUpp + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp))
            self.actTranspiUpp  += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)                                   
            #
            # - percolation fluxes depend on the remaining water
            self.percUpp         = pcr.min(self.percUpp,\
                                   pcr.max(0.0, self.storUpp + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp))
            
            # scale fluxes (for Low)
            # - remaining potential evaporation will be used to boost the transpiration process
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow + \
                                              self.percUpp)/ADJUST),0.)
            self.actTranspiLow = ADJUST*remainingPotET
            # - percolation and interflow fluxes depend on the remaining water
            ADJUST = self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow + \
                                              self.percUpp - self.actTranspiLow)/ADJUST),0.)
            self.percLow       = ADJUST*self.percLow
            self.interflow     = ADJUST*self.interflow                      

            # capillary rise to storLow is limited to available storGroundwater 
            # - also limited with reducedCapRise 
            self.capRiseLow = pcr.max(0.,\
                              pcr.min(\
                              pcr.max(0.,\
                              groundwater.storGroundwater-self.reducedCapRise),self.capRiseLow))

            # capillary rise to storUpp is limited to available storLow
            estimateStorLowBeforeCapRise = pcr.max(0,self.storLow + self.percUpp - \
                                              (self.actTranspiLow + self.percLow + self.interflow ))
            self.capRiseUpp = pcr.min(\
                              estimateStorLowBeforeCapRise,self.capRiseUpp)     # original Rens's line: 
                                                                                #  CR1_L[TYPE] = min(max(0,S2_L[TYPE]+P1_L[TYPE]-(T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE])),CR1_L[TYPE])

        if self.numberOfLayers == 3:

            # scale fluxes (for Upp000005)
            # - potential transpiration will be used to boost the transpiration process
            ADJUST = self.actBareSoilEvap + self.potTranspiration
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp000005 + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap     = ADJUST*self.actBareSoilEvap
            self.actTranspiUpp000005 = ADJUST*self.potTranspiration
            #
            # - allowing more transpiration
            remainingPotET = pcr.max(0.0, remainingPotET -\
                                         (self.actBareSoilEvap + self.actTranspiUpp000005))
            extraTranspiration   = pcr.min(remainingPotET,\
                                   pcr.max(0.0, self.storUpp000005 + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp000005))
            self.actTranspiUpp000005 += extraTranspiration
            remainingPotET = pcr.max(0.0, remainingPotET - extraTranspiration)                                   
            #
            # - percolation fluxes depend on the remaining water
            self.percUpp000005   = pcr.min(self.percUpp000005,\
                                   pcr.max(0.0, self.storUpp000005 + self.infiltration - \
                                                self.actBareSoilEvap - \
                                                self.actTranspiUpp000005))

            # scale fluxes (for Upp005030)
            # - remaining potential evaporation will be used to boost the transpiration process
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp005030 + \
                                              self.percUpp000005)/ADJUST),0.)
            self.actTranspiUpp005030 = ADJUST*remainingPotET
            # - percolation fluxes depend on the remaining water
            self.percUpp005030       = pcr.min(self.percUpp005030,\
                                       pcr.max(0.0, self.storUpp005030 + self.percUpp000005 - \
                                                    self.actTranspiUpp005030))

            # scale fluxes (for Low030150)
            # - remaining potential evaporation will be used to boost the transpiration process
            remainingPotET = pcr.max(0.0, remainingPotET - self.actTranspiUpp005030)
            ADJUST = remainingPotET
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow030150 + \
                                              self.percUpp005030)/ADJUST),0.)
            self.actTranspiLow030150 = ADJUST*remainingPotET
            # - percolation and interflow fluxes depend on the remaining water
            ADJUST = self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow030150 + \
                                              self.percUpp005030 - self.actTranspiLow030150)/ADJUST),0.)
            self.percLow030150       = ADJUST*self.percLow030150
            self.interflow           = ADJUST*self.interflow   

            # capillary rise to storLow is limited to available storGroundwater 
            # - also limited with reducedCapRise 
            #
            self.capRiseLow030150 = pcr.max(0.,\
                                    pcr.min(\
                                    pcr.max(0.,\
                                    groundwater.storGroundwater-\
                                    self.reducedCapRise),\
                                    self.capRiseLow030150))

            # capillary rise to storUpp005030 is limited to available storLow030150
            #
            estimateStorLow030150BeforeCapRise = pcr.max(0,self.storLow030150 + self.percUpp005030 - \
                                                    (self.actTranspiLow030150 + self.percLow030150 + self.interflow ))
            self.capRiseUpp005030 = pcr.min(\
                                    estimateStorLow030150BeforeCapRise,self.capRiseUpp005030)

            # capillary rise to storUpp000005 is limited to available storUpp005030
            #
            estimateStorUpp005030BeforeCapRise = pcr.max(0,self.storUpp005030 + self.percUpp000005 - \
                                                    (self.actTranspiUpp005030 + self.percUpp005030))
            self.capRiseUpp000005 = pcr.min(\
                                    estimateStorUpp005030BeforeCapRise,self.capRiseUpp000005)

    def updateSoilStates(self):

        # We give new states and make sure that no storage capacities will be exceeded.
        #################################################################################
        
        if self.numberOfLayers == 2:
            
            # update storLow after the following fluxes: 
            # + percUpp
            # + capRiseLow
            # - percLow
            # - interflow
            # - actTranspiLow
            # - capRiseUpp
            #
            self.storLow = pcr.max(0., self.storLow + \
                                       self.percUpp + \
                                       self.capRiseLow - \
                       (self.percLow + self.interflow + \
                                       self.actTranspiLow +\
                                       self.capRiseUpp))                    # S2_L[TYPE]= max(0,S2_L[TYPE]+P1_L[TYPE]+CR2_L[TYPE]-
                                                                            #             (P2_L[TYPE]+Q2_L[TYPE]+CR1_L[TYPE]+T_a2[TYPE]));          
            #
            # If necessary, reduce percolation input:
            percUpp      = self.percUpp
            
            if self.allowNegativePercolation:
                # this is as defined in the original oldcalc script of Rens 
                self.percUpp = percUpp - \
                                 pcr.max(0.,self.storLow - \
                                 self.parameters.storCapLow)                
                                                                            # Rens's line: P1_L[TYPE] = P1_L[TYPE]-max(0,S2_L[TYPE]-SC2[TYPE]);
                                                                            # PS: In the original Rens's code, P1 can be negative.
            else:                                                                 
                # alternative, proposed by Edwin: avoid negative percolation
                self.percUpp = pcr.max(0., percUpp - \
                               pcr.max(0.,self.storLow - \
                                     self.parameters.storCapLow))                    
                self.storLow = self.storLow -  percUpp + \
                                          self.percUpp     
                # If necessary, reduce capRise input:
                capRiseLow      = self.capRiseLow
                self.capRiseLow = pcr.max(0.,capRiseLow - \
                                  pcr.max(0.,self.storLow - \
                                           self.parameters.storCapLow))
                self.storLow    = self.storLow - capRiseLow + \
                                            self.capRiseLow      
                # If necessary, increase interflow outflow:
                addInterflow          = pcr.max(0.,\
                            self.storLow - self.parameters.storCapLow)
                self.interflow       += addInterflow
                self.storLow         -= addInterflow      
                #
                self.storLow = pcr.min(self.storLow, self.parameters.storCapLow) 
        
            #
            # update storUpp after the following fluxes: 
            # + infiltration
            # + capRiseUpp
            # - percUpp
            # - actTranspiUpp
            # - actBareSoilEvap
            #
            self.storUpp = pcr.max(0.,self.storUpp + \
                                      self.infiltration + \
                                      self.capRiseUpp - \
                                     (self.percUpp + \
                 self.actTranspiUpp + self.actBareSoilEvap))                # Rens's line:  S1_L[TYPE]= max(0,S1_L[TYPE]+P0_L[TYPE]+CR1_L[TYPE]-
                                                                            #              (P1_L[TYPE]+T_a1[TYPE]+ES_a[TYPE])); #*
            #
            # any excess above storCapUpp is handed to topWaterLayer
            self.satExcess = pcr.max(0.,self.storUpp - \
                               self.parameters.storCapUpp)									
            self.topWaterLayer =  self.topWaterLayer + self.satExcess
        
            # any excess above minTopWaterLayer is released as directRunoff                               
            self.directRunoff  = self.directRunoff + \
                                 pcr.max(0.,self.topWaterLayer - self.minTopWaterLayer)
        
            # make sure that storage capacities are not exceeded
            self.topWaterLayer = pcr.min( self.topWaterLayer , \
                                          self.minTopWaterLayer)
            self.storUpp       = pcr.min(self.storUpp,\
                                 self.parameters.storCapUpp)
            self.storLow       = pcr.min(self.storLow,\
                                 self.parameters.storCapLow) 
        
            # total actual evaporation + transpiration
            self.actualET += self.actBareSoilEvap + \
                             self.openWaterEvap   + \
                             self.actTranspiUpp + \
                             self.actTranspiLow
            
            # total actual transpiration
            self.actTranspiTotal = self.actTranspiUpp + \
                                   self.actTranspiLow
            
            # net percolation between upperSoilStores (positive indicating downward direction)
            self.netPercUpp = self.percUpp - self.capRiseUpp

            # groundwater recharge (positive indicating downward direction)
            self.gwRecharge = self.percLow - self.capRiseLow
        
            # the following variables introduced for the comparison with threeLayer model output                        
            self.storUppTotal       = self.storUpp
            self.storLowTotal       = self.storLow
            self.actTranspiUppTotal = self.actTranspiUpp
            self.actTranspiLowTotal = self.actTranspiLow
            self.interflowTotal     = self.interflow

        if self.numberOfLayers == 3:
            
            # update storLow030150 after the following fluxes: 
            # + percUpp005030
            # + capRiseLow030150
            # - percLow030150
            # - interflow
            # - actTranspiLow030150
            # - capRiseUpp005030
            #
            self.storLow030150 = pcr.max(0., self.storLow030150 + \
                                             self.percUpp005030 + \
                                          self.capRiseLow030150 - \
                           (self.percLow030150 + self.interflow + \
                                       self.actTranspiLow030150 +\
                                          self.capRiseUpp005030))          
            #
            # If necessary, reduce percolation input:
            percUpp005030      = self.percUpp005030
            self.percUpp005030 = pcr.max(0., percUpp005030 - \
                             pcr.max(0.,self.storLow030150 - \
                               self.parameters.storCapLow030150))                    
            self.storLow030150 =        self.storLow030150 - \
                                             percUpp005030 + \
                                        self.percUpp005030     
            #
            # If necessary, reduce capRise input:
            capRiseLow030150      = self.capRiseLow030150
            self.capRiseLow030150 = pcr.max(0.,capRiseLow030150 - \
                                  pcr.max(0.,self.storLow030150 - \
                                    self.parameters.storCapLow030150))
            self.storLow030150    =          self.storLow030150 - \
                                               capRiseLow030150 + \
                                          self.capRiseLow030150
            #
            # If necessary, increase interflow outflow:
            addInterflow          = pcr.max(0.,\
                                    self.storLow030150 - self.parameters.storCapLow030150)
            self.interflow       += addInterflow
            self.storLow030150   -= addInterflow      
        
            self.storLow030150 = pcr.min(self.storLow030150,\
                                 self.parameters.storCapLow030150) 
        
            # update storUpp005030 after the following fluxes: 
            # + percUpp000005
            # + capRiseUpp005030
            # - percUpp005030
            # - actTranspiUpp005030
            # - capRiseUpp000005
            #
            self.storUpp005030 = pcr.max(0., self.storUpp005030 + \
                                             self.percUpp000005 + \
                                          self.capRiseUpp005030 - \
                                            (self.percUpp005030 + \
                                       self.actTranspiUpp005030 + \
                                          self.capRiseUpp000005))          
            #
            # If necessary, reduce percolation input:
            percUpp000005      = self.percUpp000005
            self.percUpp000005 = pcr.max(0., percUpp000005 - \
                             pcr.max(0.,self.storUpp005030 - \
                               self.parameters.storCapUpp005030))                    
            self.storUpp005030 =        self.storUpp005030 - \
                                             percUpp000005 + \
                                        self.percUpp000005     
            #
            # If necessary, reduce capRise input:
            capRiseUpp005030      = self.capRiseUpp005030
            self.capRiseUpp005030 = pcr.max(0.,capRiseUpp005030 - \
                                  pcr.max(0.,self.storUpp005030 - \
                                    self.parameters.storCapUpp005030))
            self.storUpp005030    =          self.storUpp005030 - \
                                               capRiseUpp005030 + \
                                          self.capRiseUpp005030
            #
            # If necessary, introduce interflow outflow:
            self.interflowUpp005030 = pcr.max(0.,\
                 self.storUpp005030 - self.parameters.storCapUpp005030)
            self.storUpp005030      = self.storUpp005030 - \
                                 self.interflowUpp005030      

            # update storUpp000005 after the following fluxes: 
            # + infiltration
            # + capRiseUpp000005
            # - percUpp000005
            # - actTranspiUpp000005
            # - actBareSoilEvap
            #
            self.storUpp000005 = pcr.max(0.,self.storUpp000005 + \
                                            self.infiltration  + \
                                         self.capRiseUpp000005 - \
                                           (self.percUpp000005 + \
                                      self.actTranspiUpp000005 + \
                                          self.actBareSoilEvap))
            #
            # any excess above storCapUpp is handed to topWaterLayer
            self.satExcess     = pcr.max(0.,self.storUpp000005 - \
                                   self.parameters.storCapUpp000005)									
            self.topWaterLayer = self.topWaterLayer + self.satExcess
        
            # any excess above minTopWaterLayer is released as directRunoff                               
            self.directRunoff  = self.directRunoff + \
                                 pcr.max(0.,self.topWaterLayer - \
                                            self.minTopWaterLayer)
        
            # make sure that storage capacities are not exceeded
            self.topWaterLayer = pcr.min( self.topWaterLayer , \
                                          self.minTopWaterLayer)
            self.storUpp000005 = pcr.min(self.storUpp000005,\
                                self.parameters.storCapUpp000005)
            self.storUpp005030 = pcr.min(self.storUpp005030,\
                                self.parameters.storCapUpp005030)
            self.storLow030150 = pcr.min(self.storLow030150,\
                                self.parameters.storCapLow030150)

            # total actual evaporation + transpiration
            self.actualET += self.actBareSoilEvap + \
                             self.openWaterEvap   + \
                             self.actTranspiUpp000005 + \
                             self.actTranspiUpp005030 + \
                             self.actTranspiLow030150
            
            # total actual transpiration
            self.actTranspiUppTotal = self.actTranspiUpp000005 + \
                                      self.actTranspiUpp005030

            # total actual transpiration
            self.actTranspiTotal = self.actTranspiUppTotal + \
                                   self.actTranspiLow030150
            
            # net percolation between upperSoilStores (positive indicating downward direction)
            self.netPercUpp000005 = self.percUpp000005 - self.capRiseUpp000005
            self.netPercUpp005030 = self.percUpp005030 - self.capRiseUpp005030

            # groundwater recharge
            self.gwRecharge = self.percLow030150 - self.capRiseLow030150
        
            # the following variables introduced for the comparison with twoLayer model output                        
            self.storUppTotal       = self.storUpp000005 + self.storUpp005030
            self.storLowTotal       = self.storLow030150
            self.actTranspiUppTotal = self.actTranspiUpp000005 + self.actTranspiUpp005030
            self.actTranspiLowTotal = self.actTranspiLow030150
            self.interflowTotal     = self.interflow + self.interflowUpp005030

        # variables / states that are defined the twoLayer and threeLayer model:
        ########################################################################
        
        # landSurfaceRunoff (needed for routing)                        
        self.landSurfaceRunoff = self.directRunoff + self.interflowTotal

    def upperSoilUpdate(self,meteo,groundwater,routing,\
                        capRiseFrac,\
                        nonIrrGrossDemandDict,swAbstractionFractionDict,\
                        currTimeStep,\
                        allocSegments,\
                        desalinationWaterUse,\
                        groundwater_pumping_region_ids,regionalAnnualGroundwaterAbstractionLimit):

        if self.debugWaterBalance:
            netLqWaterToSoil = self.netLqWaterToSoil # input            
            preTopWaterLayer = self.topWaterLayer
            if self.numberOfLayers == 2: 
                preStorUpp       = self.storUpp
                preStorLow       = self.storLow
            if self.numberOfLayers == 3: 
                preStorUpp000005 = self.storUpp000005
                preStorUpp005030 = self.storUpp005030
                preStorLow030150 = self.storLow030150
        
        # given soil storages, we can calculate several derived states, such as 
        # effective degree of saturation, unsaturated hydraulic conductivity, and 
        # readily available water within the root zone.
        self.getSoilStates()
        
        # calculate water demand (including partitioning to different source)
        self.calculateWaterDemand(nonIrrGrossDemandDict, swAbstractionFractionDict, \
                                  groundwater, routing, \
                                  allocSegments, currTimeStep,\
                                  desalinationWaterUse,\
                                  groundwater_pumping_region_ids,regionalAnnualGroundwaterAbstractionLimit)

        # calculate openWaterEvap: open water evaporation from the paddy field, 
        # and update topWaterLayer after openWaterEvap.  
        self.calculateOpenWaterEvap()
        
        # calculate directRunoff and infiltration, based on the improved Arno scheme (Hageman and Gates, 2003):
        # and update topWaterLayer (after directRunoff and infiltration).  
        self.calculateDirectRunoff()
        self.calculateInfiltration()

        # estimate bare soil evaporation and transpiration:
        if self.numberOfLayers == 2: 
            self.actBareSoilEvap, self.actTranspiUpp, self.actTranspiLow = \
                   self.estimateTranspirationAndBareSoilEvap()
        if self.numberOfLayers == 3: 
            self.actBareSoilEvap, self.actTranspiUpp000005, self.actTranspiUpp005030, self.actTranspiLow030150 = \
                   self.estimateTranspirationAndBareSoilEvap()
        
        # estimate percolation and capillary rise, as well as interflow
        self.estimateSoilFluxes(capRiseFrac,groundwater)

        # all fluxes are limited to available (source) storage
        if self.name.startswith('irr') and self.includeIrrigation:
            self.scaleAllFluxesForIrrigatedAreas(groundwater)
            #~ self.scaleAllFluxes(groundwater)
        else:    
            self.scaleAllFluxes(groundwater)

        # update all soil states (including get final/corrected fluxes) 
        self.updateSoilStates()

        # reporting irrigation transpiration deficit
        self.irrigationTranspirationDeficit = 0.0
        if self.name.startswith('irr'): self.irrigationTranspirationDeficit = pcr.max(0.0, self.potTranspiration - self.actTranspiTotal)
        
        if self.debugWaterBalance:
            #
            vos.waterBalanceCheck([netLqWaterToSoil    ,\
                                   self.irrGrossDemand ,\
                                   self.satExcess     ],\
                                  [self.directRunoff   ,\
                                   self.openWaterEvap  ,\
                                   self.infiltration]  ,\
                                  [  preTopWaterLayer ],\
                                  [self.topWaterLayer ] ,\
                                       'topWaterLayer',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
            
            if self.numberOfLayers == 2: 
                # 
                vos.waterBalanceCheck([self.infiltration,
                                       self.capRiseUpp],\
                                      [self.actTranspiUpp,
                                       self.percUpp,
                                       self.actBareSoilEvap,
                                       self.satExcess],\
                                      [  preStorUpp],\
                                      [self.storUpp],\
                                           'storUpp',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                # 
                vos.waterBalanceCheck([self.percUpp],\
                                      [self.actTranspiLow,
                                       self.gwRecharge,
                                       self.interflow,
                                       self.capRiseUpp],\
                                      [  preStorLow],\
                                      [self.storLow],\
                                           'storLow',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                #
                vos.waterBalanceCheck([self.infiltration,\
                                       self.capRiseLow],\
                                      [self.satExcess,
                                       self.interflow,
                                       self.percLow,
                                       self.actTranspiUpp,
                                       self.actTranspiLow,
                                       self.actBareSoilEvap],\
                                      [  preStorUpp,
                                         preStorLow],\
                                      [self.storUpp,
                                       self.storLow],\
                                      'entireSoilLayers',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-4)
                #
                vos.waterBalanceCheck([netLqWaterToSoil,
                                       self.capRiseLow,
                                       self.irrGrossDemand],\
                                      [self.directRunoff,
                                       self.interflow,
                                       self.percLow,
                                       self.actTranspiUpp,
                                       self.actTranspiLow,
                                       self.actBareSoilEvap,
                                       self.openWaterEvap],\
                                      [  preTopWaterLayer,
                                         preStorUpp,
                                         preStorLow],\
                                      [self.topWaterLayer,
                                       self.storUpp,
                                       self.storLow],\
                                      'allLayers',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-4)

            if self.numberOfLayers == 3: 
                vos.waterBalanceCheck([self.infiltration,
                                       self.capRiseUpp000005],\
                                      [self.actTranspiUpp000005,
                                       self.percUpp000005,
                                       self.actBareSoilEvap,
                                       self.satExcess],\
                                      [  preStorUpp000005],\
                                      [self.storUpp000005],\
                                           'storUpp000005',True,\
                                       currTimeStep.fulldate,threshold=1e-5)

                # 
                vos.waterBalanceCheck([self.percUpp000005,
                                       self.capRiseUpp005030],\
                                      [self.actTranspiUpp005030,
                                       self.percUpp005030,
                                       self.interflowUpp005030,
                                       self.capRiseUpp000005],\
                                      [  preStorUpp005030],\
                                      [self.storUpp005030],\
                                           'storUpp005030',True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                #
                vos.waterBalanceCheck([self.percUpp005030],\
                                      [self.actTranspiLow030150,
                                       self.gwRecharge,
                                       self.interflow,
                                       self.capRiseUpp005030],\
                                      [  preStorLow030150],\
                                      [self.storLow030150],\
                                           'storLow030150',True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                #
                vos.waterBalanceCheck([self.infiltration,\
                                       self.capRiseLow030150],\
                                      [self.satExcess,
                                       self.interflow,
                                       self.interflowUpp005030,
                                       self.percLow030150,
                                       self.actTranspiUpp000005,
                                       self.actTranspiUpp005030,
                                       self.actTranspiLow030150,
                                       self.actBareSoilEvap],\
                                      [  preStorUpp000005,
                                     preStorUpp005030,
                                     preStorLow030150],\
                                  [self.storUpp000005,
                                   self.storUpp005030,
                                   self.storLow030150],\
                                  'entireSoilLayers',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
                #
                vos.waterBalanceCheck([netLqWaterToSoil,
                                       self.capRiseLow030150,
                                       self.irrGrossDemand],\
                                      [self.directRunoff,
                                       self.interflow,
                                       self.interflowUpp005030,
                                       self.percLow030150,
                                       self.actTranspiUpp000005,
                                       self.actTranspiUpp005030,
                                       self.actTranspiLow030150,
                                   self.actBareSoilEvap,
                                   self.openWaterEvap],\
                                  [  preTopWaterLayer,
                                     preStorUpp000005,
                                     preStorUpp005030,
                                     preStorLow030150],\
                                  [self.topWaterLayer,
                                   self.storUpp000005,
                                   self.storUpp005030,
                                   self.storLow030150],\
                                  'allLayers',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
