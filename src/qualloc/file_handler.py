import logging
import os
import sys

import pcraster as pcr

from qualloc.netCDF_recipes import netCDF_file_info
from qualloc.spatialDataSet2PCR import (
    compareSpatialAttributes,
    spatialAttributes,
    spatialDataSet,
)

logger = logging.getLogger(__name__)

critical_improvements = str.join("\n\t", ("",))

development = str.join(
    "\n\t",
    (
        "",
        "include option to read timeseries and tables not in netCDF format",
        "",
    ),
)

print("\nDevelopmens for meteo class:")

if len(critical_improvements) > 0:
    print("Critical improvements: \n%s" % critical_improvements)

if len(development) > 0:
    print("Ongoing: \n%s" % development)

if len(critical_improvements) > 0:
    sys.exit()

# global parameters: missing value identifier, types, file extensions
missing_value = -999.9
very_small_number = 1.0e-12

NoneType = type(None)

# default file extensions
file_extensions = {
    ".map": "pcraster",
    ".nc": "netcdf",
    ".nc4": "netcdf",
    ".tif": "pcraster",
    "": "",
}

# file conversion settings

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

# cache of netCDF files
nc_info = netCDF_file_info()


# generic functions to process files


def compose_filename(filename, path, *args):
    """
compose_filename: function that checks whether the filename is an absolute path, \
and if not merges it with the path provided, normalizes the path and tests if \
the file exists. Returns the resulting the filename.
"""

    # make the file name absolute if the file exists
    if os.path.isfile(filename):
        filename = os.path.abspath(filename)
    else:
        filename = os.path.join(path, filename)

    filename = os.path.normpath(filename)

    # substitute any additional arguments
    if args != ():

        if not isinstance(args, tuple):
            args = tuple(args)

        if "%" in filename:
            try:
                filename = filename % (args)
            except Exception:
                logger.warning(
                    "additional arguments could not be converted into the file name %s"
                    % filename
                )

    return filename, os.path.isfile(filename)


def file_is_nc(filename):
    """
    file_is_ncfile: tests if the file extension matches that of a netCDF file;
    returns True if this is the case.
    """

    file_ext = os.path.splitext(filename)[1]

    return file_extensions[file_ext] == "netcdf"


def file_is_pcr(filename):
    """
    file_is_ncfile: tests if the file extension matches that of a netCDF file;
    returns True if this is the case.
    """

    file_ext = os.path.splitext(filename)[1]

    return file_extensions[file_ext] == "pcraster"


def read_file_entry(
    filename,
    variablename,
    inputpath="",
    file_subst_args=(),
    clone_attributes=None,
    forced_non_spatial=False,
    datatype=pcr.Scalar,
    date=None,
    date_selection_method="exact",
    allow_year_substitution=False,
):
    """

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

"""
    var_out = None

    filename = str(filename)
    val_str = str(filename)
    datatype_str = str(datatype)
    if "VALUESCALE." in datatype_str:
        datatype_str = datatype_str.replace("VALUESCALE.", "")

    # compose the file name and check that it exists
    filename, existing_file = compose_filename(filename, inputpath, file_subst_args)

    if existing_file and file_is_nc(filename):

        # netCDF: read from the cache
        var_out = nc_info.read_nc_field(
            filename,
            variablename,
            clone_attributes=clone_attributes,
            forced_non_spatial=forced_non_spatial,
            datatype=datatype,
            date=date,
            date_selection_method=date_selection_method,
            allow_year_substitution=allow_year_substitution,
        )

    elif existing_file and file_is_pcr(filename):

        # PCRaster file

        if isinstance(clone_attributes, NoneType):

            # PCRaster maps can only be processed if clone attributes are passed
            message_str = "no clone attributes are provided to process the PCRaster map"
            logger.error(message_str)
            sys.exit(message_str)

        data_attributes = spatialAttributes(filename)
        fits_extent, same_resolution, x_resample_ratio, y_resample_ratio = (
            compareSpatialAttributes(data_attributes, clone_attributes)
        )

        file_ext = os.path.splitext(filename)[1]
        same_clone = fits_extent and same_resolution and file_ext == ".map"

        resample_method = resample_methods[datatype_str]

        print(f"{filename} (fits extent: {fits_extent})")

        if same_clone:

            var_out = pcr.readmap(filename)
            conversion_method = getattr(pcr, datatype_str.lower())
            var_out = conversion_method(var_out)

        else:

            # read the variable using gdal_translate
            var_out = getattr(
                spatialDataSet(
                    variablename,
                    filename,
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
                ),
                variablename,
            )

        # output available: log the message
        message_str = "value of %s read from %s" % (variablename, filename)
        message_str = str.join(
            " ",
            (message_str, "in PCRaster format which does not contain variable info"),
        )
        if not isinstance(date, NoneType):
            message_str = str.join(
                " ", (message_str, "and is unaware of the actual date %s" % date)
            )

        logger.debug(message_str)

    else:

        # the file type cannot be read
        try:
            var_out = float(val_str)
            if forced_non_spatial:
                conversion_method = conversion_methods[datatype_str.title()]
            else:
                conversion_method = getattr(pcr, datatype_str.lower())
            var_out = conversion_method(var_out)
            logger.debug(
                "%s is recognized as a value instead of a netCDF or PCRaster file and is converted into %s"
                % (val_str, str(conversion_method))
            )
        except Exception:
            logger.error(
                "%s is not recognized as a netCDF or PCRaster file and cannot be converted"
                % filename
            )

    return var_out


def close_nc_cache():
    """closes the cache of netCDF input files"""

    nc_info.close_cache()

    return None


def main():
    pass


if __name__ == "__main__":
    main()
