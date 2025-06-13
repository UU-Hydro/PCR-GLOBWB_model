#!/usr/bin/env python
#  -*- coding: utf-8 -*-
########################################################################
#                                                                      #
# CALEROS Landscape Development Model:                                 #
#                                                                      #
# Copyright (c) 2019 Ludovicus P.H. (Rens) van Beek - r.vanbeek@uu.nl  #
# Department of Physical Geography, Faculty of Geosciences,            #
# Utrecht University, Utrecht, The Netherlands.                        #
#                                                                      #
# This program is free software: you can redistribute it and/or modify #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# This program is distributed in the hope that it will be useful,      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.#
#                                                                      #
# configuration: module with class and additional functions to handle   #
# the input from the configuration file and initialize the run, including#
# setting up paths, loggers and reporting.                             #
# output files for dynamic modelling.                                   #
# This development is part of the CALEROS landscape development.       #
#                                                                      #
########################################################################
"""
configuration:  
"""

import os
import sys
import stat
import shutil
import datetime
import logging

import pcraster as pcr

if sys.version[0] == '2':
    from ConfigParser import RawConfigParser as ConfigParser
else:
    from six.moves.configparser import RawConfigParser as ConfigParser

try:
    from .basic_functions import get_decision, \
                                 convert_string_to_list
except:
    from basic_functions import get_decision, \
                                convert_string_to_list

# global
logger = logging.getLogger(__name__)


########
# TODO #
########
critical_improvements= str.join('\n', \
             ( \
              '', \
              ))

development= str.join('\n\t', \
             ( \
              '', \
              'make a general function to process list', \
              '', \
              ))

print ('\nDevelopmens for model config class:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print ('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

####################
# global variables #
####################
    
NoneType = type(None)

#####################
# general functions #
#####################    

def remove_readonly(func, path, _):
    '''

clears the readonly bit and reattempt the removal"

'''

    stat_method = stat.FILE_ATTRIBUTE_NORMAL

    os.chmod(path, stat_method)
    func(path)

class configuration_parser(object):
    
    """

configuration_parser: 
object to parse the configuration file and  hold all information to run \
the CALEROS model.

"""

    def __init__(self, cfgfilename, sections= [], groups= [], \
                 debug_mode = False, subst_args = [],  **optional_arguments):
        
        # init object
        object.__init__(self)

        # echo message to screen
        message_str = '\n%s\nInitializing the QUAlloc model run\n%s\n' % \
            ('=' * 80, '=' * 80)
        print (message_str)

        # get the configuration file, groups, and secions
        self.cfgfilename = cfgfilename
        self.sections = sections
        self.groups = groups

        # timestamp of this run, used in logging file names, etc
        self._timestamp = datetime.datetime.now()
        self._timestamp_str = str(self._timestamp.isoformat())
        self._timestamp_str = self._timestamp_str[:self._timestamp_str.find('.')]
        self._timestamp_str = self._timestamp_str.replace(':','.') 

        # debug option
        self.debug_mode = debug_mode

        # save the initial root for later use
        self.start_root_path = os.path.abspath(os.path.dirname(__file__))

        # check whether argument substitution is required

        # read configuration from given file
        self.parse_configuration_file(self.cfgfilename, self.groups, \
                                    self.sections, subst_args)
        
        # with the configuration set, create all necessary directories
        self.create_output_directories()

        # copy the configuration file
        logfileroot = self.backup_configuration_file(self.cfgfilename, self.logpath, self._timestamp_str)

        # initialize the logger
        logfileroot = os.path.splitext(logfileroot)[0]
        self.initialize_logger(logfileroot)

        # logger initialized, add messages
        logger.info('Model run started at %s' % self._timestamp)
        logger.info('Logging output to %s'% self.logfilename)
        logger.info('Debugging output to %s'% self.dbgfilename)

    def __repr__(self):
        return 'this is an instance of the model configuration class object'

    def __str__(self):
        return 'this object contains information on the model configuration'

    def get_items(self, config, section):
        #-returns a dictionary of all key, value pairs in the current section
        options= {}
        for key, value in config.items(section):
            options[key]= value
        return options

    def parse_configuration_file(self, cfgfilename, groups, sections, subst_args):

        #-initialize and read config parser object
        config = ConfigParser()
        config.optionxform = str
        config.read(cfgfilename)
        sections_present= config.sections()
        #-process single, preset sections first
        for section in sections:
            #-check if section exists (is compulsory for the parameterization of the model)
            if config.has_section(section):
                #-remove the current section from the ones to be processed
                sections_present.remove(section)
                #-process all values
                try:
                    # section info
                    section_info = self.get_items(config, section)
                    # argument substitution 
                    for key, value in section_info.items():
                        if '$' in value:
                            # get the argument position and substitute
                            argposcnt = value.find('$')
                            argpos = int(value[argposcnt + 1:]) - 1
                            value  = str.join('', \
                                              (value[:argposcnt], \
                                               subst_args[argpos]))
                            # set the value
                            section_info[key] = value
                    # set the values
                    setattr(self, section, section_info)
                except:
                    message_str = 'processing information on the compulsory section [%s] raised an error' % \
                        (section)
                    sys.exit(message_str)
            else:
                message_str= 'configuration file does not contain information for the compulsory section [%s] ' % \
                        (section)
                sys.exit(message_str)
        #-process groups and any miscellaneous sections
        for group in groups:
            try:
                setattr(self, group, {})
            except:
                message_str = 'processing information on the group [%s] raised an error' % \
                    (group)
                sys.exit(message_str)
        for section in sections_present:
            try:
                #-get name and group name if present
                namelist = section.split(None, 1)
                for icnt in range(len(namelist)):
                    namelist[icnt]= namelist[icnt].strip()
                group = namelist[0]
                if group in groups:
                    #-group:
                    entryname = namelist[1]
                    section_info = getattr(self, group)[entryname]= {}
                else:
                    section = section.replace(' ','')
                    #-miscellaneous: section info
                    section_info = self.get_items(config, section)
                # argument substitution 
                for key, value in section_info.items():
                    if '$' in value:
                        try:
                            value = subst_args[int(value.lstrip('$')) - 1]
                        except:
                            message_str = 'argument substitution failed on %s in optional section %s' % \
                                (key, section)
                        # set the value
                        section_info[key] = value
                # set the values
                setattr(self, section, section_info)

            except:
                message_str = 'processing information on the section [%s] raised an error' % \
                    (section)
                sys.exit(message_str)
                
        #-test if the required entries for any of the groups are present
        for group in groups:
            if len(getattr(self, group).keys()) == 0:
                message_str = 'configuration file does not contain the necessary information on %s ' %  \
                        (group)
                sys.exit(message_str)

        # all data read, return None
        return None

    def initialize_logger(self, logfileroot):

        '''

initialize_logger: function that initializes the logger that prints messages \
to a log file and to the screen at configurable levels.

    '''

        # set root logger to debug level        
        logging.getLogger().setLevel(logging.DEBUG)

        # logging format 
        formatter = logging.Formatter( \
                '%(asctime)s %(name)s %(levelname)s %(message)s', \
                datefmt = '%m-%d %H:%M')

        # default logging levels
        log_level_console = 'INFO'
        log_level_file    = 'INFO'
        # order: DEBUG, INFO, WARNING, ERROR, CRITICAL
        
        # log level based on ini/configuration file:
        if 'log_level_console' in list(self.general.keys()):
            log_level_console = self.general['log_level_console']
        if 'log_level_file' in list(self.general.keys()):
            log_level_file = self.general['log_level_file']

        # log level for debug mode:
        if self.debug_mode == True: 
            log_level_console = 'DEBUG'
            log_level_file    = 'DEBUG'

        console_level = getattr(logging, log_level_console.upper(), logging.INFO)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_console)
        
        # create handler, add to root logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logging.getLogger().addHandler(console_handler)

        # log file name (and location)
        self.logfilename = str.join('', (logfileroot, '.log'))

        file_level = getattr(logging, log_level_file.upper(), logging.DEBUG)
        if not isinstance(console_level, int):
            raise ValueError('Invalid log level: %s', log_level_file)

        # create handler, add to root logger
        file_handler = logging.FileHandler(self.logfilename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logging.getLogger().addHandler(file_handler)
        
        # file name for debug log 
        self.dbgfilename = str.join('', (logfileroot, '.dbg'))

        # create handler, add to root logger
        debug_handler = logging.FileHandler(self.dbgfilename)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(debug_handler)

        # add the log file handlers
        self.log_file_handlers = [debug_handler, file_handler]

        # logger set up, return None
        return None


    def create_output_directories(self):
        '''
create_output_directories: function to create all the necessary output \
directories using information from the model configuration.

'''
        # start by checking the input and output path
        if not os.path.isabs(self.general['inputpath']):
            self.general['inputpath'] = os.path.abspath(self.general['inputpath'])
        if not os.path.isdir(self.general['inputpath']):
            message_str = 'input path %s does not exist' % \
                (self.general['inputpath'])
            sys.exit(message_str)

        if not os.path.isabs(self.general['outputpath']):
            self.general['outputpath'] = os.path.abspath(self.general['outputpath'])

        # create the output path if it does not exist
        if not os.path.isdir(self.general['outputpath']):
            os.makedirs(self.general['outputpath'])
            message_str = 'output path %s does not exist and is created'  % \
                (self.general['outputpath'])
            print (message_str)

        # create short names to root of input and output directory
        self.inputpath  = self.general['inputpath']
        self.outputpath = self.general['outputpath']

        # create the temporary directory that serves as the working directory
        # and the log, script, netCDF, states, and table directories
        subdirectories =  [ \
            os.path.join(self.outputpath, subdirectory) \
            for subdirectory in ['temp', 'netcdf', 'scripts', 'log', \
                                 'states', 'summary', 'maps']]
        
        # test on existing directories and file input
        files_exist = False
        for subdirectory in subdirectories:
            if os.path.isdir(subdirectory) and not files_exist:
                files_exist = files_exist or (len(os.listdir(subdirectory)) > 0)
        
        # decide on progressing if files exist
        
        possible_outcomes = {'yes': True, 'no': False}
        if files_exist and self.general['overwrite_output'] == 'False':
            question_str = str.join(' ', \
                    ('WARNING: Output directory already exists.', \
                     'Continuing will overwrite existing data:', \
                     'do you want to continue?'))
            result = get_decision(question_str, possible_outcomes)
            
            if result:
                question_str = str.join(' ', \
                        ('WARNING: All existing data will be overwritten.', \
                         'Are you sure?'))
                result = get_decision(question_str, possible_outcomes)

                # decsion made if result is not yes, halt!                
                if not result:                    
                    sys.exit('run halted!')
                else:
                    print ('run continues, existing data are overwritten')
            else:
                sys.exit('run halted!')

        # continue: create the subdirectories
        # and add them to the object
        for subdirectory in subdirectories:            
            subdirname = '%spath' % os.path.split(subdirectory)[1]
            # add or empty
            if os.path.isdir(subdirectory):
                # empty the directory
                shutil.rmtree(subdirectory, onerror = remove_readonly)
            # add the subdirectory and add it to the object
            os.makedirs(subdirectory)
            setattr(self, \
                    subdirname, subdirectory)

        # all directories created, return None
        return None

    def backup_configuration_file(self, cfgfilename, \
            outputpath, replacement_str = ''):

        # copies the configuration file
        fn = os.path.split(cfgfilename)[1]
        fn, ext = os.path.splitext(fn)
        
        fn = str.join('', \
            (fn, '_', replacement_str, ext))
        fn = os.path.join(outputpath, fn)
        
        shutil.copy(cfgfilename, fn)
        
        # return a string of the backup config file
        return fn

    def convert_string_to_input(self, val_str, ftype, **kwargs):

        
        # initialize the separators
        separators = [',']
        
        # test data type
        if not isinstance(ftype, type):
            logger.error('data type %s is not a data type' % ftype)
            sys.exit()

        # initialize value
        value = None

        # test if the val_str is None
        if isinstance(val_str, NoneType) or \
                val_str.lower() == 'none':
            # set value to None
            value = None

        elif ftype == bool:

            if val_str.lower() == 'true':
                value = True
            else:
                value = False
        
        else:
            # test if the value is a list
            possible_list = False
            
            for separator in separators:
            
                possible_list = possible_list or separator in val_str
                        
            if possible_list:
                
                # get the list entries
                value = convert_string_to_list(val_str, separators)

                # get the entry and convert it to the right data type
                for ix in range(len(value)):
                    value[ix] = ftype(value[ix])

                # logger
                logger.warning('include additional separators and data type conversion!')

                
            else:
                
                # get the value for a single entry
                try:
                    value = ftype(val_str)
                except:
                    logger.error('%s cannot be converted to %s' % \
                                 (val_str, ftype))
        # return the value
        return value
        
        
#    def convert_string_to_value(self, x, datatype):
#        '''
#
# convert_string_to_value: function that reads the string of variable x 
#from the configuration file to  the format specified; this may be an integer 
#or float or any PCRaster format.
#
#        '''
#        if datatype == 'float':
#            try:
#                return float(x)
#            except:
#                message_str = 'variable %s cannot be converted to a float' % x
#                sys.exit(logger.info(message_str))
#        elif 'int' in datatype[:3]:
#            try:
#                return int(x)
#            except:
#                message_str = 'variable %s cannot be converted to an integer' % x
#                sys.exit(logger.info(message_str))
#        elif datatype == 'bool':
#            if 'false' in x.lower():
#                return false
#            elif 'true' in x.lower():
#                return true
#            else:
#                message_str = 'variable %s cannot be converted to a bool' % x
#                sys.exit(logger.info(message_str))
#        elif datatype in ['boolean','ldd','nominal',
#                'ordinal','scalar','directional']:
#            try:
#                m = pcr.spatial(pcr.scalar(float(x)))
#            except:
#                try:
#                    m = pcr.readmap(x)
#                except:
#                    message_str = 'variable %s is not of type specified' % x
#                    sys.exit(logger.info(message_str))
#            if datatype == 'scalar':
#                return pcr.scalar(m)
#            elif datatype == 'boolean':
#                return pcr.boolean(m)
#            elif datatype == 'ldd':
#                return pcr.ldd(m)
#            elif datatype == 'nominal':
#                return pcr.nominal(m)
#            elif datatype == 'ordinal':
#                return pcr.ordinal(m)
#            elif datatype == 'directional':
#                return pcr.directional(m)
#        #-none of the possible types encountered, return no value
#        else:
#            message_str = 'variable %s cannot be converted to a value' % x
#            sys.exit(logger.info(message_str))

#    def convert_to_list(self, s, separators= [',',';']):
#        '''
#        
#convert_to_list: function that converts a string (s) of entries separated by \
#the listed default separators into a list and returns it.
#
#        '''
#        
#        #-create initial list from string
#        list_constructor = create_list_constructor(s, separators)
#        return construct_list_from_dictionary(list_constructor, \
#                    result_list)
#
#    def convert_to_dictionary(self, keys, values, keywords = []):
#    
#        '''
#convert_to_dictionary: function that converts the arguments into a dictionary:
# 
#    Input:
#    ======
#    keys:               list of keys to be used in the dictionary;
#    values:             either a list of the same length as keys or a 
#                        dictionary that is ordered at its highest level by keys;
#    keywords:           a single key or list of keys to be extracted from 
#                        values if this is a dictionary
#
#    Output:
#    =======
#    sequence:           dictionary or list, depending on the availability of
#                        keys and the nature of values
#
#        '''
#
#        if isinstance(values,list):
#            if len(keys) == len(values):
#                return dict([(keys[iCnt],values[iCnt]) for iCnt in xrange(len(keys))])
#            else:
#                    sys.exit('no dictionary could be created from the information specified')
#        elif isinstance(values,dict):
#            for key in keys:
#                if not key in values.keys():
#                    sys.exit('keys do not match')
#            if isinstance(values[keys[0]],dict):
#                x = {}
#                for key in keys:
#                    if isinstance(keywords,list):
#                        x[key] = {}
#                        for keyword in keywords:
#                            x[key][keyword] = values[key][keyword]
#                    elif isinstance(keywords,str):
#                        x[key] = values[key][keywords]
#                return x
#            else:
#                return values
#        else:
#                sys.exit('no dictionary could be created from the information specified')

#    def convert_sequence_to_values(self, seq, f, data_type):
#        
#        '''
#
#convert_sequence_to_values: function that translates a mutable sequence 
#consisting of strings into values according to the datatype specified.
#
#        '''
#        
#        if isinstance(seq,list):
#            seq = seq[:]
#            for index in xrange(len(seq)):
#                if not isinstance(seq[index], list) and \
#                         not isinstance(seq[index], dict):
#                    try:
#                        value = f(seq[index], data_type)
#                    except:
#                        value = seq[index]
#                    seq[index] = value
#                else:
#                    seq[index] = self.convert_sequence_to_values(seq[index], f, data_type)
#        elif isinstance(seq,dict):
#            seq = seq.copy()
#            for key in seq.keys():
#                if not isinstance(seq[key], list) and \
#                         not isinstance(seq[key], dict):
#                    try:
#                        value = f(seq[key], data_type)
#                    except:
#                        value = seq[key]
#                    seq[key] = value
#                else:
#                    seq[key] = self.convert_sequence_to_values(seq[key], f, data_type)
#        return seq

    # /end of class definition of model configuration object/

###############################################################################
# end of the module with functions required initialize the model              #
# configuration object                                                        #
###############################################################################
