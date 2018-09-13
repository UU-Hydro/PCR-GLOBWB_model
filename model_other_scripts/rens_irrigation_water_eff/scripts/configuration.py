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
        
        # set all paths, clean output when requested
        self.set_input_files()
        self.create_output_directories()
        
        # initialize logging 
        self.initialize_logging()
        
        # copy ini file
        self.backup_configuration()

        # repair key names of initial conditions
        self.repair_ini_key_names()
        

    def initialize_logging(self):
        """
        Initialize logging. Prints to both the console and a log file, at configurable levels
        """

        #set root logger to debug level        
        logging.getLogger().setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

        log_level_console = "INFO"
        log_level_file    = "DEBUG"

        console_level = getattr(logging, log_level_console.upper(), logging.INFO)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_console)
        
        #create handler, add to root logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(console_handler)

        log_filename = self.logFileDir + os.path.basename(self.iniFileName) + '_' + self._timestamp.isoformat() + '.log'

        file_level = getattr(logging, log_level_file, logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_file)

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
        dirsAndFiles = ['precipitationNC', 'temperatureNC','refETPotFileNC']
        for item in dirsAndFiles:
            if self.meteoOptions[item] != "None":
                self.meteoOptions[item] = vos.getFullPath(self.meteoOptions[item], self.globalOptions['inputDir'])

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
        
        path_of_this_module = os.path.dirname(__file__)
                           
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
        
        # go to pcraster maps directory (so all pcr.report files will be saved in this directory) 
        os.chdir(self.mapsDir)


    def repair_ini_key_names(self):
        """
        Change key names for initial condition fields. 
        This is needed because Edwin was very stupid as once he changed some key names of initial conditions!  
        """

        # adjusment for routingOptions
        if 'routingMethod' not in self.routingOptions.keys():
            logger.info('WARNING !!! The "routingMethod" is not defined in the "routingOptions" of the configuration file. "accuTravelTime" is used in this run.')
            iniItems.routingOptions['routingMethod'] = "accuTravelTime"

        # adjusment for initial conditions in the routingOptions
        #
        if 'm2tChannelDischargeLongIni' in self.routingOptions.keys():
            self.routingOptions['m2tDischargeLongIni'] = self.routingOptions['m2tChannelDischargeLongIni']
        #
        if 'waterBodyStorageIni' not in self.routingOptions.keys():
            logger.info("Note that waterBodyStorageIni will be calculated from channelStorageIni.")
            self.routingOptions['waterBodyStorageIni'] = None
        #
        if 'avgChannelDischargeIni' in self.routingOptions.keys():
            self.routingOptions['avgDischargeLongIni'] = self.routingOptions['avgChannelDischargeIni']
        #
        if 'm2tChannelDischargeIni' in self.routingOptions.keys():
            self.routingOptions['m2tDischargeLongIni'] = self.routingOptions['m2tChannelDischargeIni']
        #
        if 'avgBaseflowIni' in self.routingOptions.keys():
            self.routingOptions['avgBaseflowLongIni'] = self.routingOptions['avgBaseflowIni']
        #
        if 'avgInflowLakeReservIni' in self.routingOptions.keys():
            self.routingOptions['avgLakeReservoirInflowShortIni'] = self.routingOptions['avgInflowLakeReservIni']
        #
        if 'avgOutflowDischargeIni' in self.routingOptions.keys():
            self.routingOptions['avgLakeReservoirOutflowLongIni'] = self.routingOptions['avgOutflowDischargeIni']
        #
        if 'avgDischargeShortIni' not in self.routingOptions.keys():
            logger.info('The initial condition "avgDischargeShortIni" is not defined. "avgDischargeLongIni" is used in this run.')
            self.routingOptions['avgDischargeShortIni'] = self.routingOptions['avgDischargeLongIni']
        #
        if 'avgSurfaceWaterInputLongIni' not in self.routingOptions.keys():
            logger.info("Note that avgSurfaceWaterInputLongIni is not used and not needed.")
            
        if 'subDischargeIni' not in self.routingOptions.keys() or self.routingOptions['subDischargeIni'] == str(None):
            msg  = 'The initial condition "subDischargeIni" is not defined. Either "avgDischargeShortIni" or "avgDischargeLongIni" is used in this run.'
            msg += 'Note that the "subDischargeIni" is only relevant if kinematic wave approaches are used.'
            logger.info(msg)
            self.routingOptions['subDischargeIni'] = self.routingOptions['avgDischargeShortIni']

        # TODO: repair key names while somebody wants to run 3 layer model but use 2 layer initial conditions (and vice versa). 
