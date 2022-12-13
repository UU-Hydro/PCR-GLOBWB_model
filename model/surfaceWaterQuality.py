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
from ncConverter import *


def surface_water_allocation_based_on_quality(available_surface_water_without_qual, wq_constituent, wd_sector, sectoral_surface_water_demand, wq_state, wq_threshold,
                                              surfaceWaterPiority, usingAllocSegments, cellArea, segmentArea, landmask, prioritizeLocalSourceToMeetWaterDemand, currTimeStep):
    
    # CONTINUE FROM HERE
    
    # initial values
    # - available surface water before allocation 
    available_surface_water_with_qual = available_surface_water_without_qual
    # - amount of water that is abstracted from the source
    totalActSurfaceWaterAbstract = 0.0
    # - remaining water demand and satisfied water demand
    water_demand_remaining = {}
    water_demand_satisfied  = {}
    for sector in wd_sector:
        water_demand_remaining[sector] = sectoral_surface_water_demand[sector]
        water_demand_satisfied[sector] = 0.0
        
    # looping for every constituent
    for consti in wq_constituent:
        
        # water quality concentrations
        water_quality_concetration_consti = wq_state[consti]
                
        # ordering sectors from less to more stringent
        thresholds = wq_threshold[consti]
        thresholds = {k: v for k, v in thresholds.items() if v is not None}
        thresholds = sorted(thresholds.items(), key=lambda item: item[1], reverse=True)
        sector_order = [threshold[0] for threshold in thresholds]
        
        # looping for every sector
        for sector in sector_order:
            
            # defining water quality thresholds
            threshold_consti_sector = wq_threshold[consti][sector]
            
            # defining actual water available depending on constituent threshold
            available_surface_water_with_qual_conti_sector = pcr.ifthenelse(water_quality_concetration_consti < threshold_consti_sector, available_surface_water_with_qual, 0.)
            
            # total remaining water demand
            total_water_demand = 0.0
            for sector in wd_sector: total_water_demand = total_water_demand + water_demand_remaining[sector]
            
            # if surface water abstraction as the first priority
            if surfaceWaterPiority: surface_water_demand = total_water_demand
            #
            available_surface_water_volume = pcr.max(0.00, available_surface_water_with_qual)
            
            if usingAllocSegments:      # using zone/segment at which supply network is defined
            #  
                logger.debug("Allocation of surface water abstraction.")
            #  
                volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = \
                 vos.waterAbstractionAndAllocation(
                 water_demand_volume = surface_water_demand*cellArea,\
                 available_water_volume = available_surface_water_volume,\
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
            #  
            else: 
                logger.debug("Surface water abstraction is only to satisfy local demand (no surface water network).")
                actSurfaceWaterAbstract   = pcr.min(available_surface_water_volume/cellArea,\
                                                         surface_water_demand)                            # unit: m
                allocSurfaceWaterAbstract = actSurfaceWaterAbstract                             # unit: m   
            #  
            
            # - the amount of water that is abstracted from the source (e.g. river, reservoir pixels)
            actSurfaceWaterAbstract   = pcr.ifthen(landmask, actSurfaceWaterAbstract)
            # - the amount of water that is given to pixels with demand (e.g. pixels with irrigation areas)
            allocSurfaceWaterAbstract = pcr.ifthen(landmask, allocSurfaceWaterAbstract)
            
            # tracking the total amount of water that is abstracted from the source
            totalActSurfaceWaterAbstract = totalActSurfaceWaterAbstract + actSurfaceWaterAbstract
            
            
            # calculating remaining water available
            available_surface_water_with_qual = available_surface_water_with_qual - actSurfaceWaterAbstract
            
            # looping for every sector to distribute allocSurfaceWaterAbstract
            for sector in wd_sector:
                current_water_withdrawal       = allocSurfaceWaterAbstract * vos.getValDivZero(water_demand_remaining[sector], total_water_demand)
                # - tracking the water demand: satisficed and remaining
                water_demand_remaining[sector] = water_demand_remaining[sector] - current_water_withdrawal
                water_demand_satisfied[sector] = water_demand_satisfied[sector] + current_water_withdrawal

    return totalActSurfaceWaterAbstract, water_demand_satisfied
    
    
    
    

