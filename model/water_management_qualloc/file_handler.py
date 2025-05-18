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
# file_handler: module with additional functions to handle input files and    #
# output files for dynamic modelling.                                         #
# This development is part of the CALEROS landscape development.              #
#                                                                             #
###############################################################################

"""
 
file_handler.py: 
 file_handler holds all the necessary functions to process files for input and
 output.

 all netCDF information is stored in a class object holding information in the
 form of dictionaries with the file names as key on:
 - a cache holding all open netCDF file objects
 - a store of all non-dimensional variables in the netCDF objects with their
   dimensions;
 - a store of all non-dimensional variables in the netCDF objects with the
   associated time steps.

"""

###########
# Modules #
###########

import os
import sys
import logging

import datetime

import pcraster as pcr

try:
    from .spatialDataSet2PCR import spatialAttributes, spatialDataSet, \
                                    compareSpatialAttributes, setClone
    from .netCDF_recipes import netCDF_file_info
except:
    from spatialDataSet2PCR import spatialAttributes, spatialDataSet, \
                                    compareSpatialAttributes, setClone
    from netCDF_recipes import netCDF_file_info

logger = logging.getLogger(__name__)

########
# TODO #
########
critical_improvements= str.join('\n\t',\
             ( \
              '', \
              ))

development= str.join('\n\t',\
             ( \
              '', \
              'include option to read timeseries and tables not in netCDF format', \
              '', \
              ))

print ('\nDevelopmens for meteo class:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print ('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

####################
# Global variables #
####################
# parameters - set as global variables
# these include a default small number for precision,
# a standard missing value indentifier and
# a file cache to reduce the opening and closing files.
missing_value = -999.9
very_small_number =  1.0e-12

# types
NoneType = type(None)

# and the default extensions to use:
file_extensions = { \
        '.map':   'pcraster', \
        '.nc':    'netcdf', \
        '.nc4':   'netcdf',\
        '.tif':   'pcraster', \
        '':       '',\
        }

# general information for file conversions

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

# initialize the cache of netCDF files
nc_info = netCDF_file_info()

#############
# Functions #
#############

# The following are generic functions to process files

def compose_filename(filename, path, *args):
    '''
compose_filename: function that checks whether the filename is an absolute path, \
and if not merges it with the path provided, normalizes the path and tests if \
the file exists. Returns the resulting the filename.
'''

    # check if the file exists, if it is an existing file, then make it absolute
    if os.path.isfile(filename):
        filename = os.path.abspath(filename)
    else:
        filename = os.path.join(path, filename)

    # normalize the path
    filename = os.path.normpath(filename)

    # substitute any additional arguments
    if args != ():
        
        if not isinstance(args, tuple):
            args = tuple(args)
        
        if '%' in filename:
            try:
                filename = filename % (args)
            except:
                logger.warning('additional arguments could not be converted into the file name %s' % filename)

    # return the file
    return filename, os.path.isfile(filename)

def file_is_nc(filename):
    '''
file_is_ncfile: tests if the file extension matches that of a netCDF file;
returns True if this is the case.
'''

    # test the filename
    file_ext = os.path.splitext(filename)[1]
    
    # return the test condition
    return file_extensions[file_ext] == 'netcdf'

def file_is_pcr(filename):
    '''
file_is_ncfile: tests if the file extension matches that of a netCDF file;
returns True if this is the case.
'''

    # test the filename
    file_ext = os.path.splitext(filename)[1]
    
    # return the test condition
    return file_extensions[file_ext] == 'pcraster'

def read_file_entry( \
                    filename,
                    variablename, \
                    inputpath               = '', \
                    file_subst_args         = (),\
                    clone_attributes        = None, \
                    forced_non_spatial      = False, \
                    datatype                = pcr.Scalar, \
                    date                    = None, \
                    date_selection_method   = 'exact', \
                    allow_year_substitution = False, \
                    ):
    
    '''

read_file_entry: generic function that can read information from file for a \
given date. This may concern spatial information or single entries.

    Input:
    ======
    required input:
    ---------------
    filename:               file name or root of the file to be extracted,
                            this can refer to PCRaster, netCDF files or a
                            value as a string;
    variablename:           name of the variable to be extracted, read from
                            the specified file;
    
    optional input:         defaults are None unless specified otherwise;
    ---------------
    inputpath:              input path that is attached to the file name if the
                            latter is a relative path (default: '');
    file_subst_args:        file substitution arguments that are used to repl-
                            enish the file name if needed (default: ());
    clone_attributes:       clone attributes that define the area of interest;
    forced_non_spatial:     boolean forcing multidimensional data to be read
                            as non-spatial, applies to netCDF files only or in 
                            case of the conversion of numerical values
                            (default: False);
    datatype:               PCRaster data type to be extracted
                            (default: pcr.Scalar);
    date:                   date to be extracted;
    date_selection_method:  option to select alternative dates if the actual
                            date is not met (default: 'exact');
    allow_year_substitution:
                            for temporal netCDF data, allows dates to be 
                            changed and match a particular year; this is part-
                            icularly useful to read climatologies or reuse
                            existing data over longer periods (e.g., spinup),
                            (default: False).

    Output:
    =======
    var_out:                output for the variable, either spatial or
                            non-spatial.

'''
    # initialize var_out as NoneType
    var_out = None

    # ensure the file name and value are strings
    filename = str(filename)
    val_str = str(filename)
    datatype_str = str(datatype)
    if 'VALUESCALE.' in datatype_str:
        datatype_str = datatype_str.replace('VALUESCALE.', '')
    
    # first compose the file name and test it exists
    filename, existing_file = compose_filename(filename, inputpath, file_subst_args)
    
    # check if the file is a netCDF file
    if existing_file and file_is_nc(filename):
        
        # netCDF: read as such from the cache
        var_out =  nc_info.read_nc_field( \
                    filename, \
                    variablename, \
                    clone_attributes        = clone_attributes, \
                    forced_non_spatial      = forced_non_spatial, \
                    datatype                = datatype, \
                    date                    = date, \
                    date_selection_method   = date_selection_method, \
                    allow_year_substitution = allow_year_substitution, \
                    )

    elif existing_file and file_is_pcr(filename):
   
        # PCRaster file

        # check and process the spatial data set
        if isinstance(clone_attributes, NoneType):
            
            # PCRaster maps can only be processed if the clone attributes are 
            # passed on to the functions
            message_str = 'no clone attributes are provided to process the PCRaster map'
            logger.error(message_str)
            sys.exit(message_str)
            
        # compare extent
        data_attributes = spatialAttributes(filename)
        fits_extent, same_resolution,  x_resample_ratio, y_resample_ratio = \
                    compareSpatialAttributes(data_attributes, \
                                             clone_attributes)

        file_ext = os.path.splitext(filename)[1]
        same_clone = fits_extent and same_resolution and file_ext == '.map'

        # resample method
        resample_method = resample_methods[datatype_str]
        
        
        print(f'{filename} (fits extent: {fits_extent})')
        
        
        # read in the data
        if same_clone:
            
            # get the map directly
            var_out = pcr.readmap(filename)
            conversion_method = getattr(pcr, datatype_str.lower())
            var_out = conversion_method(var_out)
            
        else:
            
            # get the variable using gdal_translate
            var_out = getattr(spatialDataSet( \
                              variablename, \
                              filename, \
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
                              ), variablename)
            
        # output avalaible, compose and log the message str
        message_str = 'value of %s read from %s' % (variablename, filename)
        message_str = str.join(' ', \
                               (message_str, 'in PCRaster format which does not contain variable info'))
        if not isinstance(date, NoneType):
            message_str = str.join(' ', \
                                   (message_str, 'and is unaware of the actual date %s' % date))
        
        logger.debug(message_str)

    else:

        # file type cannot be read
        try:
            var_out = float(val_str)
            if forced_non_spatial:
                conversion_method = conversion_methods[datatype_str.title()]
            else:
                conversion_method = getattr(pcr, datatype_str.lower())
            var_out = conversion_method(var_out)
            logger.debug('%s is recognized as a value instead of a netCDF or PCRaster file and is converted into %s' % \
                (val_str, str(conversion_method)))
        except:
            pass
            logger.error('%s is not recognized as a netCDF or PCRaster file and cannot be converted' % \
                         filename)

    # return the output
    return var_out


def close_nc_cache():
    
    '''closes the cache of netCDF input files'''
    
    nc_info.close_cache()

    # return None
    return None

###############################################################################
# end of functions                                                            #
###############################################################################

def main():
    pass

if __name__ == "__main__":
    main()
