# water quality module of the QUAlloc model

###########
# modules #
###########
import logging
import pcraster as pcr
from model_time      import match_date_by_julian_number, get_weights_from_dates
from basic_functions import pcr_return_val_div_zero, sum_list, max_dicts
from allocation      import get_zonal_total

####################
# global variables #
####################
# dictionary of water quality constituents' concentrations
# with variable name in configuration file as key
# and variable name in NetCDF file as value
# groundwater-related variables are set to None as they are not developed... yet
water_quality_forcing_variables = { \
            'surfacewater_temperature' : 'waterTemperature', \
            'surfacewater_organic'     : 'organic', \
            'surfacewater_salinity'    : 'salinity', \
            'surfacewater_pathogen'    : 'pathogen', \
            'groundwater_temperature'  : None, \
            'groundwater_organic'      : None, \
            'groundwater_salinity'     : None, \
            'groundwater_pathogen'     : None, \
            }

# small number to avoid zero divisions in PCRaster
very_small_number = 1.0e-12

# large number for sectors without water quality restrictions
unattainable_threshold = 1.0e20

# type set to identify None (compatible with python 2.x)
NoneType = type(None)

# set the logger
logger = logging.getLogger(__name__)

###################
# class definition #
###################

class water_quality(object):

    def __init__(self, \
                 landmask, \
                 time_increment, \
                 source_names, \
                 constituent_names, \
                 constituent_limits, \
                 quality_update_weight, \
                 surfacewater_longterm_temperature, \
                 surfacewater_longterm_organic, \
                 surfacewater_longterm_salinity, \
                 surfacewater_longterm_pathogen, \
                 groundwater_longterm_temperature, \
                 groundwater_longterm_organic, \
                 groundwater_longterm_salinity, \
                 groundwater_longterm_pathogen, \
                 ):
        
        # initialise the object
        object.__init__(self)
        
        # [ general ]
        # set general variables
        self.landmask           = landmask
        self.time_increment     = time_increment
        
        # set water quality related parameters
        self.constituent_names  = constituent_names
        self.constituent_limits = constituent_limits
        
        # [ long-term water quality ]
        self.quality_update_weight = quality_update_weight
        
        for source_name in source_names:
            for constituent_name in self.constituent_names:
                # define variable
                var_str  = '%s_longterm_%s' % (source_name, constituent_name)
                var_out = eval(var_str)
                
                # cover NaN to zero concentration values and clip map to land mask
                for date, values in var_out.items():
                    values = pcr.ifthenelse(values >= 0, values, pcr.scalar(0))
                    var_out[date] = pcr.ifthen(self.landmask, values)
                
                # set variable and a list of correspondent sorted dates
                setattr(self, var_str, var_out)
                setattr(self, var_str+'_dates', sorted(list(var_out.keys())))
        
        # compute the annual average water quality
        self.surfacewater_annual_temperature = pcr.scalar(0)
        self.surfacewater_annual_organic     = pcr.scalar(0)
        self.surfacewater_annual_salinity    = pcr.scalar(0)
        self.surfacewater_annual_pathogen    = pcr.scalar(0)
        self.groundwater_annual_temperature  = pcr.scalar(0)
        self.groundwater_annual_organic      = pcr.scalar(0)
        self.groundwater_annual_salinity     = pcr.scalar(0)
        self.groundwater_annual_pathogen     = pcr.scalar(0)
        self.update_annual_water_quality(source_names)
        
        # set the state names
        self.report_state_info = { \
              'surfacewater_longterm_temperature' : 'surfacewater_longterm_temperature', \
              'surfacewater_longterm_organic'     : 'surfacewater_longterm_organic'    , \
              'surfacewater_longterm_salinity'    : 'surfacewater_longterm_salinity'   , \
              'surfacewater_longterm_pathogen'    : 'surfacewater_longterm_pathogen'   , \
              'groundwater_longterm_temperature'  : 'groundwater_longterm_temperature' , \
              'groundwater_longterm_organic'      : 'groundwater_longterm_organic'     , \
              'groundwater_longterm_salinity'     : 'groundwater_longterm_salinity'    , \
              'groundwater_longterm_pathogen'     : 'groundwater_longterm_pathogen'    , \
              }
        
        # returns None
        return None




    def update_annual_water_quality(self, \
                                     source_names):
        
        '''
        update_annual_water_quality :
                   update the overall water quality over the year per
                   source and constituent equivalent to water_management.
        '''
        
        # log message
        logger.info('Total water quality over a year updated')

        # update the long-term total values
        for source_name in source_names:
            for constituent_name in self.constituent_names:
                
                # get key
                var_in  = '%s_longterm_%s' % (source_name, constituent_name)
                
                # get dictionary of dates (months) and 
                # calculate their correspondent weights
                dates   = getattr(self, var_in+'_dates')
                weights = get_weights_from_dates(dates)
                
                # get concentration map of constituent per source and 
                # update the long-term total constituent per source
                longterm_constituent_quality = getattr(self, var_in)
                values = sum(list(weights[date] * \
                                  longterm_constituent_quality[date] \
                                  for date in dates))
                
                # set variable
                var_out = '%s_annual_%s' % (source_name, constituent_name)
                setattr(self, var_out, values)
        
        # returns None
        return None



    def get_longterm_quality_for_date(self, \
                                       source_names, \
                                       date, \
                                       ):
        
        # set the message string to log the information
        message_str = 'Long-term water quality for %s at %s level.' % \
                      (date, self.time_increment)
        
        # initialize dictionary with long-term water quality states
        constituent_longterm_states = {}
        
        # evaluate type of potential water quality state (monthly or yearly)
        if self.time_increment in ['monthly','yearly']:
            for source_name in source_names:
                constituent_longterm_states[source_name] = {}
                for constituent_name in self.constituent_names:
                    
                    if self.time_increment == 'monthly':
                        # get the state of the water quality constituents for the matching date
                        # get the time step to update the constituent quality (monthly)
                        # add the message on the matching date to the string
                        
                        # get key
                        var_str = '%s_longterm_%s' % (source_name, constituent_name)
                        
                        # get the machting date
                        dates = getattr(self, var_str+'_dates')
                        date_index, matched_date, sub_message_str = \
                                            match_date_by_julian_number(date, dates)
                        
                        # get the monthly long-term quality
                        longterm_constituent_quality = getattr(self, var_str)
                        constituent_state = longterm_constituent_quality[matched_date]
                        
                        message_str = str.join('\n', \
                                               (message_str, sub_message_str))
                    
                    elif self.time_increment == 'yearly':
                        # set the long-term total water quality
                        var_str = '%s_annual_%s' % (source_name, constituent_name)
                        constituent_state = getattr(self, var_str)
                
                    # set variable
                    constituent_longterm_states[source_name][constituent_name] = \
                                                               constituent_state
        
        else:
            logger.error('the option %s for the time increment in the water quality module is not allowed!' % self.time_increment)
            sys.exit()
        
        # log the message
        logger.info(message_str)
        
        return constituent_longterm_states



    def update_longterm_quality_for_date(self, \
                                          source_names, \
                                          date):
        '''
        update_longterm_quality_for_date: 
                                  function that updates the quality
                                  per zone as a function of the date.
        '''
        
        for source_name in source_names:
            for constituent_name in self.constituent_names:
                
                # get key
                var = '%s_longterm_%s' % (source_name, constituent_name)
                
                # get the time step to update the long-term quality (monthly)
                dates = getattr(self, var+'_dates')
                date_index, matched_date, message_str = \
                                    match_date_by_julian_number(date, dates)
                
                # remove the date from the dictionary and update it with the present value
                # set the value using the weight, if the long-term availability is not
                # defined, cover with the present value
                constituent_longterm_quality = getattr(self, var).pop(matched_date)
                constituent_longterm_quality = \
                    pcr.cover( self.quality_update_weight[source_name]      * self.constituent_shortterm_quality[source_name][constituent_name] + \
                              (1 - self.quality_update_weight[source_name]) * constituent_longterm_quality, \
                              self.constituent_shortterm_quality[source_name][constituent_name])
                
                # reset the date
                getattr(self, var+'_dates')[date_index] = date
                
                # add the value to the dictionary
                getattr(self, var)[date] = constituent_longterm_quality
                
                # echo to screen
                message_str = str.join(' ', \
                                       ('%s from %s availability updated for' \
                                        % (constituent_name, source_name), \
                                        message_str))
                logger.debug(message_str)
        
        # returns None
        return None



    def get_suitability_per_sector(self, \
                                   constituent_state, \
                                   sector_names, \
                                   fractional_flag = False, \
                                   ):
        '''
        get_suitability_per_sector: 
                            function to define the suitability of the
                            available water to be used by a specific sector
        input
        =====
        constituent_state : dictionary with constituent names (keys) and 
                            constituent concentrations/states (values)
        fractional_flag    : boolean; if False, water could either be suitable
                            to be used or not (i.e., 0 or 1)
        
        output
        ======
        suitability_per_sector : 
                            dictionary with sector names (keys) and 
                            overall suitability of available water to be used 
                            (values) expressed as a ratio where 0 is not suitable 
                            and 1 is perfectly suitable
        '''
        
        # initialise water quality suitability fraction maps
        suitability_per_sector = dict((sector_name, \
                                       pcr.spatial(pcr.scalar(1.0))) \
                                      for sector_name in sector_names)
        
        for sector_name in sector_names:
            # initialise a temporal suitability dictionaries
            suitability_per_constituent = {}
            
            for constituent_name in self.constituent_names:
                # read minimum and maximum water quality thresholds
                limit_min = pcr.spatial(pcr.scalar(0.0))
                limit_max = pcr.spatial(pcr.scalar( \
                                self.constituent_limits[sector_name][constituent_name]))
                
                # calculate the suitability fraction and total
                suitability_per_constituent[constituent_name] = \
                    pcr_return_val_div_zero( \
                               constituent_state[constituent_name] - limit_min, \
                               limit_max - limit_min, \
                               very_small_number)
            
            # calculate overall suitability per sector
            # considers constituent with the most unsuitable condition as the predominant factor
            # invert fractions such that unity means perfect suitability and the closer to zero,
            # the worse suitability; zero means unsuitable 
            suitability = 1 - max_dicts(suitability_per_constituent)
            
            suitability = pcr.ifthenelse(suitability > 0.0, \
                                         suitability, \
                                         pcr.ifthenelse(suitability == 0.0, \
                                                        very_small_number, \
                                                        pcr.scalar(0.0)))
            
            # calculate suitability per sector
            if not fractional_flag:
                suitability = pcr.ifthenelse(suitability == 0, pcr.scalar(0), pcr.scalar(1))
            
            # set variable
            suitability_per_sector[sector_name] = \
                                pcr.ifthen(self.landmask, \
                                           pcr.cover(suitability, \
                                                     suitability_per_sector[sector_name]))
        
        # return overall suitability per sector
        return suitability_per_sector



    def get_weights_availability_per_sector(self, \
                                            source_name, \
                                            sector_names, \
                                            prioritization_per_sector, \
                                            zones_per_sector, \
                                            demand_per_sector, \
                                            availability, \
                                            suitability_per_sector = None, \
                                            water_gap_flag = True, \
                                            ):
        '''
        get_weights_availability_per_sector : 
                                    function to calculate the rates to distribute either water availability
                                    or demands based on the quality of the water, the sectoral gross demands
                                    and the sectoral prioritization
        
        input:
        =====
        source_name               : string with the source name
        sector_names              : list with sector names (string)
        prioritization_per_sector : dictionary with sector names (string) as keys and PCRaster maps with
                                    sectoral prioritization (nominal) as values
        zones_per_sector          : dictionary with sector names (string) as keys and PCRaster maps with
                                    allocation zones (nominal) as values
        demand_per_sector         : dictionary with sector names (string) as keys and PCRaster maps with
                                    sectoral gross demands as values (units: m3/period)
        availability              : PCRaster map with water availability of selected source (units: m3/period)
        suitability_per_sector    : dictionary with sector names (string) as keys and PCRaster maps with
                                    water suitability ratios as values
        water_gap_flag             : boolean; if True, sectoral prioritization is taken into account,
                                    if False, all sector has the same priority
        
        output:
        ======
        weight_per_sector      : dictionary with sector names (keys) and the weight of a sector (values) 
                                 over a variable (e.g., availability) considering the water quality
'''
        # initialise the water quality weights per sector
        weight_per_sector = dict((sector_name, \
                                  pcr.spatial(pcr.scalar(1.0))) \
                                 for sector_name in sector_names)
        
        # calculate the water quality weights per sector
        for sector_name in sector_names:
            
            # define sectoral priority
            if not water_gap_flag:
                priority_sector = pcr.spatial(pcr.scalar(1.0))
            else:
                priority_sector = prioritization_per_sector[sector_name] ** -1
            
            # define areal sectoral water demands
            demand_sector_area = get_zonal_total( \
                                     demand_per_sector[sector_name], \
                                     zones_per_sector[sector_name])
            
            demand_total_area  = get_zonal_total( \
                                     sum_list(list(demand_per_sector.values())), \
                                     zones_per_sector[sector_name])
            
            demand_sector_fraction = pcr_return_val_div_zero( \
                                        demand_sector_area, \
                                        demand_total_area, \
                                        very_small_number)
            
            # define sectoral suitability fractions
            if not isinstance(suitability_per_sector, NoneType):
                suitability_sector = suitability_per_sector[sector_name]
            else:
                suitability_sector = pcr.spatial(pcr.scalar(1))
            
            suitability_sector_area = get_zonal_total( \
                                          suitability_sector, \
                                          zones_per_sector[sector_name])
            
            # define suitable water availability
            availability_suitable_sector      = suitability_sector * availability
            availability_suitable_sector_area = get_zonal_total( \
                                                    availability_suitable_sector, \
                                                    zones_per_sector[sector_name])
            
            availability_sector_fraction = pcr_return_val_div_zero( \
                                               suitability_sector_area, \
                                               availability_suitable_sector_area, \
                                               very_small_number)
            
            # calculate the quality weight
            weight = priority_sector * \
                     demand_sector_fraction * \
                     availability_suitable_sector * \
                     availability_sector_fraction
            
            # set variable
            weight_per_sector[sector_name] = weight
        
        # normalise quality weights
        weight_total = sum_list(list(weight_per_sector.values()))
        for sector_name in sector_names:
            weight_per_sector[sector_name] = pcr_return_val_div_zero( \
                                                 weight_per_sector[sector_name], \
                                                 weight_total, \
                                                 very_small_number)
        
        return weight_per_sector




    def get_final_conditions(self):
        '''
        get_final_conditions: function that returns a dictionary holding all states \
        of the water quality module that are necessary for a restart.
        Returns state_info, a dictionary with the key and the value
        '''
        # initialize states
        state_info = {}
        
        # iterate over the report name and attribute name
        for report_name, attr_name in self.report_state_info.items():
            
            # set the state
            state_info[report_name] = getattr(self, attr_name)
        
        # return results
        return state_info

# ///  end of the water quality class ///
