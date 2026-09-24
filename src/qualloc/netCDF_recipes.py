import datetime
import logging
import sys
from copy import deepcopy
from types import BuiltinMethodType

import netCDF4 as nc
import numpy as np
import pcraster as pcr

from qualloc.spatialDataSet2PCR import (
    compareSpatialAttributes,
    spatialAttributes,
    spatialDataSet,
)

logger = logging.getLogger(__name__)

# all netCDF information is stored in a class object with dictionaries keyed by file name:
# a cache of all open netCDF file objects, and stores of all non-dimensional variables with
# their dimensions and with their time steps

critical_improvements = str.join("\n", ("",))

development = str.join(
    "\n\t",
    (
        "",
        "make netCDFs accessible via a root and for multiple years",
        "make sure scaled netCDFs are read correctly",
        "",
    ),
)

print("\nDevelopmens for netCDF recipes class:")

if len(critical_improvements) > 0:
    print("Critical improvements: \n%s" % critical_improvements)

if len(development) > 0:
    print("Ongoing: \n%s" % development)

if len(critical_improvements) > 0:
    sys.exit()

NoneType = type(None)
DictType = type(dict)

# file conversion settings
date_selection_methods = ["nearest", "before", "after", "exact"]

conversion_methods = {
    "Scalar": float,
    "Nominal": int,
    "Boolean": bool,
    "Ordinal": int,
    "Directional": float,
    "Ldd": int,
}

datatypes = {
    "Scalar": "FLOAT32",
    "Nominal": "INT32",
    "Boolean": "BYTE",
    "Ordinal": "FLOAT32",
    "Directional": "FLOAT32",
    "Ldd": "BYTE",
}


resample_methods = {
    "Scalar": "bilinear",
    "Nominal": "nearest",
    "Boolean": "nearest",
    "Ordinal": "nearest",
    "Directional": "bicubic",
    "Ldd": "nearest",
}


nc_mv_id_str = "_FillValue"
# default netCDF format and variable attributes for createVariable; testVerbose flags output
default_nc_format = "NETCDF3_CLASSIC"
default_zlib = False
default_complevel = 4
default_shuffle = True
default_fletcher32 = False
default_contiguous = False
default_chunksizes = None
default_endian = "native"
default_least_significant_digit = None
default_fill_value = -999.9
exclude_list = ["group", "set", "_", "__"]
test_verbose = False


def update_year_of_date(date, new_year, dates):
    """
update_year_of_date: function that finds the offset in days between the date \
specified and the same day in the new year specified and applies it subsequently \
to dates, which can be an iterable or a single date. Returns a copy of dates \
with the years changed accordingly.

"""
    seq_type = True
    if isinstance(dates, list):
        new_dates = dates[:]

    elif isinstance(dates, np.ndarray):
        new_dates = deepcopy(dates)
        new_dates = new_dates.ravel()

    else:
        new_dates = [dates]
        seq_type = False

    # check the data type
    if not isinstance(new_dates[0], datetime.datetime):
        "dates have not the correct datetime datetime format"

    date_offset = datetime.datetime(new_year, date.month, date.day) - datetime.datetime(
        date.year, date.month, date.day
    )

    for ix in range(len(new_dates)):

        new_dates[ix] = new_dates[ix] + date_offset

    # single entry or sequence
    if not seq_type:
        new_dates = new_dates[0]

    return new_dates


def substitute_years_of_dates(dates, date):
    """Returns a copy of a list of dates in which the years have been updated
    to include the year of the specified date"""

    # nearest date and available years
    date_index = get_date_index(date, dates, "nearest")
    nearest_date = dates[date_index]

    return update_year_of_date(nearest_date, date.year, dates)


def get_date_index(date, dates, date_selection_method, substituted_dates=False):
    """
    get_date_index: function that returns the position of the date specified in an array of dates,
    following the index date_selection_methodion method specified: exact, before, after, nearest.
    This function reproduces the date2index function of the netCDF4 package but
    circumvents the problem that the original function cannot read from a standard dictionary.

    """

    # array with time deltas and indices
    time_delta = dates.copy()

    if not isinstance(dates[0], type(date)):
        for ix in range(len(time_delta)):
            time_delta[ix] = datetime.datetime(
                time_delta[ix].year,
                time_delta[ix].month,
                time_delta[ix].day,
                time_delta[ix].hour,
                time_delta[ix].minute,
                time_delta[ix].second,
                time_delta[ix].microsecond,
            )
    time_delta = time_delta - date
    date_index = np.arange(time_delta.size)

    # masked array operation for Python 3.x and higher
    if isinstance(time_delta, np.ma.core.MaskedArray):
        time_delta = np.array(time_delta.tolist())

    # find the zero value
    if (
        np.size(dates[time_delta == datetime.timedelta(0)]) > 0
        and not substituted_dates
    ):
        return np.arange(dates.size)[time_delta == datetime.timedelta(0)][0]

    elif date_selection_method == "exact":
        return None

    elif date_selection_method == "before":
        mask = time_delta < datetime.timedelta(0)

        if time_delta[mask].size > 0:
            mask_value = time_delta[mask].max()
            return date_index[time_delta == mask_value][0]
        else:
            return None

    elif date_selection_method == "after":
        mask = time_delta > datetime.timedelta(0)
        if time_delta[mask].size > 0:
            mask_value = time_delta[mask].min()
            return date_index[time_delta == mask_value][0]
        else:
            return None

    elif date_selection_method == "nearest":
        time_delta = np.abs(time_delta)
        return np.arange(dates.size)[time_delta == time_delta.min()][0]

    else:
        sys.exit(
            "index date_selection_method %s is not allowed or does not yield a result"
            % date_selection_method
        )


def match_date_in_dates(date, dates, date_selection_method="exact"):
    """

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

"""

    date_index = get_date_index(date, dates, date_selection_method)

    message_str = str.join(
        " ", ("for the water management module", "a %s match is found for date %s")
    )
    message_str = message_str % (date_selection_method, date)

    # no match found: substitute the date
    if isinstance(date_index, NoneType):

        # replacement year, depending on the selection method
        if date_selection_method == "exact":
            replacement_year = date.year
        elif date_selection_method == "before":
            replacement_year = date.year - 1
        elif date_selection_method == "after":
            replacement_year = date.year + 1
        else:
            pass

        message_str = str.join(
            " ",
            (
                "for the water management module"
                "date substitution is allowed to find the %s match",
                "for year %d for which the dummy year %d is used",
            ),
        )
        message_str = message_str % (date_selection_method, date.year, replacement_year)

        # use the nearest date if the selection method is exact
        if date_selection_method == "exact":
            date_selection_method = "nearest"

        replacement_date = update_year_of_date(date, replacement_year, date)

        # replace the year of the dates
        dates = substitute_years_of_dates(dates, replacement_date)

        date_index = get_date_index(
            date, dates, date_selection_method, substituted_dates=True
        )

    # matched date and band
    matched_date = dates[date_index]

    message_str = str.join(
        "; ", (message_str, "the date %s is matched to %s" % (date, matched_date))
    )

    return date_index, matched_date, message_str


def print_dictionary(dobj, level=0):
    """iterates over all items in a dictionary and print key,value pairs"""
    for key, value in dobj.items():
        if isinstance(value, list) or isinstance(value, np.ndarray):
            vals = value[:]
            value = [vals[0], "...", vals[-1]]
        print(
            " " * level * 4,
            key,
        )
        try:
            print(value)
        except:
            print


def get_nc_object_attributes(obj, exclude_list=[], exclude_class_objects=True):
    """Reads all information from the netCDF dataset object specified and returns a dictionary
    of key, value pairs; should only be applied on copies of netCDF dataset objects
    to avoid unwanted changes in the dataset"""
    # dictionary of the allowed entries
    dobj = {}
    for item in dir(obj):
        include_entry = True
        for check_item in exclude_list:
            len_str = min(len(check_item), len(item))

            if item[:len_str] == check_item:
                include_entry = include_entry and False

        if include_entry:
            if isinstance(getattr(obj, item), BuiltinMethodType):
                if not exclude_class_objects:
                    try:
                        dobj[item] = getattr(obj, item)()
                    except:
                        pass
            else:
                dobj[item] = getattr(obj, item)
    return dobj


def get_nc_attributes(ncfilename):
    """
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
    information on variables"""

    # TODO: include groups; note: information is partly copied, as netCDF variables and dimensions
    # cannot be accessed once the file is closed

    rootgrp = nc.Dataset(
        ncfilename,
        "r",
    )

    # file format, dimensions, attributes, variables and missing value
    nc_format = rootgrp.file_format
    nc_dimensions = rootgrp.dimensions.copy()
    nc_variables = rootgrp.variables.copy()

    # exclude high-level entries; class objects are ignored by default
    exclude_list = ["_"]

    nc_attributes = {}

    for key, value in rootgrp.__dict__.items():
        nc_attributes[key] = value

    # attributes and values of the dimensions, as dictionaries for reuse
    nc_dimattrs = {}
    for key in nc_dimensions.keys():
        nc_dimattrs[key] = get_nc_object_attributes(
            nc_dimensions[key], exclude_list=exclude_list
        )
        if key in nc_variables.keys():
            nc_dimattrs[key]["values"] = nc_variables[key][:]
            nc_dimattrs[key]["size"] = nc_variables[key].size

    # attributes of each variable, for reuse
    nc_varattrs = {}
    for key in nc_variables.keys():
        nc_varattrs[key] = get_nc_object_attributes(
            nc_variables[key], exclude_list=exclude_list
        )

    rootgrp.close()

    return nc_format, nc_attributes, nc_dimattrs, nc_varattrs


def initialize_ncfile(
    ncfilename,
    nc_format=None,
    nc_global_attributes={},
    cache={},
):
    """
        
initialize_netCD: initializes the netCDF file with the name and format specified\
     and set its attributes for output.

"""

    if isinstance(nc_format, NoneType):
        nc_format = default_nc_format

    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, "w", format=nc_format)

    for attribute, value in nc_global_attributes.items():
        rootgrp.setncattr(attribute, value)

    # close the file if it is not in the cache
    if not ncfilename in cache:
        rootgrp.close()

    return None


def add_variable_to_netCDF(
    ncfilename,
    name,
    datatype,
    dimensions,
    cache={},
    **nc_optional_info,
):
    """
                
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
   
    """

    # process the optional keywords and set the defaults
    nc_defaults = {}
    nc_defaults["varname"] = name
    nc_defaults["datatype"] = datatype
    nc_defaults["dimensions"] = dimensions
    nc_defaults["zlib"] = default_zlib
    nc_defaults["complevel"] = default_complevel
    nc_defaults["shuffle"] = default_shuffle
    nc_defaults["fletcher32"] = default_fletcher32
    nc_defaults["contiguous"] = default_contiguous
    nc_defaults["chunksizes"] = default_chunksizes
    nc_defaults["endian"] = default_endian
    nc_defaults["fill_value"] = default_fill_value
    nc_defaults["least_significant_digit"] = default_least_significant_digit

    # optional nc_var_attrs
    if "nc_var_atttrs" in nc_optional_info.keys() and isinstance(
        nc_optional_info["nc_var_attrs"], DictType
    ):
        nc_var_attrs = nc_optional_info["nc_var_attrs"].copy()
    else:
        nc_var_attrs = {}

    # pass keywords to the defaults
    for key, value in nc_optional_info.items():

        if key != "nc_var_attrs":

            if not key in nc_var_attrs.keys():

                nc_var_attrs[key] = value

    # update the defaults
    nc_var_keys = list(nc_var_attrs.keys())
    for key in nc_var_keys:

        if key in nc_defaults.keys():

            nc_var_attrs[key] = nc_var_attrs[key]

            # strip the keyword from the attributes
            del nc_var_attrs[key]

    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, "a")

    # create the variable, first with the defaults, then with the remaining keys of nc_var_attrs
    nc_variable = rootgrp.createVariable(**nc_defaults)

    if "ncattrs" in nc_var_attrs.keys():

        for key, value in nc_var_attrs["nc_attrs"].items():

            nc_variable.setncattr(key, value)

    else:

        # remaining attributes
        for key, value in nc_var_attrs.items():

            nc_variable.setncattr(key, value)

    rootgrp.sync()

    # close the file if it is not in the cache
    if not ncfilename in cache:
        rootgrp.close()

    return None


def add_dimension_to_netCDF(
    ncfilename,
    name,
    datatype,
    unlimited=False,
    values=[],
    cache={},
    **nc_optional_info,
):
    """

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
   
    """

    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, "a")

    if unlimited:
        size = None
    else:
        size = len(values)

    rootgrp.createDimension(name, size)

    rootgrp.sync()

    # close the file if it is not in the cache
    if not ncfilename in cache:
        rootgrp.close()

    add_variable_to_netCDF(
        ncfilename=ncfilename,
        name=name,
        datatype=datatype,
        dimensions=(name,),
        cache=cache,
        **nc_optional_info,
    )

    if not isinstance(size, NoneType):

        if ncfilename in cache:
            rootgrp = cache[ncfilename]
        else:
            rootgrp = nc.Dataset(ncfilename, "a")

        rootgrp.variables[name][:] = values[:]

        rootgrp.sync()

        # close the file if it is not in the cache
        if not ncfilename in cache:
            rootgrp.close()

    return None


def add_data_to_netCDF(
    ncfilename, name, variable_array, dim_slices, cache={}, **additional_info
):
    """

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

    """

    if ncfilename in cache:
        rootgrp = cache[ncfilename]
    else:
        rootgrp = nc.Dataset(ncfilename, "a")

    # copy the dimension slices and the variable array
    dim_slices = deepcopy(dim_slices)
    variable_array = deepcopy(variable_array)

    simple_update = True

    dim_keys = list(rootgrp.variables[name].dimensions)

    time_dimension = ""
    if "time_dimension" in additional_info.keys() and "dates" in additional_info.keys():

        time_dimension = additional_info["time_dimension"]
        dates = additional_info["dates"]

        # temporal information: add the dates
        nc_time = rootgrp.variables[time_dimension]
        if len(nc_time[:]) > 0:
            try:
                date_ixs = np.array(nc.date2index(dates, nc_time)).ravel()
            except:
                date_ixs = np.arange(len(dates)) + len(nc_time[:])
        else:
            date_ixs = np.arange(len(dates)) + len(nc_time[:])

        date_ixs = date_ixs.tolist()
        for date_ix in date_ixs:

            date = dates[date_ixs.index(date_ix)]
            nc_time[date_ix] = nc.date2num(date, nc_time.units, nc_time.calendar)

        # insert the date indices if the dimension values are not set
        if isinstance(dim_slices[time_dimension], NoneType):

            simple_update = True

            # first and last position
            dim_slices[time_dimension] = (date_ixs[0], date_ixs[-1] + 1)

        else:
            simple_update = False

    # set dimension slices that are None, and get the required size of the (sliced) variable array;
    # processing is simplified for the maximum non-temporal dimensions
    req_size = 1

    for dim_key in dim_keys:

        if isinstance(dim_slices[dim_key], NoneType):

            dim_slices[dim_key] = (0, len(rootgrp.variables[dim_key][:]))

        if dim_key != time_dimension:
            simple_update = simple_update and (
                (dim_slices[dim_key][1] - dim_slices[dim_key][0])
                == len(rootgrp.variables[dim_key][:])
            )

        req_size = req_size * (dim_slices[dim_key][1] - dim_slices[dim_key][0])

    while variable_array.size != req_size:
        sys.exit("array sizes do not match!")

    # a simple update is possible if the variable array has the size of a single time step

    if simple_update:

        if time_dimension != "":
            # timed: write to the last field
            rootgrp.variables[name][dim_slices[time_dimension][0], ...] = (
                variable_array[:]
            )
        else:
            # not timed: write the full array
            rootgrp.variables[name][...] = variable_array[:]

    else:

        # otherwise, use a boolean mask and index array to set the corresponding entries

        mask_array = np.ones(rootgrp.variables[name][:].shape, dtype=bool)
        g_ixs = np.indices(mask_array.shape)
        for dim_key in dim_keys:

            dim_ix = dim_keys.index(dim_key)

            mask_ix = (g_ixs[dim_ix] >= dim_slices[dim_key][0]) & (
                g_ixs[dim_ix] < dim_slices[dim_key][1]
            )

            mask_array = mask_array & mask_ix

        v_a = rootgrp.variables[name][:].copy()

        v_a[mask_array] = variable_array[:].ravel()

        rootgrp.variables[name][:] = v_a.copy()

    rootgrp.sync()

    v_a = None
    mask_array = None
    mask_ix = None
    del v_a, mask_array, mask_ix

    # close the file if it is not in the cache
    if not ncfilename in cache:
        rootgrp.close()

    return None


def get_nc_dates(ncfilename):
    """
    get_nc_dates: returns a list of sorted dates from a timet netCDF file.

    """
    nc_dates = []

    nc_format, nc_attributes, nc_dimattrs, nc_varattrs = get_nc_attributes(ncfilename)

    time_dimension = None
    for variablename in nc_dimattrs.keys():
        if "calendar" in nc_varattrs[variablename]:
            time_dimension = variablename

    # get the dates of timed data and store them for later access
    if not isinstance(time_dimension, NoneType):
        nc_dates = nc.num2date(
            nc_dimattrs[time_dimension]["values"],
            nc_varattrs[time_dimension]["units"],
            nc_varattrs[time_dimension]["calendar"],
        )

        nc_dates.sort()
        nc_dates = nc_dates.tolist()

    return nc_dates


class netCDF_file_info(object):

    def __init__(
        self,
    ):

        object.__init__(self)

        # cache of open files and information
        self.cache = dict()
        self.attributes = dict()
        self.dimensions = dict()
        self.variables = dict()
        self.spatialattributes = dict()
        self.time_dimension = dict()

    def test_ncfile_in_cache(self, ncfilename):
        """tests if the specified nc file name is present in the cache"""

        return ncfilename in self.cache.keys()

    def add_ncfile_to_cache(
        self, ncfilename, clone_attributes=None, forced_non_spatial=False
    ):
        """adds the information from the specified netCDF file to this instance \
holding netCDF information to facilitate access."""

        # add the netCDF file to the cache if not present yet
        if not ncfilename in self.cache.keys():

            nc_format, nc_attributes, nc_dimattrs, nc_varattrs = get_nc_attributes(
                ncfilename
            )

            self.attributes[ncfilename] = nc_attributes.copy()
            self.dimensions[ncfilename] = nc_dimattrs.copy()
            self.variables[ncfilename] = nc_varattrs.copy()

            # global fill value, if possible
            if nc_mv_id_str in self.attributes[ncfilename].keys():
                global_mv = self.attributes[ncfilename][nc_mv_id_str]
            else:
                global_mv = default_fill_value

            self.cache[ncfilename] = nc.Dataset(ncfilename)

            time_dimension = None
            for variablename in self.dimensions[ncfilename].keys():
                if "calendar" in self.variables[ncfilename][variablename]:
                    time_dimension = variablename

            # get the dates of timed data and store them for later access
            if not isinstance(time_dimension, NoneType):
                self.time_dimension[ncfilename] = time_dimension
                dates = nc.num2date(
                    self.dimensions[ncfilename][time_dimension]["values"],
                    self.variables[ncfilename][time_dimension]["units"],
                    self.variables[ncfilename][time_dimension]["calendar"],
                )
                self.dimensions[ncfilename][time_dimension]["values"] = dates[:]

            # check the dimensions, determine whether the data set is spatial and temporal, and add the
            # missing value information of the variable if not included yet
            for variablename in self.variables[ncfilename].keys():

                # default missing value identifier
                mv = None

                nc_dims = self.obtain_dimensions(ncfilename, variablename)

                # process non-dimensional variables (at least one dimension, not equal to the variable name)
                process_non_dimensional_variable = False
                if len(nc_dims) > 0:
                    process_non_dimensional_variable = nc_dims[0] != variablename

                if process_non_dimensional_variable:

                    # nature of the data: timed and spatial
                    self.variables[ncfilename][variablename]["timed_variable"] = False
                    self.variables[ncfilename][variablename]["spatial_variable"] = False

                    # spatial data, unless forced as non-spatial
                    if not forced_non_spatial:

                        data_attributes = None
                        try:

                            data_attributes = spatialAttributes(
                                'NETCDF:"%s":%s' % (ncfilename, variablename)
                            )
                        except:

                            logger.debug(
                                "%s in %s is treated as a non-spatial dataset"
                                % (variablename, ncfilename)
                            )

                        if not isinstance(data_attributes, NoneType):

                            (
                                fits_extent,
                                same_resolution,
                                x_resample_ratio,
                                y_resample_ratio,
                            ) = compareSpatialAttributes(
                                data_attributes, clone_attributes
                            )
                            same_clone = fits_extent and same_resolution

                            mv = getattr(data_attributes, "noDataValue")

                            # spatial variable: set the spatial attributes of the nc_info instance
                            self.variables[ncfilename][variablename][
                                "spatial_variable"
                            ] = True

                            if not ncfilename in self.spatialattributes.keys():
                                self.spatialattributes[ncfilename] = {}

                            if (
                                not variablename
                                in self.spatialattributes[ncfilename].keys()
                            ):

                                self.spatialattributes[ncfilename][
                                    variablename
                                ] = same_clone

                            else:

                                self.spatialattributes[ncfilename][variablename] = (
                                    self.spatialattributes[ncfilename][variablename]
                                    | same_clone
                                )

                            # appears to be non-spatial
                            logger.debug(
                                "%s in %s is treated as a spatial dataset"
                                % (variablename, ncfilename)
                            )

                    else:
                        # definitely non-spatial
                        logger.debug(
                            "%s in %s is defined as a non-spatial dataset"
                            % (variablename, ncfilename)
                        )

                    # the variable is timed if the first dimension is time
                    if not isinstance(time_dimension, NoneType):

                        self.variables[ncfilename][variablename]["timed_variable"] = (
                            nc_dims[0] == time_dimension
                        )

                        logger.debug(
                            "%s in %s is defined as a temporal dataset"
                            % (variablename, ncfilename)
                        )

                    else:
                        logger.debug(
                            "%s in %s is defined as a non-temporal dataset"
                            % (variablename, ncfilename)
                        )

                    # add the missing value information (attribute nc_mv_id_str, '_FillValue') of all
                    # non-dimensional variables, if necessary
                    if (
                        not nc_mv_id_str
                        in self.variables[ncfilename][variablename].keys()
                    ):

                        if isinstance(mv, NoneType):
                            mv = global_mv

                        self.variables[ncfilename][variablename][nc_mv_id_str] = mv

            logger.info("neCDF file %s added to cache" % ncfilename)

    def remove_ncfile_from_cache(self, ncfilename):
        """closes the netCDF file and remove all information from the \
specified netCDF file."""

        # remove the netCDF file from the cache if present
        if ncfilename in self.cache.keys():

            self.cache[ncfilename].close()
            del self.cache[ncfilename]

            del self.attributes[ncfilename]
            del self.dimensions[ncfilename]
            del self.variables[ncfilename]

            logger.info("neCDF file %s removed from cache" % ncfilename)

    def obtain_dimensions(self, ncfilename, variablename):
        """gets the dimensions as a tuple from a netCDF file if the variable is matched"""

        nc_dims = ()

        # dimensions of the variable if present, otherwise remove the file from the cache
        if variablename in self.variables[ncfilename].keys():
            nc_dims = self.variables[ncfilename][variablename]["dimensions"]

        else:
            # the file does not contain the correct information
            self.remove_ncfile_from_cache(ncfilename)

        return nc_dims

    def test_var_in_ncfile(self, ncfilename, variablename):
        """
test_var_in_ncfile: function that tests if a variable is present in the \
netCDF file specified.
     
"""
        return variablename in self.variables[ncfilename]

    def read_nc_field(
        self,
        ncfilename,
        variablename,
        clone_attributes=None,
        datatype=pcr.Scalar,
        date=None,
        date_selection_method="exact",
        allow_year_substitution="False",
        forced_non_spatial=False,
    ):
        """
        
read_nc_field: function that retrieves an entry of the variable name within \
the specified netCDF file name with consideration of the spatial attributes of \
the present clone. It can automatically retrieve the corresponding date, \
depending on the type of match specified.

"""
        date_selection_method = date_selection_method.lower()

        if not date_selection_method in date_selection_methods:
            logger.error(
                "date selection method %s is not available" % date_selection_method
            )

        # add the netCDF file to the cache if not included yet
        if not self.test_ncfile_in_cache(ncfilename):

            self.add_ncfile_to_cache(ncfilename, clone_attributes, forced_non_spatial)

        # clone attributes must be defined for spatially explicit variables
        if (
            isinstance(clone_attributes, NoneType)
            and self.variables[ncfilename][variablename]["spatial_variable"]
            and not self.spatialattributes[ncfilename][variablename]
        ):

            logger.error(
                "No clone attributes are specified to extract spatial information for variable %s from %s"
                % (variablename, ncfilename)
            )

        # dimensions, to decide how the data are processed
        nc_dims = self.obtain_dimensions(ncfilename, variablename)

        # halt if the variable is not found
        if nc_dims == ():
            logger.error(
                "neCDF file %s does not contain information on the requested variable %s"
                % (ncfilename, variablename)
            )

        # timed variable: get the position and band
        if self.variables[ncfilename][variablename]["timed_variable"]:

            time_dimension = self.time_dimension[ncfilename]

            # date index, possibly from the substituted dates
            dates = self.dimensions[ncfilename][time_dimension]["values"].copy()

            message_str = ""

            # first check whether an exact match can be found
            if not allow_year_substitution:

                true_date = False

                if date in dates:

                    true_date = True
                    date_selection_method = "exact"

                else:

                    message_str = (
                        "for variable %s, date %s is not encountered in %s"
                        % (variablename, date, ncfilename)
                    )

                    if date_selection_method == "exact":

                        logger.error(message_str)
                        sys.exit(message_str)

                date_index = nc.date2index(
                    date,
                    self.cache[ncfilename].variables[time_dimension],
                    self.variables[ncfilename][time_dimension]["calendar"],
                    select=date_selection_method,
                )

                true_date = True

            # year substitution is allowed: find the corresponding match
            else:

                date_index = get_date_index(date, dates, date_selection_method)

                # no match found: substitute the date
                if isinstance(date_index, NoneType):

                    # replacement year, depending on the selection method
                    if date_selection_method == "exact":
                        replacement_year = date.year
                    elif date_selection_method == "before":
                        replacement_year = date.year - 1
                    elif date_selection_method == "after":
                        replacement_year = date.year + 1
                    else:
                        pass

                    message_str = str.join(
                        " ",
                        (
                            "for variable %s",
                            "date substitution is allowed to find the %s match",
                            "for year %d for which the dummy year %d is used",
                        ),
                    )
                    message_str = message_str % (
                        variablename,
                        date_selection_method,
                        date.year,
                        replacement_year,
                    )
                    logger.warning(message_str)

                    # use the nearest date if the selection method is exact
                    if date_selection_method == "exact":
                        date_selection_method = "nearest"

                    replacement_date = update_year_of_date(date, replacement_year, date)

                    # replace the year of the dates
                    dates = substitute_years_of_dates(dates, replacement_date)

                    date_index = get_date_index(
                        date, dates, date_selection_method, substituted_dates=True
                    )

                true_date = False

            # matched date and band
            matched_date = dates[date_index]
            band_number = date_index + 1

        else:

            date_index = None
            band_number = None

        # retrieve the data; four cases, for which the band and arrays are read:
        # non-spatial/non-temporal, spatial/non-temporal, non-spatial/temporal and spatial/temporal

        # conversion method (for non-spatial output) and resample method
        datatype_str = str(datatype)
        if "VALUESCALE." in datatype_str:
            datatype_str = datatype_str.replace("VALUESCALE.", "")
        conversion_method = conversion_methods[datatype_str]
        resample_method = resample_methods[datatype_str]

        # spatial data
        if self.variables[ncfilename][variablename]["spatial_variable"]:

            # spatial data are read directly if possible, otherwise with gdal_translate
            if not self.spatialattributes[ncfilename][variablename]:

                # no resampling is allowed for LDD data
                if datatype == pcr.Ldd or datatype == str(pcr.Ldd):

                    data_attributes = spatialAttributes(
                        'NETCDF:"%s":%s' % (ncfilename, variablename)
                    )

                    fits_extent, same_resolution, x_resample_ratio, y_resample_ratio = (
                        compareSpatialAttributes(data_attributes, clone_attributes)
                    )

                    # halt if the resolution differs
                    if not same_resolution:

                        logger.error(
                            "data of type LDD as read from %s for %s can not be resampled"
                            % (ncfilename, variablename)
                        )

                # different areas: get the actual area using gdal_translate
                var_out = getattr(
                    spatialDataSet(
                        variablename,
                        'NETCDF:"%s":%s' % (ncfilename, variablename),
                        datatypes[datatype_str],
                        datatype,
                        clone_attributes.xLL,
                        clone_attributes.xUR,
                        clone_attributes.yLL,
                        clone_attributes.yUR,
                        clone_attributes.xResolution,
                        clone_attributes.yResolution,
                        pixels=clone_attributes.numberCols,
                        lines=clone_attributes.numberRows,
                        resampleMethod=resample_method,
                        band=band_number,
                    ),
                    variablename,
                )

            else:
                # data can be converted directly using numpy2pcr
                if self.variables[ncfilename][variablename]["timed_variable"]:
                    var_array = self.cache[ncfilename][variablename][date_index, :]
                else:
                    # not timed
                    var_array = self.cache[ncfilename][variablename][:]

                var_out = pcr.numpy2pcr(
                    datatype,
                    var_array,
                    self.variables[ncfilename][variablename][nc_mv_id_str],
                )

                var_array = None
                del var_array

        # non-spatial data
        else:

            # temporal: return the value for the date
            if self.variables[ncfilename][variablename]["timed_variable"]:

                if self.variables[ncfilename][variablename]["ndim"] == 1:

                    # current date only
                    var_out = conversion_method(
                        self.cache[ncfilename][variablename][date_index]
                    )

                else:

                    var_out = self.cache[ncfilename][variablename][date_index, :]

            else:

                # all values
                var_out = self.variables[ncfilename][variablename][:]

        message_str = "value of %s read from %s" % (variablename, ncfilename)
        if self.variables[ncfilename][variablename]["timed_variable"]:
            message_str = str.join(" ", (message_str, "for %s" % date))
            if not true_date or matched_date != date:
                message_str = str.join(
                    " ",
                    (
                        message_str,
                        "which was matched by %s using a %s match"
                        % (matched_date, date_selection_method),
                    ),
                )

        logger.debug(message_str)

        return var_out

    def close_cache(self):

        for ncfilename in list(self.cache.keys()):

            self.remove_ncfile_from_cache(ncfilename)

        return None


class netCDF_output_handler(object):
    """
   
netCDF_output_handler: class that holds all information to create and update \
output netCDF files.
    
"""

    def __init__(self, model_configuration):

        object.__init__(self)

        # cache of open files, dimensions per variable and the timed variable
        self.cache = dict()
        self.dimensions = dict()
        self.time_dimension = dict()

        self.latitude = pcr.pcr2numpy(
            pcr.ycoordinate(pcr.spatial(pcr.boolean(1))), default_fill_value
        )[:, 0]
        self.longitude = pcr.pcr2numpy(
            pcr.xcoordinate(pcr.spatial(pcr.boolean(1))), default_fill_value
        )[0, :]

        # netCDF format and zlib setup
        self.default_fill_value = default_fill_value
        self.nc_format = default_nc_format
        self.zlib = default_zlib
        if "nc_format" in model_configuration.reporting.keys():
            self.format = model_configuration.convert_string_to_input(
                model_configuration.reporting["nc_format"], str
            )
        if "zlib" in model_configuration.reporting.keys():
            self.format = model_configuration.convert_string_to_input(
                model_configuration.reporting["zlib"], bool
            )

        # general netCDF attributes from the ini file
        self.nc_global_attributes = self.get_general_netcdf_attributes(
            model_configuration
        )

        self.dimension_info = {}

        # dimension info for time and the x and y coordinates
        self.dimension_info["time"] = {
            "dim_pos": 0,
            "is_temporal": True,
            "is_spatial": False,
            "datatype": "f4",
            "unlimited": True,
            "long_name": "Days since 1901-01-01",
            "standard_name": "Days since 1901-01-01",
            "calendar": "standard",
            "units": "Days since 1901-01-01",
        }
        self.dimension_info["latitude"] = {
            "dim_pos": 1,
            "is_temporal": False,
            "is_spatial": True,
            "datatype": "f4",
            "unlimited": False,
            "long_name": "latitude",
            "standard_name": "latitude",
            "units": "degrees_north",
        }
        self.dimension_info["longitude"] = {
            "dim_pos": 2,
            "is_temporal": False,
            "is_spatial": True,
            "datatype": "f4",
            "unlimited": False,
            "long_name": "longitude",
            "standard_name": "longitude",
            "units": "degrees_east",
        }

        return None

    def get_general_netcdf_attributes(self, model_configuration):

        nc_default_attributes = {
            "title": "QUAlloc run for %s" % model_configuration.general["scenarioname"],
            "history": "Created on %s" % model_configuration._timestamp_str,
            "institution": "Dept. Physical Geography, Utrecht University (r.vanbeek@uu.nl)",
        }
        nc_global_attributes = {}

        # add all attributes from the dictionary
        for key, attribute in model_configuration.netcdfattrs.items():

            nc_global_attributes[key] = attribute

        # add defaults if necessary
        for key, attribute in nc_default_attributes.items():

            if not key in nc_global_attributes.keys():
                nc_global_attributes[key] = attribute

        return nc_global_attributes

    def test_ncfile_in_cache(self, ncfilename):
        """tests if the specified nc file name is present in the cache"""

        return ncfilename in self.cache.keys()

    def add_ncfile_to_cache(
        self,
        ncfilename,
    ):
        """adds the information from the specified netCDF file to this instance \
holding netCDF information to facilitate access."""

        # add the netCDF file to the cache if not present yet
        if not self.test_ncfile_in_cache(ncfilename):

            self.cache[ncfilename] = nc.Dataset(ncfilename, "w", format=self.nc_format)

            logger.info("neCDF file %s added to cache" % ncfilename)

    def remove_ncfile_from_cache(self, ncfilename):
        """closes the netCDF file and remove all information from the \
specified netCDF file."""

        # remove the netCDF file from the cache if present
        if ncfilename in self.cache.keys():

            self.cache[ncfilename].close()
            del self.cache[ncfilename]

            logger.info("neCDF file %s removed from cache" % ncfilename)

    def initialize_ncfile(self, ncfilename):
        """
initialize_ncfile: function of the netCDF_output_handler that wraps around \
initialize_ncfile to create the output netCDF file and adds it to the cache \
for reduced IO.
        
"""

        self.add_ncfile_to_cache(ncfilename)

        initialize_ncfile(
            ncfilename=ncfilename,
            nc_format=self.nc_format,
            nc_global_attributes=self.nc_global_attributes,
            cache=self.cache,
        )

    def initialize_nc_variable(
        self,
        ncfilename,
        variablename,
        variable_units,
        is_spatial,
        is_temporal,
        long_name,
        standard_name,
        datatype,
    ):
        """

initialize_nc_variable: function of the netCDF_output_handler that creates the \
variable and adds all the necessary dimensions to the output netCDF file and \
includes its dimensions and time dimension to the cache when appropriate.
Function wraps around the functions add_dimension_to_netCDF and add_variable_to_netCDF.

"""

        # initialize the netCDF file if necessary
        if not self.test_ncfile_in_cache(ncfilename):
            self.initialize_ncfile(ncfilename)

        var_dim_keys = []
        for dim_key, dim_info in self.dimension_info.items():
            dim_pos = dim_info["dim_pos"]
            if dim_info["is_spatial"] and is_spatial:
                var_dim_keys.insert(dim_pos, dim_key)
            if dim_info["is_temporal"] and is_temporal:
                var_dim_keys.insert(dim_pos, dim_key)

        nc_dim_keys = list(self.cache[ncfilename].dimensions.keys())

        for dim_key in var_dim_keys:
            if not dim_key in nc_dim_keys:

                logger.debug("dimension %s added to %s" % (dim_key, ncfilename))

                dim_info = self.dimension_info[dim_key]

                # temporal
                if dim_info["is_temporal"]:

                    add_dimension_to_netCDF(
                        ncfilename=ncfilename,
                        name=dim_key,
                        datatype=datatype,
                        unlimited=dim_info["unlimited"],
                        cache=self.cache,
                        long_name=dim_info["long_name"],
                        standard_name=dim_info["standard_name"],
                        calendar=dim_info["calendar"],
                        units=dim_info["units"],
                    )

                    # add the temporal variable
                    self.time_dimension[ncfilename] = dim_key

                # spatial
                elif dim_info["is_spatial"]:

                    values = getattr(self, dim_key)
                    add_dimension_to_netCDF(
                        ncfilename=ncfilename,
                        name=dim_key,
                        datatype=datatype,
                        unlimited=dim_info["unlimited"],
                        values=values,
                        cache=self.cache,
                        long_name=dim_info["long_name"],
                        standard_name=dim_info["standard_name"],
                        units=dim_info["units"],
                    )

                else:
                    pass

        # dimensions of the current variable
        if not ncfilename in self.dimensions.keys():
            self.dimensions[ncfilename] = {variablename: var_dim_keys}

        logger.debug("variable %s added to %s" % (variablename, ncfilename))

        add_variable_to_netCDF(
            ncfilename=ncfilename,
            name=variablename,
            datatype=datatype,
            dimensions=var_dim_keys,
            cache=self.cache,
            long_name=long_name,
            standard_name=standard_name,
            units=variable_units,
        )

        return None

    def add_data_to_netCDF(
        self, ncfilename, variablename, variable_array, **additional_info
    ):
        """

add_data_to_netCDF: function of the netCDF_output_handler that adds the output \
to netCDF file for the variable specified.
Function wraps around the function add_data_to_netCDF and initializes the tuple \
of the dimensions to be written.
     
"""

        # time variable and date of temporal variables
        is_timed = False

        if "is_timed" in additional_info.keys():
            is_timed = additional_info["is_timed"]

        if is_timed:
            if not "time_dimension" in additional_info.keys():
                additional_info["time_dimension"] = self.time_dimension[ncfilename]

        dim_slices = dict(
            [(dim_key, None) for dim_key in self.dimensions[ncfilename][variablename]]
        )

        add_data_to_netCDF(
            ncfilename=ncfilename,
            name=variablename,
            variable_array=variable_array,
            dim_slices=dim_slices,
            cache=self.cache,
            **additional_info,
        )

        return None

    def close_cache(self):

        for ncfilename in list(self.cache.keys()):

            self.remove_ncfile_from_cache(ncfilename)

        return None
