#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

import netCDF4 as nc
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

import virtualOS as vos
from ncConverter import *

class LandCover(object):

    def __init__(self,iniItems,NameOfSectionInIniFile,parameters,landmask,usingAllocSegments = False):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        self.landmask = landmask
        
        # limitAbstraction
        self.limitAbstraction = False
        if iniItems.landSurfaceOptions['limitAbstraction'] == "True": self.limitAbstraction = True
        
        # configuration for a certain land cover type
        self.iniItemsLC = iniItems.__getattribute__(NameOfSectionInIniFile)
        self.name = self.iniItemsLC['name']
        self.debugWaterBalance = self.iniItemsLC['debugWaterBalance']

        # get snow module type and its parameters:
        self.snowModuleType = self.iniItemsLC['snowModuleType']
        snowParams      = ['freezingT',
                           'degreeDayFactor',
                           'snowWaterHoldingCap',
                           'refreezingCoeff']
        for var in snowParams:
            input = self.iniItemsLC[str(var)]
            vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)

        # get landCovParams that are fixed for the entire simulation:
        landCovParams = ['minSoilDepthFrac','maxSoilDepthFrac',
                         'rootFraction1','rootFraction2',
                         'maxRootDepth',
                         'fracVegCover']
        if self.iniItemsLC['landCoverMapsNC'] == str(None):
            for var in landCovParams:
                input = self.iniItemsLC[str(var)]
                vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                self.tmpDir,self.inputDir)
                if input != "None":\
                   vars(self)[var] = pcr.cover(vars(self)[var],0.0)                                
        else:
            landCoverPropertiesNC = vos.getFullPath(\
                                    self.iniItemsLC['landCoverMapsNC'],\
                                    self.inputDir)
            for var in landCovParams:
                vars(self)[var] = vos.netcdf2PCRobjCloneWithoutTime(\
                                    landCoverPropertiesNC,var, \
                                    cloneMapFileName = self.cloneMap)
                vars(self)[var] = pcr.cover(vars(self)[var], 0.0)

        # avoid small values (in order to avoid rounding error)
        self.fracVegCover = pcr.cover(self.fracVegCover, 0.0)
        self.fracVegCover = pcr.rounddown(self.fracVegCover * 1000.)/1000.
        
        # limit 0.0 <= fracVegCover <= 1.0
        self.fracVegCover = pcr.max(0.0,self.fracVegCover)
        self.fracVegCover = pcr.min(1.0,self.fracVegCover)

        self.fractionArea         = None # area (m2) of a certain land cover type ; will be assigned by the landSurface module
        self.naturalFracVegCover  = None # fraction (-) of natural area over (entire) cell ; will be assigned by the landSurface module
        self.irrTypeFracOverIrr   = None # fraction (m2) of a certain irrigation type over (only) total irrigation area ; will be assigned by the landSurface module

        # previous fractions of land cover (needed while land cover changes ; for transfering fluxes)
        self.previousFracVegCover = None
        
        cellArea = vos.readPCRmapClone(\
          iniItems.routingOptions['cellAreaMap'],
          self.cloneMap,self.tmpDir,self.inputDir)
        cellArea = pcr.ifthen(self.landmask, cellArea)                  # TODO: integrate this one with the one coming from the routing module

        # irrigation / water allocation zones:
        self.usingAllocSegments = usingAllocSegments # water allocation option:
        if self.usingAllocSegments:

            self.allocSegments = vos.readPCRmapClone(\
             iniItems.landSurfaceOptions['allocationSegmentsForGroundSurfaceWater'],
             self.cloneMap,self.tmpDir,self.inputDir,isLddMap=False,cover=None,isNomMap=True)
            self.allocSegments = pcr.ifthen(self.landmask, self.allocSegments)

            #~ self.allocSegments = pcr.clump(self.allocSegments)       # According to Menno, "clump" is NOT recommended.

            self.segmentArea = pcr.areatotal(pcr.cover(cellArea, 0.0), self.allocSegments)
            self.segmentArea = pcr.ifthen(self.landmask, self.segmentArea)

        landCovParamsAdd = ['arnoBeta',
                            'minTopWaterLayer',
                            'minCropKC',
                            'minInterceptCap']
        for var in landCovParamsAdd:
            input = self.iniItemsLC[str(var)]
            vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)
            if input != "None":\
               vars(self)[var] = pcr.cover(vars(self)[var],0.0)                                
        # additional parameter(s) for irrigation Areas:
        if self.iniItemsLC['name'].startswith('irr'):
            input = self.iniItemsLC['cropDeplFactor']
            vars(self)['cropDeplFactor'] = \
                              vos.readPCRmapClone(input,self.cloneMap,
                                            self.tmpDir,self.inputDir)

        # Improved Arno's scheme parameters:
        if self.iniItemsLC['arnoBeta'] == "None":\
           self.arnoBeta = pcr.max(0.001,\
                (self.maxSoilDepthFrac-1.)/(1.-self.minSoilDepthFrac)+\
                                           parameters.orographyBeta-0.01)   # Rens's line: BCF[TYPE]= max(0.001,(MAXFRAC[TYPE]-1)/(1-MINFRAC[TYPE])+B_ORO-0.01)
        self.arnoBeta = pcr.max(0.001,self.arnoBeta)
        self.arnoBeta = pcr.cover(self.arnoBeta, 0.001)

        self.rootZoneWaterStorageMin   = self.minSoilDepthFrac * \
                               parameters.rootZoneWaterStorageCap
        self.rootZoneWaterStorageRange = \
                               parameters.rootZoneWaterStorageCap -\
                                         self.rootZoneWaterStorageMin

        self.numberOfLayers = parameters.numberOfLayers
        
        self.scaleRootFractions()
        self.calculateTotAvlWaterCapacityInRootZone(parameters)
        self.calculateParametersAtHalfTranspiration(parameters)

        # get the names of cropCoefficient files:
        self.cropCoefficientNC = vos.getFullPath(\
                    self.iniItemsLC['cropCoefficientNC'],self.inputDir)

        # get the names of interceptCap and coverFraction files:
        if not self.iniItemsLC['name'].startswith("irr"):
            self.interceptCapNC = vos.getFullPath(\
                       self.iniItemsLC['interceptCapNC'],self.inputDir)
            self.coverFractionNC = vos.getFullPath(\
                      self.iniItemsLC['coverFractionNC'],self.inputDir)

        # for reporting: output in netCDF files:
        self.report = True
        try:
            self.outDailyTotNC = self.iniItemsLC['outDailyTotNC'].split(",")
            self.outMonthTotNC = self.iniItemsLC['outMonthTotNC'].split(",")
            self.outMonthAvgNC = self.iniItemsLC['outMonthAvgNC'].split(",")
            self.outMonthEndNC = self.iniItemsLC['outMonthEndNC'].split(",")
        except:
            self.report = False
        if self.report:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            # prepare the netCDF objects and files:
            if self.outDailyTotNC[0] != "None":    
                for var in self.outDailyTotNC:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/" + \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                     "dailyTot.nc",\
                                     var,"undefined")
        
            # monthly output in netCDF files:
            # - cummulative
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initiating monthlyVarTot (accumulator variable):
                    vars(self)[var+'Tot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                                "monthTot.nc",\
                                                    var,"undefined")
            # - average
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # initiating monthlyVarAvg:
                    vars(self)[var+'Avg'] = None
                    # initiating monthlyTotAvg (accumulator variable)
                    vars(self)[var+'Tot'] = None
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                                "monthAvg.nc",\
                                                    var,"undefined")
            # - last day of the month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                                "monthEnd.nc",\
                                                    var,"undefined")


    def scaleRootFractions(self):
                                         
        if self.numberOfLayers == 2: 
            # root fractions
            rootFracUpp = (0.30/0.30) * self.rootFraction1
            rootFracLow = (1.20/1.20) * self.rootFraction2
            self.adjRootFrUpp = rootFracUpp / (rootFracUpp + rootFracLow)
            self.adjRootFrLow = rootFracLow / (rootFracUpp + rootFracLow)       # RFW1[TYPE]= RFRAC1[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE]);
            #                                                                   # RFW2[TYPE]= RFRAC2[TYPE]/(RFRAC1[TYPE]+RFRAC2[TYPE]);
            # if not defined, put everything in the first layer:
            self.adjRootFrUpp = pcr.cover(self.adjRootFrUpp,1.0) 
            self.adjRootFrLow = 1.0 - self.adjRootFrUpp 

        if self.numberOfLayers == 3: 
            # root fractions
            rootFracUpp000005 = 0.05/0.30 * self.rootFraction1
            rootFracUpp005030 = 0.25/0.30 * self.rootFraction1
            rootFracLow030150 = 1.20/1.20 * self.rootFraction2
            self.adjRootFrUpp000005 = rootFracUpp000005 / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)
            self.adjRootFrUpp005030 = rootFracUpp005030 / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)
            self.adjRootFrLow030150 = rootFracLow030150 / (rootFracUpp000005 + rootFracUpp005030 + rootFracLow030150)
            #
            # if not defined, put everything in the first layer:
            self.adjRootFrUpp000005 = pcr.cover(self.adjRootFrUpp000005,1.0) 
            self.adjRootFrUpp005030 = pcr.ifthenelse(self.adjRootFrUpp000005 < 1.0, self.adjRootFrUpp005030, 0.0) 
            self.adjRootFrLow030150 = 1.0 - (self.adjRootFrUpp000005 + self.adjRootFrUpp005030) 

    def calculateParametersAtHalfTranspiration(self,parameters):

        # average soil parameters at which actual transpiration is halved

        if self.numberOfLayers == 2: 

            self.effSatAt50 = \
                             (parameters.storCapUpp * \
                                  self.adjRootFrUpp * \
                             (parameters.matricSuction50/parameters.airEntryValueUpp)**\
                                                     (-1./parameters.poreSizeBetaUpp)  +\
                              parameters.storCapLow * \
                                  self.adjRootFrLow * \
                             (parameters.matricSuction50/parameters.airEntryValueLow)**\
                                                     (-1./parameters.poreSizeBetaLow)) /\
                         (parameters.storCapUpp*self.adjRootFrUpp +\
                          parameters.storCapLow*self.adjRootFrLow )     # THEFF_50[TYPE]= (SC1[TYPE]*RFW1[TYPE]*(PSI_50/PSI_A1[TYPE])**(-1/BCH1[TYPE]) +
                                                                        #                  SC2[TYPE]*RFW2[TYPE]*(PSI_50/PSI_A2[TYPE])**(-1/BCH2[TYPE])) /
                                                                        #                 (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]);
            self.effPoreSizeBetaAt50 = (\
                          parameters.storCapUpp*self.adjRootFrUpp*\
                                       parameters.poreSizeBetaUpp +\
                          parameters.storCapLow*self.adjRootFrLow*\
                                       parameters.poreSizeBetaLow) / (\
                         (parameters.storCapUpp*self.adjRootFrUpp +\
                          parameters.storCapLow*self.adjRootFrLow ))    # BCH_50 = (SC1[TYPE]*RFW1[TYPE]*BCH1[TYPE]+SC2[TYPE]*RFW2[TYPE]*BCH2[TYPE])/
                                                                        #          (SC1[TYPE]*RFW1[TYPE]+SC2[TYPE]*RFW2[TYPE]);

        if self.numberOfLayers == 3: 
        
            self.effSatAt50 = (parameters.storCapUpp000005 * \
                                   self.adjRootFrUpp000005 * \
                              (parameters.matricSuction50/parameters.airEntryValueUpp000005)**\
                                                      (-1./parameters.poreSizeBetaUpp000005) +\
                               parameters.storCapUpp005030 * \
                                   self.adjRootFrUpp005030 * \
                              (parameters.matricSuction50/parameters.airEntryValueUpp000005)**\
                                                      (-1./parameters.poreSizeBetaUpp000005) +\
                               parameters.storCapLow030150 * \
                                   self.adjRootFrLow030150 * \
                              (parameters.matricSuction50/parameters.airEntryValueLow030150)**\
                                                      (-1./parameters.poreSizeBetaLow030150) /\
                         (parameters.storCapUpp000005*self.adjRootFrUpp000005 +\
                          parameters.storCapUpp005030*self.adjRootFrUpp005030 +\
                          parameters.storCapLow030150*self.adjRootFrLow030150 ))

            self.effPoreSizeBetaAt50 = (\
                          parameters.storCapUpp000005*self.adjRootFrUpp000005*\
                                             parameters.poreSizeBetaUpp000005 +\
                          parameters.storCapUpp005030*self.adjRootFrUpp005030*\
                                             parameters.poreSizeBetaUpp005030 +\
                          parameters.storCapLow030150*self.adjRootFrLow030150*\
                                             parameters.poreSizeBetaLow030150) / \
                         (parameters.storCapUpp000005*self.adjRootFrUpp000005 +\
                          parameters.storCapUpp005030*self.adjRootFrUpp005030 +\
                          parameters.storCapLow030150*self.adjRootFrLow030150 )

    def calculateTotAvlWaterCapacityInRootZone(self,parameters):

        # total water capacity in the root zone (upper soil layers)
        # Note: This is dependent on the land cover type.

        if self.numberOfLayers == 2: 

            self.totAvlWater = \
                               (pcr.max(0.,\
                               parameters.effSatAtFieldCapUpp - parameters.effSatAtWiltPointUpp))*\
                               (parameters.satVolMoistContUpp -   parameters.resVolMoistContUpp )*\
                        pcr.min(parameters.thickUpp,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                               parameters.effSatAtFieldCapLow - parameters.effSatAtWiltPointLow))*\
                               (parameters.satVolMoistContLow -   parameters.resVolMoistContLow )*\
                        pcr.min(parameters.thickLow,\
                        pcr.max(self.maxRootDepth-parameters.thickUpp,0.))      # Edwin modified this line. Edwin uses soil thickness thickUpp and thickLow (instead of storCapUpp and storCapLow). 
                                                                                # And Rens support this. 
            self.totAvlWater = pcr.min(self.totAvlWater, \
                            parameters.storCapUpp + parameters.storCapLow)

        if self.numberOfLayers == 3: 

            self.totAvlWater = \
                               (pcr.max(0.,\
                               parameters.effSatAtFieldCapUpp000005 - parameters.effSatAtWiltPointUpp000005))*\
                               (parameters.satVolMoistContUpp000005 -   parameters.resVolMoistContUpp000005 )*\
                        pcr.min(parameters.thickUpp000005,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                               parameters.effSatAtFieldCapUpp005030 - parameters.effSatAtWiltPointUpp005030))*\
                               (parameters.satVolMoistContUpp005030 -   parameters.resVolMoistContUpp005030 )*\
                        pcr.min(parameters.thickUpp005030,\
                        pcr.max(self.maxRootDepth-parameters.thickUpp000005))  + \
                               (pcr.max(0.,\
                               parameters.effSatAtFieldCapLow030150 - parameters.effSatAtWiltPointLow030150))*\
                               (parameters.satVolMoistContLow030150 -   parameters.resVolMoistContLow030150 )*\
                        pcr.min(parameters.thickLow030150,\
                        pcr.max(self.maxRootDepth-parameters.thickUpp005030,0.)) 
            #
            self.totAvlWater = pcr.min(self.totAvlWater, \
                               parameters.storCapUpp000005 + \
                               parameters.storCapUpp005030 + \
                               parameters.storCapLow030150)

        
    def getICsLC(self,iniItems,iniConditions = None):

        if self.numberOfLayers == 2: 
        
            # List of state and flux variables:
            initialVars  = ['interceptStor',
                            'snowCoverSWE','snowFreeWater',
                            'topWaterLayer',
                            'storUpp',
                            'storLow',
                            'interflow']
            for var in initialVars:
                if iniConditions == None:
                    input = self.iniItemsLC[str(var)+'Ini']
                    vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                    self.tmpDir,self.inputDir)
                    vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                else:
                    vars(self)[var] = iniConditions[str(var)]
                vars(self)[var] = pcr.ifthen(self.landmask,vars(self)[var])

        if self.numberOfLayers == 3: 

            # List of state and flux variables:
            initialVars  = ['interceptStor',
                            'snowCoverSWE','snowFreeWater',
                            'topWaterLayer',
                            'storUpp000005','storUpp005030',
                            'storLow030150',
                            'interflow']
            for var in initialVars:
                if iniConditions == None:
                    input = self.iniItemsLC[str(var)+'Ini']
                    vars(self)[var] = vos.readPCRmapClone(input,self.cloneMap,
                                                    self.tmpDir,self.inputDir,
                                                    cover = 0.0)
                    vars(self)[var] = pcr.cover(vars(self)[var], 0.0)
                else:
                    vars(self)[var] = iniConditions[str(var)]
                vars(self)[var] = pcr.ifthen(self.landmask,vars(self)[var])

    def updateLC(self,meteo,groundwater,routing,\
                 parameters,capRiseFrac,\
                 nonIrrGrossDemand,swAbstractionFraction,\
                 currTimeStep,
                 allocSegments):

        self.getPotET(meteo,currTimeStep)              # calculate total PotET (based on meteo and cropKC) 
        self.interceptionUpdate(meteo,currTimeStep)    # calculate interception and update storage	 

         # calculate snow melt (or refreezing)
        if self.snowModuleType  == "Simple": self.snowMeltHBVSimple(meteo,currTimeStep)
        # TODO: Define other snow modules

        # calculate qDR & qSF & q23 (and update storages)
        self.upperSoilUpdate(meteo,groundwater,routing,\
                             parameters,capRiseFrac,\
                             nonIrrGrossDemand,swAbstractionFraction,\
                             currTimeStep,\
                             allocSegments)

        if self.report == True:
            # writing Output to netcdf files
            # - daily output:
            timeStamp = datetime.datetime(currTimeStep.year,\
                                          currTimeStep.month,\
                                          currTimeStep.day,\
                                          0)
            timestepPCR = currTimeStep.timeStepPCR
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    self.netcdfObj.data2NetCDF(str(self.outNCDir)+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                     "dailyTot.nc",\
                                     var,\
                      pcr2numpy(self.__getattribute__(var),vos.MV),\
                                     timeStamp,timestepPCR-1)
        
            # writing monthly output to netcdf files
            # -cummulative
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # introduce variables at the beginning of simulation:
                    if currTimeStep.timeStepPCR == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                    # reset variables at the beginning of the month
                    if currTimeStep.day == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                    # accumulating
                    vars(self)[var+'Tot'] += vars(self)[var]
                    # reporting at the end of the month:
                    if currTimeStep.endMonth == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                         "monthTot.nc",\
                                      var,\
                          pcr2numpy(self.__getattribute__(var+'Tot'),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)
            # -average
            if self.outMonthAvgNC[0] != "None":
                for var in self.outMonthAvgNC:
                    # only if a accumulator variable has not been defined: 
                    if var not in self.outMonthTotNC: 
                        # introduce accumulator variables at the beginning of simulation:
                        if currTimeStep.timeStepPCR == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                        # reset variables at the beginning of the month
                        if currTimeStep.day == 1: vars(self)[var+'Tot'] = \
                                              pcr.scalar(0.0)
                        # accumulating
                        vars(self)[var+'Tot'] += vars(self)[var]
                    # calculating average and reporting at the end of the month:
                    if currTimeStep.endMonth == True:
                        vars(self)[var+'Avg'] = vars(self)[var+'Tot'] /\
                                                currTimeStep.day  
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                         "monthAvg.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var+'Avg'),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)
            # -last day of the month
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                    # reporting at the end of the month:
                    if currTimeStep.endMonth == True: 
                        self.netcdfObj.data2NetCDF(str(self.outNCDir)+"/"+ \
                                     str(var) + "_" + \
                                     str(self.iniItemsLC['name']) + "_" + \
                                         "monthEnd.nc",\
                                         var,\
                          pcr2numpy(self.__getattribute__(var),vos.MV),\
                                         timeStamp,currTimeStep.monthIdx-1)


    def getPotET(self,meteo,currTimeStep):

        # get crop coefficient:
        cropKC = vos.netcdf2PCRobjClone(self.cropCoefficientNC,'kc', \
                                    currTimeStep.doy, useDoy = 'Yes',\
                                    cloneMapFileName = self.cloneMap)
        self.cropKC = pcr.max( cropKC, self.minCropKC)                                

        # calculate potential ET (unit: m/day)
        self.totalPotET = pcr.ifthen(self.landmask,\
                                     self.cropKC * meteo.referencePotET)

        # calculate potential bare soil evaporation and transpiration (unit: m/day)
        self.potBareSoilEvap  = pcr.ifthen(self.landmask,\
                                self.minCropKC * meteo.referencePotET)
        self.potTranspiration = pcr.ifthen(self.landmask,\
                                self.cropKC    * meteo.referencePotET - self.potBareSoilEvap)
    
        if self.debugWaterBalance == str('True'):
            vos.waterBalanceCheck([self.totalPotET],\
                                  [self.potBareSoilEvap,self.potTranspiration],\
                                  [],\
                                  [],\
                                  'partitioning potential evaporation',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-5)

        # fraction of potential bare soil evaporation and transpiration
        self.fracPotBareSoilEvap  = vos.getValDivZero(self.potBareSoilEvap , self.totalPotET, vos.smallNumber)
        self.fracPotTranspiration = pcr.scalar(1.0 - self.fracPotBareSoilEvap)

    def interceptionUpdate(self,meteo,currTimeStep):
        
        if self.debugWaterBalance == str('True'):
            prevStates = [self.interceptStor]
       
        # get interceptCap:
        interceptCap = pcr.scalar(self.minInterceptCap)
        if not self.iniItemsLC['name'].startswith("irr"):
            interceptCap = \
                     vos.netcdf2PCRobjClone(self.interceptCapNC,\
                                    'interceptCapInput',\
                                     currTimeStep.doy, useDoy = 'Yes',\
                                     cloneMapFileName = self.cloneMap)
            coverFraction = \
                     vos.netcdf2PCRobjClone(self.coverFractionNC,\
                                    'coverFractionInput',\
                                     currTimeStep.doy, useDoy = 'Yes',\
                                     cloneMapFileName = self.cloneMap)
            coverFraction = pcr.cover(coverFraction, 0.0)
            interceptCap = coverFraction * interceptCap                  # original Rens line: ICC[TYPE] = CFRAC[TYPE]*INTCMAX[TYPE];                                
        self.interceptCap = pcr.max(interceptCap, self.minInterceptCap)  # Edwin added this line to extend the interception definition (not only canopy interception).
        
        # canopy/cover fraction over the entire cell area (unit: m2)
        
        # throughfall = surplus above the interception storage threshold 
        self.throughfall   = pcr.max(0.0, self.interceptStor + \
                                         meteo.precipitation - \
                                         self.interceptCap)              # original Rens line: PRP = (1-CFRAC[TYPE])*PRPTOT+max(CFRAC[TYPE]*PRPTOT+INTS_L[TYPE]-ICC[TYPE],0) 
                                                                         # Edwin modified this line to extend the interception scope (not only canopy interception).
        # update interception storage after throughfall 
        self.interceptStor = pcr.max(0.0, self.interceptStor + \
                                    meteo.precipitation - \
                                    self.throughfall)                    # original Rens line: INTS_L[TYPE] = max(0,INTS_L[TYPE]+PRPTOT-PRP)
         
        # partitioning throughfall into snowfall and liquid Precipitation:
        estimSnowfall = pcr.ifthenelse(meteo.temperature < self.freezingT, \
                                       meteo.precipitation, 0.0)         # original Rens line: SNOW = if(TA<TT,PRPTOT,0)
                                                                         # But Rens put it in his "meteo" module in order to allow snowfallCorrectionFactor (SFCF).
        self.snowfall = estimSnowfall * \
                        pcr.ifthenelse(meteo.precipitation > 0.0, \
              vos.getValDivZero(self.throughfall, meteo.precipitation, \
              vos.smallNumber), 0.)                                      # original Rens line: SNOW = SNOW*if(PRPTOT>0,PRP/PRPTOT,0)                                      

        self.liquidPrecip  = self.throughfall - self.snowfall            # original Rens line: PRP = PRP-SNOW

        # potential interception flux (m/day)
        self.potInterceptionFlux = self.totalPotET                       # added by Edwin to extend the interception scope/definition
        
        # evaporation from intercepted water (based on potInterceptionFlux)
        self.interceptEvap = pcr.min(self.interceptStor, \
                                     self.potInterceptionFlux * \
             (vos.getValDivZero(self.interceptStor, self.interceptCap, \
              vos.smallNumber, 0.) ** (2.00/3.00)))                      
                                                                         # EACT_L[TYPE]= min(INTS_L[TYPE],(T_p[TYPE]*if(ICC[TYPE]>0,INTS_L[TYPE]/ICC[TYPE],0)**(2/3)))
        self.interceptEvap = pcr.min(self.interceptEvap, \
                                     self.potInterceptionFlux)
                                     
        # update interception storage 
        self.interceptStor = self.interceptStor - self.interceptEvap     # INTS_L[TYPE]= INTS_L[TYPE]-EACT_L[TYPE]
        
        
        # update potBareSoilEvap and potTranspiration 
        self.potBareSoilEvap  -= self.fracPotBareSoilEvap  * self.interceptEvap
        self.potTranspiration -= self.fracPotTranspiration * self.interceptEvap  # original Rens line: T_p[TYPE]= max(0,T_p[TYPE]-EACT_L[TYPE])
                                                                                 # Edwin modified this line to extend the interception scope/definition (not only canopy interception).

        # update actual evaporation (after interceptEvap) 
        self.actualET  = 0.  # interceptEvap is the first flux in ET 
        self.actualET += self.interceptEvap

        if self.debugWaterBalance == str('True'):
            vos.waterBalanceCheck([self.throughfall],\
                                  [self.snowfall,self.liquidPrecip],\
                                  [],\
                                  [],\
                                  'rain-snow-partitioning',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-5)
            vos.waterBalanceCheck([meteo.precipitation],
                                  [self.throughfall,self.interceptEvap],
                                  prevStates,\
                                  [self.interceptStor],\
                                  'interceptStor',\
                                  True,\
                                  currTimeStep.fulldate,threshold=1e-5)

    def snowMeltHBVSimple(self,meteo,currTimeStep):

        # output: self.snowCoverSWE, 
        #         self.netLqWaterToSoil, 
        #         self.actBareSoilEvap, 
        #         self.snowFreeWater, 
        #         self.potBareSoilEvap, 
        #         self.actualET

        # parameters:  self.freezingT,
        #              self.degreeDayFactor,
        #              self.snowWaterHoldingCap,
        #              self.refreezingCoeff

        if self.debugWaterBalance == str('True'):
            prevStates = [self.snowCoverSWE,self.snowFreeWater]

        # changes in snow cover: - melt ; + gain in snow or refreezing
        deltaSnowCover = \
            pcr.ifthenelse(meteo.temperature <= self.freezingT, \
            self.refreezingCoeff*self.snowFreeWater, \
           -pcr.min(self.snowCoverSWE, \
                    pcr.max(meteo.temperature - self.freezingT, 0.0) * \
                    self.degreeDayFactor))                              # DSC[TYPE] = if(TA<=TT,CFR*SCF_L[TYPE],-min(SC_L[TYPE],max(TA-TT,0)*CFMAX*Duration*timeslice())) 

        # for reporting snow melt in m/day
        self.snowMelt = pcr.ifthenelse(deltaSnowCover < 0.0, deltaSnowCover * pcr.scalar(-1.0), pcr.scalar(0.0))
        
        # update snowCoverSWE
        self.snowCoverSWE  = self.snowCoverSWE  + deltaSnowCover + \
                             self.snowfall                              # SC_L[TYPE] = SC_L[TYPE]+DSC[TYPE]+SNOW;
        self.snowCoverSWE  = pcr.max(self.snowCoverSWE, 0.0)                     

        # update snowFreeWater = liquid water stored above snowCoverSWE
        self.snowFreeWater = self.snowFreeWater - deltaSnowCover + \
                             self.liquidPrecip                          # SCF_L[TYPE] = SCF_L[TYPE]-DSC[TYPE]+PRP;
                                     
        # netLqWaterToSoil = net liquid transferred to soil
        self.netLqWaterToSoil = pcr.max(0, self.snowFreeWater - \
                self.snowWaterHoldingCap * self.snowCoverSWE)           # Pn = max(0,SCF_L[TYPE]-CWH*SC_L[TYPE])
        
        # update snowFreeWater (after netPfromSnowFreeWater) 
        self.snowFreeWater    = pcr.max(0., self.snowFreeWater - \
                                            self.netLqWaterToSoil)      # SCF_L[TYPE]= max(0,SCF_L[TYPE]-Pn)

        # evaporation from snowFreeWater (based on potBareSoilEvap)
        self.actSnowFreeWaterEvap = pcr.min(self.snowFreeWater, \
                                            self.potBareSoilEvap)       # ES_a[TYPE] = min(SCF_L[TYPE],ES_p[TYPE])
                                       
        # update snowFreeWater and potBareSoilEvap
        self.snowFreeWater = self.snowFreeWater - self.actSnowFreeWaterEvap  
                                                                        # SCF_L[TYPE]= SCF_L[TYPE]-ES_a[TYPE]
        self.potBareSoilEvap = pcr.max(0, \
                           self.potBareSoilEvap - self.actSnowFreeWaterEvap) 
                                                                        # ES_p[TYPE]= max(0,ES_p[TYPE]-ES_a[TYPE])

        # update actual evaporation (after evaporation from snowFreeWater) 
        self.actualET += self.actSnowFreeWaterEvap                      # EACT_L[TYPE]= EACT_L[TYPE]+ES_a[TYPE];

        if self.debugWaterBalance == str('True'):
            vos.waterBalanceCheck([self.snowfall,self.liquidPrecip],
                                  [self.netLqWaterToSoil,\
                                   self.actSnowFreeWaterEvap],
                                   prevStates,\
                                  [self.snowCoverSWE,self.snowFreeWater],\
                                  'snow module',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)

    def getSoilStates(self,parameters):

        if self.numberOfLayers == 2: 

            # initial total soilWaterStorage
            self.soilWaterStorage = pcr.max(0.,\
                                        self.storUpp + \
                                        self.storLow )

            # effective degree of saturation (-)
            self.effSatUpp = pcr.max(0., self.storUpp/ parameters.storCapUpp)  # THEFF1= max(0,S1_L[TYPE]/SC1[TYPE]);
            self.effSatLow = pcr.max(0., self.storLow/ parameters.storCapLow)  # THEFF2= max(0,S2_L[TYPE]/SC2[TYPE]);
            self.effSatUpp = pcr.min(1., self.effSatUpp)
            self.effSatLow = pcr.min(1., self.effSatLow)
        
            # matricSuction (m)
            self.matricSuctionUpp = parameters.airEntryValueUpp*\
             (pcr.max(0.01,self.effSatUpp)**-parameters.poreSizeBetaUpp)
            self.matricSuctionLow = parameters.airEntryValueLow*\
             (pcr.max(0.01,self.effSatLow)**-parameters.poreSizeBetaLow)       # PSI1= PSI_A1[TYPE]*max(0.01,THEFF1)**-BCH1[TYPE]; 
                                                                               # PSI2= PSI_A2[TYPE]*max(0.01,THEFF2)**-BCH2[TYPE]; 

            # kUnsat (m.day-1): unsaturated hydraulic conductivity
            #~ KUnSatUpp = pcr.max(0.,pcr.max(parameters.THEFF1_50,\
                                           #~ effSatUpp)**\
                         #~ parameters.campbellBeta1*parameters.KSat1)         # DW's code
            #~ KUnSatLow = pcr.max(0.,pcr.max(parameters.THEFF2_50,\
                                           #~ effSatLow)**\
                         #~ parameters.campbellBeta2*parameters.KSat2)         # DW's code
            # 
            self.kUnsatUpp = pcr.max(0.,(self.effSatUpp**\
                        parameters.campbellBetaUpp)*parameters.kSatUpp)        # original Rens's code: KTHEFF1= max(0,THEFF1**BCB1[TYPE]*KS1[TYPE])
            self.kUnsatLow = pcr.max(0.,(self.effSatLow**\
                        parameters.campbellBetaLow)*parameters.kSatLow)        # original Rens's code: KTHEFF2= max(0,THEFF2**BCB2[TYPE]*KS2[TYPE])
            self.kUnsatUpp = pcr.min(self.kUnsatUpp,parameters.kSatUpp)
            self.kUnsatLow = pcr.min(self.kUnsatLow,parameters.kSatLow)
            
            # kThVert (m.day-1) = unsaturated conductivity capped at field capacity
            # - exchange between layers capped at field capacity 
            self.kThVertUppLow  = pcr.min(\
                          pcr.sqrt(self.kUnsatUpp*self.kUnsatLow),\
                                  (self.kUnsatUpp*self.kUnsatLow* \
                                  parameters.kUnsatAtFieldCapUpp*\
                                  parameters.kUnsatAtFieldCapLow)**0.25)       # KTHVERT = min(sqrt(KTHEFF1*KTHEFF2),(KTHEFF1*KTHEFF2*KTHEFF1_FC*KTHEFF2_FC)**0.25)
        
            # gradient for capillary rise (index indicating target store to its underlying store)
            self.gradientUppLow = pcr.max(0.,2.*\
                         (self.matricSuctionUpp-self.matricSuctionLow)/\
                         (  parameters.thickUpp+  parameters.thickLow)-1.)     # GRAD = max(0,2*(PSI1-PSI2)/(Z1[TYPE]+Z2[TYPE])-1);
        
             
            # readily available water in the root zone (upper soil layers)
            #~ readAvlWater     = \
                               #~ (pcr.max(0.,\
                                #~ effSatUpp        -parameters.THEFF1_WP))*\
                               #~ (parameters.satVolWC1 -parameters.resVolWC1) *\
                        #~ pcr.min(parameters.storCapUpp,self.maxRootDepth)  + \
                               #~ (pcr.max(0.,\
                                #~ effSatLow        -parameters.THEFF2_WP))*\
                               #~ (parameters.satVolWC2 -parameters.resVolWC2) *\
                        #~ pcr.min(parameters.storCapLow,\
                        #~ pcr.max(self.maxRootDepth-parameters.storCapUpp,0.)) # DW's code (using storCapUpp and storCapLow). Edwin does not agree with this.  
            self.readAvlWater     = \
                               (pcr.max(0.,\
                                               self.effSatUpp - parameters.effSatAtWiltPointUpp))*\
                               (parameters.satVolMoistContUpp -   parameters.resVolMoistContUpp )*\
                        pcr.min(parameters.thickUpp,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                                               self.effSatLow - parameters.effSatAtWiltPointLow))*\
                               (parameters.satVolMoistContLow -   parameters.resVolMoistContLow )*\
                        pcr.min(parameters.thickLow,\
                        pcr.max(self.maxRootDepth-parameters.thickUpp,0.))      # Edwin modified this line. Edwin uses soil thickness thickUpp and thickLow (instead of storCapUpp and storCapLow). 
                                                                                # And Rens support this. 
            self.readAvlWater = pcr.min(self.readAvlWater, \
                                        self.storUpp + self.storLow)

        if self.numberOfLayers == 3: 

            # initial total soilWaterStorage
            self.soilWaterStorage = pcr.max(0.,\
                                        self.storUpp000005 + \
                                        self.storUpp005030 + \
                                        self.storLow030150 )

            # effective degree of saturation (-)
            self.effSatUpp000005 = pcr.max(0., self.storUpp000005/ parameters.storCapUpp000005)
            self.effSatUpp005030 = pcr.max(0., self.storUpp005030/ parameters.storCapUpp005030)
            self.effSatLow030150 = pcr.max(0., self.storLow030150/ parameters.storCapLow030150)
            self.effSatUpp000005 = pcr.min(1., self.effSatUpp000005)
            self.effSatUpp005030 = pcr.min(1., self.effSatUpp005030)
            self.effSatLow030150 = pcr.min(1., self.effSatLow030150)
        
            # matricSuction (m)
            self.matricSuctionUpp000005 = parameters.airEntryValueUpp000005*(pcr.max(0.01,self.effSatUpp000005)**-parameters.poreSizeBetaUpp000005)
            self.matricSuctionUpp005030 = parameters.airEntryValueUpp005030*(pcr.max(0.01,self.effSatUpp005030)**-parameters.poreSizeBetaUpp005030)
            self.matricSuctionLow030150 = parameters.airEntryValueLow030150*(pcr.max(0.01,self.effSatLow030150)**-parameters.poreSizeBetaLow030150)

            # kUnsat (m.day-1): unsaturated hydraulic conductivity
            self.kUnsatUpp000005 = pcr.max(0.,(self.effSatUpp000005**parameters.campbellBetaUpp000005)*parameters.kSatUpp000005)
            self.kUnsatUpp005030 = pcr.max(0.,(self.effSatUpp005030**parameters.campbellBetaUpp005030)*parameters.kSatUpp005030)
            self.kUnsatLow030150 = pcr.max(0.,(self.effSatLow030150**parameters.campbellBetaLow030150)*parameters.kSatLow030150)

            self.kUnsatUpp000005 = pcr.min(self.kUnsatUpp000005,parameters.kSatUpp000005)
            self.kUnsatUpp005030 = pcr.min(self.kUnsatUpp005030,parameters.kSatUpp005030)
            self.kUnsatLow030150 = pcr.min(self.kUnsatLow030150,parameters.kSatLow030150)
            
            # kThVert (m.day-1) = unsaturated conductivity capped at field capacity
            # - exchange between layers capped at field capacity 
            #   between Upp000005Upp005030
            self.kThVertUpp000005Upp005030  = pcr.min(\
                          pcr.sqrt(self.kUnsatUpp000005*self.kUnsatUpp005030),\
                                  (self.kUnsatUpp000005*self.kUnsatUpp005030* \
                   parameters.kUnsatAtFieldCapUpp000005*\
                   parameters.kUnsatAtFieldCapUpp005030)**0.25)
            #   between Upp005030Low030150
            self.kThVertUpp005030Low030150  = pcr.min(\
                          pcr.sqrt(self.kUnsatUpp005030*self.kUnsatLow030150),\
                                  (self.kUnsatUpp005030*self.kUnsatLow030150* \
                   parameters.kUnsatAtFieldCapUpp005030*\
                   parameters.kUnsatAtFieldCapLow030150)**0.25)
        
            # gradient for capillary rise (index indicating target store to its underlying store)
            #    between Upp000005Upp005030
            self.gradientUpp000005Upp005030 = pcr.max(0.,2.*\
                         (self.matricSuctionUpp000005-self.matricSuctionUpp005030)/\
                         (  parameters.thickUpp000005+  parameters.thickUpp005030)-1.)
            #    between Upp005030Low030150
            self.gradientUpp005030Low030150 = pcr.max(0.,2.*\
                         (self.matricSuctionUpp005030-self.matricSuctionLow030150)/\
                         (  parameters.thickUpp005030+  parameters.thickLow030150)-1.)
             
            # readily available water in the root zone (upper soil layers)
            self.readAvlWater = \
                               (pcr.max(0.,\
                                               self.effSatUpp000005 - parameters.effSatAtWiltPointUpp000005))*\
                               (parameters.satVolMoistContUpp000005 -   parameters.resVolMoistContUpp000005 )*\
                        pcr.min(parameters.thickUpp000005,self.maxRootDepth)  + \
                               (pcr.max(0.,\
                                               self.effSatUpp005030 - parameters.effSatAtWiltPointUpp005030))*\
                               (parameters.satVolMoistContUpp005030 -   parameters.resVolMoistContUpp005030 )*\
                        pcr.min(parameters.thickUpp005030,\
                        pcr.max(self.maxRootDepth-parameters.thickUpp000005))  + \
                               (pcr.max(0.,\
                                               self.effSatLow030150 - parameters.effSatAtWiltPointLow030150))*\
                               (parameters.satVolMoistContLow030150 -   parameters.resVolMoistContLow030150 )*\
                        pcr.min(parameters.thickLow030150,\
                        pcr.max(self.maxRootDepth-parameters.thickUpp005030,0.)) 
            #
            self.readAvlWater = pcr.min(self.readAvlWater, \
                                        self.storUpp000005 + \
                                        self.storUpp005030 + \
                                        self.storLow030150)

    def calculateWaterDemand(self, parameters, nonIrrGrossDemand, swAbstractionFraction, groundwater, routing, allocSegments):

        # non irrigation water demand
        self.nonIrrGrossDemand = pcr.cover(nonIrrGrossDemand, 0.0)                   # TODO: Please check! Do we really have to cover?    
        self.nonIrrGrossDemand = pcr.ifthen(self.landmask, self.nonIrrGrossDemand)
        
        # irrigation water demand for paddy and non-paddy (m)
        self.irrGrossDemand = pcr.scalar(0.)
        if self.name == 'irrPaddy':
            self.irrGrossDemand = \
                 pcr.ifthenelse( self.cropKC > 0.75, \
                     pcr.max(0.0,self.minTopWaterLayer - \
                                (self.topWaterLayer + \
                                 self.netLqWaterToSoil)), 0.)              # a function of cropKC (evaporation and transpiration),
                                                                           #               topWaterLayer (water available in the irrigation field), and 
                                                                           #               netLqWaterToSoil (amout of liquid precipitation)  
        if self.name == 'irrNonPaddy':
            adjDeplFactor = \
                     pcr.max(0.1,\
                     pcr.min(0.8,(self.cropDeplFactor + \
                                  40.*(0.005-self.totalPotET))))
            self.irrGrossDemand = \
                 pcr.ifthenelse( self.cropKC > 0.20, \
                 pcr.ifthenelse( self.readAvlWater < \
                                  adjDeplFactor*self.totAvlWater, \
                pcr.max(0.0,  self.totAvlWater-self.readAvlWater),0.),0.)  # a function of cropKC and totalPotET (evaporation and transpiration),
                                                                           #               readAvlWater (available water in the root zone), and 
                                                                           #               netLqWaterToSoil (amout of liquid precipitation)

        self.irrGrossDemand = pcr.cover(self.irrGrossDemand, 0.0)
        self.irrGrossDemand = pcr.ifthen(self.landmask, self.irrGrossDemand)

        self.irrGrossDemand = pcr.ifthenelse(self.irrGrossDemand > (1.0/routing.cellArea), self.irrGrossDemand, 0) # ignore demand if less than 1 m3
        self.irrGrossDemand = pcr.ifthenelse(self.irrGrossDemand > 0.0001, self.irrGrossDemand, 0)                 # ignore demand if less than 0.1 mm

        
        # totalPotentialGrossDemand (m): total maximum (potential) water demand: irrigation and non irrigation
        self.totalPotentialGrossDemand = pcr.cover(self.nonIrrGrossDemand + self.irrGrossDemand, 0.0)

        # surface water demand (m): water demand that should be satisfied by surface water abstraction
        surface_water_demand = self.totalPotentialGrossDemand * swAbstractionFraction
        
        # surface water abstraction that can be extracted to satisfy totalPotentialGrossDemand
        # - based on readAvlChannelStorage
        #        and swAbstractionFraction * totalPotGrossDemand
        # 
        if self.usingAllocSegments:      # using zone/segment at which supply network is defined

            logger.info("Allocation of surface water abstraction in progress.")
            
            allocSegments = pcr.ifthen(self.landmask, allocSegments)
            
            # gross demand volume in each cell (unit: m3) - ignore small values (less than 1 m3)
            cellVolGrossDemand = pcr.rounddown(surface_water_demand*routing.cellArea)
            
            # total gross demand volume in each segment/zone (unit: m3)
            segTtlGrossDemand = pcr.areatotal(cellVolGrossDemand, allocSegments)
            
            # total available surface water volume in each cell - ignore small values (less than 1 m3)
            cellAvlSurfaceWater = pcr.max(0.00, routing.readAvlChannelStorage)
            cellAvlSurfaceWater = pcr.rounddown(cellAvlSurfaceWater)
            
            # total available surface water volume in each segment/zone  (unit: m3)
            segAvlSurfaceWater  = pcr.areatotal(cellAvlSurfaceWater, allocSegments)
            segAvlSurfaceWater  = pcr.max(0.00, segAvlSurfaceWater)
            
            # total actual surface water abstraction volume in each segment/zone (unit: m3)
            #
            # - not limited to available water
            segActSurWaterAbs   = segTtlGrossDemand
            # 
            # - limited to available water
            segActSurWaterAbs = pcr.min(segAvlSurfaceWater, segActSurWaterAbs)
            
            # actual surface water abstraction volume in each cell (unit: m3)
            volActSurfaceWaterAbstract = vos.getValDivZero(\
                                         cellAvlSurfaceWater, segAvlSurfaceWater, vos.smallNumber) * \
                                         segActSurWaterAbs                                                 
            volActSurfaceWaterAbstract = pcr.min(cellAvlSurfaceWater, volActSurfaceWaterAbstract)  # unit: m3
            
            # actual surface water abstraction volume in meter (unit: m)
            self.actSurfaceWaterAbstract = pcr.ifthen(self.landmask, volActSurfaceWaterAbstract) /\
                                                                     routing.cellArea              # unit: m
            
            # allocation surface water abstraction volume to each cell (unit: m3)
            volAllocSurfaceWaterAbstract = vos.getValDivZero(\
                                                cellVolGrossDemand, segTtlGrossDemand, vos.smallNumber) *\
                                                segActSurWaterAbs                                  # unit: m3 
            
            # allocation surface water abstraction in meter (unit: m)
            self.allocSurfaceWaterAbstract = pcr.ifthen(self.landmask, volAllocSurfaceWaterAbstract) /\
                                                                       routing.cellArea            # unit: m

            if self.debugWaterBalance == str('True'):
    
                abstraction = pcr.cover(pcr.areatotal(self.actSurfaceWaterAbstract  *routing.cellArea, self.allocSegments)/self.segmentArea, 0.0)
                allocation  = pcr.cover(pcr.areatotal(self.allocSurfaceWaterAbstract*routing.cellArea, self.allocSegments)/self.segmentArea, 0.0)
            
                vos.waterBalanceCheck([abstraction],\
                                      [allocation],\
                                      [pcr.scalar(0.0)],\
                                      [pcr.scalar(0.0)],\
                                      'surface water abstraction - allocation per zone/segment in land cover level (PS: Error here may be caused by rounding error.)' ,\
                                       True,\
                                       "",threshold=5e-4)

        else: 
            
            logger.info("Surface water abstraction is only to satisfy local demand (no surface water network).")

            # only local surface water abstraction is allowed (network is only within a cell)
            self.actSurfaceWaterAbstract = pcr.min(routing.readAvlChannelStorage/routing.cellArea,\
                                                   surface_water_demand)                 # unit: m
            self.allocSurfaceWaterAbstract = self.actSurfaceWaterAbstract                # unit: m   

        self.actSurfaceWaterAbstract   = pcr.ifthen(self.landmask, self.actSurfaceWaterAbstract)
        self.allocSurfaceWaterAbstract = pcr.ifthen(self.landmask, self.allocSurfaceWaterAbstract)
        
        self.potGroundwaterAbstract = pcr.max(0.0, self.totalPotentialGrossDemand - self.allocSurfaceWaterAbstract)              # unit: m
            
        # if limitAbstraction == 'True'
        # - no fossil gwAbstraction.
        # - limitting abstraction with avlWater in channelStorage (m3) and storGroundwater (m)
        # - water demand may be reduced
        #
        self.reducedCapRise = 0.0                           # variable to reduce/limit groundwater abstraction (> 0 if limitAbstraction = True)  
        #
        if self.limitAbstraction:

            logger.info('Fossil groundwater abstractions are NOT allowed.')

            # calculate renewableAvlWater (non-fossil groundwater and channel) 
            
            # - from storGroundwater
            #  -- avoid small values 
            readAvlStorGroundwater = pcr.rounddown(groundwater.storGroundwater*10000.)/10000.
            readAvlStorGroundwater = pcr.cover(readAvlStorGroundwater, 0.0)
            
            # - from non-fossil groundwater and surface water bodies
            renewableAvlWater = readAvlStorGroundwater + self.allocSurfaceWaterAbstract

            # reducing nonIrrGrossDemand < renewableAvlWater  
            #
            self.nonIrrGrossDemand = \
              pcr.ifthenelse(self.totalPotentialGrossDemand > 0.0, \
              pcr.min(1.0,pcr.max(0.0, \
              vos.getValDivZero(renewableAvlWater, self.totalPotentialGrossDemand, vos.smallNumber)))*self.nonIrrGrossDemand, 0.0)

            # reducing irrGrossWaterDemand < renewableAvlWater 
            #
            self.irrGrossDemand = \
              pcr.ifthenelse(self.totalPotentialGrossDemand > 0.0, \
              pcr.min(1.0,pcr.max(0.0, \
              vos.getValDivZero(renewableAvlWater, self.totalPotentialGrossDemand, vos.smallNumber)))*   self.irrGrossDemand, 0.0)    

            # correcting total demand 
            self.totalPotentialGrossDemand = self.nonIrrGrossDemand + self.irrGrossDemand
            
            # potential groundwater abstraction (must be equal to actual no fossil groundwater abstraction)
            self.potGroundwaterAbstract = self.nonIrrGrossDemand + self.irrGrossDemand - self.allocSurfaceWaterAbstract
            
            # variable to reduce/limit capillary rise (to ensure that there are enough water for supplying nonIrrGrossDemand + irrGrossDemand)
            self.reducedCapRise = self.potGroundwaterAbstract
 
        else:
            logger.info('Fossil groundwater abstraction is allowed.')

        if self.limitAbstraction == False and\
           groundwater.limitFossilGroundwaterAbstraction and groundwater.usingAllocSegments == False:

            # Note: For simplicity, limitFossilGroundwaterAbstraction can only be combined with local (groundwater) source assumption

            logger.info('Fossil groundwater abstraction is allowed with LIMIT.')

            # calculate renewableAvlWater (non-fossil groundwater and channel) 
            
            # - from storGroundwater
            #  -- avoid small values 
            readAvlStorGroundwater = pcr.rounddown(groundwater.storGroundwater*10000.)/10000.
            readAvlStorGroundwater = pcr.cover(readAvlStorGroundwater, 0.0)
            
            # - from non-fossil groundwater and surface water bodies
            renewableAvlWater = readAvlStorGroundwater + self.allocSurfaceWaterAbstract

            # estimate of demand that will be satisfied by renewableAvlWater  
            allocRenewableAvlWater = pcr.min(renewableAvlWater, self.totalPotentialGrossDemand)

            # variable to reduce/limit capillary rise (to ensure that there are enough water for supplying nonIrrGrossDemand + irrGrossDemand)
            self.reducedCapRise = allocRenewableAvlWater - self.allocSurfaceWaterAbstract

            # calculate accessibleWater (unit: m) 
            accessibleWater = pcr.max(0.0,\
                              self.allocSurfaceWaterAbstract +\
                              groundwater.storGroundwater +\
                              groundwater.storGroundwaterFossil)

            # total nonIrrGrossDemand < accessibleWater  
            self.nonIrrGrossDemand = \
              pcr.ifthenelse(self.totalPotentialGrossDemand > 0.0, \
              pcr.min(1.0,pcr.max(0.0, \
              vos.getValDivZero(accessibleWater, self.totalPotentialGrossDemand, vos.smallNumber)))*self.nonIrrGrossDemand, 0.0)

            # total irrGrossWaterDemand < accessibleWater 
            self.irrGrossDemand = \
              pcr.ifthenelse(self.totalPotentialGrossDemand > 0.0, \
              pcr.min(1.0,pcr.max(0.0, \
              vos.getValDivZero(accessibleWater, self.totalPotentialGrossDemand, vos.smallNumber)))*   self.irrGrossDemand, 0.0)    

            # correcting total demand 
            self.totalPotentialGrossDemand = self.nonIrrGrossDemand + self.irrGrossDemand
            
            # potential groundwater abstraction (m/day)
            self.potGroundwaterAbstract = self.totalPotentialGrossDemand - self.allocSurfaceWaterAbstract
            
        if groundwater.limitRegionalAnnualGroundwaterAbstraction:

            # estimate of total groundwater abstraction (m3) from the last 365 days:
            annualGroundwaterAbstraction = groundwater.averageAbstraction * routing.cellArea
                                           pcr.min(365., pcr.max(1.0, routing.timestepsToAvgDischarge))
            # at regional scale
            regionalAnnualGroundwaterAbstraction = pcr.areatotal(pcr.cover(annualGroundwaterAbstraction, 0.0),\
                                                                 groundwater.abstraction_region_ids)
                                                                 
            # reduction factor to reduce groundwater abstraction
            reductionFactorForPotGroundwaterAbstract = pcr.max(0.00, groundwater.regionalAnnualGroundwaterAbstractionLimit -\
                                                                     regionalAnnualGroundwaterAbstraction) /\
                                                                     regionalAnnualGroundwaterAbstraction
            reductionFactorForPotGroundwaterAbstract = pcr.rounddown(reductionFactorForPotGroundwaterAbstract*100.)/100.                                                         
            reductionFactorForPotGroundwaterAbstract = pcr.min(1.00, reductionFactorForPotGroundwaterAbstract)
            
            # potential groundwater abstraction (m/day) after reduction 
            self.potGroundwaterAbstract = reductionFactorForPotGroundwaterAbstract * self.potGroundwaterAbstract

            # calculate accessibleWater (unit: m) 
            accessibleWater = self.allocSurfaceWaterAbstract + self.potGroundwaterAbstract

            # total nonIrrGrossDemand   < accessibleWater  
            self.nonIrrGrossDemand = \
              pcr.ifthenelse(self.totalPotentialGrossDemand > 0.0, \
              pcr.min(1.0,pcr.max(0.0, \
              vos.getValDivZero(accessibleWater, self.totalPotentialGrossDemand, vos.smallNumber)))*self.nonIrrGrossDemand, 0.0)

            # total irrGrossWaterDemand < accessibleWater 
            #
            self.irrGrossDemand = \
              pcr.ifthenelse(self.totalPotentialGrossDemand > 0.0, \
              pcr.min(1.0,pcr.max(0.0, \
              vos.getValDivZero(accessibleWater, self.totalPotentialGrossDemand, vos.smallNumber)))*   self.irrGrossDemand, 0.0)    

            # correcting total demand 
            self.totalPotentialGrossDemand = self.nonIrrGrossDemand + self.irrGrossDemand
            #~ # - should be the same as the following: 
            #~ self.totalPotentialGrossDemand = self.potGroundwaterAbstract + self.allocSurfaceWaterAbstract

            if self.debugWaterBalance:\
                vos.waterBalanceCheck([accessibleWater],\
                                      [self.totalPotentialGrossDemand],\
                                      [pcr.scalar(0.0)],\
                                      [pcr.scalar(0.0)],\
                                       'totalPotentialGrossDemand (limitRegionalAnnualGroundwaterAbstraction)',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-4)

    def calculateDirectRunoff(self, parameters):

        # update topWaterLayer (above soil) 
        # with netLqWaterToSoil and irrGrossDemand
        self.topWaterLayer = self.topWaterLayer + \
                             pcr.max(0.,self.netLqWaterToSoil + self.irrGrossDemand)
        		        
        # topWaterLater is partitioned into directRunoff (and infiltration)
        self.directRunoff = self.improvedArnoScheme(\
                            iniWaterStorage = self.soilWaterStorage,\
                            inputNetLqWaterToSoil =  self.topWaterLayer, 
                            parameters = parameters)
        self.directRunoff = pcr.min(self.topWaterLayer, self.directRunoff)
        # Yet, no directRunoff in the paddy field.
        if self.name == 'irrPaddy': self.directRunoff = 0.

        # update topWaterLayer (above soil) after directRunoff
        self.topWaterLayer = self.topWaterLayer - self.directRunoff

    def improvedArnoScheme(self,iniWaterStorage,inputNetLqWaterToSoil,parameters,directRunoffReduction = "Default"):

        # arnoBeta = BCF = b coefficient of soil water storage capacity distribution
        # 
        # WMIN = root zone water storage capacity, minimum values
        # WMAX = root zone water storage capacity, area-averaged values
        # W	   = actual water storage in root zone
        # WRANGE  = WMAX - WMIN
        # DW      = WMAX-W 
        # WFRAC   = DW/WRANGE ; WFRAC capped at 1
        # WFRACB  = DW/WRANGE raised to the power (1/(b+1))
        # SATFRAC =	fractional saturated area
        # WACT    = actual water storage within rootzone
        
        Pn = iniWaterStorage + \
             inputNetLqWaterToSoil                                      # Pn = W[TYPE]+Pn;
        Pn = Pn - pcr.max(self.rootZoneWaterStorageMin,\
                                    iniWaterStorage)                    # Pn = Pn-max(WMIN[TYPE],W[TYPE]);
        soilWaterStorage = pcr.ifthenelse(Pn < 0.,\
                                     self.rootZoneWaterStorageMin+Pn,\
             pcr.max(iniWaterStorage,self.rootZoneWaterStorageMin))     # W[TYPE]= if(Pn<0,WMIN[TYPE]+Pn,max(W[TYPE],WMIN[TYPE]));
        Pn = pcr.max(0.,Pn)                                             # Pn = max(0,Pn);
        #
        DW = pcr.max(0.0,parameters.rootZoneWaterStorageCap - \
                                    soilWaterStorage)                   # DW = max(0,WMAX[TYPE]-W[TYPE]);
 
        WFRAC = pcr.min(1.0,DW/self.rootZoneWaterStorageRange)          # WFRAC = min(1,DW/WRANGE[TYPE]);
        self.WFRACB = WFRAC**(1./(1.+self.arnoBeta))                    # WFRACB = WFRAC**(1/(1+BCF[TYPE]));
        #
        self.satAreaFrac = pcr.ifthenelse(self.WFRACB > 0.,\
                                       1.-self.WFRACB**self.arnoBeta,\
                                                  0.)                   # SATFRAC_L = if(WFRACB>0,1-WFRACB**BCF[TYPE],0);
        self.satAreaFrac = pcr.min(self.satAreaFrac, 1.0)
        self.satAreaFrac = pcr.max(self.satAreaFrac, 0.0)
        actualW = (self.arnoBeta+1)*parameters.rootZoneWaterStorageCap - \
                   self.arnoBeta   *self.rootZoneWaterStorageMin - \
                  (self.arnoBeta+1)*self.rootZoneWaterStorageRange*self.WFRACB       
                                                                        # WACT_L = (BCF[TYPE]+1)*WMAX[TYPE]- BCF[TYPE]*WMIN[TYPE]- (BCF[TYPE]+1)*WRANGE[TYPE]*WFRACB;

        
        if directRunoffReduction == "Default":
            if self.numberOfLayers == 2: directRunoffReduction = pcr.min(self.kUnsatLow,\
                                                                 pcr.sqrt(parameters.kUnsatAtFieldCapLow*\
                                                                                self.kUnsatLow))
            if self.numberOfLayers == 3: directRunoffReduction = pcr.min(self.kUnsatLow030150,\
                                                                 pcr.sqrt(parameters.kUnsatAtFieldCapLow030150*\
                                                                                self.kUnsatLow030150))           # Rens: # In order to maintain full saturation and     
                                                                                                                         # continuous groundwater recharge/percolation, 
                                                                                                                         # the amount of directRunoff may be reduced.  
                                                                                                                         # In this case, this reduction is estimated 
                                                                                                                         # based on (for two layer case) percLow = pcr.min(KUnSatLow,\ 
                                                                                                                         #                                         pcr.sqrt(parameters.KUnSatFC2*KUnSatLow))
        
        # directRunoff
        condition = (self.arnoBeta+pcr.scalar(1.))*self.rootZoneWaterStorageRange* self.WFRACB
        directRunoff = pcr.max(0.0, \
                          Pn -\
                      (parameters.rootZoneWaterStorageCap+directRunoffReduction-soilWaterStorage) + \
           pcr.ifthenelse(Pn >= condition,
                          pcr.scalar(0.0), \
                          self.rootZoneWaterStorageRange*(self.WFRACB-\
                          Pn / ((self.arnoBeta+1.)*\
                          self.rootZoneWaterStorageRange))**(self.arnoBeta+1.)))
                                                                        #    Q1_L[TYPE]= max(0,Pn-(WMAX[TYPE]+P2_L[TYPE]-W[TYPE])+
                                                                        #      if(Pn>=(BCF[TYPE]+1)*WRANGE[TYPE]*WFRACB, 0,
                                                                        #      WRANGE[TYPE]*(WFRACB-Pn/((BCF[TYPE]+1)*WRANGE[TYPE]))**(BCF[TYPE]+1))); #*
        return directRunoff                                            

    def calculateOpenWaterEvap(self):

        self.openWaterEvap = pcr.spatial(pcr.scalar(0.))
        remainingPotETP = self.potBareSoilEvap + self.potTranspiration   # Edwin's principle: LIMIT = self.potBareSoilEvap +self.potTranspiration 
        # remainingPotETP = self.totalPotET                              # DW, RvB, and YW use self.totalPotETP

        # open water evaporation from the paddy field
        if self.name == 'irrPaddy':
            self.openWaterEvap =  \
             pcr.min(\
             pcr.max(0.,self.topWaterLayer), remainingPotETP)  
               # PS: self.potBareSoilEvap +self.potTranspiration = LIMIT
               #     - DW, RvB, and YW use self.totalPotETP as the LIMIT. EHS does not agree (24 April 2013).
        #
        # update potBareSoilEvap & potTranspiration (after openWaterEvap)
        self.potBareSoilEvap  =       pcr.cover( self.potBareSoilEvap -\
                               (self.potBareSoilEvap/remainingPotETP)*
                                self.openWaterEvap, 0.0)       
        self.potTranspiration =       pcr.cover( self.potTranspiration-\
                              (self.potTranspiration/remainingPotETP)*
                                self.openWaterEvap, 0.0)       

        # update top water layer after openWaterEvap
        self.topWaterLayer = pcr.max(0.,self.topWaterLayer - self.openWaterEvap)

    def calculateInfiltration(self, parameters):

        # infiltration, limited with KSat1 and available water in topWaterLayer
        if self.numberOfLayers == 2:
            self.infiltration = pcr.min(self.topWaterLayer,parameters.kSatUpp)             # P0_L = min(P0_L,KS1*Duration*timeslice());

        if self.numberOfLayers == 3:
            self.infiltration = pcr.min(self.topWaterLayer,parameters.kSatUpp000005)       # P0_L = min(P0_L,KS1*Duration*timeslice());

        # update top water layer after infiltration
        self.topWaterLayer = self.topWaterLayer - self.infiltration

    def estimateTranspirationAndBareSoilEvap(self, parameters):

        # TRANSPIRATION
        #
        # - partitioning transpiration (based on actual each layer storage)
        #
        if self.numberOfLayers == 2:
            dividerTranspFracs = pcr.max( 1e-9, self.adjRootFrUpp*self.storUpp +\
                                                self.adjRootFrLow*self.storLow )
            transpFracUpp = \
                pcr.ifthenelse((self.storUpp + self.storLow) > 0.,\
                               self.adjRootFrUpp*self.storUpp/ dividerTranspFracs, \
                               self.adjRootFrUpp)
            transpFracLow = \
                pcr.ifthenelse((self.storUpp + self.storLow) > 0.,\
                               self.adjRootFrLow*self.storLow/ dividerTranspFracs, \
                               self.adjRootFrLow)                                              #   WF1= if((S1_L[TYPE]+S2_L[TYPE])>0,RFW1[TYPE]*S1_L[TYPE]/
                                                                                               #    max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW1[TYPE]);
                                                                                               #   WF2= if((S1_L[TYPE]+S2_L[TYPE])>0,RFW2[TYPE]*S2_L[TYPE]/
                                                                                               #    max(1e-9,RFW1[TYPE]*S1_L[TYPE]+RFW2[TYPE]*S2_L[TYPE]),RFW2[TYPE]);
        if self.numberOfLayers == 3:
            dividerTranspFracs = pcr.max( 1e-9, self.adjRootFrUpp000005*self.storUpp000005 +\
                                                self.adjRootFrUpp005030*self.storUpp005030 +\
                                                self.adjRootFrLow030150*self.storLow030150)
            transpFracUpp000005 = \
                pcr.ifthenelse((self.storUpp000005 + \
                                self.storUpp005030 + \
                                self.storLow030150) > 0.,\
                                self.adjRootFrUpp000005*self.storUpp000005/ dividerTranspFracs, \
                                self.adjRootFrUpp000005)
            transpFracUpp005030 = \
                pcr.ifthenelse((self.storUpp000005 + \
                                self.storUpp005030 + \
                                self.storLow030150) > 0.,\
                                self.adjRootFrUpp005030*self.storUpp005030/ dividerTranspFracs, \
                                self.adjRootFrUpp005030)
            transpFracLow030150 = \
                pcr.ifthenelse((self.storUpp000005 + \
                                self.storUpp005030 + \
                                self.storLow030150) > 0.,\
                                self.adjRootFrLow030150*self.storLow030150/ dividerTranspFracs, \
                                self.adjRootFrLow030150)

        # - relActTranspiration = fraction actual transpiration over potential transpiration 
        relActTranspiration = (parameters.rootZoneWaterStorageCap  + \
                       self.arnoBeta*self.rootZoneWaterStorageRange*(1.- \
                   (1.+self.arnoBeta)/self.arnoBeta*self.WFRACB)) / \
                                  (parameters.rootZoneWaterStorageCap  + \
                       self.arnoBeta*self.rootZoneWaterStorageRange*(1.- self.WFRACB))   # original Rens's line: 
                                                                                         # FRACTA[TYPE] = (WMAX[TYPE]+BCF[TYPE]*WRANGE[TYPE]*(1-(1+BCF[TYPE])/BCF[TYPE]*WFRACB))/
                                                                                         #                (WMAX[TYPE]+BCF[TYPE]*WRANGE[TYPE]*(1-WFRACB));
        relActTranspiration = (1.-self.satAreaFrac) / \
              (1.+(pcr.max(0.01,relActTranspiration)/self.effSatAt50)**\
                                           (self.effPoreSizeBetaAt50*pcr.scalar(-3.0)))  # original Rens's line:
                                                                                         # FRACTA[TYPE] = (1-SATFRAC_L)/(1+(max(0.01,FRACTA[TYPE])/THEFF_50[TYPE])**(-3*BCH_50));
        relActTranspiration = pcr.max(0.0, relActTranspiration)
        relActTranspiration = pcr.min(1.0, relActTranspiration)
        
        # estimates of actual transpiration fluxes:
        if self.numberOfLayers == 2:
            self.actTranspiUpp = \
              relActTranspiration*transpFracUpp*self.potTranspiration
            self.actTranspiLow = \
              relActTranspiration*transpFracLow*self.potTranspiration
        if self.numberOfLayers == 3:
            self.actTranspiUpp000005 = \
              relActTranspiration*transpFracUpp000005*self.potTranspiration
            self.actTranspiUpp005030 = \
              relActTranspiration*transpFracUpp005030*self.potTranspiration
            self.actTranspiLow030150 = \
              relActTranspiration*transpFracLow030150*self.potTranspiration
        
        # BARE SOIL EVAPORATION
        #        
        # actual bare soil evaporation (potential)
        self.actBareSoilEvap = pcr.scalar(0.0)
        if self.numberOfLayers == 2:
            self.actBareSoilEvap =     self.satAreaFrac * pcr.min(\
                                   self.potBareSoilEvap,parameters.kSatUpp) + \
                                  (1.-self.satAreaFrac)* pcr.min(\
                                   self.potBareSoilEvap,self.kUnsatUpp)            # ES_a[TYPE] =  SATFRAC_L *min(ES_p[TYPE],KS1[TYPE]*Duration*timeslice())+
                                                                                   #            (1-SATFRAC_L)*min(ES_p[TYPE],KTHEFF1*Duration*timeslice());
        if self.numberOfLayers == 3:
            self.actBareSoilEvap =     self.satAreaFrac * pcr.min(\
                                   self.potBareSoilEvap,parameters.kSatUpp000005) + \
                                  (1.-self.satAreaFrac)* pcr.min(\
                                   self.potBareSoilEvap,self.kUnsatUpp000005)

        # no bare soil evaporation in the inundated paddy field 
        if self.name == 'irrPaddy':
            self.actBareSoilEvap = pcr.ifthenelse(self.topWaterLayer > 0.0, 0.0, self.actBareSoilEvap) 


    def estimateSoilFluxes(self,parameters,capRiseFrac):

        # Given states, we estimate all fluxes.
        ################################################################
        
        if self.numberOfLayers == 2:

            # - percolation from storUpp to storLow
            self.percUpp = self.kThVertUppLow * 1.
            self.percUpp = \
                 pcr.ifthenelse(     self.effSatUpp > parameters.effSatAtFieldCapUpp, \
                 pcr.min(pcr.max(0., self.effSatUpp - parameters.effSatAtFieldCapUpp)*parameters.storCapUpp, self.percUpp), self.percUpp) + \
                 pcr.max(0.,self.infiltration - \
                 (parameters.storCapUpp-self.storUpp))                      # original Rens's line:
                                                                            #   P1_L[TYPE] = KTHVERT*Duration*timeslice();
                                                                            #   P1_L[TYPE] = if(THEFF1 > THEFF1_FC[TYPE],min(max(0,THEFF1-THEFF1_FC[TYPE])*SC1[TYPE],
                                                                            #                P1_L[TYPE]),P1_L[TYPE])+max(0,P0_L[TYPE]-(SC1[TYPE]-S1_L[TYPE]));
            # - percolation from storLow to storGroundwater
            self.percLow = pcr.min(self.kUnsatLow,pcr.sqrt(\
                             parameters.kUnsatAtFieldCapLow*\
                                             self.kUnsatLow))               # original Rens's line:
                                                                            #    P2_L[TYPE] = min(KTHEFF2,sqrt(KTHEFF2*KTHEFF2_FC[TYPE]))*Duration*timeslice()
            # - capillary rise to storUpp from storLow
            self.capRiseUpp = \
             pcr.min(pcr.max(0.,\
                             parameters.effSatAtFieldCapUpp - \
                             self.effSatUpp)*parameters.storCapUpp,\
                            self.kThVertUppLow  * self.gradientUppLow)      # original Rens's line:
                                                                            #  CR1_L[TYPE] = min(max(0,THEFF1_FC[TYPE]-THEFF1)*SC1[TYPE],KTHVERT*GRAD*Duration*timeslice());

            # - capillary rise to storLow from storGroundwater (m)
            self.capRiseLow = 0.5*(self.satAreaFrac + capRiseFrac)*\
                                       pcr.min((1.-self.effSatLow)*\
                                      pcr.sqrt(parameters.kSatLow* \
                                                   self.kUnsatLow),\
                       pcr.max(0.0,parameters.effSatAtFieldCapLow- \
                                                   self.effSatLow)*\
                                            parameters.storCapLow)          # original Rens's line:
                                                                            #  CR2_L[TYPE] = 0.5*(SATFRAC_L+CRFRAC)*min((1-THEFF2)*sqrt(KS2[TYPE]*KTHEFF2)*Duration*timeslice(),
                                                                            #                max(0,THEFF2_FC[TYPE]-THEFF2)*SC2[TYPE]);

            # - interflow (m)
            percToInterflow = parameters.percolationImp*(\
                                     self.percUpp+self.capRiseLow-\
                                    (self.percLow+self.capRiseUpp))
            self.interflow = pcr.max(\
                              parameters.interflowConcTime*percToInterflow  +\
              (pcr.scalar(1.)-parameters.interflowConcTime)*self.interflow, 0.0)
            
        if self.numberOfLayers == 3:

            # - percolation from storUpp000005 to storUpp005030 (m)
            self.percUpp000005 = self.kThVertUpp000005Upp005030 * 1.
            self.percUpp000005 = \
                 pcr.ifthenelse(     self.effSatUpp000005 > parameters.effSatAtFieldCapUpp000005, \
                 pcr.min(pcr.max(0., self.effSatUpp000005 - parameters.effSatAtFieldCapUpp000005)*parameters.storCapUpp000005, self.percUpp000005), self.percUpp000005) + \
                 pcr.max(0.,self.infiltration - \
                 (parameters.storCapUpp000005-self.storUpp000005))

            # - percolation from storUpp005030 to storLow030150 (m)
            self.percUpp005030 = self.kThVertUpp005030Low030150 * 1.
            self.percUpp005030 = \
                 pcr.ifthenelse(     self.effSatUpp005030 > parameters.effSatAtFieldCapUpp005030, \
                 pcr.min(pcr.max(0., self.effSatUpp005030 - parameters.effSatAtFieldCapUpp005030)*parameters.storCapUpp005030, self.percUpp005030), self.percUpp005030) + \
                 pcr.max(0.,self.percUpp000005 - \
                 (parameters.storCapUpp005030-self.storUpp005030))

            # - percolation from storLow030150 to storGroundwater (m)
            self.percLow030150 = pcr.min(self.kUnsatLow030150,pcr.sqrt(\
                         parameters.kUnsatAtFieldCapLow030150*\
                                         self.kUnsatLow030150))

            # - capillary rise to storUpp000005 from storUpp005030 (m)
            self.capRiseUpp000005 = pcr.min(pcr.max(0.,\
                          parameters.effSatAtFieldCapUpp000005 - \
                                          self.effSatUpp000005)* \
                                   parameters.storCapUpp000005, \
                                self.kThVertUpp000005Upp005030* \
                               self.gradientUpp000005Upp005030)

            # - capillary rise to storUpp005030 from storLow030150 (m)
            self.capRiseUpp005030 = pcr.min(pcr.max(0.,\
                          parameters.effSatAtFieldCapUpp005030 - \
                                          self.effSatUpp005030)* \
                                   parameters.storCapUpp005030, \
                                self.kThVertUpp005030Low030150* \
                               self.gradientUpp005030Low030150)

            # - capillary rise to storLow030150 from storGroundwater (m)
            self.capRiseLow030150 = 0.5*(self.satAreaFrac + capRiseFrac)*\
                                 pcr.min((1.-self.effSatLow030150)*\
                                pcr.sqrt(parameters.kSatLow030150* \
                                             self.kUnsatLow030150),\
                 pcr.max(0.0,parameters.effSatAtFieldCapLow030150- \
                                             self.effSatLow030150)*\
                                      parameters.storCapLow030150)

            # - interflow (m)
            percToInterflow = parameters.percolationImp*(\
                                     self.percUpp005030+self.capRiseLow030150-\
                                    (self.percLow030150+self.capRiseUpp005030))
            self.interflow = pcr.max(\
                              parameters.interflowConcTime*percToInterflow  +\
              (pcr.scalar(1.)-parameters.interflowConcTime)*self.interflow, 0.0)

    def scaleAllFluxes(self, parameters, groundwater):

        # We re-scale all fluxes (based on available water).
        ########################################################################################################################################
        # 

        if self.numberOfLayers == 2:

            # scale fluxes (for Upp)
            ADJUST = self.actBareSoilEvap + self.actTranspiUpp + self.percUpp
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap = ADJUST*self.actBareSoilEvap
            self.actTranspiUpp   = ADJUST*self.actTranspiUpp
            self.percUpp         = ADJUST*self.percUpp                      # original Rens's line:
                                                                            # ADJUST = ES_a[TYPE]+T_a1[TYPE]+P1_L[TYPE];
                                                                            # ADJUST = if(ADJUST>0,min(1,(max(0,S1_L[TYPE]+P0_L[TYPE]))/ADJUST),0);
                                                                            # ES_a[TYPE] = ADJUST*ES_a[TYPE];
                                                                            # T_a1[TYPE] = ADJUST*T_a1[TYPE];
                                                                            # P1_L[TYPE] = ADJUST*P1_L[TYPE];

            # scale fluxes (for Low)
            ADJUST = self.actTranspiLow + self.percLow + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow + \
                                              self.percUpp)/ADJUST),0.)
            self.actTranspiLow = ADJUST*self.actTranspiLow
            self.percLow       = ADJUST*self.percLow
            self.interflow     = ADJUST*self.interflow                      # original Rens's line:
                                                                            # ADJUST = T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE];
                                                                            # ADJUST = if(ADJUST>0,min(1,max(S2_L[TYPE]+P1_L[TYPE],0)/ADJUST),0);
                                                                            # T_a2[TYPE] = ADJUST*T_a2[TYPE];
                                                                            # P2_L[TYPE] = ADJUST*P2_L[TYPE];
                                                                            # Q2_L[TYPE] = ADJUST*Q2_L[TYPE];

            # capillary rise to storLow is limited to available storGroundwater 
            # 
            # The following is for a conservative approach (used by Rens)
            #  - using fracVegCover as "safectyFactor".                     # EHS (02 Sep 2013): NOT NEEDED
            #~ self.capRiseLow = \
                             #~ pcr.min(self.fracVegCover*\
                             #~ groundwater.storGroundwater,\
                             #~ self.capRiseLow)                            # CR2_L[TYPE]= min(VEGFRAC[TYPE]*S3,CR2_L[TYPE])
            # 
            #  - without fracVegCover (without safetyFactor)
            #~ self.capRiseLow = pcr.max(0.,\
                              #~ pcr.min(\
                              #~ groundwater.storGroundwater,self.capRiseLow))
            # 
            # also limited with reducedCapRise 
            #
            self.capRiseLow = pcr.max(0.,\
                              pcr.min(\
                              pcr.max(0.,\
                              groundwater.storGroundwater-self.reducedCapRise),self.capRiseLow))

            # capillary rise to storUpp is limited to available storLow
            #
            estimateStorLowBeforeCapRise = pcr.max(0,self.storLow + self.percUpp - \
                                              (self.actTranspiLow + self.percLow + self.interflow ))
            self.capRiseUpp = pcr.min(\
                              estimateStorLowBeforeCapRise,self.capRiseUpp)     # original Rens's line: 
                                                                                #  CR1_L[TYPE] = min(max(0,S2_L[TYPE]+P1_L[TYPE]-(T_a2[TYPE]+P2_L[TYPE]+Q2_L[TYPE])),CR1_L[TYPE])

        if self.numberOfLayers == 3:

            # scale fluxes (for Upp000005)
            ADJUST = self.actBareSoilEvap + self.actTranspiUpp000005 + self.percUpp000005
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp000005 + \
                                              self.infiltration) / ADJUST),0.)
            self.actBareSoilEvap     = ADJUST*self.actBareSoilEvap
            self.actTranspiUpp000005 = ADJUST*self.actTranspiUpp000005
            self.percUpp000005       = ADJUST*self.percUpp000005
            
            # scale fluxes (for Upp000005)
            ADJUST = self.actTranspiUpp005030 + self.percUpp005030
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storUpp005030 + \
                                              self.percUpp000005)/ ADJUST),0.)
            self.actTranspiUpp005030 = ADJUST*self.actTranspiUpp005030
            self.percUpp005030       = ADJUST*self.percUpp005030

            # scale fluxes (for Low030150)
            ADJUST = self.actTranspiLow030150 + self.percLow030150 + self.interflow
            ADJUST = pcr.ifthenelse(ADJUST>0.0, \
                     pcr.min(1.0,pcr.max(0.0, self.storLow030150 + \
                                              self.percUpp005030)/ADJUST),0.)
            self.actTranspiLow030150 = ADJUST*self.actTranspiLow030150
            self.percLow030150       = ADJUST*self.percLow030150
            self.interflow           = ADJUST*self.interflow   

            # capillary rise to storLow is limited to available storGroundwater 
            # and also limited with reducedCapRise 
            #
            self.capRiseLow030150 = pcr.max(0.,\
                                    pcr.min(\
                                    pcr.max(0.,\
                                    groundwater.storGroundwater-\
                                    self.reducedCapRise),\
                                    self.capRiseLow030150))

            # capillary rise to storUpp005030 is limited to available storLow030150
            #
            estimateStorLow030150BeforeCapRise = pcr.max(0,self.storLow030150 + self.percUpp005030 - \
                                                    (self.actTranspiLow030150 + self.percLow030150 + self.interflow ))
            self.capRiseUpp005030 = pcr.min(\
                                    estimateStorLow030150BeforeCapRise,self.capRiseUpp005030)

            # capillary rise to storUpp000005 is limited to available storUpp005030
            #
            estimateStorUpp005030BeforeCapRise = pcr.max(0,self.storUpp005030 + self.percUpp000005 - \
                                                    (self.actTranspiUpp005030 + self.percUpp005030))
            self.capRiseUpp000005 = pcr.min(\
                                    estimateStorUpp005030BeforeCapRise,self.capRiseUpp000005)

    def updateSoilStates(self, parameters):

        # We give new states and make sure that no storage capacities will be exceeded.
        #################################################################################
        
        if self.numberOfLayers == 2:
            
            # update storLow after the following fluxes: 
            # + percUpp
            # + capRiseLow
            # - percLow
            # - interflow
            # - actTranspiLow
            # - capRiseUpp
            #
            self.storLow = pcr.max(0., self.storLow + \
                                       self.percUpp + \
                                       self.capRiseLow - \
                       (self.percLow + self.interflow + \
                                       self.actTranspiLow +\
                                       self.capRiseUpp))                    # S2_L[TYPE]= max(0,S2_L[TYPE]+P1_L[TYPE]+CR2_L[TYPE]-
                                                                            #             (P2_L[TYPE]+Q2_L[TYPE]+CR1_L[TYPE]+T_a2[TYPE]));          
            #
            # If necessary, reduce percolation input:
            percUpp      = self.percUpp
            self.percUpp = pcr.max(0., percUpp - \
                           pcr.max(0.,self.storLow - \
                                 parameters.storCapLow))                    
            #~ self.percUpp = percUpp - \
                           #~ pcr.max(0.,self.storLow - \
                                 #~ parameters.storCapLow)                  # Rens's line: P1_L[TYPE] = P1_L[TYPE]-max(0,S2_L[TYPE]-SC2[TYPE]);
                                                                         #~ # PS: In the original Rens's code, P1 can be negative. 
            self.storLow = self.storLow -  percUpp + \
                                      self.percUpp     
            # If necessary, reduce capRise input:
            capRiseLow      = self.capRiseLow
            self.capRiseLow = pcr.max(0.,capRiseLow - \
                              pcr.max(0.,self.storLow - \
                                       parameters.storCapLow))
            self.storLow    = self.storLow - capRiseLow + \
                                        self.capRiseLow      
            # If necessary, increase interflow outflow:
            addInterflow          = pcr.max(0.,\
                        self.storLow - parameters.storCapLow)
            self.interflow       += addInterflow
            self.storLow         -= addInterflow      
        
            self.storLow = pcr.min(self.storLow,\
                                 parameters.storCapLow) 
        
            #
            # update storUpp after the following fluxes: 
            # + infiltration
            # + capRiseUpp
            # - percUpp
            # - actTranspiUpp
            # - actBareSoilEvap
            #
            self.storUpp = pcr.max(0.,self.storUpp + \
                                      self.infiltration + \
                                      self.capRiseUpp - \
                                     (self.percUpp + \
                 self.actTranspiUpp + self.actBareSoilEvap))                # Rens's line:  S1_L[TYPE]= max(0,S1_L[TYPE]+P0_L[TYPE]+CR1_L[TYPE]-
                                                                            #              (P1_L[TYPE]+T_a1[TYPE]+ES_a[TYPE])); #*
            #
            # any excess above storCapUpp is handed to topWaterLayer
            self.satExcess = pcr.max(0.,self.storUpp - \
                               parameters.storCapUpp)									
            self.topWaterLayer =  self.topWaterLayer + self.satExcess
        
            # any excess above minTopWaterLayer is released as directRunoff                               
            self.directRunoff  = self.directRunoff + \
                                 pcr.max(0.,self.topWaterLayer - \
                                            self.minTopWaterLayer)
        
            # make sure that storage capacities are not exceeded
            self.topWaterLayer = pcr.min( self.topWaterLayer , \
                                          self.minTopWaterLayer)
            self.storUpp       = pcr.min(self.storUpp,\
                                 parameters.storCapUpp)
            self.storLow       = pcr.min(self.storLow,\
                                 parameters.storCapLow) 
        
            # total actual evaporation + transpiration
            self.actualET += self.actBareSoilEvap + \
                             self.openWaterEvap   + \
                             self.actTranspiUpp + \
                             self.actTranspiLow
            
            # total actual transpiration
            self.actTranspiTotal = self.actTranspiUpp + \
                                   self.actTranspiLow
            
            # net percolation between upperSoilStores (positive indicating downward direction)
            self.netPercUpp = self.percUpp - self.capRiseUpp

            # groundwater recharge (positive indicating downward direction)
            self.gwRecharge = self.percLow - self.capRiseLow
        
            # the following variables introduced for the comparison with threeLayer model output                        
            self.storUppTotal       = self.storUpp
            self.storLowTotal       = self.storLow
            self.actTranspiUppTotal = self.actTranspiUpp
            self.actTranspiLowTotal = self.actTranspiLow
            self.interflowTotal     = self.interflow

        if self.numberOfLayers == 3:
            
            # update storLow030150 after the following fluxes: 
            # + percUpp005030
            # + capRiseLow030150
            # - percLow030150
            # - interflow
            # - actTranspiLow030150
            # - capRiseUpp005030
            #
            self.storLow030150 = pcr.max(0., self.storLow030150 + \
                                             self.percUpp005030 + \
                                          self.capRiseLow030150 - \
                           (self.percLow030150 + self.interflow + \
                                       self.actTranspiLow030150 +\
                                          self.capRiseUpp005030))          
            #
            # If necessary, reduce percolation input:
            percUpp005030      = self.percUpp005030
            self.percUpp005030 = pcr.max(0., percUpp005030 - \
                             pcr.max(0.,self.storLow030150 - \
                               parameters.storCapLow030150))                    
            self.storLow030150 =        self.storLow030150 - \
                                             percUpp005030 + \
                                        self.percUpp005030     
            #
            # If necessary, reduce capRise input:
            capRiseLow030150      = self.capRiseLow030150
            self.capRiseLow030150 = pcr.max(0.,capRiseLow030150 - \
                                  pcr.max(0.,self.storLow030150 - \
                                    parameters.storCapLow030150))
            self.storLow030150    =          self.storLow030150 - \
                                               capRiseLow030150 + \
                                          self.capRiseLow030150
            #
            # If necessary, increase interflow outflow:
            addInterflow          = pcr.max(0.,\
                                    self.storLow030150 - parameters.storCapLow030150)
            self.interflow       += addInterflow
            self.storLow030150   -= addInterflow      
        
            self.storLow030150 = pcr.min(self.storLow030150,\
                                 parameters.storCapLow030150) 
        
            # update storUpp005030 after the following fluxes: 
            # + percUpp000005
            # + capRiseUpp005030
            # - percUpp005030
            # - actTranspiUpp005030
            # - capRiseUpp000005
            #
            self.storUpp005030 = pcr.max(0., self.storUpp005030 + \
                                             self.percUpp000005 + \
                                          self.capRiseUpp005030 - \
                                            (self.percUpp005030 + \
                                       self.actTranspiUpp005030 + \
                                          self.capRiseUpp000005))          
            #
            # If necessary, reduce percolation input:
            percUpp000005      = self.percUpp000005
            self.percUpp000005 = pcr.max(0., percUpp000005 - \
                             pcr.max(0.,self.storUpp005030 - \
                               parameters.storCapUpp005030))                    
            self.storUpp005030 =        self.storUpp005030 - \
                                             percUpp000005 + \
                                        self.percUpp000005     
            #
            # If necessary, reduce capRise input:
            capRiseUpp005030      = self.capRiseUpp005030
            self.capRiseUpp005030 = pcr.max(0.,capRiseUpp005030 - \
                                  pcr.max(0.,self.storUpp005030 - \
                                    parameters.storCapUpp005030))
            self.storUpp005030    =          self.storUpp005030 - \
                                               capRiseUpp005030 + \
                                          self.capRiseUpp005030
            #
            # If necessary, introduce interflow outflow:
            self.interflowUpp005030 = pcr.max(0.,\
                 self.storUpp005030 - parameters.storCapUpp005030)
            self.storUpp005030      = self.storUpp005030 - \
                                 self.interflowUpp005030      

            # update storUpp000005 after the following fluxes: 
            # + infiltration
            # + capRiseUpp000005
            # - percUpp000005
            # - actTranspiUpp000005
            # - actBareSoilEvap
            #
            self.storUpp000005 = pcr.max(0.,self.storUpp000005 + \
                                            self.infiltration  + \
                                         self.capRiseUpp000005 - \
                                           (self.percUpp000005 + \
                                      self.actTranspiUpp000005 + \
                                          self.actBareSoilEvap))
            #
            # any excess above storCapUpp is handed to topWaterLayer
            self.satExcess     = pcr.max(0.,self.storUpp000005 - \
                                   parameters.storCapUpp000005)									
            self.topWaterLayer = self.topWaterLayer + self.satExcess
        
            # any excess above minTopWaterLayer is released as directRunoff                               
            self.directRunoff  = self.directRunoff + \
                                 pcr.max(0.,self.topWaterLayer - \
                                            self.minTopWaterLayer)
        
            # make sure that storage capacities are not exceeded
            self.topWaterLayer = pcr.min( self.topWaterLayer , \
                                          self.minTopWaterLayer)
            self.storUpp000005 = pcr.min(self.storUpp000005,\
                                parameters.storCapUpp000005)
            self.storUpp005030 = pcr.min(self.storUpp005030,\
                                parameters.storCapUpp005030)
            self.storLow030150 = pcr.min(self.storLow030150,\
                                parameters.storCapLow030150)

            # total actual evaporation + transpiration
            self.actualET += self.actBareSoilEvap + \
                             self.openWaterEvap   + \
                             self.actTranspiUpp000005 + \
                             self.actTranspiUpp005030 + \
                             self.actTranspiLow030150
            
            # total actual transpiration
            self.actTranspiUppTotal = self.actTranspiUpp000005 + \
                                      self.actTranspiUpp005030

            # total actual transpiration
            self.actTranspiTotal = self.actTranspiUppTotal + \
                                   self.actTranspiLow030150
            
            # net percolation between upperSoilStores (positive indicating downward direction)
            self.netPercUpp000005 = self.percUpp000005 - self.capRiseUpp000005
            self.netPercUpp005030 = self.percUpp005030 - self.capRiseUpp005030

            # groundwater recharge
            self.gwRecharge = self.percLow030150 - self.capRiseLow030150
        
            # the following variables introduced for the comparison with twoLayer model output                        
            self.storUppTotal       = self.storUpp000005 + self.storUpp005030
            self.storLowTotal       = self.storLow030150
            self.actTranspiUppTotal = self.actTranspiUpp000005 + self.actTranspiUpp005030
            self.actTranspiLowTotal = self.actTranspiLow030150
            self.interflowTotal     = self.interflow + self.interflowUpp005030

        # variables / states that are defined the twoLayer and threeLayer model:
        ########################################################################
        
        # landSurfaceRunoff (needed for routing)                        
        self.landSurfaceRunoff = self.directRunoff + self.interflowTotal

    def upperSoilUpdate(self,meteo,groundwater,routing,\
                        parameters,capRiseFrac,\
                        nonIrrGrossDemand,swAbstractionFraction,\
                        currTimeStep,\
                        allocSegments):

        if self.debugWaterBalance == str('True'):
            netLqWaterToSoil = self.netLqWaterToSoil # input            
            preTopWaterLayer = self.topWaterLayer
            if self.numberOfLayers == 2: 
                preStorUpp       = self.storUpp
                preStorLow       = self.storLow
            if self.numberOfLayers == 3: 
                preStorUpp000005 = self.storUpp000005
                preStorUpp005030 = self.storUpp005030
                preStorLow030150 = self.storLow030150
        
        # given soil storages, we can calculate several derived states, such as 
        # effective degree of saturation, unsaturated hydraulic conductivity, and 
        # readily available water within the root zone.
        self.getSoilStates(parameters)
        
        # calculate water demand (including partitioning to different source)
        self.calculateWaterDemand(parameters, \
                                  nonIrrGrossDemand, swAbstractionFraction, \
                                  groundwater, routing, \
                                  allocSegments)

        # calculate openWaterEvap: open water evaporation from the paddy field, 
        # and update topWaterLayer after openWaterEvap.  
        self.calculateOpenWaterEvap()
        
        # calculate directRunoff and infiltration, based on the improved Arno scheme (Hageman and Gates, 2003):
        # and update topWaterLayer (after directRunoff and infiltration).  
        self.calculateDirectRunoff(parameters)
        self.calculateInfiltration(parameters)

        # estimate transpiration and bare soil evaporation:
        self.estimateTranspirationAndBareSoilEvap(parameters)
        
        # estimate percolation and capillary rise, as well as interflow
        self.estimateSoilFluxes(parameters,capRiseFrac)

        # all fluxes are limited to available (source) storage
        self.scaleAllFluxes(parameters, groundwater)

        # update all soil states (including get final/corrected fluxes) 
        self.updateSoilStates(parameters)

        if self.debugWaterBalance == str('True'):
            #
            vos.waterBalanceCheck([netLqWaterToSoil,\
                                   self.irrGrossDemand,\
                                   self.satExcess],\
                                  [self.directRunoff,
                                   self.openWaterEvap,
                                   self.infiltration],\
                                  [  preTopWaterLayer],\
                                  [self.topWaterLayer],\
                                       'topWaterLayer',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
            
            if self.numberOfLayers == 2: 
                # 
                vos.waterBalanceCheck([self.infiltration,
                                       self.capRiseUpp],\
                                      [self.actTranspiUpp,
                                       self.percUpp,
                                       self.actBareSoilEvap,
                                       self.satExcess],\
                                      [  preStorUpp],\
                                      [self.storUpp],\
                                           'storUpp',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                # 
                vos.waterBalanceCheck([self.percUpp],\
                                      [self.actTranspiLow,
                                       self.gwRecharge,
                                       self.interflow,
                                       self.capRiseUpp],\
                                      [  preStorLow],\
                                      [self.storLow],\
                                           'storLow',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                #
                vos.waterBalanceCheck([self.infiltration,\
                                       self.capRiseLow],\
                                      [self.satExcess,
                                       self.interflow,
                                       self.percLow,
                                       self.actTranspiUpp,
                                       self.actTranspiLow,
                                       self.actBareSoilEvap],\
                                      [  preStorUpp,
                                         preStorLow],\
                                      [self.storUpp,
                                       self.storLow],\
                                      'entireSoilLayers',\
                                       True,\
                                       currTimeStep.fulldate,threshold=1e-4)
                #
                vos.waterBalanceCheck([netLqWaterToSoil,
                                       self.capRiseLow,
                                       self.irrGrossDemand],\
                                      [self.directRunoff,
                                       self.interflow,
                                       self.percLow,
                                       self.actTranspiUpp,
                                       self.actTranspiLow,
                                       self.actBareSoilEvap,
                                       self.openWaterEvap],\
                                      [  preTopWaterLayer,
                                         preStorUpp,
                                         preStorLow],\
                                      [self.topWaterLayer,
                                       self.storUpp,
                                       self.storLow],\
                                      'allLayers',\
                                       True,\
                                       currTimeStep.fulldate,threshold=5e-4)

            if self.numberOfLayers == 3: 
                vos.waterBalanceCheck([self.infiltration,
                                       self.capRiseUpp000005],\
                                      [self.actTranspiUpp000005,
                                       self.percUpp000005,
                                       self.actBareSoilEvap,
                                       self.satExcess],\
                                      [  preStorUpp000005],\
                                      [self.storUpp000005],\
                                           'storUpp000005',True,\
                                       currTimeStep.fulldate,threshold=1e-5)

                # 
                vos.waterBalanceCheck([self.percUpp000005,
                                       self.capRiseUpp005030],\
                                      [self.actTranspiUpp005030,
                                       self.percUpp005030,
                                       self.interflowUpp005030,
                                       self.capRiseUpp000005],\
                                      [  preStorUpp005030],\
                                      [self.storUpp005030],\
                                           'storUpp005030',True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                #
                vos.waterBalanceCheck([self.percUpp005030],\
                                      [self.actTranspiLow030150,
                                       self.gwRecharge,
                                       self.interflow,
                                       self.capRiseUpp005030],\
                                      [  preStorLow030150],\
                                      [self.storLow030150],\
                                           'storLow030150',True,\
                                       currTimeStep.fulldate,threshold=1e-5)
                #
                vos.waterBalanceCheck([self.infiltration,\
                                       self.capRiseLow030150],\
                                      [self.satExcess,
                                       self.interflow,
                                       self.interflowUpp005030,
                                       self.percLow030150,
                                       self.actTranspiUpp000005,
                                       self.actTranspiUpp005030,
                                       self.actTranspiLow030150,
                                       self.actBareSoilEvap],\
                                      [  preStorUpp000005,
                                     preStorUpp005030,
                                     preStorLow030150],\
                                  [self.storUpp000005,
                                   self.storUpp005030,
                                   self.storLow030150],\
                                  'entireSoilLayers',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
                #
                vos.waterBalanceCheck([netLqWaterToSoil,
                                       self.capRiseLow030150,
                                       self.irrGrossDemand],\
                                      [self.directRunoff,
                                       self.interflow,
                                       self.interflowUpp005030,
                                       self.percLow030150,
                                       self.actTranspiUpp000005,
                                       self.actTranspiUpp005030,
                                       self.actTranspiLow030150,
                                   self.actBareSoilEvap,
                                   self.openWaterEvap],\
                                  [  preTopWaterLayer,
                                     preStorUpp000005,
                                     preStorUpp005030,
                                     preStorLow030150],\
                                  [self.topWaterLayer,
                                   self.storUpp000005,
                                   self.storUpp005030,
                                   self.storLow030150],\
                                  'allLayers',True,\
                                   currTimeStep.fulldate,threshold=1e-4)
