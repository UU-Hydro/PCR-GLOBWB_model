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

# modules from the QUAlloc model
try:
    from .spatialDataSet2PCR import spatialAttributes, setClone
    from .basic_functions import sum_list, pcr_return_val_div_zero
    from .file_handler import compose_filename, read_file_entry, close_nc_cache
    from .initial_conditions_handler import get_initial_conditions, get_initial_condition_as_timed_dict
    from .qualloc_reporting import  qualloc_report_initial_conditions
    
    from .groundwater      import groundwater
    from .surfacewater     import surfacewater
    from .water_management import water_management, water_management_missing_value, very_small_number
    from .water_quality    import water_quality, water_quality_forcing_variables, unattainable_threshold

except:
    from spatialDataSet2PCR import spatialAttributes, setClone
    from basic_functions import sum_list, pcr_return_val_div_zero
    from file_handler import compose_filename, read_file_entry, close_nc_cache
    from initial_conditions_handler import get_initial_conditions, get_initial_condition_as_timed_dict
    from qualloc_reporting import  qualloc_report_initial_conditions
    
    from groundwater      import groundwater
    from surfacewater     import surfacewater
    from water_management import water_management, water_management_missing_value, very_small_number, water_balance_check
    from water_quality    import water_quality, water_quality_forcing_variables, unattainable_threshold


# global variables
logger = logging.getLogger(__name__)


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
                      'direct_runoff'              : 'direct_runoff', \
                      'interflow'                  : 'interflow', \
                      'irrigationGrossDemand'     : 'irrigation_water_demand', \
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
                      'environmentGrossDemand'    : 'environment_water_demand', \
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
        self.time_step  = self.model_time.time_increment
        
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
    
    def initialize(self, \
                   online_coupling = False, \
                   landmask                 = None, \
                   cellarea                 = None, \
                   groundwater_alpha        = None, \
                   total_base_flow_ini      = None, \
                   groundwater_storage_ini  = None, \
                   ldd                      = None, \
                   fraction_water           = None, \
                   water_cropfactor         = None, \
                   channel_gradient         = None, \
                   channel_width            = None, \
                   channel_length           = None, \
                   mannings_n               = None, \
                   surfacewater_storage_ini = None, \
                   ):
        
        # stand-alone QUAlloc version
        #if online_coupling == False:
        # read in the land mask
        self.landmask = read_file_entry( \
                filename                = self.model_configuration.general['clone'], \
                variablename            = 'landmask', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Boolean, \
                )
        
        # read in the cell area
        self.cellarea = read_file_entry( \
                filename                = self.model_configuration.general['cellarea'], \
                variablename            = 'cellarea', \
                inputpath               = self.model_configuration.general['inputpath'], \
                clone_attributes        = self.model_configuration.clone_attributes, \
                datatype                = pcr.Scalar, \
                )
        
        # coupled QUAlloc version
        #else:
        #    # import the land mask and cell area (m2)
        #    # from PCR-GLOBWB2
        #    self.landmask = landmask
        #    self.cellarea = cellarea
        
        # **********************
        # * initial conditions *
        # **********************
        #
        # purge initial conditions
        files_to_exclude = []
        
        # coupled QUAlloc version
        # purge forcing variables
        #if online_coupling:
        #    files_to_exclude.append('total_base_flow_ini')
        #    files_to_exclude.append('groundwater_storage_ini')
        #    files_to_exclude.append('surfacewater_storage_ini')
        
        # verify use of pumping capacity
        if not self.model_flags['groundwater_pumping_capacity_flag'] or \
           self.model_configuration.water_management\
               ['groundwater_longterm_potential_withdrawal_ini'] == 'None': \
            files_to_exclude.append('groundwater_longterm_potential_withdrawal_ini')
        if not self.model_flags['surfacewater_pumping_capacity_flag'] or \
           self.model_configuration.water_management\
               ['surfacewater_longterm_potential_withdrawal_ini'] == 'None': \
            files_to_exclude.append('surfacewater_longterm_potential_withdrawal_ini')
        
        # set the initial conditions
        if isinstance(self.initial_conditions, NoneType):
            # get the initial warm states
            self.initial_conditions = \
                    get_initial_conditions( \
                                      self.model_configuration, \
                                      self.model_time.startdate, \
                                      files_to_exclude = files_to_exclude)
        
        # initialize the module to report the initial conditions
        self.report_initial_conditions_to_file = \
                    qualloc_report_initial_conditions( \
                                      self.model_configuration, \
                                      self.initial_conditions, \
                                      self.model_flags)
        
        # *********************
        # * forcing variables *
        # *********************
        #
        # initialize the forcing data set
        # this contains all the necessary dynamic input that varies for the
        # selected time step
        inputpath               = self.model_configuration.general['inputpath']
        allow_year_substitution = True       # False
        date_selection_method   = 'exact'    #'nearest'
        datatype                = pcr.Scalar
        
        # get the totals and rates
        forcing_totals = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.forcing['totals'], str)
        forcing_rates = self.model_configuration.convert_string_to_input( \
                              self.model_configuration.forcing['rates'], str)
        
        # purge forcing variables
        # unused variables: sectors
        del_keys = []
        for forcing_variable, ncfileroot in forcing_variables.items():
            if f'{ncfileroot}_ncfile' not in self.model_configuration.forcing.keys():
                del_keys.append(forcing_variable)
        for del_key in del_keys:
            forcing_variables.pop(del_key, None)
        
        # coupled QUAlloc version
        if online_coupling:
            del_keys = ['precipitation','referencePotET','direct_runoff','interflow']
            for del_key in del_keys:
                if del_key in forcing_variables.keys():
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
                             'ncfilename'               : ncfilename, \
                             'inputpath'               : inputpath, \
                             'datatype'                : datatype, \
                             'date_selection_method'   : date_selection_method, \
                             'allow_year_substitution' : allow_year_substitution, \
                             'total_to_rate'           : total_to_rate, \
                            }
        
        logger.info('forcing information initialized')
        
        # ***************
        # * groundwater *
        # ***************
        #
        # stand-alone QUAlloc version
        #if online_coupling == False:
        # read in the groundwater alpha
        self.initial_conditions['groundwater']['groundwater_storage'] = \
                pcr.ifthen(self.landmask, \
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
        
        # define initial values:
        # total base flow and groundwater storage
        total_base_flow_ini      = self.initial_conditions['groundwater']['total_base_flow']
        groundwater_storage_ini = self.initial_conditions['groundwater']['groundwater_storage']
        
        # coupled QUAlloc version
        #else:
        #    alpha                   = groundwater_alpha
        #    alpha_default           = groundwater_alpha
        #    total_base_flow_ini      = total_base_flow_ini
        #    groundwater_storage_ini = groundwater_storage_ini
        
        # initialize the groundwater module
        self.groundwater = groundwater(alpha              = alpha, \
                                       total_base_flow_ini = total_base_flow_ini, \
                                       storage_ini        = groundwater_storage_ini)
        
        # remove alpha, alpha_default
        alpha = None; alpha_default = None; 
        total_base_flow_ini = None; groundwater_storage_ini = None
        del alpha, alpha_default, \
            total_base_flow_ini, groundwater_storage_ini
        
        # ****************
        # * surfacewater *
        # ****************
        #
        # read in the ldd, fractional water area, channel properties
        # and the initial surface water storage
        
        # stand-alone QUAlloc version
        #if online_coupling == False:
        self.initial_conditions['surfacewater']['surfacewater_storage'] = \
                pcr.ifthen(self.landmask, \
                           pcr.cover(self.initial_conditions['surfacewater']['surfacewater_storage'], 0))
        surfacewater_storage_ini = self.initial_conditions['surfacewater']['surfacewater_storage']
        
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
        
        # coupled QUAlloc version
        #else:
        #    ldd                      = ldd
        #    fraction_water           = fraction_water
        #    water_cropfactor         = water_cropfactor
        #    channel_gradient         = channel_gradient
        #    channel_width            = channel_width
        #    channel_length           = channel_length
        #    mannings_n               = mannings_n
        #    surfacewater_storage_ini = surfacewater_storage_ini
        
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
                                         storage_ini      = surfacewater_storage_ini, \
                                         )
        
        # remove the  ldd, fractional water area and channel properties
        ldd = None; fraction_water = None; water_cropfactor = None; channel_gradient = None
        channel_width = None; channel_depth = None; channel_length = None
        mannings_n = None; surfacewater_storage_ini = None
        del ldd, fraction_water, water_cropfactor, channel_gradient, channel_width, \
            channel_depth, channel_length, mannings_n, surfacewater_storage_ini
        
        # ********************
        # * water management *
        # ********************
        # [ general ]
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
        
        # [ allocation zones ]
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
        
        # [ long-term ]
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
        
        # long-term groundwater storage
        # set the long-term groundwater availability by the long-term groundwater storage
        # (units: m at the end of the day)
        self.initial_conditions['water_management']['groundwater_longterm_storage'] = \
                    get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                                       ['groundwater_longterm_storage'], \
                    water_management_dates, \
                    missing_value = water_management_missing_value, \
                    message_str   = 'Setting initial long-term groundwater storage')
        
        # long-term discharge
        # set the long-term surface water availability by the long-term discharge
        # (units: m3/s)
        self.initial_conditions['water_management']['surfacewater_longterm_discharge'] = \
                    get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                                       ['surfacewater_longterm_discharge'], \
                    water_management_dates, \
                    missing_value = water_management_missing_value, \
                    message_str   = 'Setting initial long-term surface water discharge')
        
        # long-term total runoff
        # set the long-term surface water availability by the long-term total runoff
        # (units: m/day)
        self.initial_conditions['water_management']['surfacewater_longterm_runoff'] = \
                    get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                                       ['surfacewater_longterm_runoff'], \
                    water_management_dates, \
                    missing_value = water_management_missing_value, \
                    message_str   = 'Setting initial long-term surface water total runoff')
        
        # long-term gross sectoral water demand
        # (units: m/day)
        gross_demand_longterm = {}
        for sector_name in sector_names:
            var = 'gross_demand_longterm_%s'   % sector_name
            self.initial_conditions['water_management'][var] = \
                        get_initial_condition_as_timed_dict( \
                                    self.initial_conditions['water_management'][var], \
                        water_management_dates, \
                        missing_value = water_management_missing_value, \
                        message_str   = 'Setting initial long-term %s gross water demand'   % sector_name)
            
            gross_demand_longterm[sector_name] = self.initial_conditions['water_management'][var]
        
        # long-term potential withdrawal per source
        # (units: m3/day)
        longterm_potential_withdrawal = {}
        if self.model_flags['groundwater_pumping_capacity_flag']:
            self.initial_conditions['water_management']['groundwater_longterm_potential_withdrawal']  = \
                        get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                                       ['groundwater_longterm_potential_withdrawal'], \
                        water_management_dates, \
                        missing_value = water_management_missing_value, \
                        message_str   = 'Setting initial long-term groundwater potential withdrawal')
            
            longterm_potential_withdrawal['groundwater'] = \
                self.initial_conditions['water_management']['groundwater_longterm_potential_withdrawal']
        
        if self.model_flags['surfacewater_pumping_capacity_flag']:
            self.initial_conditions['water_management']['surfacewater_longterm_potential_withdrawal']  = \
                        get_initial_condition_as_timed_dict( \
                                self.initial_conditions['water_management'] \
                                                       ['surfacewater_longterm_potential_withdrawal'], \
                        water_management_dates, \
                        missing_value = water_management_missing_value, \
                        message_str   = 'Setting initial long-term surface water potential withdrawal')
            
            longterm_potential_withdrawal['surfacewater'] = \
                self.initial_conditions['water_management']['surfacewater_longterm_potential_withdrawal']
        
        # read in the weights per water source
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
        
        # reading weight per sector
        gross_demand_update_weight = {}
        for sector_name in sector_names:
            var = '%s_update_weight'     % sector_name
            gross_demand_update_weight[sector_name] = read_file_entry( \
                    filename              = self.model_configuration.water_management[var], \
                    variablename         = var, \
                    inputpath            = self.model_configuration.general['inputpath'], \
                    clone_attributes     = self.model_configuration.clone_attributes, \
                    datatype             = pcr.Scalar, \
                    )
        
        # [ prioritization ]
        # temporarily update the source names including desalinated water use
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
        
        # [ initialization ]
        # initialize the water management module
        self.water_management = water_management( \
                    landmask                         = self.landmask, \
                    cellarea                         = self.cellarea, \
                    time_increment                   = self.model_configuration.water_management\
                                                                             ['time_increment'], \
                    time_step                        = self.model_time.time_increment, \
                    time_step_length                 = self.model_time.time_step_length, \
                    desalwater_allocation_zones      = desalwater_allocation_zones, \
                    desalwater_withdrawal_points     = desalwater_withdrawal_points, \
                    groundwater_allocation_zones     = groundwater_allocation_zones, \
                    groundwater_withdrawal_points    = groundwater_withdrawal_points, \
                    groundwater_withdrawal_capacity  = groundwater_withdrawal_capacity, \
                    groundwater_update_weight        = groundwater_update_weight, \
                    groundwater_longterm_storage     = self.initial_conditions['water_management'] \
                                                                              ['groundwater_longterm_storage'], \
                    surfacewater_allocation_zones    = surfacewater_allocation_zones, \
                    surfacewater_withdrawal_points   = surfacewater_withdrawal_points, \
                    surfacewater_withdrawal_capacity = surfacewater_withdrawal_capacity, \
                    surfacewater_update_weight       = surfacewater_update_weight, \
                    surfacewater_longterm_discharge  = self.initial_conditions['water_management'] \
                                                                              ['surfacewater_longterm_discharge'], \
                    surfacewater_longterm_runoff      = self.initial_conditions['water_management'] \
                                                                              ['surfacewater_longterm_runoff'], \
                    longterm_potential_withdrawal    = longterm_potential_withdrawal, \
                    gross_demand_update_weight       = gross_demand_update_weight, \
                    gross_demand_longterm            = gross_demand_longterm, \
                    total_return_flow_ini             = self.initial_conditions['water_management'] \
                                                                              ['total_return_flow'], \
                    prioritization                   = prioritization, \
                    sector_names                     = sector_names, \
                    source_names                     = source_names, \
                    withdrawal_names                 = withdrawal_names, \
                    water_quality_flag                = self.model_flags['water_quality_flag'], \
                    desalinated_water_use_flag        = self.model_flags['desalinated_water_use_flag'], \
                    groundwater_pumping_capacity_flag = self.model_flags['groundwater_pumping_capacity_flag'], \
                    surfacewater_pumping_capacity_flag= self.model_flags['surfacewater_pumping_capacity_flag'], \
                    )
        
        # remove temporal files
        groundwater_allocation_zones    = None; surfacewater_allocation_zones    = None;
        groundwater_withdrawal_points   = None; surfacewater_withdrawal_points   = None;
        groundwater_withdrawal_capacity = None; surfacewater_withdrawal_capacity = None;
        desalwater_allocation_zones     = None; desalwater_withdrawal_points     = None;
        gross_demand_update_weight      = None; gross_demand_longterm            = None;
        prioritization = None; source_names_prioritization = None;
        sector_names = None; source_names = None; withdrawal_names = None
        
        del groundwater_allocation_zones,       surfacewater_allocation_zones, \
            groundwater_withdrawal_points,      surfacewater_withdrawal_points, \
            groundwater_withdrawal_capacity,    surfacewater_withdrawal_capacity, \
            desalwater_allocation_zones,        desalwater_withdrawal_points, \
            gross_demand_update_weight,         gross_demand_longterm, \
            prioritization, source_names_prioritization,\
            sector_names, source_names, withdrawal_names
        
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
    
    def update(self,\
               online_coupling_to_quantity     = False, \
               irrigationGrossDemand           = None, \
               domesticGrossDemand             = None, \
               domesticNettoDemand             = None, \
               industryGrossDemand             = None, \
               industryNettoDemand             = None, \
               livestockGrossDemand            = None, \
               livestockNettoDemand            = None, \
               manufactureGrossDemand          = None, \
               manufactureNettoDemand          = None, \
               thermoelectricGrossDemand       = None, \
               thermoelectricNettoDemand       = None, \
               environmentGrossDemand          = None, \
               surfacewater_storage            = None, \
               surfacewater_discharge          = None, \
               surfacewater_totalrunoff         = None, \
               groundwater_recharge            = None, \
               groundwater_baseflow             = None, \
               groundwater_storage             = None, \
               
               online_coupling_to_quality      = False, \
               surfacewater_temperature        = None, \
               surfacewater_organic            = None, \
               surfacewater_salinity           = None, \
               surfacewater_pathogen           = None, \
               groundwater_temperature         = None, \
               groundwater_organic             = None, \
               groundwater_salinity            = None, \
               groundwater_pathogen            = None, \
               ):
        
        # set the current date to update
        date = self.model_time.date
        
        
        # ******************************************************************************************
        # * forcing                                                                                *
        # ******************************************************************************************
        
        # [ forcing: hydrology ] ...................................................................
        #
        # stand-alone QUAlloc version
        if online_coupling_to_quantity == False:
            # read in forcing datasets
            for forcing_variable in forcing_variables.keys():
                
                # get the field
                var_out = read_file_entry( \
                    filename                = self.forcing_info[forcing_variable]['ncfilename'], \
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
                
                # update totals to rates (from m/month to m/day)
                # in standard setup:
                #     input forcing variables (m/month): precipitation, referencePotET, groundwater_recharge, direct_runoff, interflow, irrigation
                #     input water demands (m/day): domestic, industry, livestock, manufacture, thermoelectric, environment
                #     all variables must be in m/day
                if self.forcing_info[forcing_variable]['total_to_rate']: \
                               var_out = var_out / self.model_time.time_step_length
                
                # set variable
                setattr(self, forcing_variable.lower(), var_out)
                
                # log message
                logger.debug('information on %s read for %s' % \
                             (forcing_variable.lower(), date))
        
        # coupled QUAlloc version: PCR-GLOBWB
        else:
            # set in forcing variables
            # (units: m/day)
            for forcing_variable in forcing_variables.keys():
                # get the field
                var_out = eval(forcing_variable)
                
                # clip to land mask
                var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))
                
                # set variable
                setattr(self, forcing_variable.lower(), var_out)
                
                # log message
                logger.debug('information on %s imported from PCR-GLOBWB2 for %s' % \
                             (forcing_variable.lower(), date))
        
        # [ forcing: water quality ] ...............................................................
        #
        # read in water quality forcing datasets
        constituent_shortterm_quality = {}
        
        for source_name in self.water_management.source_names:
            constituent_shortterm_quality[source_name] = {}
            for constituent_name in self.water_quality.constituent_names:
                # get the key
                key = '%s_%s' % (source_name, constituent_name)
                
                # get value if dataset is available
                if self.model_flags['water_quality_flag']:
                    
                    # stand-alone QUAlloc version
                    if online_coupling_to_quality == False:
                        # get the field
                        var_out = read_file_entry( \
                                  filename                = self.water_quality_forcing_info[key]['ncfilename'], \
                                  variablename            = self.water_quality_forcing_info[key]['ncvariable'], \
                                  inputpath               = self.water_quality_forcing_info[key]['inputpath'], \
                                  clone_attributes        = self.model_configuration.clone_attributes, \
                                  datatype                = pcr.Scalar, \
                                  date                    = date, \
                                  date_selection_method   = 'nearest', \
                                  allow_year_substitution = False, \
                                  )
                        # log message
                        logger.debug('information on %s %s short-term quality read for %s' % \
                                     (source_name, constituent_name, date))
                    
                    # coupled QUAlloc version: DynQual
                    else:
                        # get the field
                        var_out = eval(key)
                        msg_str = 'information on %s %s short-term quality imported from DynQual for %s' % \
                                     (source_name, constituent_name, date)
                        
                        # verify if variable is not None, else make it zeros
                        if isinstance(var_out, NoneType):
                            var_out = pcr.spatial(pcr.scalar(0))
                            msg_str = 'no %s %s short-term quality is given for %s; a value of zero is considered' % \
                                      (source_name, constituent_name, date)
                        
                        # log message
                        logger.debug(msg_str)
                
                # set zero value if dataset is not available
                else:
                    var_out = pcr.spatial(pcr.scalar(0))
                    logger.debug('no %s %s short-term quality is given for %s; a value of zero is considered' % \
                                 (source_name, constituent_name, date))
                
                # cover NaN to zero concentration values and clip map to land mask
                var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))
                
                # set variable
                constituent_shortterm_quality[source_name][constituent_name] = var_out
                setattr(self, key, var_out)
        
        # set variable
        setattr(self.water_management.water_quality, 'constituent_shortterm_quality', constituent_shortterm_quality)
        
        # [ forcing: water management features ] .........................................................
        #
        # [ desalinated water use ]
        # read in desalinated water use datasets (if activated)
        flag_name = 'desalinated_water_use_flag'
        file_name = 'desalinated_water_use'
        if self.model_flags[flag_name]:
            
            # read in the desalinated water use
            var_out = read_file_entry( \
                      filename                = self.model_configuration.water_management[file_name], \
                      variablename            = file_name, \
                      inputpath               = self.model_configuration.general['inputpath'], \
                      clone_attributes        = self.model_configuration.clone_attributes, \
                      datatype                = pcr.Scalar, \
                      date                    = date, \
                      date_selection_method   = 'exact', \
                      allow_year_substitution = True, \
                      )
            
            # clip to land mask
            var_out = pcr.ifthen(self.landmask, pcr.cover(var_out, 0))
            
            # set variable
            setattr(self, file_name, var_out)
            
            # log message
            logger.debug('information on %s read for %s' % (file_name, date))
        
        # [ pumping capacity ]
        # read in regional water pumping capacity (if activated)
        for source_name in self.water_management.source_names:
            flag_name = '%s_pumping_capacity_flag' % source_name
            file_name = '%s_regional_pumping_capacity' % source_name
            
            if self.model_flags[flag_name]:
                # evaluate if date is January 1st
                # as values are yearly totals
                # [ToDo] include if statement that accounts for first time-step
                #        in the model in case run does not start on January 1st
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
                    
                    # set variable
                    setattr(self, '%s_pumping_capacity' % source_name, regional_pumping_capacity)
                    
                    # log message
                    logger.debug('information on %s regional pumping capacity read for %s' % 
                                 (source_name, date))
        
        
        # ******************************************************************************************
        # * long-term                                                                              *
        # ******************************************************************************************
        
        if date.day == 1:
            
            # **********************************************************
            # * pumping capacity                                       *
            # **********************************************************
            #
            # update withdrawal capacity
            # based on regional water pumping capacity (if activated)
            for source_name in self.water_management.source_names:
                flag_name = '%s_pumping_capacity_flag' % source_name
                
                if self.model_flags[flag_name]:
                    # evaluate if date is January 1st
                    # as values are yearly totals
                    # [ToDo] include if statement that accounts for first time-step
                    #        in the model in case run does not start on January 1st
                    if date.day == 1 and date.month == 1:
                        
                        # get variable
                        regional_pumping_capacity = getattr(self, '%s_pumping_capacity' % source_name)
                        
                        # calculate the withdrawal capacity
                        # (units: m3/day)
                        self.water_management.update_withdrawal_capacity( \
                                        source_name            = source_name, \
                                        regional_pumping_limit = regional_pumping_capacity['regional_pumping_limit'], \
                                        region_ids             = regional_pumping_capacity['region_ids'], \
                                        region_ratios          = regional_pumping_capacity['region_ratios'], \
                                        time_step_length       = self.model_time.time_step_length, \
                                        date                   = date)
                    # log message
                    logger.info('Pumping capacity is considered to limit %s withdrawals for %s.' % \
                                (date, source_name))
            
            
            # **********************************************************
            # * long-term availability                                 *
            # **********************************************************
            #
            # get the long-term availability for a given date
            # (units: m3/day)
            surfacewater_availability, groundwater_availability = \
                self.water_management.get_longterm_availability_for_date( \
                                  date              = date, \
                                  ldd               = self.surfacewater.ldd, \
                                  waterdepth        = self.surfacewater.storage, \
                                  mannings_n        = self.surfacewater.mannings_n, \
                                  channel_gradient  = self.surfacewater.channel_gradient, \
                                  channel_width     = self.surfacewater.channel_width, \
                                  channel_length    = self.surfacewater.channel_length, \
                                  time_step_seconds = self.model_time.seconds_per_day)
            
            
            # **********************************************************
            # * long-term demands                                      *
            # **********************************************************
            #
            # get the long-term sectoral gross water demands for a given date
            # (units: m3/day)
            gross_demand_per_sector = \
                self.water_management.get_longterm_demand_for_date( \
                                  date              = date)
            
            
            # **********************************************************
            # * long-term potential withdrawal                         *
            # **********************************************************
            #
            # allocate the long-term demand to the long-term availability given the date
            # and the model settings for the time increment and return the withdrawal
            # that is met (renewable) and potentially unmet (non-renewable) for the
            # available sources
            self.water_management.update_longterm_potential_withdrawals_for_date( \
                                  availability      = {'surfacewater': surfacewater_availability, \
                                                       'groundwater' : groundwater_availability}, \
                                  demand            = gross_demand_per_sector, \
                                  date              = date)
        
        # dictionaries with the actual renewable and non-renewable withdrawals
        # have been initialized with the allocation of the demand to the poten-
        # tial withdrawals; actual withdrawals are updated iteratively and any
        # unmet demand is subdivided to the other sources within the same zone.
        # these are updated using the remaining entries in the source names
        # set the source names to process the unmet demand
        source_names_to_be_processed = self.water_management.sources_unmet_demand[:]
        
        
        # ******************************************************************************************
        # * short-term                                                                             *
        # ******************************************************************************************
        
        # **************************************************************
        # * short-term demands                                         *
        # **************************************************************
        #
        # initialize the gross and net demand per sector for current date
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
                              date         = date)
        
        
        # **************************************************************
        # * desalinated water allocation                               *
        # **************************************************************
        #
        # allocate the desalinated water use
        # on a given date to the selected sectors, i.e., domestic and manufacture
        # (units: m3/day)
        if self.model_flags['desalinated_water_use_flag']:
            self.water_management.allocate_desalinated_water_for_date( \
                              availability = self.desalinated_water_use * self.cellarea, \
                              date         = date)
        
        
        # **************************************************************
        # * short-term potential withdrawals                           *
        # **************************************************************
        #
        # update the long-term potential withdrawals
        # based on the short-term gross water demands
        # (units: m3/day)
        self.water_management.update_shortterm_potential_withdrawals_for_date(date)
        
        
        # **************************************************************
        # * surface water withdrawal                                   *
        # **************************************************************
        #
        # define surface water as the source name and
        # remove it from the potential sources to reuse
        source_name = 'surfacewater'
        source_names_to_be_processed.remove(source_name)
        
        # [ total potential withdrawal ] ...............................
        #
        # set the long-term potential withdrawal per sector
        # as the total of the non-renewable and renewable withdrawals 
        # (units: m3/day)
        potential_withdrawal_per_sector = \
                     self.water_management.get_total_potential_withdrawal(source_name)
        
        
        # [ surface water available ] ..................................
        #
        # stand-alone QUAlloc version
        if online_coupling_to_quantity == False:
            # get the channel runoff
            # (units: m/day)
            self.channel_runoff = self.precipitation - \
                                 self.surfacewater.water_cropfactor * self.referencepotet
            
            # get the return flow
            # (units: m/day)
            total_return_flow = self.water_management.total_return_flow / self.cellarea
            
            # get the total runoff 
            # (units: m/day)
            self.surfacewater.get_total_runoff( \
                          direct_runoff  = self.direct_runoff, \
                          interflow      = self.interflow, \
                          base_flow      = self.groundwater.total_base_flow / \
                                          self.model_time.time_step_length, \
                          channel_runoff = self.channel_runoff, \
                          return_flow    = total_return_flow, \
                          date          = date)
            
            # get surface water available
            # as the sum of:
            #    - surface water storage at the start of the time-step 
            #    - total runoff over the time-step
            # (units: m/day)
            surfacewater_available = \
                self.surfacewater.storage * self.surfacewater.fraction_water + self.surfacewater.total_runoff
        
        # coupled QUAlloc version
        else:
            # surface water availability is defined by the channel storage
            # (units: m/day)
            surfacewater_available = deepcopy(surfacewater_storage)
            
            # set the total runoff
            # (units: m/day)
            self.surfacewater.total_runoff = deepcopy(surfacewater_totalrunoff)
        
        
        # [ actual withdrawals ] .......................................
        #
        # get the short-term potential surface water withdrawal per sector
        # based on water quality and actual surface water availability
        # (units: m3/day)
        potential_withdrawal_per_sector = \
            self.water_management.update_surfacewater_potential_withdrawals( \
                  surfacewater_available                   = surfacewater_available, \
                  longterm_potential_withdrawal_per_sector = potential_withdrawal_per_sector)
        
        potential_withdrawal = sum_list(list(potential_withdrawal_per_sector.values()))
        
        # stand-alone QUAlloc version
        if online_coupling_to_quantity == False:
            # get the actual renewable withdrawals
            # by routing the total runoff with the potential withdrawals
            # (units: m3/day)
            actual_withdrawal = self.surfacewater.update( \
                                          potential_withdrawal = potential_withdrawal, \
                                          time_step_seconds    = self.model_time.seconds_per_day)
        
        # coupled QUAlloc version
        else:
            # get the actual rewable withdrawals
            # based on instantaneous channel storage
            # (units: m3/day)
            actual_withdrawal = pcr.ifthen(pcr.defined(self.surfacewater.ldd), \
                                           pcr.max(0, \
                                                   pcr.min(potential_withdrawal, \
                                                           surfacewater_available * self.cellarea)))
            
            # set variables in the surface water module
            #  - discharge (units: m3/s)
            #  - surface water storage (units: m)
            self.surfacewater.storage   = deepcopy(surfacewater_storage)
            self.surfacewater.discharge = deepcopy(surfacewater_discharge)
        
        
        # **************************************************************
        # * re-distribute withdrawals                                  *
        # **************************************************************
        #
        # re-distribute renewable withdrawal by sector
        # (units: m3/day)
        renewable_withdrawal = deepcopy(actual_withdrawal)
        renewable_withdrawal_per_sector = \
             dict((sector_name, \
                   actual_withdrawal * pcr_return_val_div_zero(potential_withdrawal_per_sector[sector_name], \
                                                               potential_withdrawal, \
                                                               very_small_number)) \
                  for sector_name in self.water_management.sector_names)
        
        # set the non-renewable withdrawal to zero
        # as all surface water withdrawals are currently renewable
        nonrenewable_withdrawal = pcr.ifthen(self.landmask, pcr.scalar(0))
        nonrenewable_withdrawal_per_sector = \
                                  dict((sector_name, \
                                        nonrenewable_withdrawal) \
                                       for sector_name in self.water_management.sector_names)
        
        # set the actual surface water withdrawal and add any unmet demand to the
        # potential non-renewable withdrawal for the remaining, allowable sources
        self.water_management.update_withdrawals( \
                     source_name                        = source_name, \
                     renewable_withdrawal_per_sector    = renewable_withdrawal_per_sector, \
                     nonrenewable_withdrawal_per_sector = nonrenewable_withdrawal_per_sector, \
                     source_names_to_be_processed       = source_names_to_be_processed, \
                     water_available = surfacewater_available * self.cellarea, \
                     date            = self.model_time.date)
        
        
        # **************************************************************
        # * groundwater withdrawal                                     *
        # **************************************************************
        #
        # Base flow is here the total over the time-step and is used here 
        # to compute the water availability. It is passed directly to the
        # surface water module from the groundwater module as it lags by 
        # one time step.
        source_name = 'groundwater'
        source_names_to_be_processed.remove(source_name)
        
        # [ total potential withdrawal ] ...............................
        #
        # set the long-term potential withdrawal per sector
        # as the total of the non-renewable and renewable withdrawals
        # (units: m3/day)
        potential_withdrawal_per_sector = \
                     self.water_management.get_total_potential_withdrawal(source_name)
        
        # [ groundwater available ] ....................................
        #
        # stand-alone QUAlloc version
        if online_coupling_to_quantity == False:
            # aggregate total withdrawals from all sectors as water slice
            # (units: m/day)
            potential_withdrawal = \
                  sum_list(list(potential_withdrawal_per_sector.values())) / self.cellarea
            
            # update the total base flow and the total recharge
            # (units: m/period)
            self.groundwater.get_storage( \
                                   recharge             = self.groundwater_recharge, \
                                   potential_withdrawal = potential_withdrawal, \
                                   time_step_length     = self.model_time.time_step_length, \
                                   date                 = self.model_time.date)
            
            # get groundwater available
            # as:
            #    + groundwater storage at the start of the period (month)
            #    + total recharge over at the end of the period (month)
            #    - total base flow over at the end of the period (month)
            # (units: m at the end of the period)
            storage = \
                self.groundwater.storage + \
                (self.groundwater.total_recharge - self.groundwater.total_base_flow)
            
            groundwater_available = deepcopy(storage)
        
        # coupled QUAlloc version
        else:
            # groundwater availability is defined by the groundwater storage
            # (units: m/day)
            storage = deepcopy(groundwater_storage)
            groundwater_available = deepcopy(storage)
            
            # set the (total) recharge and (total) base flow
            # (units: m/day)
            self.groundwater.total_recharge = deepcopy(self.groundwater_recharge)
            self.groundwater.total_base_flow = deepcopy(groundwater_baseflow)
        
        # [ actual withdrawals ] .......................................
        #
        # get the short-term potential groundwater withdrawal per sector
        # based on water quality and actual groundwater availability
        # (units: m3/period)
        potential_withdrawal_per_sector, groundwater_availability = \
            self.water_management.update_groundwater_potential_withdrawals( \
                  groundwater_available                    = groundwater_available, \
                  longterm_potential_withdrawal_per_sector = potential_withdrawal_per_sector, \
                  time_step_length                         = self.model_time.time_step_length)
        
        potential_withdrawal = sum_list(list(potential_withdrawal_per_sector.values()))
        
        # calculate the actual renewable and non-renewable withdrawals
        # (units: m3/day)
        renewable_withdrawal = \
                  pcr.min(groundwater_availability, \
                          potential_withdrawal)
        
        nonrenewable_withdrawal = \
                  pcr.max(0, \
                          potential_withdrawal - renewable_withdrawal)
        
        renewable_withdrawal    /= self.model_time.time_step_length
        nonrenewable_withdrawal /= self.model_time.time_step_length
        
        # [ update storage ] ...........................................
        #
        # storage is the groundwater renewable storage before water withdrawals (units m)
        # stand-alone QUAlloc version
        if online_coupling_to_quantity == False:
            # set the variables in the groundwater routine (units: m/period)
            self.groundwater.update(renewable_withdrawal    * self.model_time.time_step_length / self.cellarea, \
                                    nonrenewable_withdrawal * self.model_time.time_step_length / self.cellarea)
        
        # coupled QUAlloc version
        else:
            # set groundwater storage for the current date
            self.groundwater.storage = deepcopy(groundwater_storage)
        
        
        # **************************************************************
        # * re-distribute withdrawals                                  *
        # **************************************************************
        #
        # re-distribute renewable withdrawals by sector
        # (units: m3/day)
        renewable_withdrawal_per_sector = \
             dict((sector_name, \
                   renewable_withdrawal * \
                    pcr_return_val_div_zero(potential_withdrawal_per_sector[sector_name], \
                                            potential_withdrawal, \
                                            very_small_number)) \
                  for sector_name in self.water_management.sector_names)
        
        # re-distribute non-renewable withdrawals by sector
        # (units: m3/day)
        nonrenewable_withdrawal_per_sector = \
             dict((sector_name, \
                   nonrenewable_withdrawal * \
                    pcr_return_val_div_zero(potential_withdrawal_per_sector[sector_name], \
                                            potential_withdrawal, \
                                            very_small_number)) \
                  for sector_name in self.water_management.sector_names)
        
        # set the actual groundwater withdrawal and add any unmet demand to the
        # potential non-renewable withdrawal for the remaining, allowable sources
        self.water_management.update_withdrawals( \
                     source_name                        = source_name, \
                     renewable_withdrawal_per_sector    = renewable_withdrawal_per_sector, \
                     nonrenewable_withdrawal_per_sector = nonrenewable_withdrawal_per_sector, \
                     source_names_to_be_processed       = source_names_to_be_processed, \
                     water_available = groundwater_availability, \
                     date            = self.model_time.date)
        
        
        # **************************************************************
        # * water allocation                                           *
        # **************************************************************
        #
        # [ water allocation ] .........................................
        # allocate the actual withdrawals to the demands,
        # get the consumption and the return flows
        self.water_management.allocate_withdrawal_to_demand_for_date( \
                   date         = self.model_time.date, \
                   availability = {'surfacewater':surfacewater_available * self.cellarea,\
                                   'groundwater' :groundwater_availability})
        
        
        # **************************************************************
        # * long-term updating                                         *
        # **************************************************************
        #
        # long-term variables are accumulated over the month and, only on the
        # last day, these are divided by the number of days in the time increment
        # (i.e., monthly = 1, daily = 28/29/30/31) to obtain the average value
        # over the month
        
        # update long-term water availability
        #   groundwater_storage    (units: m per day)
        #   surfacewater_discharge (units: m3/s)
        #   surfacewater_runoff     (units: m/day)
        self.water_management.update_longterm_availability( \
                                    groundwater_storage    = storage, \
                                    surfacewater_discharge = self.surfacewater.discharge, \
                                    surfacewater_runoff     = self.surfacewater.total_runoff, \
                                    date                   = date)
        
        # update long-term gross water demands
        # (units: m/day)
        self.water_management.update_longterm_demand( \
                                    date = date)
        
        # update long-term potential withdrawal based on date
        # (units: m3/day)
        self.water_management.update_longterm_potential_withdrawals( \
                                    date = date)
        
        # update long-term water quality based on date
        # (units: oC, mg/L, cfu/100mL)
        self.water_management.water_quality.update_longterm_quality( \
                                    source_names = self.water_management.source_names, \
                                    time_step    = self.model_time.time_increment, \
                                    date         = date)
        
        # returns None
        return None
        
        # *****************
        # * end of update *
        # *****************

    def finalize_year(self):
        
        # update the total water availability
        # log message
        logger.info('last day of year %d: updating water availability, demand and quality' % \
                    self.model_time.year)
        
        # update annual water availability
        self.water_management.update_annual_water_availability()
        self.water_management.update_annual_water_demand()
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
