#!/usr/bin/env python
#  -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# CALEROS Landscape Development Model:                                        #
#                                                                             #
# Copyright (c) 2019 Ludovicus P.H. (Rens) van Beek - r.vanbeek@uu.nl         #
# Department of Physical Geography, Faculty of Geosciences,                   #
# Utrecht University, Utrecht, The Netherlands.                               #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
# netCDF_file_info: module specifying the class that holds all the            #
# information of netCDF files                                                 #
#                                                                             #
# This development is part of the CALEROS landscape development.              #
#                                                                             #
###############################################################################

import sys
import datetime
import logging

import numpy as np
import pcraster as pcr
import netCDF4 as nc

from types import BuiltinMethodType
from copy import copy, deepcopy

from spatialDataSet2PCR import compareSpatialAttributes, spatialAttributes, spatialDataSet

logger = logging.getLogger(__name__)

# all netCDF information is stored in a class object holding information in the
# form of dictionaries with the file names as key on:
# - a cache holding all open netCDF file objects
# - a store of all non-dimensional variables in the netCDF objects with their
#   dimensions;
# - a store of all non-dimensional variables in the netCDF objects with the
#   associated time steps.

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
              'make netCDFs accessible via a root and for multiple years', \
              'make sure scaled netCDFs are read correctly', \
              '',\
              ))

print ('\nDevelopmens for netCDF recipes class:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

# global variables
NoneType = type(None)
DictType = type(dict)

# general information for file conversions
date_selection_methods = ['nearest', 'before', 'after', 'exact']

conversion_methods = { \
                      'Scalar':         float, \
                      'Nominal':        int, \
                      'Boolean':        bool, \
                      'Ordinal':        int, \
                      'Directional':    float, \
                      'Ldd':            int, \
                      }

datatypes = { \
                      'Scalar':         'FLOAT32', \
                      'Nominal':        'INT32', \
                      'Boolean':        'BYTE', \
                      'Ordinal':        'FLOAT32', \
                      'Directional':    'FLOAT32', \
                      'Ldd':            'BYTE', \
                      }


resample_methods = { \
                      'Scalar':         'bilinear', \
                      'Nominal':        'nearest', \
                      'Boolean':        'nearest', \
                      'Ordinal':        'nearest', \
                      'Directional':    'bicubic', \
                      'Ldd':            'nearest', \
                      }


nc_mv_id_str = '_FillValue'
# default netCDF type and variable attributes set
# createVariable functions called with all variables specified set to the following default values
# testVerbose flags output
default_nc_format = 'NETCDF3_CLASSIC'
default_zlib = False; default_complevel = 4; default_shuffle = True;
default_fletcher32 = False; default_contiguous = False; default_chunksizes = None;
default_endian = 'native'; default_least_significant_digit = None; default_fill_value = -999.9; 
exclude_list = ['group', 'set', '_', '__']
test_verbose = False

def update_year_of_date(date, new_year, dates):
    
    '''
update_year_of_date: function that finds the offset in days between the date \
specified and the same day in the new year specified and applies it subsequently \
to dates, which can be an iterable or a single date. Returns a copy of dates \
with the years changed accordingly.

'''
    # initialize the new dates
    seq_type = True
    if isinstance(dates, list):
        new_dates = dates[:]
        
    elif isinstance(dates, np.ndarray):
        new_dates = deepcopy(dates)
        new_dates = new_dates.ravel()
        
    else:
        new_dates = [dates]
        seq_type = False
        
    # and check on the data type
    if not isinstance(new_dates[0], datetime.datetime):
        'dates have not the correct datetime datetime format'
    
    # get the new dates
    date_offset = datetime.datetime(new_year, date.month, date.day) - \
                    datetime.datetime(date.year, date.month, date.day)
    
    # iterate over the days
    for ix in range(len(new_dates)):
        
        # update
        new_dates[ix] = new_dates[ix] + date_offset

    # finally, check if the input is a single entry variable or not
    if not seq_type:
        new_dates = new_dates[0]

    # return the new dates
    return new_dates

def substitute_years_of_dates(dates, date):
    '''Returns a copy of a list of dates in which the years have been updated 
to include the year of the specified date'''

    #-initialization
    
    #-process, get the nearest date and available years
    date_index = get_date_index(date, dates, 'nearest')
    nearest_date = dates[date_index]

    # return the updated dates
    return update_year_of_date(nearest_date, date.year, dates)

def get_date_index(date, dates, date_selection_method, \
            substituted_dates = False):
    
    '''
get_date_index: function that returns the position of the date specified in an array of dates, 
following the index date_selection_methodion method specified: exact, before, after, nearest. 
This function reproduces the date2index function of the netCDF4 package but 
circumvents the problem that the original function cannot read from a standard dictionary.

'''
    
    # create array with time_delta objects and indices
    time_delta = dates.copy()
    
    # check on the type of time_delta
    if not isinstance(dates[0], type(date)):
        for ix in range(len(time_delta)):
            # update the date
            time_delta[ix] = datetime.datetime(time_delta[ix].year, \
                                               time_delta[ix].month, \
                                               time_delta[ix].day, \
                                               time_delta[ix].hour, \
                                               time_delta[ix].minute, \
                                               time_delta[ix].second, \
                                               time_delta[ix].microsecond)
    time_delta = time_delta - date
    date_index = np.arange(time_delta.size)
    
    # masked array operation for python 3.x and higher
    if isinstance(time_delta, np.ma.core.MaskedArray):
        time_delta = np.array(time_delta.tolist())
    
    #-find zero value
    if np.size(dates[time_delta == datetime.timedelta(0)]) > 0 and \
            not substituted_dates:
        return np.arange(dates.size)[time_delta == datetime.timedelta(0)][0]
    
    elif date_selection_method == 'exact':
        return None
    
    elif date_selection_method == 'before':
        mask  = time_delta < datetime.timedelta(0)

        if time_delta[mask].size > 0:
            mask_value = time_delta[mask].max()
            return date_index[time_delta == mask_value][0]
        else:
             return None
         
    elif date_selection_method == 'after':
        mask = time_delta > datetime.timedelta(0)
        if time_delta[mask].size > 0:
            mask_value = time_delta[mask].min()
            return date_index[time_delta == mask_value][0]
        else:
            return None
        
    elif date_selection_method == 'nearest':
        time_delta = np.abs(time_delta)
        return np.arange(dates.size)[time_delta == time_delta.min()][0]
    
    else:
        sys.exit('index date_selection_method %s is not allowed or does not yield a result' % date_selection_method)

def match_date_in_dates(date, dates, date_selection_method = 'exact'):

    '''

match_dates: function that allows for date substitution in the water management \
module.

    Input:
    ======
    date:                   date provided;
    dates:                  array of available dates to which the provided
                            dates should be matched;
    date_selection_method:  date selection method, default value is 'exact';
                            can be 'exact', 'before', or 'after'.

    Output:
    =======
    date_index:             date index matching the sought date to the av-
                            ailable dates;
    matched_date:           the date in the available dates that matches the
                            date index;
    message_str:            message string on the date selction for subsequent
                            logging.

'''

    # get the date index
    date_index = get_date_index( \
            date, dates, date_selection_method)

    message_str = str.join(' ', (\
            'for the water management module', \
            'a %s match is found for date %s'))
    message_str = message_str % (date_selection_method, date)

    # check whether the date was matched or not: if not, no
    # match could be found and substitution of the date is
    # actually invoked
    if isinstance(date_index, NoneType):

        # set the replacement year, that is dependent on the
        # selection method chosen
        if date_selection_method == 'exact':
            replacement_year = date.year
        elif date_selection_method == 'before':
            replacement_year = date.year - 1
        elif date_selection_method == 'after':
            replacement_year = date.year + 1
        else:
            pass

        # log warning
        message_str = str.join(' ', (\
            'for the water management module'
            'date substitution is allowed to find the %s match', \
            'for year %d for which the dummy year %d is used'))
        message_str =  message_str % \
            (date_selection_method, \
              date.year, replacement_year)

        # reset the date selection method to nearest if the
        # date selection method is exact
        if date_selection_method == 'exact':
            date_selection_method = 'nearest'
        
        # and the corresponding date
        replacement_date = update_year_of_date(date, replacement_year, date)

        # replace the date in the years
        dates = substitute_years_of_dates(dates, replacement_date)
        
        # and get the corresponding date index
        date_index = get_date_index( \
                date, dates, date_selection_method, \
                substituted_dates = True)

    # finally, retrieve the matched dates and set the band
    matched_date = dates[date_index]
    
    # messsage string
    message_str = str.join('; ', \
                           (message_str, \
                            'the date %s is matched to %s' % \
                            (date, matched_date)))

    # return date_index, matched date and message_Str
    return date_index, matched_date, message_str

def print_dictionary(dobj, level  = 0):
    '''iterates over all items in a dictionary and print key,value pairs'''
    for key, value in dobj.items():
        if isinstance(value,list) or isinstance(value,np.ndarray):
            vals = value[:]
            value = [vals[0],'...',vals[-1]]
        print (' ' * level * 4 , key,)
        try:
            print (value)
        except:
            print

def get_nc_object_attributes(obj, \
         exclude_list = [], \
         exclude_class_objects = True):
    '''Reads all information from the netCDF dataset object specified and returns a dictionary
 of key, value pairs; should only be applied on copies of netCDF dataset objects
 to avoid unwanted changes in the dataset'''
    #-create dictionary and iterate over output
    dobj = {}
    for item in dir(obj):
        #-check on allowable entries
        include_entry = True
        for check_item in exclude_list:
            len_str = min(len(check_item), len(item))
            
            if item[:len_str]  == check_item:
                include_entry = include_entry and False

        # add the attributes
        if include_entry:
            if isinstance(getattr(obj,item), BuiltinMethodType):
                if not exclude_class_objects:
                    try:
                        dobj[item] = getattr(obj,item)()
                    except:
                        pass
            else:
                dobj[item] = getattr(obj,item)
    return dobj

def get_nc_attributes(ncfilename):

    '''
 get_nc_attributes: function thatreads netcdf file specified and returns 
 dictionaries of its format, attributes, dimensions, dimension values for 
 reuse and the attributes of its variables.
 
     Input:
     ======
     ncfilename:        file name of the netCDF file to be processed
     
     Output:
     =======
     ncformat:          netcdf file format.
     attributes:        netcdf dataset attributes.
     dimattrs:          a copy of the attributes of the netcdf dataset 
                        ordered dictionary of dimensions; stored as a
                        dictionary with the dimension name as key.
    varattrs:           a copy of the attributes of each variable in the netcdf
                        dataset ordered dictionary of variables;
                        stored as a nested dictionary with the variable name as
                        key and all attributes stored stored subsequently as a
                        single key, value pair; this includes a copy of the
                        numpy datatype and dimensions of each variable.
                        
 Keys specified in varattrs but not in dimvalues identify variables holding
 information on variables'''
 
    # todo: include groups
    # note: information is passed partly as copies as netcdf dataset variables and dimensions cannot be accessed
    # when file is closed
    #-local variables: specific keys for dimensions and variables to be added to their attributes and the function to extract them
    #-open netcdf file for read

    rootgrp = nc.Dataset(ncfilename, 'r',)
    
    #-retrieve file format, dimensions, atributes, variables, and missing value
    nc_format      = rootgrp.file_format
    nc_dimensions  = rootgrp.dimensions.copy()   
    nc_variables   = rootgrp.variables.copy()

    # exclude high level entries; class objects are ignored by default
    exclude_list = ['_']

    # get the attributes
    nc_attributes  = {}
    
    for key, value in rootgrp.__dict__.items():
        nc_attributes[key] =  value

    #-get the attributes of the dimensions as dictionary and the values of the
    # dimensions as dictionary for reuse
    nc_dimattrs = {}
    for key in nc_dimensions.keys():
        # add information on the dimension
        nc_dimattrs[key] = get_nc_object_attributes(nc_dimensions[key], \
                exclude_list = exclude_list)
        # add information on the variable
        if key in nc_variables.keys():
            nc_dimattrs[key]['values']= nc_variables[key][:]
            nc_dimattrs[key]['size']= nc_variables[key].size
        
    #-get all attributes for each variable for reuse
    nc_varattrs = {}
    for key in nc_variables.keys():
        nc_varattrs[key] = get_nc_object_attributes(nc_variables[key], \
                exclude_list = exclude_list)

    #-close file
    rootgrp.close()

    #-return output
    return nc_format, nc_attributes, nc_dimattrs, nc_varattrs

def initialize_ncfile(ncfilename,  \
                     nc_format = None, \
                     nc_global_attributes= {}, \
                     cache = {}, \
                     ):

    '''
        
initialize_netCD: initializes the netCDF file with the name and format specified\
     and set its attributes for output.

'''

    # get the nc_format
    if isinstance(nc_format, NoneType):
        nc_format = default_nc_format

    # initialize the netCDF file
    
    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp= nc.Dataset(ncfilename, 'w', format= nc_format)

    #-set netCDF attributes
    for attribute, value in nc_global_attributes.items():
        rootgrp.setncattr(attribute, value)

    # if not in cache, close the file
    if not ncfilename in cache:
        rootgrp.close()

    # return None
    return None

def add_variable_to_netCDF(\
                ncfilename, \
                name, \
                datatype, \
                dimensions, \
                cache = {}, \
                **nc_optional_info, \
                ):    
    '''
                
add_variable_to_netCDF: function that adds a variable to the netCDF file using\
the netCDF4 createVariable function.

    Input:
    ======
    required inputs:
    ----------------
    ncFile:             the file name of the netCDF dataset in which the variable will be created
    name:               the name of the variable by which it is stored
    datatype:           the data type, numpy datatype object or its dtype.str attribute
                        or any of the supported specifiers included: 'S1' or 'c' (NC_CHAR),
                        'i1' or 'b' or 'B' (NC_BYTE), 'u1' (NC_UBYTE), 'i2' or
                        'h' or 's' (NC_SHORT), 'u2' (NC_USHORT), 'i4' or 'i' or
                        'l' (NC_INT), 'u4' (NC_UINT), 'i8' (NC_INT64), 'u8' (NC_UINT64),
                        'f4' or 'f' (NC_FLOAT), 'f8' or 'd' (NC_DOUBLE).
    dimensions:         tuple with dimensions.
    
    optional inputs:
    ----------------
    cache:              dictionary with already open files.
    
    Any or all of the following:
    zlib, complevel, shuffle,
    fletcher32, contiguous, chunksizes, endian,
    least_significant_digit, fill_value;
    nc_var_attrs:       a dictionary holding all netCDF variable attributes;
                        if this dictionary holds any of the above parameters but it is
                        specified explicitly, the latter is given precedence. Otherwise it is
                        set implicitly using the default, global values.
   
    '''    

    #-local variables - process optional keywords and set defaults first
    nc_defaults = {}    
    nc_defaults['varname']    = name 
    nc_defaults['datatype']   = datatype
    nc_defaults['dimensions'] = dimensions
    nc_defaults['zlib']       = default_zlib
    nc_defaults['complevel']  = default_complevel
    nc_defaults['shuffle']    = default_shuffle
    nc_defaults['fletcher32'] = default_fletcher32
    nc_defaults['contiguous'] = default_contiguous
    nc_defaults['chunksizes'] = default_chunksizes
    nc_defaults['endian']     = default_endian
    nc_defaults['fill_value'] = default_fill_value
    nc_defaults['least_significant_digit'] = default_least_significant_digit

    # get optional information
    # nc_var_attrs
    if 'nc_var_atttrs' in nc_optional_info.keys() and \
            isinstance(nc_optional_info['nc_var_attrs'], DictType):
        nc_var_attrs = nc_optional_info['nc_var_attrs'].copy()
    else:
        nc_var_attrs = {}    

    # pass any key words to the defaults
    for key, value in nc_optional_info.items():
        
        # is the key not the dictionary, then add it
        if key != 'nc_var_attrs':
            
            # add the value
            if not key in nc_var_attrs.keys():
                
                # add the key
                nc_var_attrs[key] = value

    # check and update the defaults
    nc_var_keys = list(nc_var_attrs.keys())
    for key in nc_var_keys:
        
        # check if it is a default, then update the predefined value
        if key in nc_defaults.keys():
            
            # replace the value
            nc_var_attrs[key] = nc_var_attrs[key]
            
            # and strip the key word from the attributes
            del nc_var_attrs[key]

    # get the dataset
    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, 'a')

    # create variable in netCDF dataset
    # first, use the defaults
    nc_variable = rootgrp.createVariable(**nc_defaults)

    # next, get any outstanding keys from nc_var_attrs
    if 'ncattrs' in nc_var_attrs.keys():
        
        # get the keys and values
        for key, value in nc_var_attrs['nc_attrs'].items():
            
            # add the value
            nc_variable.setncattr(key, value)
        
    else:
        
        # add the other remaining attributes
        for key, value in nc_var_attrs.items():
            
            # add the value
            nc_variable.setncattr(key, value)
   
    #-update and close
    rootgrp.sync()

    # if not in cache, close the file
    if not ncfilename in cache:
        rootgrp.close()

    # return None
    return None

def add_dimension_to_netCDF( \
                ncfilename, \
                name, \
                datatype, \
                unlimited = False, \
                values = [], \
                cache = {}, \
                **nc_optional_info, \
               ):    

    '''

add_dimension_to_netCDF: function that adds a dimension and the associated \
variable information to the netCDF file.

    Input:
    ======
    required inputs:
    ----------------
    ncFile:             the file name of the netCDF dataset in which the variable will be created
    name:               the name of the dimension that is created
    datatype:           the data type, numpy datatype object or its dtype.str attribute
                        or any of the supported specifiers included: 'S1' or 'c' (NC_CHAR),
                        'i1' or 'b' or 'B' (NC_BYTE), 'u1' (NC_UBYTE), 'i2' or
                        'h' or 's' (NC_SHORT), 'u2' (NC_USHORT), 'i4' or 'i' or
                        'l' (NC_INT), 'u4' (NC_UINT), 'i8' (NC_INT64), 'u8' (NC_UINT64),
                        'f4' or 'f' (NC_FLOAT), 'f8' or 'd' (NC_DOUBLE).
    
    optional inputs:
    ----------------
    unlimited:          boolean specifying whether the dimension is unlimited or not;
    values:             if not unlimited, then provide the values that characterize
                        the dimension;
    cache:              dictionary with already open files.

    Any or all of the following to create the variables:
    zlib, complevel, shuffle,
    fletcher32, contiguous, chunksizes, endian,
    least_significant_digit, fill_value;
    nc_var_attrs:       a dictionary holding all netCDF variable attributes;
                        if this dictionary holds any of the above parameters but it is
                        specified explicitly, the latter is given precedence. Otherwise it is
                        set implicitly using the default, global values.
   
    '''

    # get the dataset
    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, 'a')

    #-add dimension
    if unlimited:
        size = None
    else:
       size = len(values)

    # add the dimension
    rootgrp.createDimension(name, size)

    #-update and close
    rootgrp.sync()

    # if not in cache, close the file
    if not ncfilename in cache:
        rootgrp.close()

    # add the variable information
    add_variable_to_netCDF( \
                ncfilename = ncfilename, \
                name = name, \
                datatype = datatype, \
                dimensions = (name,), \
                cache = cache, \
                **nc_optional_info, \
                )

    if not isinstance(size, NoneType):

        # get the dataset
        if ncfilename in cache:
            rootgrp = cache[ncfilename]
        else:
            rootgrp = nc.Dataset(ncfilename, 'a')
    
        # add the values
        rootgrp.variables[name][:] = values[:]
        
        #-update and close
        rootgrp.sync()
    
        # if not in cache, close the file
        if not ncfilename in cache:
            rootgrp.close()

    # return None
    return None

def add_data_to_netCDF( \
                ncfilename, \
                name, \
                variable_array, \
                dim_slices, \
                cache = {}, \
                **additional_info):

    '''

add_data_to_netCDF: function that adds data to the netCDF file specified.

    Input:
    ======
    required inputs:
    ----------------
    ncfilename:         the file name of the netCDF dataset in which the variable will be created;
    name:               the name of the variable that is updated;
    variable_array:     the array with that will be added to the netCDF;
    dim_slices:         slice of dimensions: dictionary with the location on where
                        the variable field should be inserted; default value
                        is None in which case the value is inserted at the end/  
                        over the full domain. If specified, the values should be
                        a tuple of the first and last indices of the slice;
    cache:              dictionary with already open files;
    additional_info:    additional information; this should include a
                        list of dates (dates) as well as the name of the 
                        dimension that holds the time stamps (time_dimension)
                        to add temporal data.

    Output:
    =======
    None:               returns None.

'''    

    # get the dataset
    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, 'a')

    # copy the slice with dimension and the variable array
    dim_slices     = deepcopy(dim_slices)
    variable_array = deepcopy(variable_array)
    
    # simple temporal update
    simple_update = True

    # dimension names
    dim_keys= list(rootgrp.variables[name].dimensions)

    # add all dates
    time_dimension = ''
    if 'time_dimension' in additional_info.keys() \
            and 'dates' in additional_info.keys():
        
        # set the dates and time dimension
        time_dimension = additional_info['time_dimension']
        dates = additional_info['dates']

        # temporal information, add the dates
        nc_time = rootgrp.variables[time_dimension]
        if len(nc_time[:]) > 0:
            try:
                date_ixs = np.array(nc.date2index(dates, nc_time)).ravel()
            except:
                date_ixs = np.arange(len(dates)) + len(nc_time[:])
        else:
            date_ixs = np.arange(len(dates)) + len(nc_time[:])
            
        # add the dates
        date_ixs = date_ixs.tolist()
        for date_ix in date_ixs:
       
            # add the date to the netCDF time variable
            date = dates[date_ixs.index(date_ix)]
            nc_time[date_ix] = nc.date2num(date, nc_time.units, nc_time.calendar)

        # insert the date indices in case the dimension values are not set
        if isinstance(dim_slices[time_dimension], NoneType):

            # simple_update
            simple_update = True
            
            # insert the first and last position
            dim_slices[time_dimension] = (date_ixs[0], date_ixs[-1] + 1)
        
        else:
            simple_update = False
    
    # update the other indices of the dimension slices if set to None
    # and retrieve the required size of the variable array in case it is sliced
    # and for the maximum non-temporal dimensions, in which the processing is
    # simplified
    req_size = 1

    for dim_key in dim_keys:

        # insert the indices
        if isinstance(dim_slices[dim_key], NoneType):
            
            # set the indices
            dim_slices[dim_key] = (0, len(rootgrp.variables[dim_key][:]))
            
        # decide on simple processing
        if dim_key != time_dimension:
            simple_update = simple_update and \
                    ((dim_slices[dim_key][1] - dim_slices[dim_key][0]) == \
                            len(rootgrp.variables[dim_key][:]))

        # update the required size
        req_size = req_size * (dim_slices[dim_key][1] - dim_slices[dim_key][0])
        
    # update the required size
    while variable_array.size != req_size:
        sys.exit('array sizes do not match!')

    # and decide on the processing:
    # a simple update is possible if the variable array has the correct size
    # to add a single time stap
    
    if simple_update:
        
        # timed or not?
        if time_dimension != '':
            # timed: write to the last field
            rootgrp.variables[name][dim_slices[time_dimension][0], ...] = variable_array[:]
        else:
            # not timed, write the full array
            rootgrp.variables[name][...] = variable_array[:]
    
    else:   
        
        # additional processing is necessary to add the data
    
        # create a boolean array and an array of indices that is used to 
        # set the corresponding entries to True
        mask_array = np.ones(rootgrp.variables[name][:].shape, dtype = bool)
        g_ixs = np.indices(mask_array.shape)
        # iterate over the dimensions and set the boolean mask to True
        for dim_key in dim_keys:
            
            # get the key position
            dim_ix = dim_keys.index(dim_key)
    
            # set the mask
            mask_ix = (g_ixs[dim_ix] >= dim_slices[dim_key][0]) & \
                    (g_ixs[dim_ix] < dim_slices[dim_key][1])
    
            # update the mask array
            mask_array = mask_array & mask_ix
            
        # use the mask to update the variable array and the corresponding mask
        v_a =  rootgrp.variables[name][:].copy()
           
        v_a[mask_array] = variable_array[:].ravel()
            
        rootgrp.variables[name][:] = v_a.copy()
       
    #-update and close
    rootgrp.sync()

    # delete temporary variables
    v_a = None
    mask_array = None
    mask_ix = None
    del v_a, mask_array, mask_ix

    # if not in cache, close the file
    if not ncfilename in cache:
        rootgrp.close()

    # return None
    return None

def get_nc_dates(ncfilename):

    '''
get_nc_dates: returns a list of sorted dates from a timet netCDF file.

''' 
    # set the dates
    nc_dates = []

    # get all information
    nc_format, nc_attributes, nc_dimattrs, nc_varattrs = \
                get_nc_attributes(ncfilename)
    
    # get the time variable
    time_dimension = None
    for variablename in nc_dimattrs.keys():
        if 'calendar' in nc_varattrs[variablename]:
            time_dimension = variablename
    
    # get the dates if data are timed and store it for later access
    if not isinstance(time_dimension, NoneType):
        nc_dates = nc.num2date( \
                        nc_dimattrs[time_dimension]['values'], \
                        nc_varattrs[time_dimension]['units'], \
                        nc_varattrs[time_dimension]['calendar'], \
                        )
    
        nc_dates.sort()
        nc_dates = nc_dates.tolist()

    # return the dates
    return nc_dates

#==============================================================================

#///start of file with class definitions///

class netCDF_file_info(object):
    
    def __init__(self,):

        # init the object
        object.__init__(self)
        
        # create cache of open files and information
        self.cache             = dict()
        self.attributes        = dict()
        self.dimensions        = dict()
        self.variables         = dict()
        self.spatialattributes = dict()
        self.time_dimension    = dict()
        

    def test_ncfile_in_cache(self, ncfilename):
        '''tests if the specified nc file name is present in the cache'''
        
        return ncfilename in self.cache.keys()

    def add_ncfile_to_cache(self, ncfilename, \
                            clone_attributes = None, \
                            forced_non_spatial = False):
        '''adds the information from the specified netCDF file to this instance \
holding netCDF information to facilitate access.'''

        # add the netCDF file if it is not yet in the cache
        if not ncfilename in self.cache.keys():

            # get all information
            nc_format, nc_attributes, nc_dimattrs, nc_varattrs = \
                        get_nc_attributes(ncfilename)

            # add the information to the cache           
            self.attributes[ncfilename] = nc_attributes.copy()
            self.dimensions[ncfilename] = nc_dimattrs.copy()
            self.variables[ncfilename]  = nc_varattrs.copy()
            
            # retrieve, if possible, the global fill value
            if nc_mv_id_str in self.attributes[ncfilename].keys():
                global_mv = self.attributes[ncfilename][nc_mv_id_str]
            else:
                global_mv = default_fill_value

            # open the file and add it to the cache
            self.cache[ncfilename] = nc.Dataset(ncfilename)

            # get the time variable
            time_dimension = None
            for variablename in self.dimensions[ncfilename].keys():
                if 'calendar' in self.variables[ncfilename][variablename]:
                    time_dimension = variablename

            # get the dates if data are timed and store it for later access
            if not isinstance(time_dimension, NoneType):
                self.time_dimension[ncfilename] = time_dimension
                dates = nc.num2date( \
                                self.dimensions[ncfilename][time_dimension]['values'], \
                                self.variables[ncfilename][time_dimension]['units'], \
                                self.variables[ncfilename][time_dimension]['calendar'], \
                                )
                self.dimensions[ncfilename][time_dimension]['values'] = dates[:]

            # check on the dimensions once the information is added
            # and determine whether the data set is spatial and temporal
            # and add missing value information for the variable, if not
            # included already
            for variablename in self.variables[ncfilename].keys():
                
                # set a default missing value identifier
                mv = None
                
                # get the dimensions
                nc_dims = self.obtain_dimensions(ncfilename, variablename)
                
                # test if the number of dimensions is larger than zero
                # and is unequal to the variable name
                process_non_dimensional_variable = False
                # test on the number and get the value
                if len(nc_dims) > 0:
                    process_non_dimensional_variable = nc_dims[0] != variablename

                # process any non-dimensional variable if appropriate
                if process_non_dimensional_variable:

                    # initialize information on the nature of the data:
                    # timed and spatial
                    self.variables[ncfilename][variablename]['timed_variable'] = False
                    self.variables[ncfilename][variablename]['spatial_variable'] = False

                    # first check on the spatial data, this depends on whether the
                    # data is forced as non_spatial or not
                    if not forced_non_spatial:

                        data_attributes = None 
                        # try to get the spatial attributes
                        try:

                            # get data set if possible
                            data_attributes = spatialAttributes('NETCDF:"%s":%s' %\
                                                        (ncfilename, variablename))
                        except:

                            logger.debug('%s in %s is treated as a non-spatial dataset' % \
                                         (variablename, ncfilename))

                        # data attributes returned, process                        
                        if not isinstance(data_attributes, NoneType):

                            # compare extent
                            fits_extent, same_resolution, \
                                    x_resample_ratio, y_resample_ratio = \
                                compareSpatialAttributes(data_attributes, \
                                                         clone_attributes)
                            same_clone = fits_extent and same_resolution

                            # and set the missing value
                            mv = getattr(data_attributes, 'noDataValue')

                            # identify the variable as a spatial variable and set the spatial attributes
                            # object of the nc_info instance
                            self.variables[ncfilename][variablename]['spatial_variable']  = True

                            # set the spatialattributes entry for this file
                            if not ncfilename in self.spatialattributes.keys():
                                self.spatialattributes[ncfilename] = {}
                                
                            if not variablename in self.spatialattributes[ncfilename].keys():
                                
                                self.spatialattributes[ncfilename][variablename] = same_clone
                                
                            else:
                                
                                self.spatialattributes[ncfilename][variablename] = \
                                    self.spatialattributes[ncfilename][variablename] | same_clone

                            # appears to be non-spatial
                            logger.debug('%s in %s is treated as a spatial dataset' % \
                                         (variablename, ncfilename))
                            
                    else:
                        # definitely non-spatial
                        logger.debug('%s in %s is defined as a non-spatial dataset' % \
                                     (variablename, ncfilename))

                    # decide if the variable is timed, this only works if the
                    # first dimension is the time dimension
                    if not isinstance(time_dimension, NoneType):

                        # timed variable if the first dimension is that of time
                        self.variables[ncfilename][variablename]['timed_variable'] = \
                                 nc_dims[0] == time_dimension
                        
                        # definitely temporal
                        logger.debug('%s in %s is defined as a temporal dataset' % \
                                     (variablename, ncfilename))

                    else:
                        logger.debug('%s in %s is defined as a non-temporal dataset' % \
                                     (variablename, ncfilename))
                        
                    # for all non-dimensional variables, add missing value
                    # information, if necessary;
                    # check if the missing value information is stored by the
                    # attribute nc_mv_id_str ('_FillValue')
                    if not nc_mv_id_str in self.variables[ncfilename][variablename].keys():
                        
                        if isinstance(mv, NoneType):
                           mv = global_mv
                           
                        # set missing value
                        self.variables[ncfilename][variablename][nc_mv_id_str ] = mv

            # log message
            logger.info('neCDF file %s added to cache' % ncfilename)

    def remove_ncfile_from_cache(self, ncfilename):
        '''closes the netCDF file and remove all information from the \
specified netCDF file.'''

        # add the netCDF file if it is not yet in the cache
        if ncfilename in self.cache.keys():
            
            # close the file name
            self.cache[ncfilename].close()
            del self.cache[ncfilename]
            
            # remove all information from the cache           
            del self.attributes[ncfilename]
            del self.dimensions[ncfilename]
            del self.variables[ncfilename]

            # log message
            logger.info('neCDF file %s removed from cache' % ncfilename)

    def obtain_dimensions(self, ncfilename, variablename):
        '''gets the dimensions as a tuple from a netCDF file if the variable is matched'''
        
        # set the default output
        nc_dims = ()
                
        # test if the variable name is present in the netCDF File, otherwise
        # remove it
        if variablename in self.variables[ncfilename].keys():
            # get the dimensions if it is present in the netCDF variables
            nc_dims = self.variables[ncfilename][variablename]['dimensions']
            
        else:
            # remove the file name, it does not contain the correct information
            self.remove_ncfile_from_cache(ncfilename)

        # return the dimensions
        return nc_dims

    def test_var_in_ncfile(self, ncfilename, variablename):
        '''
test_var_in_ncfile: function that tests if a variable is present in the \
netCDF file specified.
     
'''
        return variablename in self.variables[ncfilename]

    def read_nc_field(self, ncfilename, \
                      variablename, \
                      clone_attributes = None, \
                      datatype = pcr.Scalar, \
                      date = None, \
                      date_selection_method = 'exact', \
                      allow_year_substitution = 'False', \
                      forced_non_spatial = False, \
                      ):
        
        '''
        
read_nc_field: function that retrieves an entry of the variable name within \
the specified netCDF file name with consideration of the spatial attributes of \
the present clone. It can automatically retrieve the corresponding date, \
depending on the type of match specified.

'''
        # recast the date selection method as lower case
        date_selection_method = date_selection_method.lower()
        
        if not date_selection_method in date_selection_methods:
            logger.error('date selection method %s is not available' % date_selection_method)

        # first invoke the add_ncfile_to_cache if the variable
        # is not included yet
        # test if the netCDF file is in the cache, otherwise add it
        if not self.test_ncfile_in_cache(ncfilename):
                       
            self.add_ncfile_to_cache(ncfilename, clone_attributes, forced_non_spatial)
            
        # test if the clone attributes are defined in case a variable is spatially explicit
        if isinstance(clone_attributes, NoneType) and \
                self.variables[ncfilename][variablename]['spatial_variable'] and \
                not self.spatialattributes[ncfilename][variablename]:
            
            # raise error
            logger.error('No clone attributes are specified to extract spatial information for variable %s from %s' % \
                         (variablename, ncfilename))

        # get the dimensions to decide on how the data will be processed
        nc_dims = self.obtain_dimensions(ncfilename, variablename)

        # halt with error if the variable is not encountered
        if nc_dims == ():
            # log message
            logger.error('neCDF file %s does not contain information on the requested variable %s' % \
                         (ncfilename, variablename))
       
        # if it is a timed variable, then get the position and band
        if self.variables[ncfilename][variablename]['timed_variable']:
            
            # get the name of the variable representing the time
            time_dimension = self.time_dimension[ncfilename]

            # get the date index possibly from the substituted dates
            dates = self.dimensions[ncfilename][time_dimension]['values'].copy()

            # initialize an empty message_str
            message_str = ''

            # get the date index: first check if an actual match can be found
            if not allow_year_substitution:

                # is the date present? then make the match exact and                 
                true_date = False

                if date in dates:
                    
                    true_date = True
                    date_selection_method = 'exact'

                else:
                    
                    message_str = 'for variable %s, date %s is not encountered in %s' % \
                                (variablename, date, ncfilename) 

                    if date_selection_method == 'exact':

                        logger.error(message_str)
                        sys.exit(message_str)

                # get the date index from the actual dates
                date_index = nc.date2index( \
                            date, \
                            self.cache[ncfilename].variables[time_dimension], \
                            self.variables[ncfilename][time_dimension]['calendar'], \
                            select = date_selection_method, \
                            )
   
                # true date
                true_date = True

            # year substitution is allowed, find the corresponding match
            else:
                
                date_index = get_date_index( \
                            date, dates, date_selection_method)
                
                # check whether the date was matched or not: if not, no
                # match could be found and substitution of the date is
                # actually invoked
                if isinstance(date_index, NoneType):

                    # set the replacement year, that is dependent on the
                    # selection method chosen
                    if date_selection_method == 'exact':
                        replacement_year = date.year
                    elif date_selection_method == 'before':
                        replacement_year = date.year - 1
                    elif date_selection_method == 'after':
                        replacement_year = date.year + 1
                    else:
                        pass
                    
                    # log warning
                    message_str = str.join(' ', ('for variable %s', \
                        'date substitution is allowed to find the %s match', \
                        'for year %d for which the dummy year %d is used'))
                    message_str =  message_str % \
                        (variablename, date_selection_method, \
                         date.year, replacement_year)
                    logger.warning(message_str)

                    # reset the date selection method to nearest if the
                    # date selection method is exact
                    if date_selection_method == 'exact':
                        date_selection_method = 'nearest'
                    
                    # and the corresponding date
                    replacement_date = update_year_of_date(date, replacement_year, date)

                    # replace the date in the years
                    dates = substitute_years_of_dates(dates, replacement_date)
                    
                    # and get the corresponding date index
                    date_index = get_date_index( \
                            date, dates, date_selection_method, \
                            substituted_dates = True)
                    
                # true date
                true_date = False 
        
            # finally, retrieve the matched dates and set the band
            matched_date = dates[date_index]
            band_number = date_index + 1
            
        else:

            # set the date index to None
            date_index = None
            band_number = None

        # all processed, retrieve the data ... finally :-p
        # there are four options
        # 1) it is non-spatial, non-temporal
        # 2) it is spatial, non-temporal
        # 3) it is non-spatial, temporal
        # 4) it is spatial, temporal
        # in these cases, the band and arrays have to be read
               
        # set the conversion method in case the output is non-spatial
        # and the resample method
        datatype_str = str(datatype)
        if 'VALUESCALE.' in datatype_str:
            datatype_str = datatype_str.replace('VALUESCALE.', '')
        conversion_method = conversion_methods[datatype_str]
        resample_method = resample_methods[datatype_str]

        # first, process the spatial data
        if self.variables[ncfilename][variablename]['spatial_variable']:
                    
            # in the case of spatial input, processing depends whether the
            # data can be read directly 
            # if data cannot be read directly, gdal_translate is used to read
            # the data
            if not self.spatialattributes[ncfilename][variablename]:

                # first, perform an additional test in case the date type is LDD
                # as no resampling is allowed in that case
                if datatype == pcr.Ldd or datatype == str(pcr.Ldd):
                    
                    # get the data attributes
                    data_attributes = spatialAttributes('NETCDF:"%s":%s' %\
                                        (ncfilename, variablename))

                    # compare extent
                    fits_extent, same_resolution, \
                            x_resample_ratio, y_resample_ratio = \
                        compareSpatialAttributes(data_attributes, \
                                                 clone_attributes)
                    
                    # raise error if not the same resolution
                    if not same_resolution:
                        
                        logger.error('data of type LDD as read from %s for %s can not be resampled' % \
                                     (ncfilename, variablename))

                # if the areas are different, get the actual area using gdal_translate
                var_out = getattr(spatialDataSet( \
                                  variablename, \
                                  'NETCDF:"%s":%s' % (ncfilename, variablename), \
                                  datatypes[datatype_str], \
                                  datatype, \
                                  clone_attributes.xLL, \
                                  clone_attributes.xUR, \
                                  clone_attributes.yLL, \
                                  clone_attributes.yUR, \
                                  clone_attributes.xResolution, \
                                  clone_attributes.yResolution, \
                                  pixels = clone_attributes.numberCols, \
                                  lines = clone_attributes.numberRows, \
                                  resampleMethod = resample_method, \
                                  band = band_number, \
                                  ), variablename)
            
            
            else:
                # data can be converted directly using numpy2pcr; get the array
                if self.variables[ncfilename][variablename]['timed_variable']:
                    # get the variable array from the timed variable
                    var_array = self.cache[ncfilename][variablename][date_index, :]
                else:
                   # not timed, get the appropriate dimension
                    var_array = self.cache[ncfilename][variablename][date_index, :]
                
                # array returned, convert to the map
                var_out = pcr.numpy2pcr(datatype, var_array, \
                                        self.variables[ncfilename][variablename][nc_mv_id_str])
                
                # delete the array
                var_array = None
                del var_array
                
        # else, non-spatial data
        else:

            # if temporal, return the appropriate value
            if self.variables[ncfilename][variablename]['timed_variable']:

                    if self.variables[ncfilename][variablename]['ndim'] == 1:
                        
                        # get the current date only
                        var_out = conversion_method(\
                                self.cache[ncfilename][variablename][date_index])
        
                    else:
                        
                        # get the slice
                        var_out = self.cache[ncfilename][variablename][date_index, :]

            else:

                # return all values
                var_out = self.variables[ncfilename][variablename][:]


        # finally log the message and return the value
        message_str = 'value of %s read from %s' % \
            (variablename, ncfilename)
        if self.variables[ncfilename][variablename]['timed_variable']:
            message_str = str.join(' ',\
                                   (message_str, \
                                    'for %s' % date))
            if not true_date or matched_date != date:
                message_str = str.join(' ',\
                                       (message_str, \
                                        'which was matched by %s using a %s match' %\
                                        (matched_date, date_selection_method)))
                
        # log message
        logger.debug(message_str)

        # return the output
        return var_out

    def close_cache(self):
        
        # close all the file names
        for ncfilename in list(self.cache.keys()):
            
            # close the file name
            self.remove_ncfile_from_cache(ncfilename)

        # return None
        return None

#/end of netCDF input class/

#///start of file with class definitions///            

class netCDF_output_handler(object):
    
    '''
   
netCDF_output_handler: class that holds all information to create and update \
output netCDF files.
    
'''
    
    def __init__(self, model_configuration):
                
        # init the object
        object.__init__(self)

        # create cache of open files and information:
        # cache is a dictionary of open files,
        # dimensions a dictionary with the dimensions per variable
        # and the timed variable
        self.cache             = dict()
        self.dimensions        = dict()
        self.time_dimension    = dict()
        
        # latitudes and longitudes
        self.latitude  = pcr.pcr2numpy(pcr.ycoordinate(pcr.spatial(pcr.boolean(1))), default_fill_value)[:, 0]
        self.longitude = pcr.pcr2numpy(pcr.xcoordinate(pcr.spatial(pcr.boolean(1))), default_fill_value)[0, :]

        # netcdf format and zlib setup 
        self.default_fill_value = default_fill_value
        self.nc_format = default_nc_format
        self.zlib = default_zlib
        if 'nc_format' in model_configuration.reporting.keys():
            self.format = model_configuration.convert_string_to_input( \
                    model_configuration.reporting['nc_format'], str)
        if 'zlib' in model_configuration.reporting.keys():
            self.format = model_configuration.convert_string_to_input( \
                    model_configuration.reporting['zlib'], bool)

        # set the general netcdf attributes (based on the information given in the ini/configuration file) 
        self.nc_global_attributes = self.get_general_netcdf_attributes(model_configuration)
        
        # set the dimensions
        self.dimension_info = {}
        
        # add the dimension info for time and the x and y coordinate
        self.dimension_info['time'] = { \
                           'dim_pos'        : 0, \
                           'is_temporal'    : True, \
                           'is_spatial'     : False, \
                            'datatype'      : 'f4', \
                            'unlimited'     : True, \
                            'long_name'     : 'Days since 1901-01-01', \
                            'standard_name' : 'Days since 1901-01-01', \
                            'calendar'      : 'standard', \
                            'units'         : 'Days since 1901-01-01', \
                           }
        self.dimension_info['latitude'] = { \
                           'dim_pos'        : 1, \
                           'is_temporal'    : False, \
                           'is_spatial'     : True, \
                            'datatype'      : 'f4', \
                            'unlimited'     : False, \
                            'long_name'     : 'latitude', \
                            'standard_name' : 'latitude', \
                            'units'         : 'degrees_north', \
                           }
        self.dimension_info['longitude'] = { \
                           'dim_pos'        : 2, \
                           'is_temporal'    : False, \
                           'is_spatial'     : True, \
                            'datatype'      : 'f4', \
                            'unlimited'     : False, \
                            'long_name'     : 'longitude', \
                            'standard_name' : 'longitude', \
                            'units'         : 'degrees_east', \
                           }

        # returns None
        return None

    def get_general_netcdf_attributes(self, model_configuration):

        # netCDF attributes
        nc_default_attributes = { \
                                 'title'        : 'QUAlloc run for %s' % \
                                                  model_configuration.general['scenarioname'], \
                                 'history'      : 'Created on %s' % \
                                                   model_configuration._timestamp_str, \
                                 'institution'  : 'Dept. Physical Geography, Utrecht University (r.vanbeek@uu.nl)', \
                                 }
        nc_global_attributes = {}

        # add all attributes from the dictionary
        for key, attribute in model_configuration.netcdfattrs.items():
            
            # set the attributes
            nc_global_attributes[key] = attribute
        
        # add defaults if necessary
        for key, attribute in nc_default_attributes.items():
            
            # set the attributes
            if not key in nc_global_attributes.keys():
                nc_global_attributes[key] = attribute

        # return the attributes 
        return nc_global_attributes

    def test_ncfile_in_cache(self, ncfilename):
        '''tests if the specified nc file name is present in the cache'''
        
        return ncfilename in self.cache.keys()

    def add_ncfile_to_cache(self, ncfilename, \
                            ):
        '''adds the information from the specified netCDF file to this instance \
holding netCDF information to facilitate access.'''

        # add the netCDF file if it is not yet in the cache
        if not self.test_ncfile_in_cache(ncfilename):

            self.cache[ncfilename] = nc.Dataset(ncfilename, \
                                                'w', format = self.nc_format)
            
            # log message
            logger.info('neCDF file %s added to cache' % ncfilename)

    def remove_ncfile_from_cache(self, ncfilename):
        '''closes the netCDF file and remove all information from the \
specified netCDF file.'''

        # remove the netCDF file if it isin the cache
        if ncfilename in self.cache.keys():
            
            # close the file name
            self.cache[ncfilename].close()
            del self.cache[ncfilename]

            # log message
            logger.info('neCDF file %s removed from cache' % ncfilename)


    def initialize_ncfile(self, ncfilename):
        
        '''
initialize_ncfile: function of the netCDF_output_handler that wraps around \
initialize_ncfile to create the output netCDF file and adds it to the cache \
for reduced IO.
        
'''
        
        # add the netCDF file to the cache
        self.add_ncfile_to_cache(ncfilename)
        
        # initialize the netCDF file
        initialize_ncfile( \
                          ncfilename = ncfilename, \
                          nc_format = self.nc_format, \
                          nc_global_attributes = self.nc_global_attributes, \
                          cache = self.cache)

    def initialize_nc_variable(self, \
                               ncfilename, \
                               variablename, \
                               variable_units, \
                               is_spatial , \
                               is_temporal, \
                               long_name, \
                               standard_name, \
                               datatype, \
                               ):

        '''

initialize_nc_variable: function of the netCDF_output_handler that creates the \
variable and adds all the necessary dimensions to the output netCDF file and \
includes its dimensions and time dimension to the cache when appropriate.
Function wraps around the functions add_dimension_to_netCDF and add_variable_to_netCDF.

'''

        # initialize the netCDF file if necessary
        if not self.test_ncfile_in_cache(ncfilename):
            self.initialize_ncfile(ncfilename)
        
        # get the dimensions
        var_dim_keys = []
        for dim_key, dim_info in self.dimension_info.items():
            dim_pos = dim_info['dim_pos']
            if dim_info['is_spatial'] and is_spatial:
                var_dim_keys.insert(dim_pos, dim_key)
            if dim_info['is_temporal'] and is_temporal:
                var_dim_keys.insert(dim_pos, dim_key)
                
        # get the dimensions
        nc_dim_keys = list(self.cache[ncfilename].dimensions.keys())
        
        # add the dimension
        for dim_key in var_dim_keys:
            if not dim_key in nc_dim_keys:
                
                # add the dimension
                logger.debug('dimension %s added to %s' % \
                             (dim_key, ncfilename))
                
                # get the dim_info
                dim_info = self.dimension_info[dim_key]
                
                # is temporal
                if dim_info['is_temporal']:

                    add_dimension_to_netCDF( \
                        ncfilename    = ncfilename, \
                        name          = dim_key, \
                        datatype      = datatype, \
                        unlimited     = dim_info['unlimited'], \
                        cache         = self.cache, \
                        long_name     = dim_info['long_name'], \
                        standard_name = dim_info['standard_name'], \
                        calendar      = dim_info['calendar'], \
                        units         = dim_info['units'], \
                        )

                    # add the temporal variable
                    self.time_dimension[ncfilename] = dim_key
                
                # is spatial
                elif dim_info['is_spatial']:
                    
                    # spatial coordinates
                    values = getattr(self, dim_key)
                    add_dimension_to_netCDF( \
                        ncfilename    = ncfilename, \
                        name          = dim_key, \
                        datatype      = datatype, \
                        unlimited     = dim_info['unlimited'], \
                        values        = values, \
                        cache         = self.cache, \
                        long_name     = dim_info['long_name'], \
                        standard_name = dim_info['standard_name'], \
                        units         = dim_info['units'], \
                        )                   
                    
                else:
                    pass

        # add the dimension for the current variable
        if not ncfilename in self.dimensions.keys():
            self.dimensions[ncfilename] = {variablename : var_dim_keys}
        

        # add the variable
        logger.debug('variable %s added to %s' % \
                     (variablename, ncfilename))

        # initialize the variable
        add_variable_to_netCDF( \
            ncfilename    = ncfilename, \
            name          = variablename, \
            datatype      = datatype, \
            dimensions    = var_dim_keys, \
            cache         = self.cache, \
            long_name     = long_name, \
            standard_name = standard_name, \
            units         = variable_units, \
            )

        # all done, return None
        return None

    def add_data_to_netCDF(self, \
                           ncfilename, \
                           variablename, \
                           variable_array, \
                           **additional_info):
        
        '''

add_data_to_netCDF: function of the netCDF_output_handler that adds the output \
to netCDF file for the variable specified.
Function wraps around the function add_data_to_netCDF and initializes the tuple \
of the dimensions to be written.
     
'''

        # get the necessary info: this includes the time variable and the date
        # for temporal variables
        is_timed = False
        
        if 'is_timed' in additional_info.keys():
            is_timed = additional_info['is_timed']

        if is_timed:
            if not 'time_dimension' in additional_info.keys():
                additional_info['time_dimension']  = self.time_dimension[ncfilename]

        # initialize the dimension slices
        dim_slices = dict([(dim_key, None) 
                           for dim_key in self.dimensions[ncfilename][variablename]])

        # call the function to add the data to the netCDF file
        add_data_to_netCDF( \
                ncfilename     = ncfilename, \
                name           = variablename, \
                variable_array = variable_array, \
                dim_slices     = dim_slices, \
                cache          = self.cache, \
                **additional_info)


        # return None
        return None

    def close_cache(self):
        
        # close all the file names
        for ncfilename in list(self.cache.keys()):
            
            # close the file name
            self.remove_ncfile_from_cache(ncfilename)

        # return None
        return None

#/end of netCDF output class/
