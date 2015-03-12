#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os

from pcraster.framework import *
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
from ncConverter import *

class Groundwater(object):
    
    def getState(self):
        result = {}
        result['storGroundwater']                        = self.storGroundwater                # unit: m
        result['storGroundwaterFossil']                  = self.storGroundwaterFossil          # unit: m
        result['avgTotalGroundwaterAbstraction']         = self.avgAbstraction                 # unit: m
        result['avgNonFossilGroundwaterAllocationLong']  = self.avgNonFossilAllocation         # unit: m
        result['avgNonFossilGroundwaterAllocationShort'] = self.avgNonFossilAllocationShort    # unit: m
        return result

    def getPseudoState(self):
        result = {}
        
        return result

    def __init__(self, iniItems,landmask,spinUp):
        object.__init__(self)
        
        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask

        # option to activate water balance check
        self.debugWaterBalance = True
        if iniItems.routingOptions['debugWaterBalance'] == "False":
            self.debugWaterBalance = False

        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == str(None):
            # assign the recession coefficient parameter(s)
            self.recessionCoeff = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['recessionCoeff'],
               self.cloneMap,self.tmpDir,self.inputDir)
        else:       
            groundwaterPropertiesNC = vos.getFullPath(\
                                      iniItems.groundwaterOptions[\
                                         'groundwaterPropertiesNC'],
                                          self.inputDir)
            self.recessionCoeff = vos.netcdf2PCRobjCloneWithoutTime(\
                                  groundwaterPropertiesNC,'recessionCoeff',\
                                  cloneMapFileName = self.cloneMap)

        # groundwater recession coefficient (day-1_
        self.recessionCoeff = pcr.cover(self.recessionCoeff,0.00)       
        self.recessionCoeff = pcr.min(1.0000,self.recessionCoeff)       
        #
        if 'minRecessionCoeff' in iniItems.groundwaterOptions.keys():
            minRecessionCoeff = float(iniItems.groundwaterOptions['minRecessionCoeff'])
        else:
            minRecessionCoeff = 1.0e-4                                       # This is the minimum value used in Van Beek et al. (2011). 
        self.recessionCoeff = pcr.max(minRecessionCoeff,self.recessionCoeff)      
        
        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == str(None):
            # assign aquifer specific yield
            self.specificYield  = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['specificYield'],
               self.cloneMap,self.tmpDir,self.inputDir)
        else:       
            self.specificYield = vos.netcdf2PCRobjCloneWithoutTime(\
                                 groundwaterPropertiesNC,'specificYield',\
                                 cloneMapFileName = self.cloneMap)

        self.specificYield  = pcr.cover(self.specificYield,0.0)       
        self.specificYield  = pcr.max(0.010,self.specificYield)         # TODO: TO BE CHECKED: The resample process of specificYield     
        self.specificYield  = pcr.min(1.000,self.specificYield)       

        if iniItems.groundwaterOptions['groundwaterPropertiesNC'] == str(None):
            # assign aquifer saturated conductivity
            self.kSatAquifer = vos.readPCRmapClone(\
               iniItems.groundwaterOptions['kSatAquifer'],
               self.cloneMap,self.tmpDir,self.inputDir)
        else:       
            self.kSatAquifer = vos.netcdf2PCRobjCloneWithoutTime(\
                               groundwaterPropertiesNC,'kSatAquifer',\
                               cloneMapFileName = self.cloneMap)

        self.kSatAquifer = pcr.cover(self.kSatAquifer,0.0)       
        self.kSatAquifer = pcr.max(0.010,self.kSatAquifer)       

        # limitAbstraction options
        self.limitAbstraction = False
        if iniItems.landSurfaceOptions['limitAbstraction'] == "True": self.limitAbstraction = True
        

        # option for limitting regional groundwater abstractions
        self.limitRegionalAnnualGroundwaterAbstraction = False
        if iniItems.groundwaterOptions['pumpingCapacityNC'] != "None":

            logger.info('Limit for annual regional groundwater abstraction is used.')
            self.limitRegionalAnnualGroundwaterAbstraction = True
            
            self.pumpingCapacityNC = vos.getFullPath(\
                                     iniItems.groundwaterOptions['pumpingCapacityNC'],self.inputDir,False)
 
            #~ # old method (using pcraster file)
            #~ region_ids = vos.readPCRmapClone(\
                         #~ iniItems.groundwaterOptions['regionIds'],\
                         #~ self.cloneMap,self.tmpDir,self.inputDir)
            #~ self.region_ids = pcr.ifthen(self.landmask, pcr.nominal(region_ids))
            #~ 
            #~ self.regionalAnnualGroundwaterAbstractionLimit = vos.readPCRmapClone(\
                                                                 #~ iniItems.groundwaterOptions['pumpingCapacity'],
                                                                 #~ self.cloneMap,self.tmpDir,self.inputDir)
            #~ self.regionalAnnualGroundwaterAbstractionLimit = pcr.roundup(self.regionalAnnualGroundwaterAbstractionLimit*1000000.)/1000000.
            #~ self.regionalAnnualGroundwaterAbstractionLimit = pcr.areamaximum(self.regionalAnnualGroundwaterAbstractionLimit, self.region_ids)
            #~ 
            #~ self.regionalAnnualGroundwaterAbstractionLimit *= 1000. * 1000. * 1000. # unit: m3/year
            #~ self.regionalAnnualGroundwaterAbstractionLimit  = pcr.ifthen(self.landmask,\
                                                                         #~ self.regionalAnnualGroundwaterAbstractionLimit)
        else:
            logger.warning('NO LIMIT for regional groundwater (annual) pumping. It may result too high groundwater abstraction.')
        
        # option for limitting fossil groundwater abstractions - This option is defined for IWMI project 
        self.limitFossilGroundwaterAbstraction = False
        #
        # estimate of fossil groundwater capacity (needed only for IWMI project)
        if "extraOptionsforProjectWithIWMI" in iniItems.allSections: 
            #
            # estimate of thickness (unit: mm) of aceesible groundwater: shallow and deep 
            totalGroundwaterThickness = vos.readPCRmapClone(\
                                        iniItems.extraOptionsforProjectWithIWMI['estimateOfTotalGroundwaterThickness'],
                                        self.cloneMap,self.tmpDir,self.inputDir)
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 1.0))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 1.5))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 2.5))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 5.0))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.windowaverage(totalGroundwaterThickness, 7.5))
            totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                        pcr.mapmaximum(totalGroundwaterThickness))
            #
            # set minimum thickness to 100 m:
            totalGroundwaterThickness = pcr.max(100.0, totalGroundwaterThickness)
            #            
            # estimate of capacity (unit: m) of renewable groundwater (shallow)
            storGroundwaterCap =  pcr.cover(
                                  vos.readPCRmapClone(\
                                  iniItems.extraOptionsforProjectWithIWMI['estimateOfRenewableGroundwaterCapacity'],
                                  self.cloneMap,self.tmpDir,self.inputDir), 0.0)
            #
            # fossil groundwater capacity (unit: m)
            self.fossilWaterCap = pcr.max(0.0,\
                                  totalGroundwaterThickness*self.specificYield - storGroundwaterCap)
            
        if self.limitAbstraction == False and "extraOptionsforProjectWithIWMI" in iniItems.allSections:
            if iniItems.extraOptionsforProjectWithIWMI['limitFossilGroundWaterAbstraction'] == "True":
                logger.info('Fossil groundwater abstraction limit is used (IWMI project).')
                self.limitFossilGroundwaterAbstraction = True

        # zones at which water allocation (surface and groundwater allocation) is determined
        self.usingAllocSegments = False
        if iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater']  != "None": self.usingAllocSegments = True
        
        # incorporating groundwater distribution network:
        if self.usingAllocSegments and self.limitAbstraction == False:

            self.allocSegments = vos.readPCRmapClone(\
             iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater'],
             self.cloneMap,self.tmpDir,self.inputDir,isLddMap=False,cover=None,isNomMap=True)
            self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)

            cellArea = vos.readPCRmapClone(\
              iniItems.routingOptions['cellAreaMap'],
              self.cloneMap,self.tmpDir,self.inputDir)
            cellArea = pcr.ifthen(self.landmask, cellArea)              # TODO: integrate this one with the one coming from the routing module

            self.segmentArea = pcr.areatotal(pcr.cover(cellArea, 0.0), self.allocSegments)
            self.segmentArea = pcr.ifthen(self.landmask, self.segmentArea)
        
        # get initial conditions
        self.getICs(iniItems,spinUp)

        # initiate old style reporting                                  # TODO: remove this!
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

    def getICs(self,iniItems,iniConditions = None):

        # initial condition for storGroundwater (unit: m)
        if iniConditions == None: # when the model just start 
            self.storGroundwater = vos.readPCRmapClone(\
                                         iniItems.groundwaterOptions['storGroundwaterIni'],
                                         self.cloneMap,self.tmpDir,self.inputDir)
            self.avgAbstraction  = vos.readPCRmapClone(\
                                         iniItems.groundwaterOptions['avgTotalGroundwaterAbstractionIni'],
                                         self.cloneMap,self.tmpDir,self.inputDir)
            self.avgNonFossilAllocation   = vos.readPCRmapClone(\
                                         iniItems.groundwaterOptions['avgNonFossilGroundwaterAllocationLongIni'],
                                         self.cloneMap,self.tmpDir,self.inputDir)
            self.avgNonFossilAllocationShort = \
                                   vos.readPCRmapClone(\
                                         iniItems.groundwaterOptions['avgNonFossilGroundwaterAllocationShortIni'],
                                         self.cloneMap,self.tmpDir,self.inputDir)
        else:                     # during/after spinUp
            self.storGroundwater    = iniConditions['groundwater'][ 'storGroundwater']
            self.avgAbstraction     = iniConditions['groundwater'][ 'avgTotalGroundwaterAbstraction']      
            self.avgNonFossilAllocation      = iniConditions['groundwater'][ 'avgNonFossilGroundwaterAllocationLong']      
            self.avgNonFossilAllocationShort = iniConditions['groundwater'][ 'avgNonFossilGroundwaterAllocationShort']      

        # initial condition for storGroundwaterFossil (unit: m)
        #
        # Note that storGroundwaterFossil should not be depleted during the spin-up. 
        #
        if iniItems.groundwaterOptions['storGroundwaterFossilIni'] == "Maximum":
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
           self.limitFossilGroundwaterAbstraction:
            logger.info("The pre-defined initial condition for fossil groundwater is limited by fossilWaterCap (full capacity).")
            self.storGroundwaterFossil = pcr.min(self.storGroundwaterFossil, self.fossilWaterCap)
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)                                 

        # make sure that active storGroundwater, avgAbstraction and avgNonFossilAllocation cannot be negative
        #
        self.storGroundwater = pcr.cover( self.storGroundwater,0.0)
        self.storGroundwater = pcr.max(0.,self.storGroundwater)                                    
        self.storGroundwater = pcr.ifthen(self.landmask,\
                                          self.storGroundwater)
        #
        self.avgAbstraction  = pcr.cover( self.avgAbstraction,0.0)
        self.avgAbstraction  = pcr.max(0.,self.avgAbstraction)                                    
        self.avgAbstraction  = pcr.ifthen(self.landmask,\
                                          self.avgAbstraction)
        #
        self.avgNonFossilAllocation   = pcr.cover( self.avgNonFossilAllocation,0.0)
        self.avgNonFossilAllocation   = pcr.max(0.,self.avgNonFossilAllocation)                                    
        self.avgNonFossilAllocation   = pcr.ifthen(self.landmask,\
                                          self.avgNonFossilAllocation)
        #
        self.avgNonFossilAllocationShort = pcr.cover( self.avgNonFossilAllocationShort,0.0)
        self.avgNonFossilAllocationShort = pcr.max(0.,self.avgNonFossilAllocationShort)                                    
        self.avgNonFossilAllocationShort = pcr.ifthen(self.landmask,\
                                             self.avgNonFossilAllocationShort)


        # storGroundwaterFossil can be negative (particularly if limitFossilGroundwaterAbstraction == False)
        self.storGroundwaterFossil = pcr.ifthen(self.landmask,\
                                                self.storGroundwaterFossil)
        
    def perturb(self, name, **parameters):
        
        if name == "groundwater":
        
            # factor for perturbing the initial storGroundwater
            self.storGroundwater = self.storGroundwater * (mapnormal()*parameters['standard_deviation']+1)
            self.storGroundwater = pcr.max(0.,self.storGroundwater)

        else:
            print("Error: only groundwater may be updated at this time")
            return -1

    def update(self,landSurface,routing,currTimeStep):

        logger.info("Updating groundwater")
        
        if self.debugWaterBalance:
            preStorGroundwater       = self.storGroundwater
            preStorGroundwaterFossil = self.storGroundwaterFossil
                
        # get riverbed infiltration from the previous time step (from routing)
        self.surfaceWaterInf  = routing.riverbedExchange/routing.cellArea     # m
        self.storGroundwater += self.surfaceWaterInf

        # get net recharge (percolation-capRise) and update storage:
        self.storGroundwater  = pcr.max(0.,\
                                self.storGroundwater + landSurface.gwRecharge)         
                        
        # potential groundwater demand (unit: m)
        potGroundwaterDemand = pcr.max(0.0,\
                               landSurface.totalPotentialGrossDemand-\
                               landSurface.desalinationAllocation   -\
                               landSurface.allocSurfaceWaterAbstract )

        if self.usingAllocSegments == False or self.limitAbstraction:   
             
            # Note: For simplicity, limitAbstraction can only be combined with local (groundwater) source assumption
        
            logger.debug("Groundwater abstraction is only to satisfy local demand. No network for distributing groundwater.")

            # nonFossil groundwater abstraction (unit: m) to fulfill water demand 
            # - assumption: Groundwater is only abstracted to satisfy local demand.
            self.nonFossilGroundwaterAbs = \
                                           pcr.max(0.0,
                                           pcr.min(self.storGroundwater,\
                                           potGroundwaterDemand)) 
            #
            self.allocNonFossilGroundwater = self.nonFossilGroundwaterAbs
        
        if self.usingAllocSegments and self.limitAbstraction == False:

            # Note: Incorporating distribution network of groundwater source is possible only if limitAbstraction = False.  

            logger.debug("Allocation of non fossil groundwater abstraction.")

            volActNonFossilGroundwaterAbstract, volActNonFossilGroundwaterAllocation = \
             vos.waterAbstractionAndAllocation(
             water_demand_volume = potGroundwaterDemand*routing.cellArea,\
             available_water_volume = pcr.max(0.00, self.storGroundwater*routing.cellArea),\
             allocation_zones = self.allocSegments,\
             zone_area = self.segmentArea,\
             high_volume_treshold = 1000000.,\
             debug_water_balance = True,\
             extra_info_for_water_balance_reporting = str(currTimeStep.fulldate))
            
            # non fossil groundwater abstraction volume (unit: m)
            self.nonFossilGroundwaterAbs    = pcr.ifthen(self.landmask, volActNonFossilGroundwaterAbstract) /\
                                                                        routing.cellArea                       # unit: m

            # allocation non fossil groundwater (unit: m)
            self.allocNonFossilGroundwater  = pcr.ifthen(self.landmask, volActNonFossilGroundwaterAllocation)/\
                                                                        routing.cellArea                        # unit: m

        # update storGoundwater after self.nonFossilGroundwaterAbs
        self.storGroundwater = pcr.max(0.,self.storGroundwater - self.nonFossilGroundwaterAbs)

        # unmetDemand (m), this will be satisfied by fossil groundwater abstraction
        self.unmetDemand = pcr.scalar(0.0)
        if self.limitAbstraction: 
            logger.info("No fossil groundwater abstraction is allowed")
        else: 
            self.unmetDemand = potGroundwaterDemand - \
                               self.allocNonFossilGroundwater           # Note that this is equal to zero if limitAbstraction = True

        # correcting unmetDemand with available fossil groundwater
        # - For simplicity, limitFossilGroundwaterAbstraction can only be combined with local source assumption
        if self.limitFossilGroundwaterAbstraction and self.usingAllocSegments:
            self.unmetDemand = pcr.min(pcr.max(0.0, self.storGroundwaterFossil), self.unmetDemand)

        # update storGroundwaterFossil after unmetDemand 
        self.storGroundwaterFossil -= self.unmetDemand

        # fossil groundwater cannot be negative if limitFossilGroundwaterAbstraction is used
        # - For simplicity, limitFossilGroundwaterAbstraction can only be combined with local source assumption
        if self.limitFossilGroundwaterAbstraction and self.usingAllocSegments:
            self.storGroundwaterFossil = pcr.max(0.0, self.storGroundwaterFossil)

        # calculate the average total groundwater abstraction (m/day) from the last 365 days:
        totalAbstraction    = self.unmetDemand + self.nonFossilGroundwaterAbs
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

        # calculate baseflow and update storage:
        self.baseflow         = pcr.max(0.,\
                                pcr.min(self.storGroundwater,\
                                        self.recessionCoeff* \
                                        self.storGroundwater))
        self.storGroundwater  = pcr.max(0.,\
                                self.storGroundwater - self.baseflow)
        # PS: baseflow must be calculated at the end (to ensure the availability of storGroundwater to support nonFossilGroundwaterAbs)


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
                                  [self.unmetDemand],\
                                  [  preStorGroundwaterFossil],\
                                  [self.storGroundwaterFossil],\
                                       'storGroundwaterFossil',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-3)

        if self.debugWaterBalance and self.limitFossilGroundwaterAbstraction:
            vos.waterBalanceCheck([pcr.scalar(0.0)],\
                                  [self.unmetDemand],\
                                  [pcr.max(0.0,  preStorGroundwaterFossil)],\
                                  [pcr.max(0.0,self.storGroundwaterFossil)],\
                                       'storGroundwaterFossil (with limitFossilGroundwaterAbstraction)',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-3)

        if self.debugWaterBalance and landSurface.limitAbstraction:
            vos.waterBalanceCheck([potGroundwaterAbstract],\
                                  [self.nonFossilGroundwaterAbs],\
                                  [pcr.scalar(0.)],\
                                  [pcr.scalar(0.)],\
                                  'non fossil groundwater abstraction',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)

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

        if self.debugWaterBalance:
            vos.waterBalanceCheck([self.unmetDemand, \
                                   self.allocNonFossilGroundwater, \
                                   landSurface.allocSurfaceWaterAbstract],\
                                  [landSurface.totalGrossDemandAfterDesalination],\
                                  [pcr.scalar(0.)],\
                                  [pcr.scalar(0.)],\
                                  'demand allocation (surface water, groundwater & unmetDemand. Error here may be due to rounding error.',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-3)

        # old-style reporting                             
        self.old_style_groundwater_reporting(currTimeStep)              # TODO: remove this one

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

