#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from pcraster.framework import *
import pcraster as pcr

import virtualOS as vos
from ncConverter import *
import ETPFunctions as refPotET

class Meteo(object):

    def __init__(self,iniItems,landmask,spinUp):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions['inputDir']
        
        # landmask/area of interest
        self.landmask = landmask
        if iniItems.globalOptions['landmask'] != "None":
           self.landmask = vos.readPCRmapClone(\
           iniItems.globalOptions['landmask'],
           self.cloneMap,self.tmpDir,self.inputDir)	

        self.preFileNC = iniItems.meteoOptions['precipitationNC']        # starting from 19 Feb 2014, we only support netcdf input files
        self.tmpFileNC = iniItems.meteoOptions['temperatureNC']

        self.refETPotMethod = iniItems.meteoOptions['referenceETPotMethod']
        if self.refETPotMethod == 'Hamon': self.latitudes = \
                                           pcr.ycoordinate(self.cloneMap) # needed to calculate 'referenceETPot'
        if self.refETPotMethod == 'Input': self.etpFileNC = \
                             iniItems.meteoOptions['refETPotFileNC']              

        # forcing downscaling options:
        self.forcingDownscalingOptions(iniItems)

        self.report = True
        if self.report == True:
            # daily output in netCDF files:
            self.outNCDir  = iniItems.outNCDir
            self.netcdfObj = PCR2netCDF(iniItems)
            #
            self.outDailyTotNC = iniItems.meteoOptions['outDailyTotNC'].split(",")
            if self.outDailyTotNC[0] != "None":
                for var in self.outDailyTotNC:
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_dailyTot.nc",\
                                                    var,"undefined")
            # MONTHly output in netCDF files:
            # - cummulative
            self.outMonthTotNC = iniItems.meteoOptions['outMonthTotNC'].split(",")
            if self.outMonthTotNC[0] != "None":
                for var in self.outMonthTotNC:
                    # initiating monthlyVarTot (accumulator variable):
                    vars(self)[var+'MonthTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthTot.nc",\
                                                    var,"undefined")
            # - average
            self.outMonthAvgNC = iniItems.meteoOptions['outMonthAvgNC'].split(",")
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
            self.outMonthEndNC = iniItems.meteoOptions['outMonthEndNC'].split(",")
            if self.outMonthEndNC[0] != "None":
                for var in self.outMonthEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_monthEnd.nc",\
                                                    var,"undefined")
            # YEARly output in netCDF files:
            # - cummulative
            self.outAnnuaTotNC = iniItems.meteoOptions['outAnnuaTotNC'].split(",")
            if self.outAnnuaTotNC[0] != "None":
                for var in self.outAnnuaTotNC:
                    # initiating yearly accumulator variable:
                    vars(self)[var+'AnnuaTot'] = None
                    # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaTot.nc",\
                                                    var,"undefined")
            # - average
            self.outAnnuaAvgNC = iniItems.meteoOptions['outAnnuaAvgNC'].split(",")
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
            self.outAnnuaEndNC = iniItems.meteoOptions['outAnnuaEndNC'].split(",")
            if self.outAnnuaEndNC[0] != "None":
                for var in self.outAnnuaEndNC:
                     # creating the netCDF files:
                    self.netcdfObj.createNetCDF(str(self.outNCDir)+"/"+ \
                                                str(var)+"_annuaEnd.nc",\
                                                    var,"undefined")


    def forcingDownscalingOptions(self, iniItems):

        self.downscalePrecipitationOption  = False
        self.downscaleTemperatureOption    = False
        self.downscaleReferenceETPotOption = False
        try:
            # creating anomaly DEM
            highResolutionDEM = vos.readPCRmapClone(\
               iniItems.meteoDownscalingOptions['highResolutionDEM'],
               self.cloneMap,self.tmpDir,self.inputDir)
            highResolutionDEM = pcr.cover(highResolutionDEM, 0.0)
            highResolutionDEM = pcr.max(highResolutionDEM, 0.0)
            self.meteoDownscaleIds = vos.readPCRmapClone(\
               iniItems.meteoDownscalingOptions['meteoDownscaleIds'],
               self.cloneMap,self.tmpDir,self.inputDir,isLddMap=False,cover=None,isNomMap=True)
            self.cellArea = vos.readPCRmapClone(\
               iniItems.routingOptions['cellAreaMap'],
               self.cloneMap,self.tmpDir,self.inputDir)
            loweResolutionDEM = pcr.areatotal(pcr.cover(highResolutionDEM*self.cellArea, 0.0),\
                                              self.meteoDownscaleIds)/\
                                pcr.areatotal(pcr.cover(self.cellArea, 0.0),\
                                              self.meteoDownscaleIds)                  
            self.anomalyDEM = highResolutionDEM - loweResolutionDEM    # unit: meter  

            # temperature lapse rate (netCDF) file 
            self.temperLapseRateNC = vos.getFullPath(iniItems.meteoDownscalingOptions[\
                                        'temperLapseRateNC'],self.inputDir)                         
            self.temperatCorrelNC  = vos.getFullPath(iniItems.meteoDownscalingOptions[\
                                        'temperatCorrelNC'],self.inputDir)                    # TODO: Remove this criteria.                         

            # precipitation lapse rate (netCDF) file 
            self.precipLapseRateNC = vos.getFullPath(iniItems.meteoDownscalingOptions[\
                                        'precipLapseRateNC'],self.inputDir)
            self.precipitCorrelNC  = vos.getFullPath(iniItems.meteoDownscalingOptions[\
                                        'precipitCorrelNC'],self.inputDir)                    # TODO: Remove this criteria.                           

            # downscaling options
            if iniItems.meteoDownscalingOptions['downscalePrecipitation']  == "True":\
                                            self.downscalePrecipitationOption  = True  
            if iniItems.meteoDownscalingOptions['downscaleTemperature']    == "True":\
                                            self.downscaleTemperatureOption    = True  
            if iniItems.meteoDownscalingOptions['downscaleReferenceETPot'] == "True":\
                                            self.downscaleReferenceETPotOption = True 

            # for Hamon method: referencePotET will be calculated based on temperature
            if self.refETPotMethod == 'Hamon':\
                                            self.downscaleReferenceETPotOption = False 

        except:
            print("No forcing downscaling is implemented.")


        # forcing smoothing options:                                    # PS: MUST BE TESTED.
        self.forcingSmoothing = False
        try:
            if iniItems.meteoDownscalingOptions['smoothingWindowsLength'] != "0":
                self.forcingSmoothing = True
                self.smoothingWindowsLength = vos.readPCRmapClone(\
                   iniItems.meteoDownscalingOptions['smoothingWindowsLength'],
                   self.cloneMap,self.tmpDir,self.inputDir)
                print("Warning!!! Forcing data are smoothed.")   
        except:
            pass
 
    def perturb(self, name, **parameters):

        if name == "precipitation":

            # perturb the precipitation
            self.precipitation = self.precipitation * \
            pcr.min(pcr.max((1 + mapnormal() * parameters['standard_deviation']),0.01),2.0)
            #TODO: Please also make sure that precipitation >= 0
            #TODO: Add minimum and maximum 

        else:
            print("Error: only precipitation may be updated at this time")
            return -1


    def update(self,currTimeStep):
        #TODO: calculate  referencePotET
        pass

    def downscalePrecipitation(self, currTimeStep, useFactor = True, minCorrelationCriteria = 0.75):
        
        preSlope = 0.001 * vos.netcdf2PCRobjClone(\
                           self.precipLapseRateNC,'precipitation',\
                           currTimeStep.month, useDoy = "Yes",\
                           cloneMapFileName=self.cloneMap,\
                           LatitudeLongitude = True)
        preSlope = pcr.cover(preSlope, 0.0)
        preSlope = pcr.max(0.,preSlope)
        
        preCriteria = vos.netcdf2PCRobjClone(\
                     self.precipitCorrelNC,'precipitation',\
                     currTimeStep.month, useDoy = "Yes",\
                     cloneMapFileName=self.cloneMap,\
                     LatitudeLongitude = True)
        preSlope = pcr.ifthenelse(preCriteria > minCorrelationCriteria,\
                   preSlope, 0.0)             
        preSlope = pcr.cover(preSlope, 0.0)
    
        if useFactor == True:
            factor = pcr.max(0.,self.precipitation + preSlope*self.anomalyDEM)
            factor = factor / \
                     pcr.areaaverage(factor, self.meteoDownscaleIds)
            factor = pcr.cover(factor, 1.0)
            self.precipitation = factor * self.precipitation
        else:
            self.precipitation = self.precipitation + preSlope*self.anomalyDEM

        self.precipitation = pcr.max(0.0, self.precipitation)

    def downscaleTemperature(self, currTimeStep, useFactor = False, maxCorrelationCriteria = -0.50, zeroCelciusInKelvin = 273.15):
        
        tmpSlope = 1.000 * vos.netcdf2PCRobjClone(\
                           self.temperLapseRateNC,'temperature',\
                           currTimeStep.month, useDoy = "Yes",\
                           cloneMapFileName=self.cloneMap,\
                           LatitudeLongitude = True)
        tmpSlope = pcr.min(0.,tmpSlope)  # must be negative
        tmpCriteria = vos.netcdf2PCRobjClone(\
                      self.temperatCorrelNC,'temperature',\
                      currTimeStep.month, useDoy = "Yes",\
                      cloneMapFileName=self.cloneMap,\
                      LatitudeLongitude = True)
        tmpSlope = pcr.ifthenelse(tmpCriteria < maxCorrelationCriteria,\
                   tmpSlope, 0.0)             
        tmpSlope = pcr.cover(tmpSlope, 0.0)
    
        if useFactor == True:
            temperatureInKelvin = self.temperature + zeroCelciusInKelvin
            factor = pcr.max(0.0, temperatureInKelvin + tmpSlope * self.anomalyDEM)
            factor = factor / \
                     pcr.areaaverage(factor, self.meteoDownscaleIds)
            factor = pcr.cover(factor, 1.0)
            self.temperature = factor * temperatureInKelvin - zeroCelciusInKelvin
        else:
            self.temperature = self.temperature + tmpSlope*self.anomalyDEM

    def downscaleReferenceETPot(self, zeroCelciusInKelvin = 273.15):
        
        temperatureInKelvin = self.temperature + zeroCelciusInKelvin
        factor = pcr.max(0.0, temperatureInKelvin)
        factor = factor / \
                 pcr.areaaverage(factor, self.meteoDownscaleIds)
        factor = pcr.cover(factor, 1.0)
        self.referencePotET = pcr.max(0.0, factor * self.referencePotET)

    def read_forcings(self,currTimeStep):
        # reading precipitation:
        self.precipitation = vos.netcdf2PCRobjClone(\
                                  self.preFileNC,'precipitation',\
                                  str(currTimeStep.fulldate), 
                                  useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)

        precipitationCorrectionFactor = pcr.scalar(1.0)                 # Since 19 Feb 2014, Edwin removed the support for correcting precipitation. 
        self.precipitation = pcr.max(0.,self.precipitation*\
                precipitationCorrectionFactor)
        self.precipitation = pcr.cover( self.precipitation, 0.0)

        # reading temperature
        self.temperature = vos.netcdf2PCRobjClone(\
                                 self.tmpFileNC,'temperature',\
                                 str(currTimeStep.fulldate), 
                                 useDoy = None,
                                  cloneMapFileName=self.cloneMap,\
                                  LatitudeLongitude = True)

        # Downscaling precipitation and temperature
        if self.downscalePrecipitationOption: self.downscalePrecipitation(currTimeStep)
        if self.downscaleTemperatureOption: self.downscaleTemperature(currTimeStep)

        # calculate or obtain referencePotET
        if self.refETPotMethod == 'Hamon': self.referencePotET = \
                                  refPotET.HamonPotET(self.temperature,\
                                                      currTimeStep.doy,\
                                                      self.latitudes)
        if self.refETPotMethod == 'Input': 
            self.referencePotET = vos.netcdf2PCRobjClone(\
                                     self.etpFileNC,'evapotranspiration',\
                                     str(currTimeStep.fulldate), 
                                     useDoy = None,
                                      cloneMapFileName=self.cloneMap,\
                                      LatitudeLongitude = True)

        # Downscaling referenceETPot (based on temperature)
        if self.downscaleReferenceETPotOption: self.downscaleReferenceETPot()
        
        # smoothing:
        if self.forcingSmoothing == True:
            print("Forcing data are smoothed.")   
            self.precipitation  = pcr.windowaverage(self.precipitation , self.smoothingWindowsLength)
            self.temperature    = pcr.windowaverage(self.temperature   , self.smoothingWindowsLength)
            self.referencePotET = pcr.windowaverage(self.referencePotET, self.smoothingWindowsLength)
        
        # define precipitation, temperature and referencePotET ONLY at landmask area (for reporting):
        self.precipitation  = pcr.ifthen(self.landmask, self.precipitation)
        self.temperature    = pcr.ifthen(self.landmask, self.temperature)
        self.referencePotET = pcr.ifthen(self.landmask, self.referencePotET)
 
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

