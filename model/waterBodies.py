#!/usr/bin/ python
# -*- coding: utf-8 -*-

from pcraster.framework import *
import pcraster as pcr

import virtualOS as vos

class WaterBodies(object):

    def __init__(self,iniItems):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir   = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
                
        self.debugWaterBalance = \
                            iniItems.routingOptions['debugWaterBalance']

        #TODO: 26 Feb 2014, Edwin found that reasonable runs are only found 
        # if all of these options = True.                    
        self.includeWaterBodies = "True"
        self.includeLakes = "True"
        self.includeReservoirs =  "True"

        if iniItems.routingOptions['waterBodyInputNC'] == str(None):
            self.useNetCDF = False
        
            self.fracWaterInp = iniItems.routingOptions['fracWaterInp']
            self.waterBodyIdsInp = \
                                iniItems.routingOptions['waterBodyIds']
            self.waterBodyTypInp = \
                                iniItems.routingOptions['waterBodyTyp']
            self.resMaxCapInp = iniItems.routingOptions['resMaxCapInp']
            self.resSfAreaInp = iniItems.routingOptions['resSfAreaInp']
        
        else:
            self.useNetCDF = True
            self.ncFileInp = vos.getFullPath(\
                        iniItems.routingOptions['waterBodyInputNC'],\
                            self.inputDir)

        self.minResvrFrac = float(\
                            iniItems.routingOptions['minResvrFrac'])
        self.maxResvrFrac = float(\
                            iniItems.routingOptions['maxResvrFrac'])
        self.minWeirWidth = float(\
                            iniItems.routingOptions['minWeirWidth'])                    

    def getICs(self,iniItems,iniConditions = None):

        # lake and reservoir storages = waterBodyStorage (m3)
        # - values are given for the entire lake / reservoir cells
        if iniConditions == None:
            self.waterBodyStorage = vos.readPCRmapClone(\
                          iniItems.routingOptions['waterBodyStorageIni'],
                              self.cloneMap,self.tmpDir,self.inputDir)

            # only for testing - NOT A GOOD IDEA (especially during SpinUp)
            #~ self.waterBodyStorage = 1000. * 1000. * vos.readPCRmapClone(\
                          #~ self.resMaxCapInp +"2000"+".map",
                          #~ self.cloneMap,self.tmpDir,self.inputDir)     # m3

        else:
            self.waterBodyStorage = iniConditions['routing']['waterBodyStorage']
        
        self.waterBodyStorage = pcr.cover(self.waterBodyStorage, 0.0)    

        # initial long and short term average outflow and inflow (m3/s)
        if iniConditions == None:
            self.avgInflow  = vos.readPCRmapClone(\
                      iniItems.routingOptions['avgInflowLakeReservIni'],
                       self.cloneMap,self.tmpDir,self.inputDir)
            self.avgOutflow = vos.readPCRmapClone(\
                      iniItems.routingOptions['avgOutflowDischargeIni'],
                       self.cloneMap,self.tmpDir,self.inputDir)
        else:
            self.avgInflow  = iniConditions['routing']['avgInflow' ]
            self.avgOutflow = iniConditions['routing']['avgOutflow']
            
        self.avgInflow  = pcr.cover(self.avgInflow , 0.0)               # unit: m3/s 
        self.avgOutflow = pcr.cover(self.avgOutflow, 0.0)               # unit: m3/s

    def getParameterFiles(self,currTimeStep,cellArea,ldd,\
                               cellLengthFD,cellSizeInArcDeg):

        # parameters for Water Bodies: fracWat 
        #                              waterBodyIds
        #                              waterBodyOut
        #                              waterBodyArea 
        #                              waterBodyTyp
        #                              waterBodyCap
        
        self.cellArea = cellArea
        
        #    fracWat = fraction of surface water bodies
        self.fracWat = pcr.scalar(0.0)
        
        if self.includeWaterBodies == "True":
            if self.useNetCDF:
                self.fracWat = vos.netcdf2PCRobjClone(self.ncFileInp,'fracWaterInp', \
                               currTimeStep.fulldate, useDoy = 'yearly',\
                               cloneMapFileName = self.cloneMap)
            else:
                self.fracWat = vos.readPCRmapClone(\
                            self.fracWaterInp+str(currTimeStep.year)+".map",
                            self.cloneMap,self.tmpDir,self.inputDir)
            
            
        self.fracWat = pcr.cover(self.fracWat, 0.0)
        self.fracWat = pcr.max(0.0,self.fracWat)
        self.fracWat = pcr.min(1.0,self.fracWat)

        self.waterBodyIds  = pcr.nominal(0)    # waterBody ids
        self.waterBodyOut  = pcr.boolean(0)    # waterBody outlets
        self.waterBodyArea = pcr.scalar(0.)    # waterBody surface areas

        if self.includeLakes == "True" or \
           self.includeReservoirs == "True":

            # water body ids
            if self.useNetCDF:
                self.waterBodyIds = vos.netcdf2PCRobjClone(self.ncFileInp,'waterBodyIds', \
                                    currTimeStep.fulldate, useDoy = 'yearly',\
                                    cloneMapFileName = self.cloneMap)
            else:
                self.waterBodyIds = vos.readPCRmapClone(\
                    self.waterBodyIdsInp+str(currTimeStep.year)+".map",\
                    self.cloneMap,self.tmpDir,self.inputDir,False,None,True)
            self.waterBodyIds = pcr.ifthen(\
                                pcr.scalar(self.waterBodyIds) > 0.,\
                                pcr.nominal(self.waterBodyIds))    

            # water body outlets:
            wbCatchment = pcr.catchmenttotal(pcr.scalar(1),ldd)
            self.waterBodyOut = pcr.ifthen(wbCatchment ==\
                                pcr.areamaximum(wbCatchment, \
                                self.waterBodyIds),\
                                self.waterBodyIds)     # = outlet ids   
            self.waterBodyOut = pcr.ifthen(\
                                pcr.scalar(self.waterBodyIds) > 0.,\
                                self.waterBodyOut)

            # correcting water body ids
            self.waterBodyIds = pcr.ifthen(\
                                pcr.scalar(self.waterBodyIds) > 0.,\
                                pcr.subcatchment(ldd,self.waterBodyOut))
            
            # boolean map for water body outlets:   
            self.waterBodyOut = pcr.ifthen(\
                                pcr.scalar(self.waterBodyOut) > 0.,\
                                pcr.boolean(1))

            # reservoir surface area (m2):
            if self.useNetCDF:
                resSfArea = 1000. * 1000. * \
                            vos.netcdf2PCRobjClone(self.ncFileInp,'resSfAreaInp', \
                            currTimeStep.fulldate, useDoy = 'yearly',\
                            cloneMapFileName = self.cloneMap)
            else:
                resSfArea = 1000. * 1000. * vos.readPCRmapClone(
                       self.resSfAreaInp+str(currTimeStep.year)+".map",\
                       self.cloneMap,self.tmpDir,self.inputDir)
            resSfArea = pcr.areaaverage(resSfArea,self.waterBodyIds)                        
            resSfArea = pcr.cover(resSfArea,0.)                        

            # water body surface area (m2): (lakes and reservoirs)
            self.waterBodyArea = pcr.max(pcr.areatotal(\
                                 pcr.cover(\
                                 self.fracWat*self.cellArea, 0.0), self.waterBodyIds),
                                 pcr.areaaverage(\
                                 pcr.cover(resSfArea, 0.0) ,       self.waterBodyIds))
            self.waterBodyArea = pcr.ifthen(self.waterBodyArea > 0.,\
                                 self.waterBodyArea)
                                    
            # correcting water body ids and outlets (excluding all water bodies with surfaceArea = 0)
            self.waterBodyIds = pcr.ifthen(self.waterBodyArea > 0.,
                                self.waterBodyIds)               
            self.waterBodyOut = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                       self.waterBodyOut)

        # water body types:
        # - 2 = reservoirs (regulated discharge)
        # - 1 = lakes (weirFormula)
        # - 0 = non lakes or reservoirs (e.g. wetland)
        self.waterBodyTyp = pcr.nominal(0)
        
        if self.includeLakes == "True" or \
           self.includeReservoirs == "True":

            if self.useNetCDF:
                self.waterBodyTyp = vos.netcdf2PCRobjClone(self.ncFileInp,'waterBodyTyp', \
                                    currTimeStep.fulldate, useDoy = 'yearly',\
                                    cloneMapFileName = self.cloneMap)
            else:
                self.waterBodyTyp = vos.readPCRmapClone(
                    self.waterBodyTypInp+str(currTimeStep.year)+".map",\
                    self.cloneMap,self.tmpDir,self.inputDir,False,None,True)

            self.waterBodyTyp = pcr.ifthen(\
                                pcr.scalar(self.waterBodyTyp) > 0,\
                                pcr.nominal(self.waterBodyTyp))    
            self.waterBodyTyp = pcr.ifthen(\
                                pcr.scalar(self.waterBodyIds) > 0,\
                                pcr.nominal(self.waterBodyTyp))    
            self.waterBodyTyp = pcr.areamajority(self.waterBodyTyp,\
                                                 self.waterBodyIds)                        
            self.waterBodyTyp = pcr.ifthen(\
                                pcr.scalar(self.waterBodyTyp) > 0,\
                                pcr.nominal(self.waterBodyTyp))    
            self.waterBodyTyp = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                       self.waterBodyTyp)

            # correcting water body ids and outlets:
            self.waterBodyIds = pcr.ifthen(pcr.boolean(self.waterBodyTyp),
                                                       self.waterBodyIds)               
            self.waterBodyOut = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                       self.waterBodyOut)

        # correcting water bodies attributes if reservoirs are ignored (for natural runs):
        if self.includeLakes == "True" and\
           self.includeReservoirs == "False":

            # correcting fracWat
            reservoirExcluded = pcr.cover(\
                                pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 2.,\
                                pcr.boolean(1)),pcr.boolean(0))
            maxWaterBodyAreaExcluded = pcr.ifthen(reservoirExcluded,\
                                       self.waterBodyArea/\
                                       pcr.areatotal(\
                                       pcr.scalar(reservoirExcluded),\
                                       self.waterBodyIds))
            maxfractionWaterExcluded = pcr.cover(\
                                       maxWaterBodyAreaExcluded / self.cellArea, 0.0)
            maxfractionWaterExcluded = pcr.min(1.0,maxfractionWaterExcluded)
            maxfractionWaterExcluded = pcr.min(self.fracWat, maxfractionWaterExcluded)

            self.fracWat = self.fracWat - maxfractionWaterExcluded
            self.fracWat = pcr.max(0.,self.fracWat)
            self.fracWat = pcr.min(1.,self.fracWat)

            self.waterBodyArea = pcr.ifthen(pcr.scalar(self.waterBodyTyp) < 2.,\
                                                       self.waterBodyArea) 
            self.waterBodyTyp  = pcr.ifthen(pcr.scalar(self.waterBodyTyp) < 2.,\
                                                       self.waterBodyTyp)
            self.waterBodyIds  = pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                                       self.waterBodyIds)               
            self.waterBodyOut  = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.,\
                                                       self.waterBodyOut)

        # reservoir maximum capacity (m3):
        self.resMaxCap = pcr.scalar(0.0)
        self.waterBodyCap = pcr.scalar(0.0)
        
        if self.includeReservoirs == "True":

            # reservoir maximum capacity (m3):
            if self.useNetCDF:
                self.resMaxCap = 1000. * 1000. * \
                                 vos.netcdf2PCRobjClone(self.ncFileInp,'resMaxCapInp', \
                                 currTimeStep.fulldate, useDoy = 'yearly',\
                                 cloneMapFileName = self.cloneMap)
            else:
                self.resMaxCap = 1000. * 1000. * vos.readPCRmapClone(\
                    self.resMaxCapInp+str(currTimeStep.year)+".map", \
                    self.cloneMap,self.tmpDir,self.inputDir)

            self.resMaxCap = pcr.ifthen(self.resMaxCap > 0,\
                                        self.resMaxCap)
            self.resMaxCap = pcr.areaaverage(self.resMaxCap,\
                                             self.waterBodyIds)
                                             
            # water body capacity (m3): (lakes and reservoirs)
            self.waterBodyCap = pcr.cover(self.resMaxCap,0.0)           # Note: Most of lakes have capacities > 0.
            self.waterBodyCap = pcr.ifthen(pcr.boolean(self.waterBodyIds),
                                                       self.waterBodyCap)
                                                   
            # correcting water body types:
            self.waterBodyTyp = pcr.ifthenelse(self.waterBodyCap > 0.,\
                                               self.waterBodyTyp,\
                     pcr.ifthenelse(pcr.scalar(self.waterBodyTyp) == 2,\
                                               pcr.nominal(1),\
                                               self.waterBodyTyp)) 
            self.waterBodyTyp = \
                     pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                           self.waterBodyTyp) 

            # final corrections:
            self.waterBodyTyp = pcr.ifthen(self.waterBodyArea > 0.,\
                                           self.waterBodyTyp)
            self.waterBodyIds = pcr.ifthen(pcr.scalar(self.waterBodyTyp) > 0.,\
                                self.waterBodyIds)               
            self.waterBodyOut = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.,\
                                                      self.waterBodyOut)

        # For each new reservoir (introduced at the beginning of the year)
        # initiating storage, average inflow and outflow:  
        self.waterBodyStorage = pcr.cover(self.waterBodyStorage,0.0)
        self.avgInflow        = pcr.cover(self.avgInflow ,0.0)
        self.avgOutflow       = pcr.cover(self.avgOutflow,0.0)

    def update(self,newStorageAtLakeAndReservoirs,\
                              timestepsToAvgDischarge,\
                           maxTimestepsToAvgDischargeShort,
                           maxTimestepsToAvgDischargeLong,\
                           currTimeStep,
                           downstreamDemand = None,\
                           avgChannelDischarge = None):

        self.inflow = pcr.scalar(0.0)
        self.waterBodyOutflow = pcr.scalar(0.0)                         # unit: m3/s
        
        if self.includeLakes == "True" or \
           self.includeReservoirs == "True":


            if self.debugWaterBalance == str('True'):\
               preStorage = self.waterBodyStorage    # unit: m

     
            self.timestepsToAvgDischarge = timestepsToAvgDischarge     # TODO: include this one in "currTimeStep"     
        
            # obtain inflow (and update storage)
            self.moveFromChannelToWaterBody(\
             newStorageAtLakeAndReservoirs,\
                 timestepsToAvgDischarge,\
                 maxTimestepsToAvgDischargeShort)
         
            # calculate outflow (and update storage)
            self.getWaterBodyOutflow(\
                 maxTimestepsToAvgDischargeLong,\
                 downstreamDemand,\
             avgChannelDischarge)
         
            if self.debugWaterBalance == 'True':\
               vos.waterBalanceCheck([          self.inflow/self.waterBodyArea],\
                                     [self.waterBodyOutflow/self.waterBodyArea],\
                                     [           preStorage/self.waterBodyArea],\
                                     [self.waterBodyStorage/self.waterBodyArea],\
                                       'WaterBodyStorage',\
                                      True,\
                                      currTimeStep.fulldate,threshold=1e-3)

    def moveFromChannelToWaterBody(self,\
                                   newStorageAtLakeAndReservoirs,\
                                   timestepsToAvgDischarge,\
                                   maxTimestepsToAvgDischargeShort):
        
        # new lake and/or reservoir storages (m3)
        newStorageAtLakeAndReservoirs = pcr.cover(\
         pcr.areatotal(pcr.cover(newStorageAtLakeAndReservoirs, 0.0),\
                       self.waterBodyIds),0.0)

        # inflow (m3/day)
        self.inflow = newStorageAtLakeAndReservoirs - self.waterBodyStorage
        
        # inflowInM3PerSec (m3/s)
        inflowInM3PerSec = self.inflow / (vos.secondsPerDay())

        # updating average (short term) inflow (m3/s) 
        # - needed to constrain lake outflow:
        #
        #~ self.avgInflow = pcr.max(0.,
                         #~ (self.avgInflow * \
                         #~ (pcr.min(maxTimestepsToAvgDischargeShort,
                                     #~ timestepsToAvgDischarge)- 1.) + \
                         #~ (inflowInM3PerSec /\
                          #~ vos.secondsPerDay()) * 1.) / \
                         #~ (pcr.min(maxTimestepsToAvgDischargeShort,
                                     #~ timestepsToAvgDischarge)))         # Edwin's old formula
        #
        deltaInflow = inflowInM3PerSec - self.avgInflow  
        self.avgInflow = self.avgInflow +\
                            deltaInflow/\
                            pcr.min(maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)                
        self.avgInflow = pcr.max(0.0, self.avgInflow)                         

        # updating waterBodyStorage (m3)
        self.waterBodyStorage = newStorageAtLakeAndReservoirs

    def getWaterBodyOutflow(self,\
                            maxTimestepsToAvgDischargeLong,\
                            downstreamDemand = None,\
                            avgChannelDischarge = None):

        # outflow from water bodies with lake type (m3/day): 
        if self.includeLakes == "True": 
            lakeOutflow = self.getLakeOutflow(avgChannelDischarge)  
            self.waterBodyOutflow = pcr.cover(\
             pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 1, lakeOutflow),0.0)
             
        # outflow from water bodies with reservoir type (m3/day): 
        if self.includeReservoirs == "True":
            reservoirOutflow = \
                          self.getReservoirOutflow(avgChannelDischarge)  
            self.waterBodyOutflow = pcr.cover(\
             pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 2, reservoirOutflow), lakeOutflow)

        # make sure that all water bodies have outflow:
        self.waterBodyOutflow = pcr.max(0.,
                                pcr.cover(self.waterBodyOutflow,\
                                          lakeOutflow))

        # limit outflow to available storage
        factor = 0.33  # to avoid flip flop 
        self.waterBodyOutflow = pcr.min(self.waterBodyStorage * factor,\
                                        self.waterBodyOutflow)                    # unit: m3/day

        waterBodyOutflowInM3PerSec = self.waterBodyOutflow / vos.secondsPerDay()  # unit: m3/s

        # update average discharge (outflow) m3/s
        #~ self.avgOutflow = (self.avgOutflow * \
                          #~ (pcr.min(maxTimestepsToAvgDischargeLong,
                                 #~ self.timestepsToAvgDischarge)- 1.) + \
                          #~ (waterBodyOutflowInM3PerSec /\
                           #~ vos.secondsPerDay()) * 1.) / \
                          #~ (pcr.min(maxTimestepsToAvgDischargeLong,
                                 #~ self.timestepsToAvgDischarge))         # Edwin's old formula
        #
        deltaOutflow    = waterBodyOutflowInM3PerSec - self.avgOutflow
        self.avgOutflow = self.avgOutflow +\
                             deltaOutflow/\
                            pcr.min(maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)                
        self.avgOutflow = pcr.max(0.0, self.avgOutflow)                         

        # update waterBodyStorage (after outflow):
        self.waterBodyStorage = self.waterBodyStorage -\
                                self.waterBodyOutflow

    def weirFormula(self,waterHeight,weirWidth): # output: m3/s
        sillElev  = pcr.scalar(0.0) 
        weirCoef  = pcr.scalar(1.0)
        weirFormula = \
         (1.7*weirCoef*pcr.max(0,waterHeight-sillElev)**1.5) *\
             weirWidth # m3/s
        return (weirFormula)

    def getLakeOutflow(self,avgChannelDischarge=None):

        # waterHeight (m): temporary variable, a function of storage:
        minWaterHeight = 0.000 # (m) Rens used 0.001 m
        waterHeight = pcr.cover(
                      pcr.max(minWaterHeight, \
                      (self.waterBodyStorage - \
                      pcr.cover(self.waterBodyCap, 0.0))/\
                      self.waterBodyArea),0.)

        # weirWidth (m) : estimated from avgOutflow (m3/s)
        avgOutflow = self.avgOutflow
        if avgChannelDischarge != None:
            avgOutflow = pcr.ifthenelse(avgOutflow > 0.,\
                         avgOutflow,avgChannelDischarge)
            avgOutflow = pcr.areamaximum(avgOutflow,self.waterBodyIds)             	
        bankfullWidth = pcr.cover(\
                        pcr.scalar(4.8) * \
                        ((avgOutflow)**(0.5)),0.)
        weirWidthUsed = bankfullWidth
        weirWidthUsed = pcr.max(weirWidthUsed,self.minWeirWidth)
        weirWidthUsed = pcr.cover(
                        pcr.ifthen(\
                        pcr.scalar(self.waterBodyIds) > 0.,\
                        weirWidthUsed),0.0)
        # TODO: minWeirWidth based on the GRanD database
        weirWidthUsed = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0.,\
                        weirWidthUsed)

        # lakeOutflow = weirFormula >= avgInflow <= waterBodyStorage
        lakeOutflow = pcr.max(\
                      self.weirFormula(waterHeight,weirWidthUsed),\
                      self.avgInflow) * \
                      vos.secondsPerDay() # m3/day
        lakeOutflow = pcr.min(self.waterBodyStorage, lakeOutflow)

        return (lakeOutflow)              # m3/day

    def getReservoirOutflow(self,\
        avgChannelDischarge=None,downstreamDemand=None):

        minWaterHeight = 0.000 # (m) Rens used 0.001 m
        reservoirWaterHeight = pcr.cover(\
                               pcr.max(minWaterHeight, \
                                      (self.waterBodyStorage)/\
                                       self.waterBodyArea),0.0)
                                       
        # avgOutflow (m3/s)
        avgOutflow = self.avgOutflow
        if avgChannelDischarge != None:
            avgOutflow = pcr.ifthenelse(avgOutflow > 0.,\
                         avgOutflow,avgChannelDischarge)
            avgOutflow = pcr.areamaximum(avgOutflow,self.waterBodyIds)
            avgOutflow = pcr.cover(avgOutflow, 0.0)

        # calculate resvOutflow (based on reservoir storage and avgDischarge): 
        # - unit: m3/day (Note that avgDischarge is given in m3/s) 
        # - using reductionFactor in such a way that:
        #   - if relativeCapacity < minResvrFrac : release is terminated
        #   - if relativeCapacity > maxResvrFrac : longterm Average
        reductionFactor = \
         pcr.cover(\
         pcr.min(1.,
         pcr.max(0., \
          self.waterBodyStorage - self.minResvrFrac*self.waterBodyCap)/\
             (self.maxResvrFrac - self.minResvrFrac)*self.waterBodyCap),0.)
        #
        resvOutflow = reductionFactor * avgOutflow * vos.secondsPerDay()                       # m3/day

        # maximum release <= average inflow (especially during dry condition)
        resvOutflow  = pcr.max(0, pcr.min(resvOutflow, self.avgInflow * vos.secondsPerDay()))  # m3/day                                          

        # downstream demand (m3/day)
        if downstreamDemand == None:
            downstreamDemand = pcr.scalar(0.0)
        else:
            print("We still have to define downstreamDemand.")
        # reduce demand if storage < lower limit
        reductionFactor  = vos.getValDivZero(downstreamDemand, self.minResvrFrac*self.waterBodyCap, vos.smallNumber)
        reductionFactor  = pcr.cover(reductionFactor, 0.0)
        downstreamDemand = pcr.min(
                           downstreamDemand,
                           downstreamDemand*reductionFactor)
        # resvOutflow > downstreamDemand
        resvOutflow  = pcr.max(resvOutflow, downstreamDemand) # m3/day       

        # additional release if storage > upper limit
        ratioQBankfull = 2.3
        estmStorage  = pcr.max(0.,self.waterBodyStorage - resvOutflow)
        floodOutflow = \
           pcr.max(0.0, estmStorage - self.waterBodyCap) +\
           pcr.cover(\
           pcr.max(0.0, estmStorage - self.maxResvrFrac*\
                                      self.waterBodyCap)/\
              ((1.-self.maxResvrFrac)*self.waterBodyCap),0.0)*\
           pcr.max(0.0,ratioQBankfull*avgOutflow* vos.secondsPerDay()-\
                                      resvOutflow)
        floodOutflow = pcr.max(0.0,
                       pcr.min(floodOutflow,\
                       estmStorage - self.maxResvrFrac*\
                                     self.waterBodyCap))
        resvOutflow  = resvOutflow + floodOutflow                                            

        # maximum release if storage > upper limit
        resvOutflow  = pcr.ifthenelse(self.waterBodyStorage > 
                       self.maxResvrFrac*self.waterBodyCap,\
                       pcr.min(resvOutflow,\
                       pcr.max(0,self.waterBodyStorage - \
                       self.maxResvrFrac*self.waterBodyCap)),
                       resvOutflow)                                            

        return (resvOutflow) # unit: m3/day  
