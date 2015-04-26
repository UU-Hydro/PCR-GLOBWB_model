#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
import pcraster as pcr
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

from ncConverter import *

import landCover as lc
import parameterSoilAndTopo as parSoilAndTopo

class LandSurface(object):
    
    def getState(self):
        result = {}
    
        if self.numberOfSoilLayers == 2:
            for coverType in self.coverTypes:
                result[coverType] = {}
                result[coverType]['interceptStor'] = \
                  self.landCoverObj[coverType].interceptStor
                result[coverType]['snowCoverSWE' ] = \
                  self.landCoverObj[coverType].snowCoverSWE
                result[coverType]['snowFreeWater'] = \
                  self.landCoverObj[coverType].snowFreeWater
                result[coverType]['topWaterLayer'] = \
                  self.landCoverObj[coverType].topWaterLayer
                result[coverType]['storUpp'] = \
                  self.landCoverObj[coverType].storUpp
                result[coverType]['storLow'] = \
                  self.landCoverObj[coverType].storLow
                result[coverType]['interflow'    ] = \
                  self.landCoverObj[coverType].interflow

        if self.numberOfSoilLayers == 3:
            for coverType in self.coverTypes:
                result[coverType] = {}
                result[coverType]['interceptStor'] = \
                  self.landCoverObj[coverType].interceptStor
                result[coverType]['snowCoverSWE' ] = \
                  self.landCoverObj[coverType].snowCoverSWE
                result[coverType]['snowFreeWater'] = \
                  self.landCoverObj[coverType].snowFreeWater
                result[coverType]['topWaterLayer'] = \
                  self.landCoverObj[coverType].topWaterLayer
                result[coverType]['storUpp000005'] = \
                  self.landCoverObj[coverType].storUpp000005
                result[coverType]['storUpp005030'] = \
                  self.landCoverObj[coverType].storUpp005030
                result[coverType]['storLow030150'] = \
                  self.landCoverObj[coverType].storLow030150
                result[coverType]['interflow'    ] = \
                  self.landCoverObj[coverType].interflow
              
        return result
    
    def getPseudoState(self):
        result = {}
        
        if self.numberOfSoilLayers == 2:
            result['interceptStor'] = self.interceptStor
            result['snowCoverSWE']  = self.snowCoverSWE
            result['snowFreeWater'] = self.snowFreeWater
            result['topWaterLayer'] = self.topWaterLayer
            result['storUpp']       = self.storUpp
            result['storLow']       = self.storLow

        if self.numberOfSoilLayers == 3:
            result['interceptStor'] = self.interceptStor
            result['snowCoverSWE']  = self.snowCoverSWE
            result['snowFreeWater'] = self.snowFreeWater
            result['topWaterLayer'] = self.topWaterLayer
            result['storUpp000005'] = self.storUpp000005
            result['storUpp005030'] = self.storUpp005030
            result['storLow030150'] = self.storLow030150
        
        return result

    def __init__(self,iniItems,landmask,initialState=None):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask

        # get cellArea:                                                 # TODO: integrate this one with the one coming from the routing module
        self.cellArea = vos.readPCRmapClone(\
          iniItems.routingOptions['cellAreaMap'],
          self.cloneMap,self.tmpDir,self.inputDir)
        self.cellArea = pcr.ifthen(self.landmask, self.cellArea)
        
        # number of soil layers:
        self.numberOfSoilLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])
        
        # list of aggregated variables that MUST be defined in the module:
        # - aggregated from landCover modules
        # - some are needed for water balance checking 
        # - some are needed in other modules (e.g. routing, groundwater)
        # - some are needed for initialConditions
        # 
        # main state variables (unit: m)
        self.mainStates = ['interceptStor',\
                           'snowCoverSWE' ,\
                           'snowFreeWater',\
                           'topWaterLayer']
        #
        # state variables (unit: m)
        self.stateVars = ['storUppTotal',
                          'storLowTotal']
        #
        # flux variables (unit: m/day)
        self.fluxVars  = ['infiltration','gwRecharge','netLqWaterToSoil',
                          'totalPotET',
                          'actualET',
                          'interceptEvap',
                          'openWaterEvap',
                          'actSnowFreeWaterEvap',
                          'actBareSoilEvap',
                          'actTranspiUppTotal',
                          'actTranspiLowTotal',
                          'actTranspiTotal',                                 
                          'directRunoff',
                          'interflow',
                          'interflowTotal',
                          'irrGrossDemand',
                          'nonIrrGrossDemand',
                          'totalPotentialGrossDemand',
                          'actSurfaceWaterAbstract',
                          'allocSurfaceWaterAbstract',
                          'desalinationAbstraction',
                          'desalinationAllocation',
                          'nonFossilGroundwaterAbs',
                          'allocNonFossilGroundwater',
                          'fossilGroundwaterAbstr',
                          'fossilGroundwaterAlloc',
                          'landSurfaceRunoff',
                          'satExcess',
                          'snowMelt',
                          'totalPotentialMaximumGrossDemand']
        #
        # specific variables for 2 and 3 layer soil models:
        #
        if self.numberOfSoilLayers == 2:
            self.mainStates += ['storUpp','storLow']
            self.stateVars  += self.mainStates
            self.fluxVars   += ['actTranspiUpp','actTranspiLow','netPercUpp']
        #                                                      
        if self.numberOfSoilLayers == 3:
            self.mainStates += ['storUpp000005','storUpp005030','storLow030150']
            self.stateVars  += self.mainStates
            self.fluxVars   += ['actTranspiUpp000005','actTranspiUpp005030','actTranspiLow030150',
                                   'netPercUpp000005',   'netPercUpp005030',
                                                       'interflowUpp005030']
        
        # list of all variables that will be calculated/reported in landSurface.py
        self.aggrVars = self.stateVars + self.fluxVars

        # assign the topography and soil parameters
        self.parameters = parSoilAndTopo.SoilAndTopoParameters(iniItems,self.landmask)
        self.parameters.read(iniItems)

        self.debugWaterBalance = iniItems.landSurfaceOptions['debugWaterBalance']

        
        # landCover types included in the simulation: 
        self.coverTypes = ["forest","grassland"]
        #
        self.includeIrrigation = False
        if iniItems.landSurfaceOptions['includeIrrigation'] == "True":
            self.includeIrrigation = True
            self.coverTypes += ["irrPaddy","irrNonPaddy"]
            logger.info("Irrigation is included/considered in this run.")
        else:     
            logger.info("Irrigation is NOT included/considered in this run.")

        # limitAbstraction
        self.limitAbstraction = False
        if iniItems.landSurfaceOptions['limitAbstraction'] == "True": self.limitAbstraction = True

        # water demand options: irrigation efficiency, non irrigation water demand, and desalination supply 
        self.waterDemandOptions(iniItems)
        
        # pre-defined fractions for groundwater and surface water source partitioning for irrigation demand:
        if 'irrigationSurfaceWaterAbstractionFractionData' in iniItems.landSurfaceOptions.keys() and\
           'irrigationSurfaceWaterAbstractionFractionDataQuality' in iniItems.landSurfaceOptions.keys():
            #
            logger.info('Using/incorporating the predefined fractions of surface water source for irrigation demand .')
            #
            self.swAbstractionFractionData = pcr.cover(\
                                             vos.readPCRmapClone(iniItems.landSurfaceOptions['irrigationSurfaceWaterAbstractionFractionData'],\
                                                                 self.cloneMap,self.tmpDir,self.inputDir), 0.0)
            self.swAbstractionFractionData = pcr.ifthen(self.swAbstractionFractionData >= 0.0, \
                                                        self.swAbstractionFractionData )
            self.swAbstractionFractionDataQuality = \
                                             pcr.cover(\
                                             vos.readPCRmapClone(iniItems.landSurfaceOptions['irrigationSurfaceWaterAbstractionFractionDataQuality'],\
                                                                 self.cloneMap,self.tmpDir,self.inputDir), 0.0)
            # ignore value with the quality above 5 
            self.swAbstractionFractionData = pcr.ifthen(self.swAbstractionFractionDataQuality <= 5.0, \
                                                        self.swAbstractionFractionData)
        else:                                                                                                                          
            logger.info('Not using/incorporating the predefined fractions of surface water source for irrigation demand .')
            self.swAbstractionFractionData = None

        # pre-defined fractions for groundwater and surface water source partitioning for non irrigation demand:
        if 'maximumNonIrrigationSurfaceWaterAbstractionFractionData' in iniItems.landSurfaceOptions.keys():
            #
            logger.info('Using/incorporating the predefined fractions of surface water source for non irrigation demand .')
            #
            self.maximumNonIrrigationSurfaceWaterAbstractionFractionData = \
                                             pcr.min(1.0,\
                                             pcr.cover(\
                                             vos.readPCRmapClone(iniItems.landSurfaceOptions['maximumNonIrrigationSurfaceWaterAbstractionFractionData'],\
                                                                 self.cloneMap,self.tmpDir,self.inputDir), 1.0))
        else:                                                                                                                          
            logger.info('Using/incorporating the predefined fractions of surface water source for non irrigation demand .')
            self.maximumNonIrrigationSurfaceWaterAbstractionFractionData = pcr.scalar(1.0)

        # instantiate self.landCoverObj[coverType]
        self.landCoverObj = {} # initialize land cover objects
        for coverType in self.coverTypes:
            self.landCoverObj[coverType] = lc.LandCover(iniItems,\
                                                        str(coverType)+'Options',\
                                                        self.parameters,self.landmask,\
                                                        self.irrigationEfficiency,\
                                                        self.usingAllocSegments)
        
        # rescale landCover Fractions
        self.scaleNaturalLandCoverFractions()
        if self.includeIrrigation: self.scaleModifiedLandCoverFractions()
        
        # If using historical/dynamic irrigation file (changing every year), we have to get fraction over irrigation area 
        #                                                                   (in order to calculate irrigation area for each irrigation type)
        #
        # Note that: totalIrrAreaFrac   = fraction irrigated areas (e.g. paddy + nonPaddy) over the entire cell area (dimensionless) ; this value changes (if self.dynamicIrrigationArea = True)
        #            irrTypeFracOverIrr = fraction each land cover type (paddy or nonPaddy) over the irrigation area (dimensionless) ; this value is constant for the entire simulation
        #
        if self.includeIrrigation and self.dynamicIrrigationArea:
            
            # total irrigated area fraction (over the entire cell) 
            totalIrrAreaFrac = 0.0 
            for coverType in self.coverTypes:
                if coverType.startswith('irr'):
                    totalIrrAreaFrac += self.landCoverObj[coverType].fracVegCover
            
            # fraction over irrigation area 
            for coverType in self.coverTypes:
                if coverType.startswith('irr'):
                    self.landCoverObj[coverType].irrTypeFracOverIrr = vos.getValDivZero(self.landCoverObj[coverType].fracVegCover,\
                                                                                        totalIrrAreaFrac, vos.smallNumber) 

        # Get the initialconditions
        self.getInitialConditions(iniItems, initialState)

        # initiate old style reporting                                  # TODO: remove this!
        self.initiate_old_style_land_surface_reporting(iniItems)

    def initiate_old_style_land_surface_reporting(self,iniItems):

        self.report = True
        try:
            self.outDailyTotNC = iniItems.landSurfaceOptions['outDailyTotNC'].split(",")
            self.outMonthTotNC = iniItems.landSurfaceOptions['outMonthTotNC'].split(",")
            self.outMonthAvgNC = iniItems.landSurfaceOptions['outMonthAvgNC'].split(",")
            self.outMonthEndNC = iniItems.landSurfaceOptions['outMonthEndNC'].split(",")
            self.outAnnuaTotNC = iniItems.landSurfaceOptions['outAnnuaTotNC'].split(",")
            self.outAnnuaAvgNC = iniItems.landSurfaceOptions['outAnnuaAvgNC'].split(",")
            self.outAnnuaEndNC = iniItems.landSurfaceOptions['outAnnuaEndNC'].split(",")
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

    def getInitialConditions(self,iniItems,iniConditions=None):

        # obtaining initial land cover fractions for runs with includeIrrigation and dynamicIrrigationArea
        #
        # starting year in integer
        starting_year = int(iniItems.globalOptions['startTime'][0:4])
        #
        # check if the run start at the first day of the year:
        start_on_1_Jan = False
        if iniItems.globalOptions['startTime'][-5:] == "01-01": start_on_1_Jan = True
        #
        # condition to consider previous year land cover fraction 
        consider_previous_year_land_cover_fraction = False
        #
        # For non spin-up runs that start at the first day of the year (1 January), 
        # - we have to consider the previous year land cover fractions, specifically if we consider the dynamic/expansion of irrigation areas
        #
        if iniConditions == None and start_on_1_Jan == True and \
           self.dynamicIrrigationArea and self.includeIrrigation: 
            # obtain the previous year land cover fractions:
            self.scaleDynamicIrrigation(starting_year - 1)                       # the previous year land cover fractions
            consider_previous_year_land_cover_fraction = True
        #
        # For spin-up runs or for runs that start after 1 January,
        # - we do not have to consider the previous year land cover fractions
        #
        if consider_previous_year_land_cover_fraction == False and \
           self.dynamicIrrigationArea and self.includeIrrigation: 
            # just using the current year land cover fractions:
            self.scaleDynamicIrrigation(starting_year)                           # the current year land cover fractions
        
        # get initial land cover fractions that will be used 
        #
        for coverType in self.coverTypes:\
            self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].fracVegCover

        # get initial conditions
        #
        # first, we set all aggregated states to zero (only the ones in mainStates): 
        for var in self.mainStates: vars(self)[var] = pcr.scalar(0.0)
        #
        # then we initiate them in the following land cover loop: 
        for coverType in self.coverTypes:
            if iniConditions != None:
                self.landCoverObj[coverType].getICsLC(iniItems,iniConditions['landSurface'][coverType])
            else:
                self.landCoverObj[coverType].getICsLC(iniItems)
            #
            # summarize/aggregate the initial states/storages (using the initial land cover fractions: previousFracVegCover)
            for var in self.mainStates:
                land_cover_states   = vars(self.landCoverObj[coverType])[var]
                land_cover_fraction = self.landCoverObj[coverType].previousFracVegCover
                vars(self)[var]    += land_cover_states * land_cover_fraction

        # get initial condition for average total 


    def waterDemandOptions(self,iniItems):

        # domestic water demand (unit: m/day)
        #
        self.domesticWaterDemandOption = False
        if iniItems.landSurfaceOptions['includeDomesticWaterDemand']  == "True":
            logger.info("Domestic water demand is included in the calculation.")
            self.domesticWaterDemandOption = True  
        else:
            logger.info("Domestic water demand is NOT included in the calculation.")
        #
        if self.domesticWaterDemandOption:
            self.domesticWaterDemandFile = vos.getFullPath(\
             iniItems.landSurfaceOptions['domesticWaterDemandFile'],self.inputDir,False)

        # industry water demand (unit: m/day)
        #
        self.industryWaterDemandOption = False
        if iniItems.landSurfaceOptions['includeIndustryWaterDemand']  == "True":
            logger.info("Industry water demand is included in the calculation.")
            self.industryWaterDemandOption = True  
        else:
            logger.info("Industry water demand is NOT included in the calculation.")
        #
        if self.industryWaterDemandOption:
            self.industryWaterDemandFile = vos.getFullPath(\
             iniItems.landSurfaceOptions['industryWaterDemandFile'],self.inputDir,False)

        # livestock water demand (unit: m/day)
        self.livestockWaterDemandOption = False
        if iniItems.landSurfaceOptions['includeLivestockWaterDemand']  == "True":
            logger.info("Livestock water demand is included in the calculation.")
            self.livestockWaterDemandOption = True  
        else:
            logger.info("Livestock water demand is NOT included in the calculation.")
        #
        if self.livestockWaterDemandOption:
            self.livestockWaterDemandFile = vos.getFullPath(\
             iniItems.landSurfaceOptions['livestockWaterDemandFile'],self.inputDir,False)
        
        # historical irrigation area (unit: hectar)
        self.dynamicIrrigationArea = False
        if iniItems.landSurfaceOptions['historicalIrrigationArea'] != "None":
            self.dynamicIrrigationArea = True
        else:
            logger.info("Extent of irrigation areas is SAME for EVERY YEAR.")
        #
        if self.dynamicIrrigationArea:
            self.dynamicIrrigationAreaFile = vos.getFullPath(\
               iniItems.landSurfaceOptions['historicalIrrigationArea'],self.inputDir,False)
        
        # irrigation efficiency map:
        self.irrigationEfficiency = vos.readPCRmapClone(\
                     iniItems.landSurfaceOptions['irrigationEfficiency'],
                     self.cloneMap,self.tmpDir,self.inputDir)
        #
        # extrapolate irrigation efficiency map:
        try:
            self.irrigationEfficiency = pcr.cover(self.irrigationEfficiency,\
                            pcr.windowaverage(self.irrigationEfficiency, 1.50),\
                            pcr.windowaverage(self.irrigationEfficiency, 2.50),\
                            pcr.windowaverage(self.irrigationEfficiency, 3.50),\
                            pcr.windowaverage(self.irrigationEfficiency, 5.00),1.0)
        except:                                                 
            pass

        # desalination water supply option
        self.includeDesalination = False
        if iniItems.landSurfaceOptions['desalinationWater'] != "None":
            logger.info("Monthly desalination water is included.")
            self.includeDesalination = True
            self.desalinationWaterFile = iniItems.landSurfaceOptions['desalinationWater']
        else:    
            logger.info("Monthly desalination water is NOT included.")

        # zones at which water allocation (surface and groundwater allocation) is determined
        self.usingAllocSegments = False
        self.allocSegments = None
        if iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater']  != "None":
            self.usingAllocSegments = True 
            
            self.allocSegments = vos.readPCRmapClone(\
             iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater'],
             self.cloneMap,self.tmpDir,self.inputDir,isLddMap=False,cover=None,isNomMap=True)
            self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)
            
            cellArea = vos.readPCRmapClone(\
              iniItems.routingOptions['cellAreaMap'],
              self.cloneMap,self.tmpDir,self.inputDir)
            cellArea = pcr.ifthen(self.landmask, cellArea)
            self.segmentArea = pcr.areatotal(pcr.cover(cellArea, 0.0), self.allocSegments)
            self.segmentArea = pcr.ifthen(self.landmask, self.segmentArea)
        else:
            logger.info("Water demand is satisfied by local source only.")


    def scaleNaturalLandCoverFractions(self): 
        ''' rescales natural land cover fractions (make sure the total = 1)'''

        # total land cover fractions
        pristineAreaFrac = 0.0
        numb_of_lc_types = 0.0
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                pristineAreaFrac += pcr.cover(self.landCoverObj[coverType].fracVegCover, 0.0)
                numb_of_lc_types += 1.0

        # Fill cells with pristineAreaFrac < 0.0 - with window average value within 0.5 and 1.5 degree
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):

                filled_fractions = pcr.windowaverage(self.landCoverObj[coverType].fracVegCover,0.5)
                filled_fractions = pcr.cover(filled_fractions,\
                                   pcr.windowaverage(self.landCoverObj[coverType].fracVegCover,1.5))
                filled_fractions = pcr.max(0.0, filled_fractions)
                filled_fractions = pcr.min(1.0, filled_fractions)
                
                self.landCoverObj[coverType].fracVegCover = pcr.ifthen(pristineAreaFrac >= 0.0, self.landCoverObj[coverType].fracVegCover)
                self.landCoverObj[coverType].fracVegCover = pcr.cover(\
                                                            self.landCoverObj[coverType].fracVegCover,filled_fractions)
                self.landCoverObj[coverType].fracVegCover = pcr.ifthen(self.landmask,\
                                                            self.landCoverObj[coverType].fracVegCover)                                            

        # re-check total land cover fractions
        pristineAreaFrac = 0.0
        numb_of_lc_types = 0.0
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                pristineAreaFrac += pcr.cover(self.landCoverObj[coverType].fracVegCover, 0.0)
                numb_of_lc_types += 1.0

        # Fill cells with pristineAreaFrac = 0.0:
        self.landCoverObj['forest'].fracVegCover    = pcr.ifthenelse(pristineAreaFrac > 0.0, self.landCoverObj['forest'].fracVegCover, 0.0)
        self.landCoverObj['forest'].fracVegCover    = pcr.min(1.0, self.landCoverObj['forest'].fracVegCover)
        self.landCoverObj['grassland'].fracVegCover = 1.0 - self.landCoverObj['forest'].fracVegCover

        # recalculate total land cover fractions
        pristineAreaFrac = 0.0
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                pristineAreaFrac += pcr.cover(self.landCoverObj[coverType].fracVegCover, 0.0)
        
        # correcting 
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                self.landCoverObj[coverType].fracVegCover = \
                self.landCoverObj[coverType].fracVegCover / pristineAreaFrac

        pristineAreaFrac = 0.0 # reset
        #
        # checking pristineAreaFrac (must be equal to 1)
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                pristineAreaFrac += self.landCoverObj[coverType].fracVegCover
                self.landCoverObj[coverType].naturalFracVegCover = \
                self.landCoverObj[coverType].fracVegCover
        #
        # check and make sure that totalArea = 1.0 for all cells
        totalArea = pristineAreaFrac
        totalArea = pcr.ifthen(self.landmask,totalArea)
        totalArea = pcr.cover(totalArea, 1.0)
        check_map = totalArea - pcr.scalar(1.0)
        a,b,c = vos.getMinMaxMean(check_map)
        threshold = 1e-4
        if abs(a) > threshold or abs(b) > threshold:
            logger.error("total of 'Natural Area' fractions is not equal to 1.0 ... Min %f Max %f Mean %f" %(a,b,c)) 

    def scaleModifiedLandCoverFractions(self): 
        ''' rescales the land cover fractions with irrigation areas'''

        # check 
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                irrigatedAreaFrac += \
                               self.landCoverObj[coverType].fracVegCover

        # scale fracVegCover of irrigation if irrigatedAreaFrac > 1 
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                self.landCoverObj[coverType].fracVegCover = pcr.ifthenelse(irrigatedAreaFrac > 1.0,\
                                                                           self.landCoverObj[coverType].fracVegCover/irrigatedAreaFrac,\
                                                                           self.landCoverObj[coverType].fracVegCover)
        
        # corrected irrigated area fraction: 
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                irrigatedAreaFrac += self.landCoverObj[coverType].fracVegCover

        totalArea  = pcr.spatial(pcr.scalar(0.0))
        totalArea += irrigatedAreaFrac

        # correction factor for forest and grassland (pristine Areas)
        lcFrac = pcr.max(0.0, 1.0 - totalArea)
        pristineAreaFrac = pcr.spatial(pcr.scalar(0.0))

        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                self.landCoverObj[coverType].fracVegCover = 0.0
                self.landCoverObj[coverType].fracVegCover = \
                self.landCoverObj[coverType].naturalFracVegCover * lcFrac
                pristineAreaFrac += pcr.cover(\
                self.landCoverObj[coverType].fracVegCover, 0.0)

        # check and make sure that totalArea = 1.0 for all cells
        totalArea += pristineAreaFrac
        totalArea = pcr.ifthen(self.landmask,totalArea)
        totalArea = pcr.cover(totalArea, 1.0)
        totalArea = pcr.ifthen(self.landmask,totalArea)
        a,b,c = vos.getMinMaxMean(totalArea - pcr.scalar(1.0))
        threshold = 1e-4
        if abs(a) > threshold or abs(b) > threshold:
            logger.error("fraction total (from all land cover types) is not equal to 1.0 ... Min %f Max %f Mean %f" %(a,b,c)) 

    def getICsFor3Layers(self,iniItems,iniConditions = None):

        # first, we set the following aggregated storages to zero
        self.interceptStor = pcr.scalar(0.0)
        self.snowCoverSWE  = pcr.scalar(0.0)
        self.snowFreeWater = pcr.scalar(0.0)
        self.topWaterLayer = pcr.scalar(0.0)
        self.storUpp000005 = pcr.scalar(0.0)
        self.storUpp005030 = pcr.scalar(0.0)
        self.storLow030150 = pcr.scalar(0.0)

        # then we initiate them in the following land cover loop: 
        for coverType in self.coverTypes:
            if iniConditions != None:
                self.landCoverObj[coverType].getICsLC(iniItems,iniConditions['landSurface'][coverType])
            else:
                self.landCoverObj[coverType].getICsLC(iniItems)
            # summarize the following initial storages:
            self.interceptStor  += \
                            self.landCoverObj[coverType].interceptStor*\
                            self.landCoverObj[coverType].fracVegCover
            self.snowCoverSWE  += \
                            self.landCoverObj[coverType].snowCoverSWE*\
                            self.landCoverObj[coverType].fracVegCover
            self.snowFreeWater += \
                            self.landCoverObj[coverType].snowFreeWater*\
                            self.landCoverObj[coverType].fracVegCover
            self.topWaterLayer += \
                            self.landCoverObj[coverType].topWaterLayer*\
                            self.landCoverObj[coverType].fracVegCover
            self.storUpp000005  += \
                            self.landCoverObj[coverType].storUpp000005*\
                            self.landCoverObj[coverType].fracVegCover
            self.storUpp005030  += \
                            self.landCoverObj[coverType].storUpp005030*\
                            self.landCoverObj[coverType].fracVegCover
            self.storLow030150  += \
                            self.landCoverObj[coverType].storLow030150*\
                            self.landCoverObj[coverType].fracVegCover
                                         
    def obtainNonIrrWaterDemand(self,routing,currTimeStep):
        # get NON-Irrigation GROSS water demand and its return flow fraction

        # domestic water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.domesticWaterDemandOption: 
                #
                if self.domesticWaterDemandFile.endswith('.nc'):  
                    #
                    self.domesticGrossDemand = pcr.max(0.0, pcr.cover(\
                     vos.netcdf2PCRobjClone(self.domesticWaterDemandFile,\
                                                'domesticGrossDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0))
                    #
                    self.domesticNettoDemand = pcr.max(0.0, pcr.cover(\
                     vos.netcdf2PCRobjClone(self.domesticWaterDemandFile,\
                                                'domesticNettoDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0))
                else:
                    string_month = str(currTimeStep.month)
                    if currTimeStep.month < 10: string_month = "0"+str(currTimeStep.month)
                    grossFileName = self.domesticWaterDemandFile+"w"+str(currTimeStep.year)+".0"+string_month
                    self.domesticGrossDemand = pcr.max(pcr.cover(\
                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
                    nettoFileName = self.domesticWaterDemandFile+"n"+str(currTimeStep.year)+".0"+string_month
                    self.domesticNettoDemand = pcr.max(pcr.cover(\
                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
            else:
                self.domesticGrossDemand = pcr.scalar(0.0)
                self.domesticNettoDemand = pcr.scalar(0.0)
                logger.debug("Domestic water demand is not included.")
            
            # gross and netto domestic water demand in m/day
            self.domesticGrossDemand = pcr.cover(self.domesticGrossDemand,0.0)
            self.domesticNettoDemand = pcr.cover(self.domesticNettoDemand,0.0)
            self.domesticNettoDemand = pcr.min(self.domesticGrossDemand, self.domesticNettoDemand)  

        # industry water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.industryWaterDemandOption: 
                #
                if self.industryWaterDemandFile.endswith('.nc'):  
                    #
                    self.industryGrossDemand = pcr.max(0.0, pcr.cover(\
                     vos.netcdf2PCRobjClone(self.industryWaterDemandFile,\
                                                'industryGrossDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0))
                    #
                    self.industryNettoDemand = pcr.max(0.0, pcr.cover(\
                     vos.netcdf2PCRobjClone(self.industryWaterDemandFile,\
                                                'industryNettoDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0))
                else:
                    grossFileName = self.industryWaterDemandFile+"w"+str(currTimeStep.year)+".map"
                    self.industryGrossDemand = pcr.max(0.0, pcr.cover(\
                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0))
                    nettoFileName = self.industryWaterDemandFile+"n"+str(currTimeStep.year)+".map"
                    self.industryNettoDemand = pcr.max(0.0, pcr.cover(\
                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0))
            else:
                self.industryGrossDemand = pcr.scalar(0.0)
                self.industryNettoDemand = pcr.scalar(0.0)
                logger.debug("Industry water demand is not included.")
        
            # gross and netto industrial water demand in m/day
            self.industryGrossDemand = pcr.cover(self.industryGrossDemand,0.0)
            self.industryNettoDemand = pcr.cover(self.industryNettoDemand,0.0)
            self.industryNettoDemand = pcr.min(self.industryGrossDemand, self.industryNettoDemand)  

        # livestock water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1:
            if self.livestockWaterDemandOption: 
                #
                if self.livestockWaterDemandFile.endswith('.nc'):  
                    #
                    self.livestockGrossDemand = pcr.max(0.0, pcr.cover(\
                     vos.netcdf2PCRobjClone(self.livestockWaterDemandFile,\
                                                'livestockGrossDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0))
                    #
                    self.livestockNettoDemand = pcr.max(0.0, pcr.cover(\
                     vos.netcdf2PCRobjClone(self.livestockWaterDemandFile,\
                                                'livestockNettoDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0))
                else:
                    string_month = str(currTimeStep.month)
                    if currTimeStep.month < 10: string_month = "0"+str(currTimeStep.month)
                    grossFileName = self.livestockWaterDemandFile+"w"+str(currTimeStep.year)+".0"+string_month
                    self.livestockGrossDemand = pcr.max(pcr.cover(\
                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
                    nettoFileName = self.livestockWaterDemandFile+"n"+str(currTimeStep.year)+".0"+string_month
                    self.livestockNettoDemand = pcr.max(pcr.cover(\
                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0), 0.0)
            else:
                self.livestockGrossDemand = pcr.scalar(0.0)
                self.livestockNettoDemand = pcr.scalar(0.0)
                logger.debug("livestock water demand is not included.")
            
            # gross and netto livestock water demand in m/day
            self.livestockGrossDemand = pcr.cover(self.livestockGrossDemand,0.0)
            self.livestockNettoDemand = pcr.cover(self.livestockNettoDemand,0.0)
            self.livestockNettoDemand = pcr.min(self.livestockGrossDemand, self.livestockNettoDemand)  

        self.domesticGrossDemand  = pcr.ifthen(self.landmask, self.domesticGrossDemand )
        self.domesticNettoDemand  = pcr.ifthen(self.landmask, self.domesticNettoDemand )
        self.industryGrossDemand  = pcr.ifthen(self.landmask, self.industryGrossDemand )
        self.industryNettoDemand  = pcr.ifthen(self.landmask, self.industryNettoDemand )
        self.livestockGrossDemand = pcr.ifthen(self.landmask, self.livestockGrossDemand)
        self.livestockNettoDemand = pcr.ifthen(self.landmask, self.livestockNettoDemand)
        
        # total (potential) non irrigation water demand
        potentialNonIrrGrossWaterDemand = self.domesticGrossDemand + self.industryGrossDemand + self.livestockGrossDemand
        potentialNonIrrNettoWaterDemand = pcr.min(potentialNonIrrGrossWaterDemand,\
                                          self.domesticNettoDemand + self.industryNettoDemand + self.livestockNettoDemand)
        
        # fraction of return flow from domestic and industrial water demand
        nonIrrReturnFlowFraction = vos.getValDivZero(\
         (potentialNonIrrGrossWaterDemand - potentialNonIrrNettoWaterDemand),\
         (potentialNonIrrGrossWaterDemand), vos.smallNumber)
        nonIrrReturnFlowFraction = pcr.cover(pcr.min(1.0, pcr.roundup(nonIrrReturnFlowFraction*1000.)/1000.), 1.0)
        # Note that in part with (almost) no demand, we assume 100% return flow
        
        return potentialNonIrrGrossWaterDemand, nonIrrReturnFlowFraction 

    def calculateCapRiseFrac(self,groundwater,routing,currTimeStep):
        # calculate cell fraction influenced by capillary rise:

        # approximate cell fraction under influence of capillary rise
        dzGroundwater = groundwater.storGroundwater/groundwater.specificYield + self.parameters.maxGWCapRise;
        FRACWAT = pcr.scalar(0.0);
        if currTimeStep.timeStepPCR > 1: 
            FRACWAT = pcr.cover(routing.WaterBodies.fracWat, 0.0); 
        else:
            if routing.includeWaterBodies:
                if routing.WaterBodies.useNetCDF:
                    routing.WaterBodies.fracWat = vos.netcdf2PCRobjClone(\
                                routing.WaterBodies.ncFileInp,'fracWaterInp', \
                                currTimeStep.fulldate, useDoy = 'yearly',\
                                cloneMapFileName = self.cloneMap)
                else:
                    routing.WaterBodies.fracWat = vos.readPCRmapClone(\
                                routing.WaterBodies.fracWaterInp+str(currTimeStep.year)+".map",
                                self.cloneMap,self.tmpDir,self.inputDir)
        FRACWAT = pcr.cover(FRACWAT, 0.0)
        
        CRFRAC = pcr.min(                                           1.0,1.0 -(self.parameters.dzRel0100-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0100-self.parameters.dzRel0090       ));
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0090,0.9 -(self.parameters.dzRel0090-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0090-self.parameters.dzRel0080),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0080,0.8 -(self.parameters.dzRel0080-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0080-self.parameters.dzRel0070),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0070,0.7 -(self.parameters.dzRel0070-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0070-self.parameters.dzRel0060),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0060,0.6 -(self.parameters.dzRel0060-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0060-self.parameters.dzRel0050),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0050,0.5 -(self.parameters.dzRel0050-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0050-self.parameters.dzRel0040),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0040,0.4 -(self.parameters.dzRel0040-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0040-self.parameters.dzRel0030),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0030,0.3 -(self.parameters.dzRel0030-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0030-self.parameters.dzRel0020),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0020,0.2 -(self.parameters.dzRel0020-dzGroundwater)*0.1 /pcr.max(1e-3,self.parameters.dzRel0020-self.parameters.dzRel0010),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0010,0.1 -(self.parameters.dzRel0010-dzGroundwater)*0.05/pcr.max(1e-3,self.parameters.dzRel0010-self.parameters.dzRel0005),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0005,0.05-(self.parameters.dzRel0005-dzGroundwater)*0.04/pcr.max(1e-3,self.parameters.dzRel0005-self.parameters.dzRel0001),CRFRAC);
        CRFRAC = pcr.ifthenelse(dzGroundwater<self.parameters.dzRel0001,0.01-(self.parameters.dzRel0001-dzGroundwater)*0.01/pcr.max(1e-3,self.parameters.dzRel0001),CRFRAC);

        CRFRAC = pcr.ifthenelse(FRACWAT < 1.0,pcr.max(0.0,CRFRAC-FRACWAT)/(1-FRACWAT),0.0);
        #
        capRiseFrac = pcr.max(0.0,pcr.min(1.0,CRFRAC))
        return capRiseFrac

    def partitioningGroundSurfaceAbstraction(self,groundwater,routing):

        # partitioning abstraction sources: groundwater and surface water
        # Inge's principle: partitioning based on local average baseflow (m3/s) and upstream average discharge (m3/s) 
        #
        # estimates of fractions of groundwater and surface water abstractions 
        averageBaseflowInput = routing.avgBaseflow
        averageUpstreamInput = pcr.max(routing.avgDischarge, pcr.cover(pcr.upstream(routing.lddMap, routing.avgDischarge), 0.0))
        
        if self.usingAllocSegments:
            
            averageBaseflowInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageBaseflowInput))
            averageUpstreamInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageUpstreamInput))
            
            averageBaseflowInput = pcr.cover(pcr.areaaverage(averageBaseflowInput, self.allocSegments), 0.0)
            averageUpstreamInput = pcr.cover(pcr.areamaximum(averageUpstreamInput, self.allocSegments), 0.0)

        else:
            logger.debug("Water demand can only be satisfied by local source.")

        swAbstractionFraction = vos.getValDivZero(\
                                averageUpstreamInput, 
                                averageUpstreamInput+averageBaseflowInput, vos.smallNumber)
        swAbstractionFraction = pcr.roundup(swAbstractionFraction*100.)/100.
        swAbstractionFraction = pcr.max(0.0, swAbstractionFraction)
        swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)

        #~ # Assume that if swAbstractionFraction > 70% , the potential of using surface water as its primary source is very high
        #~ swAbstractionFraction = pcr.ifthenelse(swAbstractionFraction > 0.7, 1.0, swAbstractionFraction)
        #~ swAbstractionFraction = pcr.roundup(swAbstractionFraction*10.)/10.
        #~ swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)
        
        #~ # Assume that if swAbstractionFraction > 20% , the potential of using surface water as its primary source is very high
        #~ swAbstractionFraction = pcr.ifthenelse(swAbstractionFraction > 0.2, 1.0, swAbstractionFraction)
        #~ swAbstractionFraction = pcr.roundup(swAbstractionFraction*10.)/10.
        #~ swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)

        if self.usingAllocSegments:
            swAbstractionFraction = pcr.areamaximum(swAbstractionFraction, self.allocSegments)
            
        #~ # a new idea by Edwin: - not used in IWMI project
        #~ # - if regional limit of groundwater abstraction is used: 
        #~ # - we set the first priority is groundwater, 
        #~ #   but this groundwater abstraction is limited by regional groundwater abstraction
        #~ if groundwater.limitRegionalAnnualGroundwaterAbstraction:
            #~ swAbstractionFraction = pcr.scalar(0.0)

        swAbstractionFraction = pcr.cover(swAbstractionFraction, 1.0)
        swAbstractionFraction = pcr.ifthen(self.landmask, swAbstractionFraction)
        
        # incorporating the predefined fraction of surface water source:  
        if not isinstance(self.swAbstractionFractionData,types.NoneType):
            
            logger.debug('Using/incorporating the predefined fractions of surface water source.')
            
            swAbstractionFractionDict = {}
            swAbstractionFractionDict['estimate']             = swAbstractionFraction
            swAbstractionFractionDict['irrigation']           = self.partitioningGroundSurfaceAbstractionForIrrigation(swAbstractionFraction,\
                                                                                                                  self.swAbstractionFractionData,\
                                                                                                                  self.swAbstractionFractionDataQuality)
            swAbstractionFractionDict['max_for_non_irrigation'] = self.maximumNonIrrigationSurfaceWaterAbstractionFractionData
            
            swAbstractionFractionDict['livestockWaterDemand'] = self.livestockGrossDemand   # unit: m/day
            swAbstractionFraction = swAbstractionFractionDict
        
        else:    
            
            logger.debug('Not using/incorporating the predefined fractions of surface water source.')

        return swAbstractionFraction

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

    def scaleDynamicIrrigation(self,yearInInteger):
        # This method is to update fracVegCover of landCover for historical irrigation areas (done at yearly basis).
        
        
        #~ # Available datasets are only from 1960 to 2010 (status on 24 September 2010)
        #~ yearInInteger = int(yearInInteger)
        #~ if float(yearInInteger) < 1960. or float(yearInInteger) > 2010.:
            #~ msg = 'Dataset for the year '+str(yearInInteger)+" is not available. Dataset of historical irrigation areas is only available from 1960 to 2010."
            #~ logger.warning(msg)
        #~ yearInInteger = min(2010, max(1960, yearInInteger))
        #
        # TODO: Generally, I do not need the aforementioned lines as I have defined the functions "findLastYearInNCTime" and "findFirstYearInNCTime" in the module virtualOS.py
        #       However, Niko still need them for his DA scheme as we somehow his DA scheme cannot handle the netcdf file of historical irrigation areas (and therefore we have to use pcraster map files). 
        

        yearInString   = str(yearInInteger) 
        
        # read historical irrigation areas  
        if self.dynamicIrrigationAreaFile.endswith(('.nc4','.nc')):
            fulldateInString = yearInString+"-01"+"-01"   
            self.irrigationArea = 10000. * pcr.cover(\
                 vos.netcdf2PCRobjClone(self.dynamicIrrigationAreaFile,\
                                            'irrigationArea',\
                     fulldateInString, useDoy = 'yearly',\
                             cloneMapFileName = self.cloneMap), 0.0)        # unit: m2 (input file is in hectare)
        else:
            irrigation_pcraster_file = self.dynamicIrrigationAreaFile + yearInString + ".map"
            logger.debug('reading irrigation area map from : '+irrigation_pcraster_file)
            self.irrigationArea = 10000. * pcr.cover(\
                 vos.readPCRmapClone(irrigation_pcraster_file,\
                                   self.cloneMap,self.tmpDir), 0.0)         # unit: m2 (input file is in hectare)
        
        # TODO: Convert the input file, from hectare to percentage. 
        # This is to avoid errors if somebody uses 30 min input to run his 5 min model.
        
        # area of irrigation is limited by cellArea
        self.irrigationArea = pcr.max(self.irrigationArea, 0.0)              
        self.irrigationArea = pcr.min(self.irrigationArea, self.cellArea)   # limited by cellArea
        
        # calculate fracVegCover (for irrigation only)
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                
                self.landCoverObj[coverType].fractionArea = 0.0    # reset 
                self.landCoverObj[coverType].fractionArea = self.landCoverObj[coverType].irrTypeFracOverIrr * self.irrigationArea # unit: m2
                self.landCoverObj[coverType].fracVegCover = pcr.min(1.0, self.landCoverObj[coverType].fractionArea/ self.cellArea) 

                # avoid small values
                self.landCoverObj[coverType].fracVegCover = pcr.rounddown(self.landCoverObj[coverType].fracVegCover * 1000.)/1000.

        # rescale land cover fractions (for all land cover types):
        self.scaleModifiedLandCoverFractions()
        
    def update(self,meteo,groundwater,routing,currTimeStep):
        
        # updating regional groundwater abstraction limit (at the begining of the year or at the beginning of simulation)
        if groundwater.limitRegionalAnnualGroundwaterAbstraction:

            logger.debug('Total groundwater abstraction is limited by regional annual pumping capacity.')
            if currTimeStep.doy == 1 or currTimeStep.timeStepPCR == 1:
            
                self.groundwater_pumping_region_ids = \
                     pcr.ifthen(self.landmask,\
                     pcr.nominal(
                     vos.netcdf2PCRobjClone(groundwater.pumpingCapacityNC,'region_ids',\
                         currTimeStep.fulldate, useDoy = 'yearly', cloneMapFileName = self.cloneMap)))

                self.regionalAnnualGroundwaterAbstractionLimit = \
                     pcr.ifthen(self.landmask,\
                     pcr.cover(\
                     vos.netcdf2PCRobjClone(groundwater.pumpingCapacityNC,'regional_pumping_limit',\
                         currTimeStep.fulldate, useDoy = 'yearly', cloneMapFileName = self.cloneMap), 0.0))
            
                #~ self.regionalAnnualGroundwaterAbstractionLimit = pcr.roundup(self.regionalAnnualGroundwaterAbstractionLimit*1000000.)/1000000.
                #~ self.regionalAnnualGroundwaterAbstractionLimit = pcr.roundup(self.regionalAnnualGroundwaterAbstractionLimit)
                self.regionalAnnualGroundwaterAbstractionLimit = pcr.areamaximum(self.regionalAnnualGroundwaterAbstractionLimit, self.groundwater_pumping_region_ids)
            
                self.regionalAnnualGroundwaterAbstractionLimit *= 1000. * 1000. * 1000. # unit: m3/year
                self.regionalAnnualGroundwaterAbstractionLimit  = pcr.ifthen(self.landmask,\
                                                                         self.regionalAnnualGroundwaterAbstractionLimit)
                # minimum value (unit: m3/year at regional scale)
                minimum_value = 0.001 * 1000. * 1000. * 1000.
                self.regionalAnnualGroundwaterAbstractionLimit  = pcr.max(minimum_value,\
                                                                  self.regionalAnnualGroundwaterAbstractionLimit)                                                         
        else:
            logger.debug('Total groundwater abstraction is NOT limited by regional annual pumping capacity.')
            self.groundwater_pumping_region_ids = None
            self.regionalAnnualGroundwaterAbstractionLimit = None
        
        # updating fracVegCover of each landCover (landCover fraction) 
        # - if considering dynamic/historical irrigation areas (expansion/reduction of irrigated areas)
        # - done at yearly basis, at the beginning of each year
        # - note, for the first time step (timeStepPCR == 1), land cover fractions have been defined in getInitialConditions
        #
        if self.dynamicIrrigationArea and self.includeIrrigation and \
          (currTimeStep.timeStepPCR > 1 and currTimeStep.doy == 1):     
            #   
            # scale land cover fraction (due to expansion/reduction of irrigated areas)
            self.scaleDynamicIrrigation(currTimeStep.year)

        # transfer some states, due to changes/dynamics in land cover conditions
        # - if considering dynamic/historical irrigation areas (expansion/reduction of irrigated areas)
        # - done at yearly basis, at the beginning of each year
        # - note that this must be done at the beginning of each year, including for the first time step (timeStepPCR == 1)
        #
        if self.dynamicIrrigationArea and self.includeIrrigation and currTimeStep.doy == 1:
            #
            # loop for all main states:
            for var in self.mainStates:
                
                logger.info("Transfering states for the variable "+str(var))

                moving_fraction = pcr.scalar(0.0)                       # total land cover fractions that will be transferred
                moving_states   = pcr.scalar(0.0)                       # total states that will be transferred
                
                for coverType in self.coverTypes:
                    
                    old_fraction = self.landCoverObj[coverType].previousFracVegCover
                    new_fraction = self.landCoverObj[coverType].fracVegCover
                    
                    moving_fraction += pcr.max(0.0, old_fraction-new_fraction)
                    moving_states   += pcr.max(0.0, old_fraction-new_fraction) * vars(self.landCoverObj[coverType])[var]

                previous_state = pcr.scalar(0.0)
                rescaled_state = pcr.scalar(0.0)
                
                # correcting states
                for coverType in self.coverTypes:
                    
                    old_states   = vars(self.landCoverObj[coverType])[var]
                    old_fraction = self.landCoverObj[coverType].previousFracVegCover
                    new_fraction = self.landCoverObj[coverType].fracVegCover
                    
                    correction   = moving_states *\
                                   vos.getValDivZero( pcr.max(0.0, new_fraction - old_fraction),\
                                                      moving_fraction, vos.smallNumber )
                     
                    new_states   = pcr.ifthenelse(new_fraction > old_fraction, 
                                   vos.getValDivZero( 
                                   old_states * old_fraction + correction, \
                                   new_fraction, vos.smallNumber), old_states) 
                    
                    new_states   = pcr.ifthenelse(new_fraction > 0.0, new_states, pcr.scalar(0.0))
                    
                    vars(self.landCoverObj[coverType])[var] = new_states

                    previous_state += old_fraction * old_states
                    rescaled_state += new_fraction * new_states
            
                # check and make sure that previous_state == rescaled_state
                check_map = previous_state - rescaled_state
                a,b,c = vos.getMinMaxMean(check_map)
                threshold = 1e-5
                if abs(a) > threshold or abs(b) > threshold:
                    logger.warning("Error in transfering states (due to dynamic in land cover fractions) ... Min %f Max %f Mean %f" %(a,b,c))
                else:     
                    logger.info("Successful in transfering states (after change in land cover fractions) ... Min %f Max %f Mean %f" %(a,b,c))
        #
        # for the last day of the year, we have to save the previous land cover fractions (to be considered in the next time step) 
        if self.dynamicIrrigationArea and self.includeIrrigation and currTimeStep.isLastDayOfYear:     
            # save the current state of fracVegCover
            for coverType in self.coverTypes:\
                self.landCoverObj[coverType].previousFracVegCover = self.landCoverObj[coverType].fracVegCover

        # calculate cell fraction influenced by capillary rise:
        self.capRiseFrac = self.calculateCapRiseFrac(groundwater,routing,currTimeStep)
            
        # get domestic and industrial water demand, including their (combined) return flow fraction
        self.potentialNonIrrGrossWaterDemand, self.nonIrrReturnFlowFraction = \
             self.obtainNonIrrWaterDemand(routing, currTimeStep)
        
        # partitioning abstraction sources: groundwater and surface water
        self.swAbstractionFraction = \
             self.partitioningGroundSurfaceAbstraction(groundwater,routing)
        
        # get desalination water use (m/day) ; assume this one as potential supply
        if self.includeDesalination: 
            logger.debug("Monthly desalination water use is included.")
            if (currTimeStep.timeStepPCR == 1 or currTimeStep.day == 1):
                desalinationWaterUse = \
                     pcr.ifthen(self.landmask,\
                     pcr.cover(\
                     vos.netcdf2PCRobjClone(self.desalinationWaterFile,'desalination_water_use',\
                         currTimeStep.fulldate, useDoy = 'monthly', cloneMapFileName = self.cloneMap), 0.0))
                self.desalinationWaterUse = pcr.max(0.0, desalinationWaterUse)
        else:    
            logger.debug("Monthly desalination water use is NOT included.")
            self.desalinationWaterUse = pcr.scalar(0.0)
        
        # update (loop per each land cover type):
        for coverType in self.coverTypes:
            
            # minimum crop coefficient for irrigation
            minCropCoefficientForIrrigation = 0.0
            
            logger.info("Updating land cover: "+str(coverType))
            #~ print(coverType)
            self.landCoverObj[coverType].updateLC(meteo,groundwater,routing,\
                                                  self.parameters,self.capRiseFrac,\
                                                  self.potentialNonIrrGrossWaterDemand,\
                                                  self.swAbstractionFraction,\
                                                  currTimeStep,\
                                                  self.allocSegments,\
                                                  self.desalinationWaterUse,\
                                                  self.groundwater_pumping_region_ids,self.regionalAnnualGroundwaterAbstractionLimit,
                                                  minCropCoefficientForIrrigation)
            
            #~ # saving minimum cropKC for irrigation
            #~ if self.includeIrrigation and coverType == "grassland": minCropCoefficientForIrrigation = self.landCoverObj[coverType]

        # first, we set all aggregated values/variables to zero: 
        for var in self.aggrVars: vars(self)[var] = pcr.scalar(0.0)
        #
        # get or calculate the values of all aggregated values/variables
        for coverType in self.coverTypes:
            # calculate the aggregrated or global landSurface values: 
            for var in self.aggrVars:
                vars(self)[var] += \
                     self.landCoverObj[coverType].fracVegCover * vars(self.landCoverObj[coverType])[var]
                     
        # total storages (unit: m3) in the entire landSurface module
        if self.numberOfSoilLayers == 2: self.totalSto = \
                        self.snowCoverSWE + self.snowFreeWater + self.interceptStor +\
                        self.topWaterLayer +\
                        self.storUpp +\
                        self.storLow
        #
        if self.numberOfSoilLayers == 3: self.totalSto = \
                        self.snowCoverSWE + self.snowFreeWater + self.interceptStor +\
                        self.topWaterLayer +\
                        self.storUpp000005 + self.storUpp005030 +\
                        self.storLow030150

        # saturation degrees (needed only for reporting):
        #
        if self.numberOfSoilLayers == 2:
            self.satDegUpp = vos.getValDivZero(\
                  self.storUpp, self.parameters.storCapUpp,\
                  vos.smallNumber,0.)
            self.satDegUpp = pcr.ifthen(self.landmask, self.satDegUpp)
            self.satDegLow = vos.getValDivZero(\
                  self.storLow, self.parameters.storCapLow,\
                  vos.smallNumber,0.)
            self.satDegLow = pcr.ifthen(self.landmask, self.satDegLow)

            self.satDegUppTotal = self.satDegUpp
            self.satDegLowTotal = self.satDegLow

        if self.numberOfSoilLayers == 3:
            self.satDegUpp000005 = vos.getValDivZero(\
                  self.storUpp000005, self.parameters.storCapUpp000005,\
                  vos.smallNumber,0.)
            self.satDegUpp000005 = pcr.ifthen(self.landmask, self.satDegUpp000005)
            self.satDegUpp005030 = vos.getValDivZero(\
                  self.storUpp005030, self.parameters.storCapUpp005030,\
                  vos.smallNumber,0.)
            self.satDegUpp005030 = pcr.ifthen(self.landmask, self.satDegUpp005030)
            self.satDegLow030150 = vos.getValDivZero(\
                  self.storLow030150, self.parameters.storCapLow030150,\
                  vos.smallNumber,0.)
            self.satDegLow030150 = pcr.ifthen(self.landmask, self.satDegLow030150)

            self.satDegUppTotal  = vos.getValDivZero(\
                  self.storUpp000005 + self.storUpp005030,\
                  self.parameters.storCapUpp000005 + \
                  self.parameters.storCapUpp005030,\
                  vos.smallNumber,0.)
            self.satDegUppTotal = pcr.ifthen(self.landmask, self.satDegUppTotal)
            self.satDegLowTotal = self.satDegLow030150

        # old-style reporting                             
        self.old_style_land_surface_reporting(currTimeStep)             # TODO: remove this one

    def old_style_land_surface_reporting(self,currTimeStep):

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
