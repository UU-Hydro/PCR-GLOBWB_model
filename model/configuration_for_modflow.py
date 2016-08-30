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

import ConfigParser
import optparse
import os
import sys
import virtualOS as vos
import time
import datetime
import shutil
import glob

import logging
logger = logging.getLogger(__name__)

import disclaimer

'''
Created on May 21, 2015

@author: Edwin H. Sutanudjaja

This file is to handle the configuration for modflow run. 


'''

class Configuration(object):

    def __init__(self, iniFileName, debug_mode = False, steady_state_only = False):
        object.__init__(self)

        # timestamp of this run, used in logging file names, etc
        self._timestamp = datetime.datetime.now()
        
        # get the full path of iniFileName
        self.iniFileName = os.path.abspath(iniFileName)

        # debug option
        self.debug_mode = debug_mode
        
        # read configuration from given file
        self.parse_configuration_file(self.iniFileName)
        
        # option to define an online coupling between PCR-GLOBWB and MODFLOW
        self.set_options_for_coupling_betweeen_pcrglobwb_and_modflow()

        # option for steady state only
        self.steady_state_only = steady_state_only
        # - modify output directory
        if self.steady_state_only:
            self.globalOptions['outputDir'] = self.globalOptions['outputDir'] + "/steady-state_only/"
        else:
            self.globalOptions['outputDir'] = self.globalOptions['outputDir'] + "/transient/"
        
        # set all paths, clean output when requested, initialize logging, copy ini file, make backup scripts, etc.
        self.set_configuration()

    def set_options_for_coupling_betweeen_pcrglobwb_and_modflow(self):

        # the default option is offline coupling procedure
        self.online_coupling_between_pcrglobwb_and_modflow = False

        if 'globalMergingAndModflowOptions' in self.allSections:

            if 'online_coupling_between_pcrglobwb_and_modflow' in self.globalMergingAndModflowOptions.keys() and\
               self.globalMergingAndModflowOptions['online_coupling_between_pcrglobwb_and_modflow'] == "True":\
               self.online_coupling_between_pcrglobwb_and_modflow = True

            # using the cloneMap and landmask as defined in the self.globalMergingAndModflowOptions:
            self.globalOptions['cloneMap'] = self.globalMergingAndModflowOptions['cloneMap']
            self.globalOptions['landmask'] = self.globalMergingAndModflowOptions['landmask']
            
            # the main output directory
            self.main_output_directory = self.globalOptions['outputDir']
            
            # the output directory for modflow calculation is stored
            self.globalOptions['outputDir'] = self.main_output_directory + "/modflow/"
            
            # temporary modflow output folder
            if 'tmp_modflow_dir' in self.globalMergingAndModflowOptions.keys():
                self.globalOptions['tmp_modflow_dir'] = self.globalMergingAndModflowOptions['tmp_modflow_dir']
			
			# water bodies file 
            if 'modflowParameterOptions' in self.allSections and\
               'waterBodyInputNC' not in self.modflowParameterOptions.keys():
                self.modflowParameterOptions['waterBodyInputNC'] = self.routingOptions['waterBodyInputNC']
			
            # option to use only natural water bodies:
            if 'modflowParameterOptions' in self.allSections and\
               'onlyNaturalWaterBodies' not in self.modflowParameterOptions.keys():
                self.modflowParameterOptions['onlyNaturalWaterBodies'] = self.routingOptions['onlyNaturalWaterBodies']
			
            # reportingOptions are taken from 'reportingForModflowOptions
            if 'reportingForModflowOptions' in self.allSections: self.reportingOptions = self.reportingForModflowOptions

    def set_configuration(self):

        # set all paths, clean output when requested
        self.set_input_files()
        self.create_output_directories()
        
        # initialize logging 
        self.initialize_logging()
        
        # copy ini file
        self.backup_configuration()

    def initialize_logging(self, log_file_location = "Default"):
        """
        Initialize logging. Prints to both the console and a log file, at configurable levels
        """

        # set root logger to debug level        
        logging.getLogger().setLevel(logging.DEBUG)

        # logging format 
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

        # default logging levels
        log_level_console    = "INFO"
        log_level_file       = "INFO"
        # order: DEBUG, INFO, WARNING, ERROR, CRITICAL
        
        # log level based on ini/configuration file:
        if "log_level_console" in self.globalOptions.keys():
            log_level_console = self.globalOptions['log_level_console']        
        if "log_level_file" in self.globalOptions.keys():
            log_level_file = self.globalOptions['log_level_file']        

        # log level for debug mode:
        if self.debug_mode == True: 
            log_level_console = "DEBUG"
            log_level_file    = "DEBUG"
        
        console_level = getattr(logging, log_level_console.upper(), logging.INFO)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_console)
        
        # create handler, add to root logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logging.getLogger().addHandler(console_handler)

        # log file name (and location)
        if log_file_location != "Default":  self.logFileDir = log_file_location
        log_filename = self.logFileDir + os.path.basename(self.iniFileName) + '_' + str(self._timestamp.isoformat()).replace(":",".") + '.log'

        file_level = getattr(logging, log_level_file.upper(), logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_file)

        # create handler, add to root logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logging.getLogger().addHandler(file_handler)
        
        # file name for debug log 
        dbg_filename = self.logFileDir + os.path.basename(self.iniFileName) + '_' +  str(self._timestamp.isoformat()).replace(":",".") + '.dbg'

        #create handler, add to root logger
        debug_handler = logging.FileHandler(dbg_filename)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(debug_handler)

        logger.info('Model run started at %s', self._timestamp)
        logger.info('Logging output to %s', log_filename)
        logger.info('Debugging output to %s', dbg_filename)
        
        # print disclaimer
        disclaimer.print_disclaimer(with_logger = True)
        
    def backup_configuration(self):
        
        # copy ini File to logDir:
        shutil.copy(self.iniFileName, self.logFileDir + \
                                     os.path.basename(self.iniFileName) + '_' +  str(self._timestamp.isoformat()).replace(":",".") + '.ini')

    def parse_configuration_file(self, modelFileName):

        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read(modelFileName)

        # all sections provided in the configuration/ini file
        self.allSections  = config.sections()
        
        # read all sections 
        for sec in self.allSections:
            vars(self)[sec] = {}                               # example: to instantiate self.globalOptions 
            options = config.options(sec)                      # example: logFileDir
            for opt in options:
                val = config.get(sec, opt)                     # value defined in every option 
                self.__getattribute__(sec)[opt] = val          # example: self.globalOptions['logFileDir'] = val
        
    def set_input_files(self):
        
        # full path for the clone map
        self.cloneMap = vos.getFullPath(self.globalOptions['cloneMap'], self.globalOptions['inputDir'])

    def create_output_directories(self):
        # making the root/parent of OUTPUT directory:
        cleanOutputDir = False
        if cleanOutputDir:
            try: 
                shutil.rmtree(self.globalOptions['outputDir'])
            except: 
                pass # for new outputDir (not exist yet)

        try: 
            os.makedirs(self.globalOptions['outputDir'])
        except: 
            pass # for new outputDir (not exist yet)

        # making temporary directory (needed for resampling process)
        self.tmpDir = vos.getFullPath("tmp/", \
                                      self.globalOptions['outputDir'])
        if os.path.exists(self.tmpDir):
            shutil.rmtree(self.tmpDir)
        os.makedirs(self.tmpDir)
        
        self.outNCDir = vos.getFullPath("netcdf/", \
                                         self.globalOptions['outputDir'])
        if os.path.exists(self.outNCDir):
            shutil.rmtree(self.outNCDir)
        os.makedirs(self.outNCDir)

        # making backup for the python scripts used:
        self.scriptDir = vos.getFullPath("scripts/", \
                                         self.globalOptions['outputDir'])
        if os.path.exists(self.scriptDir):
            shutil.rmtree(self.scriptDir)
        os.makedirs(self.scriptDir)
        self.path_of_this_module = os.path.abspath(os.path.dirname(__file__))
        for filename in glob.glob(os.path.join(self.path_of_this_module, '*.py')):
            shutil.copy(filename, self.scriptDir)

        # making log directory:
        self.logFileDir = vos.getFullPath("log/", \
                                          self.globalOptions['outputDir'])
        cleanLogDir = True
        if os.path.exists(self.logFileDir) and cleanLogDir:
            shutil.rmtree(self.logFileDir)
        os.makedirs(self.logFileDir)

        # making endStateDir directory
        # - this directory will contain the calculated groundwater head values
        self.endStateDir = vos.getFullPath("states/", \
                                           self.globalOptions['outputDir'])
        if os.path.exists(self.endStateDir):
            shutil.rmtree(self.endStateDir)
        os.makedirs(self.endStateDir)

        # making pcraster maps directory
        # - this directory will contain all variables/maps that will be used during the pcraster-modflow coupling
        self.mapsDir = vos.getFullPath("maps/", \
                                       self.globalOptions['outputDir'])
        cleanMapDir = True
        if os.path.exists(self.mapsDir) and cleanMapDir:
            shutil.rmtree(self.mapsDir)
        os.makedirs(self.mapsDir)
        
        # making temporary directory for modflow calculation and make sure that the directory is empty
        self.tmp_modflow_dir = "tmp_modflow/"
        if 'tmp_modflow_dir' in self.globalOptions.keys():
            self.tmp_modflow_dir = self.globalOptions['tmp_modflow_dir']
        self.tmp_modflow_dir = vos.getFullPath(self.tmp_modflow_dir, \
                                               self.globalOptions['outputDir'])+"/"
        if os.path.exists(self.tmp_modflow_dir):
            shutil.rmtree(self.tmp_modflow_dir)
        os.makedirs(self.tmp_modflow_dir)
        #
        # go to the temporary directory for the modflow calulation (so that all calculation will be saved in that folder)  
        os.chdir(self.tmp_modflow_dir)

