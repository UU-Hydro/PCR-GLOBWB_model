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
    waterDemandSectorsPriority = ['domestic','industrial','livestock','irrigation']
    
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
    
    # - replacing None values in waterQualityThresholds dictionary with unreachable threshold (1e100)
    for sector in waterDemandSectors:
        waterQualityThresholds[sector] = {k:v if v is not None else 1e100 for k,v in waterQualityThresholds[sector].items()}
    
    # looping for every sector
    for sectorPriority in waterDemandSectorsPriority:
        # sectoral surface water demend
        surfaceWaterDemand = sectoralSurfaceWaterDemand[sectorPriority]
        
        # water quality concentrations
        waterQualityConcentrationSWT = waterQualityStates['sw_temperature']
        waterQualityConcentrationBOD = waterQualityStates['bio_o2_demand']
        waterQualityConcentrationTDS = waterQualityStates['tot_dis_solid']
        waterQualityConcentrationFC  = waterQualityStates['fecal_coliform']
        
        # water quality thresholds
        waterQualityThresholdsSWT = waterQualityThresholds[sectorPriority]['sw_temperature']
        waterQualityThresholdsBOD = waterQualityThresholds[sectorPriority]['bio_o2_demand']
        waterQualityThresholdsTDS = waterQualityThresholds[sectorPriority]['tot_dis_solid']
        waterQualityThresholdsFC  = waterQualityThresholds[sectorPriority]['fecal_coliform']
        
        # actual water available depending on its quality (threshold)
        availableSurfaceWaterWithQuality = pcr.ifthenelse((waterQualityConcentrationSWT < waterQualityThresholdsSWT) &
                                                          (waterQualityConcentrationBOD < waterQualityThresholdsBOD) &
                                                          (waterQualityConcentrationTDS < waterQualityThresholdsTDS) &
                                                          (waterQualityConcentrationFC  < waterQualityThresholdsFC),
                                                          availableSurfaceWater, 0.0)
        
        # total remaining water demand
        #totalSurfaceWaterDemand = 0.0
        #for sector in waterDemandSectors:
        #    totalSurfaceWaterDemand = totalSurfaceWaterDemand + waterDemandRemaining[sector]
        
        # water allocation: water abtracted and allocated per pixel
        msg = "Allocating water that is above water quality thresholds for the sector " + sectorPriority
        logger.debug(msg)
        
        if usingAllocSegments:      # using zone/segment at which supply network is defined
            logger.debug("Allocation of surface water abstraction.")
            
            volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = \
             vos.waterAbstractionAndAllocation( \
                                               water_demand_volume = surfaceWaterDemand*cellArea,
                                               available_water_volume = availableSurfaceWaterWithQuality,
                                               allocation_zones = allocSegments,
                                               zone_area = segmentArea,
                                               high_volume_treshold = None,
                                               debug_water_balance = True,
                                               extra_info_for_water_balance_reporting = str(currTimeStep.fulldate),
                                               landmask = landmask,
                                               ignore_small_values = False,
                                               prioritizing_local_source = prioritizeLocalSourceToMeetWaterDemand)
            
            actSurfaceWaterAbstract   = volActSurfaceWaterAbstract / cellArea
            allocSurfaceWaterAbstract = volAllocSurfaceWaterAbstract / cellArea
        
        else:
            logger.debug("Surface water abstraction is only to satisfy local demand (no surface water network).")
            actSurfaceWaterAbstract   = pcr.min(availableSurfaceWaterWithQuality/cellArea, surfaceWaterDemand)    # unit: m
            allocSurfaceWaterAbstract = actSurfaceWaterAbstract                                                   # unit: m
        
        # masking values
        # - outgoing water: amount of water abstracted from the source (e.g. river, reservoir pixels)
        actSurfaceWaterAbstract   = pcr.ifthen(landmask, actSurfaceWaterAbstract)
        
        # - incoming water: amount of water allocated to pixels with demand (e.g. pixels with irrigation areas)
        allocSurfaceWaterAbstract = pcr.ifthen(landmask, allocSurfaceWaterAbstract)
        
        # water balance on the fly
        # - tracking the total amount of water that is abstracted from the source
        totalActualSurfaceWaterAbstract = totalActualSurfaceWaterAbstract + actSurfaceWaterAbstract
        
        # - calculating remaining water available
        availableSurfaceWater = availableSurfaceWater - actSurfaceWaterAbstract
        
        # - tracking the water demand: satisficed and remaining
        waterDemandRemaining[sectorPriority] = waterDemandRemaining[sectorPriority] - allocSurfaceWaterAbstract
        waterDemandSatisfied[sectorPriority] = waterDemandSatisfied[sectorPriority] + allocSurfaceWaterAbstract
    
    return totalActualSurfaceWaterAbstract, waterDemandSatisfied