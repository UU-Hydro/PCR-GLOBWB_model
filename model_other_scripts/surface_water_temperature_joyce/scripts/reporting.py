'''
Takes care of reporting (writing) output to netcdf files. Aggregates totals and averages for various time periods.
@author: Edwin H. Sutanudjaja

Created on Jul 28, 2014. 
This "reporting.py" module is not the same as the one module initiated by Niels Drost.
'''

import os

import logging
logger = logging.getLogger(__name__)

import pcraster as pcr

from ncConverter import *

import variable_list as varDicts

class Reporting(object):

    #list of all output variables
    
    def __init__(self, configuration, model, modelTime):

        self._model = model
        self._modelTime = modelTime

        # output directory storing netcdf files:
        self.outNCDir  = str(configuration.outNCDir)

        # object for reporting:
        self.netcdfObj = PCR2netCDF(configuration)

        # initiating netcdf files for reporting
        #
        # - daily output in netCDF files:
        self.outDailyTotNC = ["None"]
        try:
            self.outDailyTotNC = configuration.reportingOptions['outDailyTotNC'].split(",")
        except:
            pass
        #
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                
                logger.info("Creating the netcdf file for daily reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_dailyTot_output.nc",\
                                            short_name,unit,long_name)

        # - WEEKly output in netCDF files:
        # -- cummulative
        self.outWeekTotNC = ["None"]
        try:
            self.outWeekTotNC = configuration.reportingOptions['outWeekTotNC'].split(",")
        except:
            pass
        if self.outWeekTotNC[0] != "None":
            for var in self.outWeekTotNC:

                # initiating WeekVarTot (accumulator variable):
                vars(self)[var+'WeekTot'] = None

                logger.info("Creating the netcdf file for weekly accumulation reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_monthly_total_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_weekTot_output.nc",\
                                            short_name,unit,long_name)
        #
        # -- average
        self.outWeekAvgNC = ["None"]
        try:
            self.outWeekAvgNC = configuration.reportingOptions['outWeekAvgNC'].split(",")
        except:
            pass
        if self.outWeekAvgNC[0] != "None":

            for var in self.outWeekAvgNC:

                # initiating WeekTotAvg (accumulator variable)
                vars(self)[var+'WeekTot'] = None

                # initiating WeekVarAvg:
                vars(self)[var+'WeekAvg'] = None

                logger.info("Creating the netcdf file for weekly average reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_weekAvg_output.nc",\
                                            short_name,unit,long_name)
        #
        # -- last day of the week
        self.outWeekEndNC = ["None"]
        try:
            self.outWeekEndNC = configuration.reportingOptions['outWeekEndNC'].split(",")
        except:
            pass
        if self.outWeekEndNC[0] != "None":

            for var in self.outWeekEndNC:

                logger.info("Creating the netcdf file for weekly end reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_weekEnd_output.nc",\
                                            short_name,unit,long_name)

        #
        # - MONTHly output in netCDF files:
        # -- cummulative
        self.outMonthTotNC = ["None"]
        try:
            self.outMonthTotNC = configuration.reportingOptions['outMonthTotNC'].split(",")
        except:
            pass
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:

                # initiating monthlyVarTot (accumulator variable):
                vars(self)[var+'MonthTot'] = None

                logger.info("Creating the netcdf file for monthly accumulation reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_monthly_total_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthTot_output.nc",\
                                            short_name,unit,long_name)
        #
        # -- average
        self.outMonthAvgNC = ["None"]
        try:
            self.outMonthAvgNC = configuration.reportingOptions['outMonthAvgNC'].split(",")
        except:
            pass
        if self.outMonthAvgNC[0] != "None":

            for var in self.outMonthAvgNC:

                # initiating monthlyTotAvg (accumulator variable)
                vars(self)[var+'MonthTot'] = None

                # initiating monthlyVarAvg:
                vars(self)[var+'MonthAvg'] = None

                logger.info("Creating the netcdf file for monthly average reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthAvg_output.nc",\
                                            short_name,unit,long_name)
        #
        # -- last day of the month
        self.outMonthEndNC = ["None"]
        try:
            self.outMonthEndNC = configuration.reportingOptions['outMonthEndNC'].split(",")
        except:
            pass
        if self.outMonthEndNC[0] != "None":

            for var in self.outMonthEndNC:

                logger.info("Creating the netcdf file for monthly end reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthEnd_output.nc",\
                                            short_name,unit,long_name)

        # -- maximum of the month
        self.outMonthMaxNC = ["None"]
        try:
            self.outMonthMaxNC = configuration.reportingOptions['outMonthMaxNC'].split(",")
        except:
            pass
        if self.outMonthMaxNC[0] != "None":

            for var in self.outMonthMaxNC:

                logger.info("Creating the netcdf file for monthly maximum reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthMax_output.nc",\
                                            short_name,unit,long_name)
        #
        # - YEARly output in netCDF files:
        # -- cummulative
        self.outAnnuaTotNC = ["None"]
        try:
            self.outAnnuaTotNC = configuration.reportingOptions['outAnnuaTotNC'].split(",")
        except:
            pass
        if self.outAnnuaTotNC[0] != "None":

            for var in self.outAnnuaTotNC:

                # initiating yearly accumulator variable:
                vars(self)[var+'AnnuaTot'] = None

                logger.info("Creating the netcdf file for annual accumulation reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_yearly_total_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaTot_output.nc",\
                                            short_name,unit,long_name)
        #
        # -- average
        self.outAnnuaAvgNC = ["None"]
        try:
            self.outAnnuaAvgNC = configuration.reportingOptions['outAnnuaAvgNC'].split(",")
        except:
            pass
        if self.outAnnuaAvgNC[0] != "None":

            for var in self.outAnnuaAvgNC:

                # initiating annualyVarAvg:
                vars(self)[var+'AnnuaAvg'] = None

                # initiating annualyTotAvg (accumulator variable)
                vars(self)[var+'AnnuaTot'] = None

                logger.info("Creating the netcdf file for annual average reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaAvg_output.nc",\
                                            short_name,unit,long_name)
        #
        # -- last day of the year
        self.outAnnuaEndNC = ["None"]
        try:
            self.outAnnuaEndNC = configuration.reportingOptions['outAnnuaEndNC'].split(",")
        except:
            pass
        if self.outAnnuaEndNC[0] != "None":

            for var in self.outAnnuaEndNC:

                logger.info("Creating the netcdf file for annual end reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name  

                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaEnd_output.nc",\
                                            short_name,unit,long_name)
        
        # list of variables that will be reported:
        self.variables_for_report = self.outDailyTotNC +\
                                    self.outWeekTotNC +\
                                    self.outWeekAvgNC +\
                                    self.outWeekEndNC +\
                                    self.outMonthTotNC +\
                                    self.outMonthAvgNC +\
                                    self.outMonthEndNC +\
                                    self.outMonthMaxNC +\
                                    self.outAnnuaTotNC +\
                                    self.outAnnuaAvgNC +\
                                    self.outAnnuaEndNC

    def post_processing(self):

        self.basic_post_processing() 
        self.additional_post_processing() 

    def basic_post_processing(self):

        self.precipitation  = self._model.meteo.precipitation 
        self.temperature    = self._model.meteo.temperature
        self.referencePotET = self._model.meteo.referencePotET 

        self.totalLandSurfacePotET = self._model.landSurface.totalPotET 
        self.totLandSurfaceActuaET = self._model.landSurface.actualET
        
        self.fractionLandSurfaceET = vos.getValDivZero(self.totLandSurfaceActuaET,\
                                                       self.totalLandSurfacePotET,\
                                                       vos.smallNumber)
        
        self.interceptStor = self._model.landSurface.interceptStor

        self.snowCoverSWE  = self._model.landSurface.snowCoverSWE
        self.snowFreeWater = self._model.landSurface.snowFreeWater

        self.topWaterLayer = self._model.landSurface.topWaterLayer
        self.storUppTotal  = self._model.landSurface.storUppTotal
        self.storLowTotal  = self._model.landSurface.storLowTotal
        
        self.interceptEvap        = self._model.landSurface.interceptEvap
        self.actSnowFreeWaterEvap = self._model.landSurface.actSnowFreeWaterEvap
        self.topWaterLayerEvap    = self._model.landSurface.openWaterEvap
        self.actBareSoilEvap      = self._model.landSurface.actBareSoilEvap
        
        self.actTranspiTotal      = self._model.landSurface.actTranspiTotal
        self.actTranspiUppTotal   = self._model.landSurface.actTranspiUppTotal
        self.actTranspiLowTotal   = self._model.landSurface.actTranspiLowTotal
                                  
        self.directRunoff         = self._model.landSurface.directRunoff
        self.interflowTotal       = self._model.landSurface.interflowTotal
        
        self.infiltration         = self._model.landSurface.infiltration
        self.gwRecharge           = self._model.landSurface.gwRecharge
        self.gwNetCapRise         = pcr.ifthen(self._model.landSurface.gwRecharge < 0.0, self.gwRecharge*(-1.0))
        
        self.irrGrossDemand       = self._model.landSurface.irrGrossDemand    
        self.nonIrrGrossDemand    = self._model.landSurface.nonIrrGrossDemand
        self.totalGrossDemand     = self._model.landSurface.totalPotentialGrossDemand
        
        self.satDegUpp            = self._model.landSurface.satDegUppTotal
        self.satDegLow            = self._model.landSurface.satDegLowTotal
        
        self.storGroundwater      = self._model.groundwater.storGroundwater
        
        self.baseflow             = self._model.groundwater.baseflow

        self.surfaceWaterAbstraction         = self._model.landSurface.actSurfaceWaterAbstract
        self.nonFossilGroundWaterAbstraction = self._model.groundwater.nonFossilGroundwaterAbs
        #self.fossilGroundWaterAbstraction    = self._model.groundwater.fossilGroundwaterAbstr
        self.otherWaterSourceAbstraction     = self._model.groundwater.unmetDemand
        self.totalAbstraction                = self.surfaceWaterAbstraction +\
                                               self.nonFossilGroundWaterAbstraction +\
                                               self.otherWaterSourceAbstraction
        
        # water body evaporation (m) - from surface water fractions only
        self.waterBodyActEvaporation = self._model.routing.waterBodyEvaporation
        self.waterBodyPotEvaporation = self._model.routing.waterBodyPotEvap
        #
        self.fractionWaterBodyEvaporation = vos.getValDivZero(self.waterBodyActEvaporation,\
                                                              self.waterBodyPotEvaporation,\
                                                              vos.smallNumber)
        # total evaporation (m), from land and water fractions
        self.totalEvaporation = self._model.landSurface.actualET + \
                                self._model.routing.waterBodyEvaporation
            #
        self.fractionTotalEvaporation = vos.getValDivZero(self.totalEvaporation,\
                                        self._model.landSurface.totalPotET + self._model.routing.waterBodyPotEvap,\
vos.smallNumber)
        
        # runoff (m) from land surface - not including local changes in water bodies
        self.runoff = self._model.routing.runoff
        
        # discharge (unit: m3/s)
        self.discharge = self._model.routing.disChanWaterBody
        self.dynamicFracWat = self._model.routing.dynamicFracWat
        self.channelFraction = self._model.routing.channelFraction

        # water temperature (K)
        try:
          self.waterTemp = self._model.routing.waterTemp
        except:
          self.waterTemp = pcr.scalar(273)

        # water height (K)
        try:
          self.waterHeight = self._model.routing.water_height
        except:
          self.waterHeight = pcr.scalar(0.0)
       
        # ice thickness (K)
        try:
          self.iceThickness = self._model.routing.iceThickness
        except:
          self.iceThickness = pcr.scalar(0.0)
        
    def additional_post_processing(self):
        # In this method/function, users can add their own post-processing.
               
        # accumulated runoff (m3/s) along the drainage network - not including local changes in water bodies
        if "accuRunoff" in self.variables_for_report:
            self.accuRunoff = pcr.catchmenttotal(self.runoff * self._model.routing.cellArea, self._model.routing.lddMap) / vos.secondsPerDay()
        
        # accumulated baseflow (m3) along the drainage network
        if "accuBaseflow" in self.variables_for_report:
            self.accuBaseflow = pcr.catchmenttotal(self.baseflow * self._model.routing.cellArea, self._model.routing.lddMap)

        # local changes in water bodies (i.e. abstraction, return flow, evaporation, bed exchange), excluding runoff
        self.local_water_body_flux = self._model.routing.local_input_to_surface_water / self._model.routing.cellArea - self.runoff
        
        # total runoff (m) from local land surface runoff and local changes in water bodies 
        self.totalRunoff = self.runoff + self.local_water_body_flux     # actually this is equal to self._model.routing.local_input_to_surface_water / self._model.routing.cellArea
        
        # accumulated total runoff (m3) along the drainage network - not including local changes in water bodies
        if "accuTotalRunoff" in self.variables_for_report:
            self.accuTotalRunoff = pcr.catchmenttotal(self.totalRunoff * self._model.routing.cellArea, self._model.routing.lddMap) / vos.secondsPerDay()

        # fossil groundwater storage
        self.storGroundwaterFossil = self._model.groundwater.storGroundwaterFossil
        
        # total groundwater storage: (non fossil and fossil)
        self.storGroundwaterTotal  = self._model.groundwater.storGroundwater + \
                                     self._model.groundwater.storGroundwaterFossil
        
        # total active storage thickness (m) for the entire water column - not including fossil groundwater (unmetDemand) 
        # - including: interception, snow, soil and non fossil groundwater 
        self.totalActiveStorageThickness = pcr.ifthen(\
                                           self._model.routing.landmask, \
                                           self._model.routing.channelStorage / self._model.routing.cellArea + \
                                           self._model.landSurface.totalSto + \
                                           self._model.groundwater.storGroundwater)

        # total water storage thickness (m) for the entire water column: 
        # - including: interception, snow, soil, non fossil groundwater and fossil groundwater (unmetDemand)
        # - this is usually used for GRACE comparison  
        self.totalWaterStorageThickness  = self.totalActiveStorageThickness + \
                                           self._model.groundwater.storGroundwaterFossil

        # surfaceWaterStorage (unit: m) - negative values may be reported
        self.surfaceWaterStorage = self._model.routing.channelStorage / self._model.routing.cellArea

        # Menno's post proccessing: fractions of water sources (allocated for) satisfying water demand in each cell
        self.fracSurfaceWaterAllocation = pcr.ifthen(self._model.routing.landmask, \
                                          vos.getValDivZero(\
                                          self._model.landSurface.allocSurfaceWaterAbstract, self.totalGrossDemand, vos.smallNumber))
        self.fracSurfaceWaterAllocation = pcr.ifthenelse(self.totalGrossDemand < vos.smallNumber, 1.0, self.fracSurfaceWaterAllocation)
        #
        self.fracNonFossilGroundwaterAllocation = pcr.ifthen(self._model.routing.landmask, \
                                                  vos.getValDivZero(\
                                                  self._model.groundwater.allocNonFossilGroundwater, self.totalGrossDemand, vos.smallNumber))
        self.fracNonFossilGroundwaterAllocation = pcr.ifthenelse(self.totalGrossDemand < vos.smallNumber, 0.0, self.fracNonFossilGroundwaterAllocation)
        #
        self.fracOtherWaterSourceAllocation = pcr.ifthen(self._model.routing.landmask, \
                                              vos.getValDivZero(\
                                              self._model.groundwater.unmetDemand, self.totalGrossDemand, vos.smallNumber))
        self.totalFracWaterSourceAllocation = self.fracSurfaceWaterAllocation + \
                                              self.fracNonFossilGroundwaterAllocation + \
                                              self.fracOtherWaterSourceAllocation 

        # Stefanie's post processing: reporting lake and reservoir storage (unit: m3)
        self.waterBodyStorage = pcr.ifthen(self._model.routing.landmask, \
                                pcr.ifthen(\
                                pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.,\
                                           self._model.routing.WaterBodies.waterBodyStorage))     # Note: This value is after lake/reservoir outflow.
        #
        # snowMelt (m/day)
        self.snowMelt = self._model.landSurface.snowMelt

        # soil moisture state from (approximately) the first 5 cm soil  
        if self._model.landSurface.numberOfSoilLayers == 3:
            self.storUppSurface   = self._model.landSurface.storUpp000005    # unit: m
            self.satDegUppSurface = self._model.landSurface.satDegUpp000005  # unit: percentage
        
        # reporting water balance from the land surface part (excluding surface water bodies)
        self.land_surface_water_balance = self._model.waterBalance
        
        # evaporation from irrigation areas (m/day) - values are average over the entire cell area
        ##if self._model.landSurface.includeIrrigation:\
        ##   self.evaporation_from_irrigation = self._model.landSurface.landCoverObj['irrPaddy'].actualET * \
        ##                                      self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
        ##                                      self._model.landSurface.landCoverObj['irrNonPaddy'].actualET * \
        ##                                      self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover 

        # Some examples to report variables from certain land cover types:
        # - unit: m/day - values are average over the entire cell area
        self.precipitation_at_irrigation    = pcr.ifthen(self._model.routing.landmask, pcr.scalar(0.0))
        self.netLqWaterToSoil_at_irrigation = pcr.ifthen(self._model.routing.landmask, pcr.scalar(0.0))
        self.evaporation_from_irrigation    = pcr.ifthen(self._model.routing.landmask, pcr.scalar(0.0))
        self.transpiration_from_irrigation  = pcr.ifthen(self._model.routing.landmask, pcr.scalar(0.0))
        if self._model.landSurface.includeIrrigation:
            self.precipitation_at_irrigation    = self._model.meteo.precipitation * \
                                                  self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                                  self._model.meteo.precipitation * \
                                                  self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover
            self.netLqWaterToSoil_at_irrigation = self._model.landSurface.landCoverObj['irrPaddy'].netLqWaterToSoil * \
                                                  self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                                  self._model.landSurface.landCoverObj['irrNonPaddy'].netLqWaterToSoil * \
                                                  self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover
            self.evaporation_from_irrigation    = self._model.landSurface.landCoverObj['irrPaddy'].actualET * \
                                                  self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                                  self._model.landSurface.landCoverObj['irrNonPaddy'].actualET * \
                                                  self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover
            self.transpiration_from_irrigation  = self._model.landSurface.landCoverObj['irrPaddy'].actTranspiTotal * \
                                                  self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                                  self._model.landSurface.landCoverObj['irrNonPaddy'].actTranspiTotal * \
self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover 

        # consumption for and return flow from non irrigation water demand (unit: m/day)  
        self.nonIrrWaterConsumption = self._model.routing.nonIrrWaterConsumption
        self.nonIrrReturnFlow       = self._model.routing.nonIrrReturnFlow

        # Total groundwater abstraction (m) (assuming otherWaterSourceAbstraction as fossil groundwater abstraction
        #self.totalGroundwaterAbstraction = self.nonFossilGroundwaterAbstraction +\
#self.fossilGroundwaterAbstraction

        # flood volume (unit: m3): excess above the channel storage capacity
        if self._model.routing.floodPlain:
           self.floodVolume = pcr.ifthen(self._model.routing.landmask, \
                      pcr.ifthenelse(pcr.cover(self._model.routing.WaterBodies.waterBodyIds,0) == 0,\
						          pcr.max(0.0,self._model.routing.channelStorage-self._model.routing.channelStorageCapacity), 0.0))

        # water withdrawal for irrigation sectors
        #self.irrPaddyWaterWithdrawal    = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.irrGrossDemandPaddy)
        #self.irrNonPaddyWaterWithdrawal = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.irrGrossDemandNonPaddy)
        #self.irrigationWaterWithdrawal  = self.irrPaddyWaterWithdrawal + self.irrNonPaddyWaterWithdrawal

        # water withdrawal for livestock, industry and domestic water demands
        #self.domesticWaterWithdrawal    = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.domesticWaterWithdrawal)
        #self.industryWaterWithdrawal    = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.industryWaterWithdrawal)
        #self.livestockWaterWithdrawal   = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.livestockWaterWithdrawal)



    def report(self):

        self.post_processing()

        # time stamp for reporting
        timeStamp = datetime.datetime(self._modelTime.year,\
                                      self._modelTime.month,\
                                      self._modelTime.day,\
                                      0)

        # writing daily output to netcdf files
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                
                short_name = varDicts.netcdf_short_name[var]
                self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_dailyTot_output.nc",\
                                            short_name,\
                  pcr2numpy(self.__getattribute__(var),vos.MV),\
                                            timeStamp)

        # writing weekly output to netcdf files (based on Niko's sub-seasonal code) #######
        # counting from Jan 1 (doy = 1) using doy%7=1 as beginning of week and doy%7=0 as end of week
        # - cummulative
        if self.outWeekTotNC[0] != "None":
            for var in self.outWeekTotNC:

                # introduce variables at the beginning of simulation or beginning of the year or 
                #     reset variables at the beginning of the week
                if self._modelTime.timeStepPCR == 1 or \
                   self._modelTime.doy == 1 or \
                   self._modelTime.beginWeek == True :\
                   vars(self)[var+'weekTot'] = pcr.scalar(0.0)

                # accumulating
                vars(self)[var+'weekTot'] += vars(self)[var]

                # reporting at the end of the month:
                if self._modelTime.endWeek == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                               "_weekTot_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var+'weekTot'),\
                       vos.MV),timeStamp)
        #
        # - average
        if self.outWeekAvgNC[0] != "None":
            for var in self.outWeekAvgNC:
                #logger.info('outWeekAvg beginWeek: %s', self._modelTime.beginWeek)
                #logger.info('outWeekAvg endWeek  : %s', self._modelTime.endWeek)
                # only if a accumulator variable has not been defined: 
                if var not in self.outWeekTotNC: 

                    # introduce accumulator at the beginning of simulation or
                    #     reset accumulator at the beginning of the month
                    if self._modelTime.timeStepPCR == 1 or \
                       self._modelTime.doy == 1 or \
                       self._modelTime.beginWeek == True :\
                       vars(self)[var+'weekTot'] = pcr.scalar(0.0)

                    # accumulating
                    vars(self)[var+'weekTot'] += vars(self)[var]

                # calculating average & reporting at the end of the week (weekLength doesn't work yet):
                if self._modelTime.endWeek == True:
                    #logger.info('weekLength is: %s %s', self._modelTime.weekLength, type(self._modelTime.weekLength))
                    vars(self)[var+'weekAvg'] = vars(self)[var+'weekTot']/\
                                                 7.0 #int(self._modelTime.weekLength)  

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_weekAvg_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var+'weekAvg'),\
                       vos.MV),timeStamp)
        #
        # - last day of the week
        if self.outWeekEndNC[0] != "None":
            for var in self.outWeekEndNC:

                # reporting at the end of the month:
                if self._modelTime.endWeek == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_weekEnd_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var),\
                       vos.MV),timeStamp)

        # writing monthly output to netcdf files
        # - cummulative
        if self.outMonthTotNC[0] != "None":
            for var in self.outMonthTotNC:

                # introduce variables at the beginning of simulation or
                #     reset variables at the beginning of the month
                if self._modelTime.timeStepPCR == 1 or \
                   self._modelTime.day == 1:\
                   vars(self)[var+'MonthTot'] = pcr.scalar(0.0)

                # accumulating
                vars(self)[var+'MonthTot'] += vars(self)[var]

                # reporting at the end of the month:
                if self._modelTime.endMonth == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                               "_monthTot_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var+'MonthTot'),\
                       vos.MV),timeStamp)
        #
        # - average
        if self.outMonthAvgNC[0] != "None":
            for var in self.outMonthAvgNC:

                # only if a accumulator variable has not been defined: 
                if var not in self.outMonthTotNC: 

                    # introduce accumulator at the beginning of simulation or
                    #     reset accumulator at the beginning of the month
                    if self._modelTime.timeStepPCR == 1 or \
                       self._modelTime.day == 1:\
                       vars(self)[var+'MonthTot'] = pcr.scalar(0.0)
                    
                    # accumulating
                    vars(self)[var+'MonthTot'] += vars(self)[var]

                # calculating average & reporting at the end of the month:
                if self._modelTime.endMonth == True:

                    vars(self)[var+'MonthAvg'] = vars(self)[var+'MonthTot']/\
                                                 self._modelTime.day  

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_monthAvg_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var+'MonthAvg'),\
                       vos.MV),timeStamp)
        #
        # - last day of the month
        if self.outMonthEndNC[0] != "None":
            for var in self.outMonthEndNC:

                # reporting at the end of the month:
                if self._modelTime.endMonth == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_monthEnd_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var),\
                       vos.MV),timeStamp)

        # - maximum
        if self.outMonthMaxNC[0] != "None":
            for var in self.outMonthMaxNC:

                # introduce variables at the beginning of simulation or
                #     reset variables at the beginning of the month
                if self._modelTime.timeStepPCR == 1 or \
                   self._modelTime.day == 1:\
                   vars(self)[var+'MonthMax'] = pcr.scalar(0.0)

                # find the maximum
                vars(self)[var+'MonthMax'] = pcr.max(vars(self)[var], vars(self)[var+'MonthMax'])

                # reporting at the end of the month:
                if self._modelTime.endMonth == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                               "_monthMax_output.nc",\
                                               short_name,\
                      pcr.pcr2numpy(self.__getattribute__(var+'MonthMax'),\
vos.MV),timeStamp)

        # writing yearly output to netcdf files
        # - cummulative
        if self.outAnnuaTotNC[0] != "None":
            for var in self.outAnnuaTotNC:

                # introduce variables at the beginning of simulation or
                #     reset variables at the beginning of the month
                if self._modelTime.timeStepPCR == 1 or \
                   self._modelTime.doy == 1:\
                   vars(self)[var+'AnnuaTot'] = pcr.scalar(0.0)

                # accumulating
                vars(self)[var+'AnnuaTot'] += vars(self)[var]

                # reporting at the end of the year:
                if self._modelTime.endYear == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_annuaTot_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var+'AnnuaTot'),\
                       vos.MV),timeStamp)

        # - average
        if self.outAnnuaAvgNC[0] != "None":
            for var in self.outAnnuaAvgNC:

                # only if a accumulator variable has not been defined: 
                if var not in self.outAnnuaTotNC: 

                    # introduce accumulator at the beginning of simulation or
                    #     reset accumulator at the beginning of the year
                    if self._modelTime.timeStepPCR == 1 or \
                       self._modelTime.doy == 1:\
                       vars(self)[var+'AnnuaTot'] = pcr.scalar(0.0)

                    # accumulating
                    vars(self)[var+'AnnuaTot'] += vars(self)[var]

                # calculating average & reporting at the end of the year:
                if self._modelTime.endYear == True:

                    vars(self)[var+'AnnuaAvg'] = vars(self)[var+'AnnuaTot']/\
                                                 self._modelTime.doy  

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_annuaAvg_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var+'AnnuaAvg'),\
                       vos.MV),timeStamp)
        #
        # -last day of the year
        if self.outAnnuaEndNC[0] != "None":
            for var in self.outAnnuaEndNC:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_annuaEnd_output.nc",\
                                               short_name,\
                      pcr2numpy(self.__getattribute__(var),\
                       vos.MV),timeStamp)

        logger.info("reporting for time %s", self._modelTime.currTime)
        
