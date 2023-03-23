#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import re
import types

import netCDF4 as nc
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
#from ncConverter import *

def surface_water_allocation_based_on_quality(availableSurfaceWater, sectoralSurfaceWaterDemand, waterQualityStates, waterQualityThresholds,
                                              surfaceWaterPriority, usingAllocSegments, allocSegments, cellArea, segmentArea, landmask,
                                              prioritizeLocalSourceToMeetWaterDemand, currTimeStep):
    '''
    Where:
    availableSurfaceWater: maximum value between 0 and routed flow in channel
    sectoralSurfaceWaterDemand: surface water demand estimations for every sector (irrigation, domestic, industrial, livestock)
    waterQualityStates: surface water quality constituents' concentrations from DynQual (water temperature, BOD, salinity/TDS, fecal coliforms)
    waterQualityThresholds: surface water quality concentration thresholds per constituent and sector
    '''
    
    # initial values
    # - list of water demand sectors
    waterDemandSectors = list(waterQualityThresholds.keys())   # i.e., irrigation, domestic, industrial, livestock
    
    # - list of water quality constituents
    waterQualityConstituents = list(waterQualityThresholds[waterDemandSectors[0]].keys())   # i.e., water temperature, BOD, salinity/TDS, fecal coliforms
    
    # - amount of water that is abstracted from the source: initializing dataset
    totalActualSurfaceWaterAbstract = 0.0
    
    # - remaining water demand and satisfied water demand: initializing dictionaries
    waterDemandRemaining = {}
    waterDemandSatisfied  = {}
    for sector in waterDemandSectors:
        waterDemandRemaining[sector] = sectoralSurfaceWaterDemand[sector]
        waterDemandSatisfied[sector] = 0.0
    
    # - replacing None values in waterQualityThresholds dictionary with unreachable threshold (1e20)
    for sector in waterDemandSectors:
        waterQualityThresholds[sector] = {k:v if v is not None else 1e20 for k,v in wq_threshold[sector].items()}
    
    # looping for every constituent
    for consti in wq_constituent:
        sectors = wd_sector.copy()
        
        # water quality concentrations
        water_quality_concetration_consti = wq_state[consti]
        
        # ordering sectors from more stringent to less stringent
        thresholds = wq_threshold[consti]
        thresholds = dict(sorted(thresholds.items(), key=lambda item: item[1], reverse=False))
        sectors_ordered = list(thresholds.keys())
        
        # looping for every sector
        for sector_order in sectors_ordered:
            
            # defining water quality thresholds
            threshold_consti_sector = wq_threshold[consti][sector_order]
            
            # defining actual water available depending on constituent threshold
            available_surface_water_consti_sector = pcr.ifthenelse((water_quality_concetration_consti < threshold_consti_sector) | (pcr.pcrnot(pcr.defined(water_quality_concetration_consti))), available_surface_water, 0.)
            
            # total remaining water demand
            total_water_demand = 0.0
            for sector in wd_sector:
                total_water_demand = total_water_demand + water_demand_remaining[sector]
            surface_water_demand = total_water_demand
            
            # water allocation scheme
            # [ TODO ] accomodate the option "surfaceWaterPriority"!!!!
            msg = "Allocating water that is above the threshold for " + consti + " for the sector " + sector_order
            logger.debug(msg)
            
            if usingAllocSegments:      # using zone/segment at which supply network is defined
                logger.debug("Allocation of surface water abstraction.")
                
                volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = \
                 vos.waterAbstractionAndAllocation(
                 water_demand_volume = surface_water_demand*cellArea,\
                 available_water_volume = available_surface_water_consti_sector,\
                 allocation_zones = allocSegments,\
                 zone_area = segmentArea,\
                 high_volume_treshold = None,\
                 debug_water_balance = True,\
                 extra_info_for_water_balance_reporting = str(currTimeStep.fulldate), 
                 landmask = landmask,
                 ignore_small_values = False,
                 prioritizing_local_source = prioritizeLocalSourceToMeetWaterDemand)
                
                actSurfaceWaterAbstract   = volActSurfaceWaterAbstract / cellArea
                allocSurfaceWaterAbstract = volAllocSurfaceWaterAbstract / cellArea
            
            else:
                logger.debug("Surface water abstraction is only to satisfy local demand (no surface water network).")
                actSurfaceWaterAbstract   = pcr.min(available_surface_water_volume/cellArea, surface_water_demand)    # unit: m
                allocSurfaceWaterAbstract = actSurfaceWaterAbstract                                                   # unit: m
            
            # - the amount of water that is abstracted from the source (e.g. river, reservoir pixels): outgoing water
            actSurfaceWaterAbstract   = pcr.ifthen(landmask, actSurfaceWaterAbstract)
            # - the amount of water that is given to pixels with demand (e.g. pixels with irrigation areas): incoming water
            allocSurfaceWaterAbstract = pcr.ifthen(landmask, allocSurfaceWaterAbstract)
            
            # tracking the total amount of water that is abstracted from the source
            totalActSurfaceWaterAbstract = totalActSurfaceWaterAbstract + actSurfaceWaterAbstract
            
            # calculating remaining water available
            available_surface_water = available_surface_water - actSurfaceWaterAbstract
            
            # looping for every sector to distribute allocSurfaceWaterAbstract
            for sector in sectors:
                current_water_withdrawal_sector = allocSurfaceWaterAbstract * vos.getValDivZero(water_demand_remaining[sector], total_water_demand)
                
                # - tracking the water demand: satisficed and remaining
                water_demand_remaining[sector] = water_demand_remaining[sector] - current_water_withdrawal_sector
                water_demand_satisfied[sector] = water_demand_satisfied[sector] + current_water_withdrawal_sector
            sectors.remove(sector_order)

    return totalActSurfaceWaterAbstract, water_demand_satisfied