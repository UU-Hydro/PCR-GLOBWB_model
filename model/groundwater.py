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
        result['storGroundwater'] = self.storGroundwater
        
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

        self.debugWaterBalance = iniItems.groundwaterOptions['debugWaterBalance']

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

        self.recessionCoeff = pcr.cover(self.recessionCoeff,0.00)       
        self.recessionCoeff = pcr.max(2.5e-3,self.recessionCoeff)       
        self.recessionCoeff = pcr.min(1.0000,self.recessionCoeff)       

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

        #get initial conditions
        self.getICs(iniItems,spinUp)
    
    def getICs(self,iniItems,iniConditions = None):

        if iniConditions == None:
            self.storGroundwater = vos.readPCRmapClone(\
                      iniItems.groundwaterOptions['storGroundwaterIni'],
                      self.cloneMap,self.tmpDir,self.inputDir)
        else:
            self.storGroundwater = iniConditions['groundwater'][ 'storGroundwater']

        self.storGroundwater = pcr.cover(self.storGroundwater,0.0)
        self.storGroundwater = pcr.max(0.,self.storGroundwater)                                    
        self.storGroundwater = pcr.ifthen(self.landmask,\
                                         self.storGroundwater)

    def perturb(self, name, **parameters):
        
        if name == "groundwater":
        
            # factor for perturbing the initial storGroundwater
            self.storGroundwater = self.storGroundwater * (mapnormal()*parameters['standard_deviation']+1)
            self.storGroundwater = pcr.max(0.,self.storGroundwater)

        else:
            print("Error: only groundwater may be updated at this time")
            return -1

    def update(self,landSurface,routing,currTimeStep):

        if self.debugWaterBalance == str('True'):
            prestorGroundwater = self.storGroundwater
                
        # get riverbed infiltration from the previous time step (from routing)
        self.surfaceWaterInf  = routing.riverbedExchange/routing.cellArea     # m
        self.storGroundwater += self.surfaceWaterInf

        # get net recharge (percolation-capRise) and update storage:
        self.storGroundwater  = pcr.max(0.,\
                                self.storGroundwater + landSurface.gwRecharge)         
                        
        # potential groundwater abstraction (unit: m)
        potGroundwaterAbstract = landSurface.potGroundwaterAbstract

        if self.usingAllocSegments == False or self.limitAbstraction:
        
            logger.info("WARNING! Groundwater abstraction is only to satisfy local demand. No network for distributing groundwater.")

            # nonFossil groundwater abstraction (unit: m) to fulfill water demand 
            # - assumption: Groundwater is only abstracted to satisfy local demand.
            self.nonFossilGroundwaterAbs = \
                                           pcr.max(0.0,
                                           pcr.min(self.storGroundwater,\
                                           landSurface.potGroundwaterAbstract)) 
            #
            self.allocNonFossilGroundwater = self.nonFossilGroundwaterAbs
        
        else: # ( usingAllocSegments == True and limitAbstraction == True )

            # TODO: Assuming that there is also network for distributing groundwater abstractions.
            # Notes: Incorporating distribution network of groundwater source is possible only if limitAbstraction = False.  

            logger.info("Using groundwater source allocation.")

            # gross/potential demand volume in each cell (unit: m3)
            cellVolGrossDemand = potGroundwaterAbstract*routing.cellArea
            
            # total gross demand volume in each segment/zone (unit: m3)
            segTtlGrossDemand  = pcr.areatotal(cellVolGrossDemand, self.allocSegments)
            
            # total available groundwater water volume in each cell - ignore small values (less than 1 m3)
            cellAvlGroundwater = pcr.max(0.00, self.storGroundwater* routing.cellArea)
            cellAvlGroundwater = pcr.rounddown( cellAvlGroundwater/1.)*1.
            
            # total available surface water volume in each segment/zone  (unit: m3)
            segAvlGroundwater  = pcr.areatotal(cellAvlGroundwater, self.allocSegments)
            segAvlGroundwater  = pcr.max(0.00,  segAvlGroundwater)
            
            # total actual surface water abstraction volume in each segment/zone (unit: m3)
            #
            # - not limited to available water - ignore small values (less than 1 m3)
            segActGroundwaterAbs = pcr.max(0.0,\
                                   pcr.rounddown(segTtlGrossDemand))
            # 
            # - limited to available water
            segActGroundwaterAbs = pcr.min(segAvlGroundwater, segActGroundwaterAbs)
            
            # actual surface water abstraction volume in each cell (unit: m3)
            volActGroundwaterAbstract = vos.getValDivZero(\
                                        cellAvlGroundwater, segAvlGroundwater, vos.smallNumber) * \
                                        segActGroundwaterAbs                                                 
            volActGroundwaterAbstract = pcr.min(cellAvlGroundwater , volActGroundwaterAbstract)              # unit: m3
            
            # actual non fossil groundwater abstraction volume in meter (unit: m)
            self.nonFossilGroundwaterAbs = pcr.ifthen(self.landmask, volActGroundwaterAbstract) /\
                                                                     routing.cellArea                        # unit: m
            
            # allocation non fossil groundwater abstraction volume to each cell (unit: m3)
            self.volAllocGroundwaterAbstract = vos.getValDivZero(\
                                               cellVolGrossDemand, segTtlGrossDemand, vos.smallNumber) *\
                                               segActGroundwaterAbs                                          # unit: m3 
            
            # allocation surface water abstraction in meter (unit: m)
            self.allocNonFossilGroundwater   = pcr.ifthen(self.landmask, self.volAllocGroundwaterAbstract)/\
                                                                         routing.cellArea                    # unit: m

            if self.debugWaterBalance == str('True'):
    
                abstraction = pcr.cover(pcr.areatotal(self.nonFossilGroundwaterAbs  *routing.cellArea, self.allocSegments)/self.segmentArea, 0.0)
                allocation  = pcr.cover(pcr.areatotal(self.allocNonFossilGroundwater*routing.cellArea, self.allocSegments)/self.segmentArea, 0.0)
            
                vos.waterBalanceCheck([abstraction],\
                                      [allocation],\
                                      [pcr.scalar(0.0)],\
                                      [pcr.scalar(0.0)],\
                                      'non fossil groundwater abstraction - allocation per zone/segment (PS: Error here may be caused by rounding error.)' ,\
                                       True,\
                                       "",threshold=5e-4)

        # unmetDemand (m), satisfied by fossil gwAbstractions (and/or desalinization or other sources)
        self.unmetDemand = pcr.max(0.0,
                           potGroundwaterAbstract - \
                           self.allocNonFossilGroundwater)              # m  (equal to zero if limitAbstraction = True)
        
        # TODO: Before going to unmetDemand, extract (remaining) surface water first.  
        # - Needs further consideration !!                   

        if self.limitAbstraction:
            logger.info("No fossil groundwater abstraction is allowed")
            # TODO: check that self.unmetDemand = 0.0

        # fractions of water demand sources (to satisfy water demand):
        self.fracNonFossilGroundwater = pcr.ifthen(self.landmask,pcr.ifthenelse(landSurface.totalPotentialGrossDemand > 0.,\
                      self.allocNonFossilGroundwater/landSurface.totalPotentialGrossDemand, 0.0))
        self.fracUnmetDemand          = pcr.ifthen(self.landmask,pcr.ifthenelse(landSurface.totalPotentialGrossDemand > 0.,\
                      self.unmetDemand/landSurface.totalPotentialGrossDemand, 0.0))
        self.fracSurfaceWater         = pcr.ifthen(self.landmask,pcr.ifthenelse(landSurface.totalPotentialGrossDemand > 0.,\
                 pcr.max(0.0,1.0 - self.fracNonFossilGroundwater - self.fracUnmetDemand), 0.0)) 
        
        # update storGoundwater after self.nonFossilGroundwaterAbs
        self.storGroundwater  = pcr.max(0.,self.storGroundwater - self.nonFossilGroundwaterAbs)
        
        # reporting storGroundwater volume after non-fossil groundwater abstraction (unit: m3)
        self.storGroundwaterVolumeAfterAbstraction = pcr.ifthen(self.landmask, self.storGroundwater * routing.cellArea) 
        
        # calculate baseflow and update storage:
        self.baseflow         = pcr.max(0.,\
                                pcr.min(self.storGroundwater,\
                                        self.recessionCoeff* \
                                        self.storGroundwater))
        self.storGroundwater  = pcr.max(0.,\
                                self.storGroundwater - self.baseflow)
        # PS: baseflow must be calculated at the end (to ensure the availability of storGroundwater to support nonFossilGroundwaterAbs)

        if self.debugWaterBalance == 'True':
            vos.waterBalanceCheck([self.surfaceWaterInf,\
                                   landSurface.gwRecharge],\
                                  [self.baseflow,\
                                   self.nonFossilGroundwaterAbs],\
                                  [  prestorGroundwater],\
                                  [self.storGroundwater],\
                                       'storGroundwater',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)

        if self.debugWaterBalance == 'True' and landSurface.limitAbstraction:
            vos.waterBalanceCheck([potGroundwaterAbstract],\
                                  [self.nonFossilGroundwaterAbs],\
                                  [pcr.scalar(0.)],\
                                  [pcr.scalar(0.)],\
                                  'non fossil groundwater abstraction',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)

        if self.debugWaterBalance == 'True':
            vos.waterBalanceCheck([self.unmetDemand, self.allocNonFossilGroundwater, landSurface.allocSurfaceWaterAbstract],\
                                  [landSurface.totalPotentialGrossDemand],\
                                  [pcr.scalar(0.)],\
                                  [pcr.scalar(0.)],\
                                  'water demand allocation (from surface water, groundwater and unmetDemand)',\
                                   True,\
                                   currTimeStep.fulldate,threshold=1e-4)


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

