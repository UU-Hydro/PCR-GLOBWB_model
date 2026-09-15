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

import os
import sys

import pcraster as pcr
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)


class WaterManagement(object):

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # make iniItems available for other modules/functions
        self.iniItems = iniItems
        
        # cloneMap, tmpDir, inputDir based on the configuration/setting given in the ini/configuration file
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        ####################################################################################################
        # Groundwater abstraction options
        #
        # adjustment for limitAbstraction (to use only renewable water)
        # if limitAbstraction = True, only renewable groundwater use 
        if 'limitAbstraction' not in list(iniItems.waterManagementOptions.keys()):
            iniItems.waterManagementOptions['limitAbstraction'] = False
        self.limitAbstraction = False
        if iniItems.waterManagementOptions['limitAbstraction'] == "True":
            self.limitAbstraction = True
        
        # if using MODFLOW, limitAbstraction must be True (the abstraction cannot exceed storGroundwater)
        if "useMODFLOW" in list(iniItems.groundwaterOptions.keys()):
            if iniItems.groundwaterOptions["useMODFLOW"] == "True":
                self.limitAbstraction = True
        
        # option for groundwater pumping capacity 'limitRegionalAnnualGroundwaterAbstraction'
        if 'pumpingCapacityNC' not in list(iniItems.waterManagementOptions.keys()):
            msg  = 'The "pumpingCapacityNC" (annual groundwater pumping capacity limit netcdf file)'
            msg += 'is not defined in the configuration file. '
            msg += 'We assume no annual groundwater pumping limit used in this run. '
            msg += 'It may result too high groundwater abstraction.'
            logger.warning(msg)
            iniItems.waterManagementOptions['pumpingCapacityNC'] = "None"
        
        # option for limitting regional groundwater abstractions
        if iniItems.waterManagementOptions['pumpingCapacityNC'] != "None":
            logger.info('Limit for annual regional groundwater abstraction is used.')
            self.limitRegionalAnnualGroundwaterAbstraction = True
            self.pumpingCapacityNC = vos.getFullPath(\
                                     iniItems.waterManagementOptions['pumpingCapacityNC'], self.inputDir, False)
        else:
            logger.warning('NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction.')
            self.limitRegionalAnnualGroundwaterAbstraction = False
        #
        ####################################################################################################
        
        # option to prioritize local sources before abstracting water from neighboring cells
        self.prioritizeLocalSourceToMeetWaterDemand = True
        if 'prioritizeLocalSourceToMeetWaterDemand' in list(iniItems.waterManagementOptions.keys()) and \
           iniItems.waterManagementOptions['pumpingCapacityNC'] == "False":
            self.prioritizeLocalSourceToMeetWaterDemand = False
            logger.info("The option prioritizeLocalSourceToMeetWaterDemand is set to 'False'.")
        
        # option to prioritize surface water
        # (at the moment, this option is always False)
        self.surfaceWaterPiority = False
        
        # read in cell area dataset
        # (unit: m2)
        cellArea = vos.readPCRmapClone(\
                       iniItems.routingOptions['cellAreaMap'],
                       self.cloneMap,self.tmpDir,self.inputDir)
        self.cellArea = pcr.ifthen(self.landmask, cellArea)
        
        # option to use desalination water supply
        self.includeDesalination = False
        if iniItems.waterManagementOptions['desalinationWater'] not in ["None", "False"]:
            logger.info("Monthly desalination water use is included.")
            self.includeDesalination = True
            self.desalinationWaterFile = vos.getFullPath(iniItems.waterManagementOptions['desalinationWater'], self.inputDir)
        else:
            logger.info("Monthly desalination water is NOT included.")
        
        # read in the allocation zones for desalined water, surface water, and groundwater sources
        # - if not defined, only local cell water availability is considered
        self.using_allocationSegmentsForDesalinatedWaterSource = False
        self.using_allocationSegmentsForSurfaceWaterSource     = False
        self.using_allocationSegmentsForGroundwaterSource      = False
        
        sources = ["allocationSegmentsForDesalinatedWaterSource",
                   "allocationSegmentsForSurfaceWaterSource",
                   "allocationSegmentsForGroundwaterSource"]
        
        for source in sources:
            if source in iniItems.waterManagementOptions.keys() and \
               iniItems.waterManagementOptions[source] not in ["False", "None"]:
                vars(self)[ "using_" + source] = True
                vars(self)[source], vars(self)[source+"Areas"] = self.get_allocation_zone(iniItems.waterManagementOptions[source])
            else:
                vars(self)[source], vars(self)[source+"Areas"] = None, None
        
        # define the water sources and sectors to evaluate
        self.source_names = ["desalinated_water", "surface_water", "renewable_groundwater", "nonrenewable_groundwater"]
        self.sector_names = ["domestic", "industry", "manufacture", "thermoelectric", "livestock", "irrigation"]
        
        # instantiate the following variable: 
        # - allocated_withdrawal_per_sector[source_name][sector_name]: the amount of water taken from the "source_name" to the "sector_name" 
        # - note that this from the point of view of pixels which are source
        self.allocated_withdrawal_per_sector = {}
        for source_name in self.source_names: 
            self.allocated_withdrawal_per_sector[source_name] = {}
            for sector_name in self.sector_names:
                self.allocated_withdrawal_per_sector[source_name][sector_name] = pcr.scalar(0.0)
        
        # instantiate the following variable: 
        # - self.allocated_demand_per_sector[source_name][sector_name]: the amount of water given to the "sector_name" from the "source"
        # - note that this from the point of view of pixels that have demands
        self.allocated_demand_per_sector = {}
        for source_name in self.source_names: 
            self.allocated_demand_per_sector[source_name] = {}
            for sector_name in self.sector_names:
                self.allocated_demand_per_sector[source_name][sector_name] = pcr.scalar(0.0)
        
        # instantiate the following variable: 
        # - self.met_demand_per_sector[sector_name]: the amount of demand that has been met for every "sector_name"
        # - note that this from the point of view of pixels that have demands 
        # - this is the sum of "allocated_demand_per_sector"
        self.met_demand_per_sector = {}
        for sector_name in self.sector_names:
            self.met_demand_per_sector[sector_name] = pcr.scalar(0.0)
        
        # pre-defined surface water source fraction for satisfying irrigation and livestock water demand
        self.swAbstractionFractionData = None
        self.swAbstractionFractionDataQuality = None
        if 'irrigationSurfaceWaterAbstractionFractionData' in list(iniItems.waterManagementOptions.keys()) and \
           'irrigationSurfaceWaterAbstractionFractionDataQuality' in list(iniItems.waterManagementOptions.keys()):
            
            if iniItems.waterManagementOptions['irrigationSurfaceWaterAbstractionFractionData'] not in ["None", "False"] or\
               iniItems.waterManagementOptions['irrigationSurfaceWaterAbstractionFractionDataQuality'] not in ["None", "False"]:
                
                logger.info('Using/incorporating the predefined surface water source of Siebert et al. (2010) for satisfying irrigation and livestock demand.')
                self.swAbstractionFractionData = pcr.cover(\
                                                 vos.readPCRmapClone(iniItems.waterManagementOptions['irrigationSurfaceWaterAbstractionFractionData'],\
                                                                     self.cloneMap,self.tmpDir,self.inputDir), 0.0)
                self.swAbstractionFractionData = pcr.ifthen(self.swAbstractionFractionData >= 0.0, \
                                                            self.swAbstractionFractionData )
                self.swAbstractionFractionDataQuality = \
                                                 pcr.cover(\
                                                 vos.readPCRmapClone(iniItems.waterManagementOptions['irrigationSurfaceWaterAbstractionFractionDataQuality'],\
                                                                     self.cloneMap,self.tmpDir,self.inputDir), 0.0)
                # ignore value with the quality above 5 (very bad) 
                # - Note: The resulting map has values only in cells with the data auality <= 5.0 
                self.swAbstractionFractionData = pcr.ifthen(self.swAbstractionFractionDataQuality <= 5.0, \
                                                            self.swAbstractionFractionData)
        
        # threshold values defining the preference for irrigation water source (unit: fraction/percentage)
        # - threshold_to_maximize_irrigation_surface_water
        if 'threshold_to_maximize_irrigation_surface_water' not in list(iniItems.waterManagementOptions.keys()):
            msg  = 'The option "threshold_to_maximize_irrigation_surface_water" is not defined in the "waterManagementOptions" of the configuration file. '
            msg += 'This run assumes "1.0" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions['threshold_to_maximize_irrigation_surface_water'] = "1.0"
            # The default value is 1.0 such that this threshold value is not used. 
        self.threshold_to_maximize_irrigation_surface_water = \
             vos.readPCRmapClone(iniItems.waterManagementOptions['threshold_to_maximize_irrigation_surface_water'],\
                                 self.cloneMap,self.tmpDir,self.inputDir)
        
        # - threshold_to_minimize_fossil_groundwater_irrigation
        if 'threshold_to_minimize_fossil_groundwater_irrigation' not in list(iniItems.waterManagementOptions.keys()):
            msg  = 'The option "threshold_to_minimize_fossil_groundwater_irrigation" is not defined in the "waterManagementOptions" of configuration file. '
            msg += 'This run assumes "1.0" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions['threshold_to_minimize_fossil_groundwater_irrigation'] = "1.0"
            # The default value is 1.0 such that this threshold value is not used. 
        self.threshold_to_minimize_fossil_groundwater_irrigation = \
             vos.readPCRmapClone(iniItems.waterManagementOptions['threshold_to_minimize_fossil_groundwater_irrigation'],\
                                 self.cloneMap, self.tmpDir, self.inputDir)
        
        # maximum daily rate of groundwater abstraction (unit: m/day)
        if 'maximumDailyGroundwaterAbstraction' not in list(iniItems.waterManagementOptions.keys()):
            msg  = 'The option "maximumDailyGroundwaterAbstraction" is not defined in the "waterManagementOptions" of the configuration file. '
            msg += 'This run assumes "0.050 m/day" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions['maximumDailyGroundwaterAbstraction'] = "0.050"
        self.maximumDailyGroundwaterAbstraction = vos.readPCRmapClone(iniItems.waterManagementOptions['maximumDailyGroundwaterAbstraction'],\
                                                                      self.cloneMap, self.tmpDir, self.inputDir)
        
        # maximum daily rate of fossil groundwater abstraction (unit: m/day)
        if 'maximumDailyFossilGroundwaterAbstraction' not in list(iniItems.waterManagementOptions.keys()):
            msg  = 'The option "maximumDailyFossilGroundwaterAbstraction" is not defined in the "waterManagementOptions" of the configuration file. '
            msg += 'This run assumes "0.020 m/day" for this option.'
            logger.warning(msg)
            iniItems.waterManagementOptions['maximumDailyFossilGroundwaterAbstraction'] = "0.020"
        self.maximumDailyFossilGroundwaterAbstraction = vos.readPCRmapClone(iniItems.waterManagementOptions['maximumDailyFossilGroundwaterAbstraction'],\
                                                                            self.cloneMap, self.tmpDir, self.inputDir)    
        
        # maximum pre-defined surface water source fraction for satisfying industrial and domestic water demand:
        # - if not defined (default), set it to the maximum 
        self.maximumNonIrrigationSurfaceWaterAbstractionFractionData = pcr.scalar(1.0)
        if 'maximumNonIrrigationSurfaceWaterAbstractionFractionData' in list(iniItems.waterManagementOptions.keys()):
            if iniItems.waterManagementOptions['maximumNonIrrigationSurfaceWaterAbstractionFractionData'] != "None" or \
               iniItems.waterManagementOptions['maximumNonIrrigationSurfaceWaterAbstractionFractionData'] != "False":
                
                logger.info('Set the maximum fraction for predefined surface water source for satisfying domestic and industrial demand.')
                self.maximumNonIrrigationSurfaceWaterAbstractionFractionData = pcr.min(1.0,\
                                                                               pcr.cover(\
                                                                               vos.readPCRmapClone(iniItems.waterManagementOptions['maximumNonIrrigationSurfaceWaterAbstractionFractionData'],\
                                                                                                   self.cloneMap,self.tmpDir,self.inputDir), 1.0))
        
        # pre-defined surface water source fraction for satisfying industrial and domestic water demand
        self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData = None
        if 'predefinedNonIrrigationSurfaceWaterAbstractionFractionData' in list(iniItems.waterManagementOptions.keys()) and \
           (iniItems.waterManagementOptions['predefinedNonIrrigationSurfaceWaterAbstractionFractionData'] != "None" or \
            iniItems.waterManagementOptions['predefinedNonIrrigationSurfaceWaterAbstractionFractionData'] != "False"):
            
            logger.info('Set the predefined fraction of surface water source for satisfying domestic and industrial demand.')
            self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData = pcr.min(1.0,\
                                                                              pcr.cover(\
                                                                              vos.readPCRmapClone(iniItems.waterManagementOptions['predefinedNonIrrigationSurfaceWaterAbstractionFractionData'],\
                                                                                                  self.cloneMap,self.tmpDir,self.inputDir), 1.0))
            self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData = pcr.max(0.0, \
                       pcr.min(self.maximumNonIrrigationSurfaceWaterAbstractionFractionData, \
                            self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData))


    def get_allocation_zone(self, zonal_map_file_name):
        # read in the allocation zones
        allocSegments = vos.readPCRmapClone( \
                            zonal_map_file_name,
                            self.cloneMap, self.tmpDir, self.inputDir,\
                            isLddMap=False, cover=None, isNomMap=True)
        allocSegments = pcr.ifthen(self.landmask, allocSegments)
        allocSegments = pcr.clump(allocSegments)
        
        extrapolate = True
        if "noParameterExtrapolation" in self.iniItems.waterManagementOptions.keys() and self.iniItems.waterManagementOptions["noParameterExtrapolation"] == "True": extrapolate = False
        
        if extrapolate:
            # extrapolate it to half degree resolution
            allocSegments = pcr.cover(allocSegments, \
                                      pcr.windowmajority(allocSegments, 0.5))
        
        allocSegments = pcr.ifthen(self.landmask, allocSegments)
        
        # clump it and cover the rests with cell ids 
        allocSegments = pcr.clump(allocSegments)
        cell_ids = pcr.mapmaximum(pcr.scalar(allocSegments)) + pcr.scalar(100.0) + pcr.uniqueid(pcr.boolean(1.0))
        allocSegments = pcr.cover(allocSegments, pcr.nominal(cell_ids))                               
        allocSegments = pcr.clump(allocSegments)
        allocSegments = pcr.ifthen(self.landmask, allocSegments)
        
        # zonal/segment area (unit: m2)
        segmentAreas = pcr.areatotal(pcr.cover(self.cellArea, 0.0), allocSegments)
        segmentAreas = pcr.ifthen(self.landmask, segmentAreas)
        
        return allocSegments, segmentAreas  


    def waterAbstractionAndAllocation(self, 
                                      water_demand_volume,
                                      available_water_volume, 
                                      allocation_zones,
                                      zone_area = None,
                                      high_volume_threshold = None,
                                      debug_water_balance = True,\
                                      extra_info_for_water_balance_reporting = "",
                                      landmask = None,
                                      ignore_small_values = False,
                                      prioritizing_local_source = True):
        
        logger.debug("Allocation of abstraction.")
        
        if landmask is not None:
            water_demand_volume = pcr.ifthen(landmask, pcr.cover(water_demand_volume, 0.0))
            available_water_volume = pcr.ifthen(landmask, pcr.cover(available_water_volume, 0.0))
            allocation_zones = pcr.ifthen(landmask, allocation_zones)
        
        # satistify demand with local sources:
        localAllocation  = pcr.scalar(0.0)
        localAbstraction = pcr.scalar(0.0)
        cellVolDemand = pcr.max(0.0, water_demand_volume)
        cellAvlWater  = pcr.max(0.0, available_water_volume)
        if prioritizing_local_source:
            logger.debug("Allocation of abstraction - first, satisfy demand with local source.")
        
            # demand volume in each cell (unit: m3)
            if landmask is not None:
                cellVolDemand = pcr.ifthen(landmask, pcr.cover(cellVolDemand, 0.0))
            
            # total available water volume in each cell
            if landmask is not None:
                cellAvlWater = pcr.ifthen(landmask, pcr.cover(cellAvlWater, 0.0))
            
            # first, satisfy demand with local source
            localAllocation  = pcr.max(0.0, pcr.min(cellVolDemand, cellAvlWater))
            localAbstraction = localAllocation * 1.0
        
        logger.debug("Allocation of abstraction - satisfy demand with neighbour sources.")
        
        # the remaining demand and available water
        cellVolDemand = pcr.max(0.0, cellVolDemand - localAllocation )
        cellAvlWater  = pcr.max(0.0, cellAvlWater  - localAbstraction)
        
        # ignoring small values of water availability
        if ignore_small_values: available_water_volume = pcr.max(0.0, pcr.rounddown(available_water_volume))
        
        # demand volume in each cell (unit: m3)
        cellVolDemand = pcr.max(0.0, cellVolDemand)
        if landmask is not None:
            cellVolDemand = pcr.ifthen(landmask, pcr.cover(cellVolDemand, 0.0))
        
        # total demand volume in each zone/segment (unit: m3)
        zoneVolDemand = pcr.areatotal(cellVolDemand, allocation_zones)
        
        # avoid very high values of available water
        cellAvlWater  = pcr.min(cellAvlWater, zoneVolDemand)
        
        # total available water volume in each cell
        cellAvlWater  = pcr.max(0.0, cellAvlWater)
        if landmask is not None:
            cellAvlWater = pcr.ifthen(landmask, pcr.cover(cellAvlWater, 0.0))
        
        # total available water volume in each zone/segment (unit: m3)
        zoneAvlWater  = pcr.areatotal(cellAvlWater, allocation_zones)
        
        # total actual water abstraction volume in each zone/segment (unit: m3)
        # - limited to available water
        zoneAbstraction = pcr.min(zoneAvlWater, zoneVolDemand)
        
        # actual water abstraction volume in each cell (unit: m3)
        cellAbstraction = vos.getValDivZero(\
                          cellAvlWater, zoneAvlWater, vos.smallNumber) * zoneAbstraction
        cellAbstraction = pcr.min(cellAbstraction, cellAvlWater)
        
        # to minimize numerical errors
        if high_volume_threshold is not None:
            # mask: 0 for small volumes ; 1 for large volumes (e.g. lakes and reservoirs)
            mask = pcr.cover(\
                   pcr.ifthen(cellAbstraction > high_volume_threshold, pcr.boolean(1)), pcr.boolean(0))
            zoneAbstraction  = pcr.areatotal(
                               pcr.ifthenelse(mask, 0.0, cellAbstraction), allocation_zones)
            zoneAbstraction += pcr.areatotal(                
                               pcr.ifthenelse(mask, cellAbstraction, 0.0), allocation_zones)
        
        # allocation water to meet water demand (unit: m3)
        cellAllocation  = vos.getValDivZero(\
                          cellVolDemand, zoneVolDemand, vos.smallNumber) * zoneAbstraction 
        cellAllocation  = pcr.min(cellAllocation,  cellVolDemand)
        
        # adding local abstraction and local allocation
        cellAbstraction = cellAbstraction + localAbstraction
        cellAllocation  = cellAllocation  + localAllocation
        
        if debug_water_balance and zone_area is not None:
            vos.waterBalanceCheck([pcr.cover(pcr.areatotal(cellAbstraction, allocation_zones)/zone_area, 0.0)],\
                                  [pcr.cover(pcr.areatotal(cellAllocation , allocation_zones)/zone_area, 0.0)],\
                                  [pcr.scalar(0.0)],\
                                  [pcr.scalar(0.0)],\
                                  'abstraction - allocation per zone/segment (PS: Error here may be caused by rounding error.)' ,\
                                   True,\
                                   extra_info_for_water_balance_reporting, threshold=1e-4)
        
        return cellAbstraction, cellAllocation, zoneAbstraction


    def update(self, \
                vol_gross_sectoral_water_demands,
                groundwater, routing, currTimeStep):
        
        # total volume of irrigation and livestock demand (not limited by available water)
        # variable needed while allocating groundwater use
        # (units: m3)
        self.volTotalIrrigationLivestockDemand = vol_gross_sectoral_water_demands["irrigation"] +\
                                                 vol_gross_sectoral_water_demands["livestock"]
        
        # initiate the variables for remaining sectoral water demands and accumulated/satisfied_gross_sectoral_water_demand variables
        # (units: m3)
        self.satisfied_gross_sectoral_water_demands = {}
        self.remaining_gross_sectoral_water_demands = {}
        
        for sector_name in self.sector_names:
             self.satisfied_gross_sectoral_water_demands[sector_name] = pcr.scalar(0.0) 
             self.remaining_gross_sectoral_water_demands[sector_name] = vol_gross_sectoral_water_demands[sector_name]
        
        # initiate the variables for remaining volumes of surface water, as well as renewable and non renewable groundwater
        # (units: m3)
        self.available_surface_water_volume     = routing.readAvlChannelStorage
        self.available_renewable_groundwater    = groundwater.storGroundwater       * self.cellArea
        self.available_nonrenewable_groundwater = groundwater.storGroundwaterFossil * self.cellArea 
        
        # abstract and allocate desalinated water
        # - this will return the following:
        #   - self.allocated_demand_per_sector["desalinated_water"]
        #   - self.allocated_withdrawal_per_sector["desalinated_water"]
        self.abstraction_and_allocation_from_desalination(\
                 remaining_gross_sectoral_water_demands = self.remaining_gross_sectoral_water_demands,\
                 currTimeStep                           = currTimeStep)
        
        # update the following after abstraction and allocation of desalinated water
        #   - the updated self.remaining_gross_sectoral_water_demands (after desalinated_water use)
        #   - the updated self.satisfied_gross_sectoral_water_demands (after desalinated_water use)
        # ~ for sector_name in vol_gross_sectoral_water_demands.keys():
        for sector_name in self.sector_names:
             self.satisfied_gross_sectoral_water_demands[sector_name] += self.allocated_demand_per_sector["desalinated_water"][sector_name]  
             self.remaining_gross_sectoral_water_demands[sector_name] -= self.allocated_demand_per_sector["desalinated_water"][sector_name]
             self.remaining_gross_sectoral_water_demands[sector_name]  = pcr.max(0.0, self.remaining_gross_sectoral_water_demands[sector_name])
        
        # abstract and allocate surface water
        # - this will return the following:
        #   - self.allocated_demand_per_sector["surface_water"]
        #   - self.allocated_withdrawal_per_sector["surface_water"]
        self.abstraction_and_allocation_from_surface_water(
                 remaining_gross_sectoral_water_demands = self.remaining_gross_sectoral_water_demands, \
                 available_surface_water_volume         = self.available_surface_water_volume, \
                 routing                                = routing, \
                 groundwater                            = groundwater,\
                 currTimeStep                           = currTimeStep)
        
        # update the following after abstraction and allocation of surface water
        #   - the updated self.remaining_gross_sectoral_water_demands
        #   - the updated self.satisfied_gross_sectoral_water_demands
        for sector_name in self.sector_names:
             self.satisfied_gross_sectoral_water_demands[sector_name] += self.allocated_demand_per_sector["surface_water"][sector_name]  
             self.remaining_gross_sectoral_water_demands[sector_name] -= self.allocated_demand_per_sector["surface_water"][sector_name]
             self.remaining_gross_sectoral_water_demands[sector_name]  = pcr.max(0.0, self.remaining_gross_sectoral_water_demands[sector_name])
        
        # abstract and allocate groundwater
        # - this will return the following:
        #   - self.allocated_demand_per_sector["renewable_groundwater"]
        #   - self.allocated_withdrawal_per_sector["renewable_groundwater"]
        #   - self.allocated_demand_per_sector["nonrenewable_groundwater"]
        #   - self.allocated_withdrawal_per_sector["nonrenewable_groundwater"]
        self.abstraction_and_allocation_from_groundwater(
                 remaining_gross_sectoral_water_demands = self.remaining_gross_sectoral_water_demands,\
                 routing                                = routing,\
                 groundwater                            = groundwater,\
                 currTimeStep                           = currTimeStep)
        
        # update the following after abstraction and allocation of renewable_groundwater
        #   - the updated self.remaining_gross_sectoral_water_demands
        #   - the updated self.satisfied_gross_sectoral_water_demands
        for sector_name in self.sector_names:
             self.satisfied_gross_sectoral_water_demands[sector_name] += self.allocated_demand_per_sector["renewable_groundwater"][sector_name]  
             self.remaining_gross_sectoral_water_demands[sector_name] -= self.allocated_demand_per_sector["renewable_groundwater"][sector_name]
             self.remaining_gross_sectoral_water_demands[sector_name]  = pcr.max(0.0, self.remaining_gross_sectoral_water_demands[sector_name])
        
        # update the following after abstraction and allocation of nonrenewable_groundwater
        #   - the updated self.remaining_gross_sectoral_water_demands
        #   - the updated self.satisfied_gross_sectoral_water_demands
        for sector_name in self.sector_names:
             self.satisfied_gross_sectoral_water_demands[sector_name] += self.allocated_demand_per_sector["nonrenewable_groundwater"][sector_name]  
             self.remaining_gross_sectoral_water_demands[sector_name] -= self.allocated_demand_per_sector["nonrenewable_groundwater"][sector_name]
             self.remaining_gross_sectoral_water_demands[sector_name]  = pcr.max(0.0, self.remaining_gross_sectoral_water_demands[sector_name])
    
    
    
    def allocate_satisfied_demand_to_each_sector(self, \
                                                 totalVolWaterAllocation, \
                                                 sectoral_remaining_demand_volume, \
                                                 total_remaining_demand_volume):
        
        # initialize the output dictionary
        allocated_demand_per_sector = {}
        
        # distributes the total water allocated to the cell across the sectors
        # proportional to their remaining demands
        for sector_name in self.sector_names:
            allocated_demand_per_sector[sector_name] = \
                pcr.ifthenelse(total_remaining_demand_volume > 0.0, \
                               totalVolWaterAllocation * \
                               vos.getValDivZero(sectoral_remaining_demand_volume[sector_name],\
                                                 total_remaining_demand_volume),\
                               0.0)
        
        # return water allocated per sector
        # (units: m3)
        return allocated_demand_per_sector
    
    
    
    def allocate_withdrawal_to_each_sector(self, \
                                            totalVolCellWaterAbstraction, \
                                            totalVolZoneAbstraction, \
                                            cellAllocatedDemandPerSector, \
                                            allocation_zones = None):
        
        # initialize the output dictionary
        allocated_withdrawal_per_sector = {}
        
        # with allocation zone
        if allocation_zones is not None:
            zonal_allocated_withdrawal_per_sector = {}
            
            for sector_name in self.sector_names:
                # get the total water allocated over the entire allocation zone per sector
                zonal_allocated_withdrawal_per_sector[sector_name] = \
                    pcr.areatotal(cellAllocatedDemandPerSector[sector_name],\
                                  allocation_zones)   
                
                # distribute the total water abstracted per sector 
                # scaling the water abstracted per cell proportional to the
                # zonal water allocated per sector over the total water allocated
                # note:
                #     total zonal water allocated = total zonal water abstracted
                allocated_withdrawal_per_sector[sector_name] = \
                    totalVolCellWaterAbstraction * vos.getValDivZero(zonal_allocated_withdrawal_per_sector[sector_name],\
                                                                     totalVolZoneAbstraction)
        
        # without allocation zone
        else:
            # water allocated and abstracted has the same value
            allocated_withdrawal_per_sector = cellAllocatedDemandPerSector
        
        # return water withdrawal per sector
        # (units: m3)
        return allocated_withdrawal_per_sector



    def abstraction_and_allocation_from_desalination(self, \
                                                      remaining_gross_sectoral_water_demands,\
                                                      currTimeStep):
        
        # get the TOTAL (remaining) demand
        # (units: m3)
        volTotalRemainingDemand = pcr.scalar(0.0) 
        for sector_name in remaining_gross_sectoral_water_demands.keys():
             volTotalRemainingDemand = volTotalRemainingDemand + remaining_gross_sectoral_water_demands[sector_name]
        
        # get desalination water use
        # (units: m/day)
        # note: previous var_name = 'desalination_water_use' 
        if self.includeDesalination: 
            logger.debug("Monthly desalination water use is included.")
            if (currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1):
                desalinationWaterUse = \
                   pcr.ifthen(self.landmask,\
                              pcr.cover(\
                                        vos.netcdf2PCRobjClone(self.desalinationWaterFile,\
                                                               'desal_capacity',\
                                                               currTimeStep.fulldate,\
                                                               useDoy = 'monthly',\
                                                               cloneMapFileName = self.cloneMap), 0.0))
                self.desalinationWaterUse = pcr.max(0.0, desalinationWaterUse)
        else:
            logger.debug("Monthly desalination water use is NOT included.")
            self.desalinationWaterUse = pcr.scalar(0.0)
        
        # convert units to volume
        # (units: m3)
        volDesalinationWaterUse = pcr.max(0.0, self.desalinationWaterUse * self.cellArea)
        
        # Abstraction and Allocation of DESALINATED WATER
        # ##################################################################################################################
        # - desalination water to satisfy water demand
        if self.using_allocationSegmentsForDesalinatedWaterSource:
            logger.debug("Allocation of supply from desalination water.")
            volDesalinationAbstraction, volDesalinationAllocation, volZoneDesalinationAbstraction = \
                self.waterAbstractionAndAllocation(
                     water_demand_volume       = volTotalRemainingDemand,\
                     available_water_volume    = volDesalinationWaterUse,\
                     allocation_zones          = self.allocationSegmentsForDesalinatedWaterSource,\
                     zone_area                 = self.allocationSegmentsForDesalinatedWaterSourceAreas,\
                     high_volume_threshold     = None,\
                     debug_water_balance       = True,\
                     extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
                     landmask                  = self.landmask,
                     ignore_small_values       = False,
                     prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
        else:
            logger.debug("Supply from desalination water is only for satisfying local demand (no network).")
            volDesalinationAbstraction      = pcr.min(volDesalinationWaterUse, volTotalRemainingDemand)
            volDesalinationAllocation       = volDesalinationAbstraction
            volZoneDesalinationAbstraction  = volDesalinationAbstraction
        # ##################################################################################################################
        # - end of Abstraction and Allocation of DESALINATED WATER
        
        # allocate the "desalination Allocation" to each sector
        # (units: m3)
        self.allocated_demand_per_sector["desalinated_water"] = \
             self.allocate_satisfied_demand_to_each_sector(totalVolWaterAllocation          = volDesalinationAllocation,\
                                                          sectoral_remaining_demand_volume = remaining_gross_sectoral_water_demands,\
                                                          total_remaining_demand_volume    = volTotalRemainingDemand)
        
        # allocate the "desalination Abastraction" to each sector
        # (units: m3)
        self.allocated_withdrawal_per_sector["desalinated_water"] = \
             self.allocate_withdrawal_to_each_sector(totalVolCellWaterAbstraction = volDesalinationAbstraction,\
                                                     totalVolZoneAbstraction      = volZoneDesalinationAbstraction,\
                                                     cellAllocatedDemandPerSector = self.allocated_demand_per_sector["desalinated_water"],\
                                                     allocation_zones             = self.allocationSegmentsForDesalinatedWaterSource)
        
        # remaining desalination water use
        # (units: m3)
        self.volRemainingDesalinationWaterUse = pcr.max(0.0, volDesalinationWaterUse - volDesalinationAbstraction)
        
        # make the total desalination Allocation and Abstraction variables available for other modules
        # (units: m)
        self.desalinationAllocation  = volDesalinationAllocation  / self.cellArea
        self.desalinationAbstraction = volDesalinationAbstraction / self.cellArea
    
    
    
    def abstraction_and_allocation_from_surface_water(self, \
                                                       remaining_gross_sectoral_water_demands, \
                                                       available_surface_water_volume, \
                                                       routing, \
                                                       groundwater, \
                                                       currTimeStep):
        
        # Abstraction and Allocation of SURFACE WATER
        ##############################################################################################################################
        # calculate the estimate of surface water demand (considering by swAbstractionFractionDict)
        
        # get a dictionary containing the partitioning of withdrawal/abstraction sources:
        # from groundwater and surface water
        self.swAbstractionFractionDict = self.partitioningGroundSurfaceAbstraction(routing)
        
        # surface water abstraction fraction for industrial, domestic, manufacturing and thermoelectic
        # excluding irrigation and livestock
        swAbstractionFraction_industrial_domestic = pcr.min(self.swAbstractionFractionDict['max_for_non_irrigation'],\
                                                            self.swAbstractionFractionDict['estimate'])
        
        if self.swAbstractionFractionDict['non_irrigation'] is not None:
            swAbstractionFraction_industrial_domestic = self.swAbstractionFractionDict['non_irrigation']
        
        # calculate the remaining demands for the following combined sectors 
        # (units: m3)
        remainingIndustrialDomestic   = pcr.scalar(0.0)
        remainingIrrigationLivestock  = pcr.scalar(0.0)
        
        for sector_name in remaining_gross_sectoral_water_demands.keys():
            if sector_name not in ["irrigation" ,"livestock"]:
                remainingIndustrialDomestic  += remaining_gross_sectoral_water_demands[sector_name]
            else:
                remainingIrrigationLivestock += remaining_gross_sectoral_water_demands[sector_name]
        
        # total remaining demand, from all sectors
        # (units: m3)
        remainingTotalDemand = remainingIndustrialDomestic + remainingIrrigationLivestock        
       
        # surface water demand estimate (first, only from sectors outside irrigation and livestock)
        # (units: m3)
        surface_water_demand_estimate = swAbstractionFraction_industrial_domestic * remainingIndustrialDomestic
        
        # surface water demand estimate for irrigation and livestock
        # (units: m3)
        surface_water_irrigation_demand_estimate = self.swAbstractionFractionDict['irrigation'] * remainingIrrigationLivestock

        # surface water source as priority if groundwater irrigation fraction is relatively low
        # (unit: m3)
        surface_water_irrigation_demand_estimate = \
           pcr.ifthenelse(self.swAbstractionFractionDict['irrigation'] >= self.swAbstractionFractionDict['threshold_to_maximize_irrigation_surface_water'],\
                          remainingIrrigationLivestock,\
                          surface_water_irrigation_demand_estimate)
        
        # update estimate of surface water demand withdrawal
        # (units: m3)
        surface_water_demand_estimate += surface_water_irrigation_demand_estimate

        # prioritize surface water use in non productive aquifers that have limited groundwater supply
        # (units: m3)
        surface_water_demand_estimate = \
            pcr.ifthenelse(groundwater.productive_aquifer,\
                           surface_water_demand_estimate,\
                           pcr.max(0.0,\
                                   remainingIrrigationLivestock - pcr.min(groundwater.avgAllocationShort,\
                                                                          groundwater.avgAllocation) * self.cellArea))
        
        # maximize/optimize surface water use in areas with the overestimation of groundwater supply
        # (units: m3)
        surface_water_demand_estimate += pcr.max(0.0, \
                                                 pcr.max(groundwater.avgAllocationShort * self.cellArea,\
                                                         groundwater.avgAllocation * self.cellArea) -\
                                                 (1.0 - self.swAbstractionFractionDict['irrigation']) * remainingIrrigationLivestock -\
                                                 (1.0 - swAbstractionFraction_industrial_domestic) * (remainingIndustrialDomestic))
        
        # total demand that should be allocated from surface water 
        # (corrected/limited by swAbstractionFractionDict and limited by the remaining demand)
        # (units: m3) 
        surface_water_demand_estimate         = pcr.min(remainingTotalDemand, surface_water_demand_estimate)
        correctedRemainingIrrigationLivestock = pcr.min(surface_water_demand_estimate, remainingIrrigationLivestock)
        correctedRemainingIndustrialDomestic  = pcr.min(remainingIndustrialDomestic,\
                                                pcr.max(0.0, surface_water_demand_estimate - remainingIrrigationLivestock))
        correctedSurfaceWaterDemandEstimate   = correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic
        surface_water_demand = correctedSurfaceWaterDemandEstimate
        
        # if surface water abstraction as the first priority
        if self.surfaceWaterPiority: surface_water_demand = remainingTotalDemand
        
        # TODO: Incorporate the "environmental flow" concept of Rens. This may affect the estimate of 'surface_water_demand'.
        
        # Abstraction and Allocation of SURFACE WATER
        # ##################################################################################################################
        # - surface water to satisfy water demand
        if self.using_allocationSegmentsForSurfaceWaterSource:
            logger.debug("Allocation of supply from surface water.")
            volSurfaceWaterAbstraction, volSurfaceWaterAllocation, volZoneSurfaceWaterAbstraction = \
               self.waterAbstractionAndAllocation(
                    water_demand_volume       = surface_water_demand,\
                    available_water_volume    = available_surface_water_volume,\
                    allocation_zones          = self.allocationSegmentsForSurfaceWaterSource,\
                    zone_area                 = self.allocationSegmentsForSurfaceWaterSourceAreas,\
                    high_volume_threshold     = None,\
                    debug_water_balance       = True,\
                    extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
                    landmask                  = self.landmask,
                    ignore_small_values       = False,
                    prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
        else: 
            logger.debug("Supply from surface water is only for satisfying local demand (no network).")
            volSurfaceWaterAbstraction      = pcr.min(available_surface_water_volume, surface_water_demand)
            volSurfaceWaterAllocation       = volSurfaceWaterAbstraction
            volZoneSurfaceWaterAbstraction  = volSurfaceWaterAbstraction
        # ##################################################################################################################
        # - end of Abstraction and Allocation of SURFACE WATER
        
        # allocate the "surface water Allocation" to each sector
        # (units: m3)
        self.allocated_demand_per_sector["surface_water"] = \
             self.allocate_satisfied_demand_to_each_sector(\
                  totalVolWaterAllocation          = volSurfaceWaterAllocation,\
                  sectoral_remaining_demand_volume = remaining_gross_sectoral_water_demands,\
                  total_remaining_demand_volume    = remainingTotalDemand)
        
        # allocate the "surface water Abastraction" to each sector
        # (units: m3)
        self.allocated_withdrawal_per_sector["surface_water"] = \
             self.allocate_withdrawal_to_each_sector(\
                  totalVolCellWaterAbstraction = volSurfaceWaterAbstraction,\
                  totalVolZoneAbstraction      = volZoneSurfaceWaterAbstraction,\
                  cellAllocatedDemandPerSector = self.allocated_demand_per_sector["surface_water"],\
                  allocation_zones             = self.allocationSegmentsForSurfaceWaterSource)
        
        # remaining surface water that can be extracted
        # (units: m3)
        volRemainingSurfaceWater = pcr.max(0.0,  available_surface_water_volume - volSurfaceWaterAbstraction)
        
        # make the total surface water Allocation and Abstraction variables available for other modules
        # (units: m)
        self.allocSurfaceWaterAbstract = volSurfaceWaterAllocation  / self.cellArea
        self.actSurfaceWaterAbstract   = volSurfaceWaterAbstraction / self.cellArea
    
    
    
    def abstraction_and_allocation_from_groundwater(self, \
                                                     remaining_gross_sectoral_water_demands, \
                                                     routing, \
                                                     groundwater, \
                                                     currTimeStep):
        
        # calculate the remaining demands for the following combined sectors
        # (units: m3)
        remainingIndustrialDomestic   = pcr.scalar(0.0)
        remainingIrrigationLivestock  = pcr.scalar(0.0)
        
        for sector_name in remaining_gross_sectoral_water_demands.keys():
            if sector_name not in ["irrigation" ,"livestock"]:
                remainingIndustrialDomestic  += remaining_gross_sectoral_water_demands[sector_name]
            else:
                remainingIrrigationLivestock += remaining_gross_sectoral_water_demands[sector_name]
        
        # total remaining demand, from all sectors
        # (units: m3)
        remainingTotalDemand = remainingIndustrialDomestic + remainingIrrigationLivestock        
        
        # Abstraction and Allocation of GROUNDWATER (ALL: renewable (non-fossil) and non-renewable (fossil))
        #########################################################################################################################
        # estimating groundwater water demand:
        # - demand for industrial and domestic sectors 
        #   (all remaining demand for these sectors should be satisfied)
        groundwater_demand_estimate = remainingIndustrialDomestic
        # - demand for irrigation and livestock sectors
        #   (only part of them will be satisfied, as they may be too high due to the uncertainty in the irrigation scheme)
        irrigationLivestockGroundwaterDemand = pcr.min(remainingIrrigationLivestock, \
                                               pcr.max(0.0, \
                                               (1.0 - self.swAbstractionFractionDict['irrigation']) * remainingIrrigationLivestock))
        groundwater_demand_estimate += irrigationLivestockGroundwaterDemand
        
        #############################################################################################################################
        # water demand that must be satisfied by groundwater abstraction (not limited to available water) - NOTE the unit is m3/day #
        self.potVolGroundwaterAbstract = pcr.min(remainingTotalDemand, groundwater_demand_estimate)                                 #
        #############################################################################################################################
        
        # set/update regional annual groundwater pumping capacity (at the begining of the year or at the beginning of simulation)
        #groundwater_pumping_region_ids
        #regionalAnnualGroundwaterAbstractionLimit
        
        if self.limitRegionalAnnualGroundwaterAbstraction:
            
            logger.debug('Total groundwater abstraction is limited by regional annual pumping capacity.')
            if currTimeStep.doy == 1 or currTimeStep.timeStepPCR == 1:
            
                self.groundwater_pumping_region_ids = \
                     vos.netcdf2PCRobjClone(groundwater.pumpingCapacityNC,\
                                            'region_ids',\
                                            currTimeStep.fulldate,\
                                            useDoy = 'yearly',\
                                            cloneMapFileName = self.cloneMap)
                
                other_ids = pcr.mapmaximum(self.groundwater_pumping_region_ids) + pcr.scalar(1000.) + pcr.uniqueid(self.landmask)
                self.groundwater_pumping_region_ids = pcr.cover(self.groundwater_pumping_region_ids, other_ids)
                self.groundwater_pumping_region_ids = pcr.ifthen(self.landmask, pcr.nominal(self.groundwater_pumping_region_ids))
                
                self.regionalAnnualGroundwaterAbstractionLimit = \
                     pcr.ifthen(self.landmask,\
                                pcr.cover(vos.netcdf2PCRobjClone(groundwater.pumpingCapacityNC,\
                                                                 'regional_pumping_limit',\
                                                                 currTimeStep.fulldate,\
                                                                 useDoy = 'yearly',\
                                                                 cloneMapFileName = self.cloneMap), 0.0))
                
                self.regionalAnnualGroundwaterAbstractionLimit = pcr.areamaximum(self.regionalAnnualGroundwaterAbstractionLimit, self.groundwater_pumping_region_ids)
                
                self.regionalAnnualGroundwaterAbstractionLimit *= 1000. * 1000. * 1000. # unit: m3/year
                self.regionalAnnualGroundwaterAbstractionLimit  = pcr.ifthen(self.landmask,\
                                                                             self.regionalAnnualGroundwaterAbstractionLimit)
                # minimum value (unit: m3/year at the regional scale)
                minimum_value = 1000.
                self.regionalAnnualGroundwaterAbstractionLimit  = pcr.max(minimum_value,\
                                                                  self.regionalAnnualGroundwaterAbstractionLimit)                                                         
        else:
            logger.debug('Total groundwater abstraction is NOT limited by regional annual pumping capacity.')
            self.groundwater_pumping_region_ids = None
            self.regionalAnnualGroundwaterAbstractionLimit = None
        
        # constraining groundwater abstraction with the regional annual pumping capacity
        if self.limitRegionalAnnualGroundwaterAbstraction:
            
            logger.debug('Total groundwater abstraction is limited by regional annual pumping capacity.')
            
            # estimate of total groundwater abstraction from the last 365 days
            # (units: m3)
            tolerating_days = 0.
            annualGroundwaterAbstraction = groundwater.avgAbstraction * self.cellArea *\
                                           pcr.min(pcr.max(0.0, 365.0 - tolerating_days), routing.timestepsToAvgDischarge)
            # note: the groundwater.avgAbstraction must be in meter (to be consistent with previous versions) 
            
            # total groundwater abstraction (m3) from the last 365 days at the regional scale
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(pcr.cover(annualGroundwaterAbstraction, 0.0), self.groundwater_pumping_region_ids)
            
            # the remaining pumping capacity (unit: m3) at the regional scale
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.max(0.0, self.regionalAnnualGroundwaterAbstractionLimit - \
                                                                              regionalAnnualGroundwaterAbstraction)
            # considering safety factor (residence time in day-1)                                                                  
            remainingRegionalAnnualGroundwaterAbstractionLimit *= 0.33
            
            # the remaining pumping capacity (unit: m3) limited by self.potVolGroundwaterAbstract (at the regional scale)
            remainingRegionalAnnualGroundwaterAbstractionLimit = pcr.min(remainingRegionalAnnualGroundwaterAbstractionLimit,\
                                                                         pcr.areatotal(self.potVolGroundwaterAbstract, self.groundwater_pumping_region_ids))
            
            # the remaining pumping capacity (unit: m3) at the pixel scale - downscaled using self.potVolGroundwaterAbstract
            remainingPixelAnnualGroundwaterAbstractionLimit = remainingRegionalAnnualGroundwaterAbstractionLimit * \
                vos.getValDivZero(self.potVolGroundwaterAbstract, pcr.areatotal(self.potVolGroundwaterAbstract, self.groundwater_pumping_region_ids))
                
            # reduced (after pumping capacity) potential groundwater abstraction/demand (unit: m3) and considering the average recharge (baseflow) 
            self.potVolGroundwaterAbstract = pcr.min(self.potVolGroundwaterAbstract, \
                                      remainingPixelAnnualGroundwaterAbstractionLimit + pcr.max(0.0, routing.avgBaseflow ))
            
        else:
            logger.debug('NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction.')
        
        # Abstraction and Allocation of NON-FOSSIL GROUNDWATER
        # #################################################################################################################################
        # available storGroundwater (non fossil groundwater) that can be accessed (NOTE: All the following variable must have the unit  m3)
        readAvlStorGroundwater = pcr.cover(pcr.max(0.00, groundwater.storGroundwater * self.cellArea), 0.0) 
        # - considering maximum daily groundwater abstraction
        readAvlStorGroundwater = pcr.min(readAvlStorGroundwater, self.maximumDailyGroundwaterAbstraction * self.cellArea) 
        # - ignore groundwater storage in non-productive aquifer 
        readAvlStorGroundwater = pcr.ifthenelse(groundwater.productive_aquifer, readAvlStorGroundwater, 0.0)
        # for non-productive aquifer, reduce readAvlStorGroundwater to the current recharge/baseflow rate
        readAvlStorGroundwater = pcr.ifthenelse(groundwater.productive_aquifer, \
                                                readAvlStorGroundwater, pcr.min(readAvlStorGroundwater, pcr.max(routing.avgBaseflow * 24. * 3600., 0.0)))
        # avoid the condition that the entire groundwater volume abstracted instantaneously
        readAvlStorGroundwater *= 0.75
        
        # Abstraction and Allocation of RENEWABLE GROUNDWATER
        # ##################################################################################################################
        # - renewable groundwater to satisfy water demand
        if self.using_allocationSegmentsForGroundwaterSource:
            logger.debug("Allocation of supply from renewable groundwater.")
            volRenewGroundwaterAbstraction, volRenewGroundwaterAllocation, volZoneRenewGroundwaterAbstraction = \
               self.waterAbstractionAndAllocation(
                    water_demand_volume       = self.potVolGroundwaterAbstract,\
                    available_water_volume    = readAvlStorGroundwater,\
                    allocation_zones          = self.allocationSegmentsForGroundwaterSource,\
                    zone_area                 = self.allocationSegmentsForGroundwaterSourceAreas,\
                    high_volume_threshold     = None,\
                    debug_water_balance       = True,\
                    extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
                    landmask                  = self.landmask,
                    ignore_small_values       = False,
                    prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
        else:
            logger.debug("Supply from renewable groundwater is only for satisfying local demand (no network).")
            volRenewGroundwaterAbstraction      = pcr.min(readAvlStorGroundwater, self.potVolGroundwaterAbstract)
            volRenewGroundwaterAllocation       = volRenewGroundwaterAbstraction
            volZoneRenewGroundwaterAbstraction  = volRenewGroundwaterAbstraction
        # ##################################################################################################################
        # - end of Abstraction and Allocation of RENEWABLE GROUNDWATER
        
        # allocate the "renewable groundwater Allocation" to each sector
        # (units: m3)
        self.allocated_demand_per_sector["renewable_groundwater"] = self.allocate_satisfied_demand_to_each_sector(totalVolWaterAllocation = volRenewGroundwaterAllocation, sectoral_remaining_demand_volume = remaining_gross_sectoral_water_demands, total_remaining_demand_volume = remainingTotalDemand)
        
        # allocate the "renewable groundwater Abstraction" to each sector
        # (units: m3)
        self.allocated_withdrawal_per_sector["renewable_groundwater"] = self.allocate_withdrawal_to_each_sector(totalVolCellWaterAbstraction = volRenewGroundwaterAbstraction, totalVolZoneAbstraction = volZoneRenewGroundwaterAbstraction, cellAllocatedDemandPerSector = self.allocated_demand_per_sector["renewable_groundwater"], allocation_zones = self.allocationSegmentsForGroundwaterSource)
        
        # make the total renewable groundwater Allocation and Abstraction variables available for other modules
        # (units: m)
        self.allocNonFossilGroundwater = volRenewGroundwaterAllocation  / self.cellArea
        self.nonFossilGroundwaterAbs   = volRenewGroundwaterAbstraction / self.cellArea
        
        # somehow the following is needed for allocating fossil groundwater
        self.satisfiedIrrigationDemandFromNonFossilGroundwater = self.allocated_demand_per_sector["renewable_groundwater"]["irrigation"]
        
        # update remaining_gross_sectoral_water_demands after renewable groundwater allocation
        for sector_name in remaining_gross_sectoral_water_demands.keys():
             remaining_gross_sectoral_water_demands[sector_name] = pcr.max(0.0, remaining_gross_sectoral_water_demands[sector_name] - \
                                                             self.allocated_demand_per_sector["renewable_groundwater"][sector_name])
        
        # remaining renewable groundwater that can still be extracted - unit: m3
        self.volRemainingRenewGroundwater = pcr.max(0.0,  readAvlStorGroundwater - volRenewGroundwaterAbstraction)
        
        ################################################################################################################################
        # variable to reduce capillary rise in order to ensure there is always enough water to supply non fossil groundwater abstraction 
        # - unit: m
        self.reducedCapRise = volRenewGroundwaterAbstraction / self.cellArea                            
        # TODO: Check do we need this for runs with MODFLOW ???
        ################################################################################################################################
        
        ################################################################################################################################
        # water demand that must be satisfied by fossil groundwater abstraction (not limited to available water) NOTE the unit is m3/day 
        self.potVolFossilGroundwaterAbstract = pcr.max(0.0, self.potVolGroundwaterAbstract - \
                                                            volRenewGroundwaterAllocation )
        ################################################################################################################################
        
        # For a run using MODFLOW, the concept of fossil groundwater abstraction is abandoned (self.limitAbstraction == True):
        if groundwater.useMODFLOW or self.limitAbstraction:
            logger.debug('Fossil groundwater abstractions are NOT allowed')
            volNonRenewGroundwaterAbstraction = pcr.scalar(0.0)
            volNonRenewGroundwaterAllocation  = pcr.scalar(0.0)
        
        # Abstraction and Allocation of FOSSIL GROUNDWATER
        # #####################################################################################################################################
        
        if self.limitAbstraction == False:                              # TODO: For runs without any water use, we can exclude this. 
            
            logger.debug('Fossil groundwater abstractions are allowed.')
            
            # the remaining water demand (m3/day) for all sectors - NOT limited to self.potFossilGroundwaterAbstract
            #####################################################################################################################
            # - for domestic 
            remainingDomestic   = remaining_gross_sectoral_water_demands['domestic']
            # - for industry 
            remainingIndustry   = remaining_gross_sectoral_water_demands['industry']
            # - for livestock 
            remainingLivestock  = remaining_gross_sectoral_water_demands['livestock']
            # - for irrigation (excluding livestock)
            remainingIrrigation = remaining_gross_sectoral_water_demands['irrigation'] 
            
            # - total for livestock and irrigation
            remainingIrrigationLivestock = remainingIrrigation + remainingLivestock
            # - total for industrial and domestic (excluding livestock)
            remainingIndustrialDomestic  = remainingIndustry + remainingDomestic
            # - remaining total demand
            remainingTotalDemand = remainingIrrigationLivestock + remainingIndustrialDomestic
            
            # TODO: Make the above variables (remainingDomestic, remainingIndustry ... etc) more flexible, especially if we have more and different sector names.
        
        # constraining fossil groundwater abstraction with regional pumping capacity
        if self.limitRegionalAnnualGroundwaterAbstraction and self.limitAbstraction == False:
            
            logger.debug('Fossil groundwater abstraction is allowed, BUT limited by the regional annual pumping capacity.')
            
            # estimate of total groundwater abstraction (m3) from the last 365 days:
            # - considering abstraction from non fossil groundwater
            annualGroundwaterAbstraction += volRenewGroundwaterAbstraction
            
            # at the regional scale
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(pcr.cover(annualGroundwaterAbstraction, 0.0), self.groundwater_pumping_region_ids)
            
            # fossil groundwater demand/asbtraction reduced by pumping capacity
            # (units: m3)
            # - safety factor to avoid the remaining limit abstracted at once (due to overestimation of groundwater demand)
            safety_factor_for_fossil_abstraction = 1.00
            self.potVolFossilGroundwaterAbstract *= pcr.min(1.00,\
                                                 pcr.cover(\
                                                 pcr.ifthenelse(self.regionalAnnualGroundwaterAbstractionLimit > 0.0,
                                                 pcr.max(0.000, self.regionalAnnualGroundwaterAbstractionLimit * safety_factor_for_fossil_abstraction-\
                                                                regionalAnnualGroundwaterAbstraction) /
                                                                self.regionalAnnualGroundwaterAbstractionLimit , 0.0), 0.0))
        
        if self.limitAbstraction == False:                              # TODO: For runs without any water use, we can exclude this. 
            
            ###############################################################################################################################
            # estimate the remaining total demand LIMITED to self.potVolFossilGroundwaterAbstract (units: m3)
            ###############################################################################################################################
            
            correctedRemainingTotalDemand = pcr.min(self.potVolFossilGroundwaterAbstract, remainingTotalDemand)
            
            # the remaining industrial, domestic and livestock demands limited to self.potVolFossilGroundwaterAbstract
            # - no correction, we will always try to fulfil these demands first
            # (units: m3)
            correctedRemainingIndustrialDomesticLivestock = pcr.min(remainingIndustrialDomestic + remainingLivestock,\
                                                                    correctedRemainingTotalDemand)
            
            # the remaining irrigation demand limited to self.potFossilGroundwaterAbstract
            # (units: m3)
            correctedRemainingIrrigation = pcr.min(remainingIrrigation, \
                                                   pcr.max(0.0,\
                                                           correctedRemainingTotalDemand - correctedRemainingIndustrialDomesticLivestock))
            
            # ignore small irrigation demand (less than 1 mm)
            # (units: m3)
            correctedRemainingIrrigation = pcr.rounddown(correctedRemainingIrrigation/self.cellArea*1000.)/1000. * self.cellArea
            
            # the (corrected) remaining total demand (limited to self.potVolFossilGroundwaterAbstract)
            # (units: m3)
            correctedRemainingTotalDemand = correctedRemainingIndustrialDomesticLivestock + correctedRemainingIrrigation
            
            # the (corrected) remaining industrial and domestic demand (excluding livestock)
            # (units: m3)
            correctedRemainingIndustrialDomestic = pcr.min(remainingIndustrialDomestic, correctedRemainingTotalDemand)

            # the remaining irrigation and livestock water demand limited to self.potFossilGroundwaterAbstract
            # (units: m3)
            correctedRemainingIrrigationLivestock = pcr.min(remainingIrrigationLivestock, \
                                                            pcr.max(0.0,\
                                                                    correctedRemainingTotalDemand - correctedRemainingIndustrialDomestic))
            
            # the (corrected) remaining total demand limited to self.potFossilGroundwaterAbstract
            # (units: m3)
            correctedRemainingTotalDemand = correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic
            
            # TODO: Do the water balance check: correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic <= self.potFossilGroundwaterAbstract
            # constrain the irrigation groundwater demand with groundwater source fraction
            # (units: m3)
            correctedRemainingIrrigationLivestock = pcr.min((1.0 - self.swAbstractionFractionDict['irrigation']) * remainingIrrigationLivestock,\
                                                             correctedRemainingIrrigationLivestock) 
            correctedRemainingIrrigationLivestock = pcr.max(0.0,\
                                                            pcr.min(correctedRemainingIrrigationLivestock,\
                                                                    pcr.max(0.0,\
                                                                            self.volTotalIrrigationLivestockDemand) * (1.0 - self.swAbstractionFractionDict['irrigation']) -\
                                                                            self.satisfiedIrrigationDemandFromNonFossilGroundwater))
            
            # ignore fossil groundwater abstraction in irrigation areas dominated by swAbstractionFractionDict['irrigation']
            # (units: m3)
            correctedRemainingIrrigationLivestock = \
                pcr.ifthenelse(\
                               self.swAbstractionFractionDict['irrigation'] >= self.swAbstractionFractionDict['threshold_to_minimize_fossil_groundwater_irrigation'],\
                               0.0,\
                               correctedRemainingIrrigationLivestock)
            
            # reduce the fossil irrigation and livestock demands with enough supply of non fossil groundwater (in order to minimize unrealistic areas of fossil groundwater abstraction)
            # - supply from the average recharge (baseflow) and non fossil groundwater allocation
            # (units: m3)
            nonFossilGroundwaterSupply = pcr.max(pcr.max(0.0, routing.avgBaseflow * vos.secondsPerDay()),\
                                                 groundwater.avgNonFossilAllocationShort * self.cellArea,\
                                                 groundwater.avgNonFossilAllocation * self.cellArea)
            
            # irrigation supply from the non fossil groundwater
            # (units: m3)
            nonFossilIrrigationGroundwaterSupply  = nonFossilGroundwaterSupply * vos.getValDivZero(remainingIrrigationLivestock, remainingTotalDemand)
            
            # the corrected/reduced irrigation and livestock demand
            # (units: m3)
            correctedRemainingIrrigationLivestock = pcr.max(0.0, correctedRemainingIrrigationLivestock - nonFossilIrrigationGroundwaterSupply)
            
            # the corrected remaining total demand
            # (units: m3)
            correctedRemainingTotalDemand = correctedRemainingIndustrialDomestic + correctedRemainingIrrigationLivestock
            ###############################################################################################################################

            # water demand that must be satisfied by fossil groundwater abstraction - note that this is the volume unit
            self.potVolFossilGroundwaterAbstract = pcr.min(self.potVolFossilGroundwaterAbstract, correctedRemainingTotalDemand)
            
            if groundwater.limitFossilGroundwaterAbstraction == False and self.limitAbstraction == False:
                
                # Note: If limitFossilGroundwaterAbstraction == False, 
                #       allocation of fossil groundwater abstraction is not needed.  
                msg  = 'Fossil groundwater abstractions are without limit for satisfying local demand. '
                msg  = 'Allocation for fossil groundwater abstraction is NOT needed/implemented. '
                msg += 'However, the fossil groundwater abstraction rate still consider the maximumDailyGroundwaterAbstraction.'
                logger.debug(msg)
                
                # fossil groundwater abstraction
                # (unit: m3) 
                self.fossilGroundwaterAbstrVol = self.potVolFossilGroundwaterAbstract
                self.fossilGroundwaterAbstrVol = \
                     pcr.min(self.fossilGroundwaterAbstrVol,\
                             pcr.max(0.0,\
                                     self.maximumDailyGroundwaterAbstraction * self.cellArea - volRenewGroundwaterAbstraction))
                
                # fossil groundwater allocation
                # (units: m3)
                self.fossilGroundwaterAllocVol = self.fossilGroundwaterAbstrVol
            
            if groundwater.limitFossilGroundwaterAbstraction and self.limitAbstraction == False:
                logger.debug('Fossil groundwater abstractions are allowed, but with limit.')
                
                # accesible fossil groundwater
                # (units: m)
                readAvlFossilGroundwater = pcr.ifthenelse(groundwater.productive_aquifer,\
                                                          groundwater.storGroundwaterFossil,\
                                                          0.0)
                
                # residence time (day-1) or safety factor (to avoid 'unrealistic' zero fossil groundwater)
                readAvlFossilGroundwater *= 0.10
                
                # considering maximum daily groundwater abstraction
                # (units: m)
                readAvlFossilGroundwater = pcr.min(readAvlFossilGroundwater,\
                                                   self.maximumDailyFossilGroundwaterAbstraction,\
                                                   pcr.max(0.0,\
                                                           self.maximumDailyGroundwaterAbstraction - volRenewGroundwaterAbstraction/self.cellArea))
                readAvlFossilGroundwater = pcr.max(pcr.cover(readAvlFossilGroundwater, 0.0), 0.0)                                           
                
                # accesible fossil groundwater in the volume
                # (units: m3)
                readAvlFossilGroundwaterVol = readAvlFossilGroundwater * self.cellArea
                
                # fossil groundwater abstraction and allocation
                # (units: m3)
                # TODO: considering aquifer productivity while doing the allocation.
                if self.using_allocationSegmentsForGroundwaterSource:
                    logger.debug('Allocation of fossil groundwater abstraction.')
                    volFossilGroundwaterAbstraction, volFossilGroundwaterAllocation, volZoneFossilGroundwaterAbstraction = \
                        self.waterAbstractionAndAllocation(
                             water_demand_volume       = self.potVolFossilGroundwaterAbstract,\
                             available_water_volume    = pcr.max(0.00, readAvlFossilGroundwaterVol),\
                             allocation_zones          = self.allocationSegmentsForGroundwaterSource,\
                             zone_area                 = self.allocationSegmentsForGroundwaterSourceAreas,\
                             high_volume_threshold     = None,\
                             debug_water_balance       = True,\
                             extra_info_for_water_balance_reporting = str(currTimeStep.fulldate),  
                             landmask                  = self.landmask,
                             ignore_small_values       = False,
                             prioritizing_local_source = self.prioritizeLocalSourceToMeetWaterDemand)
                else:
                    logger.debug('Fossil groundwater abstraction is only for satisfying local demand. NO Allocation for fossil groundwater abstraction.')
                    
                    volFossilGroundwaterAbstraction     = pcr.min(pcr.max(0.0, readAvlFossilGroundwaterVol), self.potVolFossilGroundwaterAbstract)
                    volFossilGroundwaterAllocation      = volFossilGroundwaterAbstraction
                    volZoneFossilGroundwaterAbstraction = volFossilGroundwaterAbstraction
        
        # ##################################################################################################################
        # - end of Abstraction and Allocation of FOSSIL GROUNDWATER
        
        # allocate the "nonrenewable groundwater Allocation" to each sector
        # (units: m3)
        self.allocated_demand_per_sector["nonrenewable_groundwater"] = \
             self.allocate_satisfied_demand_to_each_sector(\
                  totalVolWaterAllocation          = volFossilGroundwaterAllocation,\
                  sectoral_remaining_demand_volume = remaining_gross_sectoral_water_demands,\
                  total_remaining_demand_volume    = remainingTotalDemand)
        
        # allocate the "nonrenewable groundwater Abstraction" to each sector
        # (unit: m3)
        self.allocated_withdrawal_per_sector["nonrenewable_groundwater"] =\
             self.allocate_withdrawal_to_each_sector(\
                  totalVolCellWaterAbstraction = volFossilGroundwaterAbstraction,\
                  totalVolZoneAbstraction      = volZoneFossilGroundwaterAbstraction,\
                  cellAllocatedDemandPerSector = self.allocated_demand_per_sector["nonrenewable_groundwater"],\
                  allocation_zones             = self.allocationSegmentsForGroundwaterSource)
        
        # update remaining_gross_sectoral_water_demands after the nonrenewable groundwater allocation
        # (units: m3)
        for sector_name in remaining_gross_sectoral_water_demands.keys():
            remaining_gross_sectoral_water_demands[sector_name] = \
                pcr.max(0.0,\
                        remaining_gross_sectoral_water_demands[sector_name] - \
                        self.allocated_demand_per_sector["nonrenewable_groundwater"][sector_name])
        
        # make the total non-renewable groundwater Allocation and Abstraction variable available for other modules
        # (units: m)
        self.fossilGroundwaterAlloc = volFossilGroundwaterAllocation  / self.cellArea
        self.fossilGroundwaterAbstr = volFossilGroundwaterAbstraction / self.cellArea
    
    
    
    def partitioningGroundSurfaceAbstraction(self, routing_module):
        
        # partitioning abstraction sources: groundwater and surface water
        # de Graaf et al., 2014 principle: partitioning based on local average baseflow (m3/s) and upstream average discharge (m3/s) 
        # - estimates of fractions of groundwater and surface water abstractions 
        averageBaseflowInput = routing_module.avgBaseflow
        averageUpstreamInput = pcr.max(routing_module.avgDischarge, pcr.cover(pcr.upstream(routing_module.lddMap, routing_module.avgDischarge), 0.0))

        if self.using_allocationSegmentsForSurfaceWaterSource:
            averageBaseflowInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageBaseflowInput))
            averageUpstreamInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageUpstreamInput))
            
            averageBaseflowInput = pcr.cover(pcr.areaaverage(averageBaseflowInput, self.allocationSegmentsForSurfaceWaterSource), 0.0)
            averageUpstreamInput = pcr.cover(pcr.areamaximum(averageUpstreamInput, self.allocationSegmentsForSurfaceWaterSource), 0.0)
        
        else:
            logger.debug("Water demand can only be satisfied by local source.")
        
        swAbstractionFraction = vos.getValDivZero(\
                                                  averageUpstreamInput,\
                                                  averageUpstreamInput + averageBaseflowInput,\
                                                  vos.smallNumber)
        swAbstractionFraction = pcr.roundup(swAbstractionFraction*100.)/100.
        swAbstractionFraction = pcr.max(0.0, swAbstractionFraction)
        swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)

        if self.using_allocationSegmentsForSurfaceWaterSource:
            swAbstractionFraction = pcr.areamaximum(swAbstractionFraction, self.allocationSegmentsForSurfaceWaterSource)
        
        swAbstractionFraction = pcr.cover(swAbstractionFraction, 1.0)
        swAbstractionFraction = pcr.ifthen(self.landmask, swAbstractionFraction)
        
        # making a dictionary containing the surface water fraction for various purpose 
        swAbstractionFractionDict = {}
        
        # - the default estimate (based on de Graaf et al., 2014)
        swAbstractionFractionDict['estimate'] = swAbstractionFraction
        
        # - for irrigation and livestock purpose
        swAbstractionFractionDict['irrigation'] = swAbstractionFraction
        
        # - for industrial and domestic purpose
        swAbstractionFractionDict['max_for_non_irrigation'] = swAbstractionFraction
        
        # - a threshold fraction value to optimize/maximize surface water withdrawal for irrigation 
        #   Principle: Areas with swAbstractionFractionDict['irrigation'] above this threshold will prioritize surface water use for irrigation purpose.
        #              A zero threshold value will ignore this principle.    
        swAbstractionFractionDict['threshold_to_maximize_irrigation_surface_water'] = self.threshold_to_maximize_irrigation_surface_water
        
        # - a threshold fraction value to minimize fossil groundwater withdrawal, particularly to remove the unrealistic areas of fossil groundwater abstraction
        #   Principle: Areas with swAbstractionFractionDict['irrigation'] above this threshold will not extract fossil groundwater.
        swAbstractionFractionDict['threshold_to_minimize_fossil_groundwater_irrigation'] = self.threshold_to_minimize_fossil_groundwater_irrigation
        
        # the default value of surface water source fraction is None or not defined (in this case, this value will be the 'estimate' and limited with 'max_for_non_irrigation')
        swAbstractionFractionDict['non_irrigation'] = None

        # incorporating the pre-defined fraction of surface water sources (e.g. based on Siebert et al., 2014 and McDonald et al., 2014)  
        if self.swAbstractionFractionData is not None:
            logger.debug('Using/incorporating the predefined fractions of surface water source.')
            swAbstractionFractionDict['estimate']   = swAbstractionFraction
            swAbstractionFractionDict['irrigation'] = self.partitioningGroundSurfaceAbstractionForIrrigation(swAbstractionFraction,\
                                                                                                             self.swAbstractionFractionData,\
                                                                                                             self.swAbstractionFractionDataQuality)
            swAbstractionFractionDict['max_for_non_irrigation'] = self.maximumNonIrrigationSurfaceWaterAbstractionFractionData
            
            if self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData is not None:
                swAbstractionFractionDict['non_irrigation'] = pcr.cover(
                                                              self.predefinedNonIrrigationSurfaceWaterAbstractionFractionData, \
                                                              swAbstractionFractionDict['estimate'])
                swAbstractionFractionDict['non_irrigation'] = pcr.min(\
                                  swAbstractionFractionDict['non_irrigation'], \
                                  swAbstractionFractionDict['max_for_non_irrigation'])                                              
        else:
            logger.debug('NOT using/incorporating the predefined fractions of surface water source.')
        
        return swAbstractionFractionDict
    
    
    
    def partitioningGroundSurfaceAbstractionForIrrigation(self,\
                                                           swAbstractionFractionEstimate,\
                                                           swAbstractionFractionData,\
                                                           swAbstractionFractionDataQuality):
        
        # surface water source fraction based on Stefan Siebert's map: 
        factor = 0.5 # using this factor, the minimum value for the following 'data_weight_value' is 0.75 (for swAbstractionFractionDataQuality == 5) 
        data_weight_value = pcr.scalar(1.0) - \
                           (pcr.min(5., pcr.max(0.0, swAbstractionFractionDataQuality))/10.0)*factor
                            
        swAbstractionFractionForIrrigation = data_weight_value  * swAbstractionFractionData +\
                                      (1.0 - data_weight_value) * swAbstractionFractionEstimate
        
        swAbstractionFractionForIrrigation = pcr.cover(swAbstractionFractionForIrrigation, swAbstractionFractionEstimate)
        swAbstractionFractionForIrrigation = pcr.cover(swAbstractionFractionForIrrigation, 1.0)
        swAbstractionFractionForIrrigation = pcr.ifthen(self.landmask, swAbstractionFractionForIrrigation)
        
        return swAbstractionFractionForIrrigation                  
