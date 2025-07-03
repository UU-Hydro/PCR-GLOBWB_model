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

import types
import pcraster as pcr
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

from ncConverter import *

import landCover as lc
import parameterSoilAndTopo as parSoilAndTopo

import water_demand.main_water_demand as water_demand
import water_management.main_water_management as water_management

# initialization of the qualloc
from copy import deepcopy
from water_management_qualloc.qualloc_main import qualloc_model
from water_management_qualloc.qualloc_reporting import qualloc_reporting
from water_management_qualloc.model_configuration import configuration_parser
from water_management_qualloc.model_time import model_time



class LandSurface(object):
    
    def getState(self):
        result = {}
    
        if self.numberOfSoilLayers == 2:
            for coverType in self.coverTypes:
                result[coverType] = {}
                result[coverType]['interceptStor'] = \
                  self.landCoverObj[coverType].interceptStor
                result[coverType]['snowCoverSWE' ] = \
                  self.landCoverObj[coverType].snowCoverSWE
                result[coverType]['snowFreeWater'] = \
                  self.landCoverObj[coverType].snowFreeWater
                result[coverType]['topWaterLayer'] = \
                  self.landCoverObj[coverType].topWaterLayer
                result[coverType]['storUpp'] = \
                  self.landCoverObj[coverType].storUpp
                result[coverType]['storLow'] = \
                  self.landCoverObj[coverType].storLow
                result[coverType]['interflow'    ] = \
                  self.landCoverObj[coverType].interflow

        if self.numberOfSoilLayers == 3:
            for coverType in self.coverTypes:
                result[coverType] = {}
                result[coverType]['interceptStor'] = \
                  self.landCoverObj[coverType].interceptStor
                result[coverType]['snowCoverSWE' ] = \
                  self.landCoverObj[coverType].snowCoverSWE
                result[coverType]['snowFreeWater'] = \
                  self.landCoverObj[coverType].snowFreeWater
                result[coverType]['topWaterLayer'] = \
                  self.landCoverObj[coverType].topWaterLayer
                result[coverType]['storUpp000005'] = \
                  self.landCoverObj[coverType].storUpp000005
                result[coverType]['storUpp005030'] = \
                  self.landCoverObj[coverType].storUpp005030
                result[coverType]['storLow030150'] = \
                  self.landCoverObj[coverType].storLow030150
                result[coverType]['interflow'    ] = \
                  self.landCoverObj[coverType].interflow
        
        return result
    
    def getPseudoState(self):
        result = {}
        
        if self.numberOfSoilLayers == 2:
            result['interceptStor'] = self.interceptStor
            result['snowCoverSWE']  = self.snowCoverSWE
            result['snowFreeWater'] = self.snowFreeWater
            result['topWaterLayer'] = self.topWaterLayer
            result['storUpp']       = self.storUpp
            result['storLow']       = self.storLow

        if self.numberOfSoilLayers == 3:
            result['interceptStor'] = self.interceptStor
            result['snowCoverSWE']  = self.snowCoverSWE
            result['snowFreeWater'] = self.snowFreeWater
            result['topWaterLayer'] = self.topWaterLayer
            result['storUpp000005'] = self.storUpp000005
            result['storUpp005030'] = self.storUpp005030
            result['storLow030150'] = self.storLow030150
        
        return result
    
    def __init__(self,iniItems,landmask,initialState=None):
        object.__init__(self)

        # clone map, temporary directory, absolute path of input directory, and landmask
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # make iniItems available for the other methods/functions:
        self.iniItems = iniItems

        # cellArea (unit: m2)
        self.cellArea = vos.readPCRmapClone(iniItems.routingOptions['cellAreaMap'], \
                                            self.cloneMap, self.tmpDir, self.inputDir)
        self.cellArea = pcr.ifthen(self.landmask, self.cellArea)
        
        # number of soil layers:
        self.numberOfSoilLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])
        
        # list of aggregated variables that MUST be defined in the module:
        # - aggregated from landCover modules
        # - some are needed for water balance checking 
        # - some are needed in other modules (e.g. routing, groundwater)
        # - some are needed for initialConditions
        
        # main state variables (unit: m)
        self.mainStates = ['interceptStor',\
                           'snowCoverSWE' ,\
                           'snowFreeWater',\
                           'topWaterLayer']
        
        # state variables (unit: m)
        self.stateVars = ['storUppTotal',
                          'storLowTotal',
                          'satDegUppTotal',
                          'satDegLowTotal',
                          'satDegTotal']
        
        # flux variables (unit: m/day)
        self.fluxVars  = ['infiltration',
                         'gwRecharge',
                         'netLqWaterToSoil',
                         'totalPotET',
                         'actualET',
                         'interceptEvap',
                         'openWaterEvap',
                         'actSnowFreeWaterEvap',
                         'actBareSoilEvap',
                         'actTranspiUppTotal',
                         'actTranspiLowTotal',
                         'actTranspiTotal',
                         'directRunoff',
                         'interflow',
                         'interflowTotal',
                         'landSurfaceRunoff',
                         'satExcess',
                         'snowMelt',
                         'irrigationTranspirationDeficit',
                         ]
        
        # specific variables for 2 and 3 layer soil models:
        if self.numberOfSoilLayers == 2:
            self.mainStates += ['storUpp','storLow']
            self.stateVars  += self.mainStates
            self.fluxVars   += ['actTranspiUpp','actTranspiLow','netPercUpp']
        
        if self.numberOfSoilLayers == 3:
            self.mainStates += ['storUpp000005',  'storUpp005030',  'storLow030150']
            self.stateVars  += self.mainStates
            self.fluxVars   += ['actTranspiUpp000005','actTranspiUpp005030','actTranspiLow030150',
                                   'netPercUpp000005',   'netPercUpp005030',
                                                       'interflowUpp005030']
        
        # list of all variables that will be calculated/reported in landSurface.py
        self.aggrVars = self.stateVars + self.fluxVars
        if self.numberOfSoilLayers == 2: self.aggrVars += ['satDegUpp','satDegLow']
        if self.numberOfSoilLayers == 3: self.aggrVars += ['satDegUpp000005','satDegUpp005030','satDegLow030150']
        
        # option to calculate the water balance
        self.debugWaterBalance = iniItems.landSurfaceOptions['debugWaterBalance']
        
        # landCover types included in the simulation: 
        self.coverTypes = ["forest","grassland"]
        
        # option to include irrigation per land cover type
        self.includeIrrigation = False
        if iniItems.waterDemandOptions['includeIrrigation'] == "True":
            self.includeIrrigation = True
            self.coverTypes += ["irrPaddy", "irrNonPaddy"]
            logger.info("Irrigation is included/considered in this run.")
        else:
            logger.info("Irrigation is NOT included/considered in this run.")
        
        # if user define their land cover types: 
        if 'landCoverTypes' in list(iniItems.landSurfaceOptions.keys()): 
            self.coverTypes = iniItems.landSurfaceOptions['landCoverTypes'].split(",")
        
        # water demand options: irrigation efficiency, non irrigation water demand, and desalination supply
        # - TODO: The following line will be deactivated due to the new development of water_demand and water_management modules.
        self.waterDemandOptions(iniItems)
        
        # TODO: Make an option so that users can easily perform natural runs (without water user, without reservoirs).
        
        # assign the topography and soil parameters
        self.soil_topo_parameters = {}
        # - default values used for all land cover types 
        self.soil_topo_parameters['default'] = parSoilAndTopo.SoilAndTopoParameters(iniItems,self.landmask)
        self.soil_topo_parameters['default'].read(iniItems)
        # - specific soil and topography parameter (per land cover type) 
        for coverType in self.coverTypes:
            name_of_section_given_in_ini_file = str(coverType)+'Options'
            dictionary_of_land_cover_settings = iniItems.__getattribute__(name_of_section_given_in_ini_file)
            
            if 'usingSpecificSoilTopo' not in list(dictionary_of_land_cover_settings.keys()): dictionary_of_land_cover_settings['usingSpecificSoilTopo'] = "False"            
            if dictionary_of_land_cover_settings['usingSpecificSoilTopo'] == "True":
                
                msg  = "Using a specific set of soil and topo parameters "
                msg += "as defined in the "+name_of_section_given_in_ini_file+" of the ini/configuration file." 
                
                self.soil_topo_parameters[coverType] = parSoilAndTopo.SoilAndTopoParameters(iniItems,self.landmask)
                self.soil_topo_parameters[coverType].read(iniItems, dictionary_of_land_cover_settings)
            else:
                
                msg  = "Using the default set of soil and topo parameters "
                msg += "as defined in the landSurfaceOptions of the ini/configuration file." 
                
                self.soil_topo_parameters[coverType] = self.soil_topo_parameters['default']            
            logger.info(msg)
        
        # instantiate self.landCoverObj[coverType]
        self.landCoverObj = {}
        for coverType in self.coverTypes: 
            self.landCoverObj[coverType] = lc.LandCover(iniItems,\
                                                        str(coverType)+'Options',\
                                                        self.soil_topo_parameters[coverType],self.landmask)
        
        # rescale landCover Fractions
        # - by default, the land cover fraction will always be corrected (to ensure the total of all fractions = 1.0)
        self.noLandCoverFractionCorrection = False
        if "noLandCoverFractionCorrection" in list(iniItems.landSurfaceOptions.keys()):
            if iniItems.landSurfaceOptions["noLandCoverFractionCorrection"] == "True": self.noLandCoverFractionCorrection = True
        # - rescaling land cover fractions
        if self.noLandCoverFractionCorrection == False:
            self.scaleNaturalLandCoverFractions()
            if self.includeIrrigation: self.scaleModifiedLandCoverFractions()
        
        # an option to introduce changes of land cover parameters (not only fracVegCover)
        self.noAnnualChangesInLandCoverParameter = True
        if 'annualChangesInLandCoverParameters' in list(iniItems.landSurfaceOptions.keys()):
            if iniItems.landSurfaceOptions['annualChangesInLandCoverParameters'] == "True": self.noAnnualChangesInLandCoverParameter = False
        
        # Note that "dynamicIrrigationArea" CANNOT be combined with "noLandCoverFractionCorrection"
        if self.noLandCoverFractionCorrection: self.dynamicIrrigationArea = False
        
        # Also note that "noAnnualChangesInLandCoverParameter = False" must be followed by "noLandCoverFractionCorrection"
        if self.noAnnualChangesInLandCoverParameter == False and self.noLandCoverFractionCorrection == False:
            self.noLandCoverFractionCorrection = True
            msg = "WARNING! No land cover fraction correction will be performed. Please make sure that the 'total' of all fracVegCover adds to one."
            logger.warning(msg) 
            logger.warning(msg) 
            logger.warning(msg) 
            logger.warning(msg) 
            logger.warning(msg) 
        
        # option to use QUAlloc
        self.using_qualloc = False
        if "using_qualloc" in iniItems.waterManagementOptions.keys():
            if iniItems.waterManagementOptions["using_qualloc"] == "True":
                self.using_qualloc = True
        
        # option to use DynQual
        self.using_dynqual = False
        if "quality" in iniItems.routingOptions.keys():
           if iniItems.routingOptions["quality"] == "True":
                self.using_dynqual = True
        
        ######################################################################################################################################################################################### 
        # 29 July 2014: 
        # 
        # If using historical/dynamic irrigation file (changing every year), we have to get fraction over irrigation area 
        #                                                                   (in order to calculate irrigation area for each irrigation type)
        #
        # Note that: totalIrrAreaFrac   = fraction irrigated areas (e.g. paddy + nonPaddy) over the entire cell area (dimensionless) ; this value changes (if self.dynamicIrrigationArea = True)
        #            irrTypeFracOverIrr = fraction each land cover type (paddy or nonPaddy) over the irrigation area (dimensionless) ; this value is constant for the entire simulation
        #
        if self.dynamicIrrigationArea:
            
            logger.info('Determining fraction of total irrigated areas over each cell')
            # Note that this is needed ONLY if historical irrigation areas are used (if self.dynamicIrrigationArea = True). 
            
            # total irrigated area fraction (over the entire cell) 
            totalIrrAreaFrac = 0.0 
            for coverType in self.coverTypes:
                if coverType.startswith('irr'):
                    totalIrrAreaFrac += self.landCoverObj[coverType].fracVegCover
            
            # fraction over irrigation area 
            for coverType in self.coverTypes:
                if coverType.startswith('irr'):
                    self.landCoverObj[coverType].irrTypeFracOverIrr = vos.getValDivZero(self.landCoverObj[coverType].fracVegCover,\
                                                                                        totalIrrAreaFrac, vos.smallNumber) 
        
        # get the initial conditions (for every land cover type)
        self.getInitialConditions(iniItems, initialState)
        
        # instantiate water demand
        self.water_demand = water_demand.WaterDemand(iniItems, landmask, self.coverTypes, self.landCoverObj)
        
        # instantiate water management
        if self.using_qualloc:
            # get the configuration file of qualloc
            qualloc_config_file = iniItems.waterManagementOptions["configuration_file_for_qualloc"] 

            # set the configuration object
            sections   = ['general','time','forcing','groundwater','surfacewater','water_management','water_quality']
            groups     = []
            subst_args = []
            self.qualloc_model_configuration = configuration_parser(\
                                                 cfgfilename = qualloc_config_file, \
                                                 sections    = sections, \
                                                 groups      = groups, \
                                                 subst_args  = subst_args)
            
            # initialize the time increment
            time_increment = 'daily'   # self.qualloc_model_configuration.time['time_increment']
            startyear      = int(self.qualloc_model_configuration.time['startyear'])
            endyear        = int(self.qualloc_model_configuration.time['endyear'])
            self.qualloc_model_time = model_time(startyear, endyear, time_increment)
            
            # dummy values for the model flags and initial conditions
            # initial conditions are initialized from the configuration file at the
            # start if set to None; otherwise, the existing warm states are used
            model_flags = {}
            initial_conditions = None
            
            # inititialize the QUAlloc model
            self.qualloc_model = qualloc_model(self.qualloc_model_configuration, \
                                               self.qualloc_model_time, \
                                               model_flags, \
                                               initial_conditions)
            self.qualloc_model.initialize(online_coupling = self.using_qualloc)
            
            # inititialize the reporting for QUAlloc
            self.qualloc_reporting = qualloc_reporting(self.qualloc_model_configuration)
            self.qualloc_reporting.initialize()
        
        else:
            # instantiate water management
            self.water_management = water_management.WaterManagement(iniItems, landmask)
        
        # initiate old style reporting (this is useful for debuging)
        self.initiate_old_style_land_surface_reporting(iniItems)


    def initiate_old_style_land_surface_reporting(self,iniItems):
        self.report = True
        try:
            self.outDailyTotNC = iniItems.landSurfaceOptions['outDailyTotNC'].split(",")
            self.outMonthTotNC = iniItems.landSurfaceOptions['outMonthTotNC'].split(",")
            self.outMonthAvgNC = iniItems.landSurfaceOptions['outMonthAvgNC'].split(",")
            self.outMonthEndNC = iniItems.landSurfaceOptions['outMonthEndNC'].split(",")
            self.outAnnuaTotNC = iniItems.landSurfaceOptions['outAnnuaTotNC'].split(",")
            self.outAnnuaAvgNC = iniItems.landSurfaceOptions['outAnnuaAvgNC'].split(",")
            self.outAnnuaEndNC = iniItems.landSurfaceOptions['outAnnuaEndNC'].split(",")
        except:
            self.report = False
        if self.report == True:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            #
            # daily output in netCDF files:
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


    def getInitialConditions(self, iniItems, iniConditions = None):
        
        # starting year in integer
        starting_year = int(iniItems.globalOptions['startTime'][0:4])
        
        # check if the run start at the first day of the year:
        start_on_1_Jan = False
        if iniItems.globalOptions['startTime'][-5:] == "01-01": start_on_1_Jan = True
        
        # condition to consider previous year land cover fraction 
        consider_previous_year_land_cover_fraction = False
        
        #######################################################################################################################################
        # obtaining initial land cover fractions for runs with dynamicIrrigationArea
        #
        # For non spin-up runs that start at the first day of the year (1 January), 
        # - we have to consider the previous year land cover fractions, specifically if we consider the dynamic/expansion of irrigation areas
        #
        if iniConditions == None and start_on_1_Jan == True and \
           self.dynamicIrrigationArea and self.noLandCoverFractionCorrection == False:
            # obtain the previous year land cover fractions:
            self.scaleDynamicIrrigation(starting_year - 1)                       # the previous year land cover fractions
            consider_previous_year_land_cover_fraction = True
        #
        # For spin-up runs or for runs that start after 1 January,
        # - we do not have to consider the previous year land cover fractions
        #
        if consider_previous_year_land_cover_fraction == False and \
           self.dynamicIrrigationArea and self.noLandCoverFractionCorrection == False:
            # just using the current year land cover fractions:
            self.scaleDynamicIrrigation(starting_year)                           # the current year land cover fractions
        #
        #################################################################################################################################
        
        #######################################################################################################################################
        # obtaining initial land cover fractions for runs with noLandCoverFractionCorrection and annualChangesInLandCoverParameters 
        #
        # For non spin-up runs that start at the first day of the year (1 January), 
        # - we have to consider the previous year land cover fractions
        #
        if iniConditions == None and start_on_1_Jan == True and \
           self.noLandCoverFractionCorrection and self.noAnnualChangesInLandCoverParameter == False:
            # obtain the previous year land cover fractions:
            previous_year = starting_year - 1
            one_january_prev_year = str(previous_year)+"-01-01"
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].get_land_cover_parameters(date_in_string = one_january_prev_year, \
                                                                                                                    get_only_fracVegCover = True)
            
            ####################################################################################################################################################################
            # correcting land cover fractions
            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover
            
            if 'grassland' in list(self.landCoverObj.keys()):
                self.landCoverObj['grassland'].previousFracVegCover = pcr.ifthenelse(total_fractions > 0.1, self.landCoverObj['grassland'].previousFracVegCover, 1.0)
            
            if 'short_natural' in list(self.landCoverObj.keys()):
                self.landCoverObj['short_natural'].previousFracVegCover = pcr.ifthenelse(total_fractions > 0.1, self.landCoverObj['short_natural'].previousFracVegCover, 1.0)
            
            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover
            
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].previousFracVegCover / total_fractions
            ####################################################################################################################################################################
            
            consider_previous_year_land_cover_fraction = True
        
        # For spin-up runs or for runs that start after 1 January,
        # - we do not have to consider the previous year land cover fractions
        if consider_previous_year_land_cover_fraction == False and \
           self.noLandCoverFractionCorrection and self.noAnnualChangesInLandCoverParameter == False:
            # just using the current year land cover fractions:
            one_january_this_year = str(starting_year)+"-01-01"
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].get_land_cover_parameters(date_in_string = one_january_this_year, \
                                                                                                                    get_only_fracVegCover = True)
            
            ####################################################################################################################################################################
            # correcting land cover fractions
            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover
            
            if 'grassland' in list(self.landCoverObj.keys()):
                self.landCoverObj['grassland'].previousFracVegCover = pcr.ifthenelse(total_fractions > 0.1, self.landCoverObj['grassland'].previousFracVegCover, 1.0)
            
            if 'short_natural' in list(self.landCoverObj.keys()):
                self.landCoverObj['short_natural'].previousFracVegCover = pcr.ifthenelse(total_fractions > 0.1, self.landCoverObj['short_natural'].previousFracVegCover, 1.0)
            
            total_fractions = pcr.scalar(0.0)
            for coverType in self.coverTypes:
                total_fractions += self.landCoverObj[coverType].previousFracVegCover
            
            for coverType in self.coverTypes:
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].previousFracVegCover / total_fractions
            ####################################################################################################################################################################
        
        # get initial conditions
        # - first, we set all aggregated states to zero (only the ones in mainStates): 
        for var in self.mainStates: vars(self)[var] = pcr.scalar(0.0)
        # - then we initiate them in the following loop of land cover types: 
        for coverType in self.coverTypes:
            if iniConditions != None:
                self.landCoverObj[coverType].getICsLC(iniItems,iniConditions['landSurface'][coverType])
            else:
                self.landCoverObj[coverType].getICsLC(iniItems)
            # summarize/aggregate the initial states/storages (using the initial land cover fractions: previousFracVegCover)
            for var in self.mainStates:
                # - initial land cover fractions (dimensionless) 
                if self.landCoverObj[coverType].previousFracVegCover is None:
                    self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].fracVegCover
                land_cover_fraction = self.landCoverObj[coverType].previousFracVegCover
                # - initial land cover states (unit: m)
                land_cover_states = vars(self.landCoverObj[coverType])[var]
                vars(self)[var]  += land_cover_states * land_cover_fraction


    def waterDemandOptions(self,iniItems):
        # historical irrigation area (unit: hectar)
        self.dynamicIrrigationArea = False
        if iniItems.landSurfaceOptions['historicalIrrigationArea'] != "None":
            logger.info("Using the dynamicIrrigationArea option. Extent of irrigation areas is based on the file provided in the 'historicalIrrigationArea'.")
            self.dynamicIrrigationArea = True
        
        if self.dynamicIrrigationArea:
            self.dynamicIrrigationAreaFile = vos.getFullPath(\
               iniItems.landSurfaceOptions['historicalIrrigationArea'],self.inputDir,False)


    def scaleNaturalLandCoverFractions(self): 
        ''' rescales natural land cover fractions (make sure the total = 1)'''
        
        # total land cover fractions
        pristineAreaFrac = 0.0
        numb_of_lc_types = 0.0
        for coverType in self.coverTypes:
            if not coverType.startswith('irr'):
                pristineAreaFrac += pcr.cover(self.landCoverObj[coverType].fracVegCover, 0.0)
                numb_of_lc_types += 1.0
        
        # Fill cells with pristineAreaFrac < 0.0 - with window average value within 0.5 and 1.5 degree
        for coverType in self.coverTypes:
            
            if not coverType.startswith('irr'):
                extrapolate = True
                if "noParameterExtrapolation" in self.iniItems.landSurfaceOptions.keys() and self.iniItems.landSurfaceOptions["noParameterExtrapolation"] == "True": extrapolate = False
                
                if extrapolate:
                    filled_fractions = pcr.windowaverage(self.landCoverObj[coverType].fracVegCover,0.5)
                    filled_fractions = pcr.cover(filled_fractions,\
                                       pcr.windowaverage(self.landCoverObj[coverType].fracVegCover,1.5))
                    filled_fractions = pcr.max(0.0, filled_fractions)
                    filled_fractions = pcr.min(1.0, filled_fractions)
                    
                    self.landCoverObj[coverType].fracVegCover = pcr.ifthen(pristineAreaFrac >= 0.0, self.landCoverObj[coverType].fracVegCover)
                    self.landCoverObj[coverType].fracVegCover = pcr.cover(\
                                                                self.landCoverObj[coverType].fracVegCover,filled_fractions)
                    self.landCoverObj[coverType].fracVegCover = pcr.ifthen(self.landmask,\
                                                                self.landCoverObj[coverType].fracVegCover)
        
        # re-check total land cover fractions
        pristineAreaFrac = 0.0
        numb_of_lc_types = 0.0
        for coverType in self.coverTypes:
            if not coverType.startswith('irr'):
                pristineAreaFrac += pcr.cover(self.landCoverObj[coverType].fracVegCover, 0.0)
                numb_of_lc_types += 1.0
        
        # Fill cells with pristineAreaFrac = 0.0:
        # - NOTE this only works for certain land cover names. TODO: FIX THIS
        try:
            self.landCoverObj['forest'].fracVegCover    = pcr.ifthenelse(pristineAreaFrac > 0.0, self.landCoverObj['forest'].fracVegCover, 0.0)
            self.landCoverObj['forest'].fracVegCover    = pcr.min(1.0, self.landCoverObj['forest'].fracVegCover)
            self.landCoverObj['grassland'].fracVegCover = 1.0 - self.landCoverObj['forest'].fracVegCover
        except:
            pass
        
        # recalculate total land cover fractions
        pristineAreaFrac = 0.0
        for coverType in self.coverTypes:
            if not coverType.startswith('irr'):
                pristineAreaFrac += pcr.cover(self.landCoverObj[coverType].fracVegCover, 0.0)
        
        # correcting 
        for coverType in self.coverTypes:
            if not coverType.startswith('irr'):
                self.landCoverObj[coverType].fracVegCover = \
                self.landCoverObj[coverType].fracVegCover / pristineAreaFrac
        
        pristineAreaFrac = 0.0 # reset
        # checking pristineAreaFrac (must be equal to 1)
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                pristineAreaFrac += self.landCoverObj[coverType].fracVegCover
                self.landCoverObj[coverType].naturalFracVegCover = \
                self.landCoverObj[coverType].fracVegCover
        
        # check and make sure that totalArea = 1.0 for all cells
        totalArea = pristineAreaFrac
        totalArea = pcr.ifthen(self.landmask,totalArea)
        totalArea = pcr.cover(totalArea, 1.0)
        check_map = totalArea - pcr.scalar(1.0)
        a,b,c = vos.getMinMaxMean(check_map)
        threshold = 1e-4
        if abs(a) > threshold or abs(b) > threshold:
            logger.error("total of 'Natural Area' fractions is not equal to 1.0 ... Min %f Max %f Mean %f" %(a,b,c))


    def scaleModifiedLandCoverFractions(self): 
        ''' rescales the land cover fractions with irrigation areas'''
        
        # calculate irrigatedAreaFrac (fraction of irrigation areas) 
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                irrigatedAreaFrac = irrigatedAreaFrac + self.landCoverObj[coverType].fracVegCover
        
        # correcting/scaling fracVegCover of irrigation if irrigatedAreaFrac > 1 
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                self.landCoverObj[coverType].fracVegCover = pcr.ifthenelse(irrigatedAreaFrac > 1.0,\
                                                                           self.landCoverObj[coverType].fracVegCover/irrigatedAreaFrac,\
                                                                           self.landCoverObj[coverType].fracVegCover)
        
        # the corrected irrigated area fraction 
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                irrigatedAreaFrac += self.landCoverObj[coverType].fracVegCover
        
        totalArea  = pcr.spatial(pcr.scalar(0.0))
        totalArea += irrigatedAreaFrac
        
        # correction factor for forest and grassland (pristine Areas)
        lcFrac = pcr.max(0.0, 1.0 - totalArea)
        pristineAreaFrac = pcr.spatial(pcr.scalar(0.0))
        
        for coverType in self.coverTypes:
            if not coverType.startswith('irr'):
                self.landCoverObj[coverType].fracVegCover = 0.0
                self.landCoverObj[coverType].fracVegCover = \
                self.landCoverObj[coverType].naturalFracVegCover * lcFrac
                pristineAreaFrac += pcr.cover(\
                self.landCoverObj[coverType].fracVegCover, 0.0)
        
        # check and make sure that totalArea = 1.0 for all cells
        totalArea += pristineAreaFrac
        totalArea = pcr.ifthen(self.landmask,totalArea)
        totalArea = pcr.cover(totalArea, 1.0)
        totalArea = pcr.ifthen(self.landmask,totalArea)
        a,b,c = vos.getMinMaxMean(totalArea - pcr.scalar(1.0))
        threshold = 1e-4
        if abs(a) > threshold or abs(b) > threshold:
            logger.error("fraction total (from all land cover types) is not equal to 1.0 ... Min %f Max %f Mean %f" %(a,b,c)) 


#    def obtainNonIrrWaterDemand(self,routing,currTimeStep):
#        # get NON-Irrigation GROSS water demand and its return flow fraction
#        # domestic water demand
#        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
#            if self.domesticWaterDemandOption: 
#                #
#                if self.domesticWaterDemandFile.endswith(vos.netcdf_suffixes):  
#                    #
#                    self.domesticGrossDemand = pcr.max(0.0, pcr.cover(\
#                     vos.netcdf2PCRobjClone(self.domesticWaterDemandFile,\
#                                                'domesticGrossDemand',\
#                         currTimeStep.fulldate, useDoy = 'monthly',\
#                                 cloneMapFileName = self.cloneMap), 0.0))
#                    #
#                    self.domesticNettoDemand = pcr.max(0.0, pcr.cover(\
#                     vos.netcdf2PCRobjClone(self.domesticWaterDemandFile,\
#                                                'domesticNettoDemand',\
#                         currTimeStep.fulldate, useDoy = 'monthly',\
#                                 cloneMapFileName = self.cloneMap), 0.0))
#                else:
#                    string_month = str(currTimeStep.month)
#                    if currTimeStep.month < 10: string_month = "0"+str(currTimeStep.month)
#                    grossFileName = self.domesticWaterDemandFile+"w"+str(currTimeStep.year)+".0"+string_month
#                    self.domesticGrossDemand = pcr.max(pcr.cover(\
#                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
#                    nettoFileName = self.domesticWaterDemandFile+"n"+str(currTimeStep.year)+".0"+string_month
#                    self.domesticNettoDemand = pcr.max(pcr.cover(\
#                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
#            else:
#                self.domesticGrossDemand = pcr.spatial(pcr.scalar(0.0))
#                self.domesticNettoDemand = pcr.spatial(pcr.scalar(0.0))
#                logger.debug("Domestic water demand is NOT included.")
#            
#            # gross and netto domestic water demand in m/day
#            self.domesticGrossDemand = pcr.cover(self.domesticGrossDemand,0.0)
#            self.domesticNettoDemand = pcr.cover(self.domesticNettoDemand,0.0)
#            self.domesticNettoDemand = pcr.min(self.domesticGrossDemand, self.domesticNettoDemand)
#        
#        # industry water demand
#        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
#            if self.industryWaterDemandOption: 
#                #
#                if self.industryWaterDemandFile.endswith(vos.netcdf_suffixes):  
#                    #
#                    self.industryGrossDemand = pcr.max(0.0, pcr.cover(\
#                     vos.netcdf2PCRobjClone(self.industryWaterDemandFile,\
#                                                'industryGrossDemand',\
#                         currTimeStep.fulldate, useDoy = 'monthly',\
#                                 cloneMapFileName = self.cloneMap), 0.0))
#                    #
#                    self.industryNettoDemand = pcr.max(0.0, pcr.cover(\
#                     vos.netcdf2PCRobjClone(self.industryWaterDemandFile,\
#                                                'industryNettoDemand',\
#                         currTimeStep.fulldate, useDoy = 'monthly',\
#                                 cloneMapFileName = self.cloneMap), 0.0))
#                else:
#                    grossFileName = self.industryWaterDemandFile+"w"+str(currTimeStep.year)+".map"
#                    self.industryGrossDemand = pcr.max(0.0, pcr.cover(\
#                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0))
#                    nettoFileName = self.industryWaterDemandFile+"n"+str(currTimeStep.year)+".map"
#                    self.industryNettoDemand = pcr.max(0.0, pcr.cover(\
#                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0))
#            else:
#                self.industryGrossDemand = pcr.spatial(pcr.scalar(0.0))
#                self.industryNettoDemand = pcr.spatial(pcr.scalar(0.0))
#                logger.debug("Industry water demand is NOT included.")
#        
#            # gross and netto industrial water demand in m/day
#            self.industryGrossDemand = pcr.cover(self.industryGrossDemand,0.0)
#            self.industryNettoDemand = pcr.cover(self.industryNettoDemand,0.0)
#            self.industryNettoDemand = pcr.min(self.industryGrossDemand, self.industryNettoDemand)  
#        
#        # livestock water demand
#        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
#            if self.livestockWaterDemandOption: 
#                #
#                if self.livestockWaterDemandFile.endswith(vos.netcdf_suffixes):  
#                    #
#                    self.livestockGrossDemand = pcr.max(0.0, pcr.cover(\
#                     vos.netcdf2PCRobjClone(self.livestockWaterDemandFile,\
#                                                'livestockGrossDemand',\
#                         currTimeStep.fulldate, useDoy = 'monthly',\
#                                 cloneMapFileName = self.cloneMap), 0.0))
#                    #
#                    self.livestockNettoDemand = pcr.max(0.0, pcr.cover(\
#                     vos.netcdf2PCRobjClone(self.livestockWaterDemandFile,\
#                                                'livestockNettoDemand',\
#                         currTimeStep.fulldate, useDoy = 'monthly',\
#                                 cloneMapFileName = self.cloneMap), 0.0))
#                else:
#                    string_month = str(currTimeStep.month)
#                    if currTimeStep.month < 10: string_month = "0"+str(currTimeStep.month)
#                    grossFileName = self.livestockWaterDemandFile+"w"+str(currTimeStep.year)+".0"+string_month
#                    self.livestockGrossDemand = pcr.max(pcr.cover(\
#                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
#                    nettoFileName = self.livestockWaterDemandFile+"n"+str(currTimeStep.year)+".0"+string_month
#                    self.livestockNettoDemand = pcr.max(pcr.cover(\
#                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
#            else:
#                self.livestockGrossDemand = pcr.spatial(pcr.scalar(0.0))
#                self.livestockNettoDemand = pcr.spatial(pcr.scalar(0.0))
#                logger.debug("Livestock water demand is NOT included.")
#            
#            # gross and netto livestock water demand in m/day
#            self.livestockGrossDemand = pcr.cover(self.livestockGrossDemand,0.0)
#            self.livestockNettoDemand = pcr.cover(self.livestockNettoDemand,0.0)
#            self.livestockNettoDemand = pcr.min(self.livestockGrossDemand, self.livestockNettoDemand)  
#
#        # GROSS domestic, industrial and livestock water demands (unit: m/day)
#        self.domesticGrossDemand  = pcr.ifthen(self.landmask, self.domesticGrossDemand )
#        self.domesticNettoDemand  = pcr.ifthen(self.landmask, self.domesticNettoDemand )
#        self.industryGrossDemand  = pcr.ifthen(self.landmask, self.industryGrossDemand )
#        self.industryNettoDemand  = pcr.ifthen(self.landmask, self.industryNettoDemand )
#        self.livestockGrossDemand = pcr.ifthen(self.landmask, self.livestockGrossDemand)
#        self.livestockNettoDemand = pcr.ifthen(self.landmask, self.livestockNettoDemand)
#        
#        # RETURN FLOW fractions for domestic, industrial and livestock water demands (unit: fraction/percentage)
#        self.domesticReturnFlowFraction  = pcr.min(1.0, pcr.max(0.0, 1.0 - vos.getValDivZero(self.domesticNettoDemand, self.domesticGrossDemand)))
#        self.industryReturnFlowFraction  = pcr.min(1.0, pcr.max(0.0, 1.0 - vos.getValDivZero(self.industryNettoDemand, self.industryGrossDemand)))
#        self.livestockReturnFlowFraction = pcr.min(1.0, pcr.max(0.0, 1.0 - vos.getValDivZero(self.livestockNettoDemand, self.livestockGrossDemand)))
#        
#        # make a dictionary summarizing potential demand (potential withdrawal) and its return flow fraction
#        nonIrrigationWaterDemandDict = {}
#        nonIrrigationWaterDemandDict['potential_demand'] = {}
#        nonIrrigationWaterDemandDict['potential_demand']['domestic']  = self.domesticGrossDemand
#        nonIrrigationWaterDemandDict['potential_demand']['industry']  = self.industryGrossDemand
#        nonIrrigationWaterDemandDict['potential_demand']['livestock'] = self.livestockGrossDemand
#        nonIrrigationWaterDemandDict['return_flow_fraction'] = {}
#        nonIrrigationWaterDemandDict['return_flow_fraction']['domestic']  = pcr.cover(pcr.min(1.0, pcr.roundup(self.domesticReturnFlowFraction *1000.)/1000.), 1.0)
#        nonIrrigationWaterDemandDict['return_flow_fraction']['industry']  = pcr.cover(pcr.min(1.0, pcr.roundup(self.industryReturnFlowFraction *1000.)/1000.), 1.0)
#        nonIrrigationWaterDemandDict['return_flow_fraction']['livestock'] = pcr.cover(pcr.min(1.0, pcr.roundup(self.livestockReturnFlowFraction*1000.)/1000.), 1.0)
#        
#        return nonIrrigationWaterDemandDict


    def calculateCapRiseFrac(self,groundwater,routing,currTimeStep):
        # calculate cell fraction influenced by capillary rise:
        # relative groundwater head (m) above the minimum elevation within a grid cell
        if groundwater.useMODFLOW == True:
            dzGroundwater = groundwater.relativeGroundwaterHead
            
            # update dzGroundwater from file, from modflow calculation, using the previous time step
            # - assumption that it will be updated once every month
            if currTimeStep.day == 1 and currTimeStep.timeStepPCR > 1: 
                
                # for online coupling, we will read files from pcraster maps
                directory = self.iniItems.main_output_directory + "/modflow/transient/maps/"
                
                # - relative groundwater head from MODFLOW
                yesterday = str(currTimeStep.yesterday())
                filename = directory + "relativeGroundwaterHead_" + str(yesterday) + ".map" 
                dzGroundwater = pcr.ifthen(self.landmask, pcr.cover(vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0))
        
        else:
            dzGroundwater = groundwater.storGroundwater/groundwater.specificYield
        
        # add some tolerance/influence level (unit: m)
        dzGroundwater += self.soil_topo_parameters['default'].maxGWCapRise;
        
        # set minimum value to zero (zero relativeGroundwaterHead indicate no capRiseFrac)
        dzGroundwater = pcr.max(0.0, dzGroundwater)
        
        # approximate cell fraction under influence of capillary rise
        FRACWAT = pcr.spatial(pcr.scalar(0.0));
        if currTimeStep.timeStepPCR > 1: 
            FRACWAT = pcr.cover(routing.WaterBodies.fracWat, 0.0); 
        else:
            if routing.includeWaterBodies:
                if routing.WaterBodies.useNetCDF:
                    routing.WaterBodies.fracWat = vos.netcdf2PCRobjClone(\
                                routing.WaterBodies.ncFileInp,'fracWaterInp', \
                                currTimeStep.fulldate, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)
                else:
                    if routing.WaterBodies.fracWaterInp != "None":
                        routing.WaterBodies.fracWat = vos.readPCRmapClone(\
                                    routing.WaterBodies.fracWaterInp+str(currTimeStep.year)+".map",
                                    self.cloneMap,self.tmpDir,self.inputDir)
                    else:
                        routing.WaterBodies.fracWat = pcr.spatial(pcr.scalar(0.0))
            else:
                if routing.WaterBodies.useNetCDF:
                    routing.WaterBodies.fracWat = vos.netcdf2PCRobjClone(\
                                routing.WaterBodies.ncFileInp,'fracWaterInp', \
                                currTimeStep.fulldate, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)
                else:
                    if routing.WaterBodies.fracWaterInp != "None":
                        routing.WaterBodies.fracWat = vos.readPCRmapClone(\
                                    routing.WaterBodies.fracWaterInp,
                                    self.cloneMap,self.tmpDir,self.inputDir)
                    else:
                        routing.WaterBodies.fracWat = pcr.spatial(pcr.scalar(0.0))
            # Note that the variable used in the following line is FRACWAT (this may be a 'small' bug fixing to the GMD paper version)
            FRACWAT = pcr.cover(routing.WaterBodies.fracWat, 0.0); 
        FRACWAT = pcr.cover(FRACWAT, 0.0)
        
        # zero fracwat assumption used for debugging against version 1.0
        if routing.zeroFracWatAllAndAlways: FRACWAT = pcr.scalar(0.0)
        
        CRFRAC = pcr.min(                                                                  1.0,1.0 -(self.soil_topo_parameters['default'].dzRel0100-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0100-self.soil_topo_parameters['default'].dzRel0090)       );
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0090,0.9 -(self.soil_topo_parameters['default'].dzRel0090-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0090-self.soil_topo_parameters['default'].dzRel0080),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0080,0.8 -(self.soil_topo_parameters['default'].dzRel0080-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0080-self.soil_topo_parameters['default'].dzRel0070),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0070,0.7 -(self.soil_topo_parameters['default'].dzRel0070-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0070-self.soil_topo_parameters['default'].dzRel0060),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0060,0.6 -(self.soil_topo_parameters['default'].dzRel0060-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0060-self.soil_topo_parameters['default'].dzRel0050),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0050,0.5 -(self.soil_topo_parameters['default'].dzRel0050-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0050-self.soil_topo_parameters['default'].dzRel0040),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0040,0.4 -(self.soil_topo_parameters['default'].dzRel0040-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0040-self.soil_topo_parameters['default'].dzRel0030),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0030,0.3 -(self.soil_topo_parameters['default'].dzRel0030-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0030-self.soil_topo_parameters['default'].dzRel0020),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0020,0.2 -(self.soil_topo_parameters['default'].dzRel0020-dzGroundwater)*0.1 /pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0020-self.soil_topo_parameters['default'].dzRel0010),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0010,0.1 -(self.soil_topo_parameters['default'].dzRel0010-dzGroundwater)*0.05/pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0010-self.soil_topo_parameters['default'].dzRel0005),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0005,0.05-(self.soil_topo_parameters['default'].dzRel0005-dzGroundwater)*0.04/pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0005-self.soil_topo_parameters['default'].dzRel0001),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater < self.soil_topo_parameters['default'].dzRel0001,0.01-(self.soil_topo_parameters['default'].dzRel0001-dzGroundwater)*0.01/pcr.max(0.001,self.soil_topo_parameters['default'].dzRel0001                                               ),CRFRAC);
        
        CRFRAC = pcr.ifthenelse(FRACWAT < 1.0,pcr.max(0.0,CRFRAC-FRACWAT)/(1.0-FRACWAT),0.0);
        
        capRiseFrac = pcr.max(0.0,pcr.min(1.0,CRFRAC))
        
        return capRiseFrac


#    def partitioningGroundSurfaceAbstraction(self,groundwater,routing):
#        # partitioning abstraction sources: groundwater and surface water
#        # de Graaf et al., 2014 principle: partitioning based on local average baseflow (m3/s) and upstream average discharge (m3/s)
#        # - estimates of fractions of groundwater and surface water abstractions 
#        averageBaseflowInput = routing.avgBaseflow
#        averageUpstreamInput = pcr.max(routing.avgDischarge, pcr.cover(pcr.upstream(routing.lddMap, routing.avgDischarge), 0.0))
#        
#        if self.usingAllocSegments:
#            
#            averageBaseflowInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageBaseflowInput))
#            averageUpstreamInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageUpstreamInput))
#            
#            averageBaseflowInput = pcr.cover(pcr.areaaverage(averageBaseflowInput, self.allocSegments), 0.0)
#            averageUpstreamInput = pcr.cover(pcr.areamaximum(averageUpstreamInput, self.allocSegments), 0.0)
#        
#        else:
#            logger.debug("Water demand can only be satisfied by local source.")
#        
#        swAbstractionFraction = vos.getValDivZero(\
#                                averageUpstreamInput, 
#                                averageUpstreamInput+averageBaseflowInput, vos.smallNumber)
#        swAbstractionFraction = pcr.roundup(swAbstractionFraction*100.)/100.
#        swAbstractionFraction = pcr.max(0.0, swAbstractionFraction)
#        swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)
#        
#        if self.usingAllocSegments:
#            swAbstractionFraction = pcr.areamaximum(swAbstractionFraction, self.allocSegments)
#        
#        swAbstractionFraction = pcr.cover(swAbstractionFraction, 1.0)
#        swAbstractionFraction = pcr.ifthen(self.landmask, swAbstractionFraction)
#        
#        # making a dictionary containing the surface water fraction for various purpose 
#        swAbstractionFractionDict = {}
#        # - the default estimate (based on de Graaf et al., 2014)
#        swAbstractionFractionDict['estimate'] = swAbstractionFraction
#        # - for irrigation and livestock purpose
#        swAbstractionFractionDict['irrigation'] = swAbstractionFraction
#        # - for industrial and domestic purpose
#        swAbstractionFractionDict['max_for_non_irrigation'] = swAbstractionFraction
#        #
#        # - a treshold fraction value to optimize/maximize surface water withdrawal for irrigation 
#        #   Principle: Areas with swAbstractionFractionDict['irrigation'] above this treshold will prioritize surface water use for irrigation purpose.
#        #              A zero treshold value will ignore this principle.    
#        swAbstractionFractionDict['treshold_to_maximize_irrigation_surface_water'] = self.treshold_to_maximize_irrigation_surface_water
#        #
#        # - a treshold fraction value to minimize fossil groundwater withdrawal, particularly to remove the unrealistic areas of fossil groundwater abstraction
#        #   Principle: Areas with swAbstractionFractionDict['irrigation'] above this treshold will not extract fossil groundwater.
#        swAbstractionFractionDict['treshold_to_minimize_fossil_groundwater_irrigation'] = self.treshold_to_minimize_fossil_groundwater_irrigation
#        
#        # the default value of surface water source fraction is None or not defined (in this case, this value will be the 'estimate' and limited with 'max_for_non_irrigation')
#        swAbstractionFractionDict['non_irrigation'] = None
#        
#        # incorporating the pre-defined fraction of surface water sources (e.g. based on Siebert et al., 2014 and McDonald et al., 2014)  
#        if self.swAbstractionFractionData is not None:
#            logger.debug('Using/incorporating the predefined fractions of surface water source.')
#            swAbstractionFractionDict['estimate']   = swAbstractionFraction
#            swAbstractionFractionDict['irrigation'] = self.partitioningGroundSurfaceAbstractionForIrrigation(swAbstractionFraction,\
#                                                                                                             self.swAbstractionFractionData,\
#                                                                                                             self.swAbstractionFractionDataQuality)
#            swAbstractionFractionDict['max_for_non_irrigation'] = self.maximumNonIrrigationSurfaceWaterAbstractionFractionData
#            
#            if self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData is not None:
#                swAbstractionFractionDict['non_irrigation'] = pcr.cover(
#                                                              self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData, \
#                                                              swAbstractionFractionDict['estimate'])
#                swAbstractionFractionDict['non_irrigation'] = pcr.min(\
#                                  swAbstractionFractionDict['non_irrigation'], \
#                                  swAbstractionFractionDict['max_for_non_irrigation'])
#        
#        else:
#            logger.debug('NOT using/incorporating the predefined fractions of surface water source.')
#        
#        return swAbstractionFractionDict


#    def partitioningGroundSurfaceAbstractionForIrrigation(self,\
#                                                          swAbstractionFractionEstimate,\
#                                                          swAbstractionFractionData,\
#                                                          swAbstractionFractionDataQuality):
#        
#        # surface water source fraction based on Stefan Siebert's map: 
#        factor = 0.5 # using this factor, the minimum value for the following 'data_weight_value' is 0.75 (for swAbstractionFractionDataQuality == 5) 
#        data_weight_value = pcr.scalar(1.0) - \
#                           (pcr.min(5., pcr.max(0.0, swAbstractionFractionDataQuality))/10.0)*factor
#                            
#        swAbstractionFractionForIrrigation = data_weight_value  * swAbstractionFractionData +\
#                                      (1.0 - data_weight_value) * swAbstractionFractionEstimate
#        
#        swAbstractionFractionForIrrigation = pcr.cover(swAbstractionFractionForIrrigation, swAbstractionFractionEstimate)
#        swAbstractionFractionForIrrigation = pcr.cover(swAbstractionFractionForIrrigation, 1.0)
#        swAbstractionFractionForIrrigation = pcr.ifthen(self.landmask, swAbstractionFractionForIrrigation)
#        
#        return swAbstractionFractionForIrrigation


    def scaleDynamicIrrigation(self,yearInInteger):
        # This method is to update fracVegCover of landCover for historical irrigation areas (done at yearly basis).
        #~ # Available datasets are only from 1960 to 2010 (status on 24 September 2010)
        #~ yearInInteger = int(yearInInteger)
        #~ if float(yearInInteger) < 1960. or float(yearInInteger) > 2010.:
            #~ msg = 'Dataset for the year '+str(yearInInteger)+" is not available. Dataset of historical irrigation areas is only available from 1960 to 2010."
            #~ logger.warning(msg)
        #~ yearInInteger = min(2010, max(1960, yearInInteger))
        #
        # TODO: Generally, I do not need the aforementioned lines as I have defined the functions "findLastYearInNCTime" and "findFirstYearInNCTime" in the module virtualOS.py
        #       However, Niko still need them for his DA scheme as we somehow his DA scheme cannot handle the netcdf file of historical irrigation areas (and therefore we have to use pcraster map files). 
        
        yearInString   = str(yearInInteger) 
        
        # read historical irrigation areas  
        if self.dynamicIrrigationAreaFile.endswith(('.nc4','.nc')):
            fulldateInString = yearInString+"-01"+"-01"   
            self.irrigationArea = 10000. * pcr.cover(\
                 vos.netcdf2PCRobjClone(self.dynamicIrrigationAreaFile,\
                                            'irrigationArea',\
                     fulldateInString, useDoy = 'yearly',\
                             cloneMapFileName = self.cloneMap), 0.0)        # unit: m2 (input file is in hectare)
        else:
            irrigation_pcraster_file = self.dynamicIrrigationAreaFile + yearInString + ".map"
            logger.debug('reading irrigation area map from : '+irrigation_pcraster_file)
            self.irrigationArea = 10000. * pcr.cover(\
                 vos.readPCRmapClone(irrigation_pcraster_file,\
                                   self.cloneMap,self.tmpDir), 0.0)         # unit: m2 (input file is in hectare)
        
        # TODO: Convert the input file, from hectare to percentage. 
        # This is to avoid errors if somebody uses 30 min input to run his 5 min model.
        
        # area of irrigation is limited by cellArea
        self.irrigationArea = pcr.max(self.irrigationArea, 0.0)              
        self.irrigationArea = pcr.min(self.irrigationArea, self.cellArea)   # limited by cellArea
        
        # calculate fracVegCover (for irrigation only)
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                
                self.landCoverObj[coverType].fractionArea = 0.0    # reset 
                self.landCoverObj[coverType].fractionArea = self.landCoverObj[coverType].irrTypeFracOverIrr * self.irrigationArea # unit: m2
                self.landCoverObj[coverType].fracVegCover = pcr.min(1.0, self.landCoverObj[coverType].fractionArea/ self.cellArea) 
                
                # avoid small values
                self.landCoverObj[coverType].fracVegCover = pcr.rounddown(self.landCoverObj[coverType].fracVegCover * 1000.)/1000.
        
        # rescale land cover fractions (for all land cover types):
        self.scaleModifiedLandCoverFractions()


    def update(self,meteo,groundwater,routing,currTimeStep):
        # for every land cover, set land cover parameters (for every land cover object)
        # - for this will return the following:
        #   fracVegCover, arnoBeta, rootZoneWaterStorageMin, rootZoneWaterStorageRange, \
        #                           maxRootDepth, adjRootFrUpp, adjRootFrLow
        #   effSatAt50 and effPoreSizeBetaAt50
        #   cropKc
        #   coverFraction and interceptCap
        
        # - loop per each land cover type):
        for coverType in self.coverTypes:
            logger.info("Setting land cover parameters: "+str(coverType))
            self.landCoverObj[coverType].set_land_cover_parameters(currTimeStep)
        
        # transfer some states from certain land covers to others, due to changes/dynamics in land cover conditions
        # - if considering dynamic/historical irrigation areas (expansion/reduction of irrigated areas)
        # - done at yearly basis, at the beginning of each year
        # - note that this must be done at the beginning of each year, including for the first time step (timeStepPCR == 1)
        self.state_transfer_among_land_cover(currTimeStep)
        
        # for every land cover, calculate total potential evaporation and partition it to bare soil evaporation and transpiration
        # - for this will return the following:
        #   totalPotET, potBareSoilEvap, potTranspiration
        # - loop per each land cover type):
        for coverType in self.coverTypes:
            logger.info("Calculate potential evaporation and partition this to bare soil evaporation and transpiration: "+str(coverType))
            self.landCoverObj[coverType].getPotET(meteo, currTimeStep)
        
        # for every land cover, running the interception module
        # - for this will return or update the following:
        #   throughfall, interceptStor, snowfall, liquidPrecip, potInterceptionFlux, interceptEvap, potBareSoilEvap, potTranspiration, actualET
        # - loop per each land cover type):
        for coverType in self.coverTypes:
            logger.info("Running the inteception module: "+str(coverType))
            self.landCoverObj[coverType].interceptionUpdate(meteo, currTimeStep)
        
        # for every land cover, running the snow module
        # - for this will return or update the following:
        #   snowCoverSWE, snowMelt, snowFreeWater, netLqWaterToSoil, actSnowFreeWaterEvap, potBareSoilEvap, actualET
        # - loop per each land cover type):
        for coverType in self.coverTypes:
            logger.info("Running the snow module: "+str(coverType))
            self.landCoverObj[coverType].snow_module_update(meteo, currTimeStep)
        
        # calculate water demand
        # (units: m)
        # - based on the 'states' after the above processes
        #   (for soil moisture and topWaterLayer states, they should be just the same as from the previous date)
        self.water_demand.update(meteo        = meteo, \
                                 landSurface  = self, \
                                 groundwater  = groundwater, \
                                 routing      = routing, \
                                 currTimeStep = currTimeStep)
        
        # - return the following gross sectoral water demands in volume
        #   (units: m3)
        vol_gross_sectoral_water_demands = {}
        
        # -- non irrigation demand
        #    (units: m3)
        vol_gross_sectoral_water_demands["domestic"]       = self.water_demand.water_demand_domestic.domesticGrossDemand             * routing.cellArea
        vol_gross_sectoral_water_demands["industry"]       = self.water_demand.water_demand_industry.industryGrossDemand             * routing.cellArea
        vol_gross_sectoral_water_demands["manufacture"]    = self.water_demand.water_demand_manufacture.manufactureGrossDemand       * routing.cellArea
        vol_gross_sectoral_water_demands["thermoelectric"] = self.water_demand.water_demand_thermoelectric.thermoelectricGrossDemand * routing.cellArea
        vol_gross_sectoral_water_demands["livestock"]      = self.water_demand.water_demand_livestock.livestockGrossDemand           * routing.cellArea
        
        # -- irrigation demand
        #    (units: m3)
        vol_gross_sectoral_water_demands["irrigation"] = pcr.scalar(0.0)
        for coverType in self.coverTypes: 
            if coverType.startswith("irr"):
                vol_gross_sectoral_water_demands["irrigation"] += \
                    self.water_demand.water_demand_irrigation[coverType].irrGrossDemand * routing.cellArea * self.landCoverObj[coverType].fracVegCover 
        
        # calculate water allocation
        # pool the demands and do the allocation on the available storages at the land surface level / water allocation model and then pass the withdrawals to the surface and groundwater
        # - input: - sectoral water demands (calculated in "self.water_demand.update")
        #          - water availabilities (from previous time step: surface water and groundwater; from the current time step: desalination)
        # - output: - water abstraction from surface water, groundwater and etc
        #           - water allocation, including irrigation supply - this will be given to the next time step
        # - note: the water_management calculation should be done in volume (m3)
        
        if self.using_qualloc:
            # QUAlloc: update ..........................................
            # set the water quality states (if specified)
            surfacewater_temperature = None
            surfacewater_organic     = None
            surfacewater_salinity    = None
            surfacewater_pathogen    = None
            if self.using_dynqual:
                surfacewater_temperature = routing.waterTemp - 273.15
                surfacewater_organic     = pcr.ifthen(routing.organic  < vos.MV, routing.organic)
                surfacewater_salinity    = pcr.ifthen(routing.salinity < vos.MV, routing.salinity)
                surfacewater_pathogen    = pcr.ifthen(routing.pathogen < vos.MV, routing.pathogen)
            
            pcr.report(surfacewater_salinity, f'/scratch-shared/gcardenas/{currTimeStep}_salinity_dynqual.map')
            
            # update QUAlloc for the current date
            self.qualloc_model_time.update(currTimeStep.timeStepPCR)
            self.qualloc_model.update(online_coupling_to_quantity     = self.using_qualloc, \
                                      irrigationGrossDemand           = vol_gross_sectoral_water_demands["irrigation"] / routing.cellArea, \
                                      domesticGrossDemand             = self.water_demand.water_demand_domestic.domesticGrossDemand, \
                                      domesticNettoDemand             = self.water_demand.water_demand_domestic.domesticNettoDemand, \
                                      industryGrossDemand             = self.water_demand.water_demand_industry.industryGrossDemand, \
                                      industryNettoDemand             = self.water_demand.water_demand_industry.industryNettoDemand, \
                                      livestockGrossDemand            = self.water_demand.water_demand_livestock.livestockGrossDemand, \
                                      livestockNettoDemand            = self.water_demand.water_demand_livestock.livestockNettoDemand, \
                                      manufactureGrossDemand          = self.water_demand.water_demand_manufacture.manufactureGrossDemand, \
                                      manufactureNettoDemand          = self.water_demand.water_demand_manufacture.manufactureNettoDemand, \
                                      thermoelectricGrossDemand       = self.water_demand.water_demand_thermoelectric.thermoelectricGrossDemand, \
                                      thermoelectricNettoDemand       = self.water_demand.water_demand_thermoelectric.thermoelectricNettoDemand, \
                                      environmentGrossDemand          = None, \
                                      surfacewater_storage            = routing.channelStorage / routing.cellArea, \
                                      surfacewater_discharge          = routing.discharge, \
                                      surfacewater_totalrunoff         = routing.runoff, \
                                      groundwater_recharge            = groundwater.gwRecharge, \
                                      groundwater_baseflow             = groundwater.baseflow, \
                                      groundwater_storage             = groundwater.storGroundwater, \
                                      
                                      online_coupling_to_quality      = self.using_dynqual, \
                                      surfacewater_temperature        = surfacewater_temperature, \
                                      surfacewater_organic            = surfacewater_organic, \
                                      surfacewater_salinity           = surfacewater_salinity, \
                                      surfacewater_pathogen           = surfacewater_pathogen, \
                                      groundwater_temperature         = None, \
                                      groundwater_organic             = None, \
                                      groundwater_salinity            = None, \
                                      groundwater_pathogen            = None, \
                                      )
            
            # QUAlloc: reporting .......................................
            # reporting QUAlloc outputs and states
            self.qualloc_reporting.report(self.qualloc_model_time, self.qualloc_model)
            
            if self.qualloc_model_time.report_flags['yearly']:
                # additional processing at the end of year:
                # report the states, so the run can be restarted
                # as a safeguard and to reduce the initial states, write any outstanding soil production
                self.qualloc_model.finalize_year()
            
            # last time step
            if self.qualloc_model_time.last_time_step:
                # close down all files open for input and output
                self.qualloc_model.finalize_run()
                self.qualloc_reporting.close()
            
            # set variables ............................................
            # get the following variables to be passed to other modules
            
            # sectoral water allocation from all sources
            # (despite the variables' name says 'withdrawal')
            # domestic: total allocated water (units: m3)
            try:
                self.domesticWaterWithdrawal = \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater']['domestic'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater']['domestic'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater']['domestic'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector_desalwater['domestic']
            except:
                self.domesticWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))
            
            # industry: total allocated water (units: m3)
            try:
                self.industryWaterWithdrawal = \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater']['industry'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater']['industry'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater']['industry'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector_desalwater['industry']
            except:
                self.industryWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))
            
            # livestock: total allocated water (units: m3)
            try:
                self.livestockWaterWithdrawal = \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater']['livestock'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater']['livestock'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater']['livestock'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector_desalwater['livestock']
            except:
                self.livestockWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))
            
            # manufacture: total allocated water (units: m3)
            try:
                self.manufactureWaterWithdrawal = \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater']['manufacture'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater']['manufacture'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater']['manufacture'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector_desalwater['manufacture']
            except:
                self.manufactureWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))
            
            # thermoelectric: total allocated water (units: m3)
            try:
                self.thermoelectricWaterWithdrawal = \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater']['thermoelectric'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater']['thermoelectric'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater']['thermoelectric'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector_desalwater['thermoelectric']
            except:
                self.thermoelectricWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))
            
            # irrigation: total allocated water (units: m3)
            try:
                self.irrigationWaterWithdrawal = \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater']['irrigation'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater']['irrigation'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater']['irrigation'] + \
                    self.qualloc_model.water_management.allocated_demand_per_sector_desalwater['irrigation']
            except:
                self.irrigationWaterWithdrawal = pcr.spatial(pcr.scalar(0.0))
            
            # desalination total water abstraction and allocation (from all sectors)
            # (units: m)
            self.desalinationAbstraction = self.qualloc_model.water_management.allocated_withdrawal_desalwater / self.cellArea
            self.desalinationAllocation  = self.qualloc_model.water_management.allocated_demand_desalwater / self.cellArea
            
            # total surface water abstraction and allocation (from all sectors)
            # (units: m/day)
            self.actSurfaceWaterAbstract   = \
                 sum(list(self.qualloc_model.water_management.allocated_withdrawal_per_sector['renewable_surfacewater'].values())) / self.cellArea
            self.allocSurfaceWaterAbstract = \
                 sum(list(self.qualloc_model.water_management.allocated_demand_per_sector['renewable_surfacewater'].values())) / self.cellArea
            
            # total renewable groundwater abstraction and allocation (from all sectors)
            # (units: m/day)
            self.nonFossilGroundwaterAbs   = \
                 sum(list(self.qualloc_model.water_management.allocated_withdrawal_per_sector['renewable_groundwater'].values())) / self.cellArea
            self.allocNonFossilGroundwater = \
                 sum(list(self.qualloc_model.water_management.allocated_demand_per_sector['renewable_groundwater'].values())) / self.cellArea
            
            # total non-renewable groundwater abstraction and allocation (from all sectors)
            # (units: m/day)
            self.fossilGroundwaterAbstr    = \
                 sum(list(self.qualloc_model.water_management.allocated_withdrawal_per_sector['nonrenewable_groundwater'].values())) / self.cellArea
            self.fossilGroundwaterAlloc    = \
                 sum(list(self.qualloc_model.water_management.allocated_demand_per_sector['nonrenewable_groundwater'].values())) / self.cellArea
            
            # total groundwater abstraction and allocation in water-slice
            # (units: m/day)
            self.totalGroundwaterAbstraction = self.nonFossilGroundwaterAbs + self.fossilGroundwaterAbstr
            self.totalGroundwaterAllocation  = self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
            
            # calculate the non-irrigation related variables
            # - volume (unit: m3/day)
            self.nonIrrReturnFlowVolumePerSector       = {}
            self.nonIrrWaterConsumptionVolumePerSector = {}
            
            for sector_name in self.qualloc_model.water_management.sector_names:
                nonIrrReturnFlowVolume = pcr.scalar(0.0)
                nonIrrWaterConsumptionVolume = pcr.scalar(0.0)
                
                if sector_name != 'irrigation':
                    # return flows from desalinated water
                    nonIrrReturnFlowVolume       += self.qualloc_model.water_management.return_flow_demand_per_sector_desalwater[sector_name]
                    # water consumption from desalinated water
                    nonIrrWaterConsumptionVolume += self.qualloc_model.water_management.consumed_demand_per_sector_desalwater[sector_name]
                    
                    for withdrawal_name in self.qualloc_model.water_management.withdrawal_names:
                        for source_name in self.qualloc_model.water_management.source_names:
                            key = '%s_%s'   % (withdrawal_name, source_name)
                            
                            # return flows from surface and groundwater
                            nonIrrReturnFlowVolume += \
                                self.qualloc_model.water_management.return_flow_demand_per_sector[key][sector_name]
                            # water consumption from surface and groundwater
                            nonIrrWaterConsumptionVolume += \
                                self.qualloc_model.water_management.consumed_demand_per_sector[key][sector_name]
                    
                    # setting variables
                    self.nonIrrReturnFlowVolumePerSector[sector_name]       = deepcopy(nonIrrReturnFlowVolume)
                    self.nonIrrWaterConsumptionVolumePerSector[sector_name] = deepcopy(nonIrrWaterConsumptionVolume)
            
            if 'domestic' not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector['domestic'] = pcr.spatial(pcr.scalar(0.0))
            
            if 'industry' not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector['industry'] = pcr.spatial(pcr.scalar(0.0))
            
            if 'manufacture' not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector['manufacture'] = pcr.spatial(pcr.scalar(0.0))
            
            if 'thermoelectric' not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector['thermoelectric'] = pcr.spatial(pcr.scalar(0.0))
            
            if 'livestock' not in self.qualloc_model.water_management.sector_names:
                self.nonIrrReturnFlowVolumePerSector['livestock'] = pcr.spatial(pcr.scalar(0.0))
            
            self.nonIrrReturnFlowVolume = sum(list(self.nonIrrReturnFlowVolumePerSector.values()))
            self.nonIrrWaterConsumptionVolume = sum(list(self.nonIrrWaterConsumptionVolumePerSector.values()))
            
            # - water-slice (unit: m/day)
            #   return flows
            self.nonIrrReturnFlow  = nonIrrReturnFlowVolume / self.cellArea
            #   water consumption
            self.nonIrrWaterConsumption  =  nonIrrWaterConsumptionVolume / self.cellArea
            
            # variable to reduce capillary rise in order to ensure there is always enough water to supply non fossil groundwater abstraction 
            # (units: m)
            self.reducedCapRise = self.nonFossilGroundwaterAbs
        
        # standard water management calculation in PCR-GLOBWB2
        else:
            # update the water management module for the current date
            self.water_management.update( \
                          vol_gross_sectoral_water_demands = vol_gross_sectoral_water_demands, \
                          groundwater  = groundwater, \
                          routing      = routing, \
                          currTimeStep = currTimeStep)
            
            # domestic: total allocated water (units: m3)
            self.domesticWaterWithdrawal = self.water_management.satisfied_gross_sectoral_water_demands["domestic"]
            
            # industry: total allocated water (units: m3)
            self.industryWaterWithdrawal = self.water_management.satisfied_gross_sectoral_water_demands["industry"]
            
            # livestock: total allocated water (units: m3)
            self.livestockWaterWithdrawal = self.water_management.satisfied_gross_sectoral_water_demands["livestock"]
            
            # manufacture: total allocated water (units: m3)
            self.manufactureWaterWithdrawal = self.water_management.satisfied_gross_sectoral_water_demands["manufacture"]
            
            # thermoelectric: total allocated water (units: m3)
            self.thermoelectricWaterWithdrawal = self.water_management.satisfied_gross_sectoral_water_demands["thermoelectric"]
            
            # irrigation: total water allocated (units: m3)
            self.irrigationWaterWithdrawal = self.water_management.satisfied_gross_sectoral_water_demands["irrigation"]
            
            # get the following variables to be passed to other modules
            # - desalination water abstraction and allocation, total for all sectors (units: m)
            self.desalinationAbstraction   = self.water_management.desalinationAbstraction
            self.desalinationAllocation    = self.water_management.desalinationAllocation
            
            # - surface water abstraction and allocation, total for all sectors (units: m)
            self.allocSurfaceWaterAbstract = self.water_management.allocSurfaceWaterAbstract
            self.actSurfaceWaterAbstract   = self.water_management.actSurfaceWaterAbstract
            
            # - renewable groundwater abstraction and allocation, total for all sectors (units: m)
            self.nonFossilGroundwaterAbs   = self.water_management.nonFossilGroundwaterAbs
            self.allocNonFossilGroundwater = self.water_management.allocNonFossilGroundwater
            
            # - non-renewable groundwater abstraction, total for all sectors (units: m)
            self.fossilGroundwaterAbstr    = self.water_management.fossilGroundwaterAbstr
            self.fossilGroundwaterAlloc    = self.water_management.fossilGroundwaterAlloc
            
            # - total groundwater abstraction and allocation in water slice/height (units: m)
            self.totalGroundwaterAbstraction = self.nonFossilGroundwaterAbs + self.fossilGroundwaterAbstr
            self.totalGroundwaterAllocation  = self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
            
            # calculate the non irrigation return flow
            # - volume (unit: m3)
            self.nonIrrReturnFlowVolumePerSector = {}
            self.nonIrrReturnFlowVolumePerSector['domestic']       = self.water_demand.water_demand_domestic.domesticReturnFlowFraction             * self.water_management.satisfied_gross_sectoral_water_demands["domestic"]
            self.nonIrrReturnFlowVolumePerSector['industry']       = self.water_demand.water_demand_industry.industryReturnFlowFraction             * self.water_management.satisfied_gross_sectoral_water_demands["industry"]
            self.nonIrrReturnFlowVolumePerSector['manufacture']    = self.water_demand.water_demand_manufacture.manufactureReturnFlowFraction       * self.water_management.satisfied_gross_sectoral_water_demands["manufacture"]
            self.nonIrrReturnFlowVolumePerSector['thermoelectric'] = self.water_demand.water_demand_thermoelectric.thermoelectricReturnFlowFraction * self.water_management.satisfied_gross_sectoral_water_demands["thermoelectric"]
            self.nonIrrReturnFlowVolumePerSector['livestock']      = self.water_demand.water_demand_livestock.livestockReturnFlowFraction           * self.water_management.satisfied_gross_sectoral_water_demands["livestock"]
            
            self.nonIrrReturnFlowVolume = sum(list(self.nonIrrReturnFlowVolumePerSector.values()))
            
            # - water-slice (unit: m)
            self.nonIrrReturnFlow  = self.nonIrrReturnFlowVolume / self.cellArea
            
            # calculate the non irrigation consumption
            # - volume (unit: m3)
            self.nonIrrWaterConsumptionVolumePerSector = {}
            self.nonIrrWaterConsumptionVolumePerSector['domestic']       = self.water_management.satisfied_gross_sectoral_water_demands["domestic"]       - self.nonIrrReturnFlowVolumePerSector['domestic']
            self.nonIrrWaterConsumptionVolumePerSector['industry']       = self.water_management.satisfied_gross_sectoral_water_demands["industry"]       - self.nonIrrReturnFlowVolumePerSector['industry']
            self.nonIrrWaterConsumptionVolumePerSector['manufacture']    = self.water_management.satisfied_gross_sectoral_water_demands["manufacture"]    - self.nonIrrReturnFlowVolumePerSector['manufacture']
            self.nonIrrWaterConsumptionVolumePerSector['thermoelectric'] = self.water_management.satisfied_gross_sectoral_water_demands["thermoelectric"] - self.nonIrrReturnFlowVolumePerSector['thermoelectric']
            self.nonIrrWaterConsumptionVolumePerSector['livestock']      = self.water_management.satisfied_gross_sectoral_water_demands["livestock"]      - self.nonIrrReturnFlowVolumePerSector['livestock']
            
            self.nonIrrWaterConsumptionVolume = sum(list(self.nonIrrWaterConsumptionVolumePerSector.values()))
            
            # - water-slice (unit: m)
            self.nonIrrWaterConsumption  =  self.nonIrrWaterConsumptionVolume / self.cellArea
            
            # variable to reduce capillary rise in order to ensure there is always enough water to supply non fossil groundwater abstraction 
            # - unit: m
            self.reducedCapRise = self.water_management.reducedCapRise
        
        # water demand limited to available/allocated water
        # (units: m)
        self.totalPotentialGrossDemand = self.fossilGroundwaterAlloc +\
                                         self.allocNonFossilGroundwater +\
                                         self.allocSurfaceWaterAbstract +\
                                         self.desalinationAllocation
        
        self.irrGrossDemand    = self.irrigationWaterWithdrawal / self.cellArea
        self.nonIrrGrossDemand = pcr.max(0.0, \
                                         self.totalPotentialGrossDemand - self.irrGrossDemand)
        
        # calculate the total fraction of irrigated areas within the cell
        total_cell_fraction_of_irrigated_areas = pcr.ifthen(self.landmask, pcr.scalar(0.0))
        for coverType in self.coverTypes: 
            if coverType.startswith("irr"):
                total_cell_fraction_of_irrigated_areas = total_cell_fraction_of_irrigated_areas + self.landCoverObj[coverType].fracVegCover
        
        # distribute the allocated irrigation water supplied
        self.satisfied_irrigation_water_volume = {}
        self.satisfied_irrigation_water_height = {}
        for coverType in self.coverTypes: 
            
            # for irrigation land cover types
            if coverType.startswith("irr"):
                
                # - in volume (m3)
                self.satisfied_irrigation_water_volume[coverType] = \
                            pcr.ifthenelse(total_cell_fraction_of_irrigated_areas > 0.0, \
                                           self.irrigationWaterWithdrawal * self.landCoverObj[coverType].fracVegCover / total_cell_fraction_of_irrigated_areas, \
                                           pcr.scalar(0.0))
                
                # - in water slice/height (m)
                self.satisfied_irrigation_water_height[coverType] = \
                            pcr.ifthenelse(self.landCoverObj[coverType].fracVegCover > 0.0, \
                                           self.satisfied_irrigation_water_volume[coverType] / (routing.cellArea * self.landCoverObj[coverType].fracVegCover), \
                                           pcr.scalar(0.0))
            
            # for non irrigation land cover types
            else:
                self.satisfied_irrigation_water_volume[coverType] = pcr.ifthen(self.landmask, pcr.scalar(0.0))
                self.satisfied_irrigation_water_height[coverType] = pcr.ifthen(self.landmask, pcr.scalar(0.0))
        
        # TODO: Fix the following water balance checks, or shall we put it within the water management module
        if self.debugWaterBalance:
           vos.waterBalanceCheck([self.desalinationAllocation, \
                                  self.allocSurfaceWaterAbstract, \
                                  self.allocNonFossilGroundwater, \
                                  self.fossilGroundwaterAlloc], \
                                  [self.totalPotentialGrossDemand], \
                                  [pcr.scalar(0.)], \
                                  [pcr.scalar(0.)], \
                                  'satisfied demand allocation from different water sources: desalination, surface water, groundwater & unmetDemand. Error here may be due to rounding error.', \
                                   True, \
                                   currTimeStep.fulldate,threshold = 1e-3)
        
        # do the remaining land cover processes
        # - this including applying the 'allocated irrGrossDemand'
        # - we also need the variable 'reducedCapRise = volRenewGroundwaterAbstraction / self.cellArea' from every land cover type
        self.land_surface_hydrology_update(meteo, groundwater, routing, currTimeStep)
        
        # old-style reporting (this is useful for debugging)
        self.old_style_land_surface_reporting(currTimeStep)


    def state_transfer_among_land_cover(self, currTimeStep):
        
        # transfer some states, due to changes/dynamics in land cover conditions
        # - if considering dynamic/historical irrigation areas (expansion/reduction of irrigated areas)
        # - done at yearly basis, at the beginning of each year
        # - note that this must be done at the beginning of each year, including for the first time step (timeStepPCR == 1)
        
        if ((self.dynamicIrrigationArea and self.includeIrrigation) or self.noAnnualChangesInLandCoverParameter == False) and currTimeStep.doy == 1:
            # loop for all main states:
            for var in self.mainStates:
                logger.info("Transfering states for the variable "+str(var))
                
                moving_fraction = pcr.scalar(0.0)                       # total land cover fractions that will be transferred
                moving_states   = pcr.scalar(0.0)                       # total states that will be transferred
                
                for coverType in self.coverTypes:
                    
                    old_fraction = self.landCoverObj[coverType].previousFracVegCover
                    new_fraction = self.landCoverObj[coverType].fracVegCover
                    
                    moving_fraction += pcr.max(0.0, old_fraction-new_fraction)
                    moving_states   += pcr.max(0.0, old_fraction-new_fraction) * vars(self.landCoverObj[coverType])[var]
                
                previous_state = pcr.scalar(0.0)
                rescaled_state = pcr.scalar(0.0)
                
                # correcting states
                for coverType in self.coverTypes:
                    
                    old_states   = vars(self.landCoverObj[coverType])[var]
                    old_fraction = self.landCoverObj[coverType].previousFracVegCover
                    new_fraction = self.landCoverObj[coverType].fracVegCover
                    
                    correction   = moving_states *\
                                   vos.getValDivZero( pcr.max(0.0, new_fraction - old_fraction),\
                                                      moving_fraction, vos.smallNumber )
                     
                    new_states   = pcr.ifthenelse(new_fraction > old_fraction, 
                                   vos.getValDivZero( 
                                   old_states * old_fraction + correction, \
                                   new_fraction, vos.smallNumber), old_states) 
                    
                    new_states   = pcr.ifthenelse(new_fraction > 0.0, new_states, pcr.scalar(0.0))
                    
                    vars(self.landCoverObj[coverType])[var] = new_states
                    
                    previous_state += old_fraction * old_states
                    rescaled_state += new_fraction * new_states
                
                # check and make sure that previous_state == rescaled_state
                check_map = previous_state - rescaled_state
                a,b,c = vos.getMinMaxMean(check_map)
                threshold = 1e-5
                if abs(a) > threshold or abs(b) > threshold:
                    logger.warning("Error in transfering states (due to dynamic in land cover fractions) ... Min %f Max %f Mean %f" %(a,b,c))
                else:     
                    logger.info("Successful in transfering states (after change in land cover fractions) ... Min %f Max %f Mean %f" %(a,b,c))
        
        # for the last day of the year, we have to save the previous land cover fractions (to be considered in the next time step) 
        if self.dynamicIrrigationArea and self.includeIrrigation and currTimeStep.isLastDayOfYear:     
            # save the current state of fracVegCover
            for coverType in self.coverTypes:\
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].fracVegCover

    def land_surface_hydrology_update(self, meteo, groundwater, routing, currTimeStep):
        
        # calculate cell fraction influenced by capillary rise:
        self.capRiseFrac = self.calculateCapRiseFrac(groundwater, routing, currTimeStep)
            
        # update (loop per each land cover type):
        # - note this will exclude the calculations of potential evaporation, interception and snow
        for coverType in self.coverTypes:
            
            logger.info("Updating land cover: "+str(coverType))
            
            # note that for calculating irrigation losses, we need information about irrigation efficiency
            if coverType.startswith('irr') and self.includeIrrigation:
                self.landCoverObj[coverType].irrigationEfficiencyUsed = self.water_demand.water_demand_irrigation[coverType].irrigationEfficiency
            
            # calculate the hydrology model part
            self.landCoverObj[coverType].land_surface_hydrology_update_for_every_lc(self.capRiseFrac, currTimeStep, groundwater, self.satisfied_irrigation_water_height[coverType], self.reducedCapRise)
        
        # first, we set all aggregated values/variables to zero: 
        for var in self.aggrVars: vars(self)[var] = pcr.scalar(0.0)
        #
        # get or calculate the values of all aggregated values/variables
        for coverType in self.coverTypes:
            # calculate the aggregrated or global landSurface values: 
            for var in self.aggrVars:
                vars(self)[var] += \
                     self.landCoverObj[coverType].fracVegCover * vars(self.landCoverObj[coverType])[var]
                     
        # total storages (unit: m3) in the entire landSurface module
        if self.numberOfSoilLayers == 2: self.totalSto = \
                        self.snowCoverSWE + self.snowFreeWater + self.interceptStor +\
                        self.topWaterLayer +\
                        self.storUpp +\
                        self.storLow
        #
        if self.numberOfSoilLayers == 3: self.totalSto = \
                        self.snowCoverSWE + self.snowFreeWater + self.interceptStor +\
                        self.topWaterLayer +\
                        self.storUpp000005 + self.storUpp005030 +\
                        self.storLow030150
        
        # old-style reporting (this is useful for debugging)
        self.old_style_land_surface_reporting(currTimeStep)


    def old_style_land_surface_reporting(self,currTimeStep):
        
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
                          pcr.pcr2numpy(self.__getattribute__(var),vos.MV),\
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
                          pcr.pcr2numpy(self.__getattribute__(var+'MonthTot'),\
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
                          pcr.pcr2numpy(self.__getattribute__(var+'MonthAvg'),\
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
                          pcr.pcr2numpy(self.__getattribute__(var),vos.MV),\
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
                          pcr.pcr2numpy(self.__getattribute__(var+'AnnuaTot'),\
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
                          pcr.pcr2numpy(self.__getattribute__(var+'AnnuaAvg'),\
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
                          pcr.pcr2numpy(self.__getattribute__(var),vos.MV),\
                                         timeStamp,currTimeStep.annuaIdx-1)
