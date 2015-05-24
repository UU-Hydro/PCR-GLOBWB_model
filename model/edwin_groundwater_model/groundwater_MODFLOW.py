#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os

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
        result['groundwaterHead'] = self.groundwaterHead       # unit: m
        return result


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

        # channel properties: read several variables from the netcdf file
        for var in ['lddMap','cellAreaMap','gradient','bankfull_width',
                    'bankfull_depth','dem_floodplain','dem_riverbed']:
            vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['channelNC'], \
                                                                var, self.cloneMap)
            vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
        
        # cell fraction if channel water reaching the flood plan
        self.flood_plain_fraction = self.return_innundation_fraction(pcr.max(0.0, self.dem_floodplain - self.dem_minimum))
        
        # coefficient of Manning
        self.manningsN = vos.readPCRmapClone(self.iniItems.modflowParameterOptions['manningsN'],\
                                             self.cloneMap,self.tmpDir,self.inputDir)
        
        # minimum channel gradient
        minGradient   = 0.000005
        self.gradient = pcr.max(minGradient, pcr.cover(self.gradient, minGradient))

        # correcting lddMap
        self.lddMap = pcr.ifthen(pcr.scalar(self.lddMap) > 0.0, self.lddMap)
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        
        # channelLength = approximation of channel length (unit: m)  # This is approximated by cell diagonal. 
        cellSizeInArcMin    =  np.round(pcr.clone().cellSize()*60.)
        verticalSizeInMeter =  cellSizeInArcMin*1852.                            
        self.channelLength  = ((self.cellAreaMap/verticalSizeInMeter)**(2)+\
                                                (verticalSizeInMeter)**(2))**(0.5)
        
        # option for lakes and reservoir
        self.onlyNaturalWaterBodies = False
        if self.iniItems.modflowParameterOptions['onlyNaturalWaterBodies'] == "True": self.onlyNaturalWaterBodies = True

        # groundwater linear recession coefficient (day-1) ; the linear reservoir concept is still being used to represent fast response flow  
        #                                                                                                                  particularly from karstic aquifer in mountainous regions                    
        self.recessionCoeff = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['groundwaterPropertiesNC'],\
                                                                 'recessionCoeff', self.cloneMap)
        self.recessionCoeff = pcr.cover(self.recessionCoeff,0.00)       
        self.recessionCoeff = pcr.min(1.0000,self.recessionCoeff)       
        #
        if 'minRecessionCoeff' in iniItems.modflowParameterOptions.keys():
            minRecessionCoeff = float(iniItems.modflowParameterOptions['minRecessionCoeff'])
        else:
            minRecessionCoeff = 1.0e-4                                       # This is the minimum value used in Van Beek et al. (2011). 
        self.recessionCoeff = pcr.max(minRecessionCoeff,self.recessionCoeff)      
        
        # aquifer specific yield (dimensionless)
        self.specificYield = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['groundwaterPropertiesNC'],\
                                                               'specificYield', self.cloneMap)
        self.specificYield  = pcr.cover(self.specificYield,0.0)       
        self.specificYield  = pcr.max(0.010,self.specificYield)         # TODO: TO BE CHECKED: The resample process of specificYield     
        self.specificYield  = pcr.min(1.000,self.specificYield)       

        # aquifer saturated conductivity (m/day)
        self.kSatAquifer = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['groundwaterPropertiesNC'],\
                                                             'kSatAquifer', self.cloneMap)
        self.kSatAquifer = pcr.cover(self.kSatAquifer,pcr.mapmaximum(self.kSatAquifer))       
        self.kSatAquifer = pcr.max(0.010,self.kSatAquifer)
        
        # estimate of thickness (unit: m) of accesible groundwater 
        totalGroundwaterThickness = vos.netcdf2PCRobjCloneWithoutTime(self.iniItems.modflowParameterOptions['estimateOfTotalGroundwaterThicknessNC'],\
                                    'thickness', self.cloneMap)
        # extrapolation 
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,\
                                    pcr.windowaverage(totalGroundwaterThickness, 1.0))
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness,\
                                    pcr.windowaverage(totalGroundwaterThickness, 1.5))
        totalGroundwaterThickness = pcr.cover(totalGroundwaterThickness, 0.0)
        #
        # set minimum thickness
        minimumThickness = pcr.scalar(float(\
                           self.iniItems.modflowParameterOptions['minimumTotalGroundwaterThickness']))
        totalGroundwaterThickness = pcr.max(minimumThickness, totalGroundwaterThickness)
        #
        # set maximum thickness: 500 m.
        maximumThickness = 500
        self.totalGroundwaterThickness = pcr.min(maximumThickness., totalGroundwaterThickness)

        # river bed resistance (unit: day)
        self.bed_resistance = 1.0
        
        # initiate pcraster modflow object
        self.initiate_modflow()
        
        # initiate old style reporting                                  # TODO: remove this!
        self.initiate_old_style_groundwater_reporting(iniItems)

    def initiate_modflow(self):

        logger.info("Initializing pcraster modflow.")
        
        # initialise 
        self.pcr_modflow = pcr.initialise(pcr.clone())
        
        # grid specification - one layer model
        top    = self.dem_average
        bottom = top - self.totalGroundwaterThickness
        self.pcr_modflow.createBottomLayer(bottom, top) 
        
        # specification for the boundary condition (IBOUND, BAS package)
        # - active cells only in landmask
        # - constant head for outside the landmask
        ibound = pcr.ifthen(self.landmask, pcr.nominal(1))
        ibound = pcr.cover(ibound, pcr.nominal(-1))
        self.pcr_modflow.setBoundary(ibound, 1)
        
        # specification for conductivities (BCF package)
        horizontal_conductivity = self.kSatAquifer # unit: m/day
        # set the minimum value for transmissivity; (Deltares's default value: 10 m2/day)
        minimimumTransmissivity = 20.
        horizontal_conductivity = pcr.max(minimimumTransmissivity, \
                                          horizontal_conductivity * self.totalGroundwaterThickness) / self.totalGroundwaterThickness
        vertical_conductivity   = horizontal_conductivity                # dummy values, as one layer model is used
        self.pcr_modflow.setConductivity(00, horizontal_conductivity, \
                                             vertical_conductivity, 1)              
        
        # set drain package
        self.set_drain_package()
        
        # TODO: defining/incorporating anisotrophy values

    def get_initial_heads(self):
		
        if self.iniItems.modflowTransientInputOptions['groundwaterHeadIni'] != "None": 
        
            # using a pre-defined groundwater head described in the ini/configuration file
            self.groundwaterHead = vos.readPCRmapClone(self.modflowTransientInputOptions['groundwaterHeadIni'],\
                                                       self.cloneMap, self.tmpDir, self.inputDir)
        else:    

            # calculate/simulate a steady state condition and obtain its calculated head values
            self.steady_state_simulation()
            self.groundwaterHead = self.pcr_modflow.getHeads(1)  

    def estimate_bottom_of_bank_storage(self):

        # influence zone depth (m)
        influence_zone_depth = 5.00
        
        # bottom_elevation > flood_plain elevation - influence zone
        bottom_of_bank_storage = self.dem_floodplain - influence_zone_depth
        
        # bottom_elevation > river bed
        bottom_of_bank_storage = pcr.max(self.dem_riverbed, bottom_of_bank_storage)
        
        # bottom_elevation > its downstream value
        bottom_of_bank_storage = pcr.max(bottom_of_bank_storage, \
                                 pcr.cover(pcr.downstream(self.lddMap, bottom_of_bank_storage), bottom_of_bank_storage))

        #~ # bottom_elevation >= 0.0 (must be higher than sea level)
        #~ bottom_of_bank_storage = pcr.max(0.0, bottom_of_bank_storage)
        
        # reducing noise
        bottom_of_bank_storage = pcr.max(bottom_of_bank_storage,\
                                 pcr.windowaverage(bottom_of_bank_storage, 3.0 * pcr.clone().cellSize()))

        # TODO: Check again this concept. 
        
        # TODO: We may want to improve this concept - by incorporating the following 
        # - smooth bottom_elevation
        # - upstream areas in the mountainous regions and above perrenial stream starting points may also be drained (otherwise water will accumulate) 
        # - bottom_elevation > minimum elevation that is estimated from the maximum of S3 from the PCR-GLOBWB simulation
        
        return bottom_of_bank_storage

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


    def update(self,landSurface,routing,currTimeStep):

        pass
        
        #~ # do the modflod update only at  
        #~ if currTimeStep
        #~ self.pcr_modflow.setInitialHead(self.dem_average, 1)

    def steady_state_simulation(self):
		
        logger.info("Preparing MODFLOW input for steady state simulation.")

        # using dem_average as the initial groundwater head value 
        self.pcr_modflow.setInitialHead(self.dem_average, 1)
        
        # set PCG solver:
        MXITER = 100                # maximum number of outer iterations
        ITERI  = 30                 # number of inner iterations
        NPCOND = 1                  # 1 - Modified Incomplete Cholesky, 2 - Polynomial matrix conditioning method;
        HCLOSE = 0.05               # HCLOSE (unit: m) # 0.1 is working
        RCLOSE = 10.* 400.*400.     # RCLOSE (unit: m3) ; Deltares uses 100 m3 for their 25 m modflow model  
        RELAX  = 1.00               # relaxation parameter used with NPCOND = 1
        NBPOL  = 2                  # indicates whether the estimate of the upper bound on the maximum eigenvalue is 2.0 (but we don ot use it, since NPCOND = 1) 
        DAMP   = 1                  # no damping (DAMP introduced in MODFLOW 2000)
        self.pcr_modflow.setPCG(MXITER, ITERI, NPCOND, HCLOSE, RCLOSE, RELAX, NBPOL, DAMP)
        
        # set parameter values for the DIS package 
        ITMUNI = 4     # indicates the time unit (0: undefined, 1: seconds, 2: minutes, 3: hours, 4: days, 5: years)
        LENUNI = 2     # indicates the length unit (0: undefined, 1: feet, 2: meters, 3: centimeters)
        PERLEN = 1.0   # duration of a stress period
        NSTP   = 1     # number of time steps in a stress period
        TSMULT = 1.0   # multiplier for the length of the successive iterations
        SSTR   = 1     # 0 - transient, 1 - steady state
        self.pcr_modflow.setDISParameter(ITMUNI, LENUNI, PERLEN, NSTP, TSMULT, SSTR)  

        # read input files (for the steady state condition, we use pcraster maps):
        # - discharge value (m3/s)
        discharge = vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgDischargeInputMap'],\
                                            self.cloneMap, self.tmpDir, self.inputDir)
        # - recharge/capillary rise (unit: m/day) from PCR-GLOBWB 
        gwRecharge = vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgGroundwaterRechargeInputMap'],\
                                            self.cloneMap, self.tmpDir, self.inputDir)
        # - groundwater abstraction (unit: m/day) from PCR-GLOBWB 
        gwAbstraction -= vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgGroundwaterAbstractionInputMap'],\
                                            self.cloneMap, self.tmpDir, self.inputDir)
        # - return flow of groundwater abstraction (unit: m/day) from PCR-GLOBWB 
        gwAbstractionReturnFlow += vos.readPCRmapClone(self.iniItems.modflowSteadyStateInputOptions['avgGroundwaterAbstractionReturnFlowInputMap'],\
                                            self.cloneMap, self.tmpDir, self.inputDir)
        
        # set recharge and river packages
        self.set_river_package(discharge)
        self.set_recharge_package(gwRecharge, gwAbstraction, gwAbstractionReturnFlow)
        
        # execute MODFLOW 
        logger.info("Executing MODFLOW for a steady state simulation.")
        self.pcr_modflow.run()
        
        # obtain the calculated values
        self.groundwaterHead  = self.pcr_modflow.getHeads(1)
        self.groundwaterDepth = pcr.ifthen(self.landmask, self.dem_average - self.groundwaterHead)
        
        # for debuging 
        pcr.report(self.groundwaterHead , "gw_head.map")
        pcr.report(self.groundwaterDepth, "gw_depth.map")
        pcr.report(self.surface_water_elevation, "surface_water_elevation.map")


    def set_river_package(self, discharge):

        # specify the river package
        #
        # - waterBody class to define the extent of lakes and reservoirs
        self.WaterBodies = waterBodies.WaterBodies(self.iniItems,\
                                                   self.landmask,\
                                                   self.onlyNaturalWaterBodies)
        #
        # - get parameter files by using the starting date given in the configuration file
        self.WaterBodies.getParameterFiles(date_given = self.iniItems.globalOptions['startTime'],\
                                           cellArea = self.cellAreaMap, \
                                           ldd = self.lddMap)        
        #
        # - surface water river bed/bottom elevation
        #
        # - for lakes and resevoirs, make the bottom elevation very deep --- Shall we do this? 
        surface_water_bed_elevation = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, \
                                                 self.dem_riverbed - 500.0)
        surface_water_bed_elevation = pcr.cover(surface_water_bed_elevation, self.dem_riverbed)
        #
        #~ surface_water_bed_elevation = self.dem_riverbed
        #
        # rounding values for surface_water_bed_elevation
        self.surface_water_bed_elevation = pcr.roundup(surface_water_bed_elevation * 1000.)/1000.
        #
        # - river bed condutance (unit: m2/day)
        bed_surface_area = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0, \
                                                 self.WaterBodies.fracWat * self.cellAreaMap)   # TODO: Incorporate the concept of dynamicFracWat
        bed_surface_area = pcr.cover(bed_surface_area, \
                                     self.bankfull_width * self.channelLength)
        bed_conductance = (1.0/self.bed_resistance) * bed_surface_area
        bed_conductance = pcr.ifthenelse(bed_conductance < 1e-20, 0.0, \
                                         bed_conductance) 
        self.bed_conductance = bed_conductance
        # 
        # - convert discharge value to surface water elevation (m)
        river_water_height = (self.bankfull_width**(-3/5)) * (discharge**(3/5)) * ((self.gradient)**(-3/10)) *(self.manningsN**(3/5))
        surface_water_elevation = self.dem_riverbed + \
                                  river_water_height
        # - calculating water level (unit: m) above the flood plain   # TODO: Improve this concept (using Rens's latest innundation scheme) 
        #----------------------------------------------------------
        water_above_fpl  = pcr.max(0.0, surface_water_elevation - self.dem_floodplain)  # unit: m, water level above the floodplain (not distributed)
        water_above_fpl *= self.bankfull_depth * self.bankfull_width / self.cellAreaMap  # unit: m, water level above the floodplain (distributed within the cell)
        # TODO: Improve this concept using Rens's latest scheme
        #
        # - corrected surface water elevation
        surface_water_elevation = pcr.ifthenelse(surface_water_elevation > self.dem_floodplain, \
                                                                           self.dem_floodplain + water_above_fpl, \
                                                                           surface_water_elevation)
        # - surface water elevation for lakes and reservoirs:
        lake_reservoir_water_elevation = pcr.ifthen(self.WaterBodies.waterBodyOut, surface_water_elevation)
        lake_reservoir_water_elevation = pcr.areamaximum(lake_reservoir_water_elevation, self.WaterBodies.waterBodyIds)
        lake_reservoir_water_elevation = pcr.cover(lake_reservoir_water_elevation, \
                                                pcr.areaaverage(surface_water_elevation, self.WaterBodies.waterBodyIds))
        # 
        # - merge lake and reservoir water elevation
        surface_water_elevation = pcr.cover(lake_reservoir_water_elevation, surface_water_elevation)
        #
        # - pass values to the river package
        surface_water_elevation = pcr.cover(surface_water_elevation, self.surface_water_bed_elevation)
        surface_water_elevation = pcr.rounddown(surface_water_elevation * 1000.)/1000.
        #
        # - make sure that HRIV >= RBOT (no infiltration if HRIV = RBOT and h < RBOT)  
        self.surface_water_elevation = pcr.max(surface_water_elevation, self.surface_water_bed_elevation)
        #
        # - pass the values to the RIV package 
        self.pcr_modflow.setRiver(self.surface_water_elevation, self.surface_water_bed_elevation, self.bed_conductance, 1)
        
    def set_recharge_package(self, gwRecharge, gwAbstraction, gwAbstractionReturnFlow):

        # specify the recharge package
        # + recharge/capillary rise (unit: m/day) from PCR-GLOBWB 
        # - groundwater abstraction (unit: m/day) from PCR-GLOBWB 
        # + return flow of groundwater abstraction (unit: m/day) from PCR-GLOBWB 
        net_recharge = gwRecharge - gwAbstraction + gwAbstractionReturnFlow
        # - correcting values (considering MODFLOW lat/lon cell properties)
        #   and pass them to the RCH package   
        net_RCH = pcr.cover(net_recharge * self.cellAreaMap/(pcr.clone().cellSize()*pcr.clone().cellSize()), 0.0)
        net_RCH = pcr.ifthenelse(pcr.abs(net_RCH) < 1e-20, 0.0, net_RCH)
        self.pcr_modflow.setRecharge(net_RCH, 1)

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


    def transient_simulation(self):

        # set initial groundwater head 
        self.pcr_modflow.setInitialHead(self.groundwaterHead, 1)
        
        # execute MODFLOW 
        self.pcr_modflow.run()

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

