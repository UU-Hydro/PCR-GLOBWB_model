#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
import optparse
import os
import sys
import virtualOS as vos
import time
import datetime
import logging
import shutil
import glob

logger = logging.getLogger(__name__)


    

class Configuration(object):

    def __init__(self):
        object.__init__(self)

        # timestamp of this run, used in logging file names, etc
        self._timestamp = datetime.datetime.now()
        
        # reading configuration file name from command line arguments
        # Note: this may not be very useful
        usage = 'usage: %prog [options] <model options> '
        parser = optparse.OptionParser(usage=usage)
        (options, arguments) = parser.parse_args()

        self.iniFileName = os.path.abspath(arguments[0])
        
        # read configuration from given file
        self.parse_configuration_file(self.iniFileName)
        
        #set all paths, clean output when requested
        self.set_input_files()
        self.create_output_directories()
        
        self.initialize_logging()
        
        self.backup_configuration()
        

    def initialize_logging(self):
        """
        Initialize logging. Prints to both the console and a log file, at configurable levels
        """

        #set root logger to debug level        
        logging.getLogger().setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

        console_level = getattr(logging, self.globalOptions['log_level_console'].upper(), logging.INFO)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', self.globalOptions['log_level_console'])
        
        #create handler, add to root logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(console_handler)

        log_filename = self.logFileDir + os.path.basename(self.iniFileName) + '_' + self._timestamp.isoformat() + '.log'

        file_level = getattr(logging, self.globalOptions['log_level_file'], logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', self.globalOptions['log_level_file'])

        #create handler, add to root logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logging.getLogger().addHandler(file_handler)
        
        logger.info('Model run started at %s', self._timestamp)
        logger.info('Logging output to %s', log_filename)
        
    def backup_configuration(self):
        
        # copy ini File to logDir:
        
        shutil.copy(self.iniFileName, self.logFileDir + \
                                     os.path.basename(self.iniFileName) + '_' + self._timestamp.isoformat() + '.ini')

    def parse_configuration_file(self, modelFileName):
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.sections()
        config.read(modelFileName)
        for sec in config.sections():
            options = config.options(sec)  # example: logFileDir
            vars(self)[sec] = {}  # example: to instantiate self.globalOptions 
            for opt in options:
                val = config.get(sec, opt)
                self.__getattribute__(sec)[opt] = val
    
    def set_input_files(self):
        # fullPath of CLONE:
        self.cloneMap = vos.getFullPath(self.globalOptions['cloneMap'], \
                                        self.globalOptions['inputDir'])

        # Get the fullPaths of the INPUT directories/files mentioned in 
        #      a list/dictionary:         
        dirsAndFiles = ['precipitationNC', 'temperatureNC']
        for item in dirsAndFiles:
            if self.meteoOptions[item] != "None":
                self.meteoOptions[item] = vos.getFullPath(self.meteoOptions[item], self.globalOptions['inputDir'])

    def create_output_directories(self):
        # making the root/parent of OUTPUT directory:
        if self.globalOptions['cleanOutputDir'] == "True":
            try: 
                shutil.rmtree(self.globalOptions['outputDir'])
            except: 
                pass # for new outputDir (not exist yet)

        try: 
            os.makedirs(self.globalOptions['outputDir'])
        except: 
            pass # for new outputDir (not exist yet)

        # making temporary directory:
        self.tmpDir = vos.getFullPath(self.globalOptions['tmpDir'], \
                                      self.globalOptions['outputDir'])
        
        if os.path.exists(self.tmpDir):
            shutil.rmtree(self.tmpDir)
        os.makedirs(self.tmpDir)
        
        self.outNCDir = vos.getFullPath(self.globalOptions['outputNCDir'], \
                                         self.globalOptions['outputDir'])
        if os.path.exists(self.outNCDir):
            shutil.rmtree(self.outNCDir)
        os.makedirs(self.outNCDir)

        # making backup for the python scripts used:
        self.scriptDir = vos.getFullPath(self.globalOptions['backupScriptDir'], \
                                         self.globalOptions['outputDir'])

        if os.path.exists(self.scriptDir):
            shutil.rmtree(self.scriptDir)
        os.makedirs(self.scriptDir)
        
        path_of_this_module = os.path.dirname(__file__)
                           
        for filename in glob.glob(os.path.join(path_of_this_module, '*.py')):
            shutil.copy(filename, self.scriptDir)

        # making log directory:
        self.logFileDir = vos.getFullPath(self.globalOptions['logFileDir'], \
                                          self.globalOptions['outputDir'])
        
        
        if os.path.exists(self.logFileDir) and self.globalOptions['cleanLogDir'] == "True":
            shutil.rmtree(self.logFileDir)
        os.makedirs(self.logFileDir)

        # making endStateDir directory:
        self.endStateDir = self.globalOptions['endStateDir']
        if self.endStateDir != "None":
            self.endStateDir = vos.getFullPath(self.endStateDir, \
                                  self.globalOptions['outputDir'])
            if os.path.exists(self.endStateDir) and self.globalOptions['cleanEndStateDir'] == "True":
                shutil.rmtree(self.endStateDir)
            os.makedirs(self.endStateDir)

