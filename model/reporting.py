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

    def __init__(self, configuration, model, modelTime):

        self._model = model
        self._modelTime = modelTime

        # initiate reporting tool/object and its configuration
        self.initiate_reporting(configuration)

    def initiate_reporting(self, configuration):
        
        # output directory storing netcdf files:
        self.outNCDir  = str(configuration.outNCDir)

        # object for reporting:
        self.netcdfObj = PCR2netCDF(configuration)

        # initiating netcdf files for reporting
        #
        # - daily output in netCDF files:
        self.outDailyTotNC = ["None"]
        try:
            self.outDailyTotNC = list(set(configuration.reportingOptions['outDailyTotNC'].split(",")))
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
        #
        # - MONTHly output in netCDF files:
        # -- cummulative
        self.outMonthTotNC = ["None"]
        try:
            self.outMonthTotNC = list(set(configuration.reportingOptions['outMonthTotNC'].split(",")))
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
            self.outMonthAvgNC = list(set(configuration.reportingOptions['outMonthAvgNC'].split(",")))
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
            self.outMonthEndNC = list(set(configuration.reportingOptions['outMonthEndNC'].split(",")))
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
        #
        # - YEARly output in netCDF files:
        # -- cummulative
        self.outAnnuaTotNC = ["None"]
        try:
            self.outAnnuaTotNC = list(set(configuration.reportingOptions['outAnnuaTotNC'].split(",")))
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
            self.outAnnuaAvgNC = list(set(configuration.reportingOptions['outAnnuaAvgNC'].split(",")))
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
            self.outAnnuaEndNC = list(set(configuration.reportingOptions['outAnnuaEndNC'].split(",")))
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
                                    self.outMonthTotNC +\
                                    self.outMonthAvgNC +\
                                    self.outMonthEndNC +\
                                    self.outAnnuaTotNC +\
                                    self.outAnnuaAvgNC +\
                                    self.outAnnuaEndNC

    def post_processing(self):

        self.basic_post_processing() 
        self.additional_post_processing() 

    def basic_post_processing(self):

        # forcing 
        self.precipitation  = self._model.meteo.precipitation 
        self.temperature    = self._model.meteo.temperature
        self.referencePotET = self._model.meteo.referencePotET 

        # potential and actual evaporation from land surface part (m)
        self.totalLandSurfacePotET = self._model.landSurface.totalPotET 
        self.totLandSurfaceActuaET = self._model.landSurface.actualET
        #
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
        self.gwNetCapRise         = pcr.ifthenelse(self._model.landSurface.gwRecharge < 0.0, self.gwRecharge*(-1.0), 0.0)
        
        # water demand (m)
        self.irrGrossDemand       = self._model.landSurface.irrGrossDemand    
        self.nonIrrGrossDemand    = self._model.landSurface.nonIrrGrossDemand
        self.totalGrossDemand     = self._model.landSurface.totalPotentialGrossDemand
        
        self.satDegUpp            = self._model.landSurface.satDegUppTotal
        self.satDegLow            = self._model.landSurface.satDegLowTotal
        
        self.storGroundwater      = self._model.groundwater.storGroundwater
        
        self.baseflow             = self._model.groundwater.baseflow

        # abstraction (m)
        self.desalinationAbstraction         = self._model.landSurface.desalinationAbstraction
        self.surfaceWaterAbstraction         = self._model.landSurface.actSurfaceWaterAbstract
        self.nonFossilGroundwaterAbstraction = self._model.groundwater.nonFossilGroundwaterAbs
        self.fossilGroundwaterAbstraction    = self._model.groundwater.fossilGroundwaterAbstr
        self.totalAbstraction                = self.desalinationAbstraction +\
                                               self.surfaceWaterAbstraction +\
                                               self.nonFossilGroundwaterAbstraction +\
                                               self.fossilGroundwaterAbstraction
        
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

        # soil moisture state from (approximately) the first 5 cm soil  
        if self._model.landSurface.numberOfSoilLayers == 3:
            self.storUppSurface   = self._model.landSurface.storUpp000005    # unit: m
            self.satDegUppSurface = self._model.landSurface.satDegUpp000005  # unit: percentage
        
        # fraction of surface water bodies.
        self.dynamicFracWat = self._model.routing.dynamicFracWat
        
    def additional_post_processing(self):
        # In this method/function, users can add their own post-processing.
        
        # reporting water balance from the land surface part (excluding surface water bodies)
        if "land_surface_water_balance" in self.variables_for_report: self.land_surface_water_balance = self._model.waterBalance

        # accumulated baseflow (m3/s) along the drainage network
        if "accuBaseflow" in self.variables_for_report:
            self.accuBaseflow = pcr.catchmenttotal(self.baseflow * self._model.routing.cellArea, self._model.routing.lddMap) / vos.secondsPerDay()

        # local changes in water bodies (i.e. abstraction, return flow, evaporation, bed exchange), excluding runoff
        self.local_water_body_flux = self._model.routing.local_input_to_surface_water / self._model.routing.cellArea - self.runoff
        
        # total runoff (m) from local land surface runoff and local changes in water bodies 
        self.totalRunoff = self.runoff + self.local_water_body_flux     # actually this is equal to self._model.routing.local_input_to_surface_water / self._model.routing.cellArea

        # water body evaporation (m) - from surface water fractions only
        self.waterBodyActEvaporation = self._model.routing.waterBodyEvaporation
        self.waterBodyPotEvaporation = self._model.routing.waterBodyPotEvap
        #
        self.fractionWaterBodyEvaporation = vos.getValDivZero(self.waterBodyActEvaporation,\
                                                              self.waterBodyPotEvaporation,\
                                                              vos.smallNumber)

        # land surface evaporation (m)
        self.actualET = self._model.landSurface.actualET

        # fossil groundwater storage
        self.storGroundwaterFossil = self._model.groundwater.storGroundwaterFossil
        
        # total groundwater storage: (non fossil and fossil)
        self.storGroundwaterTotal  = self._model.groundwater.storGroundwater + \
                                     self._model.groundwater.storGroundwaterFossil
        
        # total active storage thickness (m) for the entire water column - not including fossil groundwater
        # - including: interception, snow, soil and non fossil groundwater 
        self.totalActiveStorageThickness = pcr.ifthen(\
                                           self._model.routing.landmask, \
                                           self._model.routing.channelStorage / self._model.routing.cellArea + \
                                           self._model.landSurface.totalSto + \
                                           self._model.groundwater.storGroundwater)

        # total water storage thickness (m) for the entire water column: 
        # - including: interception, snow, soil, non fossil groundwater and fossil groundwater
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
        #
        self.fracOtherWaterSourceAllocation = pcr.ifthen(self._model.routing.landmask, \
                                              vos.getValDivZero(\
                                              self._model.groundwater.unmetDemand, self.totalGrossDemand, vos.smallNumber))
        #
        self.fracDesalinatedWaterAllocation = pcr.ifthen(self._model.routing.landmask, \
                                              vos.getValDivZero(\
                                              self._model.landSurface.desalinationAllocation, self.totalGrossDemand, vos.smallNumber))
        #
        self.totalFracWaterSourceAllocation = self.fracSurfaceWaterAllocation + \
                                              self.fracNonFossilGroundwaterAllocation + \
                                              self.fracOtherWaterSourceAllocation + \
                                              self.fracDesalinatedWaterAllocation

        # Stefanie's post processing:
        # -  reporting lake and reservoir storage (unit: m3)
        self.waterBodyStorage = pcr.ifthen(self._model.routing.landmask, \
                                pcr.ifthen(\
                                pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.,\
                                           self._model.routing.WaterBodies.waterBodyStorage))     # Note: This value is after lake/reservoir outflow.
        # - snowMelt (m)
        self.snowMelt = self._model.landSurface.snowMelt

        # An example to report variables from certain land cover types 
        # - evaporation from irrigation areas (m/day) - values are average over the entire cell area
        if self._model.landSurface.includeIrrigation:
            self.evaporation_from_irrigation = self._model.landSurface.landCoverObj['irrPaddy'].actualET * \
                                               self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                               self._model.landSurface.landCoverObj['irrNonPaddy'].actualET * \
                                               self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover
        
        # Total groundwater abstraction (m) (assuming otherWaterSourceAbstraction as fossil groundwater abstraction
        self.totalGroundwaterAbstraction = self.nonFossilGroundwaterAbstraction +\
                                           self.fossilGroundwaterAbstraction

        # net liquid water passing to the soil 
        self.net_liquid_water_to_soil = self._model.landSurface.netLqWaterToSoil
        
        # consumptive water use and return flow from non irrigation water demand (unit: m/day)  
        self.nonIrrWaterConsumption = self._model.routing.nonIrrWaterConsumption
        self.nonIrrReturnFlow       = self._model.landSurface.nonIrrReturnFlow
        
        # total potential water demand - not considering water availability
        self.totalPotentialMaximumGrossDemand = self._model.landSurface.totalPotentialMaximumGrossDemand
        
        # return flow due to groundwater abstraction (unit: m/day)
        self.groundwaterAbsReturnFlow = self._model.routing.riverbedExchange / self._model.routing.cellArea
        # NOTE: Before 24 May 2015, the stupid Edwin forgot to divide this variable with self._model.routing.cellArea

        # transpiration from irrigation areas (in percentage)
        if self._model.landSurface.includeIrrigation:
            self.irrigationTranspiration = self._model.landSurface.landCoverObj['irrPaddy'].actTranspiTotal * self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                           self._model.landSurface.landCoverObj['irrNonPaddy'].actTranspiTotal * self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover
            self.irrigationPotTranspiration = self._model.landSurface.landCoverObj['irrPaddy'].potTranspiration * self._model.landSurface.landCoverObj['irrPaddy'].fracVegCover + \
                                              self._model.landSurface.landCoverObj['irrNonPaddy'].potTranspiration * self._model.landSurface.landCoverObj['irrNonPaddy'].fracVegCover
            self.fractionIrrigationTranspiration = pcr.min(1.0, vos.getValDivZero(self.irrigationTranspiration, self.irrigationPotTranspiration))

    def report(self):

        # recap all variables
        self.post_processing()

        # time stamp for reporting
        timeStamp = datetime.datetime(self._modelTime.year,\
                                      self._modelTime.month,\
                                      self._modelTime.day,\
                                      0)

        logger.info("reporting for time %s", self._modelTime.currTime)

        # writing daily output to netcdf files
        if self.outDailyTotNC[0] != "None":
            for var in self.outDailyTotNC:
                
                short_name = varDicts.netcdf_short_name[var]
                self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_dailyTot_output.nc",\
                                            short_name,\
                  pcr.pcr2numpy(self.__getattribute__(var),vos.MV),\
                                            timeStamp)

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
                      pcr.pcr2numpy(self.__getattribute__(var+'MonthTot'),\
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
                      pcr.pcr2numpy(self.__getattribute__(var+'MonthAvg'),\
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
                      pcr.pcr2numpy(self.__getattribute__(var),\
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
                      pcr.pcr2numpy(self.__getattribute__(var+'AnnuaTot'),\
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
                      pcr.pcr2numpy(self.__getattribute__(var+'AnnuaAvg'),\
                       vos.MV),timeStamp)
        #
        # -last day of the year
        if self.outAnnuaEndNC[0] != "None":
            for var in self.outAnnuaEndNC:

                # calculating average & reporting at the end of the year:
                if self._modelTime.endYear == True:

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                               str(var)+\
                                               "_annuaEnd_output.nc",\
                                               short_name,\
                      pcr.pcr2numpy(self.__getattribute__(var),\
                       vos.MV),timeStamp)
       
