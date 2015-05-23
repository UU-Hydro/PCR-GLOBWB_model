#!/usr/bin/python
# -*- coding: utf-8 -*-

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

'''
Created on May 21, 2015

@author: Edwin H. Sutanudjaja

This file is to handle the configuration for modflow run. 


'''

class Configuration(object):

    def __init__(self, iniFileName, debug_mode = False, no_modification = True):
        object.__init__(self)

        # timestamp of this run, used in logging file names, etc
        self._timestamp = datetime.datetime.now()
        
        # get the full path of iniFileName
        self.iniFileName = os.path.abspath(iniFileName)

        # debug option
        self.debug_mode = debug_mode
        
        # read configuration from given file
        self.parse_configuration_file(self.iniFileName)
        
        # if no_modification, set configuration directly (otherwise, the function/method  
        if no_modification: self.set_configuration()

    def set_configuration(self):

        # set all paths, clean output when requested
        self.set_input_files()
        self.create_output_directories()
        
        # initialize logging 
        self.initialize_logging()
        
        # copy ini file
        self.backup_configuration()

        # repair key names of initial conditions
        self.repair_ini_key_names()
        

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

        # full paths for the folders/files mentioned in the modflowSteadyStateInputOptions
        for item in [
                     'avgDischargeInputMap',                       
                     'avgGroundwaterRechargeInputMap',             
                     'avgGroundwaterAbstractionInputMap',          
                     'avgGroundwaterAbstractionReturnFlowInputMap'
                     ]:
            if self.modflowSteadyStateInputOptions[item] != "None":\
               self.modflowSteadyStateInputOptions[item]  = vos.getFullPath(self.modflowSteadyStateInputOptions[item], self.globalOptions['inputDir'])

        # full paths for the folders/files mentioned in the modflowTransientInputOptions
        for item in [
                     'dischargeInputNC',                        
                     'groundwaterRechargeInputNC',              
                     'groundwaterAbstractionInputNC',           
                     'groundwaterAbstractionReturnFlowInputNC'
                     ]:
            if self.modflowTransientInputOptions[item] != "None":\
               self.modflowTransientInputOptions[item]  = vos.getFullPath(self.modflowSteadyStateInputOptions[item], self.globalOptions['inputDir'])

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

        # making temporary directory:
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
        
        path_of_this_module = os.path.abspath(os.path.dirname(__file__))
                           
        for filename in glob.glob(os.path.join(path_of_this_module, '*.py')):
            shutil.copy(filename, self.scriptDir)

        # making log directory:
        self.logFileDir = vos.getFullPath("log/", \
                                          self.globalOptions['outputDir'])
        cleanLogDir = True
        if os.path.exists(self.logFileDir) and cleanLogDir:
            shutil.rmtree(self.logFileDir)
        os.makedirs(self.logFileDir)

        # making endStateDir directory:
        self.endStateDir = vos.getFullPath("states/", \
                                           self.globalOptions['outputDir'])
        if os.path.exists(self.endStateDir):
            shutil.rmtree(self.endStateDir)
        os.makedirs(self.endStateDir)

        # making pcraster maps directory:
        self.mapsDir = vos.getFullPath("maps/", \
                                       self.globalOptions['outputDir'])
        cleanMapDir = True
        if os.path.exists(self.mapsDir) and cleanMapDir:
            shutil.rmtree(self.mapsDir)
        os.makedirs(self.mapsDir)
        
        # making temporary directory for modflow calculation and make sure that the directory is empty
        self.tmp_modflow_dir = vos.getFullPath("tmp_modflow/", \
                                                self.globalOptions['outputDir'])
        if os.path.exists(self.tmp_modflow_dir):
            shutil.rmtree(self.tmp_modflow_dir)
        os.makedirs(self.tmp_modflow_dir)
        #
        # go to the temporary directory for the modflow calulation (so that all calculation will be saved in that folder)  
        os.chdir(self.tmp_modflow_dir)
