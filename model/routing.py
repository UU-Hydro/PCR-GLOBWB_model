#!/usr/bin/ python
# -*- coding: utf-8 -*-

import os

from pcraster.framework import *
import pcraster as pcr

import virtualOS as vos
from ncConverter import *

import waterBodies

class Routing(object):
    
    def getState(self):
        result = {}
        
        result['channelStorage'] = self.channelStorage                       #  m3
        result['avgDischarge'] = self.avgDischarge                           #  m3/s
        result['avgBaseflow'] = self.avgBaseflow                             #  m3/s

        result['timestepsToAvgDischarge'] = self.timestepsToAvgDischarge     

        result['riverbedExchange'] = self.riverbedExchange                   #  m3
        
        result['waterBodyStorage'] = self.WaterBodies.waterBodyStorage       #  m3
        result['avgInflow'] = self.WaterBodies.avgInflow                     #  m3/s
        result['avgOutflow'] = self.WaterBodies.avgOutflow                   #  m3/s    
        
        result['m2tDischarge'] = self.m2tDischarge                           # (m3/s)^2
        
        result['readAvlChannelStorage'] = self.readAvlChannelStorage         #  m3
        
        return result

    #TODO: remove
    def getPseudoState(self):
        result = {}
        
        return result


    def getVariables(self, names):
        result = {}
        
        return result

    def __init__(self,iniItems,initialConditions,lddMap):
        object.__init__(self)

        self.lddMap=lddMap

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']

        self.debugWaterBalance = \
                        iniItems.routingOptions['debugWaterBalance']

        #~ self.method = iniItems.routingOptions['routingMethod']
        self.method = "accuTravelTime"                                  # Currently, we only support "accuTravelTime".

        # local drainage direction:
        self.lddMap = vos.readPCRmapClone(\
                  iniItems.routingOptions['lddMap'],
                  self.cloneMap,self.tmpDir,self.inputDir,True)
        self.lddMap = pcr.lddrepair(pcr.ldd(self.lddMap))
        self.lddMap = pcr.lddrepair(self.lddMap)

        # landmask:
        if iniItems.globalOptions['landmask'] != "None":
           self.landmask = vos.readPCRmapClone(\
           iniItems.globalOptions['landmask'],
           self.cloneMap,self.tmpDir,self.inputDir)
        else:   	
           self.landmask = pcr.defined(self.lddMap)

        self.cellArea = vos.readPCRmapClone(\
                  iniItems.routingOptions['cellAreaMap'],
                  self.cloneMap,self.tmpDir,self.inputDir)

        self.cellSizeInArcDeg = vos.getMapAttributes(\
                                    self.cloneMap,"cellsize")  

        # maximum memory time-length of AvgDischarge (long term)
        self.maxTimestepsToAvgDischargeShort = vos.readPCRmapClone(\
                  iniItems.routingOptions['maxTimestepsToAvgDischargeShorTerm'],
                  self.cloneMap,self.tmpDir,self.inputDir)                            

        # maximum memory time-length of AvgDischarge (short term)
        self.maxTimestepsToAvgDischargeLong  = vos.readPCRmapClone(\
                  iniItems.routingOptions['maxTimestepsToAvgDischargeLongTerm'],
                  self.cloneMap,self.tmpDir,self.inputDir)                            

        if self.method == "accuTravelTime":

            routingParameters = ['gradient','manningsN']
            for var in routingParameters:
                input = iniItems.routingOptions[str(var)]
                vars(self)[var] = vos.readPCRmapClone(input,\
                                self.cloneMap,self.tmpDir,self.inputDir)

            self.eta = 0.25
            self.nu  = 0.40
            self.tau = 8.00
            self.phi = 0.58

            #  cellLength (m) is approximated cell diagonal   
            cellSizeInArcMin    =  self.cellSizeInArcDeg*60.
            verticalSizeInMeter =  cellSizeInArcMin*1852.                            
            #
            self.cellLengthFD = ((self.cellArea/verticalSizeInMeter)**(2)+\
                                               (verticalSizeInMeter)**(2))\
                                                                    **(0.5) 
            nrCellsDownstream  = pcr.ldddist(self.lddMap,\
                                             self.lddMap == 5,1.)
            distanceDownstream = pcr.ldddist(self.lddMap,\
                                             self.lddMap == 5,\
                                             self.cellLengthFD)
            channelLengthDownstream = \
                    (self.cellLengthFD + distanceDownstream)/\
                    (nrCellsDownstream + 1)                 # unit: m
            self.dist2celllength  = channelLengthDownstream /\
                                      self.cellSizeInArcDeg # unit: m/arcDegree  
                                      
        # the channel gradient must be >= minGradient 
        minGradient   = 0.000005
        self.gradient = pcr.max(minGradient,\
                        pcr.cover(self.gradient, minGradient))

        #TODO: 26 Feb 2014, Edwin found that reasonable runs are only found 
        # if all of these options = True.                    
        self.includeWaterBodies = "True"
        self.includeLakes = "True"
        self.includeReservoirs =  "True"
        
        # initiate/create WaterBody class
        self.WaterBodies = waterBodies.WaterBodies(iniItems)

        self.fileCropKC = vos.getFullPath(\
                     iniItems.routingOptions['cropCoefficientWaterNC'],\
                     self.inputDir)

        self.report = True
        if self.report == True:
            # daily output in netCDF files:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            #
            self.outDailyTotNC = iniItems.routingOptions['outDailyTotNC'].split(",")
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_dailyTot.nc",\
                                                    var,"undefined")
            # MONTHly output in netCDF files:
            # - cummulative
            self.outMonthTotNC = iniItems.routingOptions['outMonthTotNC'].split(",")
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initiating monthlyVarTot (accumulator variable):
                    vars(self)[var+'MonthTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthTot.nc",\
                                                    var,"undefined")
            # - average
            self.outMonthAvgNC = iniItems.routingOptions['outMonthAvgNC'].split(",")
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
            self.outMonthEndNC = iniItems.routingOptions['outMonthEndNC'].split(",")
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthEnd.nc",\
                                                    var,"undefined")
            # YEARly output in netCDF files:
            # - cummulative
            self.outAnnuaTotNC = iniItems.routingOptions['outAnnuaTotNC'].split(",")
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:
                    # initiating yearly accumulator variable:
                    vars(self)[var+'AnnuaTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaTot.nc",\
                                                    var,"undefined")
            # - average
            self.outAnnuaAvgNC = iniItems.routingOptions['outAnnuaAvgNC'].split(",")
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
            self.outAnnuaEndNC = iniItems.routingOptions['outAnnuaEndNC'].split(",")
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaEnd.nc",\
                                                    var,"undefined")

        #Get the initialconditions
        self.getICs(iniItems, initialConditions)
        
    def getICs(self,iniItems,iniConditions = None):

        if iniConditions == None:

            self.channelStorage = vos.readPCRmapClone(\
                      iniItems.routingOptions['channelStorageIni'],
                      self.cloneMap,self.tmpDir,self.inputDir)
            # PS: channelStorage (m3) includes all storages 
            #     at channels and water bodies (lakes & reservoirs) 
            #     (convention since 02 October 2013 - return to original)

            self.readAvlChannelStorage = vos.readPCRmapClone(\
                      iniItems.routingOptions['readAvlChannelStorageIni'],
                      self.cloneMap,self.tmpDir,self.inputDir)

            self.timestepsToAvgDischarge = vos.readPCRmapClone(\
                  iniItems.routingOptions['timestepsToAvgDischargeIni'],
                      self.cloneMap,self.tmpDir,self.inputDir)

            self.avgDischarge = vos.readPCRmapClone(\
                   iniItems.routingOptions['avgChannelDischargeIni'],
                   self.cloneMap,self.tmpDir,self.inputDir)    
            # m3/s # PS: Since 23 Sept 2013, the unit of avgDischarge should be m3/s   

            self.m2tDischarge = vos.readPCRmapClone(\
                   iniItems.routingOptions['m2tChannelDischargeIni'],
                   self.cloneMap,self.tmpDir,self.inputDir)    

            self.avgBaseflow = vos.readPCRmapClone(\
                   iniItems.routingOptions['avgBaseflowIni'],
                   self.cloneMap,self.tmpDir,self.inputDir)    
            
            self.riverbedExchange = vos.readPCRmapClone(\
                   iniItems.routingOptions['riverbedExchangeIni'],
                   self.cloneMap,self.tmpDir,self.inputDir)    

            # get the initial conditions for water bodies (i.e. lakes and/or reservoirs):   
            self.WaterBodies.getICs(iniItems)

        else:              
            self.channelStorage = iniConditions['routing']['channelStorage']
            
            self.readAvlChannelStorage = \
                                  iniConditions['routing']['readAvlChannelStorage']
            
            self.timestepsToAvgDischarge = \
                                  iniConditions['routing']['timestepsToAvgDischarge']

            self.avgDischarge   = iniConditions['routing']['avgDischarge']


            self.m2tDischarge   = iniConditions['routing']['m2tDischarge']

            self.avgBaseflow    = iniConditions['routing']['avgBaseflow']
            
            self.riverbedExchange = \
                                  iniConditions['routing']['riverbedExchange']    

            # get the initial conditions for water bodies (i.e. lakes and/or reservoirs):   
            self.WaterBodies.getICs(iniItems,iniConditions)
        
        self.channelStorage        = pcr.cover(self.channelStorage,  0.0)
        self.readAvlChannelStorage = pcr.cover(self.readAvlChannelStorage,0.0)
        self.avgDischarge          = pcr.cover(self.avgDischarge,    0.0)
        self.m2tDischarge          = pcr.cover(self.m2tDischarge,    0.0)
        self.avgBaseflow           = pcr.cover(self.avgBaseflow,     0.0)
        self.riverbedExchange      = pcr.cover(self.riverbedExchange,0.0)

        self.channelStorage        = pcr.ifthen(self.landmask, self.channelStorage       )
        self.readAvlChannelStorage = pcr.ifthen(self.landmask, self.readAvlChannelStorage)
        self.avgDischarge          = pcr.ifthen(self.landmask, self.avgDischarge         )
        self.m2tDischarge          = pcr.ifthen(self.landmask, self.m2tDischarge         )
        self.avgBaseflow           = pcr.ifthen(self.landmask, self.avgBaseflow          )
        self.riverbedExchange      = pcr.ifthen(self.landmask, self.riverbedExchange     )

        self.readAvlChannelStorage = pcr.min(self.readAvlChannelStorage, self.channelStorage)
        
        # make sure that timestepsToAvgDischarge is consistent (or the same) for the entire map:
        try:
            self.timestepsToAvgDischarge = pcr.mapmaximum(self.timestepsToAvgDischarge)
        except:    
            pass


    def update(self,landSurface,groundwater,currTimeStep,meteo):

        print("routing in progress")
        
        if self.debugWaterBalance == str('True'):\
           preStorage = self.channelStorage                             # unit: m3


        # runoff from landSurface cells (unit: m)
        self.runoff = landSurface.landSurfaceRunoff +\
                      groundwater.baseflow   

        # update channelStorage (unit: m3) after runoff
        self.channelStorage += self.runoff * self.cellArea

        # update channelStorage (unit: m3) after actSurfaceWaterAbstraction 
        self.channelStorage -= landSurface.actSurfaceWaterAbstract * self.cellArea

        # return flow from (m) non irrigation water demand
        self.nonIrrReturnFlow = landSurface.nonIrrReturnFlowFraction*\
                                landSurface.nonIrrGrossDemand          # m
        nonIrrReturnFlowVol   = self.nonIrrReturnFlow*self.cellArea
        self.channelStorage  += nonIrrReturnFlowVol
        
        # get routing parameters (based on avgDischarge)
        self.yMean, self.wMean, self.characteristicDistance = \
                self.getRoutingParamAvgDischarge(self.avgDischarge,\
                self.dist2celllength)

        # waterBodies: get parameters at the beginning of the year or simulation
        if (currTimeStep.doy == 1) or (currTimeStep.timeStepPCR == 1):\
            self.WaterBodies.getParameterFiles(currTimeStep,\
                                               self.cellArea,\
                                               self.lddMap,\
                                               self.cellLengthFD,\
                                               self.cellSizeInArcDeg)

        # simulating water bodies fraction
        channelFraction = pcr.min(1.0,
                          self.wMean * self.cellLengthFD / (self.cellArea))
        self.dynamicFracWat = \
                          pcr.max(channelFraction, self.WaterBodies.fracWat)
        self.dynamicFracWat = pcr.ifthen(self.landmask, self.dynamicFracWat)                  

        # (additional) evaporation from water bodies
        # current principle: 
        # - if landSurface.actualET < waterKC * meteo.referencePotET * self.fracWat
        #   then, we add more evaporation
        #
        if (currTimeStep.day == 1) or (currTimeStep.timeStepPCR == 1):
            waterKC = vos.netcdf2PCRobjClone(self.fileCropKC,'kc', \
                               currTimeStep.fulldate, useDoy = 'month',\
                                       cloneMapFileName = self.cloneMap)
            self.waterKC = pcr.cover(waterKC, 0.0)                       
        #
        # evaporation from water bodies (m3), limited to available channelStorage
        volLocEvapWaterBody = pcr.min(\
                              pcr.max(0.0,self.channelStorage),
                              pcr.max(0.0,\
                             (self.waterKC * \
                              meteo.referencePotET * self.dynamicFracWat -\
                              landSurface.actualET)* self.cellArea))

        # update channelStorage (m3) after evaporation from water bodies
        self.channelStorage -= volLocEvapWaterBody
        
        # local runoff/change (m) on surface water bodies in meter:
        self.localQW =  volLocEvapWaterBody*-1. / self.cellArea         # Note that precipitation has been calculated/included in the landSurface module. 
        self.localQW =  pcr.ifthen(self.landmask, self.localQW)

        # riverbed infiltration (m3):
        # - current implementation based on Inge's principle (later, will be based on groundater head (MODFLOW) and can be negative)
        # - happening only if 0.0 < baseflow < nonFossilGroundwaterAbs
        # - infiltration rate will be based on aquifer saturated conductivity
        # - limited to fracWat
        # - limited to available channelStorage
        # - this infiltration will be handed to groundwater in the next time step
        riverbedConductivity  = groundwater.kSatAquifer
        self.riverbedExchange = pcr.max(0.0,\
                                pcr.min(self.channelStorage,\
                                pcr.ifthenelse(groundwater.baseflow > 0.0, \
                                pcr.ifthenelse(groundwater.nonFossilGroundwaterAbs > groundwater.baseflow, \
                                riverbedConductivity * self.dynamicFracWat * self.cellArea, \
                                0.0), 0.0)))
        self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)                         
        factor = 0.05 # to avoid flip flop
        self.riverbedExchange = pcr.min(self.riverbedExchange, (1.0-factor)*self.channelStorage)                                                             
        self.riverbedExchange = pcr.cover(self.riverbedExchange, 0.0)
        self.riverbedExchange = pcr.ifthen(self.landmask, self.riverbedExchange)

        # update channelStorage (m3) after riverbedExchange (m3)
        self.channelStorage  -= self.riverbedExchange

        # make sure that channelStorage >= 0
        self.channelStorage   = pcr.max(0.0, self.channelStorage)
        
        if self.debugWaterBalance == 'True':\
           vos.waterBalanceCheck([self.runoff,\
                                  self.nonIrrReturnFlow,\
                                  self.localQW],\
                                 [landSurface.actSurfaceWaterAbstract,self.riverbedExchange/self.cellArea],\
                                 [           preStorage/self.cellArea],\
                                 [  self.channelStorage/self.cellArea],\
                                   'channelStorage before routing',\
                                  True,\
                                  currTimeStep.fulldate,threshold=5e-3)
        
        # updating timesteps to calculate avgDischarge, avgInflow and avgOutflow
        self.timestepsToAvgDischarge += 1.

        if self.method == "accuTravelTime":
            self.accuTravelTime(currTimeStep)                           # output: 		

        # water height (m) = channelStorage / cellArea
        self.waterHeight = self.channelStorage / self.cellArea

        # total water storage 
        self.waterHeight = self.channelStorage / self.cellArea

        # total water storage thickness (m) for the entire column 
        # (including interception, snow, soil and groundwater) 
        self.totalWaterStorageThickness = pcr.ifthen(self.landmask,\
                                          self.waterHeight + \
                                          landSurface.totalSto + \
                                          groundwater.storGroundwater)  # unit: m


        # total water storage thickness (m) for the entire column 
        # (including interception, snow, soil and groundwater) 
        self.totalWaterStorageVolume = self.totalWaterStorageThickness *\
                                       self.cellArea                    # unit: m3
        
        # Calculating avgDischarge
        #
        # average and standard deviation of long term discharge
        #~ self.avgDischarge = (self.avgDischarge  * \
                            #~ (pcr.min(self.maxTimestepsToAvgDischargeLong,
                                     #~ self.timestepsToAvgDischarge)- 1.) + \
                             #~ self.discharge * 1.) / \
                            #~ (pcr.min(self.maxTimestepsToAvgDischargeLong,
                                     #~ self.timestepsToAvgDischarge))             # Edwin's old formula.
        #        
        dishargeUsed      = pcr.max(0.0, self.discharge)
        dishargeUsed      = pcr.max(dishargeUsed, self.disChanWaterBody)
        #
        deltaAnoDischarge = dishargeUsed - self.avgDischarge  
        self.avgDischarge = self.avgDischarge +\
                            deltaAnoDischarge/\
                            pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)
        self.avgDischarge = pcr.max(0.0, self.avgDischarge)                                    
        self.m2tDischarge = self.m2tDischarge + pcr.abs(deltaAnoDischarge*(self.discharge - self.avgDischarge))                             
        self.varDischarge = self.m2tDischarge / \
                            pcr.max(1.,\
                            pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)-1.)                             
                          # see: online algorithm on http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        self.stdDischarge = pcr.max(self.varDischarge**0.5, 0.0)
                                          
        # update available channelStorage that can be extracted:
        # principle: 
        # - during dry period, only limited water may be extracted.
        # - during non dry period, entire channel storage may be extracted.
        minDischargeForEnvironmentalFlow = pcr.max(0., self.avgDischarge - 3.*self.stdDischarge)
        factor = 0.05 # to avoid flip flop
        minDischargeForEnvironmentalFlow = pcr.max(factor*self.avgDischarge, minDischargeForEnvironmentalFlow)
        self.readAvlChannelStorage = pcr.max(factor*self.channelStorage,\
                                     pcr.max(0.00,\
                                     pcr.ifthenelse(self.discharge > minDischargeForEnvironmentalFlow,\
                                     self.channelStorage,\
                                     self.channelStorage*\
                                   vos.getValDivZero(self.discharge, minDischargeForEnvironmentalFlow, vos.smallNumber))))
        self.readAvlChannelStorage = pcr.min(self.readAvlChannelStorage, (1.0-factor)*self.channelStorage)                                                             
        #                                 
        # to avoid small values and to avoid surface water abstractions from dry channels
        tresholdChannelStorage = 0.0005*self.cellArea  # 0.5 mm
        self.readAvlChannelStorage = pcr.ifthenelse(self.readAvlChannelStorage > tresholdChannelStorage, self.readAvlChannelStorage, pcr.scalar(0.0))
        self.readAvlChannelStorage = pcr.cover(self.readAvlChannelStorage, 0.0)
        
        # average baseflow (m3/s)
        # - avgDischarge and avgBaseflow used as proxies for partitioning groundwater and surface water abstractions
        #
        baseflowM3PerSec = groundwater.baseflow * self.cellArea / vos.secondsPerDay()
        deltaAnoBaseflow = baseflowM3PerSec - self.avgBaseflow  
        self.avgBaseflow = self.avgBaseflow +\
                           deltaAnoBaseflow/\
                           pcr.min(self.maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)                
        self.avgBaseflow = pcr.max(0.0, self.avgBaseflow)

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

    def getRoutingParamAvgDischarge(self, avgDischarge, dist2celllength):
        # obtain routing parameters based on average (longterm) discharge
        # output: channel dimensions and 
        #         characteristicDistance (for accuTravelTime input)
        
        yMean = self.eta * pow (avgDischarge, self.nu ) # avgDischarge in m3/s
        wMean = self.tau * pow (avgDischarge, self.phi)
 
        yMean =   pcr.max(yMean,0.000000001) # channel depth (m)
        wMean =   pcr.max(wMean,0.000000001) # channel width (m)
        yMean = pcr.cover(yMean,0.000000001)
        wMean = pcr.cover(wMean,0.000000001)
        
        # characteristicDistance (dimensionless)
        # - This will be used for accutraveltimeflux & accutraveltimestate
        # - discharge & storage = accutraveltimeflux & accutraveltimestate
        # - discharge = the total amount of material flowing through the cell (m3/s)
        # - storage   = the amount of material which is deposited in the cell (m3)
        #
        characteristicDistance = \
             ( (yMean *   wMean)/ \
               (wMean + 2*yMean) )**(2./3.) * \
              ((self.gradient)**(0.5))/ \
                self.manningsN * \
                vos.secondsPerDay()                       #  meter/day

        characteristicDistance = \
         pcr.max((self.cellSizeInArcDeg)*0.000000001,\
                 characteristicDistance/dist2celllength)  # arcDeg/day
        
        # PS: In accutraveltime function: 
        #     If characteristicDistance (velocity) = 0 then:
        #     - accutraveltimestate will give zero 
        #     - accutraveltimeflux will be very high 
        
        # TODO: Consider to use downstreamdist function.
        
        return (yMean, wMean, characteristicDistance)

    def accuTravelTime(self,currTimeStep):
        		
        usedLDD = self.lddMap

        # at cells where lakes and/or reservoirs defined, move channelStorage to waterBodyStorage
        storageAtLakeAndReservoirs = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
                               self.channelStorage)
        storageAtLakeAndReservoirs = pcr.cover(storageAtLakeAndReservoirs,0.0)
        self.channelStorage -= storageAtLakeAndReservoirs                    # unit: m3

        # update waterBodyStorage (inflow, storage and outflow)
        self.WaterBodies.update(storageAtLakeAndReservoirs,\
                                self.timestepsToAvgDischarge,\
                                self.maxTimestepsToAvgDischargeShort,\
                                self.maxTimestepsToAvgDischargeLong,\
                                currTimeStep)

        # transfer outflow from lakes and/or reservoirs to channelStorages
        waterBodyOutflow = pcr.cover(\
                           pcr.ifthen(\
                           self.WaterBodies.waterBodyOut,
                           self.WaterBodies.waterBodyOutflow), 0.0)          # unit: m3/day
        #
        # distribute outflow to water body storage
        waterBodyOutflow = pcr.areaaverage(waterBodyOutflow, self.WaterBodies.waterBodyIds)
        waterBodyOutflow = pcr.ifthen(\
                           pcr.scalar(self.WaterBodies.waterBodyIds) > 0.0,
                           waterBodyOutflow)                                 # unit: m3/day
        waterBodyOutflow = pcr.cover(waterBodyOutflow, 0.0)
        #
        self.channelStorage += waterBodyOutflow                              # TODO: Move waterBodyOutflow according to water body discharge (velocity)
        
        # obtain water body storages (for reporting)
        self.waterBodyStorage = pcr.ifthen(self.landmask,\
                                pcr.ifthen(\
         pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                    self.WaterBodies.waterBodyStorage))     # m3
        # as well as outflows from water bodies (for reporting)
        self.waterBodyOutDisc = pcr.ifthen(self.landmask,\
                                pcr.ifthen(\
         pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                    self.WaterBodies.waterBodyOutflow)) /\
                     vos.secondsPerDay()                    # m3/s


        # channelStorage ROUTING:
        channelStorageForAccuTravelTime = self.channelStorage 
        channelStorageForAccuTravelTime = pcr.cover(channelStorageForAccuTravelTime,0.0) # TODO: check why do we have to use the "cover" operation. 
        #
        characteristicDistanceForAccuTravelTime = pcr.cover(self.characteristicDistance, 0.001*self.cellSizeInArcDeg)
        characteristicDistanceForAccuTravelTime = pcr.max(0.001*self.cellSizeInArcDeg, self.characteristicDistance)

        # self.Q = channel discharge (m3/day)
        self.Q = pcr.accutraveltimeflux(usedLDD,\
                                        channelStorageForAccuTravelTime,\
                                        characteristicDistanceForAccuTravelTime)
        self.Q = pcr.cover(self.Q, 0.0)
        # for very small velocity (i.e. characteristicDistanceForAccuTravelTime), discharge can be missing value.
        # see: http://sourceforge.net/p/pcraster/bugs-and-feature-requests/543/
        #      http://karssenberg.geo.uu.nl/tt/TravelTimeSpecification.htm        

        # updating channelStorage (after routing)
        self.channelStorage = pcr.accutraveltimestate(usedLDD,\
                              channelStorageForAccuTravelTime,\
                              characteristicDistanceForAccuTravelTime)

        # after routing, return waterBodyStorage to channelStorage  
        waterBodyStorageTotal = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         pcr.areaaverage(\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyStorage),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)) + \
         pcr.areatotal(pcr.cover(\
         pcr.ifthen(self.landmask,self.channelStorage), 0.0),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds)))
        waterBodyStoragePerCell = \
         waterBodyStorageTotal*\
                       self.cellArea/\
         pcr.areatotal(pcr.cover(\
         self.cellArea, 0.0),\
         pcr.ifthen(self.landmask,self.WaterBodies.waterBodyIds))
        waterBodyStoragePerCell = \
         pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,
         waterBodyStoragePerCell)                         # unit: m3
        #
        self.channelStorage = pcr.cover(waterBodyStoragePerCell, self.channelStorage)  # unit: m3
        self.channelStorage = pcr.ifthen(self.landmask, self.channelStorage)

        # channel discharge (m3/s): current:
        self.discharge = self.Q / vos.secondsPerDay()
        self.discharge = pcr.max(0., self.discharge)                   # reported channel discharge cannot be negative
        self.discharge = pcr.ifthen(self.landmask, self.discharge)
        
        # discharge at channel and lake/reservoir outlets (m3/s)  
        #~ self.disChanWaterBody = pcr.ifthen(self.landmask,\
                                #~ pcr.cover( self.waterBodyOutDisc,\
                                           #~ self.discharge))                  # TODO: FIX THIS, discharge at water bodies is too high. (self.waterBodyOutDisc) 
        #
        self.disChanWaterBody = pcr.ifthen(pcr.scalar(self.WaterBodies.waterBodyIds) > 0.,\
                                pcr.areamaximum(self.discharge,self.WaterBodies.waterBodyIds))
        self.disChanWaterBody = pcr.cover(self.disChanWaterBody, self.discharge)
        self.disChanWaterBody = pcr.ifthen(self.landmask, self.disChanWaterBody)
        #
        self.disChanWaterBody = pcr.max(0.,self.disChanWaterBody)               # reported channel discharge cannot be negative

