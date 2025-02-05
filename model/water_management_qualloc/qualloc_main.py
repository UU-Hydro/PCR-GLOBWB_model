#!/usr/bin/env python
#  -*- coding: utf-8 -*-

###########
# Modules #
###########
#-standard modules
import os, sys
import datetime
import logging

import pcraster as pcr
from copy import deepcopy
from spatialDataSet2PCR import spatialAttributes, setClone

# modules from the QUAlloc model
from basic_functions import sum_list, pcr_return_val_div_zero
from file_handler import compose_filename, read_file_entry, close_nc_cache
from initial_conditions_handler import get_initial_conditions, get_initial_condition_as_timed_dict
from qualloc_reporting import  qualloc_report_initial_conditions

from groundwater      import groundwater
from surfacewater     import surfacewater
from water_management import water_management, water_management_missing_value, very_small_number
from water_quality    import water_quality, water_quality_forcing_variables, unattainable_threshold

# test
from allocation import get_key
from model_time import match_date_by_julian_number

# global variables
logger = logging.getLogger(__name__)

# path out for debugging
path = '/scratch/carde003/qualloc/__debug'
verbose = False

########
# TODO #
########
critical_improvements= str.join('\n\t',\
             ( \
              '',\
              ))

development= str.join('\n\t',\
             ( \
              '', \
              'streamline input: should be able to read config files but also floats etc.', \
              'add flags!', \
              'include the functions to read the initial conditions and return them!\n', \
              'at the moment domestic, industrial and livestock water demand are read from ', \
              'a single netCDF file as is the case in PCR-GLOBWB to provide the gross and net ', \
              'water demand for these sectors(Gross, Netto sic); for clarity, these entries ', \
              'could be split out here explicitly rather than doing this under the hood in ', \
              'the main; however, a lookup table may still be required to manage the various ', \
              'variable names in the original netCDF files that could be managed more clearly via the cfg file.', \
              '', \
              ))

print ('\nDevelopmens for main module:')

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

# type set to identify None (compatible with python 2.x)
NoneType     = type(None)

# set the default list of forcing variables
forcing_variables = { \
                      'precipitation'             : 'precipitation', \
                      'referencePotET'            : 'refpot_evaporation', \
                      'groundwater_recharge'      : 'groundwater_recharge', \
                      'direct_runoff'             : 'direct_runoff', \
                      'interflow'                 : 'interflow', \
                      'irrigation_gross_demand'   : 'irrigation_water_demand', \
                      'domesticGrossDemand'       : 'domestic_water_demand', \
                      'domesticNettoDemand'       : 'domestic_water_demand', \
                      'industryGrossDemand'       : 'industrial_water_demand', \
                      'industryNettoDemand'       : 'industrial_water_demand', \
                      'livestockGrossDemand'      : 'livestock_water_demand', \
                      'livestockNettoDemand'      : 'livestock_water_demand', \
                      'manufactureGrossDemand'    : 'manufacture_water_demand', \
                      'manufactureNettoDemand'    : 'manufacture_water_demand', \
                      'thermoelectricGrossDemand' : 'thermoelectric_water_demand', \
                      'thermoelectricNettoDemand' : 'thermoelectric_water_demand', \
                      'environment_gross_demand'  : 'environment_water_demand', \
                      'desalinated_water_use'     : 'desalinated_water_use',\
                    }

#############
# functions #
#############

#///model start///#

class qualloc_model(object):
    
    ##################
    # initialization #
    ##################
    def __init__(self, \
                  model_configuration, \
                  model_time, \
                  model_flags = {}, \
                  initial_conditions = None):

        # initialize the object
        object.__init__(self)

        ######################
        # model settings     #
        # initial conditions #
        # and model flags    #
        ######################
        # model configuration and settings
        self.model_configuration = model_configuration
        
        # model settings
        self.model_flags = model_flags
        
        self.model_flags['water_quality_flag'] = False
        if 'water_quality' in vars(self.model_configuration).keys():
            self.model_flags['water_quality_flag'] = \
                eval(self.model_configuration.water_quality['water_quality_flag'])
        
        self.model_flags['groundwater_pumping_capacity_flag'] = False
        if 'groundwater_regional_pumping_capacity' in self.model_configuration.water_management.keys() and \
           self.model_configuration.water_management['groundwater_regional_pumping_capacity'] != 'None':
            self.model_flags['groundwater_pumping_capacity_flag'] = True
        
        self.model_flags['surfacewater_pumping_capacity_flag'] = False
        if 'surfacewater_regional_pumping_capacity' in self.model_configuration.water_management.keys() and \
           self.model_configuration.water_management['surfacewater_regional_pumping_capacity'] != 'None':
            self.model_flags['surfacewater_pumping_capacity_flag'] = True
        
        self.model_flags['desalinated_water_use_flag'] = False
        if 'desalinated_water_use_flag' in self.model_configuration.water_management.keys():
            self.model_flags['desalinated_water_use_flag'] = \
                eval(self.model_configuration.water_management['desalinated_water_use_flag'])
        
        # initial conditions: this is a class that holds all the initial conditions
        self.modules = ['surfacewater','groundwater','water_management','water_quality']
        self.initial_conditions = initial_conditions
        
        ##############
        # model time #
        ##############
        self.model_time = model_time
        
        #########
        # clone #
        ######### 
        # add the spatial attributes to the set the clone
        clone_file, file_exists = \
               compose_filename(model_configuration.general['clone'], \
                               model_configuration.inputpath)
        if file_exists:
            setattr(self.model_configuration, \
                    'clone_attributes', spatialAttributes(clone_file))
            setClone(self.model_configuration.clone_attributes)
        else:
            sys.exit('clone file %s does not exist' % clone_file)
        
        message_str = str.join('\n', \
            ('', \
            '', \
            '#' * 80, \
            '# %-76s #' % ('QUAlloc water use and allocation model'), \
            '#' * 80, \
            '', \
            '', \
            ))
        logger.info(message_str)
        
        message_str = 'run started at %s for %s over %s - %s using %s time increments' % \
            (self.model_configuration._timestamp_str, \
             self.model_configuration.general['scenarioname'], \
             self.model_time.date, \
             self.model_time.enddate, \
             self.model_time.time_increment)
        logger.info(message_str)
        
        # returns None
        return None
    
    def initialize(self):
        
        # read in the land mask
        self.landmask = read_file_entry( \
                filename                 = self.model_configuration.general['clone'], \
                variablename            = 'landmask', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Boolean, \
                )
        
        # read in the cell area
        self.cellarea = read_file_entry( \
                filename                 = self.model_configuration.general['cellarea'], \
                variablename            = 'cellarea', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        
        # verify use of water quality section
        sections_to_exclude = []
        
        # set the initial conditions
        if isinstance(self.initial_conditions, NoneType):
            # get the initial warm states
            self.initial_conditions = \
                    get_initial_conditions(self.model_configuration, \
                                           self.model_time.startdate, \
                                           sections_to_exclude = sections_to_exclude)
        
        # initialize the module to report the initial conditions
        self.report_initial_conditions_to_file = qualloc_report_initial_conditions( \
                                      self.model_configuration, \
                                      self.initial_conditions, \
                                      self.model_flags)
        
        # initialize the forcing data set
        # this contains all the necessary dynamic input that varies for the
        # selected time step
        inputpath               = self.model_configuration.general['inputpath']
        allow_year_substitution = True       #False
        date_selection_method   = 'exact'    #'nearest'
        datatype                = pcr.Scalar
        
        # get the totals and rates
        forcing_totals = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.forcing['totals'], str)
        forcing_rates = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.forcing['rates'], str)
        
        # purge forcing variables
        del_keys = []
        for forcing_variable, ncfileroot in forcing_variables.items():
            if f'{ncfileroot}_ncfile' not in self.model_configuration.forcing.keys():
                del_keys.append(forcing_variable)
        for del_key in del_keys:
            forcing_variables.pop(del_key, None)
        
        # add to cache forcing information
        self.forcing_info = {}
        for forcing_variable, ncfileroot in forcing_variables.items():
            
            # set the nc file name
            ncfilename = self.model_configuration.forcing['%s_ncfile' % ncfileroot]
            
            # check on the type of variable
            if   ncfileroot in forcing_totals:
                    total_to_rate = True
            elif  ncfileroot in forcing_rates:
                    total_to_rate = False
            else:
                    total_to_rate = False
            
            # set the information
            self.forcing_info[forcing_variable] = \
                            { \
                             'ncfilename'              : ncfilename, \
                             'inputpath'               : inputpath, \
                             'datatype'                : datatype, \
                             'date_selection_method'   : date_selection_method, \
                             'allow_year_substitution' : allow_year_substitution, \
                             'total_to_rate'           : total_to_rate, \
                            }
        
        logger.info('forcing information initialized')
        
        # initialize the modules
        
        # [ groundwater ]
        # read in the groundwater alpha and the initial groundwater storage
        self.initial_conditions['groundwater']['groundwater_storage'] = pcr.ifthen(self.landmask, \
                    pcr.cover(self.initial_conditions['groundwater']['groundwater_storage'], 0))
        alpha = read_file_entry( \
                filename                 = self.model_configuration.groundwater['alpha'], \
                variablename            = 'alpha', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        alpha_default = read_file_entry( \
                filename                 = self.model_configuration.groundwater['alpha_default'], \
                variablename            = 'alpha', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        alpha = pcr.ifthen(self.landmask, pcr.cover(alpha, alpha_default))

        # initialize the groundwater module
        self.groundwater = groundwater(alpha              = alpha, \
                                       total_base_flow_ini = self.initial_conditions['groundwater']['total_base_flow'], \
                                       storage_ini        = self.initial_conditions['groundwater']['groundwater_storage'])
        
        # remove alpha, alpha_default
        alpha = None; alpha_default = None
        del alpha, alpha_default
        
        # [ surfacewater ]
        # read in the ldd, fractional water area and channel properties
        # and the initial surface water storage
        self.initial_conditions['surfacewater']['surfacewater_storage'] = \
                pcr.ifthen(self.landmask, \
                           pcr.cover(self.initial_conditions['surfacewater']['surfacewater_storage'], 0))
        ldd = read_file_entry( \
                filename                = self.model_configuration.surfacewater['ldd'], \
                variablename            = 'ldd', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Ldd, \
                )
        fraction_water = read_file_entry( \
                filename                = self.model_configuration.surfacewater['fraction_water'], \
                variablename            = 'fraction_water', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        water_cropfactor=  read_file_entry( \
                filename                = self.model_configuration.surfacewater['water_cropfactor'], \
                variablename            = 'water_cropfactor', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        channel_gradient = read_file_entry( \
                filename                = self.model_configuration.surfacewater['channel_gradient'], \
                variablename            = 'channel_gradient', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        channel_width = read_file_entry( \
                filename                = self.model_configuration.surfacewater['channel_width'], \
                variablename            = 'channel_width', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        channel_length = read_file_entry( \
                filename                = self.model_configuration.surfacewater['channel_length'], \
                variablename            = 'channel_length', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        mannings_n = read_file_entry( \
                filename                = self.model_configuration.surfacewater['mannings_n'], \
                variablename            = 'mannings_n', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        
        # initialize the surface water module
        self.surfacewater = surfacewater( \
                                         ldd              = ldd, \
                                         cellarea         = self.cellarea, \
                                         fraction_water   = fraction_water, \
                                         water_cropfactor = water_cropfactor, \
                                         channel_gradient = channel_gradient,
                                         channel_width    = channel_width, \
                                         channel_length   = channel_length, \
                                         mannings_n       = mannings_n, \
                                         storage_ini      = self.initial_conditions['surfacewater']['surfacewater_storage'], \
                                         )
        
        # remove the  ldd, fractional water area and channel properties
        ldd = None; fraction_water = None; water_cropfactor = None; channel_gradient = None
        channel_width = None; channel_depth = None; channel_length = None
        mannings_n = None
        del ldd, fraction_water, water_cropfactor, channel_gradient, channel_width, \
            channel_depth, channel_length, mannings_n
        
        # [ water management ]
        # read in the sectors, sources and withdrawals
        sector_names = ['irrigation','domestic','industry','livestock']
        if 'sector_names' in self.model_configuration.water_management.keys():
            sector_names = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.water_management['sector_names'], str)
        
        source_names = ['groundwater','surfacewater']
        if 'source_names' in self.model_configuration.water_management.keys():
            source_names = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.water_management['source_names'], str)
        
        withdrawal_names = ['renewable','nonrenewable']
        if 'withdrawal_names' in self.model_configuration.water_management.keys():
            withdrawal_names = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.water_management['withdrawal_names'], str)
        
        # read in the weights
        groundwater_update_weight        = read_file_entry( \
                filename                  = self.model_configuration.water_management['groundwater_update_weight'], \
                variablename             = 'groundwater_update_weight', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Scalar, \
                )
        surfacewater_update_weight       = read_file_entry( \
                filename                  = self.model_configuration.water_management['surfacewater_update_weight'], \
                variablename             = 'surfacewater_update_weight', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Scalar, \
                )
        
        # allocation zones
        # read in the allocation zones
        groundwater_allocation_zones     = read_file_entry( \
                filename                  = self.model_configuration.water_management['groundwater_allocation_zones'], \
                variablename             = 'groundwater_allocation_zones', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Nominal, \
                ) 
        surfacewater_allocation_zones    = read_file_entry( \
                filename                  = self.model_configuration.water_management['surfacewater_allocation_zones'], \
                variablename             = 'surfacewater_allocation_zones', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Nominal, \
                )
        desalwater_allocation_zones      = read_file_entry( \
                filename                  = self.model_configuration.water_management['desalwater_allocation_zones'], \
                variablename             = 'desalwater_allocation_zones', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Nominal, \
                )
        groundwater_allocation_zones     = pcr.ifthen(self.landmask & (groundwater_allocation_zones != 0), \
                                                     groundwater_allocation_zones)
        surfacewater_allocation_zones    = pcr.ifthen(self.landmask & (surfacewater_allocation_zones != 0), \
                                                     surfacewater_allocation_zones)
        desalwater_allocation_zones      = pcr.ifthen(self.landmask & (desalwater_allocation_zones != 0), \
                                                     desalwater_allocation_zones)
            
        # read in the withdrawal points
        groundwater_withdrawal_points    = read_file_entry( \
                filename                  = self.model_configuration.water_management['groundwater_withdrawal_points'], \
                variablename             = 'groundwater_withdrawal_points', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Ordinal, \
                )
        surfacewater_withdrawal_points   = read_file_entry( \
                filename                  = self.model_configuration.water_management['surfacewater_withdrawal_points'], \
                variablename             = 'surfacewater_withdrawal_points', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Ordinal, \
                )
        desalwater_withdrawal_points     = read_file_entry( \
                filename                  = self.model_configuration.water_management['desalwater_withdrawal_points'], \
                variablename             = 'desalwater_withdrawal_points', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Ordinal, \
                )
        groundwater_withdrawal_points    = pcr.cover(groundwater_withdrawal_points, 0)
        surfacewater_withdrawal_points   = pcr.cover(surfacewater_withdrawal_points, 0)
        desalwater_withdrawal_points     = pcr.cover(desalwater_withdrawal_points, 0)
        
        # read in the withdrawal capacity
        groundwater_withdrawal_capacity  = read_file_entry( \
                filename                  = self.model_configuration.water_management['groundwater_withdrawal_capacity'], \
                variablename             = 'groundwater_withdrawal_capacity', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Scalar, \
                ) 
        surfacewater_withdrawal_capacity = read_file_entry( \
                filename                  = self.model_configuration.water_management['surfacewater_withdrawal_capacity'], \
                variablename             = 'surfacewater_withdrawal_capacity', \
                inputpath                = self.model_configuration.general['inputpath'], \
                clone_attributes         = self.model_configuration.clone_attributes, \
                datatype                 = pcr.Scalar, \
                )
        
        # long-term water availability
        # at time intervals idenfied by dates; this is organized as a dictionary 
        # with the dates as key and maps of long-term water availability as values 
        # and is read by the initial conditions module. By default, a NoneType value 
        # is provided or a single map / value can be provided. In those cases, a 
        # dictionary is created with missing values for those cells for which no 
        # values are defined.
        
        # set dummy year and create a list of corresponding dates for the water
        # management module; this currently only allows for monthly intervals
        dummy_year = self.model_time.startdate.year
        water_management_dates = [datetime.datetime(dummy_year, month, 1) for month in range(1, 13)]
        
        # set the long-term groundwater availability by the long-term base flow (units: m/day)
        self.initial_conditions['water_management']['groundwater_longterm_storage']  = \
                    get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                          ['groundwater_longterm_storage'], \
                    water_management_dates, \
                    missing_value = water_management_missing_value, \
                    message_str   = 'Setting initial long-term groundwater storage')
        
        # set the long-term surface water availability by the long-term 
        # discharge (units: m3/s) and the long-term total runoff (units: m/day)
        self.initial_conditions['water_management']['surfacewater_longterm_discharge']  = \
                    get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                        ['surfacewater_longterm_discharge'], \
                    water_management_dates, \
                    missing_value = water_management_missing_value, \
                    message_str   = 'Setting initial long-term surface water discharge')
        
        self.initial_conditions['water_management']['surfacewater_longterm_runoff']  = \
                    get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                       ['surfacewater_longterm_runoff'], \
                    water_management_dates, \
                    missing_value = water_management_missing_value, \
                    message_str   = 'Setting initial long-term surface water total runoff')
        
        # sectoral prioritization
        # update temporarily the source names including desalinated water use
        source_names_prioritization = source_names.copy()
        if self.model_flags['desalinated_water_use_flag'] and 'desalwater' not in source_names:
            source_names_prioritization.append('desalwater')
        
        # set default prioritization to all sectors per source
        prioritization = dict((source_name, \
                               dict((sector_name, \
                                     pcr.spatial(pcr.scalar(1.00))) \
                                    for sector_name in sector_names)) \
                              for source_name in source_names_prioritization)
        
        # read in prioritization from configuration file if specified
        for source_name in source_names_prioritization:
            for sector_name in sector_names:
                
                # defining key
                key = 'prioritization_%s_%s' % (source_name, sector_name)
                
                # evaluate if key exists
                if key in self.model_configuration.water_management.keys():
                    
                    # read value or path
                    values = read_file_entry( \
                        filename         = self.model_configuration.water_management[key], \
                        variablename     = self.model_configuration.water_management[key], \
                        inputpath        = self.model_configuration.general['inputpath'], \
                        clone_attributes = self.model_configuration.clone_attributes, \
                        datatype         = pcr.Scalar)
                    
                    # fill and mask results
                    var_out = pcr.cover(values, \
                                        prioritization[source_name][sector_name])
                    var_out = pcr.ifthen(self.landmask, var_out)
                    
                    # set variable
                    prioritization[source_name][sector_name] = var_out
        
        # initialize the water management module
        self.water_management = water_management( \
                    landmask                           = self.landmask, \
                    time_increment                     = self.model_configuration.water_management\
                                                                               ['time_increment'], \
                    time_step_length                   = self.model_time.time_step_length, \
                    cellarea                           = self.cellarea, \
                    desalwater_allocation_zones        = desalwater_allocation_zones, \
                    desalwater_withdrawal_points       = desalwater_withdrawal_points, \
                    groundwater_allocation_zones       = groundwater_allocation_zones, \
                    groundwater_withdrawal_points      = groundwater_withdrawal_points, \
                    groundwater_withdrawal_capacity    = groundwater_withdrawal_capacity, \
                    groundwater_update_weight          = groundwater_update_weight, \
                    groundwater_longterm_storage       = self.initial_conditions['water_management'] \
                                                                    ['groundwater_longterm_storage'], \
                    surfacewater_allocation_zones      = surfacewater_allocation_zones, \
                    surfacewater_withdrawal_points     = surfacewater_withdrawal_points, \
                    surfacewater_withdrawal_capacity   = surfacewater_withdrawal_capacity, \
                    surfacewater_update_weight         = surfacewater_update_weight, \
                    surfacewater_longterm_discharge    = self.initial_conditions['water_management'] \
                                                                 ['surfacewater_longterm_discharge'], \
                    surfacewater_longterm_runoff        = self.initial_conditions['water_management'] \
                                                                     ['surfacewater_longterm_runoff'], \
                    total_return_flow_ini               = self.initial_conditions['water_management'] \
                                                                                ['total_return_flow'], \
                    prioritization                     = prioritization, \
                    sector_names                       = sector_names, \
                    source_names                       = source_names, \
                    withdrawal_names                   = withdrawal_names, \
                    water_quality_flag                  = self.model_flags['water_quality_flag'], \
                    desalinated_water_use_flag          = self.model_flags['desalinated_water_use_flag'], \
                    groundwater_pumping_capacity_flag   = self.model_flags['groundwater_pumping_capacity_flag'], \
                    surfacewater_pumping_capacity_flag  = self.model_flags['surfacewater_pumping_capacity_flag'], \
                    )
        
        # remove temporal files
        groundwater_allocation_zones    = None; surfacewater_allocation_zones    = None;
        groundwater_withdrawal_points   = None; surfacewater_withdrawal_points   = None;
        groundwater_withdrawal_capacity = None; surfacewater_withdrawal_capacity = None;
        desalwater_allocation_zones     = None; desalwater_withdrawal_points     = None;
        prioritization = None; source_names_prioritization = None;
        sector_names = None; source_names = None; withdrawal_names = None
        
        del groundwater_allocation_zones,       surfacewater_allocation_zones, \
            groundwater_withdrawal_points,      surfacewater_withdrawal_points, \
            groundwater_withdrawal_capacity,    surfacewater_withdrawal_capacity, \
            desalwater_allocation_zones,        desalwater_withdrawal_points, \
            prioritization, source_names_prioritization,\
            sector_names, source_names, withdrawal_names
        
        # update initial conditions for surface and groundwater pumping capacity
        if self.model_flags['groundwater_pumping_capacity_flag']:
            self.initial_conditions['water_management']['groundwater_longterm_potential_withdrawal'] = \
                self.water_management.groundwater_longterm_potential_withdrawal
        
        if self.model_flags['surfacewater_pumping_capacity_flag']:
            self.initial_conditions['water_management']['surfacewater_longterm_potential_withdrawal'] = \
                self.water_management.surfacewater_longterm_potential_withdrawal
        
        # set forcing variables for water demand
        self.gross_demand_forcing_vars = {}
        self.net_demand_forcing_vars = {}
        
        for forcing_variable in forcing_variables.keys():
            for sector_name in self.water_management.sector_names:
                for demand_name_root in ['%s_gross_demand', '%sgrossdemand']:
                    if forcing_variable.lower() == (demand_name_root % sector_name):
                        self.gross_demand_forcing_vars[sector_name] = forcing_variable.lower()
                
                for demand_name_root in ['%s_net_demand', '%snetdemand', \
                                         '%s_netto_demand', '%snettodemand']:
                    if forcing_variable.lower() == (demand_name_root % sector_name):
                        self.net_demand_forcing_vars[sector_name] = forcing_variable.lower()
        
        # check for any missing sectors
        for sector_name in self.gross_demand_forcing_vars.keys():
            if sector_name not in self.net_demand_forcing_vars.keys():
                self.net_demand_forcing_vars[sector_name] = self.gross_demand_forcing_vars[sector_name]
        
        for sector_name in self.net_demand_forcing_vars.keys():
            if sector_name not in self.gross_demand_forcing_vars.keys():
                self.gross_demand_forcing_vars[sector_name] = self.net_demand_forcing_vars[sector_name]
        
        # echo to screen
        message_str = 'Water demand per sector is associated to the following forcing variables:'
        for sector_name in self.water_management.sector_names:
            message_str = str.join('\n', \
                                   (message_str, \
                                    'Gross: %20s; Net: %20s' % \
                                    (self.gross_demand_forcing_vars[sector_name], \
                                     self.net_demand_forcing_vars[sector_name])))
        
        #log message on demand
        logger.info(message_str)
        
        # [ water quality ] ........................................................................
        # constituent names
        # as a list with standard water quality constituents
        constituent_names = ['temperature','organic','salinity','pathogen']
        
        # constituent limits
        # dictionary of water quality thresholds per sector and constituent
        constituent_limits = {}
        for sector_name in self.water_management.sector_names:
            constituent_limits[sector_name] = {}
            
            for constituent_name in constituent_names:
                # get value/path of limits
                var = 'limit_%s_%s' % (constituent_name, sector_name)
                
                if var in self.model_configuration.water_quality.keys():
                    limit = self.model_configuration.water_quality[var]
                else:
                    limit = None
                    logger.info('A threshold value for %s was not specified, an unattainable value of %s is assigned.' % \
                                (constituent_name, unattainable_threshold))
                
                # replace None values with unreachable threshold
                if limit == 'None':
                    limit = str(unattainable_threshold)
                
                # identify variable name (make sure netcdf and variable has the same name)
                ncvariable = os.path.basename(limit).split('.')[0]
                
                # read file
                limit = read_file_entry( \
                            filename         = limit, \
                            variablename     = ncvariable, \
                            inputpath        = self.model_configuration.general['inputpath'], \
                            clone_attributes = self.model_configuration.clone_attributes, \
                            datatype         = pcr.Scalar, \
                            )
                
                # set variable
                constituent_limits[sector_name][constituent_name] = limit
        
        # long-term water quality
        # dictionary with dates (keys) and maps of long-term water quality (values)
        # is read by the 'initial conditions' module
        for source_name in self.water_management.source_names:
            for constituent_name in constituent_names:
                # get variable name
                var = '%s_longterm_%s' % (source_name, constituent_name)
                
                if self.model_flags['water_quality_flag']:
                    # verify if constituent has long-term water quality data
                    if var+'_ini' in self.model_configuration.water_quality.keys():
                        constituent_longterm_quality = \
                                    self.initial_conditions['water_quality'][var]
                    else:
                        constituent_longterm_quality = \
                                    dict((date, pcr.spatial(pcr.scalar(0))) \
                                         for date in water_management_dates)
                        logger.info('Long-term %s was not specified, a value of zero is assigned.' % \
                                    constituent_name)
                
                # set zero concentration values when water quality is not evaluated
                else:
                    constituent_longterm_quality = \
                                        dict((date, pcr.spatial(pcr.scalar(0))) \
                                             for date in water_management_dates)
                
                # update format of initial conditions
                self.initial_conditions['water_quality'][var] = \
                    get_initial_condition_as_timed_dict( \
                        initial_condition = constituent_longterm_quality, \
                        dates             = water_management_dates, \
                        missing_value     = water_management_missing_value, \
                        message_str       = 'Setting initial long-term %s state for %s source' % \
                                            (constituent_name, source_name))
        
        # short-term water quality
        # set water quality forcing information in dictionary
        self.water_quality_forcing_info = {}
        
        for source_name in self.water_management.source_names:
            for constituent_name in constituent_names:
                # get variable name
                var = '%s_%s' % (source_name, constituent_name)
                
                # verify if constituent has short-term water quality data
                if self.model_flags['water_quality_flag']:
                    if var+'_ncfile' in self.model_configuration.water_quality.keys():
                        ncfilename = self.model_configuration.water_quality[var+'_ncfile']
                    else:
                        ncfilename = '0.0'
                        message_str = str.join('\n',
                                                ('Concentration values of %s for %s source' %\
                                                 (constituent_name, source_name), \
                                                 'were not specified, a value of zero is assigned.')\
                                                 )
                        logger.info(message_str)
                
                # set zero concentration values when water quality is not evaluated
                else:
                    ncfilename = '0.0'
                
                # set the information
                self.water_quality_forcing_info[var] = \
                              { \
                               'ncfilename': ncfilename, \
                               'ncvariable': water_quality_forcing_variables[var], \
                               'inputpath' : self.model_configuration.general['inputpath'], \
                              }
        
        # initialize the water quality module
        self.water_quality = water_quality( \
              landmask                          = self.landmask, \
              time_increment                    = self.model_configuration.water_management\
                                                                        ['time_increment'], \
              source_names                      = self.water_management.source_names, \
              constituent_names                 = constituent_names, \
              constituent_limits                = constituent_limits, \
              quality_update_weight             = {'surfacewater': surfacewater_update_weight, \
                                                   'groundwater' : groundwater_update_weight}, \
              surfacewater_longterm_temperature = self.initial_conditions['water_quality']\
                                                     ['surfacewater_longterm_temperature'], \
              groundwater_longterm_temperature  = self.initial_conditions['water_quality']\
                                                      ['groundwater_longterm_temperature'], \
              surfacewater_longterm_organic     = self.initial_conditions['water_quality']\
                                                         ['surfacewater_longterm_organic'], \
              groundwater_longterm_organic      = self.initial_conditions['water_quality']\
                                                          ['groundwater_longterm_organic'], \
              surfacewater_longterm_salinity    = self.initial_conditions['water_quality']\
                                                        ['surfacewater_longterm_salinity'], \
              groundwater_longterm_salinity     = self.initial_conditions['water_quality']\
                                                         ['groundwater_longterm_salinity'], \
              surfacewater_longterm_pathogen    = self.initial_conditions['water_quality']\
                                                        ['surfacewater_longterm_pathogen'], \
              groundwater_longterm_pathogen     = self.initial_conditions['water_quality']\
                                                         ['groundwater_longterm_pathogen'], \
              )
        
        # remove water quality and other temporal files
        constituent_limits = None; constituent_names = None;
        groundwater_update_weight = None; surfacewater_update_weight = None
        
        del constituent_limits, constituent_names, \
            groundwater_update_weight, surfacewater_update_weight
        
        # log message on water quality module
        message_str = 'Water quality module is activated'
        logger.info(message_str)
        
        # set water quality object to water management
        setattr(self.water_management,'water_quality',self.water_quality)
        
        # returns None
        return None
    
    def update(self):
        # ***********
        # * forcing *
        # ***********
        self.update_reading_hydrology()
        self.update_reading_water_quality()
        self.update_reading_pumping_capacity()
        
        # ********************
        # * water management *
        # ********************
        self.update_calculate()
    
    
    def update_reading_hydrology(self):
        date = self.model_time.date
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        dt = f'{str(date.year)[2:]}-{str(date.month).zfill(2)}'
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # [ forcing: hydrology ] ...................................................................
        # read in forcing datasets
        for forcing_variable in forcing_variables.keys():
            
            # check if the model time-step is daily
            if self.model_time.time_increment == 'daily':
                if date.day != 1:
                    
                    # read the first value of the month
                    date = datetime.datetime(date.year, date.month, 1)
                    
                    # log message
                    logger.info('%s variable does not have daily data, first value of the month is therefore read.' % \
                                 forcing_variable.lower())
            
            # get the field
            var_out = read_file_entry( \
                filename                 = self.forcing_info[forcing_variable]['ncfilename'], \
                variablename            = forcing_variable, \
                inputpath               = self.forcing_info[forcing_variable]['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = self.forcing_info[forcing_variable]['datatype'], \
                date                    = date, \
                date_selection_method   = self.forcing_info[forcing_variable]['date_selection_method'], \
                allow_year_substitution = self.forcing_info[forcing_variable]['allow_year_substitution'], \
                )
            
            # clip to land mask
            var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))
            
            # update totals to rates (m/day)
            # in standard setup:
            #     input forcing variables (m/month): precipitation, referencePotET, groundwater_recharge, direct_runoff, interflow, irrigation
            #     input water demands (m/day): domestic, industry, livestock, manufacture, thermoelectric, environment, desalinated
            #     all variables must be in m/day
            if self.forcing_info[forcing_variable]['total_to_rate']: \
                           var_out = var_out / self.model_time.time_step_length
            
            # set the variable
            setattr(self, forcing_variable.lower(), var_out)
            
            # log message
            logger.debug('information on %s read for %s' % \
                         (forcing_variable.lower(), self.model_time.date))
        
    def update_reading_water_quality(self):
        date = self.model_time.date
        
        # [ forcing: water quality ] ...............................................................
        # read in water quality forcing datasets
        constituent_shortterm_quality = {}
        
        for source_name in self.water_management.source_names:
            constituent_shortterm_quality[source_name] = {}
            for constituent_name in self.water_quality.constituent_names:
                # get the key
                key = '%s_%s' % (source_name, constituent_name)
                
                # get value if dataset is available
                if self.model_flags['water_quality_flag']:
                    # get the field
                    var_out = read_file_entry( \
                        filename                 = self.water_quality_forcing_info[key]['ncfilename'], \
                        variablename            = self.water_quality_forcing_info[key]['ncvariable'], \
                        inputpath               = self.water_quality_forcing_info[key]['inputpath'], \
                        clone_attributes        = self.model_configuration.clone_attributes, \
                        datatype                = pcr.Scalar, \
                        date                    = self.model_time.date, \
                        date_selection_method   = 'nearest', \
                        allow_year_substitution = False, \
                        )
                    
                    msg_str = 'information on %s %s short-term quality read for %s' % \
                               (source_name, constituent_name, self.model_time.date)
                
                # set zero value if dataset is not available
                else:
                    var_out = pcr.spatial(pcr.scalar(0))
                    msg_str = 'no %s %s short-term quality is given for %s; a value of zero is considered' % \
                               (source_name, constituent_name, self.model_time.date)
                    
                # cover NaN to zero concentration values and clip map to land mask
                var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))
                
                # set the variable in dictionary
                constituent_shortterm_quality[source_name][constituent_name] = var_out
                
                # set variable
                setattr(self, key, var_out)
                
                # log message
                logger.debug(msg_str)
                
                # [ DELETEME ] verbose <--------------------------------------------------------------------------------------------------------------
                if verbose:
                    pcr.report(constituent_shortterm_quality[source_name][constituent_name], f'{path}/{dt}_shortterm_{source_name}_{constituent_name}.map')
                # ------------------------------------------------------------------------------------------------------------------------------------
            
            # set variable
            setattr(self.water_management.water_quality, 'constituent_shortterm_quality', constituent_shortterm_quality)
        
    def update_reading_pumping_capacity(self):
        date = self.model_time.date
        
        # [ forcing: withdrawal capacity ] .........................................................
        # read in regional water pumping capacity (if activated)
        for source_name in self.water_management.source_names:
            flag_name = '%s_pumping_capacity_flag' % source_name
            file_name = '%s_regional_pumping_capacity' % source_name
            
            if self.model_flags[flag_name]:
                # log message
                logger.info('Pumping capacity is considered to limit %s withdrawals for %s.' % \
                            (self.model_time.date, source_name))
                
                # evaluate if date is January 1st
                # as dataset is at yearly resolution
                if date.day == 1 and date.month == 1:
                    regional_pumping_capacity = {}
                    
                    # read in the regional water pumping capacity and IDs
                    for var, dtype in [('regional_pumping_limit',pcr.Scalar),\
                                       ('region_ids',pcr.Nominal),\
                                       ('region_ratios',pcr.Scalar)]:
                        var_out = read_file_entry( \
                                filename                 = self.model_configuration.water_management[file_name], \
                                variablename            = var, \
                                inputpath               = self.model_configuration.general['inputpath'], \
                                clone_attributes        = self.model_configuration.clone_attributes, \
                                datatype                = dtype, \
                                date                    = datetime.datetime(date.year,1,1), \
                                date_selection_method   = 'exact', \
                                allow_year_substitution = True)
                        
                        # cover NaN to zero values and clip map to land mask
                        var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))
                        
                        # set variable
                        regional_pumping_capacity[var] = var_out
                    
                    # calculate the groundwater withdrawal capacity (units: m3/month)
                    self.water_management.update_withdrawal_capacity( \
                                    source_name            = source_name, \
                                    regional_pumping_limit = regional_pumping_capacity['regional_pumping_limit'], \
                                    region_ids             = regional_pumping_capacity['region_ids'], \
                                    region_ratios          = regional_pumping_capacity['region_ratios'], \
                                    time_step_length       = self.model_time.time_step_length, \
                                    date                   = self.model_time.date)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            if self.model_flags['surfacewater_pumping_capacity_flag'] or not isinstance(self.water_management.surfacewater_withdrawal_capacity, NoneType):
                pcr.report(self.water_management.surfacewater_withdrawal_capacity, f'{path}/{dt}_surfacewater_withdrawal_capacity.map')
            if self.model_flags['groundwater_pumping_capacity_flag'] or not isinstance(self.water_management.groundwater_withdrawal_capacity, NoneType):
                pcr.report(self.water_management.groundwater_withdrawal_capacity, f'{path}/{dt}_groundwater_withdrawal_capacity.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
    
    
    
    def update_calculating(self):
        # ********************
        # * water management *
        # ********************
        
        # [ long-term availability ] ...............................................................
        # get the long-term availability for given date
        # (units: m3/day)
        surfacewater_availability, groundwater_availability = \
            self.water_management.get_longterm_availability_for_date( \
                              date              = self.model_time.date, \
                              cellarea          = self.cellarea, \
                              ldd               = self.surfacewater.ldd, \
                              waterdepth        = self.surfacewater.storage, \
                              mannings_n        = self.surfacewater.mannings_n, \
                              channel_gradient  = self.surfacewater.channel_gradient, \
                              channel_width     = self.surfacewater.channel_width, \
                              channel_length    = self.surfacewater.channel_length, \
                              time_step_seconds = self.model_time.seconds_per_day)
        
        # [ water demands ] ........................................................................
        # initialize the gross and net demand per sector as a total volume 
        # per day and cell
        gross_demand_per_sector = dict((sector_name, \
                                        pcr.spatial(pcr.scalar(0))) \
                                       for sector_name in self.water_management.sector_names)
        net_demand_per_sector   = dict((sector_name, \
                                        pcr.spatial(pcr.scalar(0))) \
                                       for sector_name in self.water_management.sector_names)
        
        for sector_name in self.water_management.sector_names:
            # add demand per sector to the gross and net demand
            # (units: m3/day)
            gross_demand_per_sector[sector_name] = gross_demand_per_sector[sector_name] + \
                                                   getattr(self, self.gross_demand_forcing_vars[sector_name]) * \
                                                   self.cellarea
            net_demand_per_sector[sector_name]   = net_demand_per_sector[sector_name] + \
                                                   getattr(self, self.net_demand_forcing_vars[sector_name]) * \
                                                   self.cellarea
        
        logger.debug('Water demand read for %s' % self.model_time.date)
        
        # assign the water demand to the water management module 
        # (units: m3/day)
        self.water_management.update_water_demand_for_date( \
                              gross_demand = gross_demand_per_sector, \
                              net_demand   = net_demand_per_sector, \
                              date         = self.model_time.date)
        
        # update environmental water demand and priority if evaluated
        # based on the channel storage required to meet the environmental flow requirements
        # (units: m3/day)
        prioritization = deepcopy(self.water_management.prioritization)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            if 'environment' in self.water_management.sector_names:
                pcr.report(self.water_management.gross_demand['environment'], f'{path}/{dt}_gross_demand_environment_[original].map')
                for source_name in self.water_management.source_names:
                    for sector_name in self.water_management.sector_names:
                        pcr.report(prioritization[source_name][sector_name], f'{path}/{dt}_prioritization_{source_name}_{sector_name}_[original].map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        if 'environment' in self.water_management.sector_names:
            prioritization = \
                   self.water_management.update_environmental_flow_requirements_for_date( \
                              surfacewater_availability = surfacewater_availability, \
                              surfacewater_depth        = self.surfacewater.storage, \
                              mannings_n                = self.surfacewater.mannings_n, \
                              channel_gradient          = self.surfacewater.channel_gradient, \
                              channel_width             = self.surfacewater.channel_width, \
                              channel_length            = self.surfacewater.channel_length, \
                              time_step_seconds         = self.model_time.seconds_per_day)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            for source_name in self.water_management.source_names:
                for sector_name in self.water_management.sector_names:
                    pcr.report(prioritization[source_name][sector_name], f'{path}/{dt}_prioritization_{source_name}_{sector_name}_[updated].map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # [ desalination water use ] ...............................................................
        # allocate the desalinated water use (units: m3/day)
        # on a given date to the selected sectors, i.e., domestic and manufacture
        if self.model_flags['desalinated_water_use_flag']:
            self.water_management.allocate_desalinated_water_for_date( \
                              availability = self.desalinated_water_use * self.cellarea, \
                              date         = self.model_time.date)
        
        # [ long-term potential water withdrawal ] .................................................
        # allocate the current demand to the long-term availability given the date
        # and the model settings for the time increment and return the withdrawal
        # that is met (renewable) and potentially unmet (non-renewable) for the
        # available sources
        self.water_management.update_potential_withdrawals_for_date( \
                              availability   = {'surfacewater': surfacewater_availability, \
                                                'groundwater' : groundwater_availability}, \
                              prioritization = prioritization, \
                              date           = self.model_time.date)
        
        # dictionaries with the actual renewable and non-renewable withdrawals
        # have been initialized with the allocation of the demand to the poten-
        # tial withdrawals; actual withdrawals are updated iteratively and any
        # unmet demand is subdivided to the other sources within the same zone.
        # these are updated using the remaining entries in the source names
        # set the source names to process the unmet demand
        source_names_to_be_processed = self.water_management.sources_unmet_demand[:]
        
        
        # *****************
        # * surface water *
        # *****************
        
        # surface water: time step length is in days, time step in seconds
        # is the value for one unit of time [s] (so one day is 86400 s)
        source_name = 'surfacewater'
        source_names_to_be_processed.remove(source_name)
        
        # [ total potential withdrawal ] ...........................................................
        # set the potential withdrawal per sector
        # as the total of the non-renewable and renewable withdrawals 
        # (units: m3/day)
        potential_withdrawal_per_sector = \
                     self.water_management.get_potential_withdrawal(source_name)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            pcr.report(sum_list(list(potential_withdrawal_per_sector.values())), f'{path}/{dt}_longterm_potential_withdrawal_surfacewater.map')
            for sector_name in self.water_management.sector_names:
                pcr.report(potential_withdrawal_per_sector[sector_name], f'{path}/{dt}_longterm_potential_withdrawal_surfacewater_{sector_name}.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # [ total runoff ] .........................................................................
        # get the channel runoff
        # (units: m/day)
        self.channel_runoff = self.precipitation - \
                             self.surfacewater.water_cropfactor * self.referencepotet
        
        # get the return flow
        # (units: m/day)
        total_return_flow = self.water_management.total_return_flow / self.cellarea
        
        # get the total runoff 
        # (units: m/day)
        total_runoff = \
             self.surfacewater.get_total_runoff( \
                                             direct_runoff  = self.direct_runoff, \
                                             interflow      = self.interflow, \
                                             base_flow      = self.groundwater.total_base_flow / \
                                                             self.model_time.time_step_length, \
                                             channel_runoff = self.channel_runoff, \
                                             return_flow    = total_return_flow, \
                                             date          = self.model_time.date)
        
        # [ renewable withdrawals ] ................................................................
        # get the short-term potential surface water withdrawal per sector
        # (units: m3/day)
        potential_withdrawal_per_sector = \
            self.water_management.update_surfacewater_potential_withdrawals( \
                  total_runoff                              = total_runoff, \
                  surfacewater_storage                     = self.surfacewater.storage, \
                  fraction_water                           = self.surfacewater.fraction_water, \
                  longterm_potential_withdrawal_per_sector = potential_withdrawal_per_sector, \
                  cellarea                                 = self.cellarea, \
                  date = self.model_time.date)
        
        potential_withdrawal = sum_list(list(potential_withdrawal_per_sector.values()))
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            pcr.report(potential_withdrawal, f'{path}/{dt}_shortterm_potential_withdrawal_surfacewater.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # get the discharge (units: m3/s) and the actual (renewable) withdrawals (units: m3/day) 
        # by routing the total runoff with the potential withdrawals
        discharge, renewable_withdrawal = self.surfacewater.update( \
                                      total_runoff          = total_runoff, \
                                      potential_withdrawal = potential_withdrawal, \
                                      cellarea             = self.cellarea, \
                                      time_step_seconds    = self.model_time.seconds_per_day)
        
        # re-distribute renewable withdrawal by sector (units: m3/day)
        renewable_withdrawal_per_sector = \
             dict((sector_name, \
                   renewable_withdrawal * pcr_return_val_div_zero(potential_withdrawal_per_sector[sector_name], \
                                                                  potential_withdrawal, \
                                                                  very_small_number)) \
                  for sector_name in self.water_management.sector_names)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            pcr.report(renewable_withdrawal, f'{path}/{dt}_actual_renewable_withdrawal_surfacewater.map')
            for sector_name in self.water_management.sector_names:
                pcr.report(renewable_withdrawal_per_sector[sector_name], f'{path}/{dt}_actual_renewable_withdrawal_surfacewater_{sector_name}.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # [ non-renewable withdrawals ]  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # set the non-renewable withdrawal to zero
        # as all surface water withdrawals are currently renewable
        nonrenewable_withdrawal = pcr.ifthen(self.landmask, pcr.scalar(0))
        nonrenewable_withdrawal_per_sector = \
                                  dict((sector_name, \
                                        nonrenewable_withdrawal) \
                                       for sector_name in self.water_management.sector_names)
        
        # *************************
        # * water management      *
        # *************************
        
        # set the actual surface water withdrawal and add any unmet demand to the
        # potential non-renewable withdrawal for the remaining, allowable sources
        self.water_management.update_withdrawals( \
                     source_name                        = source_name, \
                     renewable_withdrawal_per_sector    = renewable_withdrawal_per_sector, \
                     nonrenewable_withdrawal_per_sector = nonrenewable_withdrawal_per_sector, \
                     source_names_to_be_processed       = source_names_to_be_processed, \
                     date = self.model_time.date)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            pcr.report(self.water_management.potential_renewable_withdrawal['groundwater'], f'{path}/{dt}_potential_renewable_withdrawal_groundwater_[reallocated].map')
            pcr.report(self.water_management.potential_nonrenewable_withdrawal['groundwater'], f'{path}/{dt}_potential_nonrenewable_withdrawal_groundwater_[reallocated].map')
            for sector_name in self.water_management.sector_names:
                pcr.report(self.water_management.potential_renewable_withdrawal_per_sector['groundwater'][sector_name], f'{path}/{dt}_potential_renewable_withdrawal_groundwater_{sector_name}_[reallocated].map')
                pcr.report(self.water_management.potential_nonrenewable_withdrawal_per_sector['groundwater'][sector_name], f'{path}/{dt}_potential_nonrenewable_withdrawal_groundwater_{sector_name}_[reallocated].map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # ***************
        # * groundwater *
        # ***************
        
        # groundwater: base_flow is added to the forcing variables to complement
        # the direct runoff and interflow in the forcing variables;
        # base flow is the total here and is used here to compute the water 
        # availability here below.
        # The total over the time step is used to compute the groundwater avail-
        # ability here below but is passed directly to the surface water module
        # from the groundwater module in the call to the surface water module 
        # above as it lags by one time step.
        source_name = 'groundwater'
        source_names_to_be_processed.remove(source_name)
        
        # [ total potential withdrawal ] . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # as the total of the non-renewable and renewable withdrawals (units: m3/day)
        potential_withdrawal_per_sector = \
                     self.water_management.get_potential_withdrawal(source_name)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            pcr.report(sum_list(list(potential_withdrawal_per_sector.values())), f'{path}/{dt}_longterm_potential_withdrawal_groundwater.map')
            for sector_name in self.water_management.sector_names:
                pcr.report(potential_withdrawal_per_sector[sector_name], f'{path}/{dt}_longterm_potential_withdrawal_groundwater_{sector_name}.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # [ groundwater components ] . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
        # aggregate total withdrawals from all sectors (units: m/day)
        potential_withdrawal = \
              sum_list(list(potential_withdrawal_per_sector.values())) / self.cellarea
        
        # update the total base flow and the actual usable groundwater storage (units: m/period)
        self.groundwater.get_storage( \
                               recharge             = self.groundwater_recharge, \
                               potential_withdrawal = potential_withdrawal, \
                               time_step_length     = self.model_time.time_step_length, \
                               date                 = self.model_time.date)
        
        # [ withdrawals ]  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # get the actual renewable and non-renewable groundwater withdrawals
        # (units: m3/day)
        # and renewable groundwater storage (units: m per day)
        renewable_withdrawal_per_sector, nonrenewable_withdrawal_per_sector, \
        renewable_withdrawal, nonrenewable_withdrawal, storage = \
                     self.water_management.update_groundwater_actual_withdrawals( \
                               groundwater_storage                      = self.groundwater.storage, \
                               total_recharge                           = self.groundwater.total_recharge, \
                               total_base_flow                           = self.groundwater.total_base_flow, \
                               longterm_potential_withdrawal_per_sector = potential_withdrawal_per_sector, \
                               cellarea                                 = self.cellarea, \
                               time_step_length                         = self.model_time.time_step_length, \
                               date = self.model_time.date)
        
        # [ update storage ] . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        # set the variables in the groundwater routine (units: m/period)
        self.groundwater.update(renewable_withdrawal    * self.model_time.time_step_length / self.cellarea, \
                                nonrenewable_withdrawal * self.model_time.time_step_length / self.cellarea)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            pcr.report(renewable_withdrawal,    f'{path}/{dt}_actual_renewable_withdrawal_groundwater.map')
            pcr.report(nonrenewable_withdrawal, f'{path}/{dt}_actual_nonrenewable_withdrawal_groundwater.map')
            for sector_name in self.water_management.sector_names:
                pcr.report(renewable_withdrawal_per_sector[sector_name],    f'{path}/{dt}_actual_renewable_withdrawal_groundwater_{sector_name}.map')
                pcr.report(nonrenewable_withdrawal_per_sector[sector_name], f'{path}/{dt}_actual_nonrenewable_withdrawal_groundwater_{sector_name}.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # ********************
        # * water management *
        # ********************
        
        # [ set variables ]
        # set the actual groundwater withdrawal and add any unmet demand to the
        # potential non-renewable withdrawal for the remaining, allowable sources
        self.water_management.update_withdrawals( \
                     source_name                        = source_name, \
                     renewable_withdrawal_per_sector    = renewable_withdrawal_per_sector, \
                     nonrenewable_withdrawal_per_sector = nonrenewable_withdrawal_per_sector, \
                     source_names_to_be_processed       = source_names_to_be_processed, \
                     date = self.model_time.date)
        
        if pcr.cellvalue(pcr.mapminimum(renewable_withdrawal), 1)[0] < -1:
            pcr.aguila(renewable_withdrawal, nonrenewable_withdrawal)
            sys.exit()
        
        # [ water allocation ]
        # allocate the actual withdrawals to the demands,
        # get the consumption and the return flows
        self.water_management.allocate_withdrawal_to_demand_for_date( \
                                            date = self.model_time.date)
        
        # [ DELETEME ] verbose <----------------------------------------------------------------------------------------------------------------------
        if verbose:
            for withdrawal_name in self.water_management.withdrawal_names:
                for source_name in self.water_management.source_names:
                    key = f'{withdrawal_name}_{source_name}'
                    for sector_name in self.water_management.sector_names:
                        pcr.report(self.water_management.allocated_demand_per_sector[key][sector_name], f'{path}/{dt}_allocated_withdrawal_{withdrawal_name}_{source_name}_{sector_name}.map')
        # --------------------------------------------------------------------------------------------------------------------------------------------
        
        # [ long-term updating ]
        # update long-term water availability:
        # groundwater_storage    (units: m per day)
        # surfacewater_discharge (units: m3/s)
        # surfacewater_runoff     (units: m/day)
        self.water_management.update_longterm_availability( \
                                    groundwater_storage    = storage, \
                                    surfacewater_discharge = discharge, \
                                    surfacewater_runoff     = total_runoff, \
                                    date                   = self.model_time.date)
        
        # update long-term potential withdrawal based on date    <------------------------ pumping capacity
        self.water_management.update_longterm_potential_withdrawals( \
                                    date = self.model_time.date)
        
        # update long-term water quality based on date
        self.water_management.water_quality.update_longterm_quality_for_date( \
                                    source_names = self.water_management.source_names, \
                                    date         = self.model_time.date)
        
        # returns None
        return None

        # *****************
        # * end of update *
        # *****************

    def finalize_year(self):
     
        # update the total water availability
        # log message
        logger.info('last day of year %d: updating water availability' % \
                    self.model_time.year)
        # update total water availability
        self.water_management.update_total_water_availability()
        self.water_management.water_quality.update_annual_water_quality( \
                              source_names = self.water_management.source_names)
         
        # get the final states as the new initial conditions
        # log message
        logger.info('last day of year %d: writing states' % self.model_time.year)
        # write the values
        self.update_initial_conditions(self.model_time.date)
        self.report_initial_conditions(self.model_time.date)

    def finalize_run(self):

        # log message
        logger.info('final time step: closing down all files')

        # close the caches
        # initial conditions
        self.report_initial_conditions_to_file.close()
        # main module
        close_nc_cache()
        
        # returns None
        return None

    def update_initial_conditions(self, date):
        '''
update_initial_conditions: function that updates the initial conditions from \
the different modules that are required to start with a warm state.

Returns None

'''
        # get the warm states
        for module_name in self.modules:
            
            # first, get the states for the present module
            if module_name != 'water_quality':
                state_info = getattr(self, module_name).get_final_conditions()
            else:
                state_info = self.water_management.water_quality.get_final_conditions()
                
            # update the information
            if not module_name in self.initial_conditions.keys():
                self.initial_conditions[module_name] = {}
            
            # update the values
            for key, value in state_info.items():
               self.initial_conditions[module_name][key] = value
        
        # log message
        logger.info('Initial conditions updated for %s' % date)
        
        # returns None
        return None

    def report_initial_conditions(self, date):

        '''

report_initial_conditions: functions that report the initial conditions to file.

Returns None

'''

        # report the initial conditions
        self.report_initial_conditions_to_file.report(date, \
                                                     self.initial_conditions)

        # return None
        return None

    # ==============
    # =END OF MODEL=
    # ==============

#///model end///#
