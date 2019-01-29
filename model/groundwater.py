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

import math
import subprocess
import os
import types

from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

try:
    import groundwater_MODFLOW as gw_modflow
except:
    pass

import virtualOS as vos
from ncConverter import *

class Groundwater(object):

    def getState(self):
        result = {}
        result['storGroundwater']                        = self.storGroundwater                # unit: m
        result['storGroundwaterFossil']                  = self.storGroundwaterFossil          # unit: m
        result['avgTotalGroundwaterAbstraction']         = self.avgAbstraction                 # unit: m/day
        result['avgTotalGroundwaterAllocationLong']      = self.avgAllocation                  # unit: m/day
        result['avgTotalGroundwaterAllocationShort']     = self.avgAllocationShort             # unit: m/day
        result['avgNonFossilGroundwaterAllocationLong']  = self.avgNonFossilAllocation         # unit: m/day
        result['avgNonFossilGroundwaterAllocationShort'] = self.avgNonFossilAllocationShort    # unit: m/day

        # states needed for the coupling between PCR-GLOBWB and MODFLOW:
        result['relativeGroundwaterHead'] = self.relativeGroundwaterHead                       # unit: m
        result['baseflow']                = self.baseflow                                      # unit: m/day

        # states needed for (daily) coupling with MODFLOW
        if self.coupleToDailyMODFLOW:
            for i in range(1, self.gw_modflow.number_of_layers+1):
                var_name = 'groundwaterHeadLayer'+str(i)
                result[var_name] = vars(self.gw_modflow)[var_name]                                           
        
        return result

    def getPseudoState(self):
        result = {}

        return result

    def __init__(self, iniItems, landmask, spinUp, initial_condition_is_required = True):
        object.__init__(self)

        # configuration from the ini file
        self.iniItems = iniItems

        self.cloneMap = self.iniItems.cloneMap
        self.tmpDir   = self.iniItems.tmpDir
        self.inputDir = self.iniItems.globalOptions['inputDir']
        self.landmask = landmask

        # option to activate a water balance check
        self.debugWaterBalance = True
        if iniItems.groundwaterOptions['debugWaterBalance'] == "False": self.debugWaterBalance = False

        # MODFLOW option
        self.useMODFLOW = False
        if 'useMODFLOW' in iniItems.groundwaterOptions.keys() and iniItems.groundwaterOptions['useMODFLOW'] == "True": self.useMODFLOW = True
        
        # option for daily coupling to MODFLOW
        self.coupleToDailyMODFLOW = False
        if "coupleToDailyMODFLOW" in iniItems.groundwaterOptions.keys() and iniItems.groundwaterOptions['coupleToDailyMODFLOW'] == "True":
            self.useMODFLOW = True
            self.coupleToDailyMODFLOW = True
        
        
        if self.useMODFLOW: logger.info("Coupling to MODFLOW is activated.")
        if self.coupleToDailyMODFLOW:
            logger.info("MODFLOW stress period is daily.")    
        if self.coupleToDailyMODFLOW == False and self.useMODFLOW:
            logger.info("MODFLOW stress period is monthly.")    

        # option/setting for offline MODFLOW coupling (running MODFLOW based on a set of predefined PCR-GLOBWB output files)
        self.modflowOfflineCoupling = False
        if "modflowOfflineCoupling" in self.iniItems.globalOptions.keys() and\
            self.iniItems.globalOptions['modflowOfflineCoupling'] == "True":
            self.modflowOfflineCoupling = True	 
        #####################################################################################################################################################
        # limitAbstraction options
        self.limitAbstraction = False
        if self.modflowOfflineCoupling == False and 'limitAbstraction' in iniItems.landSurfaceOptions.keys() and iniItems.landSurfaceOptions['limitAbstraction'] == "True": self.limitAbstraction = True

        # option for limitting fossil groundwater abstractions:
        self.limitFossilGroundwaterAbstraction = False
        if self.modflowOfflineCoupling == False and iniItems.groundwaterOptions['limitFossilGroundWaterAbstraction'] == "True":
            self.limitFossilGroundwaterAbstraction = True

        # if using MODFLOW, limitAbstraction must be True: the abstraction cannot exceed storGroundwater (consequently, the concept of fossil groundwater is abandoned):
        if self.useMODFLOW:
            self.limitAbstraction = True
            self.limitFossilGroundwaterAbstraction = False              
            # TODO: Please check! It seems that the latter is not necessary.   

        # option for limitting regional groundwater abstractions
        if self.modflowOfflineCoupling == False and 'pumpingCapacityNC' in iniItems.groundwaterOptions.keys():
            if iniItems.groundwaterOptions['pumpingCapacityNC'] != "None":
                logger.info('Limit for annual regional groundwater abstraction (groundwater pumping capacity) is used.')
                self.limitRegionalAnnualGroundwaterAbstraction = True
                self.pumpingCapacityNC = vos.getFullPath(\
                                         iniItems.groundwaterOptions['pumpingCapacityNC'], self.inputDir, False)
            else:
                logger.warning('NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction.')
                self.limitRegionalAnnualGroundwaterAbstraction = False
        #####################################################################################################################################################


        ####################################################################################################################
        # a netcdf file containing the groundwater properties
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] != "None":
            groundwaterPropertiesNC = vos.getFullPath(iniItems.groundwaterOptions['groundwaterPropertiesNC'], self.inputDir)
        ####################################################################################################################


        #####################################################################################################################################################
        # assign aquifer specific yield (dimensionless)
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == "None" or 'specificYield' in iniItems.groundwaterOptions.keys():
            self.specificYield  = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['specificYield'], self.cloneMap, self.tmpDir, self.inputDir)
        else:
            self.specificYield = vos.netcdf2PCRobjCloneWithoutTime(\
                                 groundwaterPropertiesNC, 'specificYield', self.cloneMap)
        
        # minimum and maximum values for aquifer specific yield (dimensionless)
        self.specificYield = pcr.cover(self.specificYield, 0.00)
        self.specificYield = pcr.min(1.0000, self.specificYield)
        if 'minSpecificYield' in iniItems.groundwaterOptions.keys():
            minSpecificYield = float(iniItems.groundwaterOptions['minSpecificYield'])
        else:
            msg  = 'The option "minSpecificYield" is not defined in the "groundwaterOptions" of the configuration file. '
            msg += 'This run assumes 0.01 for this option.'
            logger.warning(msg)
            minSpecificYield = 0.01
        # - the minimum value may be automatically set in the configuration.py 
        self.specificYield = pcr.max(minSpecificYield, self.specificYield)
        #~ pcr.aguila(self.specificYield)
        #####################################################################################################################################################


        #####################################################################################################################################################
        # assign aquifer hydraulic conductivity (unit: m/day)
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == "None" or 'kSatAquifer' in iniItems.groundwaterOptions.keys():
            self.kSatAquifer = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['kSatAquifer'],self.cloneMap,self.tmpDir,self.inputDir)
        else:
            self.kSatAquifer = vos.netcdf2PCRobjCloneWithoutTime(\
                               groundwaterPropertiesNC,'kSatAquifer', self.cloneMap)

        # minimum kSatAquifer (m.day-1)
        self.kSatAquifer = pcr.cover(self.kSatAquifer, 0.0)
        if 'minAquiferSatConductivity' in iniItems.groundwaterOptions.keys():
            minAquiferSatConductivity = float(iniItems.groundwaterOptions['minAquiferSatConductivity'])
        else:
            msg  = 'The option "minAquiferSatConductivity" is not defined in the "groundwaterOptions" of the configuration file. '
            msg += 'This run assumes 0.01 for this option.'
            logger.warning(msg)
            minAquiferSatConductivity = 0.01
        # - the minimum value may be automatically set in the configuration.py 
        self.kSatAquifer = pcr.max(minAquiferSatConductivity, self.kSatAquifer)              
        #~ pcr.aguila(self.kSatAquifer)
        #####################################################################################################################################################


        #####################################################################################################################################################
        # try to assign the reccesion coefficient (unit: day-1) from the netcdf file of groundwaterPropertiesNC
        try:
            self.recessionCoeff = vos.netcdf2PCRobjCloneWithoutTime(\
                                  groundwaterPropertiesNC,'recessionCoeff',\
                                  cloneMapFileName = self.cloneMap)
            msg = "The 'recessionCoeff' is be obtained from the file: " + groundwaterPropertiesNC
            logger.info(msg)
        except:
            self.recessionCoeff = None
            msg = "The 'recessionCoeff' cannot be read from the file: "+groundwaterPropertiesNC
            logger.warning(msg)

        # assign the reccession coefficient based on the given pcraster file
        if 'recessionCoeff' in iniItems.groundwaterOptions.keys() and iniItems.groundwaterOptions['recessionCoeff'] != "None":
            msg = "The 'recessionCoeff' is be obtained from the file: " + iniItems.groundwaterOptions['recessionCoeff']
            logger.info(msg)
            self.recessionCoeff = vos.readPCRmapClone(iniItems.groundwaterOptions['recessionCoeff'], self.cloneMap, self.tmpDir, self.inputDir)

        # calculate the reccession coefficient based on the given parameters
        if isinstance(self.recessionCoeff, types.NoneType) and\
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
            # TODO: Perhaps, we should use interpolation/extrapolation here. 

            # aquifer thickness (unit: m) for recession coefficient
            aquiferThicknessForRecessionCoeff = vos.readPCRmapClone(iniItems.groundwaterOptions['aquiferThicknessForRecessionCoeff'],\
                                                                    self.cloneMap,self.tmpDir,self.inputDir)

            # calculate recessionCoeff (unit; day-1)
            self.recessionCoeff = (math.pi**2.) * aquiferThicknessForRecessionCoeff / \
                                  (4.*self.specificYield*(aquiferWidth**2.))

            #~ pcr.aguila(self.recessionCoeff)


        # minimum and maximum values for groundwater recession coefficient (day-1)
        self.recessionCoeff = pcr.cover(self.recessionCoeff,0.00)
        self.recessionCoeff = pcr.min(0.9999,self.recessionCoeff)
        if 'minRecessionCoeff' in iniItems.groundwaterOptions.keys():
            minRecessionCoeff = float(iniItems.groundwaterOptions['minRecessionCoeff'])
        # - the minimum value may be automatically set in the configuration.py 
        self.recessionCoeff = pcr.max(minRecessionCoeff,self.recessionCoeff)
        #~ pcr.aguila(self.recessionCoeff)
        #####################################################################################################################################################


        #####################################################################################################################################################

        # assign surface water bed conductivity (unit: m.day-1)
        # - the default value is equal to kSatAquifer
        self.riverBedConductivity = self.kSatAquifer
        if iniItems.groundwaterOptions['riverBedConductivity'] != "Default":
            self.riverBedConductivity = vos.readPCRmapClone(iniItems.groundwaterOptions['riverBedConductivity'], self.cloneMap, self.tmpDir, self.inputDir)
            self.riverBedConductivity = pcr.ifthen(self.riverBedConductivity > 0.0, self.riverBedConductivity)
            self.riverBedConductivity = pcr.cover(self.riverBedConductivity, pcr.mapminimum(self.riverBedConductivity))
        #~ pcr.aguila(self.riverBedConductivity)


        # maximum surface water bed conductivity (unit: m.day-1)
        if 'maximumRiverBedConductivity' not in iniItems.groundwaterOptions.keys():
            msg  = 'The option "maximumRiverBedConductivity" is not defined in the "groundwaterOptions" of the configuration file. '
            msg += 'This run assumes "0.1" (m/day) for this option.'
            logger.warning(msg)
            iniItems.groundwaterOptions['maximumRiverBedConductivity'] = "0.1"
        maximumRiverBedConductivity = vos.readPCRmapClone(iniItems.groundwaterOptions['maximumRiverBedConductivity'], self.cloneMap, self.tmpDir, self.inputDir)
        maximumRiverBedConductivity = pcr.ifthen(maximumRiverBedConductivity > 0.0, maximumRiverBedConductivity)
        maximumRiverBedConductivity = pcr.cover(maximumRiverBedConductivity, pcr.mapminimum(maximumRiverBedConductivity))


        # surface water bed conductivity - limited by the maximum value
        self.riverBedConductivity = pcr.min(maximumRiverBedConductivity, self.riverBedConductivity)
        #~ pcr.aguila(self.riverBedConductivity)
        
        
        # assign surface water bed thickness (unit: m)
        self.riverBedThickness = vos.readPCRmapClone(iniItems.groundwaterOptions['riverBedThickness'], self.cloneMap, self.tmpDir, self.inputDir)
        self.riverBedThickness = pcr.ifthen(self.riverBedThickness > 0.0, self.riverBedThickness)
        self.riverBedThickness = pcr.cover(self.riverBedThickness, pcr.mapminimum(self.riverBedThickness))
        

        # assign minimum value surface water bed resistance (unit: day)
        minimumBedResistance = vos.readPCRmapClone(iniItems.groundwaterOptions['minimumBedResistance'], self.cloneMap, self.tmpDir, self.inputDir)
        minimumBedResistance = pcr.ifthen(minimumBedResistance > 0.0, minimumBedResistance)
        minimumBedResistance = pcr.cover(minimumBedResistance, pcr.mapminimum(minimumBedResistance))
        #~ pcr.aguila(self.minimumBedResistance)

        
        # calculate river bed resistance (day) - limited by the minimum value
        self.bed_resistance = self.riverBedThickness / self.riverBedConductivity
        self.bed_resistance = pcr.max(minimumBedResistance, self.bed_resistance)
        
        
        # calculate riverBedConductivity (m/day) - limited by resistance
        self.riverBedConductivity = self.riverBedThickness / self.bed_resistance
        
        
        #####################################################################################################################################################
        
        

        #####################################################################################################################################################
        # total groundwater thickness (unit: m)
        totalGroundwaterThickness = None
        groundwaterThicknessIsNeeded = False
        # - For PCR-GLOBWB, the estimate of total groundwater thickness is needed to estimate for the following purpose:
        #   - to estimate fossil groundwater capacity (this is needed only for runs without MODFLOW)
        #   - to determine productive aquifer areas (where capillary rise can occur and groundwater depletion can occur) (for runs with/without MODFLOW)
        if 'estimateOfTotalGroundwaterThickness' in iniItems.groundwaterOptions.keys() and\
           (self.limitFossilGroundwaterAbstraction or self.useMODFLOW): groundwaterThicknessIsNeeded = True
        # - Note that for runs with MODFLOW, ideally, we want to minimize enormous drawdown in non-productive aquifer areas
        if self.modflowOfflineCoupling: groundwaterThicknessIsNeeded = True  
        if groundwaterThicknessIsNeeded:

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
            # - TODO: Check whether totalGroundwaterThickness = 0 can work? 

            # set minimum thickness
            if 'minimumTotalGroundwaterThickness' in iniItems.groundwaterOptions.keys() and \
                                                    (iniItems.groundwaterOptions['minimumTotalGroundwaterThickness'] != "None"):
                minimumThickness = pcr.scalar(float(\
                                   iniItems.groundwaterOptions['minimumTotalGroundwaterThickness']))
                totalGroundwaterThickness = pcr.max(minimumThickness, totalGroundwaterThickness)
                #~ pcr.aguila(totalGroundwaterThickness)

            # set maximum thickness
            if 'maximumTotalGroundwaterThickness' in iniItems.groundwaterOptions.keys() and\
                                                    (iniItems.groundwaterOptions['maximumTotalGroundwaterThickness'] != "None"):
                maximumThickness = float(iniItems.groundwaterOptions['maximumTotalGroundwaterThickness'])
                totalGroundwaterThickness = pcr.min(maximumThickness, totalGroundwaterThickness)
                #~ pcr.aguila(totalGroundwaterThickness)

            # estimate of total groundwater thickness (unit: m)
            self.totalGroundwaterThickness = totalGroundwaterThickness
        #####################################################################################################################################################


        #####################################################################################################################################################
        # extent of the productive aquifer (a boolean map)
        # - Principle: In non-productive aquifer areas, no capillary rise and groundwater abstraction should not exceed recharge
        #
        self.productive_aquifer = pcr.ifthen(self.landmask, pcr.boolean(1.0))
        excludeUnproductiveAquifer = True
        if excludeUnproductiveAquifer:
            if 'minimumTransmissivityForProductiveAquifer' in iniItems.groundwaterOptions.keys() and\
                                                             (iniItems.groundwaterOptions['minimumTransmissivityForProductiveAquifer'] not in ["None", "False"]):
                msg = "Defining areas of productive aquifer based on transmissivity criteria defined in the field 'minimumTransmissivityForProductiveAquifer' of 'groundwaterOptions'."
                logger.info(msg)      
                minimumTransmissivityForProductiveAquifer = \
                                          vos.readPCRmapClone(iniItems.groundwaterOptions['minimumTransmissivityForProductiveAquifer'],\
                                                              self.cloneMap, self.tmpDir, self.inputDir)
                self.productive_aquifer = pcr.cover(\
                 pcr.ifthen(self.kSatAquifer * totalGroundwaterThickness > minimumTransmissivityForProductiveAquifer, pcr.boolean(1.0)), pcr.boolean(0.0))
                #~ pcr.aguila(self.productive_aquifer) 
            else:
                msg = "All cells are assumed as productive aquifers."
                logger.info(msg)
        self.productive_aquifer = pcr.cover(self.productive_aquifer, pcr.boolean(0.0))
        # - TODO: Check and re-calculate the GLHYMPS map to confirm the kSatAquifer value in groundwaterPropertiesNC (e.g. we miss some parts of HPA).
        #####################################################################################################################################################


        #####################################################################################################################################################
        # estimate of fossil groundwater capacity (based on the aquifer thickness and specific yield)
        if self.modflowOfflineCoupling == False and iniItems.groundwaterOptions['limitFossilGroundWaterAbstraction'] == "True" and self.limitAbstraction == False:

            logger.info('Fossil groundwater abstractions are allowed with LIMIT.')
            logger.info('Estimating fossil groundwater capacities based on aquifer thicknesses and specific yield.')
            # TODO: Make the following aquifer thickness information can be used to define the extent of productive aquifer.

            # estimate of capacity (unit: m) of renewable groundwater (to correct the initial estimate of fossil groundwater capacity)
            # - this value is NOT relevant, but requested in the IWMI project
            if 'estimateOfRenewableGroundwaterCapacity' not in iniItems.groundwaterOptions.keys():\
                iniItems.groundwaterOptions['estimateOfRenewableGroundwaterCapacity'] = 0.0
            storGroundwaterCap =  pcr.cover(
                                  vos.readPCRmapClone(\
                                  iniItems.groundwaterOptions['estimateOfRenewableGroundwaterCapacity'],
                                  self.cloneMap,self.tmpDir,self.inputDir), 0.0)
            # fossil groundwater capacity (unit: m)
            self.fossilWaterCap = pcr.ifthen(self.landmask,\
                                  pcr.max(0.0,\
                                  totalGroundwaterThickness*self.specificYield - storGroundwaterCap))
        else:                         
            if self.modflowOfflineCoupling == False: logger.info('Fossil groundwater capacity is NOT defined.')
        #####################################################################################################################################################


        #####################################################################################################################################################
        # zones at which groundwater allocations are determined
        self.usingAllocSegments = False
        # - by default, it is consistent with the one defined in the landSurfaceOptions
        if self.modflowOfflineCoupling == False and 'allocationSegmentsForGroundSurfaceWater' in iniItems.landSurfaceOptions.keys() and iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater'] not in ["None", "False"]:
            self.usingAllocSegments = True
            groundwaterAllocationSegments = iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater']
        # - yet, we can also define a specific one for groundwater
        if self.modflowOfflineCoupling == False and "allocationSegmentsForGroundwater" in iniItems.groundwaterOptions.keys():
            if iniItems.groundwaterOptions['allocationSegmentsForGroundwater'] not in ["None", "False"]:
                self.usingAllocSegments = True
                groundwaterAllocationSegments = iniItems.groundwaterOptions['allocationSegmentsForGroundwater']
            else:
                self.usingAllocSegments = False
        else:
            self.usingAllocSegments = False
        #####################################################################################################################################################


        #####################################################################################################################################################
        # incorporating groundwater distribution network:
        if self.usingAllocSegments:

            # reading the allocation zone file
            self.allocSegments = vos.readPCRmapClone(\
             groundwaterAllocationSegments,
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
            
            #~ pcr.aguila(self.allocSegments)
            
            # cell area (unit: m2)
            cellArea = vos.readPCRmapClone(\
              iniItems.routingOptions['cellAreaMap'],
              self.cloneMap,self.tmpDir,self.inputDir)
            cellArea = pcr.ifthen(self.landmask, cellArea)              # TODO: integrate this one with the one coming from the routing module

            # zonal/segment area (unit: m2)
            self.segmentArea = pcr.areatotal(pcr.cover(cellArea, 0.0), self.allocSegments)
            self.segmentArea = pcr.ifthen(self.landmask, self.segmentArea)
        #####################################################################################################################################################


        #####################################################################################################################################################
        # maximumDailyGroundwaterAbstraction (unit: m/day) - in order to avoid over-abstraction of groundwater source
        if self.modflowOfflineCoupling == False and 'maximumDailyGroundwaterAbstraction' in iniItems.groundwaterOptions.keys():
            self.maximumDailyGroundwaterAbstraction = vos.readPCRmapClone(iniItems.groundwaterOptions['maximumDailyGroundwaterAbstraction'],
                                                                          self.cloneMap,self.tmpDir,self.inputDir)
        #~ pcr.aguila(self.maximumDailyGroundwaterAbstraction)
        #####################################################################################################################################################


        #####################################################################################################################################################
        # maximumDailyFossilGroundwaterAbstraction (unit: m/day) - in order to avoid over-abstraction of groundwater source
        if self.modflowOfflineCoupling == False and 'maximumDailyFossilGroundwaterAbstraction' in iniItems.groundwaterOptions.keys():
            self.maximumDailyFossilGroundwaterAbstraction = vos.readPCRmapClone(iniItems.groundwaterOptions['maximumDailyFossilGroundwaterAbstraction'], self.cloneMap,self.tmpDir,self.inputDir)
        #~ pcr.aguila(self.maximumDailyFossilGroundwaterAbstraction)
        #####################################################################################################################################################


        # get the initial conditions
        if initial_condition_is_required: self.getICs(iniItems, spinUp)
        # PS: For an offline MODFLOW run, initial conditions will be read from the groundwater_MODFLOW module.   


        # coupling to daily modflow
        if self.coupleToDailyMODFLOW:
            # initiating a groundwater MODFLOW module
            self.gw_modflow = gw_modflow.GroundwaterModflow(iniItems, self.landmask, self)
            # get initial conditions for MODFLOW
            self.gw_modflow.get_initial_heads(spinUp)
            
        # initiate old style reporting (this is useful for debugging)
        self.initiate_old_style_groundwater_reporting(iniItems)


    def initiate_old_style_groundwater_reporting(self,iniItems):

        self.report = True
        try:
            self.outDailyTotNC = iniItems.groundwaterOptions['outDailyTotNC'].split(",")
            self.outMonthTotNC = iniItems.groundwaterOptions['outMonthTotNC'].split(",")
            self.outMonthAvgNC = iniItems.groundwaterOptions['outMonthAvgNC'].split(",")
            self.outMonthEndNC = iniItems.groundwaterOptions['outMonthEndNC'].split(",")
            self.outAnnuaTotNC = iniItems.groundwaterOptions['outAnnuaTotNC'].split(",")
            self.outAnnuaAvgNC = iniItems.groundwaterOptions['outAnnuaAvgNC'].split(",")
            self.outAnnuaEndNC = iniItems.groundwaterOptions['outAnnuaEndNC'].split(",")
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

    def getICs(self, iniItems, iniConditions = None):

        self.initialize_states(iniItems, iniConditions)

    def initialize_states(self, iniItems, iniConditions):

        # initial conditions (unit: m)
        if iniConditions == None: # when the model just start (reading the initial conditions from file)


            self.storGroundwater         = vos.readPCRmapClone(\
                                           iniItems.groundwaterOptions['storGroundwaterIni'],
                                           self.cloneMap,self.tmpDir,self.inputDir)
            self.avgAbstraction          = vos.readPCRmapClone(\
                                           iniItems.groundwaterOptions['avgTotalGroundwaterAbstractionIni'],
                                           self.cloneMap,self.tmpDir,self.inputDir)
            self.avgAllocation           = vos.readPCRmapClone(\
                                           iniItems.groundwaterOptions['avgTotalGroundwaterAllocationLongIni'],
                                           self.cloneMap,self.tmpDir,self.inputDir)
            self.avgAllocationShort      = vos.readPCRmapClone(\
                                           iniItems.groundwaterOptions['avgTotalGroundwaterAllocationShortIni'],
                                           self.cloneMap,self.tmpDir,self.inputDir)
            self.avgNonFossilAllocation   = vos.readPCRmapClone(\
                                            iniItems.groundwaterOptions['avgNonFossilGroundwaterAllocationLongIni'],
                                            self.cloneMap,self.tmpDir,self.inputDir)
            self.avgNonFossilAllocationShort = vos.readPCRmapClone(\
                                               iniItems.groundwaterOptions['avgNonFossilGroundwaterAllocationShortIni'],
                                               self.cloneMap,self.tmpDir,self.inputDir)

            # additional initial conditions (needed ONLY for the online coupling between PCR-GLOBWB and MODFLOW))
            if iniItems.groundwaterOptions['relativeGroundwaterHeadIni'] != "None":\
                
                msg = "The initial condition 'relativeGroundwaterHead' is read from the file defined in the configuration file."
                logger.info(msg)
                
                self.relativeGroundwaterHead = vos.readPCRmapClone(\
                                               iniItems.groundwaterOptions['relativeGroundwaterHeadIni'],
                                               self.cloneMap,self.tmpDir,self.inputDir)
            else:
 
                msg = "The initial condition 'relativeGroundwaterHead' is estimated based on the provided 'storGroundwater'."
                logger.info(msg)
 
                self.relativeGroundwaterHead = self.storGroundwater / self.specificYield
 
            self.baseflow = vos.readPCRmapClone(\
                            iniItems.groundwaterOptions['baseflowIni'],
                            self.cloneMap,self.tmpDir,self.inputDir)

        else:                     # during/after spinUp
            self.storGroundwater             = iniConditions['groundwater']['storGroundwater']
            self.avgAbstraction              = iniConditions['groundwater']['avgTotalGroundwaterAbstraction']
            self.avgAllocation               = iniConditions['groundwater']['avgTotalGroundwaterAllocationLong']
            self.avgAllocationShort          = iniConditions['groundwater']['avgTotalGroundwaterAllocationShort']
            self.avgNonFossilAllocation      = iniConditions['groundwater']['avgNonFossilGroundwaterAllocationLong']
            self.avgNonFossilAllocationShort = iniConditions['groundwater']['avgNonFossilGroundwaterAllocationShort']

            self.relativeGroundwaterHead     = iniConditions['groundwater']['relativeGroundwaterHead']
            self.baseflow                    = iniConditions['groundwater']['baseflow']

        # initial condition for storGroundwaterFossil (unit: m)
        #
        # Note that storGroundwaterFossil should not be depleted during the spin-up.
        #
        if iniItems.groundwaterOptions['storGroundwaterFossilIni'] == "Maximum" and\
           self.limitFossilGroundwaterAbstraction and self.limitAbstraction == False:
            logger.info("Assuming 'full' fossilWaterCap as the initial condition for fossil groundwater storage.")
            self.storGroundwaterFossil = self.fossilWaterCap
        #
        if iniItems.groundwaterOptions['storGroundwaterFossilIni'] != "Maximum":
            logger.info("Using a pre-defined initial condition for fossil groundwater storage.")
            self.storGroundwaterFossil = vos.readPCRmapClone(\
                                         iniItems.groundwaterOptions['storGroundwaterFossilIni'],
                                         self.cloneMap,self.tmpDir,self.inputDir)
        #
        if iniItems.groundwaterOptions['storGroundwaterFossilIni'] != "Maximum" and\
           self.limitFossilGroundwaterAbstraction and self.limitAbstraction == False:
            logger.info("The pre-defined initial condition for fossil groundwater is limited by fossilWaterCap (full capacity).")
            self.storGroundwaterFossil = pcr.min(self.storGroundwaterFossil, self.fossilWaterCap)
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)


        self.avgAbstraction  = pcr.cover( self.avgAbstraction,0.0)
        self.avgAbstraction  = pcr.ifthen(self.landmask,\
                                          self.avgAbstraction)

        self.avgAllocation   = pcr.cover( self.avgAllocation,0.0)
        self.avgAllocation   = pcr.ifthen(self.landmask,\
                                          self.avgAllocation)

        self.avgAllocationShort = pcr.cover( self.avgAllocationShort,0.0)
        self.avgAllocationShort = pcr.ifthen(self.landmask,\
                                             self.avgAllocationShort)

        self.avgNonFossilAllocation   = pcr.cover( self.avgNonFossilAllocation,0.0)
        self.avgNonFossilAllocation   = pcr.ifthen(self.landmask,\
                                                   self.avgNonFossilAllocation)

        self.avgNonFossilAllocationShort = pcr.cover( self.avgNonFossilAllocationShort,0.0)
        self.avgNonFossilAllocationShort = pcr.ifthen(self.landmask,\
                                                      self.avgNonFossilAllocationShort)

        self.storGroundwater = pcr.cover( self.storGroundwater,0.0)
        self.storGroundwater = pcr.ifthen(self.landmask,\
                                          self.storGroundwater)

        self.relativeGroundwaterHead = pcr.cover(self.relativeGroundwaterHead, 0.0)
        self.relativeGroundwaterHead = pcr.ifthen(self.landmask, self.relativeGroundwaterHead)

        self.baseflow = pcr.cover(self.baseflow, 0.0)
        self.baseflow = pcr.ifthen(self.landmask, self.baseflow)

        self.storGroundwaterFossil = pcr.cover( self.storGroundwaterFossil, 0.0)
        self.storGroundwaterFossil = pcr.ifthen(self.landmask,\
                                                self.storGroundwaterFossil)


        # make sure that the following average values cannot be negative
        self.avgAbstraction  = pcr.max(0.,self.avgAbstraction)
        self.avgAllocation   = pcr.max(0.,self.avgAllocation)
        self.avgAllocationShort = pcr.max(0.,self.avgAllocationShort)
        self.avgNonFossilAllocation   = pcr.max(0.,self.avgNonFossilAllocation)
        self.avgNonFossilAllocationShort = pcr.max(0.,self.avgNonFossilAllocationShort)


        # storGroundwaterFossil cannot be negative for runs with limitFossilGroundwaterAbstraction
        if self.limitFossilGroundwaterAbstraction:
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)


        # for runs without MODFLOW, the following values cannot be negative 
        if self.useMODFLOW == False:
            self.storGroundwater         = pcr.max(0.0, self.storGroundwater)
            self.relativeGroundwaterHead = pcr.max(0.0, self.relativeGroundwaterHead)
            self.baseflow                = pcr.max(0.0, self.baseflow)


    def perturb(self, name, **parameters):

        if name == "groundwater":

            # factor for perturbing the initial storGroundwater
            self.storGroundwater = self.storGroundwater * (mapnormal()*parameters['standard_deviation']+1)
            self.storGroundwater = pcr.max(0.,self.storGroundwater)

        else:
            print("Error: only groundwater may be updated at this time")
            return -1

    def update(self,landSurface,routing,currTimeStep):

        if self.useMODFLOW:
            self.update_with_MODFLOW(landSurface,routing,currTimeStep)
        else:
            self.update_without_MODFLOW(landSurface,routing,currTimeStep)

        self.calculate_statistics(routing)

        # old-style reporting
        self.old_style_groundwater_reporting(currTimeStep)              # TODO: remove this one


    def update_with_MODFLOW(self, landSurface, routing, currTimeStep):

        # non fossil groundwater abstraction
        self.nonFossilGroundwaterAbs = landSurface.nonFossilGroundwaterAbs
        
        # fossil groundwater abstraction (must be zero):
        self.fossilGroundwaterAbstr  = landSurface.fossilGroundwaterAbstr
        # - this must be zero
        if self.debugWaterBalance:
            vos.waterBalanceCheck([pcr.spatial(pcr.scalar(0.0))],\
                                  [self.fossilGroundwaterAbstr],\
                                  [],\
                                  [],\
                                  'fossil groundwater abstraction must be zero (if online coupled to MODFLOW)',\
                                  True,\
                                  currTimeStep.fulldate,threshold=5e-4)
        
        # groundwater allocation
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc    = landSurface.fossilGroundwaterAlloc
        
        # Note: The following variable (unmetDemand) is a bad name and used in the past.
        #       Its definition is actually as follows: (the amount of demand that is satisfied/allocated from fossil groundwater)
        self.unmetDemand = self.fossilGroundwaterAlloc
        # - this must be zero
        if self.debugWaterBalance:
            vos.waterBalanceCheck([pcr.spatial(pcr.scalar(0.0))],\
                                  [self.unmetDemand],\
                                  [],\
                                  [],\
                                  'fossil groundwater allocation (unmetDemand) must be zero (if online coupled to MODFLOW)',\
                                  True,\
                                  currTimeStep.fulldate,threshold=5e-4)

        # for monthly coupling (and still for global runs only)
        if self.coupleToDailyMODFLOW == False:
        
            logger.info("Updating groundwater based on the MODFLOW output.")
            
            # relativeGroundwaterHead, storGroundwater and baseflow fields are assumed to be constant
            self.relativeGroundwaterHead = self.relativeGroundwaterHead
            self.storGroundwater = self.storGroundwater
            self.baseflow = self.baseflow
            
            if currTimeStep.day == 1 and currTimeStep.timeStepPCR > 1:
            
                # for online coupling, we will read files from pcraster maps, using the previous day values
                directory = self.iniItems.main_output_directory + "/modflow/transient/maps/"
                yesterday = str(currTimeStep.yesterday())
            
                # - relative groundwater head from MODFLOW
                filename = directory + "relativeGroundwaterHead_" + str(yesterday) + ".map"
                self.relativeGroundwaterHead = pcr.ifthen(self.landmask, pcr.cover(vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0))
            
                # - storGroundwater from MODFLOW
                filename = directory + "storGroundwater_" + str(yesterday) + ".map"
                self.storGroundwater = pcr.ifthen(self.landmask, pcr.cover(vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0))
            
                # - baseflow from MODFLOW
                filename = directory + "baseflow_" + str(yesterday) + ".map"
                self.baseflow = pcr.ifthen(self.landmask, pcr.cover(vos.readPCRmapClone(filename, self.cloneMap, self.tmpDir), 0.0))

        # by default, river bed exchange has been accomodated in baseflow (via MODFLOW, river and drain packages)
        self.surfaceWaterInf = pcr.scalar(0.0)

        # Note: The following variable (unmetDemand) is a bad name and used in the past.
        #       Its definition is actually as follows: (the amount of demand that is satisfied/allocated from fossil groundwater)
        #
        self.unmetDemand = self.fossilGroundwaterAlloc

        # for daily coupling
        if self.coupleToDailyMODFLOW:

            logger.info("Updating groundwater based on the DAILY MODFLOW simulation.")
            
            # surface water infiltration (unit: m/day), from surface water bodies to groundwater bodies, taken from the previous time step 
            self.surfaceWaterInf = routing.riverbedExchange / routing.cellArea
            # - Ideally, this should be accomodated in the river (RIV) package of MODFLOW. 
            # - Yet, the RIV package often results negative channel storage (too much infiltration).
            # - Hence, this flux is calculated in the routing.py module (by following the principle of MODFLOW river package).
            # - See the function/method "calculate_exchange_to_groundwater" in the routing.py. 

            # groundwater recharge (unit: m/day)
            groundwater_recharge = landSurface.gwRecharge 
            # - add river infiltration
            groundwater_recharge = groundwater_recharge + self.surfaceWaterInf 
            

            # total groundwater abstraction (unit: m/day)
            groundwater_abstraction = landSurface.nonFossilGroundwaterAbs + landSurface.fossilGroundwaterAbstr
            

            # bankfull depth
            try:
                bankfull_depth      = routing.channelDepth                # m
            except:
                bankfull_depth      = routing.predefinedChannelDepth      # m
            # TODO: FIX THIS (remove try and except)    


            # estimate of flood depth
            flood_depth             = routing.transferVolToTopWaterLayer / \
                                      routing.cellArea                    # m


            # fraction of surface water within cells
            surface_water_fraction  = routing.dynamicFracWat              # m2.m-2


            # surface water volume
            # - this will be converted to surface water head elevation
            surface_water_volume    = routing.channelStorage + \
                                      routing.transferVolToTopWaterLayer  # m3
            # Note that the 'routing.channelStorage' may not include "routing.floodInundationVolume", particularly if the "routing.floodInundationVolume" is transferred to the "landSurface.topWaterLayer".                           
            

            # surface water discharge (m3/s) 
            surface_water_discharge = routing.discharge                   # m3.s-1
            

            self.gw_modflow.update(currTimeStep, groundwater_recharge, \
                                                 groundwater_abstraction, \
                                                 surface_water_discharge, \
                                                 surface_water_volume, \
                                                 surface_water_fraction, \
                                                 bankfull_depth, \
                                                 flood_depth)


            self.baseflow                = self.gw_modflow.baseflow
            self.relativeGroundwaterHead = self.gw_modflow.relativeGroundwaterHead
            self.storGroundwater         = self.gw_modflow.storGroundwater


            self.groundwaterHeadLayer1 = pcr.ifthen(self.landmask, self.gw_modflow.groundwaterHeadLayer1)
            self.groundwaterHeadLayer2 = pcr.ifthen(self.landmask, self.gw_modflow.groundwaterHeadLayer2)
            # TODO: Make it general, for any numbers of layers



            
    def update_without_MODFLOW(self,landSurface,routing,currTimeStep):

        logger.info("Updating groundwater")

        if self.debugWaterBalance:
            preStorGroundwater       = self.storGroundwater
            preStorGroundwaterFossil = self.storGroundwaterFossil

        # get riverbed infiltration from the previous time step (from routing)
        self.surfaceWaterInf  = routing.riverbedExchange/\
                                routing.cellArea               # unit: m
        self.storGroundwater += self.surfaceWaterInf

        # get net recharge (percolation-capRise) and update storage:
        self.storGroundwater  = pcr.max(0.,\
                                self.storGroundwater + landSurface.gwRecharge)

        # non fossil groundwater abstraction
        self.nonFossilGroundwaterAbs = landSurface.nonFossilGroundwaterAbs
        self.storGroundwater         = pcr.max(0.,\
                                       self.storGroundwater - self.nonFossilGroundwaterAbs)

        # baseflow
        self.baseflow         = pcr.max(0.,\
                                pcr.min(self.storGroundwater,\
                                        self.recessionCoeff* \
                                        self.storGroundwater))
        self.storGroundwater  = pcr.max(0.,\
                                self.storGroundwater - self.baseflow)
        # PS: baseflow must be calculated at the end (to ensure the availability of storGroundwater to support nonFossilGroundwaterAbs)

        # fossil groundwater abstraction:
        self.fossilGroundwaterAbstr = landSurface.fossilGroundwaterAbstr
        self.storGroundwaterFossil -= self.fossilGroundwaterAbstr

        # fossil groundwater cannot be negative if limitFossilGroundwaterAbstraction is used
        if self.limitFossilGroundwaterAbstraction:
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)

        # groundwater allocation (Note: This is done in the landSurface module)
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc    = landSurface.fossilGroundwaterAlloc

        # Note: The following variable (unmetDemand) is a bad name and used in the past.
        #       Its definition is actually as follows: (the amount of demand that is satisfied/allocated from fossil groundwater)
        self.unmetDemand = self.fossilGroundwaterAlloc

        # calculate relative groundwater head above the minimum level (unit: m)
        # - needed to estimate areas influenced by capillary rise
        self.relativeGroundwaterHead = self.storGroundwater/self.specificYield

        if self.debugWaterBalance:
            vos.waterBalanceCheck([self.surfaceWaterInf,\
                                   landSurface.gwRecharge],\
                                  [self.baseflow,\
                                   self.nonFossilGroundwaterAbs],\
                                  [  preStorGroundwater],\
                                  [self.storGroundwater],\
                                       'storGroundwater',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)

        if self.debugWaterBalance:
            vos.waterBalanceCheck([pcr.scalar(0.0)],\
                                  [self.fossilGroundwaterAbstr],\
                                  [  preStorGroundwaterFossil],\
                                  [self.storGroundwaterFossil],\
                                       'storGroundwaterFossil',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-3)

        if self.debugWaterBalance:
            vos.waterBalanceCheck([landSurface.desalinationAllocation,\
                                   self.unmetDemand, \
                                   self.allocNonFossilGroundwater, \
                                   landSurface.allocSurfaceWaterAbstract],\
                                  [landSurface.totalPotentialGrossDemand],\
                                  [pcr.scalar(0.)],\
                                  [pcr.scalar(0.)],\
                                  'demand allocation (desalination, surface water, groundwater & unmetDemand. Error here may be due to rounding error.',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-3)

    def calculate_statistics(self, routing):

        # calculate the average total groundwater abstraction (m/day) from the last 365 days:
        totalAbstraction    = self.fossilGroundwaterAbstr + self.nonFossilGroundwaterAbs
        deltaAbstraction    = totalAbstraction - self.avgAbstraction
        self.avgAbstraction = self.avgAbstraction +\
                                 deltaAbstraction/\
                              pcr.min(365., pcr.max(1.0, routing.timestepsToAvgDischarge))
        self.avgAbstraction = pcr.max(0.0, self.avgAbstraction)

        # calculate the average non fossil groundwater allocation (m/day)
        # - from the last 365 days:
        deltaAllocation     = self.allocNonFossilGroundwater  - self.avgNonFossilAllocation
        self.avgNonFossilAllocation  = self.avgNonFossilAllocation +\
                                 deltaAllocation/\
                              pcr.min(365., pcr.max(1.0, routing.timestepsToAvgDischarge))
        self.avgNonFossilAllocation = pcr.max(0.0, self.avgNonFossilAllocation)
        # - from the last 7 days:
        deltaAllocationShort    = self.allocNonFossilGroundwater - self.avgNonFossilAllocationShort
        self.avgNonFossilAllocationShort = self.avgNonFossilAllocationShort +\
                                     deltaAllocationShort/\
                                  pcr.min(7., pcr.max(1.0, routing.timestepsToAvgDischarge))
        self.avgNonFossilAllocationShort = pcr.max(0.0, self.avgNonFossilAllocationShort)

        # calculate the average total (fossil + non fossil) groundwater allocation (m/day)
        totalGroundwaterAllocation = self.allocNonFossilGroundwater + self.fossilGroundwaterAlloc
        # - from the last 365 days:
        deltaAllocation            = totalGroundwaterAllocation - self.avgAllocation
        self.avgAllocation         = self.avgAllocation +\
                                        deltaAllocation/\
                                        pcr.min(365., pcr.max(1.0, routing.timestepsToAvgDischarge))
        self.avgAllocation         = pcr.max(0.0, self.avgAllocation)
        # - from the last 7 days:
        deltaAllocationShort       = totalGroundwaterAllocation - self.avgAllocationShort
        self.avgAllocationShort    = self.avgAllocationShort +\
                                        deltaAllocationShort/\
                                        pcr.min(7., pcr.max(1.0, routing.timestepsToAvgDischarge))
        self.avgAllocationShort    = pcr.max(0.0, self.avgAllocationShort)

    def old_style_groundwater_reporting(self,currTimeStep):

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

