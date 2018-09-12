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

import waterBodies_for_modflow as waterBodies

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

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # cloneMap, temporary directory for the resample process, temporary directory for the modflow process, absolute path for input directory, landmask
        self.cloneMap        = iniItems.cloneMap
        self.tmpDir          = iniItems.tmpDir
        self.tmp_modflow_dir = iniItems.tmp_modflow_dir
        self.inputDir        = iniItems.globalOptions['inputDir']
        self.landmask        = landmask
        
        # configuration from the ini file
        self.iniItems = iniItems
                
        # number of modflow layers:
        self.number_of_layers = int(iniItems.modflowParameterOptions['number_of_layers'])
        
        # topography properties: read several variables from the netcdf file
        for var in ['dem_minimum','dem_maximum','dem_average','dem_standard_deviation',\
                    'slopeLength','orographyBeta','tanslope',\
                    'dzRel0000','dzRel0001','dzRel0005',\
                    'dzRel0010','dzRel0020','dzRel0030','dzRel0040','dzRel0050',\
                    'dzRel0060','dzRel0070','dzRel0080','dzRel0090','dzRel0100']:
            vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['topographyNC'], \
                                                                var, self.cloneMap)
            vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

        # channel properties: read several variables from the netcdf file
        for var in ['lddMap','cellAreaMap','gradient','bankfull_width',
                    'bankfull_depth','dem_floodplain','dem_riverbed']:
            vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['channelNC'], \
                                                                var, self.cloneMap)
            vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
        
        # minimum channel width
        minimum_channel_width = 5.0                                                # TODO: Define this one in the configuration file
        self.bankfull_width = pcr.max(minimum_channel_width, self.bankfull_width)
        
        #~ # cell fraction if channel water reaching the flood plain               # NOT USED YET 
        #~ self.flood_plain_fraction = self.return_innundation_fraction(pcr.max(0.0, self.dem_floodplain - self.dem_minimum))
        
        # coefficient of Manning
        self.manningsN = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['manningsN'],\
                                             self.cloneMap,self.tmpDir,self.inputDir)
        
        # minimum channel gradient
        minGradient   = 0.00005                                                                                     # TODO: Define this one in the configuration file
        minGradient   = 0.000005   # 24 March 2016: I lower this so that we don't have too deep water table.        # TODO: Define this one in the configuration file
        self.gradient = pcr.max(minGradient, pcr.cover(self.gradient, minGradient))

        # correcting lddMap
        self.lddMap = pcr.ifthen(pcr.scalar(self.lddMap) > 0.0, self.lddMap)
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        
        # channelLength = approximation of channel length (unit: m)  # This is approximated by cell diagonal. 
        cellSizeInArcMin      = np.round(pcr.clone().cellSize()*60.)               # FIXME: This one will not work if you use the resolution: 0.5, 1.5, 2.5 arc-min
        verticalSizeInMeter   = cellSizeInArcMin*1852.                            
        horizontalSizeInMeter = self.cellAreaMap/verticalSizeInMeter
        self.channelLength    = ((horizontalSizeInMeter)**(2)+\
                                 (verticalSizeInMeter)**(2))**(0.5)
        
        # option for lakes and reservoir
        self.onlyNaturalWaterBodies = False
        if self.iniItems.modflowParameterOptions['onlyNaturalWaterBodies'] == "True": self.onlyNaturalWaterBodies = True

        
        
        ######################################################################################
        # a netcdf file containing the groundwater properties 
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] != "None":
            groundwaterPropertiesNC = vos.getFullPath(\
                                      iniItems.groundwaterOptions[\
                                      'groundwaterPropertiesNC'],self.inputDir)
        ######################################################################################


        #####################################################################################################################################################
        # assign aquifer specific yield (dimensionless) 
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == "None" or 'specificYield' in iniItems.groundwaterOptions.keys():
            self.specificYield  = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['specificYield'],self.cloneMap,self.tmpDir,self.inputDir)
        else:       
            self.specificYield = vos.netcdf2PCRobjCloneWithoutTime(\
                                 groundwaterPropertiesNC,'specificYield',self.cloneMap)
        self.specificYield = pcr.cover(self.specificYield,0.0)       
        self.specificYield = pcr.max(0.010,self.specificYield)          # TODO: Set the minimum values of specific yield.      
        self.specificYield = pcr.min(1.000,self.specificYield)       
        #####################################################################################################################################################


        #####################################################################################################################################################
        # assign aquifer hydraulic conductivity (unit: m/day)
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == "None" or 'kSatAquifer' in iniItems.groundwaterOptions.keys():
            self.kSatAquifer = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['kSatAquifer'],self.cloneMap,self.tmpDir,self.inputDir)
        else:       
            self.kSatAquifer = vos.netcdf2PCRobjCloneWithoutTime(\
                               groundwaterPropertiesNC,'kSatAquifer',self.cloneMap)
        self.kSatAquifer = pcr.cover(self.kSatAquifer,0.0)       
        self.kSatAquifer = pcr.max(0.010,self.kSatAquifer)
        #####################################################################################################################################################

        
        #####################################################################################################################################################
        # try to assign the reccesion coefficient (unit: day-1) from the netcdf file of groundwaterPropertiesNC      
        try: 
            self.recessionCoeff = vos.netcdf2PCRobjCloneWithoutTime(\
                                  groundwaterPropertiesNC,'recessionCoeff',\
                                  cloneMapFileName = self.cloneMap)    
        except:    
            self.recessionCoeff = None
            msg = "The 'recessionCoeff' cannot be read from the file: "+groundwaterPropertiesNC
            logger.warning(msg)
 
        # assign the reccession coefficient based on the given pcraster file 
        if 'recessionCoeff' in iniItems.groundwaterOptions.keys(): 
            if iniItems.groundwaterOptions['recessionCoeff'] != "None":\
               self.recessionCoeff = vos.readPCRmapClone(iniItems.groundwaterOptions['recessionCoeff'],self.cloneMap,self.tmpDir,self.inputDir)

        # calculate the reccession coefficient based on the given parameters 
        if isinstance(self.recessionCoeff,types.NoneType) and\
                          'recessionCoeff' not in iniItems.groundwaterOptions.keys(): 
            
            msg = "Calculating the groundwater linear reccesion coefficient based on the given parameters."
            logger.info(msg)
            
            # reading the 'aquiferWidth' value from the landSurfaceOptions (slopeLength)
            if iniItems.landSurfaceOptions['topographyNC'] == None:
                aquiferWidth = vos.readPCRmapClone(iniItems.landSurfaceOptions['slopeLength'],self.cloneMap,self.tmpDir,self.inputDir)
            else:    
                topoPropertiesNC = vos.getFullPath(iniItems.landSurfaceOptions['topographyNC'],self.inputDir)
                aquiferWidth = vos.netcdf2PCRobjCloneWithoutTime(topoPropertiesNC,'slopeLength',self.cloneMap)
            # covering aquiferWidth with its maximum value
            aquiferWidth = pcr.ifthen(self.landmask, pcr.cover(aquiferWidth, pcr.mapmaximum(aquiferWidth))) 
            
            # aquifer thickness (unit: m) for recession coefficient
            aquiferThicknessForRecessionCoeff = vos.readPCRmapClone(iniItems.groundwaterOptions['aquiferThicknessForRecessionCoeff'],\
                                                                    self.cloneMap,self.tmpDir,self.inputDir)
            
            # calculate recessionCoeff (unit; day-1)
            self.recessionCoeff = (math.pi**2.) * aquiferThicknessForRecessionCoeff / \
                                  (4.*self.specificYield*(aquiferWidth**2.))                                                               

        # assign the reccession coefficient based on the given pcraster file 
        if 'recessionCoeff' in iniItems.groundwaterOptions.keys(): 
            if iniItems.groundwaterOptions['recessionCoeff'] != "None":\
               self.recessionCoeff = vos.readPCRmapClone(iniItems.groundwaterOptions['recessionCoeff'],self.cloneMap,self.tmpDir,self.inputDir)

        # minimum and maximum values for groundwater recession coefficient (day-1)
        self.recessionCoeff = pcr.cover(self.recessionCoeff,0.00)       
        self.recessionCoeff = pcr.min(0.9999,self.recessionCoeff)       
        if 'minRecessionCoeff' in iniItems.groundwaterOptions.keys():
            minRecessionCoeff = float(iniItems.groundwaterOptions['minRecessionCoeff'])
        else:
            minRecessionCoeff = 1.0e-4                                               # This is the minimum value used in Van Beek et al. (2011). 
        self.recessionCoeff = pcr.max(minRecessionCoeff,self.recessionCoeff)      
        #####################################################################################################################################################


        #####################################################################################################################################################
        # assign the river/stream/surface water bed conductivity
        # - the default value is equal to kSatAquifer 
        self.riverBedConductivity = self.kSatAquifer 
        # - assign riverBedConductivity coefficient based on the given pcraster file 
        if 'riverBedConductivity' in iniItems.groundwaterOptions.keys(): 
            if iniItems.groundwaterOptions['riverBedConductivity'] != "None":\
               self.riverBedConductivity = vos.readPCRmapClone(iniItems.groundwaterOptions['riverBedConductivity'],self.cloneMap,self.tmpDir,self.inputDir)
        #
        # surface water bed thickness  (unit: m)
        bed_thickness  = 0.1
        # surface water bed resistance (unit: day)
        bed_resistance = bed_thickness / (self.riverBedConductivity) 
        minimum_bed_resistance = 1.0
        self.bed_resistance = pcr.max(minimum_bed_resistance,\
                                              bed_resistance,)
        ##############################################################################################################################################


        #####################################################################################################################################################
        # total groundwater thickness (unit: m) 
        # - For PCR-GLOBWB, the estimate of total groundwater thickness is needed to estimate for the following purpose:
        #   - productive aquifer areas (where capillary rise can occur and groundwater depletion can occur)
        #   - and also to estimate fossil groundwater capacity (the latter is needed only for run without MODFLOW) 
        totalGroundwaterThickness = None
        if 'estimateOfTotalGroundwaterThickness' in iniItems.groundwaterOptions.keys():

            totalGroundwaterThickness = vos.readPCRmapClone(iniItems.groundwaterOptions['estimateOfTotalGroundwaterThickness'],
                                                            self.cloneMap, self.tmpDir, self.inputDir)
            
            # extrapolation of totalGroundwaterThickness 
            # - TODO: Make a general extrapolation option as a function in the virtualOS.py 
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 0.75))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 0.75))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 0.75))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 1.00))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness, 0.0)
            
            # set minimum thickness
            if 'minimumTotalGroundwaterThickness' in iniItems.groundwaterOptions.keys():
                minimumThickness = pcr.scalar(float(\
                                   iniItems.groundwaterOptions['minimumTotalGroundwaterThickness']))
                totalGroundwaterThickness = pcr.max(minimumThickness, totalGroundwaterThickness)

            # set maximum thickness
            if 'maximumTotalGroundwaterThickness' in iniItems.groundwaterOptions.keys():
                maximumThickness = float(self.iniItems.groundwaterOptions['maximumTotalGroundwaterThickness'])
                totalGroundwaterThickness = pcr.min(maximumThickness, totalGroundwaterThickness)
            
            # estimate of total groundwater thickness (unit: m)
            self.totalGroundwaterThickness = totalGroundwaterThickness    
        #####################################################################################################################################################

        
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
            self.maximumConfiningLayerResistance = float(self.iniItems.modflowParameterOptions['maximumConfiningLayerResistance'])
            #~ self.maximumConfiningLayerResistance = pcr.cover(\
                                                   #~ vos.readPCRmapClone(self.iniItems.modflowParameterOptions['maximumConfiningLayerResistance'],\
                                                                       #~ self.cloneMap, self.tmpDir, self.inputDir), 0.0)
        ##############################################################################################################################################
        

        #####################################################################################################################################################
        # extent of the productive aquifer (a boolean map)
        # - Principle: In non-productive aquifer areas, capillary rise and groundwater abstraction should not exceed recharge
        # 
        self.productive_aquifer = pcr.ifthen(self.landmask, pcr.boolean(1.0))        
        excludeUnproductiveAquifer = True
        if excludeUnproductiveAquifer:
            if 'minimumTransmissivityForProductiveAquifer' in iniItems.groundwaterOptions.keys() and\
                                                             (iniItems.groundwaterOptions['minimumTransmissivityForProductiveAquifer'] != "None" or\
                                                              iniItems.groundwaterOptions['minimumTransmissivityForProductiveAquifer'] != "False"):
                minimumTransmissivityForProductiveAquifer = \
                                          vos.readPCRmapClone(iniItems.groundwaterOptions['minimumTransmissivityForProductiveAquifer'],\
                                                              self.cloneMap, self.tmpDir, self.inputDir)
                self.productive_aquifer = pcr.cover(\
                 pcr.ifthen(self.kSatAquifer * totalGroundwaterThickness > minimumTransmissivityForProductiveAquifer, pcr.boolean(1.0)), pcr.boolean(0.0))
        # - TODO: Check and re-calculate the GLHYMPS map to confirm the kSatAquifer value in groundwaterPropertiesNC (e.g. we miss some parts of HPA).  
        #####################################################################################################################################################


        #####################################################################################################################################################
        # option to ignore capillary rise
        self.ignoreCapRise = False
        if 'ignoreCapRise' in self.iniItems.modflowParameterOptions.keys() and \
            self.iniItems.modflowParameterOptions['ignoreCapRise'] == "True": self.ignoreCapRise = True
        #####################################################################################################################################################
        

        #####################################################################################################################################################
        # assumption for the thickness (m) of accessible groundwater (needed for coupling to PCR-GLOBWB)
        # - Note that this assumption value does not affect the modflow calculation. The values is needed merely for reporting "accesibleGroundwaterVolume".
        accesibleDepth = 1000.0
        if 'accesibleDepth' in self.iniItems.modflowParameterOptions.keys():
            if self.iniItems.modflowParameterOptions['accesibleDepth'] != "None":
                accesibleDepth = float(self.iniItems.modflowParameterOptions['accesibleDepth'])
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
        self.criteria_HCLOSE = sorted(self.criteria_HCLOSE)
        
        # list of the convergence criteria for RCLOSE (unit: m3)
        # - Deltares default's value for their 25 and 250 m resolution models is 10 m3  # check this value with Jarno
        cell_area_assumption = verticalSizeInMeter * float(pcr.cellvalue(pcr.mapmaximum(horizontalSizeInMeter),1)[0])
        #~ self.criteria_RCLOSE = [10., 100., 10.* cell_area_assumption/(250.*250.), 10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(250.*250.), 10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(25.*25.), 100.* cell_area_assumption/(25.*25.), 10000.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [10.* cell_area_assumption/(25.*25.), 10000.* cell_area_assumption/(25.*25.)]
        #~ self.criteria_RCLOSE = [1000., 10.* cell_area_assumption/(25.*25.), 1000.* cell_area_assumption/(25.*25.), 100000.* cell_area_assumption/(25.*25.)]
        self.criteria_RCLOSE = [1000., 10.* cell_area_assumption/(25.*25.), 1000.* cell_area_assumption/(25.*25.)]
        self.criteria_RCLOSE = sorted(self.criteria_RCLOSE)

        # initiate somes variables/objects/classes to None
        # - lakes and reservoir objects (they will be constant for the entrie year, only change at the beginning of the year)
        self.WaterBodies     = None
        # - surface water bed conductance (also only change at the beginning of the year)
        self.bed_conductance = None

        # initiate pcraster modflow object to None
        self.pcr_modflow = None

        # the following condition is needed if we have to 
        self.valuesRechargeAndAbstractionInMonthlyTotal = False
        if 'valuesRechargeAndAbstractionInMonthlyTotal' in self.iniItems.modflowTransientInputOptions.keys():
            if self.iniItems.modflowTransientInputOptions['valuesRechargeAndAbstractionInMonthlyTotal'] == "True":\
               self.valuesRechargeAndAbstractionInMonthlyTotal = True
        
        # minimum and maximum transmissivity values (unit: m2/day)
        self.minimumTransmissivity = 10.0     # assumption used by Deltares
        self.maximumTransmissivity = 100000.0 # ridiculosly high (for 20 m/day with the thickness = 5 km)
        if 'minimumTransmissivity' in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['minimumTransmissivity'] != "None":
            self.minimumTransmissivity = float(self.iniItems.modflowParameterOptions['minimumTransmissivity'])
        if 'maximumTransmissivity' in self.iniItems.modflowParameterOptions.keys() and\
            self.iniItems.modflowParameterOptions['maximumTransmissivity'] != "None":
            self.maximumTransmissivity = float(self.iniItems.modflowParameterOptions['maximumTransmissivity'])
        
        # option for online coupling purpose, we also need to know the location of pcrglobwb output
        self.online_coupling = self.iniItems.online_coupling_between_pcrglobwb_and_modflow

        # initiate old style reporting (this is usually used for debugging process)
        self.initiate_old_style_reporting(iniItems)
        
        # option to make backup of modflow files
        self.make_backup_of_modflow_files = False
        if "make_backup_of_modflow_files" in self.iniItems.reportingOptions.keys() and\
           self.iniItems.reportingOptions["make_backup_of_modflow_files"] == "True": self.make_backup_of_modflow_files = True

    def initiate_modflow(self):

        logger.info("Initializing pcraster modflow.")
        
        # TODO: removing all previous pcraster modflow files:
        
        # initialise pcraster modflow
        self.pcr_modflow = pcr.initialise(pcr.clone())
        
        # setup the DIS package specifying the grids/layers used for the groundwater model
        # - Note the layer specification must start with the bottom layer (layer 1 is the lowermost layer)
        if self.number_of_layers == 1: self.set_grid_for_one_layer_model()
        if self.number_of_layers == 2: self.set_grid_for_two_layer_model()
         
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

        # TODO: defining/incorporating anisotrophy values

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
        # - thickness of layer 2 should be until 5 m below the river bed
        bottom_layer_2       = pcr.min(self.dem_riverbed - 5.0, bottom_layer_2)
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
            # - thickness of layer 2 should be until 5 m below the river bed elevation
            bottom_layer_2       = pcr.min(self.dem_riverbed - 5.0, bottom_layer_2)
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
        
    def set_bcf_for_two_layer_model_original(self):

        # specification for storage coefficient (BCF package)

        # layer 2 (upper layer) - storage coefficient
        self.storage_coefficient_2 = self.specificYield
        # - correction due to the usage of lat/lon coordinates
        primary_2   = pcr.cover(self.storage_coefficient_2 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary_2   = pcr.max(1e-20, primary_2)
        secondary_2 = pcr.cover(pcr.min(0.005, self.storage_coefficient_2) * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)    # dummy values as we use layer type 00
        secondary_2 = pcr.max(1e-20, secondary_2)

        # layer 1 (lower layer) - storage coefficient
        self.storage_coefficient_1 = self.specificYield
        # - correction due to the usage of lat/lon coordinates
        primary_1   = pcr.cover(self.storage_coefficient_1 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary_1   = pcr.max(1e-20, primary_1)
        secondary_1 = pcr.cover(pcr.min(0.005, self.storage_coefficient_1) * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)    # dummy values as we use layer type 00
        secondary_1 = pcr.max(1e-20, secondary_1)

        # put the storage coefficient values to the modflow model
        self.pcr_modflow.setStorage(primary_1, secondary_1, 1)
        self.pcr_modflow.setStorage(primary_2, secondary_2, 2)


        # specification for conductivities (BCF package)
        horizontal_conductivity = self.kSatAquifer # unit: m/day
        
        # layer 2 (upper layer) - horizontal conductivity
        horizontal_conductivity_layer_2 = pcr.max(self.minimumTransmissivity, \
                                          horizontal_conductivity * self.thickness_of_layer_2) / self.thickness_of_layer_2
        horizontal_conductivity_layer_2 = pcr.min(self.maximumTransmissivity, \
                                          horizontal_conductivity * self.thickness_of_layer_2) / self.thickness_of_layer_2

        # layer 2 (upper layer) - vertical conductivity
        vertical_conductivity_layer_2   = self.kSatAquifer * self.cellAreaMap/\
                                          (pcr.clone().cellSize()*pcr.clone().cellSize())
        
        if self.usePreDefinedConfiningLayer:

            # vertical conductivity values are limited by the predefined minimumConfiningLayerVerticalConductivity and maximumConfiningLayerResistance
            vertical_conductivity_layer_2  = pcr.min(self.kSatAquifer, self.maximumConfiningLayerVerticalConductivity)
            vertical_conductivity_layer_2  = pcr.ifthenelse(self.confiningLayerThickness > 0.0, vertical_conductivity_layer_2, self.kSatAquifer)
            vertical_conductivity_layer_2  = pcr.max(self.thickness_of_layer_2/self.maximumConfiningLayerResistance, \
                                                     vertical_conductivity_layer_2)
            # minimum resistance is one day
            vertical_conductivity_layer_2  = pcr.min(self.thickness_of_layer_2/1.0,\
                                                     vertical_conductivity_layer_2)
            # correcting vertical conductivity
            vertical_conductivity_layer_2 *= self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize())
        
        # layer 1 (lower layer)
        horizontal_conductivity_layer_1 = pcr.max(self.minimumTransmissivity, \
                                          horizontal_conductivity * self.thickness_of_layer_1) / self.thickness_of_layer_1
        horizontal_conductivity_layer_1 = pcr.min(self.maximumTransmissivity, \
                                          horizontal_conductivity * self.thickness_of_layer_1) / self.thickness_of_layer_1

        # ignoring the vertical conductivity in the lower layer 
        # such that the values of resistance (1/vcont) depend only on vertical_conductivity_layer_2 
        vertical_conductivity_layer_1  = pcr.spatial(pcr.scalar(1e99)) * self.cellAreaMap/\
                                        (pcr.clone().cellSize()*pcr.clone().cellSize())
        vertical_conductivity_layer_2 *= 0.5
        # see: http://inside.mines.edu/~epoeter/583/08/discussion/vcont/modflow_vcont.htm
        
        #~ # for areas with ibound <= 0, we set very high horizontal conductivity values:             # TODO: Check this, shall we implement this?
        #~ horizontal_conductivity_layer_2 = pcr.ifthenelse(self.ibound > 0, horizontal_conductivity_layer_2, \
                                                           #~ pcr.mapmaximum(horizontal_conductivity_layer_2))
        #~ horizontal_conductivity_layer_1 = pcr.ifthenelse(self.ibound > 0, horizontal_conductivity_layer_1, \
                                                           #~ pcr.mapmaximum(horizontal_conductivity_layer_1))

        # set conductivity values to MODFLOW
        self.pcr_modflow.setConductivity(00, horizontal_conductivity_layer_2, \
                                             vertical_conductivity_layer_2, 2)              
        self.pcr_modflow.setConductivity(00, horizontal_conductivity_layer_1, \
                                             vertical_conductivity_layer_1, 1)              

    def set_storages_for_two_layer_model(self):

        msg = "Set storage coefficient for the upper layer (including lat/lon correction)."
        logger.debug(msg)

        # adjusting factor 
        adjust_factor = 1.00
        if 'linear_multiplier_for_storage_coefficients' in self.iniItems.modflowParameterOptions.keys():
            linear_multiplier_for_storage_coefficients = float(self.iniItems.modflowParameterOptions['linear_multiplier_for_storage_coefficients'])
            adjust_factor                              = linear_multiplier_for_storage_coefficients
        
        # minimum and maximum values of storage coefficients
        minimum_storage_coefficient = 1e-10
        maximum_storage_coefficient = 0.500
        msg = 'The minimum storage coefficient value is limited to (-) ' + str(minimum_storage_coefficient)  
        logger.debug(msg)
        msg = 'The maximum storage coefficient value is limited to (-) ' + str(maximum_storage_coefficient)  
        logger.debug(msg)


        # layer 2 (upper layer) - storage coefficient
        self.storage_coefficient_2  = self.specificYield

        # adjusting factor and set minimum and maximum values to keep values realistics
        self.storage_coefficient_2  = adjust_factor * self.storage_coefficient_2
        self.storage_coefficient_2  = pcr.min(maximum_storage_coefficient, pcr.max(minimum_storage_coefficient, self.storage_coefficient_2))
        
        # - correction due to the usage of lat/lon coordinates
        primary_2   = pcr.cover(self.storage_coefficient_2 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary_2   = pcr.max(1e-20, primary_2)

        # - dummy values for the secondary term - as we use layer type 00
        secondary_2 = primary_2


        msg = "Set storage coefficient for the lower layer (including lat/lon correction)."
        logger.debug(msg)
        # layer 1 (lower layer) - storage coefficient
        self.storage_coefficient_1 = self.specificYield

        # - correction due to the usage of lat/lon coordinates
        primary_1   = pcr.cover(self.storage_coefficient_1 * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        primary_1   = pcr.max(1e-20, primary_1)

        # adjusting factor and set minimum and maximum values to keep values realistics
        self.storage_coefficient_1  = adjust_factor * self.storage_coefficient_1
        self.storage_coefficient_1  = pcr.min(maximum_storage_coefficient, pcr.max(minimum_storage_coefficient, self.storage_coefficient_1))

        # - dummy values for the secondary term - as we use layer type 00
        secondary_1 = primary_1


        msg = "Assign storage coefficient values to the MODFLOW (BCF package)."
        logger.debug(msg)
        # put the storage coefficient values to the modflow model
        self.pcr_modflow.setStorage(primary_1, secondary_1, 1)
        self.pcr_modflow.setStorage(primary_2, secondary_2, 2)


    def set_conductivities_for_two_layer_model(self):

        msg = "Preparing transmissivity values (TRAN) for the BCF package)."
        logger.debug(msg)

        
        # adjusting factor for horizontal conductivities 
        adjust_factor_for_horizontal_conductivities = 1.00
        if 'log_10_multiplier_for_transmissivities' in self.iniItems.modflowParameterOptions.keys():
            log_10_multiplier_for_transmissivities      = float(self.iniItems.modflowParameterOptions['log_10_multiplier_for_transmissivities'])
            adjust_factor_for_horizontal_conductivities = 10.0**(log_10_multiplier_for_transmissivities)
        
        
        # minimum and maximum values for transmissivity
        maxTransmissivity = adjust_factor_for_horizontal_conductivities * self.maximumTransmissivity
        minTransmissivity = self.minimumTransmissivity        # to keep it realistic, this one should not be multiplied
        msg = 'The minimum transmissivity value is limited to (m2/day) ' + str(minTransmissivity)  
        logger.debug(msg)
        msg = 'The maximum transmissivity value is limited to (m2/day) ' + str(maxTransmissivity)  
        logger.debug(msg)

        
        msg = "Assign horizontal conductivities of the upper layer (used for calculating transmissivity (TRAN) for the BCF package)."
        logger.debug(msg)
        horizontal_conductivity_layer_2 = adjust_factor_for_horizontal_conductivities * self.kSatAquifer
        
        # layer 2 (upper layer) - horizontal conductivity
        msg = "Constrained by minimum and maximum transmissity values."
        logger.debug(msg)
        horizontal_conductivity_layer_2 = pcr.min(minTransmissivity, \
                                          horizontal_conductivity_layer_2 * self.thickness_of_layer_2) / self.thickness_of_layer_2
        horizontal_conductivity_layer_2 = pcr.max(maxTransmissivity, \
                                          horizontal_conductivity_layer_2 * self.thickness_of_layer_2) / self.thickness_of_layer_2

        # transmissivity values for the upper layer (layer 2) - unit: m2/day
        self.transmissivity_layer_2 = horizontal_conductivity_layer_2 * self.thickness_of_layer_2
        
        
        msg = "Assign horizontal conductivities of the lower layer (used for calculating transmissivity (TRAN) for the BCF package)."
        logger.debug(msg)
        horizontal_conductivity_layer_1 = adjust_factor_for_horizontal_conductivities * self.kSatAquifer


        # layer 1 (lower layer) - horizontal conductivity 
        msg = "Constrained by minimum and maximum transmissity values."
        logger.debug(msg)
        horizontal_conductivity_layer_1 = pcr.max(minTransmissivity, \
                                          horizontal_conductivity_layer_1 * self.thickness_of_layer_1) / self.thickness_of_layer_1
        horizontal_conductivity_layer_1 = pcr.min(maxTransmissivity, \
                                          horizontal_conductivity_layer_1 * self.thickness_of_layer_1) / self.thickness_of_layer_1
                                          
        # transmissivity values for the lower layer (layer 1) - unit: m2/day
        self.transmissivity_layer_1 = horizontal_conductivity_layer_1 * self.thickness_of_layer_1



        msg = "Preparing VCONT (day-1) values (1/resistance) between upper and lower layers for the BCF package (including the correction due to the lat/lon usage)."
        logger.debug(msg)

        
        # adjusting factor for resistance values  
        adjust_factor_for_resistance_values = 1.00
        if 'log_10_multiplier_for_resistance_values' in self.iniItems.modflowParameterOptions.keys():
            log_10_multiplier_for_resistance_values  = float(self.iniItems.modflowParameterOptions['log_10_multiplier_for_resistance_values'])
            adjust_factor_for_resistance_values      = 10.0**(log_10_multiplier_for_resistance_values)
        
        # minimum and maximum resistance values (unit: days)
        minResistance = 1.0   # to keep it realistic, this one should not be multiplied
        maxResistance = adjust_factor_for_resistance_values * self.maximumConfiningLayerResistance
        msg = 'The minimum resistance (days) between upper and lower layers (1/VCONT) is limited to ' + str(minResistance)  
        logger.debug(msg)
        msg = 'The maximum resistance (days) between upper and lower layers (1/VCONT) is limited to ' + str(maxResistance)  
        logger.debug(msg)


        msg = "Assign vertical conductivities to determine VCONT values (1/resistance) between upper and lower layers (used for calculating VCONT for the BCF package)."
        logger.debug(msg)
        vertical_conductivity_layer_2 = self.kSatAquifer
        
        if self.usePreDefinedConfiningLayer:
            
            msg = "In areas with confining layer, limit vertical conductivity to the given map/value of maximumConfiningLayerVerticalConductivity"
            logger.debug(msg)
            # vertical conductivity values are limited by the predefined minimumConfiningLayerVerticalConductivity
            vertical_conductivity_layer_2  = pcr.min(self.kSatAquifer, self.maximumConfiningLayerVerticalConductivity)
            # particularly in areas with confining layer
            vertical_conductivity_layer_2  = pcr.ifthenelse(self.confiningLayerThickness > 0.0, vertical_conductivity_layer_2, self.kSatAquifer)
        
        # adjusment according to "adjust_factor_for_resistance_values":
        vertical_conductivity_layer_2 = (1.0/adjust_factor_for_resistance_values) * vertical_conductivity_layer_2
        
        # vertical conductivity values are limited by minimum and maximum resistance values
        msg = "Constrained by minimum and maximum resistance values."
        logger.debug(msg)
        vertical_conductivity_layer_2  = pcr.max(self.thickness_of_layer_2/maxResistance, \
                                                 vertical_conductivity_layer_2)
        vertical_conductivity_layer_2  = pcr.min(self.thickness_of_layer_2/minResistance,\
                                                     vertical_conductivity_layer_2)

        # resistance values between upper and lower layers - unit: days
        self.resistance   = self.thickness_of_layer_2 / vertical_conductivity_layer_2
        # VCONT values
        self.vcont_values = pcr.scalar(1.0) / self.resistance 

        # ignoring the vertical conductivity in the lower layer 
        # such that the values of resistance (1/vcont) depend only on vertical_conductivity_layer_2 
        vertical_conductivity_layer_1  = pcr.spatial(pcr.scalar(1e99))
        vertical_conductivity_layer_2 *= 0.5
        # see: http://inside.mines.edu/~epoeter/583/08/discussion/vcont/modflow_vcont.htm
        
        # correcting vertical conductivity due the lat/lon usage
        msg = "Correction due to the lat/lon usage."
        logger.debug(msg)
        vertical_conductivity_layer_2 *= self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize())
        vertical_conductivity_layer_1 *= self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize())

        
        # set conductivity values to MODFLOW
        msg = "Assign conductivity values to the MODFLOW (BCF package)."
        logger.debug(msg)
        self.pcr_modflow.setConductivity(00, horizontal_conductivity_layer_2, \
                                             vertical_conductivity_layer_2, 2)              
        self.pcr_modflow.setConductivity(00, horizontal_conductivity_layer_1, \
                                             vertical_conductivity_layer_1, 1)              

    def set_bcf_for_two_layer_model(self):

        # specification for storage coefficient (BCF package)
        self.set_storages_for_two_layer_model()

        # specification for conductivities (BCF package)
        self.set_conductivities_for_two_layer_model()

    def get_initial_heads(self):
		
        if self.iniItems.modflowTransientInputOptions['usingPredefinedInitialHead'] == "True": 
        
            msg = "Using pre-defined groundwater head(s) given in the ini/configuration file."
            logger.info(msg)
            
            # using pre-defined groundwater head(s) described in the ini/configuration file
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

        self.transient_simulation_with_constant_input_with_monthly_stress_period()
        self.transient_simulation_with_constant_input_with_yearly_stress_period()
        self.transient_simulation_with_constant_input_with_10year_stress_period()

    def transient_simulation_with_constant_input_with_monthly_stress_period(self):

        time_step_length         = 30                # unit: days
        number_of_sub_time_steps = time_step_length  # daily resolution

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

        time_step_length         = 365               # unit: days
        number_of_sub_time_steps = 365               # daily resolution

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

        time_step_length         = 365 * 10           # unit: days
        number_of_sub_time_steps =  10 * 52 * 2       # semi-weekly resolution

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

    def estimate_bottom_of_bank_storage(self):

        # influence zone depth (m)  # TODO: Define this one as part of 
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


    def update(self,currTimeStep):

        # at the end of the month, calculate/simulate a steady state condition and obtain its calculated head values
        if currTimeStep.isLastDayOfMonth():

            # get the previous state
            groundwaterHead = self.getState()
            
            # length of a stress period
            PERLEN = currTimeStep.day
            if currTimeStep.startTime.day != 1 and currTimeStep.monthIdx == 1:
                PERLEN = currTimeStep.day - currTimeStep.startTime.day + 1 
            
            # number of time step within a stress period
            NSTP = PERLEN * 3
            
            self.PERLEN = PERLEN   # number of days within a stress period
            self.NSTP   = NSTP     # number of time steps within a stress period
            
            self.modflow_simulation("transient", groundwaterHead, 
                                                 currTimeStep, 
                                                 PERLEN, 
                                                 NSTP)

            # old-style reporting (this is usually used for debugging process)                            
            self.old_style_reporting(currTimeStep)

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
            #
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

                # for online coupling, we will read files from pcraster maps
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
                    channelStorage = vos.netcdf2PCRobjClone(self.iniItems.modflowTransientInputOptions['channelStorageInputNC'],\
                                                           "channel_storage", str(currTimeStep.fulldate), None, self.cloneMap)
                    channelStorage = pcr.cover(channelStorage, 0.0)                                       


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

        # convert the values of abstraction and recharge to daily average
        if self.valuesRechargeAndAbstractionInMonthlyTotal: 
            gwAbstraction = gwAbstraction/currTimeStep.day
            gwRecharge    = gwRecharge/currTimeStep.day

        # set recharge, river, well and drain packages
        self.set_drain_and_river_package(discharge, channelStorage, currTimeStep, simulation_type)
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

        # DAMP parameters (this may help the convergence during the steady-state simulation)
        self.parameter_DAMP = [1.0] 
        if simulation_type == "steady-state": self.parameter_DAMP = [1.0, 0.80, 0.60] 

        # initiate the index for HCLOSE and RCLOSE for the interation until modflow_converged
        self.iteration_HCLOSE = 0
        self.iteration_RCLOSE = 0
        self.iteration_DAMP   = 0
        self.modflow_converged = False

        # execute MODFLOW 
        while self.modflow_converged == False:
            
            # convergence criteria 
            HCLOSE = self.criteria_HCLOSE[self.iteration_HCLOSE]
            RCLOSE = self.criteria_RCLOSE[self.iteration_RCLOSE]
            
            # damping parameter
            DAMP = self.parameter_DAMP[self.iteration_DAMP]
            
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
                self.pcr_modflow.run()
                self.modflow_converged = self.pcr_modflow.converged()           # TODO: Ask Oliver to fix the non-convergence issue that can appear before reaching the end of stress period.  
                #~ self.modflow_converged = self.old_check_modflow_convergence()
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
        
        # copy all modflow files
        if self.make_backup_of_modflow_files: 
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

    def set_drain_and_river_package(self, discharge, channel_storage, currTimeStep, simulation_type):

        logger.info("Set the river package.")
        
        # set WaterBodies class to define the extent of lakes and reservoirs (constant for the entie year, annual resolution)
        # and also set drain package (constant for the entire year, unless there are changes in the WaterBodies class)
        if simulation_type == "steady-state" or simulation_type == "steady-state-extra":
            self.WaterBodies = waterBodies.WaterBodies(self.iniItems,\
                                                       self.landmask,\
                                                       self.onlyNaturalWaterBodies)
            self.WaterBodies.getParameterFiles(date_given = self.iniItems.globalOptions['startTime'],\
                                               cellArea = self.cellAreaMap, \
                                               ldd = self.lddMap)
        if simulation_type == "transient":
            if self.WaterBodies == None:
                self.WaterBodies = waterBodies.WaterBodies(self.iniItems,\
                                                           self.landmask,\
                                                           self.onlyNaturalWaterBodies)
                self.WaterBodies.getParameterFiles(date_given = str(currTimeStep.fulldate),\
                                                   cellArea = self.cellAreaMap, \
                                                   ldd = self.lddMap)        
            if currTimeStep.month == 1:
                self.WaterBodies.getParameterFiles(date_given = str(currTimeStep.fulldate),\
                                                   cellArea = self.cellAreaMap, \
                                                   ldd = self.lddMap)        

        # reset bed conductance at the first month (due to possibility of new inclusion of lakes/reservoirs)
        if currTimeStep == None or currTimeStep.month == 1: self.bed_conductance = None
        
        if isinstance(self.bed_conductance, types.NoneType):

            logger.info("Estimating surface water bed elevation.")
        
            #~ # - for lakes and resevoirs, alternative 1: make the bottom elevation deep --- Shall we do this? NOTE: This will provide unrealistic groundwater depth. Need further investigations (consider to use US). 
            #~ additional_depth = 1500.
            #~ surface_water_bed_elevation = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, \
                                                     #~ self.dem_riverbed - additional_depth)
            #
            #~ # - for lakes and resevoirs, alternative 2: estimate bed elevation from dem and bankfull depth
            #~ surface_water_bed_elevation  = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, self.dem_average)
            #~ surface_water_bed_elevation  = pcr.areaaverage(surface_water_bed_elevation, self.WaterBodies.waterBodyIds)
            #~ surface_water_bed_elevation -= pcr.areamaximum(self.bankfull_depth, self.WaterBodies.waterBodyIds) 
            
            # - for lakes and resevoirs, alternative 3: estimate bed elevation from DEM only
            #                                           This is to avoid that groundwater heads fall too far below DEM
            #                                           This will also smooth groundwater heads.     
            surface_water_bed_elevation  = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, self.dem_average)
            
            # surface water bed elevation for rivers, lakes and reservoirs
            surface_water_bed_elevation  = pcr.cover(surface_water_bed_elevation, self.dem_riverbed)
            #~ surface_water_bed_elevation = self.dem_riverbed # This is an alternative, if we do not want to introduce very deep bottom elevations of lakes and/or reservoirs.   
            
            # rounding values for surface_water_bed_elevation
            self.surface_water_bed_elevation = pcr.rounddown(surface_water_bed_elevation * 100.)/100.


            logger.info("Estimating surface water bed conductance.")

            ############################################################################################################################################
            # lake and reservoir fraction (dimensionless)
            lake_and_reservoir_fraction = pcr.cover(\
                                          pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, \
                                                     self.WaterBodies.fracWat), 0.0)
            # river fraction (dimensionless)
            river_fraction = (1.0 - lake_and_reservoir_fraction) * (self.bankfull_width * self.channelLength)/self.cellAreaMap
            
            # lake and reservoir resistance (day)
            lake_and_reservoir_resistance = self.bed_resistance

            # - assuming a minimum resistance (due to the sedimentation, conductivity: 0.001 m/day and thickness 0.50 m)
            lake_and_reservoir_resistance  = pcr.max(0.50 / 0.001, self.bed_resistance)

            #~ # to further decrease bed conductance in lakes and reservoir, we limit the lake and reservoir fraction as follows:
            #~ lake_and_reservoir_fraction = pcr.cover(\
                                          #~ pcr.min(lake_and_reservoir_fraction,\
                                          #~ pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, \
                                          #~ pcr.areaaverage(self.bankfull_width * self.channelLength, self.WaterBodies.waterBodyIds))), 0.0)

            #~ # make the lake and reservor resistance even higher (to avoid too high seepage)   # TODO: Investigate this !!!!             
            #~ lake_and_reservoir_resistance *= 10.

            # lake and reservoir conductance (m2/day)
            lake_and_reservoir_conductance = (1.0/lake_and_reservoir_resistance) * lake_and_reservoir_fraction * \
                                                  self.cellAreaMap
            # river conductance (m2/day)
            river_conductance = (1.0/self.bed_resistance) * river_fraction *\
                                                            self.cellAreaMap
            
            # surface water bed condutance (unit: m2/day)
            bed_conductance = lake_and_reservoir_conductance + river_conductance
            self.bed_conductance = pcr.cover(bed_conductance, 0.0)
            ############################################################################################################################################
            
            # set minimum conductance values (to remove water above surface level)
            # - assume all cells have minimum river width
            minimum_width = 2.0   # Sutanudjaja et al. (2011)
            minimum_conductance = (1.0/self.bed_resistance) * \
                                  pcr.max(minimum_width, self.bankfull_width) * self.channelLength/self.cellAreaMap
            self.bed_conductance = pcr.max(minimum_conductance, self.bed_conductance)

            logger.info("Estimating outlet widths of lakes and/or reservoirs.")
            # - 'channel width' for lakes and reservoirs 
            channel_width = pcr.areamaximum(self.bankfull_width, self.WaterBodies.waterBodyIds)
            self.channel_width = pcr.cover(channel_width, self.bankfull_width)


        logger.info("Estimating surface water elevation.")
        
        # - convert discharge value to surface water elevation (m)
        river_water_height = (self.channel_width**(-3/5)) * (discharge**(3/5)) * ((self.gradient)**(-3/10)) *(self.manningsN**(3/5))
        surface_water_elevation = self.dem_riverbed + \
                                  river_water_height
        #
        # - calculating water level (unit: m) above the flood plain   # TODO: Improve this concept (using Rens's latest innundation scheme) 
        #----------------------------------------------------------
        water_above_fpl  = pcr.max(0.0, surface_water_elevation - self.dem_floodplain)   # unit: m, water level above the floodplain (not distributed)
        water_above_fpl *= self.bankfull_depth * self.channel_width / self.cellAreaMap   # unit: m, water level above the floodplain (distributed within the cell)
        # TODO: Improve this concept using Rens's latest scheme
        #
        # - corrected surface water elevation
        surface_water_elevation = pcr.ifthenelse(surface_water_elevation > self.dem_floodplain, \
                                                                           self.dem_floodplain + water_above_fpl, \
                                                                           surface_water_elevation)
        # - surface water elevation for lakes and reservoirs:
        lake_reservoir_water_elevation = pcr.ifthen(self.WaterBodies.waterBodyOut, pcr.min(surface_water_elevation, self.dem_floodplain))
        lake_reservoir_water_elevation = pcr.areamaximum(lake_reservoir_water_elevation, self.WaterBodies.waterBodyIds)
        lake_reservoir_water_elevation = pcr.cover(lake_reservoir_water_elevation, \
                                         pcr.areaaverage(surface_water_elevation, self.WaterBodies.waterBodyIds))
        # - maximum and minimum values for lake_reservoir_water_elevation
        lake_reservoir_water_elevation = pcr.min(self.dem_floodplain, lake_reservoir_water_elevation)
        lake_reservoir_water_elevation = pcr.max(self.surface_water_bed_elevation, lake_reservoir_water_elevation)
        # - smoothing
        lake_reservoir_water_elevation = pcr.areaaverage(surface_water_elevation, self.WaterBodies.waterBodyIds)
        lake_reservoir_water_elevation = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, lake_reservoir_water_elevation)
        # 
        # - to minimize negative channel storage, ignore river infiltration in smaller rivers ; no infiltration if HRIV = RBOT (and h < RBOT)  
        minimum_channel_width = 5.0
        surface_water_elevation = pcr.ifthenelse(self.channel_width > minimum_channel_width, surface_water_elevation, \
                                                                                        self.surface_water_bed_elevation)
        #
        # - merge lake and reservoir water elevation
        surface_water_elevation = pcr.cover(lake_reservoir_water_elevation, surface_water_elevation)
        #
        # - covering missing values and rounding
        surface_water_elevation = pcr.cover(surface_water_elevation, self.dem_average)
        surface_water_elevation = pcr.rounddown(surface_water_elevation * 1000.)/1000.
        #
        # - make sure that HRIV >= RBOT ; no infiltration if HRIV = RBOT (and h < RBOT)  
        surface_water_elevation = pcr.max(surface_water_elevation, self.surface_water_bed_elevation)
        

        # - to minimize negative channel storage, ignore river infiltration with low surface_water_elevation
        minimum_water_height  = 0.50
        surface_water_elevation = pcr.ifthenelse((surface_water_elevation - self.surface_water_bed_elevation) > minimum_water_height, surface_water_elevation, \
                                                                                                                                      self.surface_water_bed_elevation)
        # - to minimize negative channel storage, ignore river infiltration with low channel storage
        if not isinstance(channel_storage, types.NoneType):
            minimum_channel_storage = pcr.max(0.0, 0.10 * self.bankfull_depth * self.bankfull_width * self.channelLength)   # unit: m3
            surface_water_elevation = pcr.ifthenelse(channel_storage > minimum_channel_storage, surface_water_elevation, self.surface_water_bed_elevation)

        # - also ignore river infiltration in the mountainous region
        mountainous_extent  = pcr.cover(\
                              pcr.ifthen((self.dem_average - self.dem_floodplain) > 50.0, pcr.boolean(1.0)), pcr.boolean(0.0))
        surface_water_elevation = pcr.ifthenelse(mountainous_extent, self.surface_water_bed_elevation, surface_water_elevation)

        # make sure that HRIV >= RBOT ; no infiltration if HRIV = RBOT (and h < RBOT)  
        surface_water_elevation = pcr.rounddown(surface_water_elevation * 1000.)/1000.
        surface_water_elevation = pcr.max(surface_water_elevation, self.surface_water_bed_elevation)

        # reducing the size of table by ignoring cells outside the landmask region 
        bed_conductance_used = pcr.ifthen(self.landmask, self.bed_conductance)
        bed_conductance_used = pcr.cover(bed_conductance_used, 0.0)
        
        
        #~ # for the case HRIV == RBOT, we can use drain package --------- NOT NEEDED
        #~ additional_drain_elevation   = pcr.cover(\
                                       #~ pcr.ifthen(surface_water_elevation <= self.surface_water_bed_elevation, self.surface_water_bed_elevation), 0.0)
        #~ additional_drain_conductance = pcr.cover(\
                                       #~ pcr.ifthen(surface_water_elevation <= self.surface_water_bed_elevation, bed_conductance_used), 0.0)
        #~ bed_conductance_used = \
                              #~ pcr.ifthenelse(surface_water_elevation <= self.surface_water_bed_elevation, 0.0, bed_conductance_used)
        #~ #
        #~ # set the DRN package only to the uppermost layer
        #~ self.pcr_modflow.setDrain(additional_drain_elevation, \
                                  #~ additional_drain_conductance, self.number_of_layers)

        
        # set the RIV package only to the uppermost layer
        self.pcr_modflow.setRiver(surface_water_elevation, self.surface_water_bed_elevation, bed_conductance_used, self.number_of_layers)
        
        # TODO: Improve the concept of RIV package, particularly while calculating surface water elevation in lakes and reservoirs

        # set drain package
        self.set_drain_package()                                         
        
        
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

        # adjustment factor
        adjusting_factor = 1.0
        net_recharge = net_recharge * adjusting_factor
        
        # - correcting values (considering MODFLOW lat/lon cell properties)
        #   and pass them to the RCH package   
        net_RCH = pcr.cover(net_recharge * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        net_RCH = pcr.cover(pcr.ifthenelse(pcr.abs(net_RCH) < 1e-20, 0.0, net_RCH), 0.0)
        
        # put the recharge to the top grid/layer
        self.pcr_modflow.setRecharge(net_RCH, 1)

        #~ # if we want to put RCH in the lower layer
        #~ self.pcr_modflow.setIndicatedRecharge(net_RCH, pcr.spatial(pcr.nominal(1)))

    def set_well_package(self, gwAbstraction):

        logger.info("Set the well package.")

        if self.number_of_layers == 1: self.set_well_package_for_one_layer_model(gwAbstraction)
        if self.number_of_layers == 2: self.set_well_package_for_two_layer_model(gwAbstraction)

    def set_well_package_for_one_layer_model(self, gwAbstraction):
		
        gwAbstraction = pcr.cover(gwAbstraction, 0.0)
        gwAbstraction = pcr.max(gwAbstraction, 0.0)

        # adjustment factor
        adjusting_factor = 1.0
        gwAbstraction = gwAbstraction * adjusting_factor

        # abstraction volume (negative value, unit: m3/day)
        abstraction = pcr.cover(gwAbstraction, 0.0) * self.cellAreaMap * pcr.scalar(-1.0)
        
        # set the well package
        self.pcr_modflow.setWell(abstraction, 1)

    def set_well_package_for_two_layer_model(self, gwAbstraction):
		
        gwAbstraction = pcr.cover(gwAbstraction, 0.0)
        gwAbstraction = pcr.max(gwAbstraction, 0.0)
        
        # adjustment factor
        adjusting_factor = 1.0
        gwAbstraction = gwAbstraction * adjusting_factor

        # abstraction for the layer 1 (lower layer) is limited only in productive aquifer
        abstraction_layer_1 = pcr.cover(pcr.ifthen(self.productive_aquifer, gwAbstraction), 0.0)
        
        # abstraction for the layer 2 (upper layer)
        abstraction_layer_2 = pcr.max(0.0, gwAbstraction - abstraction_layer_1)
        
        # TODO: Distribute gwAbstraction based on KD value of each layer
        
        # abstraction volume (negative value, unit: m3/day)
        abstraction_layer_1 = abstraction_layer_1 * self.cellAreaMap * pcr.scalar(-1.0)
        abstraction_layer_2 = abstraction_layer_2 * self.cellAreaMap * pcr.scalar(-1.0)
        
        # set the well package
        self.pcr_modflow.setWell(abstraction_layer_1, 1)
        self.pcr_modflow.setWell(abstraction_layer_2, 2)

    def set_well_package_OLD(self, gwAbstraction):
        
        logger.info("Set the well package.")
        
        # reducing the size of table by ignoring cells with zero abstraction
        gwAbstraction = pcr.ifthen(gwAbstraction > 0.0, gwAbstraction)
        
        # abstraction only in productive aquifer
        gwAbstraction = pcr.ifthen(self.productive_aquifer, gwAbstraction)
        
        # abstraction volume (negative value, unit: m3/day)
        abstraction = gwAbstraction * self.cellAreaMap * pcr.scalar(-1.0)
        
        # FIXME: The following cover operations should not be necessary (Oliver should fix this).
        abstraction = pcr.cover(abstraction, 0.0) 
        
        # set the well based on number of layers
        if self.number_of_layers == 1: self.pcr_modflow.setWell(abstraction, 1)
        if self.number_of_layers == 2: self.pcr_modflow.setWell(abstraction, 1) # at the bottom layer
        
        #~ print('test')

    def set_drain_package(self):

        logger.info("Set the drain package (for the release of over bank storage).")

        # specify the drain package the drain package is used to simulate the drainage of bank storage 

        # - estimate bottom of bank storage for flood plain areas
        drain_elevation = self.estimate_bottom_of_bank_storage()                               # unit: m
        
        # - for lakes and/or reservoirs, ignore the drainage
        drain_conductance = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, pcr.scalar(0.0))
        # - drainage conductance is a linear reservoir coefficient
        drain_conductance = pcr.cover(drain_conductance, \
                            self.recessionCoeff * self.specificYield * self.cellAreaMap)       # unit: m2/day

        #~ drain_conductance = pcr.ifthenelse(drain_conductance < 1e-20, 0.0, \
                                           #~ drain_conductance) 
        #~ drain_conductance = pcr.rounddown(drain_conductance*10000.)/10000.                  # It is not a good idea to round the values down (water can be trapped).  

        # reducing the size of table by ignoring cells outside landmask region
        drain_conductance = pcr.ifthen(self.landmask, drain_conductance)
        drain_conductance = pcr.cover(drain_conductance, 0.0)
        
        #~ # set the DRN package only to the uppermost layer
        #~ self.pcr_modflow.setDrain(drain_elevation, drain_conductance, self.number_of_layers)

        # set the DRN package only to both layers ------ 4 January 2016: I think that we should use this as we want all recharge will be released as baseflow.
        self.pcr_modflow.setDrain(drain_elevation, drain_conductance, 1)
        self.pcr_modflow.setDrain(drain_elevation, drain_conductance, 2)

        #~ # set the DRN package only to the lowermost layer
        #~ self.pcr_modflow.setDrain(drain_elevation, drain_conductance, 1)
        #~ self.pcr_modflow.setDrain(pcr.spatial(pcr.scalar(0.0)),pcr.spatial(pcr.scalar(0.0)), 2)


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

