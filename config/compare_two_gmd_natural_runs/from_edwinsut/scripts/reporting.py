#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Ludovicus P. H. (Rens) van Beek, Edwin H. Sutanudjaja, Yoshihide Wada,
# Joyce H. C. Bosmans, Niels Drost, Inge E. M. de Graaf, Kor de Jong, Patricia Lopez Lopez,
# Stefanie Pessenteiner, Oliver Schmitz, Menno W. Straatsma, Niko Wanders, Dominik Wisser,
# and Marc F. P. Bierkens,
# Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Takes care of reporting (writing) output to netcdf files. Aggregates totals and averages for various time periods.
@author: Edwin H. Sutanudjaja

Created on Jul 28, 2014. 
This "reporting.py" module is not the same as the one module initiated by Niels Drost.

@editors: Ruud van der Ent, Rens van Beek 2017
Added reporting of variables within the eartH2Observe project

'''

import os
import shutil

import logging
logger = logging.getLogger(__name__)

import pcraster as pcr

from ncConverter import *

from types import NoneType

import variable_list as varDicts

class Reporting(object):

    def __init__(self, configuration, model, modelTime):

        # model (e.g. PCR-GLOBWB) and modelTime object
        self._model = model
        self._modelTime = modelTime

        # configuration/setting from the ini file
        self.configuration = configuration
        
        # initiate reporting tool/object and its configuration
        self.initiate_reporting()

        # option for debugging to PCR-GLOBWB version 1.0
        self.debug_to_version_one = False
        if self.configuration.debug_to_version_one: self.debug_to_version_one = True

    def initiate_reporting(self):
        
        # output directory storing netcdf files:
        self.outNCDir  = str(self.configuration.outNCDir)

        # object for reporting:
        #RvB 23/02/2017: specific attributes included to allow for multiple netcdfAttributes
        if 'netcdfAttributesOptions' in vars(self.configuration).keys():
            logger.info("Passing specific netcdf attributes to the output files created")
            specificAttributeDictionary= self.configuration.netcdfAttributesOptions
        else:
            specificAttributeDictionary= None
        #-initialize netcdfObj    
        self.netcdfObj = PCR2netCDF(self.configuration, specificAttributeDictionary)

        # initiating netcdf files for reporting
        #
        # - daily output in netCDF files:
        self.outDailyTotNC = ["None"]
        try:
            self.outDailyTotNC = list(set(self.configuration.reportingOptions['outDailyTotNC'].split(",")))
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
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_dailyTot_output.nc",\
                                            short_name,unit,long_name,standard_name)
        #
        # - MONTHly output in netCDF files:
        # -- cummulative
        self.outMonthTotNC = ["None"]
        try:
            self.outMonthTotNC = list(set(self.configuration.reportingOptions['outMonthTotNC'].split(",")))
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
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthTot_output.nc",\
                                            short_name,unit,long_name,standard_name)
        #
        # -- average
        self.outMonthAvgNC = ["None"]
        try:
            self.outMonthAvgNC = list(set(self.configuration.reportingOptions['outMonthAvgNC'].split(",")))
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
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthAvg_output.nc",\
                                            short_name,unit,long_name,standard_name)

        #
        # -- last day of the month
        self.outMonthEndNC = ["None"]
        try:
            self.outMonthEndNC = list(set(self.configuration.reportingOptions['outMonthEndNC'].split(",")))
        except:
            pass
        if self.outMonthEndNC[0] != "None":

            for var in self.outMonthEndNC:

                logger.info("Creating the netcdf file for monthly end reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthEnd_output.nc",\
                                            short_name,unit,long_name,standard_name)
        #
        # -- maximum of the month
        self.outMonthMaxNC = ["None"]
        try:
            self.outMonthMaxNC = list(set(self.configuration.reportingOptions['outMonthMaxNC'].split(",")))
        except:
            pass
        if self.outMonthMaxNC[0] != "None":

            for var in self.outMonthMaxNC:

                logger.info("Creating the netcdf file for monthly maximum reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_monthMax_output.nc",\
                                            short_name,unit,long_name,standard_name)

        #
        # - YEARly output in netCDF files:
        # -- cummulative
        self.outAnnuaTotNC = ["None"]
        try:
            self.outAnnuaTotNC = list(set(self.configuration.reportingOptions['outAnnuaTotNC'].split(",")))
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
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaTot_output.nc",\
                                            short_name,unit,long_name,standard_name)
        #
        # -- average
        self.outAnnuaAvgNC = ["None"]
        try:
            self.outAnnuaAvgNC = list(set(self.configuration.reportingOptions['outAnnuaAvgNC'].split(",")))
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
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaAvg_output.nc",\
                                            short_name,unit,long_name,standard_name)
        #
        # -- last day of the year
        self.outAnnuaEndNC = ["None"]
        try:
            self.outAnnuaEndNC = list(set(self.configuration.reportingOptions['outAnnuaEndNC'].split(",")))
        except:
            pass
        if self.outAnnuaEndNC[0] != "None":

            for var in self.outAnnuaEndNC:

                logger.info("Creating the netcdf file for annual end reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaEnd_output.nc",\
                                            short_name,unit,long_name,standard_name)

        # -- maximum of the year
        self.outAnnuaMaxNC = ["None"]
        try:
            self.outAnnuaMaxNC = list(set(self.configuration.reportingOptions['outAnnuaMaxNC'].split(",")))
        except:
            pass
        if self.outAnnuaMaxNC[0] != "None":

            for var in self.outAnnuaMaxNC:

                logger.info("Creating the netcdf file for annual maximum reporting for variable %s.", str(var))

                short_name = varDicts.netcdf_short_name[var]
                unit       = varDicts.netcdf_unit[var]      
                long_name  = varDicts.netcdf_long_name[var]
                if long_name == None: long_name = short_name
                standard_name= short_name
                if var in varDicts.netcdf_standard_name.keys():
                    standard_name= varDicts.netcdf_standard_name[var]
                
                # creating netCDF files:
                self.netcdfObj.createNetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                            "_annuaMax_output.nc",\
                                            short_name,unit,long_name,standard_name)

        
        # list of variables that will be reported:
        self.variables_for_report = self.outDailyTotNC +\
                                    self.outMonthTotNC +\
                                    self.outMonthAvgNC +\
                                    self.outMonthEndNC +\
                                    self.outMonthMaxNC +\
                                    self.outAnnuaTotNC +\
                                    self.outAnnuaAvgNC +\
                                    self.outAnnuaEndNC +\
                                    self.outMonthMaxNC

    def post_processing(self):

        self.basic_post_processing() 
        self.additional_post_processing()
        #-RvB 23/02/2017: post-processing for the eartH2Observe project
        self.e2o_post_processing()
                
        if self.debug_to_version_one:
            if self._modelTime.timeStepPCR == 1: self.report_static_maps_for_debugging()
            self.report_forcing_for_debugging()
            self.report_vegetation_phenology_for_debugging()
        
        # saving some model paramaters 
        if self._modelTime.timeStepPCR == 1:
            # recession coefficient (day-1)
            pcr.report(self._model.groundwater.recessionCoeff, self.configuration.mapsDir + "/globalalpha.map")

    def report_forcing_for_debugging(self):

        # prepare forcing directory
        if self._modelTime.timeStepPCR == 1: 
            self.directory_for_forcing_maps = vos.getFullPath("meteo/", self.configuration.mapsDir)
            if os.path.exists(self.directory_for_forcing_maps): shutil.rmtree(self.directory_for_forcing_maps)
            os.makedirs(self.directory_for_forcing_maps)
        
        # writing precipitation time series maps
        file_name = self.directory_for_forcing_maps +\
                    pcr.framework.frameworkBase.generateNameT("/"+varDicts.pcr_short_name['precipitation'] , self._modelTime.timeStepPCR)
        pcr.report(self._model.meteo.precipitation, file_name) 

        # writing temperature time series maps
        file_name = self.directory_for_forcing_maps +\
                    pcr.framework.frameworkBase.generateNameT("/"+varDicts.pcr_short_name['temperature']   , self._modelTime.timeStepPCR)
        pcr.report(self._model.meteo.temperature, file_name) 

        # writing referencePotET time series maps
        file_name = self.directory_for_forcing_maps +\
                    pcr.framework.frameworkBase.generateNameT("/"+varDicts.pcr_short_name['referencePotET'], self._modelTime.timeStepPCR)
        pcr.report(self._model.meteo.referencePotET, file_name) 


    def report_vegetation_phenology_for_debugging(self):

        # CF_SHORTSTACK = maps\cover_fraction/cv_s;	 # fractional vegetation cover (-) per vegetation type
        # CF_TALLSTACK  = maps\cover_fraction/cv_t;			
        
        # prepare directory
        if self._modelTime.timeStepPCR == 1: 
            self.directory_for_cover_fraction_maps = vos.getFullPath("cover_fraction/", self.configuration.mapsDir)
            if os.path.exists(self.directory_for_cover_fraction_maps): shutil.rmtree(self.directory_for_cover_fraction_maps)
            os.makedirs(self.directory_for_cover_fraction_maps)
        
        # writing CF_SHORTSTACK maps
        file_name = self.directory_for_cover_fraction_maps +\
                    pcr.framework.frameworkBase.generateNameT("/cv_s", self._modelTime.timeStepPCR)
        pcr.report(self._model.landSurface.landCoverObj["grassland"].coverFraction, file_name) 

        # writing CF_TALLSTACK maps
        file_name = self.directory_for_cover_fraction_maps +\
                    pcr.framework.frameworkBase.generateNameT("/cv_t", self._modelTime.timeStepPCR)
        pcr.report(self._model.landSurface.landCoverObj["forest"].coverFraction, file_name) 


        # SMAX_SHORTSTACK = maps\interception_capacity_input\smax_s     # interception storage (m) per vegetation type
        # SMAX_TALLSTACK  = maps\interception_capacity_input\smax_t

        # prepare directory
        if self._modelTime.timeStepPCR == 1: 
            self.directory_for_interception_capacity_input_maps = vos.getFullPath("interception_capacity_input/", self.configuration.mapsDir)
            if os.path.exists(self.directory_for_interception_capacity_input_maps): shutil.rmtree(self.directory_for_interception_capacity_input_maps)
            os.makedirs(self.directory_for_interception_capacity_input_maps)
        
        # writing SMAX_SHORTSTACK maps
        file_name = self.directory_for_interception_capacity_input_maps +\
                    pcr.framework.frameworkBase.generateNameT("/smax_s", self._modelTime.timeStepPCR)
        pcr.report(self._model.landSurface.landCoverObj["grassland"].interceptCapInput, file_name) 
        
        # writing SMAX_TALLSTACK maps
        file_name = self.directory_for_interception_capacity_input_maps +\
                    pcr.framework.frameworkBase.generateNameT("/smax_t", self._modelTime.timeStepPCR)
        pcr.report(self._model.landSurface.landCoverObj["forest"].interceptCapInput, file_name) 


        # KC_SHORTSTACK = maps\crop_coefficient\kc_s; # crop factor (-) per vegetation type
        # KC_TALLSTACK  = maps\crop_coefficient\kc_t;

        # prepare directory
        if self._modelTime.timeStepPCR == 1: 
            self.directory_for_crop_coefficient_maps = vos.getFullPath("crop_coefficient/", self.configuration.mapsDir)
            if os.path.exists(self.directory_for_crop_coefficient_maps): shutil.rmtree(self.directory_for_crop_coefficient_maps)
            os.makedirs(self.directory_for_crop_coefficient_maps)

        # writing KC_SHORTSTACK
        file_name = self.directory_for_crop_coefficient_maps +\
                    pcr.framework.frameworkBase.generateNameT("/kc_s", self._modelTime.timeStepPCR)
        pcr.report(self._model.landSurface.landCoverObj["grassland"].inputCropKC, file_name) 
        
        # writing KC_TALLSTACK
        file_name = self.directory_for_crop_coefficient_maps +\
                    pcr.framework.frameworkBase.generateNameT("/kc_t", self._modelTime.timeStepPCR)
        pcr.report(self._model.landSurface.landCoverObj["forest"].inputCropKC, file_name) 


    def report_static_maps_for_debugging(self):

        # LANDMASK = $1\maps\catclone.map;				                   # clone map representing landmask of earth surface
        # CELLAREA = $1\maps\cellarea30.map;				               # surface (m2) of cell covered by total land surface

        pcr.report(self._model.routing.landmask, self.configuration.mapsDir+"/catclone.map") 
        pcr.report(self._model.routing.cellArea, self.configuration.mapsDir+"/cellarea30.map") 


        # LSLOPE   = $1\maps\globalbcat.map;			                   # slope length (m)
        # TANSLOPE = $1\maps\globalgradslope.map;	                       # gradient of slope (m/m)
        # B_ORO    = $1\maps\globalboro.map;			                   # shape coefficient related to orography

        pcr.report(self._model.landSurface.soil_topo_parameters['default'].slopeLength  , self.configuration.mapsDir+"/globalbcat.map") 
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].tanslope     , self.configuration.mapsDir+"/globalgradslope.map") 
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].orographyBeta, self.configuration.mapsDir+"/globalboro.map") 


        # LDD      = maps\lddsound_30min.map;			                   # local drainage direction map

        pcr.report(self._model.routing.lddMap, self.configuration.mapsDir+"/lddsound_30min.map") 


        # DZREL0001 = $1\maps\hydro1k_dzrel0001.map;                       # maps of relative elevation above floodplain, in percent
        # DZREL0005 = $1\maps\hydro1k_dzrel0005.map;
        # DZREL0010 = $1\maps\hydro1k_dzrel0010.map;
        # DZREL0020 = $1\maps\hydro1k_dzrel0020.map;
        # DZREL0030 = $1\maps\hydro1k_dzrel0030.map;
        # DZREL0040 = $1\maps\hydro1k_dzrel0040.map;
        # DZREL0050 = $1\maps\hydro1k_dzrel0050.map;
        # DZREL0060 = $1\maps\hydro1k_dzrel0060.map;
        # DZREL0070 = $1\maps\hydro1k_dzrel0070.map;
        # DZREL0080 = $1\maps\hydro1k_dzrel0080.map;
        # DZREL0090 = $1\maps\hydro1k_dzrel0090.map;
        # DZREL0100 = $1\maps\hydro1k_dzrel0100.map;

        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0001, self.configuration.mapsDir+"/hydro1k_dzrel0001.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0005, self.configuration.mapsDir+"/hydro1k_dzrel0005.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0010, self.configuration.mapsDir+"/hydro1k_dzrel0010.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0020, self.configuration.mapsDir+"/hydro1k_dzrel0020.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0030, self.configuration.mapsDir+"/hydro1k_dzrel0030.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0040, self.configuration.mapsDir+"/hydro1k_dzrel0040.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0050, self.configuration.mapsDir+"/hydro1k_dzrel0050.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0060, self.configuration.mapsDir+"/hydro1k_dzrel0060.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0070, self.configuration.mapsDir+"/hydro1k_dzrel0070.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0080, self.configuration.mapsDir+"/hydro1k_dzrel0080.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0090, self.configuration.mapsDir+"/hydro1k_dzrel0090.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].dzRel0100, self.configuration.mapsDir+"/hydro1k_dzrel0100.map")
        
        # COVERTYPE = [
        #   SHORT = sv,
        #   TALL  = tv];							# array of cover type: 1) short, 2) tall
        # COVERTABLE = maps\param_permafrost.tbl;	# table with parameterization per cover type
        
        # VEGFRAC[COVERTYPE] = index(COVERTABLE);	# subdivision in cover type
        version_one_cover_type = {}
        version_one_cover_type['grassland'] = "short"
        version_one_cover_type['forest']    = "tall" 


        # VEGFRAC 	sv	maps\vegf_short.map
        # VEGFRAC 	tv	maps\vegf_tall.map

        for coverType in ['forest','grassland']:
            pcr.report(self._model.landSurface.landCoverObj[coverType].fracVegCover, self.configuration.mapsDir+"/vegf_"+version_one_cover_type[coverType]+".map") 


        # THETASAT1 	sv	maps\fao30_ths30.map					  # THETASAT1 	tv	maps\fao30_ths30.map
        # THETASAT2 	sv	maps\fao30_ths100.map                     # THETASAT2 	tv	maps\fao30_ths100.map
        # THETARES1 	sv	maps\fao30_thr30.map                      # THETARES1 	tv	maps\fao30_thr30.map
        # THETARES2 	sv	maps\fao30_thr100.map                     # THETARES2 	tv	maps\fao30_thr100.map
        # KS1 			sv	maps\fao30_ks30.map                       # KS1 		tv	maps\fao30_ks30.map
        # KS2 			sv	maps\fao30_ks100.map                      # KS2 		tv	maps\fao30_ks100.map
        # PSI_A1 		sv	maps\fao30_psis30.map                     # PSI_A1 		tv	maps\fao30_psis30.map
        # PSI_A2 		sv	maps\fao30_psis100.map                    # PSI_A2 		tv	maps\fao30_psis100.map
        # BCH1 			sv	maps\fao30_beta30.map                     # BCH1 		tv	maps\fao30_beta30.map
        # BCH2 			sv	maps\fao30_beta100.map                    # BCH2 		tv	maps\fao30_beta100.map

        pcr.report(self._model.landSurface.soil_topo_parameters['default'].satVolMoistContUpp, self.configuration.mapsDir+"/fao30_ths30.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].satVolMoistContLow, self.configuration.mapsDir+"/fao30_ths100.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].resVolMoistContUpp, self.configuration.mapsDir+"/fao30_thr30.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].resVolMoistContLow, self.configuration.mapsDir+"/fao30_thr100.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].airEntryValueUpp  , self.configuration.mapsDir+"/fao30_psis30.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].airEntryValueLow  , self.configuration.mapsDir+"/fao30_psis100.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].poreSizeBetaUpp   , self.configuration.mapsDir+"/fao30_beta30.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].poreSizeBetaLow   , self.configuration.mapsDir+"/fao30_beta100.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].kSatUpp           , self.configuration.mapsDir+"/fao30_ks30.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].kSatLow           , self.configuration.mapsDir+"/fao30_ks100.map")


        # Z1			sv	maps\fao30_z1_permafrost.map              # Z1			tv	maps\fao30_z1_permafrost.map
        # Z2			sv	maps\fao30_z2_permafrost.map              # Z2			tv	maps\fao30_z2_permafrost.map
        # SC1			sv	maps\fao30_sc1_permafrost.map             # SC1			tv	maps\fao30_sc1_permafrost.map
        # SC2			sv	maps\fao30_sc2_permafrost.map             # SC2			tv	maps\fao30_sc2_permafrost.map

        pcr.report(self._model.landSurface.soil_topo_parameters['default'].thickUpp               , self.configuration.mapsDir+"/fao30_z1_permafrost.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].thickLow               , self.configuration.mapsDir+"/fao30_z2_permafrost.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].storCapUpp             , self.configuration.mapsDir+"/fao30_sc1_permafrost.map")
        pcr.report(self._model.landSurface.soil_topo_parameters['default'].storCapLow             , self.configuration.mapsDir+"/fao30_sc2_permafrost.map")

        # WMAX			sv	maps\fao30_sc_permafrost.map              # WMAX		tv	maps\fao30_sc_permafrost.map

        pcr.report(self._model.landSurface.soil_topo_parameters['default'].rootZoneWaterStorageCap, self.configuration.mapsDir+"/fao30_sc_permafrost.map")


        # P2_IMP		sv	maps\fao30_p2imp_permafrost.map           # P2_IMP		tv	maps\fao30_p2imp_permafrost.map

        pcr.report(self._model.landSurface.soil_topo_parameters['default'].percolationImp             , self.configuration.mapsDir+"/fao30_p2imp_permafrost.map")


        # MINFRAC		sv 	maps\minf_short.map                       # MINFRAC		tv 	maps\minf_tall.map
        # MAXFRAC		sv	maps\maxf_short.map                       # MAXFRAC		tv	maps\maxf_tall.map
        # RFRAC1		sv	maps\rfrac1_short.map                     # RFRAC1		tv	maps\rfrac1_tall.map
        # RFRAC2		sv  maps\rfrac2_short.map                     # RFRAC2		tv 	maps\rfrac2_tall.map
        
        for coverType in ['forest','grassland']:
            pcr.report(self._model.landSurface.landCoverObj[coverType].minSoilDepthFrac, self.configuration.mapsDir+"/minf_"+version_one_cover_type[coverType]+".map") 
            pcr.report(self._model.landSurface.landCoverObj[coverType].maxSoilDepthFrac, self.configuration.mapsDir+"/maxf_"+version_one_cover_type[coverType]+".map") 
            pcr.report(self._model.landSurface.landCoverObj[coverType].rootFraction1   , self.configuration.mapsDir+"/rfrac1_"+version_one_cover_type[coverType]+".map") 
            pcr.report(self._model.landSurface.landCoverObj[coverType].rootFraction2   , self.configuration.mapsDir+"/rfrac2_"+version_one_cover_type[coverType]+".map") 

        
        # KQ3            = maps\globalalpha.map;	# recession coefficient for store 3 (day-1): drainage
        # SPECYIELD3     = maps\specificyield.map;	# specific yield for aquifer

        pcr.report(self._model.groundwater.recessionCoeff, self.configuration.mapsDir+"/globalalpha.map")
        pcr.report(self._model.groundwater.specificYield , self.configuration.mapsDir+"/specificyield.map")


    def basic_post_processing(self):

        # forcing 
        self.precipitation  = pcr.ifthen(self._model.routing.landmask, self._model.meteo.precipitation) 
        self.temperature    = pcr.ifthen(self._model.routing.landmask, self._model.meteo.temperature)
        self.referencePotET = pcr.ifthen(self._model.routing.landmask, self._model.meteo.referencePotET) 

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
		
        if self._model.landSurface.numberOfSoilLayers == 3:
            self.storUpp000005  = self._model.landSurface.storUpp000005
            self.storUpp005030  = self._model.landSurface.storUpp005030
            self.storLow030150  = self._model.landSurface.storLow030150
        
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

        # total water storage volume (m3) for the entire water column: 
        self.totalWaterStorageVolume = self.totalWaterStorageThickness * self._model.routing.cellArea
        
        # surfaceWaterStorage (unit: m) - negative values may be reported
        self.surfaceWaterStorage = self._model.routing.channelStorage / self._model.routing.cellArea

        # estimate of river/surface water levels (above channel/surface water bottom elevation)
        self.surfaceWaterLevel = pcr.ifthenelse(self.dynamicFracWat > 0., self._model.routing.channelStorage / \
                                                                         (self.dynamicFracWat * self._model.routing.cellArea), 
                                                                          0.0)
        self.surfaceWaterLevel = pcr.max(0.0, pcr.ifthen(self._model.routing.landmask, self.surfaceWaterLevel)) 

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
                                pcr.cover(\
                                pcr.ifthen(\
                                pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.,\
                                           self._model.routing.WaterBodies.waterBodyStorage), 0.0))     # Note: This value is after lake/reservoir outflow.
        # - snowMelt (m)
        self.snowMelt = self._model.landSurface.snowMelt

        # channel storage (unit: m3)
        self.channelStorage = pcr.ifthen(self._model.routing.landmask, \
                              pcr.cover(self._model.routing.channelStorage, 0.0)) 
        
        
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


		#-----------------------------------------------------------------------
		# NOTE (RvB, 12/07): the following has been changed to get the actual flood volume and depth;
		# because the waterBodyIDs get covered by zeroes, values for all areas are returned as zero
        #
        # flood innundation depth (unit: m) above the floodplain
        #~ if self._model.routing.floodPlain:\
           #~ self.floodDepth = pcr.ifthen(self._model.routing.landmask, \
                      #~ pcr.ifthenelse(pcr.cover(pcr.scalar(self._model.routing.WaterBodies.waterBodyIds), 0.0) > 0.0, 0.0,
                                     #~ self._model.routing.floodDepth))
        #                        
        # flood volume (unit: m3): excess above the channel storage capacity
        #~ if self._model.routing.floodPlain:\
           #~ self.floodVolume = pcr.ifthen(self._model.routing.landmask, \
                      #~ pcr.ifthenelse(pcr.cover(pcr.scalar(self._model.routing.WaterBodies.waterBodyIds), 0.0) > 0.0, 0.0, \
                      #~ pcr.max(0.0, self._model.routing.channelStorage - self._model.routing.channelStorageCapacity)))
        #              
        # flood innundation depth (unit: m) above the floodplain
        if self._model.routing.floodPlain:
           self.floodDepth = pcr.ifthen(self._model.routing.landmask, \
                      pcr.ifthenelse(pcr.cover(self._model.routing.WaterBodies.waterBodyIds,0) == 0,\
					            self._model.routing.floodDepth, 0.0))
		#				
        # flood volume (unit: m3): excess above the channel storage capacity
        if self._model.routing.floodPlain:
           self.floodVolume = pcr.ifthen(self._model.routing.landmask, \
                      pcr.ifthenelse(pcr.cover(self._model.routing.WaterBodies.waterBodyIds,0) == 0,\
						          pcr.max(0.0,self._model.routing.channelStorage-self._model.routing.channelStorageCapacity), 0.0))
		#-----------------------------------------------------------------------
        
        # water withdrawal for irrigation sectors
        self.irrPaddyWaterWithdrawal    = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.irrGrossDemandPaddy)
        self.irrNonPaddyWaterWithdrawal = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.irrGrossDemandNonPaddy)
        self.irrigationWaterWithdrawal  = self.irrPaddyWaterWithdrawal + self.irrNonPaddyWaterWithdrawal
        
        # water withdrawal for livestock, industry and domestic water demands
        self.domesticWaterWithdrawal    = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.domesticWaterWithdrawal)
        self.industryWaterWithdrawal    = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.industryWaterWithdrawal)
        self.livestockWaterWithdrawal   = pcr.ifthen(self._model.routing.landmask, self._model.landSurface.livestockWaterWithdrawal)

        
        ######################################################################################################################################################################
        # All water withdrawal variables in volume unit (m3): 
        waterWithdrawalVariables = [
                                    'totalGroundwaterAbstraction',\
                                    'surfaceWaterAbstraction',\
                                    'desalinationAbstraction',\
                                    'domesticWaterWithdrawal',\
                                    'industryWaterWithdrawal',\
                                    'livestockWaterWithdrawal',\
                                    'irrigationWaterWithdrawal',\
                                    'irrGrossDemand',\
                                    'nonIrrGrossDemand',\
                                    'totalGrossDemand'\
                                    ]
        for var in waterWithdrawalVariables:
                volVariable = var + 'Volume'
                vars(self)[volVariable] = None 
                vars(self)[volVariable] = self._model.routing.cellArea * vars(self)[var]
        ######################################################################################################################################################################
                                                         

        ##########################################################################################################################################################################################
        # Consumptive water use (unit: m3/day) for livestock, domestic and industry 
        self.livestockWaterConsumptionVolume = self._model.landSurface.livestockReturnFlowFraction * self.livestockWaterWithdrawalVolume 
        self.domesticWaterConsumptionVolume  = self._model.landSurface.domesticReturnFlowFraction  * self.domesticWaterWithdrawalVolume
        self.industryWaterConsumptionVolume  = self._model.landSurface.industryReturnFlowFraction  * self.industryWaterWithdrawalVolume
        ##########################################################################################################################################################################################


        ######################################################################################################################################################################
        # For irrigation sector, the net consumptive water use will be calculated using annual values as follows:
        # irrigation_water_consumption_volume = self.evaporation_from_irrigation_volume * self.irrigationWaterWithdrawal / \
        #                                                                         (self.precipitation_at_irrigation + self.irrigationWaterWithdrawal)  
        self.precipitation_at_irrigation_volume = self.precipitation_at_irrigation * self._model.routing.cellArea
        self.evaporation_from_irrigation_volume = self.evaporation_from_irrigation * self._model.routing.cellArea
        # - additional values (may be needed) 
        self.netLqWaterToSoil_at_irrigation_volume = self.netLqWaterToSoil_at_irrigation * self._model.routing.cellArea
        self.transpiration_from_irrigation_volume  = self.transpiration_from_irrigation  * self._model.routing.cellArea
        ######################################################################################################################################################################


        # fluxes from water bodies (lakes and reservoirs) - unit: m3/s
        self.lake_and_reservoir_inflow = self._model.routing.WaterBodies.inflowInM3PerSec


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
        #
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
                #     reset variables at the beginning of the year
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
        #
        # - maximum
        if self.outAnnuaMaxNC[0] != "None":
            for var in self.outAnnuaMaxNC:

                # introduce variables at the beginning of simulation or
                #     reset variables at the beginning of the year
                if self._modelTime.timeStepPCR == 1 or \
                   self._modelTime.doy == 1:\
                   vars(self)[var+'AnnuaMax'] = pcr.scalar(0.0)

                # find the maximum
                vars(self)[var+'AnnuaMax'] = pcr.max(vars(self)[var], vars(self)[var+'AnnuaMax'])

                # reporting at the end of the year:
                if self._modelTime.endYear == True: 

                    short_name = varDicts.netcdf_short_name[var]
                    self.netcdfObj.data2NetCDF(self.outNCDir+"/"+ \
                                            str(var)+\
                                               "_annuaMax_output.nc",\
                                               short_name,\
                      pcr.pcr2numpy(self.__getattribute__(var+'AnnuaMax'),\
                       vos.MV),timeStamp)
       
    def e2o_post_processing(self):

        # RvB 23/02/2017: post-processing of earth2observe variables
        
        # fluxes (/86.4 to go from "m day-1" to "kg m-2 s-1")
        self.Precip     =   self._model.meteo.precipitation / 86.4 # report in kg m-2 s-1
        self.Evap       = - (self._model.landSurface.actualET + 
                            self._model.routing.waterBodyEvaporation) / 86.4 # report in kg m-2 s-1
        self.Runoff     = - self._model.routing.runoff / 86.4 # report in kg m-2 s-1
        self.Qs         = - (self._model.landSurface.directRunoff + 
                            self._model.landSurface.interflowTotal) / 86.4  # report in kg m-2 s-1
        self.Qsb        = - self._model.groundwater.baseflow / 86.4 # report in kg m-2 s-1
        self.Qsm        =   self._model.landSurface.snowMelt / 86.4 # report in kg m-2 s-1
        self.PotEvap    = - self._model.meteo.referencePotET / 86.4 # report in kg m-2 s-1
        self.ECanop     = - self._model.landSurface.interceptEvap / 86.4 # report in kg m-2 s-1
        self.TVeg       = - self._model.landSurface.actTranspiTotal / 86.4 # report in kg m-2 s-1
        self.ESoil      = - self._model.landSurface.actBareSoilEvap / 86.4 # report in kg m-2 s-1
        self.EWater     = - self._model.routing.waterBodyEvaporation / 86.4 # report in kg m-2 s-1
        self.RivOut     =   self._model.routing.disChanWaterBody # report in m3/s
        
        # state variables (*1000 to go from "m" to "kg m-2")
        self.SWE        =   self._model.landSurface.snowCoverSWE * 1000 # report in kg m-2
        self.CanopInt   =   self._model.landSurface.interceptStor * 1000 # report in kg m-2
        self.SurfStor   =   ( self._model.landSurface.topWaterLayer 
                            + (self._model.routing.channelStorage/self._model.routing.cellArea) 
                            + pcr.ifthen(self._model.routing.landmask, 
                            pcr.ifthen(
                            pcr.scalar(self._model.routing.WaterBodies.waterBodyIds) > 0.,
                                       self._model.routing.WaterBodies.waterBodyStorage)) ) * 1000  # report in kg m-2
        self.SurfMoist  =   self._model.landSurface.storUppTotal * 1000 # report in kg m-2 (water in SurfLayerThick)
        self.RootMoist  =   ( self._model.landSurface.storUppTotal + 
                            self._model.landSurface.storLowTotal ) * 1000 # report in kg m-2 (water in RootLayerThick)
        self.TotMoist   =   self.RootMoist # equals RootMoist...
        self.GroundMoist    = self._model.groundwater.storGroundwater * 1000  # self._model.groundwater. # report in kg m-2
