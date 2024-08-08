#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pcraster as pcr
import virtualOS as vos
from ncConverter import *

import logging
logger = logging.getLogger(__name__)

class WaterUse(object):
    
    #................................................................................................................................................
    
    def __init__(self, nonIrrGrossDemandDict,
                       swAbstractionFractionDict,
                       groundwater,
                       routing,
                       allocSegments,
                       currTimeStep,
                       desalinationWaterUse,
                       groundwater_pumping_region_ids,
                       regionalAnnualGroundwaterAbstractionLimit,
                       
                       name,
                       landmask,
                       numberOfLayers,
                       includeIrrigation,
                       cropKC,
                       minTopWaterLayer,
                       topWaterLayer,
                       cropDeplFactor,
                       totalPotET,
                       readAvlWater,
                       totAvlWater,
                       potBareSoilEvap,
                       potTranspiration,
                       estimateTranspirationAndBareSoilEvap,
                       returnTotalEstimation,
                       returnTotalTranspirationOnly,
                       soilWaterStorage,
                       kSatUpp,
                       kSatUpp000005,
                       irrigationEfficiency,
                       netLqWaterToSoil,
                       fracVegCover,
                       usingAllocSegments,
                       segmentArea,
                       prioritizeLocalSourceToMeetWaterDemand,
                       surfaceWaterPiority,
                       limitAbstraction,
                       debugWaterBalance):
        
        object.__init__(self)
        
        self.nonIrrGrossDemandDict = nonIrrGrossDemandDict
        self.swAbstractionFractionDict = swAbstractionFractionDict
        self.groundwater = groundwater
        self.routing = routing
        self.allocSegments = allocSegments
        self.currTimeStep = currTimeStep
        self.desalinationWaterUse = desalinationWaterUse
        self.groundwater_pumping_region_ids = groundwater_pumping_region_ids
        self.regionalAnnualGroundwaterAbstractionLimit = regionalAnnualGroundwaterAbstractionLimit
        
        self.name = name
        self.landmask = landmask
        self.numberOfLayers = numberOfLayers
        self.includeIrrigation = includeIrrigation
        self.cropKC = cropKC
        self.minTopWaterLayer = minTopWaterLayer
        self.topWaterLayer = topWaterLayer
        self.cropDeplFactor = cropDeplFactor
        self.totalPotET = totalPotET
        self.readAvlWater = readAvlWater
        self.totAvlWater = totAvlWater
        self.potBareSoilEvap = potBareSoilEvap
        self.potTranspiration = potTranspiration
        self.estimateTranspirationAndBareSoilEvap = estimateTranspirationAndBareSoilEvap
        self.returnTotalEstimation = returnTotalEstimation
        self.returnTotalTranspirationOnly = returnTotalTranspirationOnly
        self.soilWaterStorage = soilWaterStorage
        self.kSatUpp = kSatUpp
        self.kSatUpp000005 = kSatUpp000005
        self.irrigationEfficiency = irrigationEfficiency
        self.netLqWaterToSoil = netLqWaterToSoil
        self.fracVegCover = fracVegCover
        self.usingAllocSegments = usingAllocSegments
        self.segmentArea = segmentArea
        self.prioritizeLocalSourceToMeetWaterDemand = prioritizeLocalSourceToMeetWaterDemand
        self.surfaceWaterPiority = surfaceWaterPiority
        self.limitAbstraction = limitAbstraction
        self.debugWaterBalance = debugWaterBalance
        
        self.calculateWaterDemand(nonIrrGrossDemandDict,
                                  swAbstractionFractionDict,
                                  groundwater,
                                  routing,
                                  allocSegments,
                                  currTimeStep,
                                  desalinationWaterUse,
                                  groundwater_pumping_region_ids,
                                  regionalAnnualGroundwaterAbstractionLimit)
    
    #................................................................................................................................................
    
    def calculateIrrigationDemand(self):
        '''
        irrigation water demand (unit: m/day) for paddy and non-paddy
        '''
        self.irrGrossDemand = pcr.scalar(0.)
        if (self.name == 'irrPaddy' or self.name == 'irr_paddy') and self.includeIrrigation:
            self.irrGrossDemand = \
                  pcr.ifthenelse(self.cropKC > 0.75, 
                                 pcr.max(0.0,
                                         self.minTopWaterLayer - (self.topWaterLayer )),
                                 0.0)
            # a function of: - cropKC (evaporation and transpiration),
            #                - topWaterLayer (water available in the irrigation field)
        
        if (self.name == 'irrNonPaddy' or self.name == 'irr_non_paddy' or self.name ==  "irr_non_paddy_crops") and self.includeIrrigation:
            adjDeplFactor = \
                     pcr.max(0.1,
                             pcr.min(0.8,
                                     (self.cropDeplFactor + 0.04*(5.-self.totalPotET*1000.))))
            # original formula based on Allen et al. (1998)
            # see: http://www.fao.org/docrep/x0490e/x0490e0e.htm#
            
            # alternative 1: irrigation demand (to fill the entire totAvlWater, maintaining the field capacity) - NOT USED
            #~ self.irrGrossDemand = \
                 #~ pcr.ifthenelse( self.cropKC > 0.20, \
                 #~ pcr.ifthenelse( self.readAvlWater < \
                                  #~ adjDeplFactor*self.totAvlWater, \
                #~ pcr.max(0.0,  self.totAvlWater-self.readAvlWater),0.),0.)  # a function of cropKC and totalPotET (evaporation and transpiration),
                                                                              #               readAvlWater (available water in the root zone)
            
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
            if self.numberOfLayers == 2: self.irrGrossDemand = pcr.min(self.irrGrossDemand, self.kSatUpp)
            if self.numberOfLayers == 3: self.irrGrossDemand = pcr.min(self.irrGrossDemand, self.kSatUpp000005)
        
        # irrigation efficiency, minimum demand for start irrigating and maximum value to cap excessive demand 
        if self.includeIrrigation:
            
            # irrigation efficiency                                                              # TODO: Improve the concept of irrigation efficiency
            self.irrigationEfficiencyUsed  = pcr.min(1.0, pcr.max(0.10, self.irrigationEfficiency))
            # demand, including its inefficiency
            self.irrGrossDemand = pcr.cover(self.irrGrossDemand / pcr.min(1.0, self.irrigationEfficiencyUsed), 0.0)
            
            # the following irrigation demand is not limited to available water
            self.irrGrossDemand = pcr.ifthen(self.landmask, self.irrGrossDemand)
            
            # reduce irrGrossDemand by netLqWaterToSoil
            self.irrGrossDemand = pcr.max(0.0, self.irrGrossDemand - self.netLqWaterToSoil)
            
            # minimum demand for start irrigating
            minimum_demand = 0.005   # unit: m/day                                               # TODO: set the minimum demand in the ini/configuration file.
            if self.name == 'irrPaddy' or self.name == 'irr_paddy':
                minimum_demand = pcr.min(self.minTopWaterLayer, 0.025)                           # TODO: set the minimum demand in the ini/configuration file.
            self.irrGrossDemand = pcr.ifthenelse(self.irrGrossDemand > minimum_demand, \
                                                 self.irrGrossDemand , 0.0)
            
            maximum_demand = 0.025  # unit: m/day                                                # TODO: set the maximum demand in the ini/configuration file.
            if self.name == 'irrPaddy' or\
               self.name == 'irr_paddy': maximum_demand = pcr.min(self.minTopWaterLayer, 0.025)  # TODO: set the minimum demand in the ini/configuration file.
            self.irrGrossDemand = pcr.min(maximum_demand, self.irrGrossDemand)
            
            # ignore small irrigation demand (less than 1 mm)
            self.irrGrossDemand = pcr.rounddown( self.irrGrossDemand *1000.)/1000.
            
            # irrigation demand is only calculated for areas with fracVegCover > 0                # DO WE NEED THIS ? 
            self.irrGrossDemand = pcr.ifthenelse(self.fracVegCover >  0.0, self.irrGrossDemand, 0.0)
        
        # total irrigation gross demand (m) per cover types (not limited by available water)
        self.totalPotentialMaximumIrrGrossDemandPaddy    = 0.0
        self.totalPotentialMaximumIrrGrossDemandNonPaddy = 0.0
        if self.name == 'irrPaddy' or self.name == 'irr_paddy':
            self.totalPotentialMaximumIrrGrossDemandPaddy = self.irrGrossDemand
        if self.name == 'irrNonPaddy' or self.name == 'irr_non_paddy' or self.name == 'irr_non_paddy_crops':
            self.totalPotentialMaximumIrrGrossDemandNonPaddy = self.irrGrossDemand

#..............................................................................................................................................................

    def calculateWaterDemand(self, nonIrrGrossDemandDict,
                                   swAbstractionFractionDict,
                                   groundwater,
                                   routing,
                                   allocSegments,
                                   currTimeStep,
                                   desalinationWaterUse,
                                   groundwater_pumping_region_ids,
                                   regionalAnnualGroundwaterAbstractionLimit):
        
        # irrigation demand
        self.calculateIrrigationDemand()
        
        # non irrigation demand is only calculated for areas with fracVegCover > 0                   # DO WE NEED THIS ?
        nonIrrGrossDemandDict['potential_demand']['domestic']  = pcr.ifthenelse(self.fracVegCover > 0.0, nonIrrGrossDemandDict['potential_demand']['domestic'] , 0.0) 
        nonIrrGrossDemandDict['potential_demand']['industry']  = pcr.ifthenelse(self.fracVegCover > 0.0, nonIrrGrossDemandDict['potential_demand']['industry'] , 0.0)
        nonIrrGrossDemandDict['potential_demand']['livestock'] = pcr.ifthenelse(self.fracVegCover > 0.0, nonIrrGrossDemandDict['potential_demand']['livestock'], 0.0)
        
        # non irrigation water demand, including the livestock (not limited by available water)
        self.nonIrrGrossDemand = nonIrrGrossDemandDict['potential_demand']['domestic'] +\
                                 nonIrrGrossDemandDict['potential_demand']['industry'] +\
                                 nonIrrGrossDemandDict['potential_demand']['livestock']
        
        # total irrigation and livestock demand (not limited by available water)
        totalIrrigationLivestockDemand = self.irrGrossDemand + nonIrrGrossDemandDict['potential_demand']['livestock']
        
        # totalGrossDemand (m): irrigation and non irrigation (not limited by available water) - these values will not be reduced
        self.totalPotentialMaximumGrossDemand       = self.irrGrossDemand + self.nonIrrGrossDemand
        # - irrigation (excluding livestock)
        self.totalPotentialMaximumIrrGrossDemand    = self.irrGrossDemand
        # - non irrigation (including livestock)
        self.totalPotentialMaximumNonIrrGrossDemand = self.nonIrrGrossDemand
        
        # the following value will be reduced by available/accesible water
        self.totalPotentialGrossDemand           = self.totalPotentialMaximumGrossDemand
        
        #...................................................................................................................
        # Abstraction and Allocation of DESALINATED WATER
        # - desalination water to satisfy water demand
        if self.usingAllocSegments: # using zone/segments at which networks are defined (as defined in the landSurface options)
        #  
            logger.debug("Allocation of supply from desalination water.")
        #  
            volDesalinationAbstraction, volDesalinationAllocation = \
              vos.waterAbstractionAndAllocation(
              water_demand_volume = self.totalPotentialGrossDemand*routing.cellArea,\
              available_water_volume = pcr.max(0.00, desalinationWaterUse*routing.cellArea),\
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
            self.desalinationAbstraction = pcr.min(desalinationWaterUse, self.totalPotentialGrossDemand)
            self.desalinationAllocation  = self.desalinationAbstraction
        #     
        self.desalinationAbstraction = pcr.ifthen(self.landmask, self.desalinationAbstraction)
        self.desalinationAllocation  = pcr.ifthen(self.landmask, self.desalinationAllocation)
        
        # water demand that have been satisfied (unit: m/day) - after desalination
        # - for irrigation (excluding livestock)
        satisfiedIrrigationDemand = vos.getValDivZero(self.irrGrossDemand, self.totalPotentialGrossDemand) * self.desalinationAllocation
        # - for domestic, industry and livestock
        satisfiedNonIrrDemand     = pcr.max(0.00, self.desalinationAllocation - satisfiedIrrigationDemand)
        # - for domestic
        satisfiedDomesticDemand   = satisfiedNonIrrDemand * vos.getValDivZero(nonIrrGrossDemandDict['potential_demand']['domestic'], 
                                                                              self.totalPotentialMaximumNonIrrGrossDemand)  
        # - for industry
        satisfiedIndustryDemand   = satisfiedNonIrrDemand * vos.getValDivZero(nonIrrGrossDemandDict['potential_demand']['industry'], 
                                                                              self.totalPotentialMaximumNonIrrGrossDemand)
        # - for livestock
        satisfiedLivestockDemand  = pcr.max(0.0, satisfiedNonIrrDemand - satisfiedDomesticDemand - satisfiedIndustryDemand)
    
        # total remaining gross demand (m/day) after desalination
        ################################################################################################################################
        self.totalGrossDemandAfterDesalination = pcr.max(0.0, self.totalPotentialGrossDemand - self.desalinationAllocation)
        # the remaining water demand per sector
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
        remainingIndustrialDomestic  = pcr.max(0.0, self.totalGrossDemandAfterDesalination - remainingIrrigationLivestock)                                              
    
        # Abstraction and Allocation of SURFACE WATER
        ##############################################################################################################################
        # calculate the estimate of surface water demand (considering by swAbstractionFractionDict)
        # - for industrial and domestic
        swAbstractionFraction_industrial_domestic = pcr.min(swAbstractionFractionDict['max_for_non_irrigation'],\
                                                            swAbstractionFractionDict['estimate'])
        if swAbstractionFractionDict['non_irrigation'] is not None:
            swAbstractionFraction_industrial_domestic = swAbstractionFractionDict['non_irrigation']
    
        surface_water_demand_estimate = swAbstractionFraction_industrial_domestic * remainingIndustrialDomestic
        # - for irrigation and livestock 
        surface_water_irrigation_demand_estimate = swAbstractionFractionDict['irrigation'] * remainingIrrigationLivestock
        # - surface water source as priority if groundwater irrigation fraction is relatively low  
        surface_water_irrigation_demand_estimate = \
           pcr.ifthenelse(swAbstractionFractionDict['irrigation'] >= swAbstractionFractionDict['treshold_to_maximize_irrigation_surface_water'],\
           remainingIrrigationLivestock, surface_water_irrigation_demand_estimate)
        # - update estimate of surface water demand withdrawal (unit: m/day)
        surface_water_demand_estimate += surface_water_irrigation_demand_estimate
        # - prioritize surface water use in non productive aquifers that have limited groundwater supply
        surface_water_demand_estimate = pcr.ifthenelse(groundwater.productive_aquifer, surface_water_demand_estimate,\
                                                       pcr.max(0.0, remainingIrrigationLivestock - \
                                                       pcr.min(groundwater.avgAllocationShort, groundwater.avgAllocation)))
        # - maximize/optimize surface water use in areas with the overestimation of groundwater supply 
        surface_water_demand_estimate += pcr.max(0.0, pcr.max(groundwater.avgAllocationShort, groundwater.avgAllocation) -\
               (1.0 - swAbstractionFractionDict['irrigation']) * totalIrrigationLivestockDemand -\
               (1.0 - swAbstractionFraction_industrial_domestic) * (self.totalPotentialMaximumGrossDemand - totalIrrigationLivestockDemand))
        #
        # total demand (unit: m/day) that should be allocated from surface water 
        # (corrected/limited by swAbstractionFractionDict and limited by the remaining demand)
        surface_water_demand_estimate         = pcr.min(self.totalGrossDemandAfterDesalination, surface_water_demand_estimate)
        correctedRemainingIrrigationLivestock = pcr.min(surface_water_demand_estimate, remainingIrrigationLivestock)
        correctedRemainingIndustrialDomestic  = pcr.min(remainingIndustrialDomestic,\
                                                pcr.max(0.0, surface_water_demand_estimate - remainingIrrigationLivestock))
        correctedSurfaceWaterDemandEstimate   = correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic
        surface_water_demand = correctedSurfaceWaterDemandEstimate
        #
        # if surface water abstraction as the first priority
        if self.surfaceWaterPiority: surface_water_demand = self.totalGrossDemandAfterDesalination
        #
        if self.usingAllocSegments:      # using zone/segment at which supply network is defined
        #  
            logger.debug("Allocation of surface water abstraction.")
        #  
            volActSurfaceWaterAbstract, volAllocSurfaceWaterAbstract = \
             vos.waterAbstractionAndAllocation(
             water_demand_volume = surface_water_demand*routing.cellArea,\
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
        # - for irrigation and livestock water demand 
        satisfiedIrrigationLivestockDemandFromSurfaceWater = self.allocSurfaceWaterAbstract * \
               vos.getValDivZero(correctedRemainingIrrigationLivestock, correctedSurfaceWaterDemandEstimate)
        # - for irrigation water demand, but not including livestock 
        satisfiedIrrigationDemandFromSurfaceWater = satisfiedIrrigationLivestockDemandFromSurfaceWater * \
               vos.getValDivZero(remainingIrrigation, remainingIrrigationLivestock)
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromSurfaceWater
        # - for non irrigation water demand: livestock, domestic and industry 
        satisfiedNonIrrDemandFromSurfaceWater = pcr.max(0.0, self.allocSurfaceWaterAbstract - satisfiedIrrigationDemandFromSurfaceWater)
        satisfiedNonIrrDemand += satisfiedNonIrrDemandFromSurfaceWater
        # - for livestock                                                                      
        satisfiedLivestockDemand += pcr.max(0.0, satisfiedIrrigationLivestockDemandFromSurfaceWater - \
                                                 satisfiedIrrigationDemandFromSurfaceWater)
        # - for industrial and domestic demand (excluding livestock)
        satisfiedIndustrialDomesticDemandFromSurfaceWater = pcr.max(0.0, self.allocSurfaceWaterAbstract -\
                                                                         satisfiedIrrigationLivestockDemandFromSurfaceWater)
        # - for domestic                                                                 
        satisfiedDomesticDemand += satisfiedIndustrialDomesticDemandFromSurfaceWater * vos.getValDivZero(remainingDomestic, \
                                                                                                         remainingIndustrialDomestic)
        # - for industry
        satisfiedIndustryDemand += satisfiedIndustrialDomesticDemandFromSurfaceWater * vos.getValDivZero(remainingIndustry, \
                                                                                                         remainingIndustrialDomestic)             
    
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
        remainingIndustrialDomestic  = remainingIndustry + remainingDomestic                                                     
        
    
        # Abstraction and Allocation of GROUNDWATER (fossil and non fossil)
        #########################################################################################################################
        # estimating groundwater water demand:
        # - demand for industrial and domestic sectors 
        #   (all remaining demand for these sectors should be satisfied)
        groundwater_demand_estimate = remainingIndustrialDomestic
        # - demand for irrigation and livestock sectors
        #   (only part of them will be satisfied, as they may be too high due to the uncertainty in the irrigation scheme)
        irrigationLivestockGroundwaterDemand = pcr.min(remainingIrrigationLivestock, \
                                               pcr.max(0.0, \
                                               (1.0 - swAbstractionFractionDict['irrigation'])*totalIrrigationLivestockDemand))
        groundwater_demand_estimate += irrigationLivestockGroundwaterDemand
    
        #####################################################################################################
        # water demand that must be satisfied by groundwater abstraction (not limited to available water)
        self.potGroundwaterAbstract = pcr.min(self.potGroundwaterAbstract, groundwater_demand_estimate)
        #####################################################################################################
        
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
    
            ################## NEW METHOD #################################################################################################################
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
            ################## end of NEW METHOD (but still under development) ##########################################################################################################
    
            #~ # Shall we will always try to fulfil the industrial and domestic demand?
            #~ self.potGroundwaterAbstract = pcr.max(remainingIndustrialDomestic, self.potGroundwaterAbstract)
    
        else:
            logger.debug('NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction.')
        
        # Abstraction and Allocation of NON-FOSSIL GROUNDWATER
        # #############################################################################################################################
        # available storGroundwater (non fossil groundwater) that can be accessed (unit: m)
        readAvlStorGroundwater = pcr.cover(pcr.max(0.00, groundwater.storGroundwater), 0.0)
        # - considering maximum daily groundwater abstraction
        readAvlStorGroundwater = pcr.min(readAvlStorGroundwater, groundwater.maximumDailyGroundwaterAbstraction)
        # - ignore groundwater storage in non-productive aquifer 
        readAvlStorGroundwater = pcr.ifthenelse(groundwater.productive_aquifer, readAvlStorGroundwater, 0.0)
        
        # for non-productive aquifer, reduce readAvlStorGroundwater to the current recharge/baseflow rate
        readAvlStorGroundwater = pcr.ifthenelse(groundwater.productive_aquifer, \
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
        # - for irrigation and livestock water demand 
        satisfiedIrrigationLivestockDemandFromNonFossilGroundwater = self.allocNonFossilGroundwater * \
               vos.getValDivZero(irrigationLivestockGroundwaterDemand, groundwater_demand_estimate)
        # - for irrigation water demand, but not including livestock 
        satisfiedIrrigationDemandFromNonFossilGroundwater = satisfiedIrrigationLivestockDemandFromNonFossilGroundwater * \
               vos.getValDivZero(remainingIrrigation, remainingIrrigationLivestock)
        satisfiedIrrigationDemand += satisfiedIrrigationDemandFromNonFossilGroundwater
         # - for non irrigation water demand: livestock, domestic and industry 
        satisfiedNonIrrDemandFromNonFossilGroundwater = pcr.max(0.0, self.allocNonFossilGroundwater - satisfiedIrrigationLivestockDemandFromNonFossilGroundwater)
        satisfiedNonIrrDemand += satisfiedNonIrrDemandFromNonFossilGroundwater
        # - for livestock                                                                      
        satisfiedLivestockDemand += pcr.max(0.0, satisfiedIrrigationLivestockDemandFromNonFossilGroundwater - \
                                                 satisfiedIrrigationDemandFromNonFossilGroundwater)
        # - for industrial and domestic demand (excluding livestock)
        satisfiedIndustrialDomesticDemandFromNonFossilGroundwater = pcr.max(0.0, self.allocNonFossilGroundwater -\
                                                                                 satisfiedIrrigationLivestockDemandFromNonFossilGroundwater)
        # - for domestic                                                                 
        satisfiedDomesticDemand += satisfiedIndustrialDomesticDemandFromNonFossilGroundwater * vos.getValDivZero(remainingDomestic, remainingIndustrialDomestic)
        # - for industry
        satisfiedIndustryDemand += satisfiedIndustrialDomesticDemandFromNonFossilGroundwater * vos.getValDivZero(remainingIndustry, remainingIndustrialDomestic)        
    
        ######################################################################################################################
        ######################################################################################################################
        # water demand that must be satisfied by fossil groundwater abstraction (unit: m, not limited to available water)
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
            remainingIndustrialDomestic  = remainingIndustry + remainingDomestic
            # - remaining total demand
            remainingTotalDemand = remainingIrrigationLivestock + remainingIndustrialDomestic                                                     
    
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
    
            #~ # Shall we will always try to fulfil the remaining industrial and domestic demand?
            #~ self.potFossilGroundwaterAbstract = pcr.max(remainingIndustrialDomestic, self.potFossilGroundwaterAbstract)
    
        if self.limitAbstraction == False:                              # TODO: For runs without any water use, we can exclude this. 
    
            ###############################################################################################################################
            # estimate the remaining total demand (unit: m/day) LIMITED to self.potFossilGroundwaterAbstract
            ###############################################################################################################################
    
            correctedRemainingTotalDemand = pcr.min(self.potFossilGroundwaterAbstract, remainingTotalDemand)
    
            # the remaining industrial and domestic demand and livestock (unit: m/day) limited to self.potFossilGroundwaterAbstract
            # - no correction, we will always try to fulfil these demands
            correctedRemainingIndustrialDomesticLivestock = pcr.min(remainingIndustrialDomestic + remainingLivestock, correctedRemainingTotalDemand)
            
            # the remaining irrigation demand limited to self.potFossilGroundwaterAbstract
            correctedRemainingIrrigation = pcr.min(remainingIrrigation, \
                                                    pcr.max(0.0, correctedRemainingTotalDemand - correctedRemainingIndustrialDomesticLivestock))
            # - ignore small irrigation demand (less than 1 mm)
            correctedRemainingIrrigation = pcr.rounddown(correctedRemainingIrrigation*1000.)/1000.
            
            # the (corrected) remaining total demand (limited to self.potFossilGroundwaterAbstract)
            correctedRemainingTotalDemand = correctedRemainingIndustrialDomesticLivestock + correctedRemainingIrrigation
            
            # the (corrected) remaining industrial and domestic demand (excluding livestock)
            correctedRemainingIndustrialDomestic = pcr.min(remainingIndustrialDomestic, correctedRemainingTotalDemand)
    
            # the remaining irrigation and livestock water demand limited to self.potFossilGroundwaterAbstract
            correctedRemainingIrrigationLivestock = pcr.min(remainingIrrigationLivestock, \
                                                    pcr.max(0.0, correctedRemainingTotalDemand - correctedRemainingIndustrialDomestic))
                                                  
            # the (corrected) remaining total demand (unit: m/day) limited to self.potFossilGroundwaterAbstract
            correctedRemainingTotalDemand = correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic
            
            # TODO: Do the water balance check: correctedRemainingIrrigationLivestock + correctedRemainingIndustrialDomestic <= self.potFossilGroundwaterAbstract                                          
    
            # constrain the irrigation groundwater demand with groundwater source fraction 
            correctedRemainingIrrigationLivestock = pcr.min((1.0 - swAbstractionFractionDict['irrigation']) * remainingIrrigationLivestock,\
                                                             correctedRemainingIrrigationLivestock) 
            correctedRemainingIrrigationLivestock = pcr.max(0.0,\
             pcr.min(correctedRemainingIrrigationLivestock,\
             pcr.max(0.0, totalIrrigationLivestockDemand) * (1.0 - swAbstractionFractionDict['irrigation']) - satisfiedIrrigationDemandFromNonFossilGroundwater))
            
            # ignore fossil groundwater abstraction in irrigation areas dominated by swAbstractionFractionDict['irrigation']
            correctedRemainingIrrigationLivestock = pcr.ifthenelse(\
                               swAbstractionFractionDict['irrigation'] >= swAbstractionFractionDict['treshold_to_minimize_fossil_groundwater_irrigation'], 0.0,\
                               correctedRemainingIrrigationLivestock)
    
            # reduce the fossil irrigation and livestock demands with enough supply of non fossil groundwater (in order to minimize unrealistic areas of fossil groundwater abstraction)
            # - supply from the average recharge (baseflow) and non fossil groundwater allocation 
            nonFossilGroundwaterSupply = pcr.max(pcr.max(0.0, routing.avgBaseflow) / routing.cellArea, \
                                                 groundwater.avgNonFossilAllocationShort, groundwater.avgNonFossilAllocation)  
            # - irrigation supply from the non fossil groundwater
            nonFossilIrrigationGroundwaterSupply  = nonFossilGroundwaterSupply * vos.getValDivZero(remainingIrrigationLivestock, remainingTotalDemand)
            # - the corrected/reduced irrigation and livestock demand
            correctedRemainingIrrigationLivestock = pcr.max(0.0, correctedRemainingIrrigationLivestock - nonFossilIrrigationGroundwaterSupply)
    
            # the corrected remaining total demand (unit: m/day) 
            correctedRemainingTotalDemand = correctedRemainingIndustrialDomestic + correctedRemainingIrrigationLivestock                                                                                                                                               
    
            ###############################################################################################################################
    
            # water demand that must be satisfied by fossil groundwater abstraction           
            self.potFossilGroundwaterAbstract = pcr.min(self.potFossilGroundwaterAbstract, correctedRemainingTotalDemand)
            
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
        
    
            # water demand that have been satisfied (m/day) - after desalination, surface water, non fossil groundwater & fossil groundwater
            ################################################################################################################################
            
            # from fossil groundwater, we should prioritize domestic and industrial water demand
            prioritizeFossilGroundwaterForDomesticIndutrial = False                            # TODO: Define this in the configuration file.
            
            if prioritizeFossilGroundwaterForDomesticIndutrial:
                
                # - first priority: for industrial and domestic demand (excluding livestock)
                satisfiedIndustrialDomesticDemandFromFossilGroundwater = pcr.min(self.fossilGroundwaterAlloc, \
                                                                                 remainingIndustrialDomestic)
                # - for domestic                                                                 
                satisfiedDomesticDemand += satisfiedIndustrialDomesticDemandFromFossilGroundwater * vos.getValDivZero(remainingDomestic, \
                                                                                                                 remainingIndustrialDomestic)
                # - for industry
                satisfiedIndustryDemand += satisfiedIndustrialDomesticDemandFromFossilGroundwater * vos.getValDivZero(remainingIndustry, \
                                                                                                                 remainingIndustrialDomestic)             
                # - for irrigation and livestock demand
                satisfiedIrrigationLivestockDemandFromFossilGroundwater = pcr.max(0.0, self.fossilGroundwaterAlloc - \
                                                                                       satisfiedIndustrialDomesticDemandFromFossilGroundwater)
                # - for irrigation
                satisfiedIrrigationDemand += satisfiedIrrigationLivestockDemandFromFossilGroundwater * vos.getValDivZero(remainingIrrigation, \
                                                                                                                remainingIrrigationLivestock)
                # - for livestock
                satisfiedLivestockDemand  += satisfiedIrrigationLivestockDemandFromFossilGroundwater * vos.getValDivZero(remainingLivestock, \
                                                                                                                remainingIrrigationLivestock)
            
            else:
            
                # Distribute fossil water proportionaly based on the amount of each sector
                
                # - for irrigation and livestock water demand 
                satisfiedIrrigationLivestockDemandFromFossilGroundwater = self.fossilGroundwaterAlloc * \
                       vos.getValDivZero(correctedRemainingIrrigationLivestock, correctedRemainingTotalDemand)
                # - for irrigation water demand, but not including livestock 
                satisfiedIrrigationDemandFromFossilGroundwater = satisfiedIrrigationLivestockDemandFromFossilGroundwater * \
                       vos.getValDivZero(remainingIrrigation, remainingIrrigationLivestock)
                satisfiedIrrigationDemand += satisfiedIrrigationDemandFromFossilGroundwater
                # - for non irrigation water demand: livestock, domestic and industry 
                satisfiedNonIrrDemandFromFossilGroundwater = pcr.max(0.0, self.fossilGroundwaterAlloc - satisfiedIrrigationDemandFromFossilGroundwater)
                satisfiedNonIrrDemand += satisfiedNonIrrDemandFromFossilGroundwater
                # - for livestock                                                                      
                satisfiedLivestockDemand += pcr.max(0.0, satisfiedIrrigationLivestockDemandFromFossilGroundwater - \
                                                         satisfiedIrrigationDemandFromFossilGroundwater)
                # - for industrial and domestic demand (excluding livestock)
                satisfiedIndustrialDomesticDemandFromFossilGroundwater = pcr.max(0.0, self.fossilGroundwaterAlloc - \
                                                                                      satisfiedIrrigationLivestockDemandFromFossilGroundwater)
                # - for domestic                                                                 
                satisfiedDomesticDemand += satisfiedIndustrialDomesticDemandFromFossilGroundwater * vos.getValDivZero(remainingDomestic, \
                                                                                                                 remainingIndustrialDomestic)
                # - for industry
                satisfiedIndustryDemand += satisfiedIndustrialDomesticDemandFromFossilGroundwater * vos.getValDivZero(remainingIndustry, \
                                                                                                                 remainingIndustrialDomestic)             
    
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
        # - ignore very small return flow (less than 0.1 mm)
        self.nonIrrReturnFlow = pcr.rounddown(self.nonIrrReturnFlow * 10000.)/10000.
        self.nonIrrReturnFlow = pcr.min(self.nonIrrReturnFlow, self.nonIrrGrossDemand)                        
    
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
