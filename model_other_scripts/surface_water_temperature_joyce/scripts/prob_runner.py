#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
logger = logging.getLogger(__name__)

sys.path.append("/home/wande001/pcrglobwb/EnKF")

print sys.path

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

logger = logging.getLogger(__name__)

class DeterministicRunner(DynamicModel, MonteCarloModel):

    def __init__(self, configuration, modelTime, initialState = None):
        DynamicModel.__init__(self)
        MonteCarloModel.__init__(self)

        self._configuration = configuration
        self.modelTime = modelTime        
        self.model = PCRGlobWB(configuration, modelTime, initialState)
        self.reporting = Reporting(configuration, self.model, modelTime)

        #cmd = 'cp '+str(self._configuration.cloneMap)+' clone.map'
        #os.system(cmd)
        #os.system('pcrcalc id.map = "uniqueid(clone.map)"')

        self.ids = pcr.nominal(str(self._configuration.globalOptions['observationDir'])+"ObsPoints.map")
        self.ObsNum = int(cellvalue(mapmaximum(scalar(self.ids)),1,1)[0])
        self.TRes = pcr.nominal(1)

        Qxloc = []
        Qyloc = []
        for x in range(1,vos.getMapAttributes(self._configuration.cloneMap,"rows")):
            for y in range(1,vos.getMapAttributes(self._configuration.cloneMap,"cols")):
                if cellvalue(self.ids, x, y)[0] >= 1:
                        Qxloc.append(x)
                        Qyloc.append(y)
        self.Qxloc = Qxloc
        self.Qyloc = Qyloc

        self.ReportTime = self._configuration.dataAssimilationOptions['filterTimeSteps']
        self.ReportTime = map(int, self.ReportTime.split(','))
        self.ReportTime.append(0)
        
        self.shortNames = ['f','g','p','n']
        
        print len(self.Qxloc)
        
    def premcloop(self):

        # Niko's way to identify coordinates of active/landmask cells: 
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


        self.CatchTotal = catchmenttotal(self.model.routing.cellArea,self.model.routing.lddMap)

        self.Height = pcr.scalar(str(self._configuration.globalOptions['EnKFinputDir'])+"elevation/dem30min.map")
        self.Slope = pcr.scalar(str(self._configuration.globalOptions['EnKFinputDir'])+"elevation/slope30min.map")
        self.Aspect = scalar(aspect(self.Height))
        self.Aspect = cover(self.Aspect, 0.0)
        self.Slope = cover(self.Slope, 0.0)        

        conPara = open(str(1)+"/errorGlobal.txt", "w")
        conPara.writelines(str(1)+"\t"+str(0.0)+"\n")
        conPara.close()

        self.calibrationPara = self._configuration.dataAssimilationOptions['calibrationPara']

    def initial(self):
        try:
          cmd = 'mkdir '+str(self.currentSampleNumber())+'/stateVar'
          os.system(cmd)
        except:
          foo = 0
        dumpfile("time.obj", int(0),"1")
        dumpfile("WriteTime.obj", int(0),"1")
        folderName = self._configuration.dataAssimilationOptions['folderName']

        ##perturb the parameter(s):
        if folderName == "None":
          if "wmin" in self.calibrationPara:
	    self.minSoilDepthAdjust = mapnormal() * 0.1 + 1
	  else:
	    self.minSoilDepthAdjust = scalar(1)
	  if "wmax" in self.calibrationPara:
	    self.maxSoilDepthAdjust = mapnormal() * 0.1 + 1
	  else:
	    self.maxSoilDepthAdjust = scalar(1)
	  if "ddf" in self.calibrationPara:
	    self.degreeDayAdjust = mapnormal() * 0.1 + 1
	  else:
	    self.degreeDayAdjust = scalar(1)
	  if "theta50" in self.calibrationPara:
	    self.Theta50Adjust = mapnormal() * 0.1 + 1
	  else:
	    self.Theta50Adjust = scalar(1)
	  if "ksat" in self.calibrationPara:
	    self.KSatAdjust = mapnormal() * 0.1 + 1
	  else:
	    self.KSatAdjust = scalar(1)
	  if "j" in self.calibrationPara:
	    self.recessionAdjust = mapnormal() * 0.1 + 1
	  else:
	    self.recessionAdjust = scalar(1)
	  if "n" in self.calibrationPara:
	    self.routingAdjust = mapnormal() * 0.03 + 1
	  else:
	    self.routingAdjust = scalar(1)
	  if "precBias" in self.calibrationPara:
	    self.precBiasAdjust = mapnormal() * 0.03
	  else:
	    self.precBiasAdjust = scalar(0)
	  if "precConvec" in self.calibrationPara:
	    self.precConvectAdjust = mapnormal() * 0.03
	  else:
	    self.precConvectAdjust = scalar(0)
	  if "precWindWard" in self.calibrationPara:
	    self.precHeightAdjust1 = mapnormal() * 0.03
	  else:
	    self.precHeightAdjust1 = scalar(0)
	  if "precLeeWard" in self.calibrationPara:
	    self.precHeightAdjust2 = mapnormal() * 0.03
	  else:
	    self.precHeightAdjust2 = scalar(0)
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
          try:
	    self.precBiasAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/precBias.map")
	  except:
	    self.precBiasAdjust = scalar(0)
          try:
	    self.precConvectAdjust = readmap(folderName+"/"+str(self.currentSampleNumber())+"/precConvec.map")
	  except:
	    self.precConvectAdjust = scalar(0)
          try:
	    self.precHeightAdjust1 = readmap(folderName+"/"+str(self.currentSampleNumber())+"/precWindWard.map")
	  except:
	    self.precHeightAdjust1 = scalar(0)
          try:
	    self.precHeightAdjust2 = readmap(folderName+"/"+str(self.currentSampleNumber())+"/precLeeWard.map")      
	  except:
	    self.precHeightAdjust2 = scalar(0)
          
        if "wmin" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/wmin.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.minSoilDepthAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "wmax" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/wmax.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.maxSoilDepthAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "theta50" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/theta50.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.Theta50Adjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "ksat" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/ksat.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.KSatAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "ddf" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/ddf.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.degreeDayAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "j" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/j.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.recessionAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "n" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/n.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.routingAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "precBias" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/precBias.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.precConvectAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "precConvec" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/precConvec.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.precBiasAdjust, 1, 1)[0])+"\n")
	  conPara.close()
        if "precWindWard" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/precWindWard.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.precHeightAdjust1, 1, 1)[0])+"\n")
	  conPara.close()
        if "precLeeWard" in self.calibrationPara:
	  conPara = open(str(self.currentSampleNumber())+"/precLeeWard.txt", "w")
	  conPara.writelines("1"+"\t"+str(cellvalue(self.precHeightAdjust2, 1, 1)[0])+"\n")
	  conPara.close()
        
        # Perturb maps
        for coverType in self.model.landSurface.coverTypes:
          self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac = min(self.minSoilDepthOrig[coverType] * self.minSoilDepthAdjust,0.9999)
          self.model.landSurface.landCoverObj[coverType].maxSoilDepthFrac = max(self.maxSoilDepthOrig[coverType]* self.maxSoilDepthAdjust,1.0001)
          self.model.landSurface.landCoverObj[coverType].degreeDayFactor = self.degreeDayOrig[coverType] * self.degreeDayAdjust
        self.model.landSurface.parameters.kSatUpp = self.KSat1Orig * self.KSatAdjust
        self.model.landSurface.parameters.kSatLow = self.KSat2Orig * self.KSatAdjust
        self.model.landSurface.parameters.effSatAt50Upp = self.THEFF1_50org * self.Theta50Adjust
        self.model.landSurface.parameters.effSatAt50Low = self.THEFF2_50org * self.Theta50Adjust
        self.model.groundwater.recessionCoeff = self.recessionOrig * self.recessionAdjust
        self.model.routing.manningsN = self.routingOrig * self.routingAdjust

        self.model.groundwater.storGroundwater = self.model.groundwater.storGroundwater * (mapnormal() * 0.20 + 1)
        
        self.Qaccu = scalar(0)
        self.Precacc = scalar(0)
        self.PrecAdacc = scalar(0)
        self.Evap = scalar(0)
        self.annualPrec = scalar(0)
        self.Runoff = scalar(0)
        self.Eint = scalar(0)
        self.Esoil = scalar(0)
        self.Etrans = scalar(0)
        self.Epaddy = scalar(0)
        self.Ewater = scalar(0)
        self.Esnow = scalar(0)
        self.actInfiltration = scalar(0)
        self.gwRecharge = scalar(0)
        self.interFlow = scalar(0)
        self.directRunoff = scalar(0)
        self.baseFlow = scalar(0)
        self.surfaceWaterRunoff = scalar(0)
        self.irrGrossDemand = scalar(0)
        self.nonIrrGrossDemand = scalar(0)
        self.totalGrossDemand = scalar(0)
        self.nonFossilGroundWater = scalar(0)
        self.otherWater = scalar(0)
        self.abstrSurfaceWater = scalar(0)
        self.riverBed = scalar(0)
        self.nonIrrConsumption = scalar(0)
        self.activeStorage = scalar(0)
        
    def dynamic(self):
        #re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        #update model (will pick up current model time from model time object)
        
        self.model.read_forcings()
        
        WriteTime = int(loadfile("WriteTime.obj", "1"))
        if self.modelTime.currTime.day == 1 or self.modelTime.timeStepPCR == 1:
          ### Calculate Windresistance
          if self.modelTime.currTime.year < 1979:
	    self.Uwind = vos.netcdf2PCRobjCloneWind(str(self._configuration.globalOptions['EnKFinputDir'])+"meteo/pcrERA-40-WindComponents1957-2002.nc", "v10u", self.modelTime.fulldate)
	    self.Vwind = vos.netcdf2PCRobjCloneWind(str(self._configuration.globalOptions['EnKFinputDir'])+"meteo/pcrERA-40-WindComponents1957-2002.nc", "v10v", self.modelTime.fulldate)
	  else:
	    self.Uwind = vos.netcdf2PCRobjCloneWind(str(self._configuration.globalOptions['EnKFinputDir'])+"meteo/pcrERA-Interim-WindComponents1979-2013.nc", "v10u", self.modelTime.fulldate)
	    self.Vwind = vos.netcdf2PCRobjCloneWind(str(self._configuration.globalOptions['EnKFinputDir'])+"meteo/pcrERA-Interim-WindComponents1979-2013.nc", "v10v", self.modelTime.fulldate)	    
          self.Wind = (self.Uwind**2 + self.Vwind**2)**0.5
          self.Wind = (self.Uwind**2 + self.Vwind**2)**0.5
          self.WindDir = scalar(atan(abs(self.Vwind)/abs(self.Uwind)))
          self.WindDir = ifthenelse(self.Uwind > 0, ifthenelse(self.Vwind > 0, self.WindDir, 360-self.WindDir), ifthenelse(self.Vwind > 0, 180-self.WindDir, 180+self.WindDir))
          self.Resistance = cos(abs(self.Aspect - self.WindDir)) * self.Slope
          self.TravelDist = vos.netcdf2PCRobjCloneWindDist(str(self._configuration.globalOptions['EnKFinputDir'])+"meteo/Climatology_winddis.nc", "Dist", self.modelTime.currTime.month, useDoy = "Yes")
          self.AvgSlope = self.Height/self.TravelDist
          ### Reset Qaccu
          self.Qaccu = scalar(0)
          self.Precacc = scalar(0)
          self.PrecAdacc = scalar(0)
          dumpfile("time.obj", self.modelTime.timeStepPCR-1,str(self.currentSampleNumber()))      

        self.Cor1 = self.precHeightAdjust1 * max(self.Resistance, 0.0)
        self.Cor2 = self.precHeightAdjust2 * min(self.Resistance, 0.0)
        self.Cor3 = self.precConvectAdjust * self.AvgSlope
        self.Precacc += self.model.meteo.precipitation
        self.model.meteo.precipitation = self.model.meteo.precipitation * min(max((1 + self.precBiasAdjust + self.Cor1 + self.Cor2 + self.Cor3),0.1),2.0)
        self.PrecAdacc += self.model.meteo.precipitation          

        msg = "Date = " + str(self.modelTime.currTime.day)+ "-"+ str(self.modelTime.currTime.month)+ " " + str(self.currentSampleNumber())
        logger.info(msg)
        
        self.model.update(report_water_balance=False)
        
        msg = 'Model update succesfull' + str(self.currentSampleNumber())
        logger.info(msg)

        #do any needed reporting for this time step        
        self.reporting.report()
        msg = 'Reporting succesfull' + str(self.currentSampleNumber())
        logger.info(msg)

        self.Qaccu += self.model.routing.discharge

        self.Runoff += self.reporting.totalRunoff 
        self.annualPrec += self.model.meteo.precipitation
        self.Evap += self.reporting.totalEvaporation
        self.Eint += self.reporting.interceptEvap
        self.Esoil += self.reporting.actBareSoilEvap
        self.Etrans += self.reporting.actTranspiTotal
        self.Epaddy += self.reporting.topWaterLayerEvap
        self.Ewater += self.reporting.waterBodyActEvaporation
        self.Esnow += self.reporting.actSnowFreeWaterEvap
        
        self.actInfiltration += self.reporting.infiltration
        self.gwRecharge += self.reporting.gwRecharge
        self.interFlow += self.reporting.interflowTotal
        self.directRunoff += self.reporting.directRunoff
        self.baseFlow += self.model.groundwater.baseflow
        self.surfaceWaterRunoff += self.reporting.local_water_body_flux
        self.irrGrossDemand += self.reporting.irrGrossDemand
        self.nonIrrGrossDemand += self.reporting.nonIrrGrossDemand
        self.nonIrrConsumption += self.model.routing.nonIrrReturnFlow
        self.totalGrossDemand += self.reporting.totalGrossDemand
        self.nonFossilGroundWater += self.reporting.nonFossilGroundWaterAbstraction
        self.otherWater += self.reporting.otherWaterSourceAbstraction
        self.abstrSurfaceWater += self.reporting.surfaceWaterAbstraction
        
        self.riverBed += self.model.routing.riverbedExchange/self.model.routing.cellArea
        
        self.activeStorage += self.model.groundwater.unmetDemand

        # writing the model states to disk 
        # - that will be re-used in the "resume" method:
        dumpfile("month.obj", self.modelTime.currTime.month, str(self.currentSampleNumber()))
        dumpfile("day.obj", self.modelTime.currTime.day, str(self.currentSampleNumber()))
        print self.ReportTime[WriteTime]
        print self.currentTimeStep()
        print self.modelTime.timeStepPCR
        if (self.modelTime.currTime.month == 1 and self.modelTime.currTime.day == 31) or (self.modelTime.currTime.month == 2 and self.modelTime.currTime.day == 28) or (self.modelTime.currTime.month == 2 and self.modelTime.currTime.day == 29) or\
            (self.modelTime.currTime.month == 3 and self.modelTime.currTime.day == 31) or (self.modelTime.currTime.month == 4 and self.modelTime.currTime.day == 30) or (self.modelTime.currTime.month == 5 and self.modelTime.currTime.day == 31) or\
            (self.modelTime.currTime.month == 6 and self.modelTime.currTime.day == 30) or (self.modelTime.currTime.month == 7 and self.modelTime.currTime.day == 31) or (self.modelTime.currTime.month == 8 and self.modelTime.currTime.day == 31) or\
            (self.modelTime.currTime.month == 9 and self.modelTime.currTime.day == 30) or (self.modelTime.currTime.month == 10 and self.modelTime.currTime.day == 31) or (self.modelTime.currTime.month == 11 and self.modelTime.currTime.day == 30) or (self.modelTime.currTime.month == 12 and self.modelTime.currTime.day == 31):
	      self.report(self.Qaccu/scalar(self.modelTime.currTime.day), "q_acc")
	      self.report(self.PrecAdacc, "precAd")
	      self.report(self.Precacc, "precOr")
        if(self.modelTime.currTime.month == 12 and self.modelTime.currTime.day == 31):
	      self.report(self.Evap, "evap")
	      self.report(self.annualPrec, "anPrec")
	      self.report(self.Runoff, "runoff")
	      self.report(self.Eint, "Eint")
	      self.report(self.Esoil, "Esoil")
	      self.report(self.Etrans, "Etrans")
	      self.report(self.Epaddy, "Epaddy")
	      self.report(self.Ewater, "Ewater")
	      self.report(self.Esnow, "Esnow")
	      self.report(self.actInfiltration, "actInf")
	      self.report(self.gwRecharge, "gwRch")
	      self.report(self.interFlow, "intFlo")
	      self.report(self.directRunoff, "dirRun")
	      self.report(self.baseFlow, "basFlo")
	      self.report(self.surfaceWaterRunoff, "surf")
	      self.report(self.irrGrossDemand, "irrGro")
	      self.report(self.nonIrrGrossDemand, "nonIrr")
	      self.report(self.nonIrrConsumption, "nonCon")
	      self.report(self.totalGrossDemand, "totDem")
	      self.report(self.nonFossilGroundWater, "nonFos")
	      self.report(self.otherWater, "othWat")
	      self.report(self.abstrSurfaceWater, "surAbs")
	      self.report(self.riverBed, "rivBed")
	      self.report(self.reporting.totalWaterStorageThickness + self.activeStorage, "stor")
	      self.report(self.model.routing.channelStorage/self.model.routing.cellArea, "chaSto")
	      self.Evap = scalar(0)
	      self.annualPrec = scalar(0)
	      self.Runoff = scalar(0)
	      self.Eint = scalar(0)
	      self.Esoil = scalar(0)
	      self.Etrans = scalar(0)
	      self.Epaddy = scalar(0)
	      self.Ewater = scalar(0)
	      self.Esnow = scalar(0)
	      self.actInfiltration = scalar(0)
	      self.gwRecharge = scalar(0)
	      self.interFlow = scalar(0)
	      self.directRunoff = scalar(0)
	      self.baseFlow = scalar(0)
	      self.surfaceWaterRunoff = scalar(0)
	      self.irrGrossDemand = scalar(0)
	      self.nonIrrGrossDemand = scalar(0)
	      self.totalGrossDemand = scalar(0)
	      self.nonFossilGroundWater = scalar(0)
	      self.otherWater = scalar(0)
	      self.abstrSurfaceWater = scalar(0)
	      self.riverBed = scalar(0)
	      self.nonIrrConsumption = scalar(0)
	      self.activeStorage = scalar(0)

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
              str(self.currentSampleNumber())+"/"+"su"+str(self.shortNames[idx])+".map")
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
          #report(self.model.routing.WaterBodies.avgInflow,str(self.currentSampleNumber())+"/"+"in"+".map")
          #report(self.model.routing.WaterBodies.avgOutflow,str(self.currentSampleNumber())+"/"+"out"+".map")
          #report(self.model.routing.WaterBodies.waterBodyStorage,str(self.currentSampleNumber())+"/"+"rs"+".map")
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

          report(self.model.routing.Q, str(self.currentSampleNumber())+"/"+"Q"+".map")
          report(self.Resistance, str(self.currentSampleNumber())+"/"+"Res"+".map")
          report(self.AvgSlope, str(self.currentSampleNumber())+"/"+"Slope"+".map")
          # Parameter report
          if "wmin" in self.calibrationPara:
	    report(self.minSoilDepthAdjust, str(self.currentSampleNumber())+"/wmin.map")
          if "wmax" in self.calibrationPara:
	    report(self.maxSoilDepthAdjust, str(self.currentSampleNumber())+"/wmax.map")
          if "ddf" in self.calibrationPara:
	    report(self.degreeDayAdjust, str(self.currentSampleNumber())+"/ddf.map")
          if "ksat" in self.calibrationPara:
	    report(self.KSatAdjust, str(self.currentSampleNumber())+"/ksat.map")
          if "theta50" in self.calibrationPara:
	    report(self.Theta50Adjust, str(self.currentSampleNumber())+"/theta50.map")
          if "j" in self.calibrationPara:
	    report(self.recessionAdjust, str(self.currentSampleNumber())+"/j.map")
          if "n" in self.calibrationPara:
	    report(self.routingAdjust, str(self.currentSampleNumber())+"/n.map")
          if "precBias" in self.calibrationPara:
	    report(self.precBiasAdjust, str(self.currentSampleNumber())+"/precBias.map")
          if "precConvec" in self.calibrationPara:
	    report(self.precConvectAdjust, str(self.currentSampleNumber())+"/precConvec.map")
          if "precWindWard" in self.calibrationPara:
	    report(self.precHeightAdjust1, str(self.currentSampleNumber())+"/precWindWard.map")
          if "precLeeWard" in self.calibrationPara:
	    report(self.precHeightAdjust2, str(self.currentSampleNumber())+"/precLeeWard.map")
          
          self.report(self.model.routing.discharge, "q")
          self.report(maptotal(self.Precacc), "orPrec")
          self.report(maptotal(self.PrecAdacc), "Prec")
          
    def setState(self):
        #~ values = np.zeros(5)
        #~ return values 
        timestep = self.currentTimeStep()
        #print str(timestep) + "State"

        prev_time = int(loadfile("time.obj", str(self.currentSampleNumber())))

        qmod = self.readmap("q_acc")

        # Principle (at this moment): If there is at least a observation, 
        #                             we get the model state. 

        # The following will be replaced by observation data:
        stats = self.ids                                     # station code
        #~ qobs  = self.readmap("q") + 0.1*self.readmap("q") # observation data
        year = int(self._configuration.globalOptions['startTime'][0:4])
        month = int(self._configuration.globalOptions['startTime'][5:7])
        day = int(self._configuration.globalOptions['startTime'][8:10])
        dif = datetime.date(year, month, day) - datetime.date(1900, 01, 01)
        obs = scalar(0)
        dayCur = int(loadfile("day.obj", str(self.currentSampleNumber())))

	print timestep+dif.days
	print generateNameT(str(self._configuration.globalOptions['observationDir'])+"update/Qobs", timestep+dif.days)        
	print self.currentSampleNumber() == 1
        
	if self.currentSampleNumber() == 1:
	  self.Qmean = 1
	  try:
	    self.qobs = vos.readPCRmapClone(generateNameT(str(self._configuration.globalOptions['observationDir'])+"update/Qobs", timestep+dif.days), self._configuration.cloneMap, ".")
	    self.MMlim = self.qobs/self.CatchTotal*scalar(31000)*scalar(86400)
	  except:
	    self.qobs = scalar(0)
	    self.MMlim = scalar(0)
	  try:
	    self.qsd = vos.readPCRmapClone(generateNameT(str(self._configuration.globalOptions['observationDir'])+"update/Qsd", timestep+dif.days), self._configuration.cloneMap, ".")
	    self.Qlim = self.qsd*self.qobs
	    print "Qlim succesfull"
	  except:
	    self.qsd = scalar(0)
	    self.Qlim = scalar(0)
	#report((qmod-self.qobs)/self.qobs, generateNameT(str(self.currentSampleNumber())+"/Rdif", time))
	#report(qmod-self.qobs, generateNameT(str(self.currentSampleNumber())+"/Adif", time))

  
        values = []
        Qtel = []
        if self.currentSampleNumber() == 1:
          errorGlobal = 0.0
          errorTel = 0
	  for s in range(len(self.Qxloc)):
	    val  = cellvalue(qmod, self.Qxloc[s],self.Qyloc[s])[0]
	    val2 = cellvalue(self.qobs, self.Qxloc[s],self.Qyloc[s])[0]
	    valQlim = cellvalue(self.Qlim, self.Qxloc[s],self.Qyloc[s])[0]
	    valSDlim = cellvalue(self.Qlim, self.Qxloc[s],self.Qyloc[s])[0]
	    #valMMlim = cellvalue(self.MMlim, self.Qxloc[s],self.Qyloc[s])[0]
            errorLocal = numpy.abs(val-val2)
	    if errorLocal < valQlim:
	      print str(val) + " " + str(val2)
              errorGlobal += errorLocal
              errorTel += 1
	      values.append(val)
	      Qtel.append(s)
	  if len(values) == 0:
	    values.append(numpy.random.normal(0,1,1)[0])
	    Qtel.append(-999)
	  dumpfile("Qtel.obj", Qtel, str(self.currentSampleNumber()))
          conPara = open(str(self.currentSampleNumber())+"/errorGlobal.txt", "a")
          conPara.writelines(str(timestep+1)+"\t"+str(errorGlobal/errorTel)+"\t"+str(errorTel)+"\n")
          conPara.close()
	else:
	  Qlist = loadfile("Qtel.obj", str(1))
	  if Qlist[-1] != -999:
	    for s in Qlist:
	      val  = cellvalue(qmod, self.Qxloc[s],self.Qyloc[s])[0]
	      values.append(val)
	      Qtel.append(s)  
	  else:
	    values.append(numpy.random.normal(0,1,1)[0])
            Qtel.append(-999)	    
        print len(Qtel)

        #print values
        xlocs2 = self.xlocs2 ## All locations with data
        ylocs2 = self.ylocs2 ## All locations with data
        endx = len(xlocs2)
        self.endx = endx
        #print endx

        x = xlocs2[0]
        y = ylocs2[0]
        
        if "wmin" in self.calibrationPara:
	  wmin = readmap(str(self.currentSampleNumber())+"/wmin.map")
	  values.append(numpy.log10(cellvalue(wmin, x, y)[0]))
        if "wmax" in self.calibrationPara:
	  wmax = readmap(str(self.currentSampleNumber())+"/wmax.map")
	  values.append(numpy.log10(cellvalue(wmax, x, y)[0]))
        if "ddf" in self.calibrationPara:
	  ddf = readmap(str(self.currentSampleNumber())+"/ddf.map")
	  values.append(numpy.log10(cellvalue(ddf, x, y)[0]))
        if "ksat" in self.calibrationPara:
	  ksat = readmap(str(self.currentSampleNumber())+"/ksat.map")
	  values.append(numpy.log10(cellvalue(ksat, x, y)[0]))
        if "theta50" in self.calibrationPara:
	  theta50 = readmap(str(self.currentSampleNumber())+"/theta50.map")
	  values.append(numpy.log10(cellvalue(theta50, x, y)[0]))
        if "j" in self.calibrationPara:
	  j = readmap(str(self.currentSampleNumber())+"/j.map")
	  values.append(numpy.log10(cellvalue(j, x, y)[0]))
        if "n" in self.calibrationPara:
	  n = readmap(str(self.currentSampleNumber())+"/n.map")
	  values.append(numpy.log10(cellvalue(n, x, y)[0]))
        if "precBias" in self.calibrationPara:
	  precBias = readmap(str(self.currentSampleNumber())+"/precBias.map")
	  values.append(cellvalue(precBias, x, y)[0])
        if "precConvec" in self.calibrationPara:
	  precConvec = readmap(str(self.currentSampleNumber())+"/precConvec.map")
	  values.append(cellvalue(precConvec, x, y)[0])
        if "precWindWard" in self.calibrationPara:
	  precWindWard = readmap(str(self.currentSampleNumber())+"/precWindWard.map")
	  values.append(cellvalue(precWindWard, x, y)[0])
        if "precLeeWard" in self.calibrationPara:
	  precLeeWard = readmap(str(self.currentSampleNumber())+"/precLeeWard.map")
	  values.append(cellvalue(precLeeWard, x, y)[0])
        
        values2 = numpy.array(values)
#        print values2

        dumpfile("x2.obj", xlocs2, str(self.currentSampleNumber()))
        dumpfile("y2.obj", ylocs2, str(self.currentSampleNumber()))
        return values2

    def setObservations(self):

        timestep = self.currentTimeStep()
        values = []
        obs = self.qobs
        SD = self.qsd
        SDmin = 400
        
        Qtel = loadfile("Qtel.obj", str(1))
        Qlen = len(Qtel)
        #print str(Qlen)
        covariance = numpy.eye(Qlen, Qlen, dtype=float)

        Qplace = 0
        for s in Qtel:
          if s != -999:
            val = cellvalue(obs, self.Qxloc[s],self.Qyloc[s])[0]
	    SDval = cellvalue(SD, self.Qxloc[s],self.Qyloc[s])[0]
	    values.append(numpy.maximum(val,1))
	    covariance[Qplace, Qplace] = numpy.maximum((SDval*val)**2, SDmin)
            Qplace += 1
          else:
            val = numpy.random.normal(0,1000,1)[0]
            values.append(val)
            covariance[Qplace, Qplace] = (1000)**2
            Qplace += 1
        #dumpfile("time.obj", timestep,"1")
        dumpfile("WriteTime.obj", int(loadfile("WriteTime.obj", "1"))+1, "1")
        values2 = numpy.array(values)
#        print values2
        observations = numpy.array([values2,]*self.nrSamples()).transpose()
        #for i in range(Qplace):
        #    observations[i,:] += numpy.random.normal(0,covariance[i,i]**0.5,self.nrSamples())
        #    observations[i,:]  = numpy.maximum(observations[i,:], 0.01)

        #month_end = loadfile("Monthend.obj", "1")
        #if month_end == 1:
          #print "End of month"
        print Qtel

        #self.giveLenghts(Qlen, self.endx)
        self.setObservedMatrices(observations, covariance)
        return values
        
        
    def resume(self):
        beta = 0.0
        pert = 0.01
        vec = self.getStateVector(self.currentSampleNumber())
        timestep = self.currentTimeStep()-1

        Qtel = loadfile("Qtel.obj", str(1))

        Qlen = len(Qtel)
        tel = Qlen

        ### Read parameter maps
        if "wmin" in self.calibrationPara:
 	  self.minSoilDepthAdjust = readmap(str(self.currentSampleNumber())+"/wmin.map")
	  self.minSoilDepthAdjust = min((beta * self.minSoilDepthAdjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/wmin.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.minSoilDepthAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.minSoilDepthAdjust = scalar(1)
	if "wmax" in self.calibrationPara:
	  self.maxSoilDepthAdjust = readmap(str(self.currentSampleNumber())+"/wmax.map")
	  self.maxSoilDepthAdjust = min((beta * self.maxSoilDepthAdjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/wmax.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(maxSoilDepthAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.maxSoilDepthAdjust = scalar(1)
        if "ddf" in self.calibrationPara:
	  self.degreeDayAdjust = readmap(str(self.currentSampleNumber())+"/ddf.map")
	  self.degreeDayAdjust = min((beta * self.degreeDayAdjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/ddf.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.degreeDayAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.degreeDayAdjust = scalar(1)
        if "ksat" in self.calibrationPara:
	  self.KSatAdjust = readmap(str(self.currentSampleNumber())+"/ksat.map")
	  self.KSatAdjust = min((beta * self.KSatAdjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/ksat.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.KSatAdjust, 1, 1)[0])+"\n")
	  conPara.close()	  
	  tel += 1
	else:
	  self.KSatAdjust = scalar(1)
        if "theta50" in self.calibrationPara:
	  self.Theta50Adjust = readmap(str(self.currentSampleNumber())+"/theta50.map")
	  self.Theta50Adjust = min((beta * self.Theta50Adjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/theta50.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.Theta50Adjust, 1, 1)[0])+"\n")
	  conPara.close()	  
	  tel += 1
	else:
	  self.Theta50Adjust = scalar(1)
        if "j" in self.calibrationPara:
	  self.recessionAdjust = readmap(str(self.currentSampleNumber())+"/j.map")
	  self.recessionAdjust = min((beta * self.recessionAdjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/j.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.recessionAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.recessionAdjust = scalar(1)
        if "n" in self.calibrationPara:
	  self.routingAdjust = readmap(str(self.currentSampleNumber())+"/n.map")
	  self.routingAdjust = min((beta * self.routingAdjust + (1- beta)* scalar(10**vec[tel])) * (1+ mapnormal() * pert),mapnormal()+10.0)
	  conPara = open(str(self.currentSampleNumber())+"/n.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.routingAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.routingAdjust = scalar(1)
        if "precBias" in self.calibrationPara:
	  self.precBiasAdjust = readmap(str(self.currentSampleNumber())+"/precBias.map")
	  self.precBiasAdjust = max(min((beta * self.precBiasAdjust + (1- beta)* scalar(vec[tel])) * (1+ mapnormal() * pert),mapnormal()*0.1+1.0),mapnormal()*0.1-1.0)
	  conPara = open(str(self.currentSampleNumber())+"/precBias.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.precBiasAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.precBiasAdjust = scalar(0)
        if "precConvec" in self.calibrationPara:
	  self.precConvectAdjust = readmap(str(self.currentSampleNumber())+"/precConvec.map")
	  self.precConvectAdjust = max(min((beta * self.precConvectAdjust + (1- beta)* scalar(vec[tel])) * (1+ mapnormal() * pert),mapnormal()*0.5+5.0),mapnormal()*0.5-5.0)
	  conPara = open(str(self.currentSampleNumber())+"/precConvec.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.precConvectAdjust, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.precConvectAdjust = scalar(0)
        if "precWindWard" in self.calibrationPara:
	  self.precHeightAdjust1 = readmap(str(self.currentSampleNumber())+"/precWindWard.map")
	  self.precHeightAdjust1 = max(min((beta * self.precHeightAdjust1 + (1- beta)* scalar(vec[tel])) * (1+ mapnormal() * pert),mapnormal()*0.5+5.0),mapnormal()*0.5-5.0)
	  conPara = open(str(self.currentSampleNumber())+"/precWindWard.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.precHeightAdjust1, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.precHeightAdjust1 = scalar(0)
        if "precLeeWard" in self.calibrationPara:
	  self.precHeightAdjust2 = readmap(str(self.currentSampleNumber())+"/precLeeWard.map")
	  self.precHeightAdjust2 = max(min((beta * self.precHeightAdjust2 + (1- beta)* scalar(vec[tel])) * (1+ mapnormal() * pert),mapnormal()*0.5+5.0),mapnormal()*0.5-5.0)
	  conPara = open(str(self.currentSampleNumber())+"/precLeeWard.txt", "a")
	  conPara.writelines(str(timestep+1)+"\t"+str(cellvalue(self.precHeightAdjust2, 1, 1)[0])+"\n")
	  conPara.close()
	  tel += 1
	else:
	  self.precHeightAdjust2 = scalar(0)

        # Perturb maps
        for coverType in self.model.landSurface.coverTypes:
          self.model.landSurface.landCoverObj[coverType].minSoilDepthFrac = min(self.minSoilDepthOrig[coverType] * self.minSoilDepthAdjust,0.9999)
          self.model.landSurface.landCoverObj[coverType].maxSoilDepthFrac = max(self.maxSoilDepthOrig[coverType]* self.maxSoilDepthAdjust,1.0001)
          self.model.landSurface.landCoverObj[coverType].degreeDayFactor = self.degreeDayOrig[coverType] * self.degreeDayAdjust
        self.model.landSurface.parameters.kSatUpp = self.KSat1Orig * self.KSatAdjust
        self.model.landSurface.parameters.kSatLow = self.KSat2Orig * self.KSatAdjust
        self.model.landSurface.parameters.effSatAt50Upp = self.THEFF1_50org * self.Theta50Adjust
        self.model.landSurface.parameters.effSatAt50Low = self.THEFF2_50org * self.Theta50Adjust
        self.model.groundwater.recessionCoeff = self.recessionOrig * self.recessionAdjust
        self.model.routing.manningsN = self.routingOrig * self.routingAdjust

        self.model.routing.discharge = self.readmap("q")
        self.Qaccu = self.readmap("q_acc")

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
              cover(readmap(str(self.currentSampleNumber())+"/"+"su"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].storLow =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"sl"+str(self.shortNames[idx])+".map"), 0.0)
            self.model.landSurface.landCoverObj[coverType].interflow =\
              cover(readmap(str(self.currentSampleNumber())+"/"+"qi"+str(self.shortNames[idx])+".map"), 0.0)
            idx = idx + 1
        self.model.groundwater.storGroundwater = readmap(str(self.currentSampleNumber())+"/"+"sg"+".map")
        self.model.routing.channelStorage = readmap(str(self.currentSampleNumber())+"/"+"Qc"+".map")
        self.model.routing.avgDischarge = readmap(str(self.currentSampleNumber())+"/"+"Qa"+".map")
        self.model.routing.Q = readmap(str(self.currentSampleNumber())+"/"+"Q"+".map")
        self.Resistance = readmap(str(self.currentSampleNumber())+"/"+"Res"+".map")
        self.AvgSlope = readmap(str(self.currentSampleNumber())+"/"+"Slope"+".map")

        self.model.routing.timestepsToAvgDischarge = readmap(str(self.currentSampleNumber())+"/"+"t"+".map")
        self.model.routing.readAvlChannelStorage = readmap(str(self.currentSampleNumber())+"/"+"racs"+".map")
        self.model.routing.m2tDischarge = readmap(str(self.currentSampleNumber())+"/"+"mtd"+".map")
        self.model.routing.avgBaseflow = readmap(str(self.currentSampleNumber())+"/"+"abf"+".map")
        self.model.routing.riverbedExchange = readmap(str(self.currentSampleNumber())+"/"+"rbe"+".map")
        
        #self.model.routing.WaterBodies.waterBodyStorage = readmap(str(self.currentSampleNumber())+"/"+"rs"+".map")
        #self.model.routing.WaterBodies.avgInflow = readmap(str(self.currentSampleNumber())+"/"+"in"+".map")
        #self.model.routing.WaterBodies.avgOutflow = readmap(str(self.currentSampleNumber())+"/"+"out"+".map")

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
          ### WaterDemand
        except:
          foo = 0
        try:
          self.model.landSurface.domesticGrossDemand = readmap(str(self.currentSampleNumber())+"/"+"dgd"+".map")
          self.model.landSurface.domesticNettoDemand = readmap(str(self.currentSampleNumber())+"/"+"dnd"+".map")
          self.model.landSurface.industryGrossDemand = readmap(str(self.currentSampleNumber())+"/"+"igd"+".map")
          self.model.landSurface.industryNettoDemand = readmap(str(self.currentSampleNumber())+"/"+"ind"+".map")
        except:
          foo = 0

        #month_end = loadfile("Monthend.obj", "1")

	self.Qaccu = scalar(0)

        #self.groundwater.recessionCoeff = readmap(str(self.currentSampleNumber())+"/GrAlpha.map")
        

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

