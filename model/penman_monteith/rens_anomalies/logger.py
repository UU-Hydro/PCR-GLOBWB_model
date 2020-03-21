#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime
import logging

# logger object
logger = logging.getLogger(__name__)

class Logger(object):

    def __init__(self, output_folder, log_front_filename = None, cleanLogDir = False):
        object.__init__(self)

        # initialize logging and its properties 
        # (log file, debug level, format, etc.)
        self.initialize_logging(output_folder, log_front_filename, cleanLogDir)

    def initialize_logging(self, output_folder, log_front_filename = None, cleanLogDir = False):
        """
        Initialize logging. Prints to both the console and a log file
        """

        # make log folder and set log filename        
        log_folder = output_folder+"/"+"log/"
        if cleanLogDir: os.system('rm -r '+log_folder)
        os.system('mkdir '+log_folder)

        # set log filename
        log_filename = "log"
        if log_front_filename != None: log_filename = log_front_filename 
        self._start_timestamp = datetime.datetime.now()
        log_filename = log_filename + '_' + self._start_timestamp.isoformat() + '.log'
        log_filename = log_folder + "/" + log_filename

        # set root logger to debug level        
        logging.getLogger().setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

        # create CONSOLE handler, set format and set log level = INFO, add to root logger 
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(console_handler)

        # create CONSOLE handler, set format and set log level = INFO, add to root logger 
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(file_handler)
        
        logger.info('Calculation started at %s', self._start_timestamp)
        logger.info('Logging output to %s', log_filename)
        
