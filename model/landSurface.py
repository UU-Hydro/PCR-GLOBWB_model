#!/usr/bin/python
# -*- coding: utf-8 -*-

import pcraster as pcr
import virtualOS as vos
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

    def __init__(self,iniItems,landmask,spinUp):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask

        # get cellArea:                                                 # TODO: integrate this one with the one coming from the routing module
        self.cellArea = vos.readPCRmapClone(\
          iniItems.routingOptions['cellAreaMap'],
          self.cloneMap,self.tmpDir,self.inputDir)
        self.cellArea = pcr.ifthen(self.landmask, self.cellArea)
        
        # number of soil layers:
        self.numberOfSoilLayers = int(iniItems.landSurfaceOptions['numberOfUpperSoilLayers'])
        
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

        # limitAbstraction
        self.limitAbstraction = iniItems.landSurfaceOptions['limitAbstraction']

        # non irrigation water demand options: 
        self.waterDemandOptions(iniItems)
        
        # instantiate self.landCoverObj[coverType]
        self.landCoverObj = {} # initialize land cover objects
        for coverType in self.coverTypes:
            self.landCoverObj[coverType] = lc.LandCover(iniItems,\
                                                        str(coverType)+'Options',\
                                                        self.parameters,self.landmask,self.usingAllocSegments)                                   
        
        # rescale landCover Fractions
        self.scaleNaturalLandCoverFractions()
        if self.includeIrrigation: self.scaleModifiedLandCoverFractions()
        
        # if using historical/dynamic irrigation file (changing every year), we have to get fraction over irrigation area 
        #                                                                   (in order to calculate irrigation area for each irrigation type)
        if self.includeIrrigation and self.dynamicIrrigationArea:
            
            # total irrigated area fraction (over the entire cell) 
            totalIrrAreaFrac = 0.0 
            for coverType in self.coverTypes:
                if coverType.startswith('irr'):
                    totalIrrAreaFrac += self.landCoverObj[coverType].fracVegCover
            
            # fraction over irrigation area 
            for coverType in self.coverTypes:
                if coverType.startswith('irr'):
                    self.landCoverObj[coverType].irrTypeFracOverIrr = self.landCoverObj[coverType].fracVegCover / pcr.max(1E-9, totalIrrAreaFrac) 

        # Get the initialconditions
        self.getInitialConditions(iniItems, spinUp)

        self.report = True
        if self.report == True:
            # daily output in netCDF files:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            #
            self.outDailyTotNC = iniItems.landSurfaceOptions['outDailyTotNC'].split(",")
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_dailyTot.nc",\
                                                    var,"undefined")
            # MONTHly output in netCDF files:
            # - cummulative
            self.outMonthTotNC = iniItems.landSurfaceOptions['outMonthTotNC'].split(",")
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initiating monthlyVarTot (accumulator variable):
                    vars(self)[var+'MonthTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthTot.nc",\
                                                    var,"undefined")
            # - average
            self.outMonthAvgNC = iniItems.landSurfaceOptions['outMonthAvgNC'].split(",")
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
            self.outMonthEndNC = iniItems.landSurfaceOptions['outMonthEndNC'].split(",")
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthEnd.nc",\
                                                    var,"undefined")
            # YEARly output in netCDF files:
            # - cummulative
            self.outAnnuaTotNC = iniItems.landSurfaceOptions['outAnnuaTotNC'].split(",")
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:
                    # initiating yearly accumulator variable:
                    vars(self)[var+'AnnuaTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaTot.nc",\
                                                    var,"undefined")
            # - average
            self.outAnnuaAvgNC = iniItems.landSurfaceOptions['outAnnuaAvgNC'].split(",")
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
            self.outAnnuaEndNC = iniItems.landSurfaceOptions['outAnnuaEndNC'].split(",")
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaEnd.nc",\
                                                    var,"undefined")

        # list of aggregated variables that MUST be defined in the module:
        # - aggregated from landCover modules
        # - some are needed for water balance checking 
        # - some are needed in other modules (e.g. routing, groundwater)
        # - some are needed for initialConditions
        # 
        # state variables (unit: m)
        self.stateVars = ['interceptStor',
                          'snowCoverSWE','snowFreeWater',
                          'topWaterLayer',
                          'storUppTotal',
                          'storLowTotal']
        self.fluxVars  = ['infiltration','gwRecharge',
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
                          'potGroundwaterAbstract',
                          'actSurfaceWaterAbstract',
                          'allocSurfaceWaterAbstract',
                          'landSurfaceRunoff',
                          'totalPotET',
                          'satExcess']
        # 
        if self.numberOfSoilLayers == 2:
            self.stateVars += ['storUpp','storLow']
            self.fluxVars  += ['actTranspiUpp','actTranspiLow','netPercUpp']
        #                                                      
        if self.numberOfSoilLayers == 3:
            self.stateVars += ['storUpp000005','storUpp005030','storLow030150']
            self.fluxVars  += ['actTranspiUpp000005','actTranspiUpp005030','actTranspiLow030150',
                                  'netPercUpp000005',   'netPercUpp005030',
                                                      'interflowUpp005030']
        self.aggrVars = self.stateVars + self.fluxVars

    def getInitialConditions(self,iniItems,spinUp):

        # correcting (initial) landCover fractions:
        if self.dynamicIrrigationArea and self.includeIrrigation:\
           self.scaleDynamicIrrigation(iniItems.globalOptions['startTime'])

        # Get the initialconditions
        if self.numberOfSoilLayers == 2: self.getICsFor2Layers(iniItems, spinUp)
        if self.numberOfSoilLayers == 3: self.getICsFor3Layers(iniItems, spinUp)

    def waterDemandOptions(self,iniItems):

        # domestic water demand (unit: m/day)
        #
        self.domesticWaterDemandOption = False
        try:
            if iniItems.landSurfaceOptions['includeDomesticWaterDemand']  == "True":\
                 self.domesticWaterDemandOption = True  
        except:
            print("WARNING! Domestic water demand is not included in the calculation.")
        #
        if self.domesticWaterDemandOption:
            self.domesticWaterDemandFile = vos.getFullPath(\
             iniItems.landSurfaceOptions['domesticWaterDemandFile'],self.inputDir,False)

        # industry water demand (unit: m/day)
        #
        self.industryWaterDemandOption = False
        try:
            if iniItems.landSurfaceOptions['includeIndustryWaterDemand']  == "True":\
                 self.industryWaterDemandOption = True  
        except:
            print("WARNING! Industry water demand is not included in the calculation.")
        #
        if self.industryWaterDemandOption:
            self.industryWaterDemandFile = vos.getFullPath(\
             iniItems.landSurfaceOptions['industryWaterDemandFile'],self.inputDir,False)

        # historical irrigation area (unit: hectar)
        self.dynamicIrrigationArea = False
        try:
            if iniItems.landSurfaceOptions['historicalIrrigationArea'] != "None":
                self.dynamicIrrigationArea = True
            else:
                print("WARNING! Extent of irrigation areas is SAME for EVERY YEAR.")
        except:
            print("WARNING! Extent of irrigation areas is SAME for EVERY YEAR.")
        #
        if self.dynamicIrrigationArea:
            self.dynamicIrrigationAreaFile = vos.getFullPath(\
               iniItems.landSurfaceOptions['historicalIrrigationArea'],self.inputDir,False)
        
        # zones at which water allocation (surface and groundwater allocation) is determined
        self.usingAllocSegments = False
        self.allocSegments = None
        try:
            if iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater']  != "None":
                
                self.usingAllocSegments = True 
                
                self.allocSegments = vos.readPCRmapClone(\
                 iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater'],
                 self.cloneMap,self.tmpDir,self.inputDir,isLddMap=False,cover=None,isNomMap=True)
                self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)
                #~ self.allocSegments = pcr.clump(self.allocSegments)
                
                cellArea = vos.readPCRmapClone(\
                  iniItems.routingOptions['cellAreaMap'],
                  self.cloneMap,self.tmpDir,self.inputDir)
                cellArea = pcr.ifthen(self.landmask, cellArea)
                self.segmentArea = pcr.areatotal(pcr.cover(cellArea, 0.0), self.allocSegments)
                self.segmentArea = pcr.ifthen(self.landmask, self.segmentArea)
                 
            else:       
                print("WARNING! Water demand can only be satisfied by the local cell.")
        except:
            print("WARNING! Water demand can only be satisfied by the local cell.")

    def scaleNaturalLandCoverFractions(self): 
        ''' rescales natural land cover fractions (make sure the total = 1)'''

        pristineAreaFrac = 0.0 # start
        #
        # correcting 
        for coverType in self.coverTypes:         
            if not coverType.startswith('irr'):
                pristineAreaFrac += self.landCoverObj[coverType].fracVegCover
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
        a,b,c = vos.getMinMaxMean(totalArea - pcr.scalar(1.0))
        threshold = 1e-5
        if abs(a) > threshold or abs(b) > threshold:
            print "total of 'Natural Area' fractions is not equal to 1.0 ... Min %f Max %f Mean %f" %(a,b,c); 
            print ""

    def scaleModifiedLandCoverFractions(self): 
        ''' rescales the land cover fractions with irrigation areas'''

        totalArea         = pcr.spatial(pcr.scalar(0.0))
        irrigatedAreaFrac = pcr.spatial(pcr.scalar(0.0))

        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                irrigatedAreaFrac += \
                               self.landCoverObj[coverType].fracVegCover

        totalArea += irrigatedAreaFrac

        # correction factor for forest and grassland (pristine Areas)
        lcFrac = 1.0 - totalArea        
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
        a,b,c = vos.getMinMaxMean(totalArea - pcr.scalar(1.0))
        threshold = 1e-5
        if abs(a) > threshold or abs(b) > threshold:
            print "fraction total (from all land cover types) is not equal to 1.0 ... Min %f Max %f Mean %f" %(a,b,c); 
            print ""

    def getICsFor2Layers(self,iniItems,iniConditions = None):

        # first, we set the following aggregated storages to zero
        self.interceptStor = pcr.scalar(0.0)
        self.snowCoverSWE  = pcr.scalar(0.0)
        self.snowFreeWater = pcr.scalar(0.0)
        self.topWaterLayer = pcr.scalar(0.0)
        self.storUpp       = pcr.scalar(0.0)
        self.storLow       = pcr.scalar(0.0)

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
            self.storUpp       += \
                            self.landCoverObj[coverType].storUpp*\
                            self.landCoverObj[coverType].fracVegCover
            self.storLow       += \
                            self.landCoverObj[coverType].storLow*\
                            self.landCoverObj[coverType].fracVegCover

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
                    self.domesticGrossDemand = pcr.cover(\
                     vos.netcdf2PCRobjClone(self.domesticWaterDemandFile,\
                                                'domesticGrossDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0)
                    #
                    self.domesticNettoDemand = pcr.cover(\
                     vos.netcdf2PCRobjClone(self.domesticWaterDemandFile,\
                                                'domesticNettoDemand',\
                         currTimeStep.fulldate, useDoy = 'monthly',\
                                 cloneMapFileName = self.cloneMap), 0.0)
                else:
                    string_month = str(currTimeStep.month)
                    if currTimeStep.month < 10: string_month = "0"+str(currTimeStep.month)
                    grossFileName = self.domesticWaterDemandFile+"w"+str(currTimeStep.year)+".0"+string_month
                    self.domesticGrossDemand = pcr.cover(\
                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0)
                    nettoFileName = self.domesticWaterDemandFile+"n"+str(currTimeStep.year)+".0"+string_month
                    self.domesticNettoDemand = pcr.cover(\
                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0)
            else:
                self.domesticGrossDemand = pcr.scalar(0.0)
                self.domesticNettoDemand = pcr.scalar(0.0)
                print("WARNING! Domestic water demand is not included.")
            
            # avoid small values (less than 1 m3):
            self.domesticGrossDemand = pcr.ifthenelse(self.domesticGrossDemand > (1.0/routing.cellArea), self.domesticGrossDemand, 0)
            self.domesticNettoDemand = pcr.ifthenelse(self.domesticNettoDemand > (1.0/routing.cellArea), self.domesticNettoDemand, 0)    

        #
        # industry water demand
        if currTimeStep.timeStepPCR == 1 or currTimeStep.doy == 1:
            if self.industryWaterDemandOption: 
                #
                if self.industryWaterDemandFile.endswith('.nc'):  
                    #
                    self.industryGrossDemand = pcr.cover(\
                     vos.netcdf2PCRobjClone(self.industryWaterDemandFile,\
                                                'industryGrossDemand',\
                         currTimeStep.fulldate, useDoy = 'yearly',\
                                 cloneMapFileName = self.cloneMap), 0.0)
                    #
                    self.industryNettoDemand = pcr.cover(\
                     vos.netcdf2PCRobjClone(self.industryWaterDemandFile,\
                                                'industryNettoDemand',\
                         currTimeStep.fulldate, useDoy = 'yearly',\
                                 cloneMapFileName = self.cloneMap), 0.0)
                else:
                    grossFileName = self.industryWaterDemandFile+"w"+str(currTimeStep.year)+".map"
                    self.industryGrossDemand = pcr.cover(\
                                               vos.readPCRmapClone(grossFileName,self.cloneMap,self.tmpDir), 0.0)
                    nettoFileName = self.industryWaterDemandFile+"n"+str(currTimeStep.year)+".map"
                    self.industryNettoDemand = pcr.cover(\
                                               vos.readPCRmapClone(nettoFileName,self.cloneMap,self.tmpDir), 0.0)
            else:
                self.industryGrossDemand = pcr.scalar(0.0)
                self.industryNettoDemand = pcr.scalar(0.0)
                print("WARNING! Industry water demand is not included.")
        
            # avoid small values (less than 1 m3):
            self.industryGrossDemand = pcr.ifthenelse(self.domesticGrossDemand > (1.0/routing.cellArea), self.industryGrossDemand, 0)
            self.industryNettoDemand = pcr.ifthenelse(self.domesticNettoDemand > (1.0/routing.cellArea), self.industryNettoDemand, 0)    

        self.domesticGrossDemand = pcr.ifthen(self.landmask, self.domesticGrossDemand)
        self.domesticNettoDemand = pcr.ifthen(self.landmask, self.domesticNettoDemand)
        self.industryGrossDemand = pcr.ifthen(self.landmask, self.industryGrossDemand)
        self.industryNettoDemand = pcr.ifthen(self.landmask, self.industryNettoDemand)
        
        # total (potential) non irrigation water demand
        potentialNonIrrGrossWaterDemand = self.domesticGrossDemand + self.industryGrossDemand
        potentialNonIrrNettoWaterDemand = pcr.min(potentialNonIrrGrossWaterDemand,\
                                          self.domesticNettoDemand + self.industryNettoDemand)
        
        # fraction of return flow from domestic and industrial water demand
        nonIrrReturnFlowFraction = vos.getValDivZero(\
         (potentialNonIrrGrossWaterDemand - potentialNonIrrNettoWaterDemand),\
         (potentialNonIrrGrossWaterDemand), vos.smallNumber)
        
        return potentialNonIrrGrossWaterDemand, nonIrrReturnFlowFraction 

    def calculateCapRiseFrac(self,groundwater,routing,currTimeStep):
        # calculate cell fraction influenced by capillary rise:

        # approximate height of groundwater table and corresponding reach of cell under influence of capillary rise
        dzGroundwater = groundwater.storGroundwater/groundwater.specificYield + self.parameters.maxGWCapRise;
        FRACWAT = pcr.scalar(0.0);
        if currTimeStep.timeStepPCR > 1: 
            FRACWAT = pcr.cover(routing.WaterBodies.fracWat, 0.0); 
        else:
            if routing.includeWaterBodies == "True":
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
        averageBaseflowInput  = routing.avgBaseflow
        averageUpstreamInput  = pcr.upstream(routing.lddMap, routing.avgDischarge)
        
        if self.usingAllocSegments:
            
            averageBaseflowInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageBaseflowInput))
            averageUpstreamInput = pcr.max(0.0, pcr.ifthen(self.landmask, averageUpstreamInput))
            
            averageBaseflowInput = pcr.cover(pcr.areaaverage(pcr.cover(averageBaseflowInput, 0.0), self.allocSegments), 0.0)
            averageUpstreamInput = pcr.cover(pcr.areamaximum(pcr.cover(averageUpstreamInput, 0.0), self.allocSegments), 0.0)

        else:
            print("WARNING! Water demand can only be satisfied by local source.")

        swAbstractionFraction = pcr.max(0.0,\
                                pcr.min(1.0,\
                                averageUpstreamInput / \
                                pcr.max(1e-20,
                                averageUpstreamInput+averageBaseflowInput)))
        swAbstractionFraction = pcr.cover(swAbstractionFraction, 0.0)
        swAbstractionFraction = pcr.roundup(swAbstractionFraction*100.)/100.
        swAbstractionFraction = pcr.max(0.0, swAbstractionFraction)
        swAbstractionFraction = pcr.min(1.0, swAbstractionFraction)
        
        gwAbstractionFraction = 1.0 - swAbstractionFraction
        
        return swAbstractionFraction

    def scaleDynamicIrrigation(self,fulldateInString):

        # updating fracVegCover of landCover (for historical irrigation areas, done at yearly basis)

        # read historical irrigation areas  
        self.irrigationArea = 10000. * pcr.cover(\
                 vos.netcdf2PCRobjClone(self.dynamicIrrigationAreaFile,\
                                            'irrigationArea',\
                     fulldateInString, useDoy = 'yearly',\
                             cloneMapFileName = self.cloneMap), 0.0)         # unit: m2 (input file is in hectare)
        
        # area of irrigation is limited by cellArea
        self.irrigationArea = pcr.max(self.irrigationArea, 0.0)              
        self.irrigationArea = pcr.min(self.irrigationArea, self.cellArea)    # limited by cellArea
        
        # calculate fracVegCover (for irrigation only)
        for coverType in self.coverTypes:
            if coverType.startswith('irr'):
                
                self.landCoverObj[coverType].fractionArea = 0.0    # reset 
                self.landCoverObj[coverType].fractionArea = self.landCoverObj[coverType].irrTypeFracOverIrr * self.irrigationArea # unit: m2
                self.landCoverObj[coverType].fracVegCover = pcr.min(1.0, self.landCoverObj[coverType].fractionArea/ self.cellArea) 

                # avoid small values
                self.landCoverObj[coverType].fracVegCover = pcr.ifthenelse(\
                 self.landCoverObj[coverType].fracVegCover > 0.001, \
                 self.landCoverObj[coverType].fracVegCover, 0) 

        # rescale land cover fractions (for all land cover types):
        self.scaleModifiedLandCoverFractions()
        
        #~ # debug
        #~ total = self.landCoverObj['forest'].fracVegCover    +\
                #~ self.landCoverObj['grassland'].fracVegCover +\
                #~ self.landCoverObj['irrPaddy'].fracVegCover     +\
                #~ self.landCoverObj['irrNonPaddy'].fracVegCover
        #~ pcr.report(self.landCoverObj['forest'].fracVegCover     ,"f.map") 
        #~ pcr.report(self.landCoverObj['grassland'].fracVegCover  ,"g.map") 
        #~ pcr.report(self.landCoverObj['irrPaddy'].fracVegCover   ,"p.map") 
        #~ pcr.report(self.landCoverObj['irrNonPaddy'].fracVegCover,"np.map") 
        #~ pcr.report(total                                        ,"t.map")
        #~ os.system('aguila *.map') 
        #~ os.system('rm *.map') 


    def update(self,meteo,groundwater,routing,currTimeStep):
        
        # updating fracVegCover of landCover (for historical irrigation areas, done at yearly basis)
        if self.dynamicIrrigationArea and self.includeIrrigation and \
          (currTimeStep.timeStepPCR == 1 or currTimeStep.doy == 1):\
           self.scaleDynamicIrrigation(currTimeStep.fulldate)

        # calculate cell fraction influenced by capillary rise:
        self.capRiseFrac = self.calculateCapRiseFrac(groundwater,routing,currTimeStep)
            
        # get domestic and industrial water demand, including their (combined) return flow fraction
        self.potentialNonIrrGrossWaterDemand, self.nonIrrReturnFlowFraction = \
             self.obtainNonIrrWaterDemand(routing, currTimeStep)
        
        # partitioning abstraction sources: groundwater and surface water
        self.swAbstractionFraction = \
             self.partitioningGroundSurfaceAbstraction(groundwater,routing)
        
        # update (loop per each land cover type):
        for coverType in self.coverTypes:
            print(coverType)
            self.landCoverObj[coverType].updateLC(meteo,groundwater,routing,\
                                                  self.parameters,self.capRiseFrac,\
                                                  self.potentialNonIrrGrossWaterDemand,\
                                                  self.swAbstractionFraction,\
                                                  currTimeStep,\
                                                  allocSegments = self.allocSegments)

        # first, we set all aggregated values/variables to zero: 
        for var in self.aggrVars: vars(self)[var] = pcr.scalar(0.0)
        #
        # get or calculate the values of all aggregated values/variables
        for coverType in self.coverTypes:
            # calculate the aggregrated or global landSurface values: 
            for var in self.aggrVars:
                vars(self)[var] += \
                     self.landCoverObj[coverType].fracVegCover*\
                     vars(self.landCoverObj[coverType])[var]
                     
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
            self.satDegUppTotal = pcr.ifthen(self.landmask, self.satDegUppTotal)

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
