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

import datetime
import subprocess
import os
import types
import glob

from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import groundwater

#~ import waterBodies_for_modflow as waterBodies
import waterBodies as waterBodies
# Since 22 Nov 2017, I have started to remove "waterBodies_for_modflow.py".

import virtualOS as vos
from ncConverter import *

class GroundwaterModflow(object):
    
    def getState(self):
        result = {}
        
        # groundwater head (unit: m) for all layers
        for i in range(1, self.number_of_layers+1):
            var_name = 'groundwaterHeadLayer'+str(i)
            result[var_name] = vars(self)[var_name]
        
        return result

    def getGroundwaterDepth(self):
        result = {}
        
        # groundwater head (unit: m) for all layers
        for i in range(1, self.number_of_layers+1):
            var_name = 'groundwaterDepthLayer'+str(i)
            headname = 'groundwaterHeadLayer' +str(i)
            result[var_name] = self.dem_average - vars(self)[headname]

        return result

    def getVariableValuesForPCRGLOBWB(self):
        
        result = {}
        
        result['relativeGroundwaterHead'] = pcr.ifthen(self.landmask, self.relativeGroundwaterHead) 
        result['baseflow']                = pcr.ifthen(self.landmask, self.baseflow)
        result['storGroundwater']         = pcr.ifthen(self.landmask, self.storGroundwater)
        
        return result

    def __init__(self, iniItems, landmask, groundwater_pcrglobwb = None):
        object.__init__(self)
        
        # configuration from the ini file
        self.iniItems = iniItems

        self.landmask = landmask
        self.cloneMap = self.iniItems.cloneMap
        self.tmpDir   = self.iniItems.tmpDir
        self.inputDir = self.iniItems.globalOptions['inputDir']

        # number of modflow layers:
        self.number_of_layers = int(iniItems.modflowParameterOptions['number_of_layers'])

        # making temporary directory for modflow calculation and make sure that the directory is empty
        self.tmp_modflow_dir = "tmp_modflow/"
        if 'tmp_modflow_dir' in self.iniItems.globalOptions.keys():
            self.tmp_modflow_dir = self.iniItems.globalOptions['tmp_modflow_dir']
        self.tmp_modflow_dir = vos.getFullPath(self.tmp_modflow_dir, \
                                               self.iniItems.globalOptions['outputDir'])+"/"
        if os.path.exists(self.tmp_modflow_dir):
            shutil.rmtree(self.tmp_modflow_dir)
        os.makedirs(self.tmp_modflow_dir)

        # go to the temporary directory for the modflow calculation (so that all calculation will be saved in that folder)  
        os.chdir(self.tmp_modflow_dir)
        # In the future, this is not necessary anymore, given the new option provided by Oliver.  
    

        # option for the daily modflow (and daily coupling between pcrglobwb and modflow)
        if isinstance(groundwater_pcrglobwb, types.NoneType):
            self.online_daily_coupling_between_pcrglobwb_and_modflow = False
        else:
            self.online_daily_coupling_between_pcrglobwb_and_modflow = groundwater_pcrglobwb.coupleToDailyMODFLOW
        # - if True, the stress period of MODFLOW is daily.    
        # - if False, the (default) MODFLOW stress period is monthly. This setting is also used for an offline MODFLOW run. 
        #
        # TODO: We should introduce a possibility to run an offline daily stress period of MODFLOW.     


        # option for the online coupling purpose
        self.online_coupling = False
        if self.online_daily_coupling_between_pcrglobwb_and_modflow:
            self.online_coupling = True
        else:
            if 'globalMergingAndModflowOptions' in self.iniItems.allSections:
                self.online_coupling = self.iniItems.globalMergingAndModflowOptions['online_coupling_between_pcrglobwb_and_modflow'] == "True"

        # option to exclude surface water (river) infiltration (to groundwater bodies)
        self.exclude_river_infiltration = False
        # - for daily online coupling, we exclude river infiltration as it will be calculated within the routing module
        if self.online_daily_coupling_between_pcrglobwb_and_modflow: self.exclude_river_infiltration = True

        # topography properties: read several variables from a netcdf file
        if 'topographyNC' not in self.iniItems.modflowParameterOptions.keys() or\
            self.iniItems.modflowParameterOptions['topographyNC'] == "Default":
            msg = "Topography properties (e.g. DEM) are taken from the 'landSurfaceOptions' of the ini/configuration file."
            logger.info(msg)
            self.iniItems.modflowParameterOptions['topographyNC'] = self.iniItems.landSurfaceOptions['topographyNC']
        for var in ['dem_minimum', 'dem_average']:
            vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['topographyNC'], \
                                                                var, self.cloneMap)
            vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

        # channel properties: read several variables from the netcdf file
        if 'channelNC' in self.iniItems.modflowParameterOptions.keys():
            for var in ['gradient', 'bankfull_width',
                        'bankfull_depth', 'dem_floodplain', 'dem_riverbed']:
                vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['channelNC'], \
                                                                    var, self.cloneMap)
                vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
        else:
            msg = 'The "channelNC" file is NOT defined in the "modflowParameterOptions" of the configuration file.'
            logger.info(msg)
            logger.warning(msg)
            pass
            
        
        minimumChannelWidth = 0.0
        if 'minimumChannelWidth' in self.iniItems.modflowParameterOptions.keys():
            minimumChannelWidth = float(self.iniItems.modflowParameterOptions['minimumChannelWidth'])
        elif 'routingOptions' in self.iniItems.allSections and 'minimumChannelWidth' in self.iniItems.routingOptions.keys():
            msg = 'The minimumChannelWidth is taken from the "routingOptions" of the ini/configuration file.'
            logger.info(msg)
            minimumChannelWidth = float(self.iniItems.routingOptions['minimumChannelWidth'])
        self.bankfull_width = pcr.max(minimumChannelWidth, self.bankfull_width)
        
        if 'minimumChannelGradient' in self.iniItems.modflowParameterOptions.keys():
            minimumChannelGradient = float(self.iniItems.modflowParameterOptions['minimumChannelGradient'])
        elif 'routingOptions' in self.iniItems.allSections and 'minimumChannelGradient' in self.iniItems.routingOptions.keys():
            msg = 'The minimumChannelGradient is taken from the "routingOptions" of the ini/configuration file.'
            logger.info(msg)
            minimumChannelGradient = float(self.iniItems.routingOptions['minimumChannelGradient'])
        else:
            msg  = 'The minimumChannelGradient is not defined in the ini/configuration file. '
            msg += 'This value is set to 0.00005'
            logger.info(msg)
            minimumChannelGradient = 0.00005
        self.gradient = pcr.ifthen(self.landmask, \
                        pcr.max(minimumChannelGradient, pcr.cover(self.gradient, minimumChannelGradient)))

        # coefficient of Manning
        if 'manningsN' not in self.iniItems.modflowParameterOptions.keys():
            msg = 'The manning coefficient used to convert discharge to water level is taken from the "routingOptions" of the ini/configuration file.'
            logger.info(msg)
            self.iniItems.modflowParameterOptions['manningsN'] = self.iniItems.routingOptions['manningsN']
        self.manningsN = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['manningsN'],\
                                             self.cloneMap,self.tmpDir,self.inputDir)
                

        # cellAreaMap and lddMap 
        if 'routingOptions' not in self.iniItems.allSections: 
            self.iniItems.routingOptions = {}
            self.iniItems.routingOptions['lddMap'] = self.iniItems.modflowParameterOptions['lddMap']
            self.iniItems.routingOptions['cellAreaMap'] = self.iniItems.modflowParameterOptions['cellAreaMap']
            
        # cell area (unit: m2)
        self.cellAreaMap = vos.readPCRmapClone(self.iniItems.routingOptions['cellAreaMap'],
                                               self.cloneMap, self.tmpDir, self.inputDir)
        self.cellAreaMap = pcr.cover(self.cellAreaMap, 0.0)

        # ldd
        self.lddMap = vos.readPCRmapClone(self.iniItems.routingOptions['lddMap'],
                                          self.cloneMap,self.tmpDir,self.inputDir,True)

        # correcting lddMap
        self.lddMap = pcr.ifthen(pcr.scalar(self.lddMap) > 0.0, self.lddMap)
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        self.lddMap = pcr.lddmask(self.lddMap, self.landmask)


        self.convert_channel_discharge_to_water_level = False
        # This conversion is definitely needed for a run with monthly MODFLOW stress period.
        if self.online_daily_coupling_between_pcrglobwb_and_modflow == False: self.convert_channel_discharge_to_water_level = True
        
        
        # configuration for lakes and reservoirs
        if 'waterBodyInputNC' not in self.iniItems.modflowParameterOptions.keys():
            msg = 'The "waterBodyInputNC" option is taken from the "routingOptions" of the ini/configuration file.'
            logger.info(msg)
            self.iniItems.modflowParameterOptions['waterBodyInputNC'] = self.iniItems.routingOptions['waterBodyInputNC']
        if 'onlyNaturalWaterBodies' not in self.iniItems.modflowParameterOptions.keys():
            msg = 'The "onlyNaturalWaterBodies" option is taken from the "routingOptions" of the ini/configuration file.'
            logger.info(msg)
            self.iniItems.modflowParameterOptions['onlyNaturalWaterBodies'] = self.iniItems.routingOptions['onlyNaturalWaterBodies']
        #
        # - default option to exclude/include reservoirs
        self.onlyNaturalWaterBodies = False
        if self.iniItems.modflowParameterOptions['onlyNaturalWaterBodies'] == "True": self.onlyNaturalWaterBodies = True
        #
        # PS: WaterBodies will be initiated within the method "modflow_simulation".
        
        
        # option to exclude river infiltration
        self.minimumWidthOfRiversWithInfiltration = 0.0
        if 'minimumWidthOfRiversWithInfiltration' in self.iniItems.modflowParameterOptions.keys():
            msg = 'Exclude river infiltration (RIV behaves as DRN) for rivers with widths smaller than: ' + self.iniItems.modflowParameterOptions['minimumWidthOfRiversWithInfiltration']
            logger.info(msg)
            self.minimumWidthOfRiversWithInfiltration = pcr.cover(
                                                        vos.readPCRmapClone(self.iniItems.modflowParameterOptions['minimumWidthOfRiversWithInfiltration'],
                                                                            self.cloneMap, self.tmpDir, self.inputDir), 0.0)
                                                                            

        # TODO: Refactor the configuration file, particularly to merge some double fields defined in the "routingOptions" and "modflowParameterOptions"
        # - One of the ideas is to keep all channel properties in the routingOptions (so that ini files for offline modflow runs will still need them). 
        # - Also, we can keep/put the topography properties (e.g. 'topographyNC') in the "landSurfaceOptions".


        # extent of mountainous region
        # TODO: Define this from the ini/configuration file
        mountainous_thresh  = 50.
        self.mountainous_extent  = pcr.cover(\
                                   pcr.ifthen((self.dem_average - self.dem_floodplain) > mountainous_thresh, pcr.boolean(1.0)), pcr.boolean(0.0))


        # cell dimensions: length, width, diagonal, etc. (in various units) 
        self.get_cell_dimensions()
        
        # estimate channel length (m) - needed for calculating river bed conductance
        self.channelLength = self.cell_diagonal


        # obtain default groundwater properties based on PCR-GLOBWB - this is needed for an offline MODFLOW run
        if groundwater_pcrglobwb == None:
            msg = "Obtain the default groundwater properties based on PCR-GLOBWB setting."
            logger.info(msg)
            groundwater_pcrglobwb = groundwater.Groundwater(self.iniItems, self.landmask, None, False)
        # - default groundwater properties
        self.kSatAquifer               = groundwater_pcrglobwb.kSatAquifer
        self.specificYield             = groundwater_pcrglobwb.specificYield
        self.recessionCoeff            = groundwater_pcrglobwb.recessionCoeff
        self.totalGroundwaterThickness = groundwater_pcrglobwb.totalGroundwaterThickness
        self.productive_aquifer        = groundwater_pcrglobwb.productive_aquifer
        self.riverBedConductivity      = groundwater_pcrglobwb.riverBedConductivity
        self.riverBedThickness         = groundwater_pcrglobwb.riverBedThickness   
        self.bed_resistance            = groundwater_pcrglobwb.bed_resistance

        # Perform extrapolation for the following variables:
        for var in ['kSatAquifer',\
                    'specificYield',\
                    'recessionCoeff',\
                    'totalGroundwaterThickness',\
                    ]:
            vars(self)[var] = pcr.ifthen(self.landmask, vars(self)[var])
            vars(self)[var] = pcr.cover(pcr.cover(vars(self)[var], pcr.windowaverage(vars(self)[var], 0.5)), vars(groundwater_pcrglobwb)[var])
            #~ pcr.aguila(vars(self)[var])
            #~ raw_input("Press Enter to continue...")

        
        #~ # remove isolated cells - a productive aquifer cell must be surrounded by at least a minimum number of cells - OPTIONAL (NOT RECOMMENDED) # TODO: Find a better method that this one. 
        #~ if "minimizeIsolatedAquiferCellsUnderGroundwaterAbstraction" in iniItems.modflowParameterOptions.keys() and iniItems.modflowParameterOptions['minimizeIsolatedAquiferCellsUnderGroundwaterAbstraction'] == "True": 
            #~ pcr.aguila(pcr.ifthen(self.landmask, self.productive_aquifer))
            #~ raw_input("Press Enter to continue...")
            #~ minimum_surrounding_cells = 3.0
            #~ self.productive_aquifer = pcr.ifthenelse(pcr.window4total(pcr.scalar(self.productive_aquifer)) >= minimum_surrounding_cells, self.productive_aquifer, pcr.boolean(0.0))
            #~ self.productive_aquifer = pcr.ifthenelse(pcr.window4total(pcr.scalar(self.productive_aquifer)) >= minimum_surrounding_cells, self.productive_aquifer, pcr.boolean(0.0))
            #~ pcr.aguila(pcr.ifthen(self.landmask, self.productive_aquifer))
            #~ raw_input("Press Enter to continue...")

        ##############################################################################################################################################
        # confining layer thickness (for more than one layer)
        self.usePreDefinedConfiningLayer = False
        if self.number_of_layers > 1 and self.iniItems.modflowParameterOptions['usePreDefinedConfiningLayer'] == "True":
            self.usePreDefinedConfiningLayer = True
            # confining layer thickness (unit: m)
            self.confiningLayerThickness = pcr.cover(\
                                           vos.readPCRmapClone(self.iniItems.modflowParameterOptions['confiningLayerThickness'],\
                                                               self.cloneMap, self.tmpDir, self.inputDir), 0.0)
            
            # maximum confining layer vertical conductivity (unit: m/day)
            self.maximumConfiningLayerVerticalConductivity = pcr.cover(\
                                           vos.readPCRmapClone(self.iniItems.modflowParameterOptions['maximumConfiningLayerVerticalConductivity'],\
                                                               self.cloneMap, self.tmpDir, self.inputDir), 0.0)
            # confining layer resistance (unit: day)
            self.maximumConfiningLayerResistance = pcr.cover(\
                                                   vos.readPCRmapClone(self.iniItems.modflowParameterOptions['maximumConfiningLayerResistance'],\
                                                                       self.cloneMap, self.tmpDir, self.inputDir), 0.0)
        ##############################################################################################################################################
        


        #####################################################################################################################################################
        # option to ignore capillary rise
        self.ignoreCapRise = False
        if 'ignoreCapRise' in self.iniItems.modflowParameterOptions.keys() and \
            self.iniItems.modflowParameterOptions['ignoreCapRise'] == "True": self.ignoreCapRise = True
        if self.ignoreCapRise:    
            msg = "Negative groundwater recharge is ignored (set to zero)."
            logger.info(msg)
        #####################################################################################################################################################

        

        #####################################################################################################################################################
        # assumption for the thickness (m) of accessible groundwater
        # - Note that this assumption value does not affect the modflow calculation. The values is needed merely for reporting "accesibleGroundwaterVolume".
        if 'accesibleDepth' in self.iniItems.modflowParameterOptions.keys() and \
                               self.iniItems.modflowParameterOptions['accesibleDepth'] != "Default":
            accesibleDepth = float(self.iniItems.modflowParameterOptions['accesibleDepth'])
        else:
            msg  = 'The "accesibleDepth" option is not defined in the "modflowParameterOptions" of the ini/configuration file. '
            msg += 'This value is set to 1000. (m).'
            logger.info(msg)
            accesibleDepth = 1000.0
        self.max_accesible_elevation = self.dem_average - accesibleDepth
        

        # list of the convergence criteria for HCLOSE (unit: m)
        # - Deltares default's value is 0.001 m                         # check this value with Jarno
        #~ self.criteria_HCLOSE = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]  
        #~ self.criteria_HCLOSE = [0.001, 0.01, 0.1, 0.5, 1.0]  
        #~ self.criteria_HCLOSE = [0.001, 0.01, 0.1, 0.15, 0.2, 0.5, 1.0]
        #~ self.criteria_HCLOSE = [0.001, 0.005, 0.01, 0.1, 0.15, 0.2, 0.5, 1.0]
        #~ self.criteria_HCLOSE = [0.001, 0.005, 0.01, 0.1, 0.2, 0.5, 1.0]
        #~ self.criteria_HCLOSE = [0.001, 0.005, 0.01, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0]
        #~ self.criteria_HCLOSE = [0.001, 0.01, 0.1, 0.25]
        self.criteria_HCLOSE = [0.001, 0.01, 0.1]
        #~ self.criteria_HCLOSE = [0.01, 0.1, 0.15, 0.2, 0.5, 1.0]
        #~ self.criteria_HCLOSE = [0.5, 1.0]
        #~ self.criteria_HCLOSE = [0.001]
        #
        if "HCLOSE" in self.iniItems.modflowParameterOptions.keys():
            self.criteria_HCLOSE = list(set(self.iniItems.modflowParameterOptions['HCLOSE'].split(",")))
        #
        self.criteria_HCLOSE = sorted(self.criteria_HCLOSE)
        


        # list of the convergence criteria for RCLOSE (unit: m3)
        # - Deltares default's value for their 25 and 250 m resolution models is 10 m3  # check this value with Jarno
        cell_area_assumption = self.verticalSizeInMeter * float(pcr.cellvalue(pcr.mapmaximum(self.horizontalSizeInMeter),1)[0])
        #~ self.criteria_RCLOSE = [10., 100., 10.* cell_area_assumption/(250.*250.), 10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(250.*250.), 10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.), 10000.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(25.*25.), 10000.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [1000., 10.* cell_area_assumption/(25.*25.), 1000.* cell_area_assumption/(25.*25.), 100000.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [1000., 10.* cell_area_assumption/(25.*25.), 1000.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [1000., 1000.* cell_area_assumption/(25.*25.)]
        self.criteria_RCLOSE = [10000., 10.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [1000.]
        self.criteria_RCLOSE = sorted(self.criteria_RCLOSE)
        #
        if "RCLOSE" in self.iniItems.modflowParameterOptions.keys():
            self.criteria_RCLOSE = list(set(self.iniItems.modflowParameterOptions['RCLOSE'].split(",")))
        #
        self.criteria_RCLOSE = sorted(self.criteria_RCLOSE)


        # DAMP parameter for PCG solver
        self.parameter_DAMP_default = [0.75]
        if "DAMP" in self.iniItems.modflowParameterOptions.keys():
            self.parameter_DAMP_default = list(set(self.iniItems.modflowParameterOptions['DAMP'].split(",")))
        # - for steady state simulation 
        self.parameter_DAMP_steady_state_default = self.parameter_DAMP_default
        if "DAMP_steady_state" in self.iniItems.modflowParameterOptions.keys():
            self.parameter_DAMP_steady_state_default = list(set(self.iniItems.modflowParameterOptions['DAMP_steady_state'].split(",")))


        # minimum and maximum transmissivity values (unit: m2/day)
        if 'minimumTransmissivity' in self.iniItems.modflowParameterOptions.keys() and\
           (self.iniItems.modflowParameterOptions['minimumTransmissivity'] not in ["None", "False", "Default"]):
            self.minimumTransmissivity = float(self.iniItems.modflowParameterOptions['minimumTransmissivity'])
        else:
            msg  = 'The "minimumTransmissivity" option is not defined in the "modflowParameterOptions" of the ini/configuration file. '
            msg += 'This value is set to 10.0 (m2.day-1).'
            logger.info(msg)
            self.minimumTransmissivity = 10.0        # assumption used by Deltares
        if 'maximumTransmissivity' in self.iniItems.modflowParameterOptions.keys() and\
           (self.iniItems.modflowParameterOptions['maximumTransmissivity'] not in ["None", "False", "Default"]):
            self.maximumTransmissivity = float(self.iniItems.modflowParameterOptions['maximumTransmissivity'])
        elif self.iniItems.modflowParameterOptions['minimumTransmissivity'] == "Default":
            msg  = 'The "maximumTransmissivity" option is not defined in the "modflowParameterOptions" of the ini/configuration file. '
            msg += 'The default value is used: 100000.0 (m2.day-1).'
            logger.info(msg)
            self.maximumTransmissivity = 100000.0    # ridiculosly high (for 20 m/day with the thickness = 5 km)
        else:
            msg  = 'The "maximumTransmissivity" option is not defined in the "modflowParameterOptions" of the ini/configuration file. '
            msg += 'This value is set to 10000000000000000000000000000.0 (m2.day-1).'
            logger.info(msg)
            self.maximumTransmissivity = 10000000000000000000000000000.0  # really really ridiculosly high



        # initiate somes variables/objects/classes to None
        # - lakes and reservoirs (they will be constant for the entire year, and they will change at the beginning (first day) of the year)
        self.WaterBodies = None
        # - surface water bed conductance and elevation (they also change at the beginning of the year only)
        self.surface_water_bed_elevation = None
        self.bed_conductance = None


        # initiate pcraster modflow object to None
        self.pcr_modflow = None

        # option to perform only steady state MODFLOW simulation (offline approach only)
        self.steady_state_only = iniItems.steady_state_only
        # TODO: FIX THIS, put this option in the ini/configuration file.
        

        # the following condition is needed if we have to convert the unit of recharge and abstraction (ONLY for a transient simulation) 
        self.valuesRechargeAndAbstractionInMonthlyTotal = False
        if self.steady_state_only == False and\
           "modflowTransientInputOptions" in self.iniItems.allSections and\
           'valuesRechargeAndAbstractionInMonthlyTotal' in self.iniItems.modflowTransientInputOptions.keys():
            if self.iniItems.modflowTransientInputOptions['valuesRechargeAndAbstractionInMonthlyTotal'] == "True":
               msg = "Recharge and abstraction values in monthly total and must be converted to daily values."
               logger.info(msg)
               self.valuesRechargeAndAbstractionInMonthlyTotal = True

        
        # initiate old style reporting (this is usually used for debugging process)
        self.initiate_old_style_reporting(iniItems)
        
        # option to make backup of modflow files
        self.make_backup_of_modflow_files = False
        if "make_backup_of_modflow_files" in self.iniItems.reportingOptions.keys() and\
           self.iniItems.reportingOptions["make_backup_of_modflow_files"] == "True": self.make_backup_of_modflow_files = True
        
        # a boolean status to reduce log info file
        self.log_to_info = True   

        # option to activate water balance check
        self.debugWaterBalance = True
        

        # option to read channelStorageInput (m3) based on surfaceWaterStorageInput (m)
        self.usingSurfaceWaterStorageInput = False        
        if 'modflowTransientInputOptions' in self.iniItems.allSections and\
           'surfaceWaterStorageInputNC' in self.iniItems.modflowTransientInputOptions.keys() and\
           'channelStorageInputNC' in self.iniItems.modflowTransientInputOptions.keys() and\
           self.iniItems.modflowTransientInputOptions['channelStorageInputNC'] == "surfaceWaterStorageInputNC":
            msg = "The channel storage input (for transient simulation) will be based on surfaceWaterStorageInputNC (multiplied by cellArea)."
            logger.info(msg)
            self.usingSurfaceWaterStorageInput = True


        # option to correcting recharge with built-up area
        self.using_built_up_area_correction_for_recharge = False
        if 'nc_file_for_built_up_area_correction_for_recharge' in self.iniItems.groundwaterOptions.keys() and\
           self.iniItems.groundwaterOptions['nc_file_for_built_up_area_correction_for_recharge'] != "None":
            msg = "Using built-up area fractions for correcting recharge."
            logger.info(msg)
            self.using_built_up_area_correction_for_recharge = True
        # NOTE: For online coupling, YOU CANNOT USE THIS.    



    def get_cell_dimensions(self):

        cellSizeInArcMin = np.round(pcr.clone().cellSize()*60.) 
        if pcr.clone().cellSize()*60. < 1.0:
            cellSizeInArcMin = np.round(pcr.clone().cellSize()*60., decimals = 2)
        
        self.verticalSizeInMeter   = cellSizeInArcMin*1852.                            
        self.horizontalSizeInMeter = self.cellAreaMap / self.verticalSizeInMeter

        self.cell_diagonal = ((self.horizontalSizeInMeter)**(2)+\
                              (self.verticalSizeInMeter)**(2))**(0.5)

        
        # The following lists are needed for DELR and DELC    - NOT USED YET
        self.listOfHorizontalSizeInMeter = ((pcr.pcr2numpy(self.horizontalSizeInMeter, vos.MV)[0,:])).tolist()
        self.listOfVerticalSizeInMeter = ((pcr.pcr2numpy(self.cellAreaMap/self.horizontalSizeInMeter, vos.MV)[0,:])).tolist()

        
    def initiate_modflow(self):

        logger.info("Initializing pcraster modflow.")
        
        # TODO: removing all previous pcraster modflow files:
        
        # initialise pcraster modflow
        self.pcr_modflow = pcr.initialise(pcr.clone())
        
        # setup the DIS package specifying the grids/layers used for the groundwater model
        # - Note the layer specification must start with the bottom layer (layer 1 is the lowermost layer)
        if self.number_of_layers == 1: self.set_grid_for_one_layer_model()
        if self.number_of_layers == 2: self.set_grid_for_two_layer_model()
         
        #~ # TODO: set DELR and DELC in meter. PS: For this, you also have to change the corrections in RCH, VCONT, etc.
        #~ self.pcr_modflow.setColumnWidth(self.listOfHorizontalSizeInMeter)
        #~ self.pcr_modflow.setRowWidth(self.listOfHorizontalSizeInMeter)
        
        # specification for the boundary condition (ibound)
        # - active cells only in landmask
        # - constant head for outside the landmask
        ibound = pcr.ifthen(self.landmask, pcr.nominal(1))
        ibound = pcr.cover(ibound, pcr.nominal(-1))
        self.ibound = ibound
        for i in range(1, self.number_of_layers+1): self.pcr_modflow.setBoundary(self.ibound, i)
        
        # setup the BCF package 
        if self.number_of_layers == 1: self.set_bcf_for_one_layer_model()
        if self.number_of_layers == 2: self.set_bcf_for_two_layer_model()

        # save some pcraster static maps
        if self.log_to_info:
            self.save_some_pcraster_static_maps()
            # after the first call, we do not have to log it anymore
            self.log_to_info = False

    def set_grid_for_one_layer_model(self):

        # grid specification - one layer model
        top    = self.dem_average
        bottom = top - self.totalGroundwaterThickness
        self.pcr_modflow.createBottomLayer(bottom, top)
        
        # make the following value(s) available for the other modules/methods:
        self.thickness_of_layer_1 = top - bottom
        self.total_thickness = self.thickness_of_layer_1
        self.bottom_layer_1 = bottom

    def set_grid_for_two_layer_model(self):

        # grid specification - two layer model
        
        # - top upper layer is elevation
        top_layer_2          = self.dem_average
        # - thickness of layer 2 is at least 10% of totalGroundwaterThickness
        bottom_layer_2       = self.dem_average - 0.10 * self.totalGroundwaterThickness
        #~ # - thickness of layer 2 should be until 5 m below the river bed - NOT NEEDED (this creates artefacts in low resolution models, e.g. >= 5 arcmin resolution)
        #~ bottom_layer_2    = pcr.min(self.dem_riverbed - 5.0, bottom_layer_2)
        # - make sure that the minimum thickness of layer 2 is at least 0.1 m
        thickness_of_layer_2 = pcr.max(0.1, top_layer_2 - bottom_layer_2)
        bottom_layer_2       = top_layer_2 - thickness_of_layer_2
        # - thickness of layer 1 is at least 5.0 m
        thickness_of_layer_1 = pcr.max(5.0, self.totalGroundwaterThickness - thickness_of_layer_2)
        bottom_layer_1       = bottom_layer_2 - thickness_of_layer_1
        
        if self.usePreDefinedConfiningLayer:
            # make sure that totalGroundwaterThickness is at least 50 m thicker than confiningLayerThickness
            total_thickness = pcr.max(self.totalGroundwaterThickness, self.confiningLayerThickness + 50.0)
            # - top upper layer is elevation
            top_layer_2     = self.dem_average
            # - thickness of layer 2 is based on the predefined confiningLayerThickness
            bottom_layer_2       = self.dem_average - self.confiningLayerThickness
            #~ # - thickness of layer 2 should be until 5 m below the river bed elevation # THIS IS NOT NEEDED
            #~ bottom_layer_2       = pcr.min(self.dem_riverbed - 5.0, bottom_layer_2)    # THIS IS NOT NEEDED
            # - make sure that the minimum thickness of layer 2 is at least 0.1 m
            thickness_of_layer_2 = pcr.max(0.1, top_layer_2 - bottom_layer_2)
            bottom_layer_2       = top_layer_2 - thickness_of_layer_2
            # - thickness of layer 1 is at least 5.0 m
            thickness_of_layer_1 = pcr.max(5.0, total_thickness - thickness_of_layer_2)
            bottom_layer_1       = bottom_layer_2 - thickness_of_layer_1
        
        # set grid in modflow
        self.pcr_modflow.createBottomLayer(bottom_layer_1, bottom_layer_2)
        self.pcr_modflow.addLayer(top_layer_2)
        
        # make the following value(s) available for the other modules/methods:
        self.thickness_of_layer_1 = thickness_of_layer_1
        self.thickness_of_layer_2 = thickness_of_layer_2
        self.total_thickness = self.thickness_of_layer_1 + self.thickness_of_layer_2
        self.bottom_layer_1 = bottom_layer_1
        self.bottom_layer_2 = bottom_layer_2
        self.top_layer_2    = top_layer_2
        
        #~ # report elevation in pcraster map
        #~ pcr.report(pcr.ifthen(self.landmask, self.top_layer_2), "top_uppermost_layer.map")
        #~ pcr.report(pcr.ifthen(self.landmask, self.bottom_layer_2), "bottom_uppermost_layer.map")
        #~ pcr.report(pcr.ifthen(self.landmask, self.bottom_layer_1), "bottom_lowermost_layer.map")

    def set_bcf_for_one_layer_model(self):

        # specification for storage coefficient (BCF package)
        # - correction due to the usage of lat/lon coordinates
        primary = pcr.cover(self.specificYield * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary = pcr.max(1e-10, primary)
        secondary = primary                                            # dummy values as we used the layer type 00
        self.pcr_modflow.setStorage(primary, secondary, 1)

        # specification for horizontal conductivities (BCF package)
        horizontal_conductivity = self.kSatAquifer # unit: m/day
        # set the minimum value for transmissivity
        horizontal_conductivity = pcr.max(self.minimumTransmissivity, \
                                          horizontal_conductivity * self.total_thickness) / self.total_thickness
        # set the maximum value for transmissivity
        horizontal_conductivity = pcr.min(self.maximumTransmissivity, \
                                          horizontal_conductivity * self.total_thickness) / self.total_thickness

        # specification for horizontal conductivities (BCF package)
        vertical_conductivity   = horizontal_conductivity               # dummy values, as one layer model is used

        #~ # for areas with ibound <= 0, we set very high horizontal conductivity values:             # TODO: Check this, shall we implement this?
        #~ horizontal_conductivity = pcr.ifthenelse(self.ibound > 0, horizontal_conductivity, \
                                                   #~ pcr.mapmaximum(horizontal_conductivity))

        # set BCF package
        self.pcr_modflow.setConductivity(00, horizontal_conductivity, \
                                             vertical_conductivity, 1)              

        # make the following value(s) available for the other modules/methods:
        self.storage_coefficient_1 = self.specificYield

    def set_storages_for_two_layer_model(self):

        msg = "Set storage coefficients for the upper and bottom layers (including lat/lon correction)."
        if self.log_to_info: logger.info(msg)

        # adjusting factor 
        adjust_factor = 1.00
        if 'linear_multiplier_for_storage_coefficients' in self.iniItems.modflowParameterOptions.keys():
            linear_multiplier_for_storage_coefficients = float(self.iniItems.modflowParameterOptions['linear_multiplier_for_storage_coefficients'])
            adjust_factor                              = linear_multiplier_for_storage_coefficients
        msg = 'Adjustment factor: ' + str(adjust_factor)  
        if self.log_to_info: logger.info(msg)
        
        # minimum and maximum values of storage coefficients
        minimum_storage_coefficient = 1e-10
        maximum_storage_coefficient = 0.500
        msg = 'The minimum storage coefficient value is limited to (-) ' + str(minimum_storage_coefficient)  
        if self.log_to_info: logger.info(msg)
        msg = 'The maximum storage coefficient value is limited to (-) ' + str(maximum_storage_coefficient)  
        if self.log_to_info: logger.info(msg)

        msg = "Set storage coefficient for the upper layer (including lat/lon correction)."
        if self.log_to_info: logger.info(msg)
        # layer 2 (upper layer) - storage coefficient
        # - default values
        self.storage_coefficient_2  = self.specificYield
        # - if specifically defined in the configuration/ini file
        if "confiningLayerPrimaryStorageCoefficient" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['confiningLayerPrimaryStorageCoefficient'] != "Default":
            msg = "Set storage coefficient for the confing layer based on the input in 'confiningLayerPrimaryStorageCoefficient'."
            if self.log_to_info: logger.info(msg)
            confiningLayerPrimaryStorageCoefficient = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['confiningLayerPrimaryStorageCoefficient'], \
                                                                          self.cloneMap, self.tmpDir, self.inputDir)
            # - only for cells identified as the confining layer
            confiningLayerPrimaryStorageCoefficient = pcr.ifthen(self.confiningLayerThickness > 0.0, confiningLayerPrimaryStorageCoefficient)
            #
            # - cover the rest, using the default value
            self.storage_coefficient_2 = pcr.cover(confiningLayerPrimaryStorageCoefficient, self.storage_coefficient_2)
            

        # adjusting factor and set minimum and maximum values to keep values realistics
        self.storage_coefficient_2  = adjust_factor * self.storage_coefficient_2
        self.storage_coefficient_2  = pcr.min(maximum_storage_coefficient, pcr.max(minimum_storage_coefficient, self.storage_coefficient_2))
        
        # - correction due to the usage of lat/lon coordinates
        primary_2   = pcr.cover(self.storage_coefficient_2 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary_2   = pcr.max(1e-20, primary_2)

        # - dummy values for the secondary term - as we use layer type 00
        secondary_2 = primary_2
        # For the confining layer, we simplify that storage coefficient values (and transmissivities) are constant. 


        msg = "Set storage coefficient for the lower layer (including lat/lon correction)."
        if self.log_to_info: logger.info(msg)
        # layer 1 (lower layer) - storage coefficient
        # - default values
        self.storage_coefficient_1 = self.specificYield
        # - if specifically defined in the configuration/ini file
        if "aquiferLayerPrimaryStorageCoefficient" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['aquiferLayerPrimaryStorageCoefficient'] != "Default":
            msg = "Set storage coefficient for the aquifer layer based on the input in 'aquiferLayerPrimaryStorageCoefficient'."
            if self.log_to_info: logger.info(msg)
            aquiferLayerPrimaryStorageCoefficient = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['aquiferLayerPrimaryStorageCoefficient'], \
                                                                        self.cloneMap, self.tmpDir, self.inputDir)
            msg = "Note that this is for the confined aquifer layer only (aquifer covered by the confining layer)'."
            if self.log_to_info: logger.info(msg)
            # - only for cells below the confining layer
            aquiferLayerPrimaryStorageCoefficient = pcr.ifthen(self.confiningLayerThickness > 0.0, aquiferLayerPrimaryStorageCoefficient)
            #
            # - TODO: Perform interpolation in transition areas between cells with and without confining layer. 
            #
            # - cover the rest, using the default value
            self.storage_coefficient_1 = pcr.cover(aquiferLayerPrimaryStorageCoefficient, self.storage_coefficient_1)

        # adjusting factor and set minimum and maximum values to keep values realistics
        self.storage_coefficient_1  = adjust_factor * self.storage_coefficient_1
        self.storage_coefficient_1  = pcr.min(maximum_storage_coefficient, pcr.max(minimum_storage_coefficient, self.storage_coefficient_1))

        # - correction due to the usage of lat/lon coordinates
        primary_1   = pcr.cover(self.storage_coefficient_1 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary_1   = pcr.max(1e-20, primary_1)

        # - dummy values for the secondary term (layer type 00)
        secondary_1 = primary_1
        self.secondary_storage_coefficient_1 = secondary_1
        

        # secondary storage coefficient for aquifer layer (optional)
        if "aquiferLayerSecondaryStorageCoefficient" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['aquiferLayerSecondaryStorageCoefficient'] not in ["None", "False"]:
            # - default value
            self.secondary_storage_coefficient_1 = self.specificYield
            msg = "Using the layer type (LAYCON) 2. Storage coefficient values may alter from their primary to the secondary ones (and vice versa)"
            logger.info(msg)
            if self.iniItems.modflowParameterOptions['aquiferLayerSecondaryStorageCoefficient'] != "Default":
                msg = "Set the secondary storage coefficient for the aquifer layer based on the input in 'aquiferLayerSecondaryStorageCoefficient'."
                if self.log_to_info: logger.info(msg)
                aquiferLayerSecondaryStorageCoefficient = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['aquiferLayerSecondaryStorageCoefficient'], \
                                                                              self.cloneMap, self.tmpDir, self.inputDir)
            else:
                msg = "Set the secondary storage coefficient for the aquifer layer to the specific yield.'."
                if self.log_to_info: logger.info(msg)
                aquiferLayerSecondaryStorageCoefficient = self.specificYield
            # - cover the rest, using the default value
            self.secondary_storage_coefficient_1 = pcr.cover(aquiferLayerSecondaryStorageCoefficient, self.secondary_storage_coefficient_1)
        
        # adjusting factor and set minimum and maximum values to keep values realistics
        self.secondary_storage_coefficient_1 = adjust_factor * self.secondary_storage_coefficient_1
        self.secondary_storage_coefficient_1 = pcr.min(maximum_storage_coefficient, pcr.max(minimum_storage_coefficient, self.secondary_storage_coefficient_1))

        # - the value should be bigger or equal compared to its primary
        self.secondary_storage_coefficient_1 = pcr.max(self.secondary_storage_coefficient_1, self.storage_coefficient_1)
        
        # - correction due to the usage of lat/lon coordinates
        secondary_1 = pcr.cover(self.secondary_storage_coefficient_1 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        secondary_1 = pcr.max(1e-20, secondary_1)
        secondary_1 = pcr.max(1e-20, primary_1)
        

        msg = "Assign storage coefficient values to the MODFLOW (BCF package)."
        if self.log_to_info: logger.info(msg)
        # put the storage coefficient values to the modflow model
        self.pcr_modflow.setStorage(primary_1, secondary_1, 1)
        self.pcr_modflow.setStorage(primary_2, secondary_2, 2)


    def set_conductivities_for_two_layer_model(self):

        msg = "Preparing transmissivity values (TRAN) for the BCF package)."
        if self.log_to_info: logger.info(msg)

        
        # adjusting factor for horizontal conductivities 
        adjust_factor_for_horizontal_conductivities = 1.00
        if 'log_10_multiplier_for_transmissivities' in self.iniItems.modflowParameterOptions.keys():
            log_10_multiplier_for_transmissivities      = float(self.iniItems.modflowParameterOptions['log_10_multiplier_for_transmissivities'])
            adjust_factor_for_horizontal_conductivities = 10.0**(log_10_multiplier_for_transmissivities)
        msg = 'Adjustment factor: ' + str(adjust_factor_for_horizontal_conductivities)  
        if self.log_to_info: logger.info(msg)
        
        # minimum and maximum values for transmissivity
        maxTransmissivity = adjust_factor_for_horizontal_conductivities * self.maximumTransmissivity
        minTransmissivity = self.minimumTransmissivity        # to keep it realistic, this one should not be multiplied
        msg = 'The minimum transmissivity value is limited to (m2/day) ' + str(minTransmissivity)  
        if self.log_to_info: logger.info(msg)
        msg = 'The maximum transmissivity value is limited to (m2/day) ' + str(maxTransmissivity)  
        if self.log_to_info: logger.info(msg)

        
        msg = "Assign horizontal conductivities of the upper layer (used for calculating transmissivity (TRAN) for the BCF package)."
        if self.log_to_info: logger.info(msg)
        # - default values
        horizontal_conductivity_layer_2 = self.kSatAquifer
        # - if specifically defined in the configuration/ini file
        if "confiningLayerHorizontalConductivity" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['confiningLayerHorizontalConductivity'] != "Default":
            msg = "Set horizontal conductivities for the confining layer based on the input in 'confiningLayerHorizontalConductivity'."
            if self.log_to_info: logger.info(msg)
            confiningLayerHorizontalConductivity = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['confiningLayerHorizontalConductivity'], \
                                                                       self.cloneMap, self.tmpDir, self.inputDir)
            # - only for cells identified as the confining layer
            confiningLayerHorizontalConductivity = pcr.ifthen(self.confiningLayerThickness > 0.0, confiningLayerHorizontalConductivity)
            # - cover the rest, using the default value
            horizontal_conductivity_layer_2 = pcr.cover(confiningLayerHorizontalConductivity, horizontal_conductivity_layer_2)
        horizontal_conductivity_layer_2 = adjust_factor_for_horizontal_conductivities * horizontal_conductivity_layer_2
        
        # layer 2 (upper layer) - horizontal conductivity
        msg = "Constrained by minimum and maximum transmissity values."
        if self.log_to_info: logger.info(msg)
        horizontal_conductivity_layer_2 = pcr.max(minTransmissivity, \
                                          horizontal_conductivity_layer_2 * self.thickness_of_layer_2) / self.thickness_of_layer_2
        horizontal_conductivity_layer_2 = pcr.min(maxTransmissivity, \
                                          horizontal_conductivity_layer_2 * self.thickness_of_layer_2) / self.thickness_of_layer_2

        # transmissivity values for the upper layer (layer 2) - unit: m2/day
        self.transmissivity_layer_2 = horizontal_conductivity_layer_2 * self.thickness_of_layer_2
        self.transmissivity_layer_2_landmask_only = pcr.ifthen(self.landmask, self.transmissivity_layer_2)
        
        msg = "Assign horizontal conductivities of the lower layer (used for calculating transmissivity (TRAN) for the BCF package)."
        if self.log_to_info: logger.info(msg)
        # - default values
        horizontal_conductivity_layer_1 = self.kSatAquifer
        # - if specifically defined in the configuration/ini file
        if "aquiferLayerHorizontalConductivity" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['aquiferLayerHorizontalConductivity'] != "Default":
            msg = "Set horizontal conductivities for the aquifer layer based on the input in 'aquiferLayerHorizontalConductivity'."
            if self.log_to_info: logger.info(msg)
            aquiferLayerHorizontalConductivity = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['aquiferLayerHorizontalConductivity'], \
                                                                     self.cloneMap, self.tmpDir, self.inputDir)
            # - cover the rest, using the default value
            horizontal_conductivity_layer_1 = pcr.cover(aquiferLayerHorizontalConductivity, horizontal_conductivity_layer_1)
        horizontal_conductivity_layer_1 = adjust_factor_for_horizontal_conductivities * horizontal_conductivity_layer_1

        # layer 1 (lower layer) - horizontal conductivity 
        msg = "Constrained by minimum and maximum transmissity values."
        if self.log_to_info: logger.info(msg)
        horizontal_conductivity_layer_1 = pcr.max(minTransmissivity, \
                                          horizontal_conductivity_layer_1 * self.thickness_of_layer_1) / self.thickness_of_layer_1
        horizontal_conductivity_layer_1 = pcr.min(maxTransmissivity, \
                                          horizontal_conductivity_layer_1 * self.thickness_of_layer_1) / self.thickness_of_layer_1
                                          

        #~ # smoothing TRAN surrounding productive aquifer - EXPERIMENTAL # TODO: Check this!
        #~ transmissivity_layer_1 = horizontal_conductivity_layer_1 * self.thickness_of_layer_1
        #~ transmissivity_layer_1 = pcr.cover(
                                 #~ pcr.cover(
                                 #~ pcr.ifthen(self.productive_aquifer, transmissivity_layer_1), \
                                 #~ pcr.windowaverage(transmissivity_layer_1, 0.5)), transmissivity_layer_1)
        #~ horizontal_conductivity_layer_1 = pcr.max(horizontal_conductivity_layer_1, \
                                                  #~ transmissivity_layer_1/self.thickness_of_layer_1)                                                                  
        

        # transmissivity values for the lower layer (layer 1) - unit: m2/day
        self.transmissivity_layer_1 = horizontal_conductivity_layer_1 * self.thickness_of_layer_1
        self.transmissivity_layer_1_landmask_only = pcr.ifthen(self.landmask, self.transmissivity_layer_1)



        msg = "Preparing VCONT (day-1) values (1/resistance) between upper and lower layers for the BCF package (including the correction due to the lat/lon usage)."
        if self.log_to_info: logger.info(msg)

        
        # adjusting factor for resistance values  
        adjust_factor_for_resistance_values = 1.00
        if 'log_10_multiplier_for_resistance_values' in self.iniItems.modflowParameterOptions.keys():
            log_10_multiplier_for_resistance_values  = float(self.iniItems.modflowParameterOptions['log_10_multiplier_for_resistance_values'])
            adjust_factor_for_resistance_values      = 10.0**(log_10_multiplier_for_resistance_values)
        msg = 'Adjustment factor for resistance: ' + str(adjust_factor_for_resistance_values)  
        if self.log_to_info: logger.info(msg)

        
        # minimum and maximum resistance values (unit: days)
        minResistance = 1.0   # to keep it realistic, this one should not be multiplied
        maxResistance = adjust_factor_for_resistance_values * self.maximumConfiningLayerResistance
        msg = 'The minimum resistance (days) between upper and lower layers (1/VCONT) is limited to ' + str(minResistance)  
        if self.log_to_info: logger.info(msg)
        msg = 'The maximum resistance (days) between upper and lower layers (1/VCONT) is limited to ' + str(maxResistance)  
        if self.log_to_info: logger.info(msg)


        msg = "Assign vertical conductivities to determine VCONT values (1/resistance) between upper and lower layers (used for calculating VCONT for the BCF package)."
        if self.log_to_info: logger.info(msg)
        # - default values
        vertical_conductivity_layer_2 = self.kSatAquifer
        # - if specifically defined in the configuration/ini file
        if "confiningLayerVerticalConductivity" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['confiningLayerHorizontalConductivity'] != "Default":
            msg = "In areas with confining layer, set vertical conductivities based on the input in 'confiningLayerVerticalConductivity'."
            if self.log_to_info: logger.info(msg)
            confiningLayerVerticalConductivity = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['confiningLayerVerticalConductivity'], \
                                                                     self.cloneMap, self.tmpDir, self.inputDir)
            # - only for cells identified as the confining layer
            confiningLayerVerticalConductivity = pcr.ifthen(self.confiningLayerThickness > 0.0, confiningLayerVerticalConductivity)
            # - cover the rest, using the default value
            vertical_conductivity_layer_2 = pcr.cover(confiningLayerVerticalConductivity, vertical_conductivity_layer_2)
        #
        if "maximumConfiningLayerVerticalConductivity" in self.iniItems.modflowParameterOptions.keys():
            msg = "In areas with confining layer, limit vertical conductivity to the given map/value of maximumConfiningLayerVerticalConductivity"
            if self.log_to_info: logger.info(msg)
            # vertical conductivity values are limited by the predefined maximumConfiningLayerVerticalConductivity
            maximumConfiningLayerVerticalConductivity = pcr.min(vertical_conductivity_layer_2, self.maximumConfiningLayerVerticalConductivity)
            # particularly in areas with confining layer
            vertical_conductivity_layer_2  = pcr.ifthenelse(self.confiningLayerThickness > 0.0, maximumConfiningLayerVerticalConductivity, vertical_conductivity_layer_2)
        #
        # adjusment according to "adjust_factor_for_resistance_values":
        vertical_conductivity_layer_2 = (1.0/adjust_factor_for_resistance_values) * vertical_conductivity_layer_2
        
        # vertical conductivity values are limited by minimum and maximum resistance values
        msg = "Constrained by minimum and maximum resistance values."
        if self.log_to_info: logger.info(msg)
        vertical_conductivity_layer_2  = pcr.max(self.thickness_of_layer_2/maxResistance, \
                                                 vertical_conductivity_layer_2)
        vertical_conductivity_layer_2  = pcr.min(self.thickness_of_layer_2/minResistance,\
                                                     vertical_conductivity_layer_2)



        # resistance values between upper and lower layers - unit: days
        self.resistance_between_layers = self.thickness_of_layer_2 / vertical_conductivity_layer_2
        # VCONT values
        self.vcont_values = pcr.scalar(1.0) / self.resistance_between_layers

        # ignoring the vertical conductivity in the lower layer 
        # such that the values of resistance (1/vcont) depend only on vertical_conductivity_layer_2 
        vertical_conductivity_layer_1  = pcr.spatial(pcr.scalar(1e99))
        vertical_conductivity_layer_2 *= 0.5
        # see: http://inside.mines.edu/~epoeter/583/08/discussion/vcont/modflow_vcont.htm
        
        # correcting vertical conductivity due the lat/lon usage
        msg = "Correction due to the lat/lon usage."
        if self.log_to_info: logger.info(msg)
        vertical_conductivity_layer_2 *= self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize())
        vertical_conductivity_layer_1 *= self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize())

        #~ pcr.aguila(vertical_conductivity_layer_1)
        #~ raw_input("Press Enter to continue...")
        
        # set conductivity values to MODFLOW
        msg = "Assign conductivity values to the MODFLOW (BCF package)."
        if self.log_to_info: logger.info(msg)
        #~ pcr.aguila(self.kSatAquifer)
        #~ pcr.aguila(horizontal_conductivity_layer_2)
        #~ pcr.aguila(vertical_conductivity_layer_2)
        #~ raw_input("Press Enter to continue...")
        self.pcr_modflow.setConductivity(00, horizontal_conductivity_layer_2, \
                                             vertical_conductivity_layer_2, 2)              
        if "aquiferLayerSecondaryStorageCoefficient" in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['aquiferLayerSecondaryStorageCoefficient'] not in ["None", "False"]:
            msg = "Using the layer type (LAYCON) 2 for the aquifer layer."
            logger.debug(msg)
            self.pcr_modflow.setConductivity(02, horizontal_conductivity_layer_1, \
                                                 vertical_conductivity_layer_1, 1)              
            #~ self.pcr_modflow.setConductivity(22, horizontal_conductivity_layer_1, \
                                                 #~ vertical_conductivity_layer_1, 1)              
        else:
            self.pcr_modflow.setConductivity(00, horizontal_conductivity_layer_1, \
                                                 vertical_conductivity_layer_1, 1)              
            #~ self.pcr_modflow.setConductivity(20, horizontal_conductivity_layer_1, \
                                                 #~ vertical_conductivity_layer_1, 1)              


    def set_bcf_for_two_layer_model(self):

        # specification for conductivities (BCF package)
        self.set_conductivities_for_two_layer_model()

        # specification for storage coefficient (BCF package)
        self.set_storages_for_two_layer_model()


    def get_initial_heads(self, initialHeadsFromSpinUp = None):

		
        if initialHeadsFromSpinUp != None:
           
           msg = "Using initial groundwater head(s) resulted from the spin-up process."
           logger.info(msg)

           for i in range(1, self.number_of_layers+1):
               var_name = 'groundwaterHeadLayer'+str(i)
               vars(self)[var_name] = initialHeadsFromSpinUp['groundwater'][var_name]
        
        else:
        
           if self.steady_state_only == False and\
              self.iniItems.modflowTransientInputOptions['usingPredefinedInitialHead'] == "True": 
           
               msg = "Using pre-defined groundwater head(s) given in the ini/configuration file."
               logger.info(msg)
               
               for i in range(1, self.number_of_layers+1):
                   var_name = 'groundwaterHeadLayer'+str(i)
                   vars(self)[var_name] = vos.readPCRmapClone(self.iniItems.modflowTransientInputOptions[var_name+'Ini'],\
                                                              self.cloneMap, self.tmpDir, self.inputDir)
                   vars(self)[var_name] = pcr.cover(vars(self)[var_name], 0.0)                                           
           
           else:    
           
               msg = "Estimating initial conditions based on the steady state simulation using the input as defined in the ini/configuration file."
               logger.info(msg)
           
               # using the digital elevation model as the initial heads 
               for i in range(1, self.number_of_layers+1):
                   var_name = 'groundwaterHeadLayer'+str(i)
                   vars(self)[var_name] = self.dem_average
           
               # using initial head estimate given in the configuration file
               if 'usingInitialHeadEstimate' in self.iniItems.modflowSteadyStateInputOptions.keys() and\
                   self.iniItems.modflowSteadyStateInputOptions['usingInitialHeadEstimate'] == "True":
                   for i in range(1, self.number_of_layers+1):
                       var_name = 'groundwaterHeadLayer'+str(i)
                       vars(self)[var_name] = vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions[var_name+'Estimate'],\
                                                                  self.cloneMap, self.tmpDir, self.inputDir)
                       vars(self)[var_name] = pcr.cover(vars(self)[var_name], 0.0)                                           
               
               # calculate/simulate a steady state condition (until the modflow converges)
               # get the current state(s) of groundwater head and put them in a dictionary
               groundwaterHead = self.getState()
               self.modflow_simulation("steady-state", groundwaterHead, None, 1, 1)
               
               # An extra steady state simulation using transient simulation with constant input
               self.transient_simulation_with_constant_input()
           
               # extrapolating the calculated heads for areas/cells outside the landmask (to remove isolated cells) 
               # 
               # - the calculate groundwater head within the landmask region
               for i in range(1, self.number_of_layers+1):
                   var_name = 'groundwaterHeadLayer'+str(i)
                   vars(self)[var_name] = pcr.ifthen(self.landmask, vars(self)[var_name])
                   # keep the ocean values (dem <= 0.0) - this is in order to maintain the 'behaviors' of sub marine groundwater discharge
                   vars(self)[var_name] = pcr.cover(vars(self)[var_name], pcr.ifthen(self.dem_average <= 0.0, self.dem_average))
                   # extrapolation  
                   vars(self)[var_name] = pcr.cover(vars(self)[var_name], pcr.windowaverage(vars(self)[var_name], 3.*pcr.clone().cellSize()))
                   vars(self)[var_name] = pcr.cover(vars(self)[var_name], pcr.windowaverage(vars(self)[var_name], 5.*pcr.clone().cellSize()))
                   vars(self)[var_name] = pcr.cover(vars(self)[var_name], pcr.windowaverage(vars(self)[var_name], 7.*pcr.clone().cellSize()))
                   vars(self)[var_name] = pcr.cover(vars(self)[var_name], self.dem_average)
                   # TODO: Define the window sizes as part of the configuration file. Also consider to use the inverse distance method. 
               
               # TODO: Also please consider to use Deltares's trick to remove isolated cells.

    def transient_simulation_with_constant_input(self):

        self.transient_simulation_with_constant_input_with_10year_stress_period()
        self.transient_simulation_with_constant_input_with_yearly_stress_period()
        self.transient_simulation_with_constant_input_with_monthly_stress_period()

    def transient_simulation_with_constant_input_with_monthly_stress_period(self):

        time_step_length            = 30                # unit: days
        number_of_sub_time_steps    = time_step_length  # daily resolution
        #~ number_of_sub_time_steps = time_step_length * 4

        number_of_extra_years = 10                                                    

        if "extraSpinUpYearsWith30DayStressPeriod" in self.iniItems.modflowSteadyStateInputOptions.keys() and\
                                                      self.iniItems.modflowSteadyStateInputOptions['extraSpinUpYearsWith30DayStressPeriod'] != "None":
            number_of_extra_years = int(\
                                 self.iniItems.modflowSteadyStateInputOptions['extraSpinUpYearsWith30DayStressPeriod'])

        number_of_extra_months = 12 * number_of_extra_years    

        # maximum number of months = 999
        if number_of_extra_months > 999:
            
            msg = "To avoid a very long spin up, we limit the number of extra months to 999 months."
            logger.info(msg)
            number_of_extra_months = min(999, number_of_extra_months)
        
        if number_of_extra_months > 0:
        
            # preparing extra spin up folder/directory:
            extra_spin_up_directory = self.iniItems.endStateDir + "/extra_spin_up_with_monthly_stress_period/"
            if os.path.exists(extra_spin_up_directory): shutil.rmtree(extra_spin_up_directory)
            os.makedirs(extra_spin_up_directory)
            
            for i_month in range(1, number_of_extra_months + 1):
            
                msg  = "\n"
                msg += "\n"
                msg += "Extra steady state simulation (transient simulation with constant input and monthly stress period): " + str(i_month) + " from " + str(number_of_extra_months) 
                msg += "\n"
                msg += "\n"
                logger.info(msg)

                groundwaterHead = self.getState()
                self.modflow_simulation("steady-state-extra", groundwaterHead, None, time_step_length, number_of_sub_time_steps)
            
                # reporting the calculated head to pcraster files
                # - extension for output file:
                extension = "00" + str(i_month)
                if i_month > 9: extension = "0" + str(i_month)
                if i_month > 99: extension = str(i_month)
                
                for i in range(1, self.number_of_layers+1):

                    var_name = 'groundwaterHeadLayer' + str(i)
                    file_name = extra_spin_up_directory + "/gwhead" + str(i) + "_." + extension
                    pcr.report(groundwaterHead[var_name], file_name) 


    def transient_simulation_with_constant_input_with_yearly_stress_period(self):

        time_step_length            = 365                     # unit: days
        number_of_sub_time_steps    = 365                     # daily resolution
        #~ number_of_sub_time_steps = time_step_length * 4

        number_of_extra_years = 0                                                    

        if "extraSpinUpYearsWith365DayStressPeriod" in self.iniItems.modflowSteadyStateInputOptions.keys() and\
                                                       self.iniItems.modflowSteadyStateInputOptions['extraSpinUpYearsWith365DayStressPeriod'] != "None":
            number_of_extra_years = int(\
                                 self.iniItems.modflowSteadyStateInputOptions['extraSpinUpYearsWith365DayStressPeriod'])

        if number_of_extra_years > 0:
        
            # preparing extra spin up folder/directory:
            extra_spin_up_directory = self.iniItems.endStateDir + "/extra_spin_up_with_yearly_stress_period/"
            if os.path.exists(extra_spin_up_directory): shutil.rmtree(extra_spin_up_directory)
            os.makedirs(extra_spin_up_directory)
            
            for i_year in range(1, number_of_extra_years + 1):
            
                msg  = "\n"
                msg += "\n"
                msg += "Extra steady state simulation (transient simulation with constant input and yearly stress period): " + str(i_year) + " from " + str(number_of_extra_years) 
                msg += "\n"
                msg += "\n"
                logger.info(msg)

                groundwaterHead = self.getState()
                self.modflow_simulation("steady-state-extra", groundwaterHead, None, time_step_length, number_of_sub_time_steps)
            
                # reporting the calculated head to pcraster files
                # - extension for output file:
                extension = "00" + str(i_year)
                if i_year > 9: extension = "0" + str(i_year)
                if i_year > 99: extension = str(i_year)
                
                for i in range(1, self.number_of_layers+1):

                    var_name = 'groundwaterHeadLayer' + str(i)
                    file_name = extra_spin_up_directory + "/gwhead" + str(i) + "_." + extension
                    pcr.report(groundwaterHead[var_name], file_name) 

    def transient_simulation_with_constant_input_with_10year_stress_period(self):

        time_step_length            = 365 * 10        # unit: days
        #~ number_of_sub_time_steps =  10 * 52 * 2    # semi-weekly resolution
        number_of_sub_time_steps    =  10 * 52        # weekly resolution

        number_of_extra_10_years = 0                                                    

        if "extraSpinUpYearsWith10YearStressPeriod" in self.iniItems.modflowSteadyStateInputOptions.keys() and\
                                                       self.iniItems.modflowSteadyStateInputOptions['extraSpinUpYearsWith10YearStressPeriod'] != "None":
            number_of_extra_10_years = int(\
                                 self.iniItems.modflowSteadyStateInputOptions['extraSpinUpYearsWith10YearStressPeriod'])

        if number_of_extra_10_years > 0:
        
            # preparing extra spin up folder/directory:
            extra_spin_up_directory = self.iniItems.endStateDir + "/extra_spin_up_with_10year_stress_period/"
            if os.path.exists(extra_spin_up_directory): shutil.rmtree(extra_spin_up_directory)
            os.makedirs(extra_spin_up_directory)
            
            for i_10_year in range(1, number_of_extra_10_years + 1):
            
                msg  = "\n"
                msg += "\n"
                msg += "Extra steady state simulation (transient simulation with constant input and 10-year stress period): " + str(i_10_year) + " from " + str(number_of_extra_10_years) 
                msg += "\n"
                msg += "\n"
                logger.info(msg)

                groundwaterHead = self.getState()
                self.modflow_simulation("steady-state-extra", groundwaterHead, None, time_step_length, number_of_sub_time_steps)
            
                # reporting the calculated head to pcraster files
                # - extension for output file:
                extension = "00" + str(i_10_year)
                if i_10_year > 9: extension = "0" + str(i_10_year)
                if i_10_year > 99: extension = str(i_10_year)
                
                for i in range(1, self.number_of_layers+1):

                    var_name = 'groundwaterHeadLayer' + str(i)
                    file_name = extra_spin_up_directory + "/gwhead" + str(i) + "_." + extension
                    pcr.report(groundwaterHead[var_name], file_name) 

    def estimate_bottom_of_bank_storage_OLD_method(self):

        # influence zone depth (m)  # TODO: Define this one as part of the configuration file. 
        influence_zone_depth = 5.0
        
        # bottom_elevation = flood_plain elevation - influence zone
        bottom_of_bank_storage = self.dem_floodplain - influence_zone_depth

        # reducing noise (so we will not introduce unrealistic sinks)      # TODO: Define the window size as part of the configuration/ini file
        bottom_of_bank_storage = pcr.max(bottom_of_bank_storage,\
                                 pcr.windowaverage(bottom_of_bank_storage, 3.0 * pcr.clone().cellSize()))

        # bottom_elevation > river bed
        bottom_of_bank_storage = pcr.max(self.dem_riverbed, bottom_of_bank_storage)
        
        # reducing noise by comparing to its downstream value (so we will not introduce unrealistic sinks)
        bottom_of_bank_storage = pcr.max(bottom_of_bank_storage, \
                                        (bottom_of_bank_storage +
                                         pcr.cover(pcr.downstream(self.lddMap, bottom_of_bank_storage), bottom_of_bank_storage))/2.)

        # bottom_elevation >= 0.0 (must be higher than sea level)
        bottom_of_bank_storage = pcr.max(0.0, bottom_of_bank_storage)
         
        # bottom_elevation <= dem_average (this is to drain overland flow)
        bottom_of_bank_storage = pcr.min(bottom_of_bank_storage, self.dem_average)
        bottom_of_bank_storage = pcr.cover(bottom_of_bank_storage, self.dem_average)

        # for the mountainous region, the bottom of bank storage equal to its lowest point
        # - extent of mountainous region
        mountainous_extent  = pcr.ifthen((self.dem_average - self.dem_floodplain) > 50.0, pcr.boolean(1.0))
        # - sub_catchment classes
        sub_catchment_class = pcr.ifthen(mountainous_extent, \
                              pcr.subcatchment(self.lddMap, pcr.nominal(pcr.uniqueid(mountainous_extent))))
        # - bottom of bak storage
        bottom_of_bank_storage = pcr.cover(pcr.areaminimum(bottom_of_bank_storage, sub_catchment_class), \
                                           bottom_of_bank_storage)  

        # rounding down
        bottom_of_bank_storage = pcr.rounddown(bottom_of_bank_storage * 1000.)/1000.
        
        # TODO: We may want to improve this concept - by incorporating the following:
        # - smooth bottom_elevation
        # - upstream areas in the mountainous regions and above perrenial stream starting points may also be drained (otherwise water will be accumulated and trapped there) 
        # - bottom_elevation > minimum elevation that is estimated from the maximum of S3 from the PCR-GLOBWB simulation
        
        return bottom_of_bank_storage


    def estimate_bottom_of_bank_storage(self):

        # 20 March 2018, Edwin simplifies the concept as follows:
        # - Groundwater above floodplain is drained based on the linear reservoir concept (using the DRN package). 
        # - Below floodplain, it is drained based on the RIV package conceptualization.  
        
        # influence zone depth (m)  # TODO: Define this one as part of the configuration file. 
        influence_zone_depth = 0.0

        # bottom_elevation = flood_plain elevation - influence zone
        bottom_of_bank_storage = self.dem_floodplain - influence_zone_depth

        # bottom_elevation > river bed
        bottom_of_bank_storage = pcr.max(self.dem_riverbed, bottom_of_bank_storage)
        
        # bottom_elevation <= dem_average (this is to drain overland flow)
        bottom_of_bank_storage = pcr.min(bottom_of_bank_storage, self.dem_average)
        bottom_of_bank_storage = pcr.cover(bottom_of_bank_storage, self.dem_average)

        # for the mountainous region, the bottom of bank storage equal to its lowest point
        # - sub_catchment classes
        sub_catchment_class = pcr.ifthen(self.mountainous_extent, \
                              pcr.subcatchment(self.lddMap, pcr.nominal(pcr.uniqueid(self.mountainous_extent))))
        # - bottom of bank storage
        bottom_of_bank_storage = pcr.cover(pcr.areaminimum(bottom_of_bank_storage, sub_catchment_class), bottom_of_bank_storage) 
        # TODO: Using a map of perrenial streams to replace the 'mountainous region' concept.  

        # rounding down
        bottom_of_bank_storage = pcr.rounddown(bottom_of_bank_storage * 1000.)/1000.
        
        # TODO: We may want to improve this concept, see e.g. the paper sent by John Selker during the review of Sutanudjaja et al. (2014). 
        
        return bottom_of_bank_storage


    def initiate_old_style_reporting(self,iniItems):

        self.report = True
        try:
            self.outDailyTotNC = iniItems.oldReportingOptions['outDailyTotNC'].split(",")
            self.outMonthTotNC = iniItems.oldReportingOptions['outMonthTotNC'].split(",")
            self.outMonthAvgNC = iniItems.oldReportingOptions['outMonthAvgNC'].split(",")
            self.outMonthEndNC = iniItems.oldReportingOptions['outMonthEndNC'].split(",")
            self.outAnnuaTotNC = iniItems.oldReportingOptions['outAnnuaTotNC'].split(",")
            self.outAnnuaAvgNC = iniItems.oldReportingOptions['outAnnuaAvgNC'].split(",")
            self.outAnnuaEndNC = iniItems.oldReportingOptions['outAnnuaEndNC'].split(",")
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


    def update(self, currTimeStep, groundwater_recharge = None, \
                                   groundwater_abstraction = None, \
                                   surface_water_discharge = None, \
                                   surface_water_volume = None, \
                                   surface_water_fraction = None, \
                                   surface_water_bankfull_depth = None, \
                                   surface_water_flood_depth = None):
									   
        # for daily time step MODFLOW
        if self.online_daily_coupling_between_pcrglobwb_and_modflow:

            # get the previous state
            self.previousGroundwaterHead = self.getState()
            
            # length of a stress period = 1 day (daily)
            PERLEN = 1 
            # number of time step within a stress period
            NSTP = PERLEN
            
            self.PERLEN = PERLEN   # number of days within a stress period
            self.NSTP   = NSTP     # number of time steps within a stress period
            
            self.groundwater_recharge    = groundwater_recharge   
            self.groundwater_abstraction = groundwater_abstraction
            self.surface_water_discharge = surface_water_discharge
            self.surface_water_storage   = surface_water_volume
            self.dynamicFracWat          = surface_water_fraction
            self.bankfullDepth           = surface_water_bankfull_depth 
            self.floodDepth              = surface_water_flood_depth
               
            #~ pcr.aguila( self.groundwater_recharge)
            
            self.modflow_simulation("transient", self.previousGroundwaterHead, \
                                                 currTimeStep, PERLEN, NSTP) 

            # old-style reporting (this is usually used for debugging process)                            
            self.old_style_reporting(currTimeStep)


        # for monthly time step MODFLOW
        # at the end of the month, calculate/simulate a steady state condition and obtain its calculated head values
        if currTimeStep.isLastDayOfMonth() and self.online_daily_coupling_between_pcrglobwb_and_modflow == False:

            # get the previous state
            groundwaterHead = self.getState()
            
            # length of a stress period
            PERLEN = currTimeStep.day
            if currTimeStep.startTime.day != 1 and currTimeStep.monthIdx == 1:
                PERLEN = currTimeStep.day - currTimeStep.startTime.day + 1 
            
            # number of time step within a stress period
            #~ NSTP = 1
            NSTP    = PERLEN
            #~ NSTP = PERLEN * 2
            #~ NSTP = PERLEN * 4   # VERY IDEAL FOR CONVERGENCE
            # - Rule of thumb to estimate NSTP: delta_t = storage_coefficient * cell_area / (4 * transmissivity)
            # - see also: www.geology.wisc.edu/courses/g724/week10a.ppt
            
            self.PERLEN = PERLEN   # number of days within a stress period
            self.NSTP   = NSTP     # number of time steps within a stress period
            
            self.modflow_simulation("transient", groundwaterHead, 
                                                 currTimeStep, 
                                                 PERLEN, 
                                                 NSTP)

            # old-style reporting (this is usually used for debugging process)                            
            self.old_style_reporting(currTimeStep)
            
            # for debugging
            #~ pcr.aguila(self.transmissivity_layer_1)
            #~ raw_input("Press Enter to continue...")


    def save_some_pcraster_static_maps(self):

        msg = "Saving some pcraster maps (MODFLOW parameters/input files) to the folder"
        logger.info(msg)

        # - top and bottom layer elevations, as well as thicknesses
        pcr.report(pcr.ifthen(self.landmask, self.top_layer_2), self.iniItems.mapsDir + "/" + "top_uppermost_layer.map")
        pcr.report(pcr.ifthen(self.landmask, self.bottom_layer_2), self.iniItems.mapsDir + "/" + "bottom_uppermost_layer.map")
        pcr.report(pcr.ifthen(self.landmask, self.bottom_layer_1), self.iniItems.mapsDir + "/" + "bottom_lowermost_layer.map")
        pcr.report(pcr.ifthen(self.landmask, self.thickness_of_layer_2), self.iniItems.mapsDir + "/" + "thickness_uppermost_layer.map")
        pcr.report(pcr.ifthen(self.landmask, self.thickness_of_layer_1), self.iniItems.mapsDir + "/" + "thickness_lowermost_layer.map")
        
        # - transmissivities
        pcr.report(self.transmissivity_layer_2, self.iniItems.mapsDir + "/" + "transmissivity_uppermost_layer.map")
        pcr.report(self.transmissivity_layer_1, self.iniItems.mapsDir + "/" + "transmissivity_lowermost_layer.map")

        # - resistance values
        pcr.report(self.resistance_between_layers, self.iniItems.mapsDir + "/" + "resistance_between_layers.map")

        # - storage coefficients
        pcr.report(self.storage_coefficient_2, self.iniItems.mapsDir + "/" + "storage_coefficient_uppermost_layer.map")
        pcr.report(self.storage_coefficient_1, self.iniItems.mapsDir + "/" + "storage_coefficient_lowermost_layer.map")
        
        # TODO: Implement this for one layer model.

    def modflow_simulation(self,\
                           simulation_type,\
                           initialGroundwaterHeadInADictionary,\
                           currTimeStep = None,\
                           PERLEN = 1.0, 
                           NSTP   = 1, \
                           MXITER = 50,\
                           ITERI = 30,\
                           NPCOND = 1,\
                           RELAX = 0.98,\
                           NBPOL = 2,\
                           DAMP = 1,\
                           ITMUNI = 4, LENUNI = 2, TSMULT = 1.0):
        
        # initiate pcraster modflow object including its grid/layer/elevation:
        # - constant for the entire simulation
        if self.pcr_modflow == None: self.initiate_modflow()

        if simulation_type == "transient":
            logger.info("Preparing MODFLOW input for a transient simulation.")
            SSTR = 0
        if simulation_type == "steady-state":
            logger.info("Preparing MODFLOW input for a steady-state simulation.")
            SSTR = 1
        if simulation_type == "steady-state-extra":
            msg  = "Preparing MODFLOW input for an 'extra' steady-state simulation: "
            msg += "a transient simulation with constant input for 30 day (monthly) stress period with daily time step."
            logger.info(msg)
            SSTR = 0

        # extract and set initial head for modflow simulation
        groundwaterHead = initialGroundwaterHeadInADictionary
        for i in range(1, self.number_of_layers+1):
            var_name = 'groundwaterHeadLayer'+str(i)
            initial_head = pcr.scalar(groundwaterHead[var_name])
            self.pcr_modflow.setInitialHead(initial_head, i)
        
        # read input files (for the steady-state condition, we use pcraster maps):
        if simulation_type == "steady-state" or simulation_type == "steady-state-extra":
            # - discharge (m3/s) from PCR-GLOBWB
            discharge = vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgDischargeInputMap'],\
                                                self.cloneMap, self.tmpDir, self.inputDir)
            # - recharge/capillary rise (unit: m/day) from PCR-GLOBWB 
            gwRecharge = vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgGroundwaterRechargeInputMap'],\
                                                self.cloneMap, self.tmpDir, self.inputDir)
            # - groundwater abstraction (unit: m/day) from PCR-GLOBWB 
            gwAbstraction = pcr.spatial(pcr.scalar(0.0))
            gwAbstraction = vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgGroundwaterAbstractionInputMap'],\
                                                self.cloneMap, self.tmpDir, self.inputDir)
            # - average channel storage (unit: m3) from PCR-GLOBWB 
            channelStorage = None                                           
            if 'avgChannelStorageInputMap' in self.iniItems.modflowSteadyStateInputOptions.keys() and\
               self.iniItems.modflowSteadyStateInputOptions['avgChannelStorageInputMap'][-4:] != "None": 
                channelStorage = pcr.cover(\
                                 vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgChannelStorageInputMap'],\
                                                     self.cloneMap, self.tmpDir, self.inputDir), 0.0)

        # read input files 
        if simulation_type == "transient":
            
            if self.online_coupling:

                if self.online_daily_coupling_between_pcrglobwb_and_modflow:

                    discharge      = pcr.cover(self.surface_water_discharge, 0.0)
                    channelStorage = pcr.cover(self.surface_water_storage, 0.0)
                    
                    gwRecharge     = pcr.cover(self.groundwater_recharge, 0.0)
                    gwAbstraction  = pcr.cover(self.groundwater_abstraction, 0.0)
                
                else:
                
                    # for non daily online coupling, we will read files from pcraster maps
                    directory = self.iniItems.main_output_directory + "/global/maps/"
                    
                    # - discharge (m3/s) from PCR-GLOBWB
                    discharge_file_name = directory + "monthly_discharge_cubic_meter_per_second_" + str(currTimeStep.fulldate) + ".map" 
                    discharge = pcr.cover(vos.readPCRmapClone(discharge_file_name, self.cloneMap, self.tmpDir), 0.0)
                    
                    # - recharge/capillary rise (unit: m/day) from PCR-GLOBWB 
                    gwRecharge_file_name = directory + "groundwater_recharge_meter_per_day_" + str(currTimeStep.fulldate) + ".map"
                    gwRecharge = pcr.cover(vos.readPCRmapClone(gwRecharge_file_name, self.cloneMap, self.tmpDir), 0.0)
                    
                    # - groundwater abstraction (unit: m/day) from PCR-GLOBWB 
                    gwAbstraction_file_name = directory + "groundwater_abstraction_meter_per_day_" + str(currTimeStep.fulldate) + ".map"
                    gwAbstraction = pcr.cover(vos.readPCRmapClone(gwAbstraction_file_name, self.cloneMap, self.tmpDir), 0.0)
                    
                    # - channel storage (unit: m/day) 
                    channel_storage_file_name = directory + "channel_storage_cubic_meter_" + str(currTimeStep.fulldate) + ".map"
                    channelStorage = pcr.cover(vos.readPCRmapClone(channel_storage_file_name, self.cloneMap, self.tmpDir), 0.0)
                    
                    # TODO: Try to read from netcdf files, avoid reading from pcraster maps (avoid resampling using gdal) 

            else:
            
                # for offline coupling, we will read files from netcdf files
                
                # - discharge (m3/s) from PCR-GLOBWB
                discharge = vos.netcdf2PCRobjClone(self.iniItems.modflowTransientInputOptions['dischargeInputNC'],
                                                   "discharge", str(currTimeStep.fulldate), None, self.cloneMap)
                # - recharge/capillary rise (unit: m/day) from PCR-GLOBWB 
                gwRecharge = vos.netcdf2PCRobjClone(self.iniItems.modflowTransientInputOptions['groundwaterRechargeInputNC'],\
                                                   "groundwater_recharge", str(currTimeStep.fulldate), None, self.cloneMap)
                gwRecharge = pcr.cover(gwRecharge, 0.0)                                   
            
                # - groundwater abstraction (unit: m/day) from PCR-GLOBWB 
                gwAbstraction = pcr.spatial(pcr.scalar(0.0))
                if self.iniItems.modflowTransientInputOptions['groundwaterAbstractionInputNC'][-4:] != "None": 
                    gwAbstraction = vos.netcdf2PCRobjClone(self.iniItems.modflowTransientInputOptions['groundwaterAbstractionInputNC'],\
                                                           "total_groundwater_abstraction", str(currTimeStep.fulldate), None, self.cloneMap)
                    gwAbstraction = pcr.cover(gwAbstraction, 0.0)
                
                # - for offline coupling, the provision of channel storage (unit: m3) is only optional
                channelStorage = None                                           
                if 'channelStorageInputNC' in self.iniItems.modflowTransientInputOptions.keys() and\
                   self.iniItems.modflowTransientInputOptions['channelStorageInputNC'][-4:] != "None": 
                    if self.usingSurfaceWaterStorageInput:
                       msg = "Using surfaceWaterStorageInputNC (multiplied by cellAreaMap) to estimate channelStorage."
                       logger.debug(msg)
                       surfaceWaterStorage = vos.netcdf2PCRobjClone(self.iniItems.modflowTransientInputOptions['surfaceWaterStorageInputNC'],\
                                                                    "surface_water_storage", str(currTimeStep.fulldate), None, self.cloneMap)
                       channelStorage = pcr.cover(surfaceWaterStorage * self.cellAreaMap, 0.0)                                       
                    else:
                       channelStorage = vos.netcdf2PCRobjClone(self.iniItems.modflowTransientInputOptions['channelStorageInputNC'],\
                                                              "channel_storage", str(currTimeStep.fulldate), None, self.cloneMap)
                       channelStorage = pcr.cover(channelStorage, 0.0)
                    channelStorage = pcr.max(0.0, channelStorage)                                          


        #####################################################################################################################################################
        # for a steady-state simulation, the capillary rise is usually ignored: 
        if (simulation_type == "steady-state" or\
            simulation_type == "steady-state-extra"):
            self.ignoreCapRise = True
            if 'ignoreCapRiseSteadyState' in self.iniItems.modflowSteadyStateInputOptions.keys() and\
                self.iniItems.modflowSteadyStateInputOptions['ignoreCapRiseSteadyState'] == "False": self.ignoreCapRise = False
        #####################################################################################################################################################

        # ignore capillary rise if needed:
        if self.ignoreCapRise: gwRecharge = pcr.max(0.0, gwRecharge) 

        # convert the values of abstraction and recharge to daily average (ONLY for a transient simulation)
        if self.valuesRechargeAndAbstractionInMonthlyTotal and simulation_type == "transient": 
            gwAbstraction = gwAbstraction/currTimeStep.day
            gwRecharge    = gwRecharge/currTimeStep.day

        # built-up area fractions for limitting groundwater recharge 
        if self.using_built_up_area_correction_for_recharge:
            msg = 'Reading built-up area fractions to limit groundwater recharge.'
            logger.info(msg)
            # read input files 
            if simulation_type == "transient":
                date_used = currTimeStep.fulldate
            else:
                # for a steady-state simulation, we use the year of the starting date
                date_used = '%04i-%02i-%02i' %(int(self.iniItems.globalOptions['startTime'][0:4]), 1, 1)
            self.built_up_area_correction_for_recharge = pcr.cover(
                                                         vos.netcdf2PCRobjClone(self.iniItems.groundwaterOptions['nc_file_for_built_up_area_correction_for_recharge'],
                                                                                "vegetation_fraction", 
                                                                                date_used, 'yearly',\
                                                                                self.cloneMap), 0.0)
            self.built_up_area_correction_for_recharge = pcr.max(0.0, self.built_up_area_correction_for_recharge)
            self.built_up_area_correction_for_recharge = pcr.min(1.0, self.built_up_area_correction_for_recharge)   
        
 
 
        if self.online_daily_coupling_between_pcrglobwb_and_modflow:
            self.set_drain_and_river_package(discharge, channelStorage, currTimeStep, simulation_type, "daily", \
                                                                                                       False, \
                                                                                                       self.dynamicFracWat,\
                                                                                                       self.bankfullDepth,\
                                                                                                       self.floodDepth)
        else:
            self.set_drain_and_river_package(discharge, channelStorage, currTimeStep, simulation_type)
        
        # set recharge and well packages
        self.set_recharge_package(gwRecharge)
        self.set_well_package(gwAbstraction)

        # set parameter values for the DIS package
        self.pcr_modflow.setDISParameter(ITMUNI, LENUNI, PERLEN, NSTP, TSMULT, SSTR)
        #
        # Some notes about the values  
        #
        # ITMUNI = 4     # indicates the time unit (0: undefined, 1: seconds, 2: minutes, 3: hours, 4: days, 5: years)
        # LENUNI = 2     # indicates the length unit (0: undefined, 1: feet, 2: meters, 3: centimeters)
        # PERLEN = 1.0   # duration of a stress period
        # NSTP   = 1     # number of time steps in a stress period
        # TSMULT = 1.0   # multiplier for the length of the successive iterations
        # SSTR   = 1     # 0 - transient, 1 - steady state

        # DAMP parameters (this may help the convergence)
        self.parameter_DAMP = self.parameter_DAMP_default
        # TODO: Set DAMP in the configuration/ini file (as a list, see also below)
        if simulation_type == "steady-state":
            #~ self.parameter_DAMP = [1.0, 0.80, 0.60] 
            #~ self.parameter_DAMP = [1.0, 0.75] 
            #~ self.parameter_DAMP = [0.80] 
            #~ self.parameter_DAMP = [0.75]
            #~ self.parameter_DAMP = [0.75, 0.60]
            # PS: Starting from 25 September 2017, I decided to reduce DAMP values. It seems that doing this ease the convergence.      
            self.parameter_DAMP    = self.parameter_DAMP_steady_state_default
            
        # initiate the index for HCLOSE and RCLOSE for the interation until modflow_converged
        self.iteration_HCLOSE = 0
        self.iteration_RCLOSE = 0
        self.iteration_DAMP   = 0
        self.modflow_converged = False


        # execute MODFLOW 
        while self.modflow_converged == False:
            
            # convergence criteria 
            HCLOSE = float(self.criteria_HCLOSE[self.iteration_HCLOSE])
            RCLOSE = float(self.criteria_RCLOSE[self.iteration_RCLOSE])
            
            # damping parameter
            DAMP = float(self.parameter_DAMP[self.iteration_DAMP])
            
            # set PCG solver
            self.pcr_modflow.setPCG(MXITER, ITERI, NPCOND, HCLOSE, RCLOSE, RELAX, NBPOL, DAMP)

            # some notes for PCG solver values  
            #
            # MXITER = 50                 # maximum number of outer iterations           # Deltares use 50
            # ITERI  = 30                 # number of inner iterations                   # Deltares use 30
            # NPCOND = 1                  # 1 - Modified Incomplete Cholesky, 2 - Polynomial matrix conditioning method;
            # HCLOSE = 0.01               # HCLOSE (unit: m) 
            # RCLOSE = 10.* 400.*400.     # RCLOSE (unit: m3)
            # RELAX  = 1.00               # relaxation parameter used with NPCOND = 1
            # NBPOL  = 2                  # indicates whether the estimate of the upper bound on the maximum eigenvalue is 2.0 (but we don ot use it, since NPCOND = 1) 
            # DAMP   = 1                  # no damping (DAMP introduced in MODFLOW 2000)

            msg = "Executing MODFLOW with DAMP = " + str(DAMP) + " and HCLOSE = "+str(HCLOSE)+" and RCLOSE = "+str(RCLOSE)+" and MXITER = "+str(MXITER)+" and ITERI = "+str(ITERI)+" and PERLEN = "+str(PERLEN)+" and NSTP = "+str(NSTP)
            logger.info(msg)
            
            try:
                #~ working_directory_where_modflow_files_are_written = self.tmp_modflow_dir
                #~ self.pcr_modflow.run(working_directory_where_modflow_files_are_written)
                self.pcr_modflow.run()
                try:
                    self.modflow_converged = self.pcr_modflow.converged()           # TODO: Ask Oliver to fix the non-convergence issue that can appear before reaching the end of stress period.  
                except:
                    self.modflow_converged = self.old_check_modflow_convergence()
            except:
                self.modflow_converged = False

            print self.modflow_converged

            if self.modflow_converged == False:
            
                logger.info('')
                msg = "MODFLOW FAILED TO CONVERGE with HCLOSE = "+str(HCLOSE)+" and RCLOSE = "+str(RCLOSE)
                logger.info(msg)
                logger.info('')

                ####################################################################################################################################### OPTIONAL ######
                # for the steady state simulation, we still save the calculated head(s) 
                # so that we can use them as the initial estimate for the next iteration (by doing this, it may ease the convergence?? - TODO: check this
                # NOTE: We must NOT extract the calculated heads of a transient simulation result that does not converge.
                if simulation_type == "steady-state": 

                    msg = "Set the result from the uncoverged modflow simulation as the initial new estimate (for a steady-state simulation only)."
                    logger.info(msg)
                    
                    # obtain the result from the uncoverged modflow simulation
                    for i in range(1, self.number_of_layers+1):
                        var_name = 'groundwaterHeadLayer'+str(i)
                        vars(self)[var_name] = None
                        vars(self)[var_name] = self.pcr_modflow.getHeads(i)

                    # set the result from the uncoverged modflow simulation as the initial new estimate
                    for i in range(1, self.number_of_layers+1):
                        var_name = 'groundwaterHeadLayer'+str(i)
                        initial_head = pcr.scalar(vars(self)[var_name])
                        self.pcr_modflow.setInitialHead(initial_head, i)
                ####################################################################################################################################### OPTIONAL ######

                # set a new iteration index for the DAMP
                self.iteration_DAMP   += 1
                # reset if the index has reached the length of available criteria
                if self.iteration_DAMP > (len(self.parameter_DAMP)-1): self.iteration_DAMP = 0     

                # set a new iteration index for the RCLOSE
                if self.iteration_DAMP == 0: self.iteration_RCLOSE += 1 
                # reset if the index has reached the length of available criteria
                if self.iteration_RCLOSE > (len(self.criteria_RCLOSE)-1): self.iteration_RCLOSE = 0     
            
                # set a new iteration index for the HCLOSE
                if self.iteration_RCLOSE == 0 and self.iteration_DAMP == 0: self.iteration_HCLOSE += 1
                     
                # if we already using all available HCLOSE
                if self.iteration_RCLOSE == 0 and self.iteration_DAMP == 0 and self.iteration_HCLOSE == len(self.criteria_HCLOSE):
                    
                    msg  = "\n\n\n"
                    msg += "NOT GOOD!!! MODFLOW STILL FAILED TO CONVERGE with HCLOSE = "+str(HCLOSE)+" and RCLOSE = "+str(RCLOSE)
                    msg += "\n\n"

                    # for a steady-state simulation, we give up 
                    if simulation_type == "steady-state": 

                        msg += "But, we give up and we can only decide/suggest to use the last calculated groundwater heads."
                        msg += "\n\n"
                        logger.warning(msg)
                        
                        # force MODFLOW to converge
                        self.modflow_converged = True

                    else: 

                        additional_HLCOSE = HCLOSE * 2.0

                        msg += "We will try again using the HCLOSE: " + str(additional_HLCOSE)
                        msg += "\n\n"
                        logger.warning(msg)

                        self.criteria_HCLOSE.append(additional_HLCOSE)
                        self.criteria_HCLOSE = sorted(self.criteria_HCLOSE)
                        
                        # TODO: Shall we also increase RCLOSE ??

            else:
            
                msg  = "\n\n\n"
                msg += "HURRAY!!! MODFLOW CONVERGED with HCLOSE = "+str(HCLOSE)+" and RCLOSE = "+str(RCLOSE)
                msg += "\n\n"
                logger.info(msg)
            
        # obtaining the results from modflow simulation
        if self.modflow_converged: self.get_all_modflow_results(simulation_type)
        
        # copy all modflow files (only for transient simulation)
        if self.make_backup_of_modflow_files and simulation_type == "transient": 
            # target directory:
            target_directory = self.iniItems.globalOptions['outputDir'] + "/" + "modflow_files" + "/" + str(currTimeStep.fulldate) + "/"
            if os.path.exists(target_directory): shutil.rmtree(target_directory)
            os.makedirs(target_directory)
            # copying modflow files:
            for filename in glob.glob(os.path.join(self.tmp_modflow_dir, '*')):
                shutil.copy(filename, target_directory)

        # clear modflow object
        self.pcr_modflow = None
        
        # calculate some variables that will be accessed from PCR-GLOBWB (for online coupling purpose)
        self.calculate_values_for_pcrglobwb()
        
    def calculate_values_for_pcrglobwb(self):

        logger.info("Calculate some variables for PCR-GLOBWB (needed for online coupling purpose: 'relativeGroundwaterHead', 'baseflow', and 'storGroundwater'")
        

        # relative uppermost groundwater head (unit: m) above the minimum elevation within grid
        uppermost_head = vars(self)['groundwaterHeadLayer'+str(self.number_of_layers)]
        self.relativeGroundwaterHead = uppermost_head - self.dem_minimum
        

        # baseflow (unit: m/day)
        # - initiate the (accumulated) volume rate (m3/day) (for accumulating the fluxes from all layers)
        totalBaseflowVolumeRate = pcr.scalar(0.0) 
        # - accumulating fluxes from all layers
        for i in range(1, self.number_of_layers+1):
            # from the river leakage
            var_name = 'riverLeakageLayer'+str(i)
            totalBaseflowVolumeRate += pcr.cover(vars(self)[var_name], 0.0)
            # from the drain package
            var_name = 'drainLayer'+str(i)
            totalBaseflowVolumeRate += pcr.cover(vars(self)[var_name], 0.0)
            # use only in the landmask region
            if i == self.number_of_layers: totalBaseflowVolumeRate = pcr.ifthen(self.landmask, totalBaseflowVolumeRate)
        # - convert the unit to m/day and convert the flow direction 
        #   for this variable, positive values indicates flow leaving aquifer (following PCR-GLOBWB assumption, opposite direction from MODFLOW) 
        self.baseflow = pcr.scalar(-1.0) * (totalBaseflowVolumeRate/self.cellAreaMap)
        

        # storGroundwater (unit: m)
        # - from the lowermost layer
        accesibleGroundwaterThickness = pcr.ifthen(self.landmask, \
                                                       self.storage_coefficient_1 * \
                                                       pcr.max(0.0, self.groundwaterHeadLayer1 - pcr.max(self.max_accesible_elevation, \
                                                                                                         self.bottom_layer_1)))
        # - from the uppermost layer                                                
        if self.number_of_layers == 2:\
           accesibleGroundwaterThickness += pcr.ifthen(self.landmask, \
                                                       self.storage_coefficient_2 * \
                                                       pcr.max(0.0, self.groundwaterHeadLayer2 - pcr.max(self.max_accesible_elevation, \
                                                                                                         self.bottom_layer_2)))
        # - TODO: Make this flexible for a model that has more than two layers. 
        # - storGroundwater (unit: m) that can be accessed for abstraction
        self.storGroundwater = accesibleGroundwaterThickness                                                                                                

                
    def get_all_modflow_results(self, simulation_type):
        
        logger.info("Get all modflow results.")
        
        # obtaining the results from modflow simulation
        
        for i in range(1, self.number_of_layers+1):
            
            # groundwater head (unit: m)
            var_name = 'groundwaterHeadLayer'+str(i)
            vars(self)[var_name] = None
            vars(self)[var_name] = self.pcr_modflow.getHeads(i)
            
            # river leakage (unit: m3/day)
            var_name = 'riverLeakageLayer'+str(i)
            vars(self)[var_name] = None
            vars(self)[var_name] = self.pcr_modflow.getRiverLeakage(i)
            
            # drain (unit: m3/day)
            var_name = 'drainLayer'+str(i)
            vars(self)[var_name] = None
            vars(self)[var_name] = self.pcr_modflow.getDrain(i)
            #~ pcr.aguila(vars(self)[var_name])
            
            # bdgfrf - cell-by-cell flows right (m3/day)
            var_name = 'flowRightFaceLayer'+str(i)
            vars(self)[var_name] = None
            vars(self)[var_name] = self.pcr_modflow.getRightFace(i)

            # bdgfff - cell-by-cell flows front (m3/day)
            var_name = 'flowFrontFaceLayer'+str(i)
            vars(self)[var_name] = None
            vars(self)[var_name] = self.pcr_modflow.getFrontFace(i)
            
            # bdgflf - cell-by-cell flows lower (m3/day) 
            # Note: No flow through the lower face of the bottom layer
            if i > 1:
                var_name = 'flowLowerFaceLayer'+str(i)
                vars(self)[var_name] = None
                vars(self)[var_name] = self.pcr_modflow.getLowerFace(i)

            # flow to/from constant head cells (unit: m3/day)
            var_name = 'flowConstantHeadLayer'+str(i)
            vars(self)[var_name] = None
            vars(self)[var_name] = self.pcr_modflow.getConstantHead(i)

            # cell-by-cell storage flow term (unit: m3)
            if simulation_type == "transient":
                var_name = 'flowStorageLayer'+str(i)
                vars(self)[var_name] = None
                vars(self)[var_name] = self.pcr_modflow.getStorage(i)

        #~ # for debuging only
        #~ pcr.report(self.groundwaterHeadLayer1 , "gw_head_layer_1.map")
        #~ pcr.report(self.groundwaterDepthLayer1, "gw_depth_layer_1.map")


    def old_check_modflow_convergence(self, file_name = "pcrmf.lst"):
        
        # open and read the lst file
        file_name = self.tmp_modflow_dir + "/" + file_name
        f = open(file_name) ; all_lines = f.read() ; f.close()
        
        # split the content of the file into several lines
        all_lines = all_lines.replace("\r","") 
        all_lines = all_lines.split("\n")
        
        # scan the last 200 lines and check if the model 
        modflow_converged = True
        for i in range(0,200): 
            if 'FAILED TO CONVERGE' in all_lines[-i]: modflow_converged = False
        
        print modflow_converged
        
        return modflow_converged    


    def estimate_river_water_elevations_based_on_pcrglobwb_river_water_levels(self, channelStorage, dynamicFracWat, bankfullDepth, floodDepth):

        # water levels in channels  
        river_water_levels = pcr.ifthenelse(dynamicFracWat > 0., pcr.max(0.0, channelStorage) / (dynamicFracWat * self.cellAreaMap), 
                                                                 0.0)
        river_water_levels = pcr.ifthenelse(floodDepth > 0., bankfullDepth + floodDepth, pcr.min(bankfullDepth, river_water_levels))
        # - elevation
        river_water_elevation = river_water_levels + self.dem_riverbed 
        
        # surface water elevation (m) is limited by flood plain elevation (m)
        # - water above the flood plain will be drained based on the linear reservoir concept
        river_water_elevation = pcr.min(river_water_elevation, self.dem_floodplain) 
        
        return river_water_elevation



    def estimate_surface_water_bed_properties(self):

        logger.info("(Re-)Estimating surface water bed elevation.")
        
        # estimate of lake and reservoir fraction and estimate of river fraction:
        lake_and_reservoir_fraction_per_entire_cell = pcr.cover(self.WaterBodies.fracWat, 0.0)
        river_fraction_per_entire_cell = pcr.cover((self.bankfull_width * self.channelLength) / self.cellAreaMap, 0.0)
        # - per surface water area only
        self.lake_and_reservoir_fraction = pcr.min(1.0, \
                                           vos.getValDivZero(lake_and_reservoir_fraction_per_entire_cell, lake_and_reservoir_fraction_per_entire_cell + river_fraction_per_entire_cell, 0.0))
        self.river_fraction              = pcr.max(0.0, \
                                           1.0 - self.lake_and_reservoir_fraction)
        self.lake_and_reservoir_fraction = pcr.ifthenelse(lake_and_reservoir_fraction_per_entire_cell + river_fraction_per_entire_cell > 0.0, self.lake_and_reservoir_fraction, 0.0)
        self.river_fraction = pcr.ifthenelse(lake_and_reservoir_fraction_per_entire_cell + river_fraction_per_entire_cell > 0.0, self.river_fraction, 0.0)
        # PS: One of the ideas of these fraction values is to accomodate if one wants to use different bed conductance values.                                    
        

        # - for lakes and resevoirs, estimate bed elevation from DEM only
        #                            This is to avoid that groundwater heads fall too far below DEM
        #                            This will also smooth groundwater heads.     
        #~ # --- alternative 1: using just DEM
        #~ surface_water_bed_elevation = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, self.dem_average)
        #~ surface_water_bed_elevation = pcr.cover(surface_water_bed_elevation, 0.0)
        # --- alternative 2: using average DEM
        surface_water_bed_elevation = pcr.areaaverage(self.dem_average, self.WaterBodies.waterBodyIds)
        surface_water_bed_elevation = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, surface_water_bed_elevation)
        surface_water_bed_elevation = pcr.cover(surface_water_bed_elevation, self.dem_average)
        #
        # TODO: Need further investigation for lake and reservoir bed elevations. 
        
        surface_water_bed_elevation = self.lake_and_reservoir_fraction * surface_water_bed_elevation + self.river_fraction * self.dem_riverbed

        # rounding values for surface_water_bed_elevation
        self.surface_water_bed_elevation = pcr.rounddown(surface_water_bed_elevation * 1000.)/1000.


        logger.info("(Re-)Estimating surface water bed conductance.")

        ############################################################################################################################################
        # lake and reservoir resistance (day)
        lake_and_reservoir_resistance = self.bed_resistance

        # lake and reservoir conductance (m2/day)
        lake_and_reservoir_conductance = (1.0/lake_and_reservoir_resistance) * lake_and_reservoir_fraction_per_entire_cell * \
                                              self.cellAreaMap
        # river conductance (m2/day)
        river_conductance = (1.0/self.bed_resistance) * river_fraction_per_entire_cell *\
                                                        self.cellAreaMap
        # assume all cells have minimum river width
        # - this is to drain groundwater flood over the surface
        minimum_width = 2.0   # TODO: Set this in the configuration file
        minimum_conductance = (1.0/self.bed_resistance) * \
                              pcr.max(minimum_width, self.bankfull_width) * self.channelLength
        river_conductance   = pcr.max(minimum_conductance, river_conductance)

        # surface water bed condutance (unit: m2/day)
        bed_conductance = pcr.cover(lake_and_reservoir_conductance, 0.0) + pcr.cover(river_conductance, 0.0)
        self.bed_conductance = pcr.cover(bed_conductance, 0.0)
        ############################################################################################################################################


    def set_drain_and_river_package(self, discharge, channel_storage, currTimeStep, simulation_type, stress_period = "monthly", \
                                                                                                     estimate_river_water_level_from_discharge = True, \
                                                                                                     dynamicFracWat = None, \
                                                                                                     bankfullDepth = None, \
                                                                                                     floodDepth = None):
        
        # set the river package
        self.set_river_package(discharge = discharge, \
                               channel_storage = channel_storage, \
                               currTimeStep = currTimeStep, \
                               simulation_type = simulation_type, \
                               exclude_river_infiltration = self.exclude_river_infiltration, \
                               stress_period = stress_period, \
                               estimate_river_water_level_from_discharge = estimate_river_water_level_from_discharge, \
                               dynamicFracWat = dynamicFracWat, \
                               bankfullDepth = bankfullDepth, \
                               floodDepth = floodDepth,\
                               set_the_modflow_river_package = True)
        
        # set drain package
        self.set_drain_package()                                         



    def set_river_package(self, discharge, channel_storage, currTimeStep, simulation_type, \
                                                                          exclude_river_infiltration = True, \
                                                                          stress_period = "monthly", \
                                                                          estimate_river_water_level_from_discharge = True, \
                                                                          dynamicFracWat = None, \
                                                                          bankfullDepth = None, \
                                                                          floodDepth = None,\
                                                                          set_the_modflow_river_package = True):

        
        logger.info("Estimating surface water level and bed elevations, as well as be conductance (RIV package).")


        # set WaterBodies class and its parameters to define the extent of lakes and reservoirs (constant for the entire year, annual resolution)
        if simulation_type == "steady-state" or simulation_type == "steady-state-extra":

            onlyNaturalWaterBodies = self.onlyNaturalWaterBodies
            if 'onlyNaturalWaterBodiesDuringSteadyStateSimulation' in self.iniItems.modflowSteadyStateInputOptions.keys(): 
                onlyNaturalWaterBodies == self.iniItems.modflowSteadyStateInputOptions['onlyNaturalWaterBodiesDuringSteadyStateSimulation'] == "True"
            self.WaterBodies = waterBodies.WaterBodies(self.iniItems,\
                                                       self.landmask,\
                                                       self.onlyNaturalWaterBodies)

            sd = str(self.iniItems.globalOptions['startTime']).split('-')
            startTime = datetime.date(int(sd[0]), int(sd[1]), int(sd[2]))
            self.WaterBodies.getParameterFiles(startTime,\
                                               self.cellAreaMap, \
                                               self.lddMap,
                                               None, True)

        if simulation_type == "transient":

            if self.WaterBodies == None:
                self.WaterBodies = waterBodies.WaterBodies(self.iniItems,\
                                                           self.landmask,\
                                                           self.onlyNaturalWaterBodies,\
                                                           self.lddMap)
                self.WaterBodies.getParameterFiles(currTimeStep,\
                                                   self.cellAreaMap, \
                                                   self.lddMap)        
            if currTimeStep.month == 1 and stress_period == "monthly":
                self.WaterBodies.getParameterFiles(currTimeStep,\
                                                   self.cellAreaMap, \
                                                   self.lddMap)        
            if currTimeStep.day == 1 and currTimeStep.month == 1 and stress_period == "daily":
                self.WaterBodies.getParameterFiles(currTimeStep,\
                                                   self.cellAreaMap, \
                                                   self.lddMap)        


        # reset bed conductance and bed elevation (due to possibility of new inclusion of lakes/reservoirs)
        new_lakes_reservoirs_introduced = False
        if currTimeStep == None:
            new_lakes_reservoirs_introduced = True
        else:
            if currTimeStep.month == 1 and stress_period == "monthly": new_lakes_reservoirs_introduced = True
            if currTimeStep.day == 1 and currTimeStep.month == 1 and stress_period == "daily": new_lakes_reservoirs_introduced = True
        #
        if new_lakes_reservoirs_introduced:
            self.surface_water_bed_elevation = None
            self.bed_conductance = None
        else:
            msg = "Surface water bed elevation and conductance values stay the same as the previous ones."
            logger.info(msg)
        #
        if isinstance(self.surface_water_bed_elevation, types.NoneType) and isinstance(self.bed_conductance, types.NoneType):
            msg = "Estimating or re-estimating surface water bed and conductance due to new lakes/reservoirs."
            logger.info(msg)
            self.estimate_surface_water_bed_properties()
           

        # surface water bed elevation that will be supplied to RIV package
        surface_water_bed_elevation_used = self.surface_water_bed_elevation
        # - rounding
        surface_water_bed_elevation_used = pcr.rounddown(surface_water_bed_elevation_used * 1000.)/1000.


        logger.info("Estimating surface water elevation.")
        if estimate_river_water_level_from_discharge:

            logger.info("River water levels based on PCR-GLOBWB discharge output (converted to water levels using Manning's equation)")

            # - convert discharge value to surface water elevation (m)
            river_water_height = (self.bankfull_width**(-3/5)) * (discharge**(3/5)) * ((self.gradient)**(-3/10)) *(self.manningsN**(3/5))
            river_water_elevation = self.dem_riverbed + river_water_height
            #
            # - calculating water level (unit: m) above the flood plain - estimated from discharge only 
            #------------------------------------------------------------------------------------------
            water_above_fpl  = pcr.max(0.0, river_water_elevation - self.dem_floodplain)      # unit: m, water level above the floodplain (not distributed)
            water_above_fpl *= self.bankfull_depth * self.bankfull_width / self.cellAreaMap   # unit: m, water level above the floodplain (distributed within the cell)
            #
            # - corrected surface water elevation
            river_water_elevation = pcr.ifthenelse(river_water_elevation > self.dem_floodplain, self.dem_floodplain + water_above_fpl, \
                                                                                                river_water_elevation)

        else:

            logger.info('Estimating river water levels based on PCR-GLOBWB surface water volume and level output (e.g. channel storage, flood extent and depth)')

            river_water_elevation = self.estimate_river_water_elevations_based_on_pcrglobwb_river_water_levels(channel_storage, \
                                                                                                               dynamicFracWat, \
                                                                                                               bankfullDepth, \
                                                                                                               floodDepth)
        
        # surface water elevations:
        #
        # - surface water elevation for lakes and reservoirs:
        #
        #~ # -- alternative 1: based on maximum water levels within the lake
        #~ lake_reservoir_water_elevation = pcr.areamaximum(river_water_elevation, self.WaterBodies.waterBodyIds)
        #
        #~ # -- alternative 2: just using the constant value based on the digital elevation model 
        #~ lake_reservoir_water_elevation    = self.dem_average
        #~ #
        #~ lake_reservoir_water_elevation    = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, lake_reservoir_water_elevation)
        #
        # --- alternative 3: using average DEM
        lake_reservoir_water_elevation = pcr.areaaverage(river_water_elevation, self.WaterBodies.waterBodyIds)
        lake_reservoir_water_elevation = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, lake_reservoir_water_elevation)
        lake_reservoir_water_elevation = pcr.cover(lake_reservoir_water_elevation, river_water_elevation)
        lake_reservoir_water_elevation = pcr.cover(lake_reservoir_water_elevation, self.dem_average)
        #
        # - surface water elevation for rivers, lakes and reservoirs
        #
        surface_water_elevation = pcr.cover(lake_reservoir_water_elevation, self.dem_average) * self.lake_and_reservoir_fraction + \
                                  pcr.cover(river_water_elevation, self.dem_average) * self.river_fraction
        #                              
        # - rounding
        surface_water_elevation = pcr.rounddown(surface_water_elevation * 1000.)/1000.

        # - make sure that HRIV >= RBOT
        surface_water_elevation = pcr.max(surface_water_elevation, surface_water_bed_elevation_used)

        # to avoid negative channel storage, river infiltration will be excluded from the river package
        if exclude_river_infiltration:
            msg = 'Set the river bed elevations to water level elevation (RIV behaves as DRN).'
            logger.info(msg)
            surface_water_bed_elevation_used = surface_water_elevation
        else:
            # - exclude infiltration for small rivers
            minimum_width_of_river_with_infiltration = self.minimumWidthOfRiversWithInfiltration
            river_bed_elevation = pcr.ifthenelse(self.bankfull_width >= minimum_width_of_river_with_infiltration, surface_water_bed_elevation_used, surface_water_elevation)
            # - maintain bed elevation defined for lakes and reservoir
            surface_water_bed_elevation_used = self.lake_and_reservoir_fraction * surface_water_bed_elevation_used +\
                                               self.river_fraction * river_bed_elevation

        # - covering missing values
        surface_water_elevation = pcr.cover(surface_water_elevation, self.dem_average)
        surface_water_bed_elevation_used = pcr.cover(surface_water_bed_elevation_used, self.dem_average)

        # - make sure that HRIV >= RBOT
        surface_water_elevation = pcr.max(surface_water_elevation, surface_water_bed_elevation_used)

        # reducing the size of table by ignoring cells outside the landmask region 
        bed_conductance_used = pcr.ifthen(self.landmask, self.bed_conductance)
        bed_conductance_used = pcr.cover(bed_conductance_used, 0.0)

        # - limit the condutance using channel storage
        if not isinstance(channel_storage, types.NoneType):
            logger.info('Limit river bed conductance with channel storage.')
            maximum_bed_conductance = pcr.ifthenelse((surface_water_elevation - surface_water_bed_elevation_used) > 0.00, \
                                      (channel_storage / (surface_water_elevation - surface_water_bed_elevation_used)) / self.PERLEN, \
                                      (bed_conductance_used))
            maximum_bed_conductance = pcr.max(0.0, pcr.ifthenelse(channel_storage > 0.0, maximum_bed_conductance, 0.0))
            bed_conductance_used = pcr.min(maximum_bed_conductance, bed_conductance_used)
        

        # set the RIV package only to the uppermost layer
        if set_the_modflow_river_package:
            logger.info('Set the RIVER package.')
            self.pcr_modflow.setRiver(surface_water_elevation, surface_water_bed_elevation_used, bed_conductance_used, self.number_of_layers)
        else:
            return surface_water_elevation, surface_water_bed_elevation_used, bed_conductance_used


        #~ # set also the RIV package to the lowermost layer # TODO: Still experimental. Need further checks/tests !!
        #~ bed_conductance_lower_layer = pcr.ifthenelse(surface_water_bed_elevation_used < self.bottom_layer_2, bed_conductance_used, 0.0)
        #~ self.pcr_modflow.setRiver(surface_water_elevation, surface_water_bed_elevation_used, bed_conductance_used, 1)



    def set_recharge_package(self, \
                             gwRecharge, gwAbstraction = 0.0, 
                             gwAbstractionReturnFlow = 0.0):            # Note: We ignored the latter as MODFLOW should capture this part as well.
								                                        #       We also moved the abstraction to the WELL package 

        logger.info("Set the recharge package.")

        # specify the recharge package
        # + recharge/capillary rise (unit: m/day) from PCR-GLOBWB 
        # - groundwater abstraction (unit: m/day) from PCR-GLOBWB 
        # + return flow of groundwater abstraction (unit: m/day) from PCR-GLOBWB 
        net_recharge = gwRecharge - gwAbstraction + \
                       gwAbstractionReturnFlow

        # built-up area fractions for limitting groundwater recharge 
        if self.using_built_up_area_correction_for_recharge:
            msg = 'Incorporating built-up area fractions to limit groundwater recharge.'
            logger.info(msg)
            net_recharge = net_recharge * pcr.min(1.0, pcr.max(0.0, 1.0 - self.built_up_area_correction_for_recharge))

        # adjustment factor
        adjusting_factor = 1.0
        if 'linear_multiplier_for_groundwater_recharge' in self.iniItems.modflowParameterOptions.keys():
            linear_multiplier_for_groundwater_recharge = float(self.iniItems.modflowParameterOptions['linear_multiplier_for_groundwater_recharge'])
            adjusting_factor                           = linear_multiplier_for_groundwater_recharge
        msg = 'Adjustment factor: ' + str(adjusting_factor)  
        if self.log_to_info: logger.info(msg)
        
        # adjusting recharge values
        self.net_recharge = net_recharge * adjusting_factor
        
        # - correcting values (considering MODFLOW lat/lon cell properties)
        #   and pass them to the RCH package   
        net_RCH = pcr.cover(self.net_recharge * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        net_RCH = pcr.cover(pcr.ifthenelse(pcr.abs(net_RCH) < 1e-20, 0.0, net_RCH), 0.0)
        
        # put the recharge to the top grid/layer
        self.pcr_modflow.setRecharge(net_RCH, 1)

        #~ # if we want to put RCH in the lower layer
        #~ self.pcr_modflow.setIndicatedRecharge(net_RCH, pcr.spatial(pcr.nominal(1)))

    def set_well_package(self, gwAbstraction):

        logger.info("Set the well package.")

        # adjustment factor
        adjusting_factor = 1.0
        if 'linear_multiplier_for_groundwater_abstraction' in self.iniItems.modflowParameterOptions.keys():
            linear_multiplier_for_groundwater_abstraction = float(self.iniItems.modflowParameterOptions['linear_multiplier_for_groundwater_abstraction'])
            adjusting_factor                              = linear_multiplier_for_groundwater_abstraction
        msg = 'Adjustment factor: ' + str(adjusting_factor)  
        if self.log_to_info: logger.info(msg)
        
        # adjusting groundwater abstraction
        gwAbstractionUsed = gwAbstraction * adjusting_factor

        if self.number_of_layers == 1: self.set_well_package_for_one_layer_model(gwAbstractionUsed)
        if self.number_of_layers == 2: self.set_well_package_for_two_layer_model(gwAbstractionUsed)
        
        # for debugging
        self.gwAbstractionUsed = pcr.ifthen(self.landmask, gwAbstractionUsed)

    def set_well_package_for_one_layer_model(self, gwAbstraction):
		
        gwAbstraction = pcr.cover(gwAbstraction, 0.0)
        gwAbstraction = pcr.max(gwAbstraction, 0.0)

        # abstraction volume (negative value, unit: m3/day)
        abstraction = pcr.cover(gwAbstraction, 0.0) * self.cellAreaMap * pcr.scalar(-1.0)
        
        # set the well package
        self.pcr_modflow.setWell(abstraction, 1)

    def set_well_package_for_two_layer_model(self, gwAbstraction):
		
        gwAbstraction = pcr.cover(gwAbstraction, 0.0)
        gwAbstraction = pcr.max(gwAbstraction, 0.0)
        
        # abstraction for the layer 1 (lower layer) is limited only in productive aquifer
        abstraction_layer_1 = pcr.cover(pcr.ifthen(self.productive_aquifer, gwAbstraction), 0.0)
        
        #~ # abstraction for the layer 2 (upper layer)          # DON'T DO THIS
        #~ abstraction_layer_2 = pcr.spatial(pcr.scalar(0.0))

        # remaining abstraction
        remaining_abstraction = pcr.max(0.0, gwAbstraction - abstraction_layer_1)
        # remaining abstraction will be distributed as follows:
        # - first, to the upper layer, but limited to groundwater recharge
        abstraction_layer_2 = pcr.min(pcr.max(0.0, pcr.cover(self.net_recharge, 0.0)), remaining_abstraction)
        remaining_abstraction = pcr.max(0.0, remaining_abstraction - abstraction_layer_2)
        # - then, distribute the remaining based on transmissivities
        abstraction_layer_1 += remaining_abstraction * pcr.cover(vos.getValDivZero(self.transmissivity_layer_1, \
                                                                        (self.transmissivity_layer_1 + self.transmissivity_layer_2)), 0.0)
        abstraction_layer_2  = pcr.max(0.0, gwAbstraction - abstraction_layer_1)
        # - water balance check                                                                 
        if self.debugWaterBalance:
            vos.waterBalanceCheck([gwAbstraction],\
                                  [abstraction_layer_1, abstraction_layer_2],\
                                  [],\
                                  [],\
                                  'partitioning groundwater abstraction to both layers',\
                                  True,\
                                  '-', threshold=5e-4)
        
        # TODO: Distribute remaining_abstraction based on 'effective' KD value (based on saturated thickness) of each layer
        
        # for reporting/debugging
        self.abstraction_layer_1 = pcr.ifthen(self.landmask, abstraction_layer_1)
        self.abstraction_layer_2 = pcr.ifthen(self.landmask, abstraction_layer_2)
        
        # abstraction volume (negative value, unit: m3/day)
        abstraction_layer_1 = abstraction_layer_1 * self.cellAreaMap * pcr.scalar(-1.0)
        abstraction_layer_2 = abstraction_layer_2 * self.cellAreaMap * pcr.scalar(-1.0)
        
        # set the well package
        self.pcr_modflow.setWell(abstraction_layer_1, 1)
        self.pcr_modflow.setWell(abstraction_layer_2, 2)

    def set_drain_package(self):

        logger.info("Set the drain package (for the release of over bank storage).")

        # specify the drain package the drain package is used to simulate the drainage of bank storage 

        # - estimate bottom of bank storage for flood plain areas
        drain_elevation = self.estimate_bottom_of_bank_storage()                               # unit: m
        
        # - drainage conductance is a linear reservoir coefficient
        drain_conductance = self.recessionCoeff * self.specificYield * self.cellAreaMap        # unit: m2/day
        # - for lakes and/or reservoirs, ignore the drainage
        drain_conductance *= pcr.cover(pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, pcr.scalar(self.WaterBodies.fracWat)), 1.0)

        #~ drain_conductance = pcr.ifthenelse(drain_conductance < 1e-20, 0.0, \
                                           #~ drain_conductance) 
        #~ drain_conductance = pcr.rounddown(drain_conductance*10000.)/10000.                  # It is not a good idea to round the values down (water can be trapped).  

        # reducing the size of table by ignoring cells outside landmask region
        drain_conductance = pcr.ifthen(self.landmask, drain_conductance)
        drain_conductance = pcr.cover(drain_conductance, 0.0)
        
        #~ # set the DRN package only to the uppermost layer
        #~ self.pcr_modflow.setDrain(drain_elevation, drain_conductance, self.number_of_layers)

        #~ # set the DRN package only to both layers ------ 4 January 2016: I think that we should use this as we want all recharge will be released as baseflow.
        #~ self.pcr_modflow.setDrain(drain_elevation, drain_conductance, 1)
        #~ self.pcr_modflow.setDrain(drain_elevation, drain_conductance, 2)

        #~ # set the DRN package only to the lowermost layer
        #~ self.pcr_modflow.setDrain(drain_elevation, drain_conductance, 1)
        #~ self.pcr_modflow.setDrain(pcr.spatial(pcr.scalar(0.0)),pcr.spatial(pcr.scalar(0.0)), 2)
        
        # a new idea 9 Nov 2018:
        drain_elevation_lowermost_layer = pcr.max(drain_elevation, self.bottom_layer_1)
        self.pcr_modflow.setDrain(drain_elevation_lowermost_layer, drain_conductance, 1)
        drain_elevation_uppermost_layer = pcr.max(drain_elevation, self.bottom_layer_2)
        self.pcr_modflow.setDrain(drain_elevation_uppermost_layer, drain_conductance, 2)

        # TODO: Shall we link the specificYield used to the BCF package ??
        
        #~ pcr.aguila(pcr.ifthen(self.landmask, self.recessionCoeff))

    def return_innundation_fraction(self,relative_water_height):

        # - fractions of flooded area (in percentage) based on the relative_water_height (above the minimum dem)
        DZRIV = relative_water_height
        
        CRFRAC_RIV =                         pcr.min(1.0,1.00-(self.dzRel0100-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0100-self.dzRel0090)       	 )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0090,0.90-(self.dzRel0090-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0090-self.dzRel0080),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0080,0.80-(self.dzRel0080-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0080-self.dzRel0070),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0070,0.70-(self.dzRel0070-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0070-self.dzRel0060),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0060,0.60-(self.dzRel0060-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0060-self.dzRel0050),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0050,0.50-(self.dzRel0050-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0050-self.dzRel0040),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0040,0.40-(self.dzRel0040-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0040-self.dzRel0030),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0030,0.30-(self.dzRel0030-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0030-self.dzRel0020),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0020,0.20-(self.dzRel0020-DZRIV)*0.10/pcr.max(1e-3,self.dzRel0020-self.dzRel0010),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0010,0.10-(self.dzRel0010-DZRIV)*0.05/pcr.max(1e-3,self.dzRel0010-self.dzRel0005),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0005,0.05-(self.dzRel0005-DZRIV)*0.04/pcr.max(1e-3,self.dzRel0005-self.dzRel0001),CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<self.dzRel0001,0.01-(self.dzRel0001-DZRIV)*0.01/pcr.max(1e-3,self.dzRel0001)               ,CRFRAC_RIV )
        CRFRAC_RIV = pcr.ifthenelse(DZRIV<=0,0, CRFRAC_RIV)
        
        # - minimum value of innundation fraction is river/channel area
        CRFRAC_RIV = pcr.cover(pcr.max(0.0,pcr.min(1.0,pcr.max(CRFRAC_RIV,(self.bankfull_depth*self.bankfull_width/self.cellAreaMap)))),scalar(0))		;

        # TODO: Improve this concept using Rens's latest scheme

    def old_style_reporting(self,currTimeStep):

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

