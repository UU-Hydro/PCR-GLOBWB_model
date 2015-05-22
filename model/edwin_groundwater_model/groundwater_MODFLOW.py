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

class GroundwaterModflow(object):
    
    def getState(self):
        result = {}
        result['groundwaterHead'] = self.groundwaterHead       # unit: m
        return result


    def estimate_bottom_elevation_of_bank_storage(self):

        # influence zone depth (m)
        influence_zone_depth = 5.0
        
        # bottom_elevation > flood_plain elevation - influence zone
        self.bottom_elevation_of_bank_storage = self.dem_floodplain - 5.0
        
        # - smooth bottom_elevation
        # - upstream areas in the mountainous regions and above perrenial stream starting points may also be drained (otherwise water will accumulate) 
        # - bottom_elevation > minimum elevation that is estimated from the maximum of S3 from the PCR-GLOBWB simulation

    def __init__(self, iniItems, landmask):
        object.__init__(self)
        
        # cloneMap, temporary directory, absolute path for input directory, landmask
        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # configuration from the ini file
        self.iniItems = iniItems
                
        # topography properties: read several variables from the netcdf file
        for var in ['dem_minimum','dem_maximum','dem_average','dem_standard_deviation',\
                    'slopeLength','orographyBeta','tanslope',\
                    'dzRel0000','dzRel0001','dzRel0005',\
                    'dzRel0010','dzRel0020','dzRel0030','dzRel0040','dzRel0050',\
                    'dzRel0060','dzRel0070','dzRel0080','dzRel0090','dzRel0100']:
            vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['topographyNC'], \
                                                                var, self.cloneMap)
            vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
            vars(self)[var] = pcr.ifthen(self.landmask, vars(self)[var])

        # channel properties: read several variables from the netcdf file
        for var in ['lddMap','cellAreaMap','gradient','bankfull_width',
                    'bankfull_depth','dem_floodplain','dem_riverbed']:
            vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['channelNC'], \
                                                                var, self.cloneMap)
            vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
            vars(self)[var] = pcr.ifthen(self.landmask, vars(self)[var])
        
        # correcting lddMap
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        
        # groundwater linear recession coefficient (day-1) ; the linear reservoir concept is still being used to represent fast response flow  
        #                                                                                                                  particularly from karstic aquifer in mountainous regions                    
         self.recessionCoeff = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['groundwaterPropertiesNC'],\
                                  groundwaterPropertiesNC,'recessionCoeff',\
                                  cloneMapFileName = self.cloneMap)
        #
        self.recessionCoeff = pcr.cover(self.recessionCoeff,0.00)       
        self.recessionCoeff = pcr.min(1.0000,self.recessionCoeff)       
        #
        if 'minRecessionCoeff' in iniItems.groundwaterOptions.keys():
            minRecessionCoeff = float(iniItems.groundwaterOptions['minRecessionCoeff'])
        else:
            minRecessionCoeff = 1.0e-4                                       # This is the minimum value used in Van Beek et al. (2011). 
        self.recessionCoeff = pcr.max(minRecessionCoeff,self.recessionCoeff)      
        
        # aquifer specific yield (
        self.specificYield = vos.netcdf2PCRobjCloneWithoutTime(groundwaterPropertiesNC,'specificYield',\
                                 cloneMapFileName = self.cloneMap)
        # 
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
        # 
        self.kSatAquifer = pcr.cover(self.kSatAquifer,0.0)       
        self.kSatAquifer = pcr.max(0.010,self.kSatAquifer)       

        # estimate of thickness (unit: m) of accesible groundwater 
        totalGroundwaterThickness = vos.readPCRmapClone(\
                                    iniItems.groundwaterOptions['estimateOfTotalGroundwaterThickness'],
                                    self.cloneMap,self.tmpDir,self.inputDir)
        # extrapolation 
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                    pcr.windowaverage(totalGroundwaterThickness, 1.0))
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                    pcr.windowaverage(totalGroundwaterThickness, 1.5))
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                    pcr.windowaverage(totalGroundwaterThickness, 2.5))
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,
                                    pcr.windowaverage(totalGroundwaterThickness, 5.0))
        #
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness, 0.0)
        #
        # set minimum thickness
        minimumThickness = pcr.scalar(float(\
                           iniItems.groundwaterOptions['minimumTotalGroundwaterThickness']))
        totalGroundwaterThickness = pcr.max(minimumThickness, totalGroundwaterThickness)

        # if using MODFLOW, the concept of fossil groundwater abstraction is abandoned 
        if self.useMODFLOW: self.limitFossilGroundwaterAbstraction = False
        
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

        self.initialize_states(iniItems,iniConditions)
        if self.useMODFLOW: self.initialize_with_MODFLOW(iniItems,iniConditions) 

    def initialize_with_MODFLOW(self,iniItems,iniConditions):

        # obtain relative groundwater head (unit: m) and 
        self.relativeGroundwaterHead = \
                        pcr.ifthen(self.landmask,\
                        vos.readPCRmapClone(iniItems.couplingToModflowOptions['relativeGroundwaterHeadFromModflow'],
                                            self.cloneMap,self.tmpDir,self.inputDir))
        self.baseflow = pcr.ifthen(self.landmask,\
                        vos.readPCRmapClone(iniItems.couplingToModflowOptions['baseflowFromModflow'],                                                   
                                            self.cloneMap,self.tmpDir,self.inputDir))
        
        # use storGroundwater from the MODFLOW calculation/simulation:
        self.storGroundwater = pcr.ifthen(self.landmask,\
                               vos.readPCRmapClone(iniItems.couplingToModflowOptions['storGroundwaterFromModflow'],  
                                                   self.cloneMap,self.tmpDir,self.inputDir))
        
        # additional states from MODFLOW can be added here !!!

    def initialize_states(self,iniItems,iniConditions):
 
        # initial condition for storGroundwater (unit: m)
        if iniConditions == None: # when the model just start 
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
            self.avgNonFossilAllocationShort = \
                                   vos.readPCRmapClone(\
                                         iniItems.groundwaterOptions['avgNonFossilGroundwaterAllocationShortIni'],
                                         self.cloneMap,self.tmpDir,self.inputDir)
        else:                     # during/after spinUp
            self.storGroundwater             = iniConditions['groundwater'][ 'storGroundwater']
            self.avgAbstraction              = iniConditions['groundwater'][ 'avgTotalGroundwaterAbstraction']      
            self.avgAllocation               = iniConditions['groundwater'][ 'avgTotalGroundwaterAllocationLong']
            self.avgAllocationShort          = iniConditions['groundwater'][ 'avgTotalGroundwaterAllocationShort']
            self.avgNonFossilAllocation      = iniConditions['groundwater'][ 'avgNonFossilGroundwaterAllocationLong']      
            self.avgNonFossilAllocationShort = iniConditions['groundwater'][ 'avgNonFossilGroundwaterAllocationShort']      

        # initial condition for storGroundwaterFossil (unit: m)
        #
        # Note that storGroundwaterFossil should not be depleted during the spin-up. 
        #
        if iniItems.groundwaterOptions['storGroundwaterFossilIni'] == "Maximum" and\
           self.limitFossilGroundwaterAbstraction:
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
        self.avgAllocation   = pcr.cover( self.avgAllocation,0.0)
        self.avgAllocation   = pcr.max(0.,self.avgAllocation)                                    
        self.avgAllocation   = pcr.ifthen(self.landmask,\
                                          self.avgAllocation)
        #
        self.avgAllocationShort = pcr.cover( self.avgAllocationShort,0.0)
        self.avgAllocationShort = pcr.max(0.,self.avgAllocationShort)                                    
        self.avgAllocationShort = pcr.ifthen(self.landmask,\
                                             self.avgAllocationShort)
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

        if self.useMODFLOW: 
            self.update_with_MODFLOW(landSurface,routing,currTimeStep)
        else:    
            self.update_without_MODFLOW(landSurface,routing,currTimeStep)
        
        self.calculate_statistics(routing)    

        # old-style reporting                             
        self.old_style_groundwater_reporting(currTimeStep)              # TODO: remove this one

    def update_with_MODFLOW(self,landSurface,routing,currTimeStep):

        logger.info("Updating groundwater based on the MODFLOW output.")

        # relativeGroundwaterHead, storGroundwater and baseflow fields are assumed to be constant  
        self.storGroundwater = self.storGroundwater
        self.baseflow = self.baseflow 

        # river bed exchange has been accomodated in baseflow (via MODFLOW, river and drain packages)
        self.surfaceWaterInf = pcr.scalar(0.0) 
        
        # non fossil groundwater abstraction
        self.nonFossilGroundwaterAbs = landSurface.nonFossilGroundwaterAbs

        # fossil groundwater abstraction (must be zero):
        self.fossilGroundwaterAbstr = landSurface.fossilGroundwaterAbstr

        # groundwater allocation (Note: This is done in the landSurface module)
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc    = landSurface.fossilGroundwaterAlloc

        # groundwater allocation (Note: This is done in the landSurface module)
        self.allocNonFossilGroundwater = landSurface.allocNonFossilGroundwater
        self.fossilGroundwaterAlloc    = landSurface.fossilGroundwaterAlloc
        
        # Note: The following variable (unmetDemand) is a bad name and used in the past. 
        #       Its definition is actually as follows: (the amount of demand that is satisfied/allocated from fossil groundwater) 
        self.unmetDemand = self.fossilGroundwaterAlloc


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

