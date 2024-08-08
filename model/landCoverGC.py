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

import re
import types

import netCDF4 as nc
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
from ncConverter import *
import waterUse as wu

class LandCover(object):

    def __init__(self,iniItems,nameOfSectionInIniFile,soil_and_topo_parameters,landmask,irrigationEfficiency,usingAllocSegments = False):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
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
        if "useMODFLOW" in list(iniItems.groundwaterOptions.keys()):
            if iniItems.groundwaterOptions["useMODFLOW"] == "True": self.limitAbstraction = True
        
        # calculate naturalised conditions
        self.naturalisedConditions = False
        if iniItems.landSurfaceOptions['naturalisedConditions'] == "True": self.naturalisedConditions = True
        
        # includeIrrigation
        self.includeIrrigation = False
        if iniItems.landSurfaceOptions['includeIrrigation'] == "True": self.includeIrrigation = True
        
        # irrigation efficiency map (dimensionless)
        self.irrigationEfficiency = irrigationEfficiency

        # interception module type
        # - "Original" is principally the same as defined in van Beek et al., 2014 (default)
        # - "Modified" is with a modification by Edwin Sutanudjaja: extending interception definition, using totalPotET for the available energy  
        self.interceptionModuleType = "Original"
        if "interceptionModuleType" in list(self.iniItemsLC.keys()):
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
        if self.interceptionModuleType == "Original" and "minInterceptCap" in list(self.iniItemsLC.keys()):
            msg = 'As the "Original" interceptionModuleType is used, the "minInterceptCap" value is ignored. The interception scope is only "canopy".'
            logger.warning(msg)
        if self.interceptionModuleType == "Modified":
            self.minInterceptCap = vos.readPCRmapClone(self.iniItemsLC['minInterceptCap'], self.cloneMap,
                                                       self.tmpDir, self.inputDir)
        
        # option to assume surface water as the first priority/alternative for water source (not used)
        self.surfaceWaterPiority = False
        
        # option to activate water balance check
        self.debugWaterBalance = True
        if self.iniItemsLC['debugWaterBalance'] == "False": self.debugWaterBalance = False

        # Improved Arno Scheme's method:
        # - In the "Original" work of van Beek et al., 2011 there is no "directRunoff reduction"
        # - However, later (20 April 2011), Rens van Beek introduce this reduction, particularly to maintain soil saturation. This is currently the "Default" method. 
        self.improvedArnoSchemeMethod = "Default"
        if "improvedArnoSchemeMethod" in list(iniItems.landSurfaceOptions.keys()):
            self.improvedArnoSchemeMethod = iniItems.landSurfaceOptions['improvedArnoSchemeMethod']
            if self.improvedArnoSchemeMethod == "Original": logger.warning("Using the old/original approach of Improved Arno Scheme. No reduction for directRunoff.")

        # In the original oldcalc script of Rens (2 layer model), the percolation percUpp (P1) can be negative
        # - To avoid this, Edwin changed few lines (see the method updateSoilStates)
        self.allowNegativePercolation = False
        if 'allowNegativePercolation' in list(self.iniItemsLC.keys()) and self.iniItemsLC['allowNegativePercolation'] == "True":
            msg  = 'Allowing negative values of percolation percUpp (P1), as done in the oldcalc script of PCR-GLOBWB 1.0. \n'
            msg += 'Note that this option is only relevant for the two layer soil model.'
            logger.warning(msg)
            self.allowNegativePercolation = True
        
        # In the original oldcalc script of Rens, there is a possibility that rootFraction/transpiration is only defined in the bottom layer, while no root in upper layer(s) 
        # - To avoid this, Edwin changed few lines (see the methods 'scaleRootFractionsFromTwoLayerSoilParameters' and 'estimateTranspirationAndBareSoilEvap')
        self.usingOriginalOldCalcRootTranspirationPartitioningMethod = False
        if 'usingOriginalOldCalcRootTranspirationPartitioningMethod' in list(self.iniItemsLC.keys()) and self.iniItemsLC['usingOriginalOldCalcRootTranspirationPartitioningMethod'] == "True":
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
        if 'annualChangesInLandCoverParameters' in list(iniItems.landSurfaceOptions.keys()):
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
        
        
        # get the names of cropCoefficient files:
        self.cropCoefficientNC = vos.getFullPath(self.iniItemsLC['cropCoefficientNC'], self.inputDir)
        
        # get the file names of interceptCap and coverFraction files:
        if 'interceptCapNC' in list(self.iniItemsLC.keys()) and 'coverFractionNC' in list(self.iniItemsLC.keys()):
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

        if 'coverFractionNC' in list(self.iniItemsLC.keys()) and self.iniItemsLC['coverFractionNC'] == "None": self.coverFractionNC = None 
        if 'interceptCapNC'  in list(self.iniItemsLC.keys()) and self.iniItemsLC['interceptCapNC' ] == "None": self.interceptCapNC  = None
        
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
        
        if var in list(self.iniItemsLC.keys()) or 'irrigationEfficiency' in list(self.iniItemsLC.keys()) and (self.iniItemsLC['name'].startswith('irr')):
            msg = "Irrigation efficiency is set based on the file defined in the landCoverOptions."
            
            if 'irrigationWaterEfficiency' in list(self.iniItemsLC.keys()):
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
            
            extrapolate = True
            if "noParameterExtrapolation" in iniItems.landSurfaceOptions.keys() and iniItems.landSurfaceOptions["noParameterExtrapolation"] == "True": extrapolate = False
            
            if extrapolate:
                 # extrapolate efficiency map:                                # TODO: Make a better extrapolation algorithm (considering cell size, etc.).
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
            if 'arnoBeta' not in list(self.iniItemsLC.keys()) and get_only_fracVegCover == False: self.iniItemsLC['arnoBeta'] = "None" 

            # - option one (top priority): using a pcraster file
            if self.iniItemsLC['arnoBeta'] != "None" and get_only_fracVegCover == False: 
                
                logger.debug("The parameter arnoBeta: "+str(self.iniItemsLC['arnoBeta']))
                lc_parameters['arnoBeta'] = vos.readPCRmapClone(self.iniItemsLC['arnoBeta'], self.cloneMap,\
                                                                self.tmpDir, self.inputDir)

            # - option two: included in the netcdf file
            if (lc_parameters['arnoBeta'] is None
                and landCoverPropertiesNC is not None
                and not get_only_fracVegCover):
                                    
                if vos.checkVariableInNC(landCoverPropertiesNC, "arnoBeta"):
                    
                    logger.debug("The parameter arnoBeta is defined in the netcdf file "+str(self.iniItemsLC['arnoBeta']))
                    lc_parameters['arnoBeta'] = vos.netcdf2PCRobjCloneWithoutTime(landCoverPropertiesNC, 'arnoBeta', self.cloneMap)
                                        
            # - option three: approximated from the minSoilDepthFrac and maxSoilDepthFrac
            if lc_parameters['arnoBeta'] is None and not get_only_fracVegCover:
   
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
            if not get_only_fracVegCover and lc_parameters['arnoBeta'] is None:

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
        if 'minPercolationLoss' in list(iniPaddyOptions.keys()) and iniPaddyOptions['minPercolationLoss'] != "None":
            min_percolation_loss = vos.readPCRmapClone(iniPaddyOptions['minPercolationLoss'], self.cloneMap,    
                                                       self.tmpDir, self.inputDir)
        if 'maxPercolationLoss' in list(iniPaddyOptions.keys()) and iniPaddyOptions['maxPercolationLoss'] != "None":
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


    def calculateParametersAtHalfTranspiration(self):
        # average soil parameters at which actual transpiration is halved
        if self.numberOfLayers == 2: 
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

#.....................................................................................................................................................

    def updateLC(self,meteo,groundwater,routing,
                      capRiseFrac,
                      nonIrrGrossDemandDict,
                      swAbstractionFractionDict,
                      currTimeStep,
                      allocSegments,
                      desalinationWaterUse,
                      groundwater_pumping_region_ids,
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
            
            self.satDegTotal = pcr.ifthen(self.landmask, \
                  vos.getValDivZero(\
                  self.storUpp + self.storLow, self.parameters.storCapUpp + self.parameters.storCapLow,\
                  vos.smallNumber, 0.0))

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

            self.satDegTotal = pcr.ifthen(self.landmask, \
                  vos.getValDivZero(\
                  self.storUpp000005 + self.storUpp005030 + self.satDegLow030150, self.parameters.storCapUpp000005 + self.parameters.storCapUpp005030 + self.parameters.storCapLow030150,\
                  vos.smallNumber, 0.0))
        
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
        # get crop coefficient
        if self.iniItemsLC['cropCoefficientNC'] == "None":
            cropKC = pcr.ifthen(self.landmask, pcr.spatial(pcr.scalar(0.0)))
        else:
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
            interceptCap = coverFraction * interceptCap

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

#.....................................................................................................................................................

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
            
            self.readAvlWater   = \
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
        # W    = actual water storage in root zone
        # WRANGE  = WMAX - WMIN
        # DW      = WMAX-W 
        # WFRAC   = DW/WRANGE ; WFRAC capped at 1
        # WFRACB  = DW/WRANGE raised to the power (1/(b+1))
        # SATFRAC = fractional saturated area
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
        
        # an idea by Edwin - 23 March 2015: no transpiration reduction in irrigated areas
        if self.name.startswith('irr') and self.includeIrrigation: relActTranspiration = pcr.scalar(1.0)
        
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
            # and also limited with reducedCapRise
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
        
        # deep percolation should consider irrigation application losses  (idea on 16 June 2015)
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
        
        # scale all fluxes based on available water (alternative 1)
        self.scaleAllFluxes(groundwater)

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

    def upperSoilUpdate(self,meteo,groundwater,routing,
                             capRiseFrac,
                             nonIrrGrossDemandDict,
                             swAbstractionFractionDict,
                             currTimeStep,
                             allocSegments,
                             desalinationWaterUse,
                             groundwater_pumping_region_ids,
                             regionalAnnualGroundwaterAbstractionLimit):

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
        # self.calculateWaterDemand(nonIrrGrossDemandDict,
                                  # swAbstractionFractionDict,
                                  # groundwater, routing,
                                  # allocSegments, currTimeStep,
                                  # desalinationWaterUse,
                                  # groundwater_pumping_region_ids,
                                  # regionalAnnualGroundwaterAbstractionLimit)
        
        water_use = wu.WaterUse(self,
                                nonIrrGrossDemandDict,
                                swAbstractionFractionDict,
                                groundwater,
                                routing,
                                allocSegments,
                                currTimeStep,
                                desalinationWaterUse,
                                groundwater_pumping_region_ids,
                                regionalAnnualGroundwaterAbstractionLimit)
        
        self.totalPotentialGrossDemand   = water_use.totalPotentialGrossDemand
        self.nonIrrGrossDemand           = water_use.nonIrrGrossDemand
        self.irrGrossDemand              = water_use.irrGrossDemand
        self.irrGrossDemandPaddy         = water_use.irrGrossDemandPaddy
        self.irrGrossDemandNonPaddy      = water_use.irrGrossDemandNonPaddy
        self.desalinationAbstraction     = water_use.desalinationAbstraction
        self.desalinationAllocation      = water_use.desalinationAllocation
        self.actSurfaceWaterAbstract     = water_use.actSurfaceWaterAbstract
        self.allocSurfaceWaterAbstract   = water_use.allocSurfaceWaterAbstract
        self.nonFossilGroundwaterAbs     = water_use.nonFossilGroundwaterAbs
        self.allocNonFossilGroundwater   = water_use.allocNonFossilGroundwater
        self.fossilGroundwaterAbstr      = water_use.fossilGroundwaterAbstr
        self.fossilGroundwaterAlloc      = water_use.fossilGroundwaterAlloc
        self.totalGroundwaterAbstraction = water_use.totalGroundwaterAbstraction
        self.totalGroundwaterAllocation  = water_use.totalGroundwaterAllocation
        
        self.totalPotentialMaximumGrossDemand            = water_use.totalPotentialMaximumGrossDemand
        self.totalPotentialMaximumNonIrrGrossDemand      = water_use.totalPotentialMaximumNonIrrGrossDemand
        self.totalPotentialMaximumIrrGrossDemand         = water_use.totalPotentialMaximumIrrGrossDemand
        self.totalPotentialMaximumIrrGrossDemandPaddy    = water_use.totalPotentialMaximumIrrGrossDemandPaddy
        self.totalPotentialMaximumIrrGrossDemandNonPaddy = water_use.totalPotentialMaximumIrrGrossDemandNonPaddy
        
        self.domesticWaterWithdrawal     = water_use.domesticWaterWithdrawal
        self.industryWaterWithdrawal     = water_use.industryWaterWithdrawal
        self.livestockWaterWithdrawal    = water_use.livestockWaterWithdrawal
        
        self.nonIrrReturnFlow            = water_use.nonIrrReturnFlow
        self.reducedCapRise              = water_use.reducedCapRise
        self.irrigationEfficiencyUsed      = water_use.irrigationEfficiencyUsed
        
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
