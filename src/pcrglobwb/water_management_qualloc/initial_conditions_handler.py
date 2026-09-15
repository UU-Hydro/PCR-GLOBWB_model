#!/usr/bin/python

"""

read_initial_conditions.py: module for setting the initial conditions.

"""

# TODO: include an update of the initial conditions to inherit warm states during spinup
# TODO: Make sure non-included components are not updated and initial settings remain consistent

###########
# modules #
###########
#-general modules and packages
import sys
import datetime
import logging

import pcraster as pcr

from copy import deepcopy

# specific packages
# only file handler is required
try:
    from .model_time     import match_date_by_julian_number
    from .netCDF_recipes import get_nc_dates
    from .file_handler   import file_is_nc, compose_filename, read_file_entry
except:
    from model_time     import match_date_by_julian_number
    from netCDF_recipes import get_nc_dates
    from file_handler   import file_is_nc, compose_filename, read_file_entry

########
# TODO #
########
critical_improvements= str.join('\n',\
             ( \
              '', \
              ))

development= str.join('\n\t',\
             ( \
              '',\
              '*** dictionaries of initial conditions can be saved but not be read correctly!',\
              '',\
              ))

print ('\nDevelopmens for caleros_runner:')

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

# inherit logger
logger = logging.getLogger(__name__)

# type set to identify None (compatible with pytyon 2.x)
NoneType = type(None)

# type set to identify PCRaster fields
pcrFieldType = pcr._pcraster.Field

#############
# functions #
#############

def test_timed_netcdf(filename, path = '', \
                           time_interval_days = 365):
    
    # function that tests whether the file is a timed netCDF file and what the
    # temporal spacing is
    
    # set the default values
    timed_netcdf = False
    nc_dates     = []
    
    # update the file name
    filename, file_exists = compose_filename(filename, path)
    
    # is it an existing netCDF?
   
    if file_is_nc(filename) and file_exists:

        # it is a netcdf file, now get the dates
        nc_dates = get_nc_dates(filename)

        # and decide on the content
        for ix in range(1, len(nc_dates)):
            
            delta_time = (nc_dates[ix] - nc_dates[ix - 1]).days

            timed_netcdf = timed_netcdf or (delta_time < time_interval_days)
            
    # return the output
    return timed_netcdf, nc_dates

def get_initial_conditions (model_configuration, \
                            date, \
                            ini_identifiers = ['_ini'], \
                            files_to_exclude = []):

    '''

get_initial_conditions: function to read the initial conditions that can be \
found in the model configuration file at the start of the model run.
All sections of the configuration file are read and those that are identified \
by the appropriate suffix are added to a dictionary in this class with the \
appropriate key and value pairs.

    Input:
    ======
    model_configuration    : class holding all the information that was parsed
                            from the configuration file that are organized as
                            dictionaries with key, value pairs; values are
                            strings that can refer to files with spatio-
                            temporal input or (alpha)numerical values; only
                            those that are identified as initial conditions
                            are read and copied as the initial_conditons;
    date:                   start date of the simulation which is used to find,
                            if relevant, the necessary temporal information in
                            the file;
    ini_identifiers        : list of possible suffixes identifying spinup values
                            in the model configuration object; input is optional
                            and the default identifier is '_ini', which should
                            be added to the key identifier, e.g. 
                            soil_moisture_ini.
    files_to_exclude       : list of files in the configuration file that must
                            be disregarded as initial conditions will be not be used

    Output:
    =======
    initial_conditions:     this is the copy of the model configuration with
                            the relevant info copied. Note that this can be
                            created at the start of the simulation with cold
                            states or reconstituted at the end of the
                            simulation with warm states.

'''

    # initialization
    # first, check on the ini_identifiers; this is only used in the init section
    for ini_identifier in ini_identifiers:
        ix = ini_identifiers.index(ini_identifier)
        if ini_identifier[0] != '_':
            ini_identifiers[ix] = str.join('', ('_', ini_identifier))

    # next, initialize the initial conditions
    initial_conditions = {}

    # iterate over the names and corresponding info in possible sections
    for section_name, section_info in vars(model_configuration).items():

        # process if this is a dictionary
        if isinstance(section_info, dict):
            
            # get the key value pair and process if it is identified as an
            # initial setting
            for key, entry in section_info.items():
                
                # check if an initial conditions is specified
                if len(key) > 4 and key not in files_to_exclude:
                    
                    # get suffix and variable name
                    suffix = key[-4:]
                    if suffix in ini_identifiers:
                        
                        # variable name in the netcdf is the same as the
                        # variable name in the configuration file
                        variablename = key[:-4]
                        
                        # if not included, add the section name to the
                        # initial condtions as an empty dictionary
                        if section_name not in initial_conditions.keys():
                            initial_conditions[section_name] = {}
                        
                        # next, decide on the processing of the data
                        timed_netcdf, nc_dates = test_timed_netcdf(entry, model_configuration.inputpath)
                        
                        if len(nc_dates) == 0: nc_dates = [date]
                        
                        # add a single field or a time series
                        if  timed_netcdf:
                            
                            # initialize the initial conditions as an empty dict,
                            # add the dates and the corresponding value
                            
                            initial_conditions[section_name][variablename] = {}
                            
                            for nc_date in nc_dates:
                                value = read_file_entry( \
                                        filename                = entry, \
                                        variablename            = variablename, \
                                        inputpath               = model_configuration.inputpath, \
                                        clone_attributes        = model_configuration.clone_attributes, \
                                        date                    = nc_date, \
                                        date_selection_method   = 'exact', \
                                        allow_year_substitution = True, \
                                        )
                                 
                                initial_conditions[section_name][variablename][nc_date] = value
                        
                        else:
                            
                            date_selection_method   = 'before'
                            allow_year_substitution = True
                            
                            if nc_dates[-1] >= date:
                                nc_date = nc_dates[-1]
                            else:
                                nc_date = date
                            
                            # get the value from the provided entry
                            value = read_file_entry( \
                                    filename                = entry, \
                                    variablename            = variablename, \
                                    inputpath               = model_configuration.inputpath, \
                                    clone_attributes        = model_configuration.clone_attributes, \
                                    date                    = nc_date, \
                                    date_selection_method   = date_selection_method, \
                                    allow_year_substitution = allow_year_substitution, \
                                    )
                            # next, add the value under the reduced key
                            initial_conditions[section_name][variablename] = value
                         
                        # log message
                        if isinstance(initial_conditions[section_name][variablename], pcrFieldType) or \
                                      isinstance(initial_conditions[section_name][variablename], dict):
                            logger.info('initial conditions for %s on %s successfully read' % \
                                          (variablename, date))
                        elif isinstance(initial_conditions[section_name][variablename], NoneType):
                            logger.warning('initial conditions for %s on %s unsuccessfully read and set to None' % \
                                          (variablename, date))
                            sys.exit()
                        else:
                            sys.exit('initial condition %s of %s cannot be read' % \
                                     (variablename, section_name))

    # all read, return the initial conditions
    return initial_conditions


def get_initial_condition_as_timed_dict( \
                                        initial_condition, \
                                        dates, \
                                        missing_value = None, \
                                        cover_value   = None, \
                                        pcr_data_func = pcr.scalar, \
                                        message_str   = '', \
                                        ):

    '''
get_initial_condition_as_timed_dict: function that checks whether the provided \
initial condition is a dictionary with dates as key; if not, a new timed \
dictionary is created; if it is timed, a selection based on the best possible \
date is generated.

    Input:
    ======
    initial_condition:          initial condition, expected to be a dictionary
                                with dates as keys and PCRaster fields as values;
                                in case, it is not, it can be cast as such
                                starting from None, a non-spatial value or a
                                single PCRaster field.
    dates:                      a sequence of dates in datetime format;
    missing_value:              a value that is used to create missing values
                                if the initial condition is a None type; default
                                is None, in which case the application of the
                                missing value is ignored, except whe the init-
                                ial condition is a None type and a value of
                                zero is used; missing value removal occurs
                                before the spatial field is covered;
    cover_value:                value that is applied to cover any missing
                                values; default is None, in which case missing
                                values are not covered;
    pcr_data_func:              PCRaster function that sets the data type,
                                default is scalar;
    message_str:                message_str that is used as a basis to log
                                the changes made; default is an empty string.
                                
    Output:
    =======
    initial_condition:          a dictionary of the initial condition with dates
                                as keys and PCRaster fields as values.

'''
    # check if the initial condition is a dictionary, create one if not
    if not isinstance(initial_condition, dict):    
        
        # create a dictionary
        value =  deepcopy(initial_condition)
        initial_condition = {dates[0]: value}

    # get the available dates of the initial condition
    available_dates = list(initial_condition.keys())
    available_dates.sort()

    # initialize the output initial condition
    initial_condition_dict = dict((date, None) for date in dates)
    
    # iterate over the dates and get the match and match string
    for date in dates:
        
        # get the date index
        date_index, matched_date, matched_str = match_date_by_julian_number(date, \
                                                available_dates)

        # add the matched date to the message string
        message_str = str.join('\n', (message_str, matched_str))

        # get the value
        value = initial_condition[matched_date]
    
        # update the value if it is not a PCRaster field
        if isinstance(value, NoneType):

            message_str = str.join('\n',\
                                    (message_str, \
                                    'initial condition contains a NoneType'))
            
            # set the initial condition to the missing value
            if isinstance(missing_value, NoneType):
                missing_value = 0

                message_str = str.join('\n',\
                                        (message_str, \
                                        'missing value is not defined, reset to zero'))

            # set the missing value
            value = pcr.spatial(pcr_data_func(missing_value))

        # check if the value is not a PCRaster field
        if not isinstance(value, pcrFieldType):
            try:
                value = pcr.spatial(pcr_data_func(value))
            except:
                sys.exit('ERROR: %s cannot be converted to a PCRaster field' % \
                         value)
            
            message_str = str.join('\n',\
                                    (message_str, \
                                    'initial condition is set from non-spatial information'))

        # and if it is non-spatial type, update
        if not value.isSpatial():
            value = pcr.spatial(value)
        
        # and cast as the right type, this is done always
        value = pcr_data_func(value)
        
        # remove missing values and cover
        if not isinstance(missing_value, NoneType):
            value = pcr.ifthen(value != pcr_data_func(missing_value), value)
        
        if not isinstance(cover_value, NoneType):
            value = pcr.cover(value, pcr_data_func(cover_value))
        
        # reset the value
        initial_condition[matched_date] = value
        
        # set the value for the date
        initial_condition_dict[date]    = value
        
    # log the message string
    logger.info(message_str)

    # return the updated initial condition
    return initial_condition_dict
