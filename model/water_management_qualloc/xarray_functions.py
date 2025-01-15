#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 15:30:42 2023

@author: beek0120
"""

import sys
import numpy as np
import netCDF4 as nc
import xarray as xr

default_fillvalue       = -999.9
NoneType                = type(None)

def get_fillvalue(nc_filename, variablename):

    rootgrp   =  nc.Dataset(nc_filename)
    fillvalue = rootgrp.variables[variablename]._FillValue

    return fillvalue


def open_xr_dataset(nc_filename, to_cache = True):

    xr_dataset = xr.open_dataset(nc_filename, cache = to_cache)

    return xr_dataset

def close_xr_dataset(xr_dataset):

    xr_dataset.close()

    return None


def get_mask(var_array, fillvalue):

    '''creates a 2D mask to mask out the results of an operation'''

    # TODO: remove any NaN / masked values from the input

    array_shape = var_array.shape

    if len(array_shape) > 3 or len(array_shape) < 2:

        sys.exit('only 2D or 3D arrays allowed')

    mask = np.zeros(array_shape, dtype = bool)

    mask = np.abs(var_array - fillvalue) <= 1.0e-4

    return mask


def select_coordinates(xr_dataset, dimensions, dimension, indices):

    # check on the coordinates
    if dimension in dimensions and not isinstance(indices, NoneType):

        # process: set the indices to a tuple that has to have a length
        # of maximum two entries (start and end)
        if not '__iter__'  in dir(indices):

            indices = [indices, indices]

        indices = tuple(indices)

        # assert len(indices) <= 2, str.join(' ', \
        #                ('only a single entry or a tuple', \
        #                 'with a start and end entry can be processed'))

        # next get the indices
        ix0 = indices[0]
        ix1 = indices[-1]

        assert type(ix0) == type(ix1), \
                'only dimension information of the same type can be passed'

        if isinstance(ix0, int):

            # get the values
            values = getattr(xr_dataset, dimension).values

            for ix in range(indices):

                ix

            indices = (values[ix0], values[ix1])

    else:

        indices = None

    return indices


def get_xr_variable_array(xr_dataset, \
                         var_name, \
                         fillvalue       = default_fillvalue, \
                         **dimension_info):


    '''

get_xr_variable_array: function that returns the selected variable from \
an open xarray dataset with missing values set to the values defined and with \
the option to select part of the variable array on the basis of the dimensions \
and to compute the statistic

    Input:
    ======

    Output:
    =======


'''

    # TODO: include a more comprehensive way of computing statistics

    # read in the data
    xr_var_array = getattr(xr_dataset, var_name)

    # set a default output: use the array as is
    var_array = xr_var_array

    # get the dimensions and specify the conditions
    dimensions = list(xr_dataset.dims)

    statistic  = dict((dimension, None)  for dimension in dimensions)
    sel_coords = dict((dimension, None)  for dimension in dimensions)
    use_index  = dict((dimension, False) for dimension in dimensions)
    use_slice  = dict((dimension, None)  for dimension in dimensions)

    # iterate over the dimension and check
    for dimension in dimensions:

        # check whether the dimension is provided in the
        if dimension in dimension_info.keys():

            # get the value
            dim_input = dimension_info[dimension]

            # and set the values
            if not isinstance(dim_input, dict):

                # use the value as selected coordinates
                sel_coords[dimension] = dim_input

            else:

               # process the dictionary
               if 'values' in dim_input.keys():
                   sel_coords[dimension] = dim_input['values']

               if 'slice' in dim_input.keys():

                   use_slice[dimension] = dim_input['slice']

               if 'statistic' in dim_input.keys():

                   statistic[dimension] = dim_input['statistic']

            # set the slice if not set
            if isinstance(use_slice[dimension], NoneType):

                # of maximum two entries (start and end)
                if not '__iter__'  in dir(sel_coords[dimension]) or \
                        len(sel_coords[dimension]) == 1:

                    use_slice[dimension] = False

                elif len(sel_coords[dimension]) == 2:

                    print(str.join(' ', \
                               ('WARNING:', \
                                 'two coordinate values are set',
                                 'but the option to interpret this as single', \
                                 'values or a slice is not explicitly set;', \
                                  'hence the values are interpreted as a slice')))

                    use_slice[dimension] = True

                else:

                    use_slice[dimension] = False

            # decide on the use of the index or not
            if not isinstance(sel_coords[dimension], NoneType):

                if not '__iter__'  in dir(sel_coords[dimension]):

                    tix0 = type(sel_coords[dimension])

                else:

                    tix0 = type(sel_coords[dimension][0])
                    tix1 = type(sel_coords[dimension][-1])

                    assert tix0 == tix1, \
                        'only dimension information of the same type can be passed'

                use_index[dimension] = tix0 == int

    # all dimension information set, process accordingly
    for dimension in dimensions:

        if not isinstance(sel_coords[dimension], NoneType):

            if use_index[dimension] and not use_slice[dimension]:

                var_array = var_array.isel(**{dimension: \
                            sel_coords[dimension]})

            elif use_index[dimension] and use_slice[dimension]:

                var_array = var_array.isel(**{dimension: \
                            slice(sel_coords[dimension][0], \
                                  sel_coords[dimension][-1])})

            elif not use_index[dimension] and not use_slice[dimension]:

                var_array = var_array.sel(**{dimension: \
                            sel_coords[dimension]})

            elif not use_index[dimension] and use_slice[dimension]:

                var_array = var_array.sel(**{dimension: \
                            slice(sel_coords[dimension][0], \
                                  sel_coords[dimension][-1])})

            else:

                sys.exit(str.join(' ', ('options cannot be processed to read', \
                                        'from the xarray data set')))


    # this returned the requested variable in xarray as a slice or in full
    # set the mask: this identifies cells that contain missing values
    # and removes any missing values
    mask = get_mask(var_array, fillvalue)

    # statistics are currently only allowed when the dimension is the first
    # out of a 3D array; other options are not allowed.

    dimension = dimensions[0]

    assert isinstance(statistic[dimension], NoneType) or \
           (not isinstance(statistic[dimension], NoneType) and \
            mask.ndim == 3), \
       str.join(' ', ( \
                'statistics of the first dimension %s' % dimension, \
                 'can only be computed on arrays with three dimensions'))

    if not isinstance(statistic[dimension], NoneType) and mask.ndim == 3:

        # apply the statistic on the first variable

        # get the string of the function
        if not isinstance(statistic[dimension], str):

            statistic[dimension] = getattr(statistic[dimension], '__name__')

        if   statistic[dimension] == 'max' or statistic[dimension] == 'amax':

            var_array = var_array.max(dimension)

        elif statistic[dimension] == 'min' or statistic[dimension] == 'amin':

            var_array = var_array.min(dimension)

        elif statistic[dimension] == 'mean':

            var_array = var_array.mean(dimension)

        elif statistic[dimension] == 'sum':

            var_array = var_array.sum(dimension)

        else:

            sys.exit('statistic %s over the dimension time cannot be computed' % \
                      statistic[dimension])

        if mask.ndim == 3:

            mask = np.any(mask, axis = 0)

    # reset the values to the missing value if the mask is true
    var_array.values[mask] = fillvalue

    # return selected xr array
    return var_array
