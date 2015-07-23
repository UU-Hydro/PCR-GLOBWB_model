#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import datetime

import pcraster as pcr
from pcraster.framework import DynamicModel

from ncConverter import *
import virtualOS as vos

import variable_list as varDicts

import logging
logger = logging.getLogger(__name__)

class PCRGlobWBVersionOne(DynamicModel):

    def __init__(self, configuration, \
                       modelTime):
        DynamicModel.__init__(self)
        
        # configuration (based on the ini file)
        self.configuration = configuration
        
        # time variable/object
        self.modelTime = modelTime
        
        # cloneMapFileName
        self.cloneMapFileName = self.configuration.cloneMap
        pcr.setclone(self.cloneMapFileName)
        
        # output variables that will be compared (at daily resolution)
        self.debug_variables = ['runoff',
                                'actualET',
                                'storUppTotal',
                                'storLowTotal',
                                'actBareSoilEvap',
                                'directRunoff',
                                'gwRecharge',
                                'baseflow',
                                'precipitation',
                                'temperature',
                                'referencePotET',
                                'interflowTotal',
                                'interceptStor',
                                'storGroundwater',
                                'infiltration']
        
        # folder/location of oldcalc input maps
        self.maps_folder = self.configuration.mapsDir
        
        # folder/location of oldcalc results maps
        self.results_folder = self.configuration.globalOptions['outputDir']+"/oldcalc_results/"
        # - preparing the directory
        if os.path.exists(self.results_folder): shutil.rmtree(self.results_folder)
        os.makedirs(self.results_folder)
        # - preparing the folder to store netcdf files
        self.netcdf_folder  = self.configuration.globalOptions['outputDir']+"/oldcalc_results/netcdf/"
        os.makedirs(self.netcdf_folder)
        
        # go to the starting directory and copy/backup the oldcalc_script and parameter_table files 
        os.chdir(self.configuration.starting_directory)
        
        # the oldscript scripts used:
        self.oldcalc_script_file  = vos.getFullPath(self.configuration.globalOptions['oldcalc_script_file'],  self.configuration.starting_directory)
        self.parameter_tabel_file = vos.getFullPath(self.configuration.globalOptions['parameter_tabel_file'], self.configuration.starting_directory)
        
        # make the backup of oldscript scripts used
        shutil.copy(self.oldcalc_script_file , self.configuration.scriptDir)
        shutil.copy(self.parameter_tabel_file, self.configuration.scriptDir)

        # attribute information used in netcdf files:
        netcdfAttributeDictionary = {}
        netcdfAttributeDictionary['institution'] = self.configuration.globalOptions['institution'] 
        netcdfAttributeDictionary['title'      ] = "PCR-GLOBWB 1 output"
        netcdfAttributeDictionary['description'] = self.configuration.globalOptions['description']+" (this is the output from the oldcalc PCR-GLOBWB version 1)"
        
        # netcdf object for reporting
        self.netcdf_report = PCR2netCDF(configuration, netcdfAttributeDictionary)       

        # make/prepare netcdf files
        for var in self.debug_variables:

            short_name = varDicts.netcdf_short_name[var]
            unit       = varDicts.netcdf_unit[var]      
            long_name  = varDicts.netcdf_long_name[var]
            if long_name == None: long_name = short_name  

            netcdf_file_name = self.netcdf_folder+"/"+str(var)+"_dailyTot_output_version_one.nc"

            logger.info("Creating the netcdf file for daily reporting for the variable %s to the file %s (output from PCR-GLOBWB version 1).", str(var), str(netcdf_file_name))

            self.netcdf_report.createNetCDF(netcdf_file_name,short_name,unit,long_name)
        
    def initial(self): 
        
        logger.info("Execute the oldcalc script.")
        
        # choosing the steps for monthly reporting
        if self.modelTime.nrOfTimeSteps == 365: monthly_end_times = "31 59 90 120 151 181 212 243 273 304 334 365"
        if self.modelTime.nrOfTimeSteps == 366: monthly_end_times = "31 60 91 121 152 182 213 244 274 305 335 366"
        
        # execute oldcalc script
        # - copy the parameter table file to mapsDir
        shutil.copy(self.parameter_tabel_file, self.configuration.mapsDir)
        # - copy the script directory to outputDir and execute it from there
        shutil.copy(self.oldcalc_script_file , self.configuration.globalOptions['outputDir'])
        os.chdir(self.configuration.globalOptions['outputDir'])
        # - execute the script
        cmd = 'oldcalc -f '+str(os.path.basename(self.oldcalc_script_file))+" "+monthly_end_times
        print cmd
        vos.cmd_line(cmd)

    def dynamic(self):
        
        # make netcdf files, particularly for daily resolution values 
        
        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())

        # timeStamp for reporting
        timeStamp = datetime.datetime(self.modelTime.year,\
                                      self.modelTime.month,\
                                      self.modelTime.day,0)

        # reading variables from pcraster files and report them as netcdf files
        for var in self.debug_variables:

            pcraster_map_file_name = self.results_folder + "/" +\
                                     pcr.framework.frameworkBase.generateNameT(varDicts.pcr_short_name[var],\
                                                                               self.modelTime.timeStepPCR)
            logger.debug("Reading the variable %s from the file %s ", var, pcraster_map_file_name)
            pcr_map_values = pcr.readmap(str(pcraster_map_file_name))
            
            short_name = varDicts.netcdf_short_name[var]
            netcdf_file_name = self.netcdf_folder+"/"+str(var)+"_dailyTot_output_version_one.nc"

            logger.debug("Saving to the file %s ", netcdf_file_name)
            self.netcdf_report.data2NetCDF(netcdf_file_name, short_name,\
                                           pcr.pcr2numpy(pcr_map_values,vos.MV),\
                                           timeStamp)

    def compare_output(self):

        logger.info("Comparing the netcdf output files from versions one and two (using cdo).")
        
        # make/prepare the debug directory and go to the debug directory
        debug_directory = self.configuration.globalOptions['outputDir']+"/debug/"
        # - preparing the directory
        if os.path.exists(debug_directory): shutil.rmtree(debug_directory)
        os.makedirs(debug_directory)
        # - go to the debug directory
        os.chdir(debug_directory)
        
        for var in self.debug_variables:

            msg = "Comparing the netcdf output files from the variable "+str(var)
            logger.info(msg)

            short_name = varDicts.netcdf_short_name[var]

            filename_version_two = self.configuration.outNCDir+"/"+str(var)+"_dailyTot_output.nc"
            filename_version_one = self.netcdf_folder         +"/"+str(var)+"_dailyTot_output_version_one.nc"

            cmd = 'cdo sub '+filename_version_two+" "+filename_version_one+" "+var+"_diff.nc"
            vos.cmd_line(cmd)

        pass


