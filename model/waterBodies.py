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
                
        self.debugWaterBalance = iniItems.routingOptions['debugWaterBalance']

        # TODO: 26 Feb 2014, Edwin found that reasonable runs are only found 
        # if all of these options = True.                    
        self.includeWaterBodies = True
        self.includeLakes = True
        self.includeReservoirs =  True

        if iniItems.routingOptions['waterBodyInputNC'] == str(None):
            self.useNetCDF = False
            self.fracWaterInp    = iniItems.routingOptions['fracWaterInp']
            self.waterBodyIdsInp = iniItems.routingOptions['waterBodyIds']
            self.waterBodyTypInp = iniItems.routingOptions['waterBodyTyp']
            self.resMaxCapInp    = iniItems.routingOptions['resMaxCapInp']
            self.resSfAreaInp    = iniItems.routingOptions['resSfAreaInp']
        else:
            self.useNetCDF = True
            self.ncFileInp       = vos.getFullPath(\
                                   iniItems.routingOptions['waterBodyInputNC'],\
                                   self.inputDir)

        # minimum width (m) used in the weir formula  # TODO: define minWeirWidth based on the GLWD, GRanD database and/or bankfull discharge formula 
        self.minWeirWidth = 10.

        # lower and upper limits at which reservoir release is terminated and 
        #                        at which reservoir release is equal to long-term average outflow
        self.minResvrFrac = 0.10
        self.maxResvrFrac = 0.75

    def getParameterFiles(self,currTimeStep,cellArea,ldd,\
                               cellLengthFD,cellSizeInArcDeg,\
                               channelStorage=None,avgInflow=None,avgOutflow=None):

        # parameters for Water Bodies: fracWat 
        #                              waterBodyIds
        #                              waterBodyOut
        #                              waterBodyArea 
        #                              waterBodyTyp
        #                              waterBodyCap
        
        self.cellArea = cellArea
        
        #    fracWat = fraction of surface water bodies
        self.fracWat = pcr.scalar(0.0)
        
        if self.includeWaterBodies:
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

        if self.includeLakes or self.includeReservoirs:

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
        
        if self.includeLakes or self.includeReservoirs:

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

        # reservoir maximum capacity (m3):
        self.resMaxCap = pcr.scalar(0.0)
        self.waterBodyCap = pcr.scalar(0.0)

        if self.includeReservoirs:

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
                                                   
            # correcting water body types:                              # Reservoirs that have zero capacities will be assumed as lakes.
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
        # initiating storage, average inflow and outflow
        #
        if currTimeStep.timeStepPCR > 1:
            self.waterBodyStorage = pcr.cover(self.waterBodyStorage,0.0)
            self.avgInflow        = pcr.cover(self.avgInflow ,0.0)
            self.avgOutflow       = pcr.cover(self.avgOutflow,0.0)
        else:
            # at the beginning of simulation period (timeStepPCR = 1)
            # - we have to define the initial conditions 
            self.getICs(channelStorage,avgInflow,avgOutflow)

        # cropping only in the landmask (ldd) region:
        self.fracWat           = pcr.ifthen(defined(ldd), self.fracWat         )
        self.waterBodyIds      = pcr.ifthen(defined(ldd), self.waterBodyIds    ) 
        self.waterBodyOut      = pcr.ifthen(defined(ldd), self.waterBodyOut    )
        self.waterBodyArea     = pcr.ifthen(defined(ldd), self.waterBodyArea   )
        self.waterBodyTyp      = pcr.ifthen(defined(ldd), self.waterBodyTyp    )  
        self.waterBodyCap      = pcr.ifthen(defined(ldd), self.waterBodyCap    )
        self.waterBodyStorage  = pcr.ifthen(defined(ldd), self.waterBodyStorage)
        self.avgInflow         = pcr.ifthen(defined(ldd), self.avgInflow       )
        self.avgOutflow        = pcr.ifthen(defined(ldd), self.avgOutflow      )

    def getICs(self,channelStorage,avgInflow,avgOutflow):

        # calculate waterBodyStorage at cells where lakes and/or reservoirs are defined
        #
        storageAtLakeAndReservoirs = pcr.cover(\
         pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., channelStorage), 0.0)
        #
        # - move only non negative values and use rounddown values
        storageAtLakeAndReservoirs = pcr.max(0.00, pcr.rounddown(storageAtLakeAndReservoirs))
        #
        # lake and reservoir storages = waterBodyStorage (m3) ; values are given for the entire lake / reservoir cells
        self.waterBodyStorage = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., \
                                           pcr.areatotal(storageAtLakeAndReservoirs,\
                                                         self.waterBodyIds))

        self.avgInflow        = pcr.cover(avgInflow , 0.0)              # unit: m3/s 
        self.avgOutflow       = pcr.cover(avgOutflow, 0.0)              # unit: m3/s
        self.waterBodyStorage = pcr.cover(self.waterBodyStorage, 0.0)   # unit: m3

    def update(self,newStorageAtLakeAndReservoirs,\
                              timestepsToAvgDischarge,\
                           maxTimestepsToAvgDischargeShort,
                           maxTimestepsToAvgDischargeLong,\
                           currTimeStep,\
                           avgChannelDischarge = None,\
                           downstreamDemand = None):

        if self.includeLakes or self.includeReservoirs:

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
                 avgChannelDischarge,\
                 downstreamDemand)
         
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
                                        pcr.areatotal(newStorageAtLakeAndReservoirs,\
                                                      self.waterBodyIds),0.0)

        # inflow (m3/day)
        self.inflow = newStorageAtLakeAndReservoirs - self.waterBodyStorage
        
        # inflowInM3PerSec (m3/s)
        inflowInM3PerSec = self.inflow / (vos.secondsPerDay())

        # updating (short term) average inflow (m3/s) ; needed to constrain lake outflow:
        deltaInflow = inflowInM3PerSec - self.avgInflow  
        self.avgInflow = self.avgInflow +\
                            deltaInflow/\
                            pcr.min(maxTimestepsToAvgDischargeShort, self.timestepsToAvgDischarge)                
        self.avgInflow = pcr.max(0.0, self.avgInflow)                         

        # updating waterBodyStorage (m3)
        self.waterBodyStorage = newStorageAtLakeAndReservoirs

    def getWaterBodyOutflow(self,\
                            maxTimestepsToAvgDischargeLong,\
                            avgChannelDischarge = None,\
                            downstreamDemand = None):

        # outflow from water bodies with lake type (m3/day): 
        if self.includeLakes: 
            lakeOutflow = self.getLakeOutflow(avgChannelDischarge)  
            self.waterBodyOutflow = lakeOutflow
             
        # outflow from water bodies with reservoir type (m3/day): 
        if self.includeReservoirs:
            reservoirOutflow = self.getReservoirOutflow(avgChannelDischarge)  
            self.waterBodyOutflow = reservoirOutflow

        if self.includeLakes and self.includeReservoirs:
            self.waterBodyOutflow = pcr.cover(reservoirOutflow, lakeOutflow)  
        
        # make sure that all water bodies have outflow:
        self.waterBodyOutflow = pcr.max(0.,
                                pcr.cover(self.waterBodyOutflow,0.0))

        # limit outflow to available storage
        factor = 0.25  # to avoid flip flop 
        self.waterBodyOutflow = pcr.min(self.waterBodyStorage * factor,\
                                        self.waterBodyOutflow)                    # unit: m3/day
        # use round values 
        self.waterBodyOutflow = pcr.rounddown(self.waterBodyOutflow/100.)*100.    # unit: m3/day
        
        # outflow in m3 per sec
        waterBodyOutflowInM3PerSec = self.waterBodyOutflow / vos.secondsPerDay()  # unit: m3/s

        # update average discharge (outflow) m3/s
        deltaOutflow    = waterBodyOutflowInM3PerSec - self.avgOutflow
        self.avgOutflow = self.avgOutflow +\
                             deltaOutflow/\
                            pcr.min(maxTimestepsToAvgDischargeLong, self.timestepsToAvgDischarge)                
        self.avgOutflow = pcr.max(0.0, self.avgOutflow)                         

        # update waterBodyStorage (after outflow):
        self.waterBodyStorage = self.waterBodyStorage -\
                                self.waterBodyOutflow
        self.waterBodyStorage = pcr.max(0.0, self.waterBodyStorage)                        

    def weirFormula(self,waterHeight,weirWidth): # output: m3/s
        sillElev  = pcr.scalar(0.0) 
        weirCoef  = pcr.scalar(1.0)
        weirFormula = \
         (1.7*weirCoef*pcr.max(0,waterHeight-sillElev)**1.5) *\
             weirWidth # m3/s
        return (weirFormula)

    def getLakeOutflow(self,avgChannelDischarge=None):

        # waterHeight (m): temporary variable, a function of storage:
        minWaterHeight = 0.001 # (m) Rens used 0.001 m - in order to make sure there is at least 
        waterHeight = pcr.cover(
                      pcr.max(minWaterHeight, \
                      (self.waterBodyStorage - \
                      pcr.cover(self.waterBodyCap, 0.0))/\
                      self.waterBodyArea),0.)

        # weirWidth (m) : estimated from avgOutflow (m3/s)
        avgOutflow = self.avgOutflow
        try:
            avgOutflow = pcr.ifthenelse(avgOutflow > 0.,\
                         avgOutflow,pcr.max(avgChannelDischarge,self.avgInflow,0.001))
            avgOutflow = pcr.areamaximum(avgOutflow,self.waterBodyIds)             	
        except:
            pass 
        bankfullWidth = pcr.cover(\
                        pcr.scalar(4.8) * \
                        ((avgOutflow)**(0.5)),0.)
        weirWidthUsed = bankfullWidth
        weirWidthUsed = pcr.max(weirWidthUsed,self.minWeirWidth)        # TODO: minWeirWidth based on the GRanD database
        weirWidthUsed = pcr.cover(
                        pcr.ifthen(\
                        pcr.scalar(self.waterBodyIds) > 0.,\
                        weirWidthUsed),0.0)

        # avgInflow <= lakeOutflow (weirFormula) <= waterBodyStorage
        lakeOutflow = pcr.max(\
                      self.weirFormula(waterHeight,weirWidthUsed),\
                      self.avgInflow) * vos.secondsPerDay() # m3/day
        lakeOutflow = pcr.min(self.waterBodyStorage, lakeOutflow)

        lakeOutflow = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., lakeOutflow)
        lakeOutflow = pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 1, lakeOutflow)
        return (lakeOutflow) # unit: m3/day

    def getReservoirOutflow(self,\
        avgChannelDischarge=None,downstreamDemand=None):

        # avgOutflow (m3/s)
        avgOutflow = self.avgOutflow
        try:
            avgOutflow = pcr.ifthenelse(avgOutflow > 0.,\
                         avgOutflow,pcr.max(avgChannelDischarge,self.avgInflow,0.001))
            avgOutflow = pcr.areamaximum(avgOutflow,self.waterBodyIds)
        except:
            pass

        # calculate resvOutflow (based on reservoir storage and avgDischarge): 
        # - unit: m3/day (Note that avgDischarge is given in m3/s) 
        # - using reductionFactor in such a way that:
        #   - if relativeCapacity < minResvrFrac : release is terminated
        #   - if relativeCapacity > maxResvrFrac : longterm average
        reductionFactor = \
         pcr.cover(\
         pcr.min(1.,
         pcr.max(0., \
          self.waterBodyStorage - self.minResvrFrac*self.waterBodyCap)/\
             (self.maxResvrFrac - self.minResvrFrac)*self.waterBodyCap),0.0)
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

        # floodOutflow: additional release if storage > upper limit
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
                                     self.waterBodyCap*0.75)) # maximum limit of floodOutflow: bring the reservoir storages only to 3/4 of upper limit capacities
        
        # update resvOutflow after floodOutflow
        resvOutflow  = pcr.cover(resvOutflow , 0.0) +\
                       pcr.cover(floodOutflow, 0.0)                                            

        # maximum release if storage > upper limit : bring the reservoir storages only to 3/4 of upper limit capacities
        resvOutflow  = pcr.ifthenelse(self.waterBodyStorage > 
                       self.maxResvrFrac*self.waterBodyCap,\
                       pcr.min(resvOutflow,\
                       pcr.max(0,self.waterBodyStorage - \
                       self.maxResvrFrac*self.waterBodyCap*0.75)),
                       resvOutflow)                                            

        # if storage > upper limit : resvOutflow > avgInflow
        resvOutflow  = pcr.ifthenelse(self.waterBodyStorage > 
                       self.maxResvrFrac*self.waterBodyCap,\
                       pcr.max(0.0, resvOutflow, self.avgInflow),
                       resvOutflow)                                            
        
        # resvOutflow < waterBodyStorage
        resvOutflow = pcr.min(self.waterBodyStorage, resvOutflow)
        
        resvOutflow = pcr.ifthen(pcr.scalar(self.waterBodyIds) > 0., resvOutflow)
        resvOutflow = pcr.ifthen(pcr.scalar(self.waterBodyTyp) == 2, resvOutflow)
        return (resvOutflow) # unit: m3/day  
