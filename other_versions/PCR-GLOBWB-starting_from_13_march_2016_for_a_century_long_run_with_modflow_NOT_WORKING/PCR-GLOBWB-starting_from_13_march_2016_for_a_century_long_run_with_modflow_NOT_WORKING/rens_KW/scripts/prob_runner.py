#!/usr/bin/env python
# -*- coding: utf-8 -*-

########PCRGLOB-WB with data assimilation######
#### Author N.Wanders (n.wanders@uu.nl)#####
#### Version 1.0 (25-08-2014) ###########

import sys
import logging
logger = logging.getLogger(__name__)

from pcraster.framework import DynamicModel
from pcraster.framework import MonteCarloModel
from pcraster.framework import DynamicFramework

from configuration import Configuration
from currTimeStep import ModelTime
from reporting import Reporting
from spinUp import SpinUp

from pcrglobwb import PCRGlobWB

from EnKF import *

import pcraster as pcr
import virtualOS as vos
import datetime
import numpy

logger = logging.getLogger(__name__)

class DeterministicRunner(DynamicModel, MonteCarloModel):

    def __init__(self, configuration, modelTime, initialState = None):
        DynamicModel.__init__(self)
        MonteCarloModel.__init__(self)

        self._configuration = configuration
        self.modelTime = modelTime        
        self.model = PCRGlobWB(configuration, modelTime, initialState)
        self.reporting = Reporting(configuration, self.model, modelTime)
        self.cmdOptions = sys.argv
        print self.cmdOptions

        self.ids = pcr.nominal(self._configuration.cloneMap)
        self.ObsNum = int(cellvalue(mapmaximum(scalar(self.ids)),1,1)[0])

        SMxloc = []
        SMyloc = []
        for x in range(1,vos.getMapAttributes(self._configuration.cloneMap,"rows")):
            for y in range(1,vos.getMapAttributes(self._configuration.cloneMap,"cols")):
                if cellvalue(self.ids, x, y)[0] >= 1:
                        SMxloc.append(x)
                        SMyloc.append(y)
        self.SMxloc = SMxloc
        self.SMyloc = SMyloc
        
        Qxloc = [1]
        Qyloc = [1]
        self.Qxloc = Qxloc
        self.Qyloc = Qyloc
        print "Qpoints " + str(self.Qxloc)
        print len(self.Qxloc)
		
        self.ReportTime = self._configuration.dataAssimilationOptions['filterTimeSteps']
        self.ReportTime = map(int, self.ReportTime.split(','))
        self.ReportTime.append(0)
        
        self.shortNames = ['f','g','p','n']
        
        print len(self.SMxloc)
        
    def premcloop(self):

        self.mask = boolean(self.model.routing.lddMap)
        xlocs2 = []
        ylocs2 = []
        for x in range(1,vos.getMapAttributes(self._configuration.cloneMap,"rows")):
            for y in range(1,vos.getMapAttributes(self._configuration.cloneMap,"cols")):
                if cellvalue(self.mask, x, y)[1] == True:
                        xlocs2.append(x)
                        ylocs2.append(y)
        self.xlocs2 = xlocs2
        self.ylocs2 = ylocs2
		
        # set initial conditions:
        self.minSoilDepthOrig = {}
        self.maxSoilDepthOrig = {}
        self.degreeDayOrig = {}
        for coverType in self.model.landSurface.coverTypes:
          self.minSoilDepthOrig[coverType] = self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac
          self.maxSoilDepthOrig[coverType] = self.model.landSurface.landCoverObj[coverType].maxSoilDepthFrac
          self.degreeDayOrig[coverType] = self.model.landSurface.landCoverObj[coverType].degreeDayFactor
        self.KSat1Orig = self.model.landSurface.parameters.kSatUpp
        self.KSat2Orig = self.model.landSurface.parameters.kSatLow
        self.THEFF1_50org = self.model.landSurface.parameters.effSatAt50Upp
        self.THEFF2_50org = self.model.landSurface.parameters.effSatAt50Low
        self.recessionOrig = self.model.groundwater.recessionCoeff
        self.routingOrig = self.model.routing.manningsN	

        self.calibrationPara = self._configuration.dataAssimilationOptions['calibrationPara']
        print self.calibrationPara
        self.calibrationPara = self.calibrationPara.split(',')
      
    def initial(self):
        try:
          cmd = 'mkdir '+str(self.currentSampleNumber())+'/stateVar'
          os.system(cmd)
        except:
          foo = 0
        dumpfile("time.obj", int(0),str(self.currentSampleNumber()))
        dumpfile("WriteTime.obj", int(0),"1")
        folderName = self._configuration.dataAssimilationOptions['folderName']
       
        ##perturb the parameter(s):
        if "wmin" in self.calibrationPara:
          self.minSoilDepthAdjust = scalar(numpy.exp(numpy.random.normal(0.0,0.2,1)[0]))
        else:
          self.minSoilDepthAdjust = scalar(1)
        if "wmax" in self.calibrationPara:
          self.maxSoilDepthAdjust = scalar(numpy.exp(numpy.random.normal(0.0,0.6,1)[0]))
        else:
          self.maxSoilDepthAdjust = scalar(1)
        if "ddf" in self.calibrationPara:
          self.degreeDayAdjust = scalar(numpy.exp(numpy.random.normal(0.0,0.6,1)[0]))
        else:
          self.degreeDayAdjust = scalar(1)
        if "theta50" in self.calibrationPara:
          self.Theta50Adjust = scalar(numpy.exp(numpy.random.normal(0.0,0.6,1)[0]))
        else:
          self.Theta50Adjust = scalar(1)
        if "ksat" in self.calibrationPara:
          self.KSatAdjust = scalar(numpy.exp(numpy.random.normal(0.0,0.4,1)[0]))
        else:
          self.KSatAdjust = scalar(1)
        if "j" in self.calibrationPara:
          self.recessionAdjust = scalar(numpy.exp(numpy.random.normal(-1.0,0.6,1)[0]))
        else:
          self.recessionAdjust = scalar(1)
        if "n" in self.calibrationPara:
          self.routingAdjust = scalar(numpy.exp(numpy.random.normal(0.0,0.6,1)[0]))
        else:
          self.routingAdjust = scalar(1)

        if folderName != "None":
	      try:
	        self.minSoilDepthAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/wmin.map")
	      except:
	        self.minSoilDepthAdjust = scalar(1)
	      try:
	        self.maxSoilDepthAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/wmax.map")
	      except:
	        self.maxSoilDepthAdjust = scalar(1)
	      try:
	        self.degreeDayAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/ddf.map")
	      except:
	        self.degreeDayAdjust = scalar(1)
	      try:
	        self.Theta50Adjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/theta.map")
	      except:
	        self.Theta50Adjust = scalar(1)
	      try:
	        self.KSatAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/ksat.map")
	      except:
	        self.KSatAdjust = scalar(1)
	      try:
	        self.recessionAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/j.map")
	      except:
	        self.recessionAdjust = scalar(1)
	      try:
	        self.routingAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/n.map")
	      except:
	        self.routingAdjust = scalar(1)
          
        if self.calibrationPara != "None":
          conPara = open(str(self.currentSampleNumber())+"_paraVals.txt", "w")
        if "wmin" in self.calibrationPara:
          conPara.writelines("wmin"+"\t"+str(cellvalue(self.minSoilDepthAdjust, 1, 1)[0])+"\n")
        if "wmax" in self.calibrationPara:
          conPara.writelines("wmax"+"\t"+str(cellvalue(self.maxSoilDepthAdjust, 1, 1)[0])+"\n")
        if "theta50" in self.calibrationPara:
          conPara.writelines("theta50"+"\t"+str(cellvalue(self.Theta50Adjust, 1, 1)[0])+"\n")
        if "ksat" in self.calibrationPara:
          conPara.writelines("ksat"+"\t"+str(cellvalue(self.KSatAdjust, 1, 1)[0])+"\n")
        if "ddf" in self.calibrationPara:
          conPara.writelines("ddf"+"\t"+str(cellvalue(self.degreeDayAdjust, 1, 1)[0])+"\n")
        if "j" in self.calibrationPara:
          conPara.writelines("j"+"\t"+str(cellvalue(self.recessionAdjust, 1, 1)[0])+"\n")
        if "n" in self.calibrationPara:
          conPara.writelines("n"+"\t"+str(cellvalue(self.routingAdjust, 1, 1)[0])+"\n")
        if "precBias" in self.calibrationPara:
          conPara.writelines("precBias"+"\t"+str(cellvalue(self.precConvectAdjust, 1, 1)[0])+"\n")
        conPara.close()
		
        # Perturb maps
        for coverType in self.model.landSurface.coverTypes:
          self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac = min(self.minSoilDepthOrig[coverType] * self.minSoilDepthAdjust,0.9999)
          self.model.landSurface.landCoverObj[coverType].maxSoilDepthFrac = max(self.maxSoilDepthOrig[coverType]* self.maxSoilDepthAdjust,1.0001)
          self.model.landSurface.landCoverObj[coverType].degreeDayFactor = self.degreeDayOrig[coverType] * self.degreeDayAdjust
        self.model.landSurface.parameters.kSatUpp000005 = self.KSat1Orig * self.KSatAdjust
        self.model.landSurface.parameters.kSatUpp005030 = self.KSat1Orig * self.KSatAdjust
        self.model.landSurface.parameters.kSatLow030150 = self.KSat2Orig * self.KSatAdjust
        self.model.landSurface.parameters.effSatAt50Upp = self.THEFF1_50org * self.Theta50Adjust
        self.model.landSurface.parameters.effSatAt50Low = self.THEFF2_50org * self.Theta50Adjust
        self.model.groundwater.recessionCoeff = self.recessionOrig * self.recessionAdjust
        self.model.routing.manningsN = self.routingOrig * self.routingAdjust

        ## Perturb initial groundwater
        self.model.groundwater.storGroundwater = self.model.groundwater.storGroundwater * (mapnormal() * 0.20 + 1)

        
    def dynamic(self):
        #re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        #update model (will pick up current model time from model time object)
        
        self.model.read_forcings()
        if self._configuration.dataAssimilationOptions['method'] == "EnKF":
          self.model.meteo.precipitation = self.model.meteo.precipitation * scalar(numpy.random.normal(1,0.1,1)[0])
        #self.model.meteo.referencePotET = self.model.meteo.referencePotET * scalar(numpy.random.random(1)[0]*0.1+1.0)
		
        
        WriteTime = int(loadfile("WriteTime.obj", "1"))
        dumpfile("time.obj", int(self.modelTime.timeStepPCR),str(self.currentSampleNumber()))		

        msg = "Date = " + str(self.modelTime.currTime.day)+ "-"+ str(self.modelTime.currTime.month)+ " " + str(self.currentSampleNumber())
        logger.info(msg)
        print self.model.landSurface.coverTypes
        self.model.update(report_water_balance=False)
        
        msg = 'Model update succesfull' + str(self.currentSampleNumber())
        logger.info(msg)

        #do any needed reporting for this time step        
        #self.reporting.report()
        msg = 'Reporting succesfull' + str(self.currentSampleNumber())
        logger.info(msg)

        # writing the model states to disk 
        # - that will be re-used in the "resume" method:
        dumpfile("month.obj", self.modelTime.currTime.month, str(self.currentSampleNumber()))
        dumpfile("day.obj", self.modelTime.currTime.day, str(self.currentSampleNumber()))

        if self.modelTime.timeStepPCR == self.ReportTime[WriteTime]:
          idx = 0
          for coverType in self.model.landSurface.coverTypes:
            report(\
              self.model.landSurface.landCoverObj[coverType].interceptStor,
              str(self.currentSampleNumber())+"/"+"si"+str(self.shortNames[idx])+".map")
            report(\
              self.model.landSurface.landCoverObj[coverType].snowCoverSWE,
              str(self.currentSampleNumber())+"/"+"sc"+str(self.shortNames[idx])+".map")
            report(\
              self.model.landSurface.landCoverObj[coverType].snowFreeWater,
              str(self.currentSampleNumber())+"/"+"sf"+str(self.shortNames[idx])+".map")
            report(\
              self.model.landSurface.landCoverObj[coverType].topWaterLayer,
              str(self.currentSampleNumber())+"/"+"st"+str(self.shortNames[idx])+".map")
            report(\
              self.model.landSurface.landCoverObj[coverType].storUpp,
              str(self.currentSampleNumber())+"/"+"sm"+str(self.shortNames[idx])+".map")
            report(\
              self.model.landSurface.landCoverObj[coverType].storLow,
              str(self.currentSampleNumber())+"/"+"sl"+str(self.shortNames[idx])+".map")
            report(\
              self.model.landSurface.landCoverObj[coverType].interflow,
              str(self.currentSampleNumber())+"/"+"qi"+str(self.shortNames[idx])+".map")
            idx = idx + 1
          report(self.model.groundwater.storGroundwater, str(self.currentSampleNumber())+"/"+"sg"+".map")
          report(self.model.routing.channelStorage, str(self.currentSampleNumber())+"/"+"Qc"+".map")
          report(self.model.routing.avgDischarge, str(self.currentSampleNumber())+"/"+"Qa"+".map")

          report(self.model.routing.timestepsToAvgDischarge, str(self.currentSampleNumber())+"/"+"t"+".map")
          report(self.model.routing.readAvlChannelStorage, str(self.currentSampleNumber())+"/"+"racs"+".map")
          report(self.model.routing.m2tDischarge, str(self.currentSampleNumber())+"/"+"mtd"+".map")
          report(self.model.routing.avgBaseflow, str(self.currentSampleNumber())+"/"+"abf"+".map")
          report(self.model.routing.riverbedExchange, str(self.currentSampleNumber())+"/"+"rbe"+".map")
          report(self.model.routing.waterKC, str(self.currentSampleNumber())+"/"+"wkc"+".map")
          try:
	    ### WaterBodies
            report(self.model.routing.WaterBodies.waterBodyTyp,str(self.currentSampleNumber())+"/"+"ty"+".map")
            report(self.model.routing.WaterBodies.fracWat,str(self.currentSampleNumber())+"/"+"rfr"+".map")
            report(self.model.routing.WaterBodies.waterBodyIds,str(self.currentSampleNumber())+"/"+"ri"+".map")
            report(self.model.routing.WaterBodies.waterBodyArea,str(self.currentSampleNumber())+"/"+"ra"+".map")
            report(self.model.routing.WaterBodies.waterBodyOut,str(self.currentSampleNumber())+"/"+"ro"+".map")
            report(self.model.routing.WaterBodies.waterBodyCap,str(self.currentSampleNumber())+"/"+"rc"+".map")
            report(self.model.routing.WaterBodies.waterBodyStorage, str(self.currentSampleNumber())+"/"+"rs"+".map")
            report(self.model.routing.WaterBodies.avgInflow, str(self.currentSampleNumber())+"/"+"rif"+".map")
            report(self.model.routing.WaterBodies.avgOutflow, str(self.currentSampleNumber())+"/"+"rof"+".map")
          except:
            foo = 0
          try:
            ### WaterDemand
            report(self.model.landSurface.domesticGrossDemand,str(self.currentSampleNumber())+"/"+"dgd"+".map")
            report(self.model.landSurface.domesticNettoDemand,str(self.currentSampleNumber())+"/"+"dnd"+".map")
            report(self.model.landSurface.industryGrossDemand,str(self.currentSampleNumber())+"/"+"igd"+".map")
            report(self.model.landSurface.industryNettoDemand,str(self.currentSampleNumber())+"/"+"ind"+".map")
          except:
            foo = 0            
          try:
            ### Flooding
            report(self.model.routing.dynamicFracWat,str(self.currentSampleNumber())+"/"+"dfw"+".map")
          except:
            foo = 0  
          try:
            ### WaterTemp
            report(self.model.routing.rsw,str(self.currentSampleNumber())+"/"+"rsw"+".map")
            report(self.model.routing.atmosEmis,str(self.currentSampleNumber())+"/"+"rae"+".map")
            report(self.model.routing.waterTemp.str(self.currentSampleNumber())+"/"+"rwt"+".map")
            report(self.model.routing.iceThickness,str(self.currentSampleNumber())+"/"+"rit"+".map")            
          except:
            foo = 0  
          report(self.model.routing.Q, str(self.currentSampleNumber())+"/"+"Q"+".map")

        self.report(self.model.routing.discharge, "q")
          
    def setState(self):
        #~ values = np.zeros(5)
        #~ return values 
        timestep = self.currentTimeStep()
        #print str(timestep) + "State"

        #Qmod = self.readmap("q")
        Qmod = numpy.random.normal(0,1,50)
        Qtel= []
        values = []

        # Principle (at this moment): If there is at least a observation, 
        #                             we get the model state. 

        # The following will be replaced by observation data:

        if self.currentSampleNumber() == 1:
	  for s in range(len(Qmod)):
	    val  = Qmod[s]
	    values.append(val)
	    Qtel.append(s)
	    if len(Qtel) == 0:
	      values.append(numpy.random.normal(0,1,1)[0])
	      Qtel.append(-999)
	  dumpfile("Qtel.obj", Qtel, str(self.currentSampleNumber()))
        else:
	  Qlist = loadfile("Qtel.obj", str(1))
	  if Qlist[-1] != -999:
	    for s in Qlist:
	      val  = Qmod[s]
	      values.append(val)
	      Qtel.append(s)  
	  else:
	    values.append(numpy.random.normal(0,1,1)[0])
	    Qtel.append(-999)	
        print "# Discharge " + str(len(Qtel))
        print values

        values2 = numpy.array(values)
        return values2

    def setObservations(self):
        values = []
        Qtel = loadfile("Qtel.obj", str(1))
        
        self.Qobs = numpy.random.normal(0,1,len(Qtel))
        Qerror = 1.0

        Qlen = len(Qtel)
        for s in Qtel:
          if s != -999:
            val = self.Qobs[s]
            values.append(val)
          else:
            val = numpy.random.normal(0,1000,1)[0]
            values.append(val)

        covariance = numpy.zeros((Qlen, Qlen), dtype=float)            
        for s in range(Qlen):
	  val = values[s]
	  covariance[s,s] = Qerror
        
        dumpfile("WriteTime.obj", int(loadfile("WriteTime.obj", "1"))+1, "1")
        values2 = numpy.array(values)
        observations = numpy.array([values2,]*self.nrSamples()).transpose()

        print values2
        self.setObservedMatrices(observations, covariance)      
        
    def resume(self):
        vec = self.getStateVector(self.currentSampleNumber())
        print vec

        idx = 0
        for coverType in self.model.landSurface.coverTypes:
            self.model.landSurface.landCoverObj[coverType].interceptStor =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"si"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].snowCoverSWE  =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"sc"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].snowFreeWater =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"sf"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].topWaterLayer =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"st"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].storUpp =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"sm"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].storLow =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"sl"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].interflow =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"qi"+str(self.shortNames[idx])+".map"), 0.0)
            idx = idx + 1
        self.model.routing.channelStorage = readmap(str(self.currentSampleNumber())+"/"+"Qc"+".map")
        self.model.routing.avgDischarge = readmap(str(self.currentSampleNumber())+"/"+"Qa"+".map")
        self.model.routing.Q = readmap(str(self.currentSampleNumber())+"/"+"Q"+".map")
        self.model.groundwater.storGroundwater = readmap(str(self.currentSampleNumber())+"/"+"sg"+".map")

        self.model.routing.timestepsToAvgDischarge = readmap(str(self.currentSampleNumber())+"/"+"t"+".map")
        self.model.routing.readAvlChannelStorage = readmap(str(self.currentSampleNumber())+"/"+"racs"+".map")
        self.model.routing.m2tDischarge = readmap(str(self.currentSampleNumber())+"/"+"mtd"+".map")
        self.model.routing.avgBaseflow = readmap(str(self.currentSampleNumber())+"/"+"abf"+".map")
        self.model.routing.riverbedExchange = readmap(str(self.currentSampleNumber())+"/"+"rbe"+".map")
        self.model.routing.waterKC = readmap(str(self.currentSampleNumber())+"/"+"wkc"+".map")
        try:
	  ### WaterBodies
          self.model.routing.WaterBodies.waterBodyTyp = readmap(str(self.currentSampleNumber())+"/"+"ty"+".map")
          self.model.routing.WaterBodies.fracWat = readmap(str(self.currentSampleNumber())+"/"+"rfr"+".map")
          self.model.routing.WaterBodies.waterBodyIds = readmap(str(self.currentSampleNumber())+"/"+"ri"+".map")
          self.model.routing.WaterBodies.waterBodyArea = readmap(str(self.currentSampleNumber())+"/"+"ra"+".map")
          self.model.routing.WaterBodies.waterBodyOut = readmap(str(self.currentSampleNumber())+"/"+"ro"+".map")
          self.model.routing.WaterBodies.waterBodyCap = readmap(str(self.currentSampleNumber())+"/"+"rc"+".map")
          self.model.routing.WaterBodies.waterBodyStorage = readmap(str(self.currentSampleNumber())+"/"+"rs"+".map")
          self.model.routing.WaterBodies.avgInflow = readmap(str(self.currentSampleNumber())+"/"+"rif"+".map")
          self.model.routing.WaterBodies.avgOutflow = readmap(str(self.currentSampleNumber())+"/"+"rof"+".map")
        except:
          foo = 0
        try:
          ### WaterDemand
          self.model.landSurface.domesticGrossDemand = readmap(str(self.currentSampleNumber())+"/"+"dgd"+".map")
          self.model.landSurface.domesticNettoDemand = readmap(str(self.currentSampleNumber())+"/"+"dnd"+".map")
          self.model.landSurface.industryGrossDemand = readmap(str(self.currentSampleNumber())+"/"+"igd"+".map")
          self.model.landSurface.industryNettoDemand = readmap(str(self.currentSampleNumber())+"/"+"ind"+".map")
        except:
          foo = 0
        try:
          ### Flooding
          self.model.routing.dynamicFracWat = readmap(str(self.currentSampleNumber())+"/"+"dfw"+".map")
        except:
          foo = 0        
        try:
          ### WaterTemp
          self.model.routing.rsw = readmap(str(self.currentSampleNumber())+"/"+"rsw"+".map")
          self.model.routing.atmosEmis = readmap(str(self.currentSampleNumber())+"/"+"rae"+".map")
          self.model.routing.waterTemp = readmap(str(self.currentSampleNumber())+"/"+"rwt"+".map")
          self.model.routing.iceThickness = readmap(str(self.currentSampleNumber())+"/"+"rit"+".map")
        except:
          foo = 0    

def main():
    initial_state = None
    configuration = Configuration()
    
    spin_up = SpinUp(configuration)                   # object for spin_up
    
    currTimeStep = ModelTime() # timeStep info: year, month, day, doy, hour, etc
    
    # spinningUp
    noSpinUps = int(configuration.globalOptions['maxSpinUpsInYears'])
    if noSpinUps > 0:
        
        logger.info('Spin-Up #Total Years: '+str(noSpinUps))

        spinUpRun = 0 ; has_converged = False
        while spinUpRun < noSpinUps and has_converged == False:
            spinUpRun += 1
            currTimeStep.getStartEndTimeStepsForSpinUp(
                    configuration.globalOptions['startTime'],
                    spinUpRun, noSpinUps)
            logger.info('Spin-Up Run No. '+str(spinUpRun))
            deterministic_runner = DeterministicRunner(configuration, currTimeStep, initial_state)
            
            all_state_begin = deterministic_runner.model.getAllState() 
            
            dynamic_framework = DynamicFramework(deterministic_runner,currTimeStep.nrOfTimeSteps)
            dynamic_framework.setQuiet(True)
            dynamic_framework.run()
            
            all_state_end = deterministic_runner.model.getAllState() 
            
            has_converged = spin_up.checkConvergence(all_state_begin, all_state_end, spinUpRun, deterministic_runner.model.routing.cellArea)
            
            initial_state = deterministic_runner.model.getState()
    #
    # Running the deterministic_runner (excluding DA scheme)
    currTimeStep.getStartEndTimeSteps(configuration.globalOptions['startTime'],
                                      configuration.globalOptions['endTime'])
    
    logger.info('Transient simulation run started.')
    deterministic_runner = DeterministicRunner(configuration, currTimeStep, initial_state)
    
    dynamic_framework = DynamicFramework(deterministic_runner,currTimeStep.nrOfTimeSteps)
    dynamic_framework.setQuiet(True)
    if configuration.dataAssimilationOptions['method'] == "None":
        dynamic_framework.run()
    else:
        nrSamples = int(configuration.dataAssimilationOptions['nrSamples'])
        mcModel = MonteCarloFramework(dynamic_framework,nrSamples)
        mcModel.setForkSamples(True, nrCPUs=int(configuration.dataAssimilationOptions['nrCores']))
    if configuration.dataAssimilationOptions['method'] == "MonteCarlo":
        mcModel.run()
    if configuration.dataAssimilationOptions['method'] == "EnKF":
        ekfModel = EnsKalmanFilterFramework(mcModel)
        filterTime = configuration.dataAssimilationOptions['filterTimeSteps']
        filterTime = map(int, filterTime.split(','))
        ekfModel.setFilterTimesteps(filterTime)    #range(365,6900,30)
        ekfModel.run()

        
if __name__ == '__main__':
    sys.exit(main())

