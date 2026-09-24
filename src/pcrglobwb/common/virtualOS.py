import calendar
import datetime
import glob
import logging
import math
import os
import random
import re
import shutil
import subprocess
import sys

import netCDF4 as nc
import numpy as np
import pcraster as pcr
import pyinterp.backends.xarray
import xarray as xr
import zarr
from six.moves import range

logger = logging.getLogger(__name__)

# file cache to minimize/reduce opening/closing files.
filecache = dict()

# Global variables:
MV = 1e20
smallNumber = 1e-39

# and set pi
pi = math.pi

# tuple of netcdf file suffixes (extensions) that can be used:
netcdf_suffixes = (".nc4", ".nc")

# maximum number of tries for reading files:
max_num_of_tries = 5


def readUpstreamDischarge(
    ncFile,
    varName="automatic",
    dateInput=None,
    useDoy=None,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
):
    logger.debug(f"Reading Upstream Discharge: {ncFile}")
    lon = pcr.pcr2numpy(pcr.xcoordinate(pcr.defined(cloneMapFileName)), np.nan)[0, :]
    lat = np.sort(
        pcr.pcr2numpy(pcr.ycoordinate(pcr.defined(cloneMapFileName)), np.nan)[:, 0]
    )

    ds = xr.open_dataset(ncFile, chunks="auto", engine="netcdf4")
    ds = ds.sel(time=dateInput).compute()
    ds = ds.reindex(lat=lat, lon=lon).sortby("lat", ascending=False)
    ds = ds.fillna(0.0)
    cropData = ds.discharge.values
    outPCR = pcr.numpy2pcr(
        pcr.Scalar, regridData2FinerGrid(1, cropData, float(0)), float(0)
    )
    ds.close()
    return outPCR


def readDownscalingZarr(
    ncFile,
    dateInput=None,
    useDoy=None,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
):
    f = zarr.convenience.open(ncFile)

    keys = sorted(f.keys())

    yRef = "lat"
    xRef = "lon"
    if LatitudeLongitude:
        if "latitude" in keys:
            yRef = "latitude"
        if "longitude" in keys:
            xRef = "longitude"

    dims = ["time", xRef, yRef]
    varName = [item for item in keys if item not in dims][0]

    attributeClone = getMapAttributesALL(cloneMapFileName)
    cellsizeClone = attributeClone["cellsize"]
    rowsClone = attributeClone["rows"]
    colsClone = attributeClone["cols"]
    xULClone = attributeClone["xUL"]
    yULClone = attributeClone["yUL"]
    # get the attributes of input (netCDF)
    cellsizeInput = f[yRef][0] - f[yRef][1]
    cellsizeInput = float(cellsizeInput)

    factor = int(round(float(cellsizeInput) / float(cellsizeClone)))
    diffX = np.abs(f[xRef][:] - (xULClone + 0.5 * cellsizeInput))
    xIdxSta = np.argmin(diffX)
    xIdxEnd = math.ceil(xIdxSta + colsClone / factor)
    xslice = slice(xIdxSta, xIdxEnd)

    diffY = np.abs(f[yRef][:] - (yULClone - 0.5 * cellsizeInput))
    yIdxSta = np.argmin(diffY)
    yIdxEnd = math.ceil(yIdxSta + rowsClone / factor)
    yslice = slice(yIdxSta, yIdxEnd)

    timeID = dateInput - 1

    cropData = f[varName].get_basic_selection((timeID, xslice, yslice))[:]
    cropData = np.nan_to_num(cropData).T

    lon = pcr.pcr2numpy(pcr.xcoordinate(cloneMapFileName), np.nan)[0, :]
    lat = pcr.pcr2numpy(pcr.ycoordinate(cloneMapFileName), np.nan)[:, 0]
    cropData = xr.DataArray(
        cropData,
        dims=["latitude", "longitude"],
        coords=dict(longitude=lon, latitude=lat),
    ).sortby("latitude", ascending=False)

    cropData = cropData.values
    # convert to PCR object and close f
    if specificFillValue is not None:
        outPCR = pcr.numpy2pcr(pcr.Scalar, cropData, float(specificFillValue))
    else:
        try:
            outPCR = pcr.numpy2pcr(pcr.Scalar, cropData, float(f[varName].fill_value))
        except Exception:
            outPCR = pcr.numpy2pcr(pcr.Scalar, cropData, float(MV))

    return outPCR


def readDownscalingMeteo(
    ncFile,
    varName="automatic",
    dateInput=None,
    useDoy=None,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
):
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    # Get netCDF file and variable name:

    if varName != "automatic":
        logger.debug(
            "reading variable: " + str(varName) + " from the file: " + str(ncFile)
        )

    if ncFile in list(filecache.keys()):
        f = filecache[ncFile]

    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f

    varName = str(varName)

    if LatitudeLongitude:
        try:
            f.variables["lat"] = f.variables["latitude"]
            f.variables["lon"] = f.variables["longitude"]
        except Exception:
            pass

    if varName == "automatic":
        nc_dims = [dim for dim in f.dimensions]
        nc_vars = [var for var in f.variables]
        for var in nc_vars:
            if var not in nc_dims and var not in [
                "lat",
                "lon",
                "latitude",
                "longitude",
            ]:
                varName = var
        logger.debug(
            "reading variable: " + str(varName) + " from the file: " + str(ncFile)
        )

    if dateInput is None:
        logger.debug("Using the first time step in the netcdf file.")
        idx = 0
        if len(f.variables["time"]) > 1:
            logger.warning(
                "NOTE that there are more than one time steps in the netcdf file."
            )

    else:
        # date
        date = dateInput
        if useDoy == "Yes":
            logger.debug(
                "Finding the date based on the given climatology doy index (1 to 366, or index 0 to 365)"
            )
            idx = int(dateInput) - 1
        elif (
            useDoy == "month"
        ):  # PS: WE NEED THIS ONE FOR NETCDF FILES that contain only 12 monthly values (e.g. cropCoefficientWaterNC).
            logger.debug(
                "Finding the date based on the given climatology month index (1 to 12, or index 0 to 11)"
            )
            # make sure that date is in the correct format
            if isinstance(date, str):
                date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
            idx = int(date.month) - 1
        else:
            # make sure that date is in the correct format
            if isinstance(date, str):
                date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
            date = datetime.datetime(date.year, date.month, date.day)
            if useDoy == "yearly":
                date = datetime.datetime(date.year, int(1), int(1))
            if useDoy == "monthly":
                date = datetime.datetime(date.year, date.month, int(1))
            if (
                useDoy == "yearly"
                or useDoy == "monthly"
                or useDoy == "daily_seasonal"
                or useDoy == "daily"
                or useDoy == "daily_per_monthly_file"
            ):
                # if the desired year is not available, use the first year or the last year that is available
                first_year_in_nc_file = findFirstYearInNCTime(f.variables["time"])
                last_year_in_nc_file = findLastYearInNCTime(f.variables["time"])
                #
                if date.year < first_year_in_nc_file:
                    if (
                        date.day == 29
                        and date.month == 2
                        and calendar.isleap(date.year)
                        and not calendar.isleap(first_year_in_nc_file)
                    ):
                        date = datetime.datetime(first_year_in_nc_file, date.month, 28)
                    else:
                        date = datetime.datetime(
                            first_year_in_nc_file, date.month, date.day
                        )
                    msg = "\n"
                    msg += (
                        "WARNING related to the netcdf file: "
                        + str(ncFile)
                        + " ; variable: "
                        + str(varName)
                        + " !!!!!!"
                        + "\n"
                    )
                    msg += "The date " + str(dateInput) + " is NOT available. "
                    msg += (
                        "The date "
                        + str(date.year)
                        + "-"
                        + str(date.month)
                        + "-"
                        + str(date.day)
                        + " is used."
                    )
                    msg += "\n"
                    logger.warning(msg)
                if date.year > last_year_in_nc_file:
                    if (
                        date.day == 29
                        and date.month == 2
                        and calendar.isleap(date.year)
                        and not calendar.isleap(last_year_in_nc_file)
                    ):
                        date = datetime.datetime(last_year_in_nc_file, date.month, 28)
                    else:
                        date = datetime.datetime(
                            last_year_in_nc_file, date.month, date.day
                        )
                    msg = "\n"
                    msg += (
                        "WARNING related to the netcdf file: "
                        + str(ncFile)
                        + " ; variable: "
                        + str(varName)
                        + " !!!!!!"
                        + "\n"
                    )
                    msg += "The date " + str(dateInput) + " is NOT available. "
                    msg += (
                        "The date "
                        + str(date.year)
                        + "-"
                        + str(date.month)
                        + "-"
                        + str(date.day)
                        + " is used."
                    )
                    msg += "\n"
                    logger.warning(msg)
            try:
                idx = nc.date2index(
                    date,
                    f.variables["time"],
                    calendar=f.variables["time"].calendar,
                    select="exact",
                )
                msg = (
                    "The date "
                    + str(date.year)
                    + "-"
                    + str(date.month)
                    + "-"
                    + str(date.day)
                    + " 00:00:00 is available. The 'exact' option is used while selecting netcdf time."
                )
                logger.debug(msg)
            except Exception:
                msg = (
                    "The date "
                    + str(date.year)
                    + "-"
                    + str(date.month)
                    + "-"
                    + str(date.day)
                    + " 00:00:00 is NOT available. The 'exact' option CANNOT be used while selecting netcdf time."
                )
                logger.debug(msg)
                if useDoy == "daily":
                    idx = nc.date2index(
                        date,
                        f.variables["time"],
                        calendar=f.variables["time"].calendar,
                        select="after",
                    )
                    msg = "\n"
                    msg += (
                        "WARNING related to the netcdf file: "
                        + str(ncFile)
                        + " ; variable: "
                        + str(varName)
                        + " !!!!!!"
                        + "\n"
                    )
                    msg += (
                        "The date "
                        + str(date.year)
                        + "-"
                        + str(date.month)
                        + "-"
                        + str(date.day)
                        + " 00:00:00 is NOT available. The 'after' option is used while selecting netcdf time."
                    )
                    msg += "\n"
                else:
                    try:
                        idx = nc.date2index(
                            date,
                            f.variables["time"],
                            calendar=f.variables["time"].calendar,
                            select="before",
                        )
                        msg = "\n"
                        msg += (
                            "WARNING related to the netcdf file: "
                            + str(ncFile)
                            + " ; variable: "
                            + str(varName)
                            + " !!!!!!"
                            + "\n"
                        )
                        msg += (
                            "The date "
                            + str(date.year)
                            + "-"
                            + str(date.month)
                            + "-"
                            + str(date.day)
                            + " 00:00:00 is NOT available. The 'before' option is used while selecting netcdf time."
                        )
                        msg += "\n"
                    except Exception:
                        idx = nc.date2index(
                            date,
                            f.variables["time"],
                            calendar=f.variables["time"].calendar,
                            select="after",
                        )
                        msg = "\n"
                        msg += (
                            "WARNING related to the netcdf file: "
                            + str(ncFile)
                            + " ; variable: "
                            + str(varName)
                            + " !!!!!!"
                            + "\n"
                        )
                        msg += (
                            "The date "
                            + str(date.year)
                            + "-"
                            + str(date.month)
                            + "-"
                            + str(date.day)
                            + " 00:00:00 is NOT available. The 'after' option is used while selecting netcdf time."
                        )
                        msg += "\n"
                logger.warning(msg)
                date_string = nc.num2date(
                    f.variables["time"][int(idx)],
                    f.variables["time"].units,
                    f.variables["time"].calendar,
                )
                logger.warning("Using the datetime " + str(date_string))
                logger.warning(msg)

    idx = int(idx)
    logger.debug("Using the date index " + str(idx))

    date_string = nc.num2date(
        f.variables["time"][int(idx)],
        f.variables["time"].units,
        f.variables["time"].calendar,
    )
    logger.debug("Using the datetime " + str(date_string))

    attributeClone = getMapAttributesALL(cloneMapFileName)
    cellsizeClone = attributeClone["cellsize"]
    rowsClone = attributeClone["rows"]
    colsClone = attributeClone["cols"]
    xULClone = attributeClone["xUL"]
    yULClone = attributeClone["yUL"]
    # get the attributes of input (netCDF)
    cellsizeInput = f.variables["lat"][0] - f.variables["lat"][1]
    cellsizeInput = float(cellsizeInput)

    # check data on dimensions - this correction is needed in case of the WFDEI_Forcing which has includes levels for surface varables (time, height/level, lat, lon)
    if f.variables[varName].ndim == 4:
        # not standard NC format
        logger.warning(
            "WARNING: the netCDF file %s has an additional dimension for variable %s ; the last two are read as latitude, longitude"
            % (ncFile, varName)
        )
        # file with additional layer/dimension
        cropData = f.variables[varName][int(idx), 0, :, :]  # still original data
    else:
        # standard nc file
        cropData = f.variables[varName][int(idx), :, :]  # still original data

    factor = 1  # needed in regridData2FinerGrid
    factor = int(round(float(cellsizeInput) / float(cellsizeClone)))

    # crop to cloneMap:
    minX = min(abs(f.variables["lon"][:] - (xULClone + 0.5 * cellsizeInput)))
    xIdxSta = (
        int(
            np.where(
                abs(f.variables["lon"][:] - (xULClone + 0.5 * cellsizeInput)) == minX
            )[0]
        )
        - 1
    )
    if xIdxSta == -1:
        xIdxSta = 0

    xIdxEnd = int(math.ceil((xIdxSta + 1) + colsClone / (factor))) + 1

    minY = min(abs(f.variables["lat"][:] - (yULClone - 0.5 * cellsizeInput)))

    yIdxSta = (
        int(
            np.where(
                abs(f.variables["lat"][:] - (yULClone - 0.5 * cellsizeInput)) == minY
            )[0]
        )
        - 1
    )

    yIdxEnd = int(math.ceil((yIdxSta + 1) + rowsClone / (factor))) + 1

    # retrieve data from netCDF for slice

    if f.variables[varName].ndim == 4:
        # not standard NC format
        logger.warning(
            "WARNING: the netCDF file %s has an additional dimension for variable %s ; the last two are read as latitude, longitude"
            % (ncFile, varName)
        )
        # -file with additional layer
        cropData = f.variables[varName][
            int(idx), 0, yIdxSta:yIdxEnd, xIdxSta:xIdxEnd
        ]  # selection of original data
    else:
        # standard nc file
        cropData = f.variables[varName][
            int(idx), yIdxSta:yIdxEnd, xIdxSta:xIdxEnd
        ]  # selection of original data
    lon = pcr.pcr2numpy(pcr.xcoordinate(pcr.defined(cloneMapFileName)), np.nan)[0, :]
    lat = np.sort(
        pcr.pcr2numpy(pcr.ycoordinate(pcr.defined(cloneMapFileName)), np.nan)[:, 0]
    )

    array = xr.DataArray(
        cropData,
        dims=["latitude", "longitude"],
        coords=dict(
            latitude=f.variables["lat"][yIdxSta:yIdxEnd],
            longitude=f.variables["lon"][xIdxSta:xIdxEnd],
        ),
    ).sortby("latitude")

    array = pyinterp.backends.xarray.Grid2D(array, geodetic=False)
    mx, my = np.meshgrid(lon, lat, indexing="ij")
    cropData = array.bivariate(
        coords=dict(longitude=mx.ravel(), latitude=my.ravel()), num_threads=1
    )
    cropData = cropData.reshape(mx.shape).T

    cropData = xr.DataArray(
        cropData,
        dims=["latitude", "longitude"],
        coords=dict(longitude=lon, latitude=lat),
    ).sortby("latitude", ascending=False)

    cropData = cropData.values
    if specificFillValue is not None:
        outPCR = pcr.numpy2pcr(pcr.Scalar, cropData, float(specificFillValue))
    else:
        try:
            outPCR = pcr.numpy2pcr(
                pcr.Scalar, cropData, float(f.variables[varName]._FillValue)
            )
        except Exception:
            outPCR = pcr.numpy2pcr(pcr.Scalar, cropData, float(MV))
    return outPCR


def getFileList(inputDir, filePattern):
    """creates a dictionary of  files meeting the pattern specified"""
    fileNameList = glob.glob(os.path.join(inputDir, filePattern))
    ll = {}
    for fileName in fileNameList:
        ll[os.path.split(fileName)[-1]] = fileName
    return ll


def checkVariableInNC(ncFile, varName):

    logger.debug(
        "Check whether the variable: "
        + str(varName)
        + " is defined in the file: "
        + str(ncFile)
    )

    if ncFile in list(filecache.keys()):
        f = filecache[ncFile]

    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f

    varName = str(varName)

    return varName in list(f.variables.keys())


def netcdf2PCRobjCloneWithoutTime(
    ncFile,
    varName,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
    absolutePath=None,
):

    iter_try = 0
    while iter_try < max_num_of_tries:
        try:
            return singleTryNetcdf2PCRobjCloneWithoutTime(
                ncFile, varName, cloneMapFileName, LatitudeLongitude, specificFillValue
            )
            iter_try = max_num_of_tries + 100
        except Exception:
            iter_try = iter_try + 1
            logger.warning("Re-try to read file: " + str(ncFile))

    if iter_try >= max_num_of_tries:
        logger.error("CANNOT READ file: " + str(ncFile))
        return singleTryNetcdf2PCRobjCloneWithoutTime(
            ncFile, varName, cloneMapFileName, LatitudeLongitude, specificFillValue
        )


def singleTryNetcdf2PCRobjCloneWithoutTime(
    ncFile,
    varName,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
    absolutePath=None,
):

    if absolutePath is not None:
        ncFile = getFullPath(ncFile, absolutePath)

    logger.debug("reading variable: " + str(varName) + " from the file: " + str(ncFile))

    #
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    # Get netCDF file and variable name:

    f = nc.Dataset(ncFile)
    varName = str(varName)

    if varName == "automatic":
        nc_dims = [dim for dim in f.dimensions]
        nc_vars = [var for var in f.variables]
        for var in nc_vars:
            if var not in nc_dims and var not in [
                "lat",
                "lon",
                "latitude",
                "longitude",
            ]:
                varName = var
        logger.debug(
            "reading variable: " + str(varName) + " from the file: " + str(ncFile)
        )

    if LatitudeLongitude:
        try:
            f.variables["lat"] = f.variables["latitude"]
            f.variables["lon"] = f.variables["longitude"]
        except Exception:
            pass

    sameClone = True
    # check whether clone and input maps have the same attributes:
    if cloneMapFileName is not None:
        # get the attributes of cloneMap
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone["cellsize"]
        rowsClone = attributeClone["rows"]
        colsClone = attributeClone["cols"]
        xULClone = attributeClone["xUL"]
        yULClone = attributeClone["yUL"]
        # get the attributes of input (netCDF)
        cellsizeInput = f.variables["lat"][0] - f.variables["lat"][1]
        cellsizeInput = float(cellsizeInput)
        rowsInput = len(f.variables["lat"])
        colsInput = len(f.variables["lon"])
        xULInput = f.variables["lon"][0] - 0.5 * cellsizeInput
        yULInput = f.variables["lat"][0] + 0.5 * cellsizeInput
        # check whether both maps have the same attributes
        if cellsizeClone != cellsizeInput:
            sameClone = False
        if rowsClone != rowsInput:
            sameClone = False
        if colsClone != colsInput:
            sameClone = False
        if xULClone != xULInput:
            sameClone = False
        if yULClone != yULInput:
            sameClone = False

    factor = 1
    yslice = slice(None)
    xslice = slice(None)
    if not sameClone:

        factor = int(round(float(cellsizeInput) / float(cellsizeClone)))
        if factor > 1:
            logger.debug(
                "Resample: input cell size = "
                + str(float(cellsizeInput))
                + " ; output/clone cell size = "
                + str(float(cellsizeClone))
            )

        diffX = np.abs(f.variables["lon"][:] - (xULClone + 0.5 * cellsizeInput))
        xIdxSta = np.argmin(diffX)
        xIdxEnd = math.ceil(xIdxSta + colsClone / factor)
        xslice = slice(xIdxSta, xIdxEnd)

        diffY = np.abs(f.variables["lat"][:] - (yULClone - 0.5 * cellsizeInput))
        yIdxSta = np.argmin(diffY)
        yIdxEnd = math.ceil(yIdxSta + rowsClone / factor)
        yslice = slice(yIdxSta, yIdxEnd)

    cropData = f.variables[varName][yslice, xslice]

    # convert to PCR object and close f
    if specificFillValue is not None:
        outPCR = pcr.numpy2pcr(
            pcr.Scalar,
            regridData2FinerGrid(factor, cropData, float(specificFillValue)),
            float(specificFillValue),
        )
    else:
        try:
            outPCR = pcr.numpy2pcr(
                pcr.Scalar,
                regridData2FinerGrid(
                    factor, cropData, float(f.variables[varName]._FillValue)
                ),
                float(f.variables[varName]._FillValue),
            )
        except Exception:
            outPCR = pcr.numpy2pcr(
                pcr.Scalar,
                regridData2FinerGrid(
                    factor, cropData, float(f.variables[varName].missing_value)
                ),
                float(f.variables[varName].missing_value),
            )

    # we should close the file
    f.close()

    # PCRaster object
    return outPCR


def netcdf2PCRobjClone(
    ncFile,
    varName="automatic",
    dateInput=None,
    useDoy=None,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
):

    iter_try = 0
    while iter_try < max_num_of_tries:
        try:
            return singleTryNetcdf2PCRobjClone(
                ncFile,
                varName,
                dateInput,
                useDoy,
                cloneMapFileName,
                LatitudeLongitude,
                specificFillValue,
            )
            iter_try = max_num_of_tries + 100
        except Exception:
            iter_try = iter_try + 1
            logger.warning("Re-try to read file: " + str(ncFile))

    if iter_try >= max_num_of_tries:
        logger.error("CANNOT READ file: " + str(ncFile))
        return singleTryNetcdf2PCRobjClone(
            ncFile,
            varName,
            dateInput,
            useDoy,
            cloneMapFileName,
            LatitudeLongitude,
            specificFillValue,
        )


def singleTryNetcdf2PCRobjClone(
    ncFile,
    varName="automatic",
    dateInput=None,
    useDoy=None,
    cloneMapFileName=None,
    LatitudeLongitude=True,
    specificFillValue=None,
):
    #
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    # Get netCDF file and variable name:

    if varName != "automatic":
        logger.debug(
            "reading variable: " + str(varName) + " from the file: " + str(ncFile)
        )

    if ncFile in list(filecache.keys()):
        f = filecache[ncFile]

    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f

    varName = str(varName)

    if LatitudeLongitude:
        try:
            f.variables["lat"] = f.variables["latitude"]
            f.variables["lon"] = f.variables["longitude"]
        except Exception:
            pass

    if varName == "automatic":
        nc_dims = [dim for dim in f.dimensions]
        nc_vars = [var for var in f.variables]
        for var in nc_vars:
            if var not in nc_dims and var not in [
                "lat",
                "lon",
                "latitude",
                "longitude",
            ]:
                varName = var
        logger.debug(
            "reading variable: " + str(varName) + " from the file: " + str(ncFile)
        )

    if varName == "evapotranspiration":
        try:
            f.variables["evapotranspiration"] = f.variables["referencePotET"]
        except Exception:
            pass

    if varName == "kc":  # the variable name in PCR-GLOBWB
        try:
            f.variables["kc"] = f.variables[
                "Cropcoefficient"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if varName == "interceptCapInput":  # the variable name in PCR-GLOBWB
        try:
            f.variables["interceptCapInput"] = f.variables[
                "Interceptioncapacity"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if varName == "coverFractionInput":  # the variable name in PCR-GLOBWB
        try:
            f.variables["coverFractionInput"] = f.variables[
                "Coverfraction"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if varName == "fracVegCover":  # the variable name in PCR-GLOBWB
        try:
            f.variables["fracVegCover"] = f.variables[
                "vegetation_fraction"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if varName == "minSoilDepthFrac":  # the variable name in PCR-GLOBWB
        try:
            f.variables["minSoilDepthFrac"] = f.variables[
                "minRootDepthFraction"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if varName == "maxSoilDepthFrac":  # the variable name in PCR-GLOBWB
        try:
            f.variables["maxSoilDepthFrac"] = f.variables[
                "maxRootDepthFraction"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if varName == "arnoBeta":  # the variable name in PCR-GLOBWB
        try:
            f.variables["arnoBeta"] = f.variables[
                "arnoSchemeBeta"
            ]  # the variable name in the netcdf file
        except Exception:
            pass

    if dateInput is None:
        logger.debug("Using the first time step in the netcdf file.")
        idx = 0
        if len(f.variables["time"]) > 1:
            logger.warning(
                "NOTE that there are more than one time steps in the netcdf file."
            )

    else:

        # date
        date = dateInput
        if useDoy == "Yes":
            logger.debug(
                "Finding the date based on the given climatology doy index (1 to 366, or index 0 to 365)"
            )
            idx = int(dateInput) - 1
        elif (
            useDoy == "month"
        ):  # PS: WE NEED THIS ONE FOR NETCDF FILES that contain only 12 monthly values (e.g. cropCoefficientWaterNC).
            logger.debug(
                "Finding the date based on the given climatology month index (1 to 12, or index 0 to 11)"
            )
            # make sure that date is in the correct format
            if isinstance(date, str):
                date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
            idx = int(date.month) - 1
        else:
            # make sure that date is in the correct format
            if isinstance(date, str):
                date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
            date = datetime.datetime(date.year, date.month, date.day)
            if useDoy == "yearly":
                date = datetime.datetime(date.year, int(1), int(1))
            if useDoy == "monthly":
                date = datetime.datetime(date.year, date.month, int(1))
            if (
                useDoy == "yearly"
                or useDoy == "monthly"
                or useDoy == "daily_seasonal"
                or useDoy == "daily"
                or useDoy == "daily_per_monthly_file"
            ):
                # if the desired year is not available, use the first year or the last year that is available
                first_year_in_nc_file = findFirstYearInNCTime(f.variables["time"])
                last_year_in_nc_file = findLastYearInNCTime(f.variables["time"])
                #
                if date.year < first_year_in_nc_file:
                    if (
                        date.day == 29
                        and date.month == 2
                        and calendar.isleap(date.year)
                        and not calendar.isleap(first_year_in_nc_file)
                    ):
                        date = datetime.datetime(first_year_in_nc_file, date.month, 28)
                    else:
                        date = datetime.datetime(
                            first_year_in_nc_file, date.month, date.day
                        )
                    msg = "\n"
                    msg += (
                        "WARNING related to the netcdf file: "
                        + str(ncFile)
                        + " ; variable: "
                        + str(varName)
                        + " !!!!!!"
                        + "\n"
                    )
                    msg += "The date " + str(dateInput) + " is NOT available. "
                    msg += (
                        "The date "
                        + str(date.year)
                        + "-"
                        + str(date.month)
                        + "-"
                        + str(date.day)
                        + " is used."
                    )
                    msg += "\n"
                    logger.warning(msg)
                if date.year > last_year_in_nc_file:
                    if (
                        date.day == 29
                        and date.month == 2
                        and calendar.isleap(date.year)
                        and not calendar.isleap(last_year_in_nc_file)
                    ):
                        date = datetime.datetime(last_year_in_nc_file, date.month, 28)
                    else:
                        date = datetime.datetime(
                            last_year_in_nc_file, date.month, date.day
                        )
                    msg = "\n"
                    msg += (
                        "WARNING related to the netcdf file: "
                        + str(ncFile)
                        + " ; variable: "
                        + str(varName)
                        + " !!!!!!"
                        + "\n"
                    )
                    msg += "The date " + str(dateInput) + " is NOT available. "
                    msg += (
                        "The date "
                        + str(date.year)
                        + "-"
                        + str(date.month)
                        + "-"
                        + str(date.day)
                        + " is used."
                    )
                    msg += "\n"
                    logger.warning(msg)
            try:
                idx = nc.date2index(
                    date,
                    f.variables["time"],
                    calendar=f.variables["time"].calendar,
                    select="exact",
                )
                msg = (
                    "The date "
                    + str(date.year)
                    + "-"
                    + str(date.month)
                    + "-"
                    + str(date.day)
                    + " 00:00:00 is available. The 'exact' option is used while selecting netcdf time."
                )
                logger.debug(msg)
            except Exception:
                msg = (
                    "The date "
                    + str(date.year)
                    + "-"
                    + str(date.month)
                    + "-"
                    + str(date.day)
                    + " 00:00:00 is NOT available. The 'exact' option CANNOT be used while selecting netcdf time."
                )
                logger.debug(msg)
                if useDoy == "daily":
                    idx = nc.date2index(
                        date,
                        f.variables["time"],
                        calendar=f.variables["time"].calendar,
                        select="after",
                    )
                    msg = "\n"
                    msg += (
                        "WARNING related to the netcdf file: "
                        + str(ncFile)
                        + " ; variable: "
                        + str(varName)
                        + " !!!!!!"
                        + "\n"
                    )
                    msg += (
                        "The date "
                        + str(date.year)
                        + "-"
                        + str(date.month)
                        + "-"
                        + str(date.day)
                        + " 00:00:00 is NOT available. The 'after' option is used while selecting netcdf time."
                    )
                    msg += "\n"
                else:
                    try:
                        idx = nc.date2index(
                            date,
                            f.variables["time"],
                            calendar=f.variables["time"].calendar,
                            select="before",
                        )
                        msg = "\n"
                        msg += (
                            "WARNING related to the netcdf file: "
                            + str(ncFile)
                            + " ; variable: "
                            + str(varName)
                            + " !!!!!!"
                            + "\n"
                        )
                        msg += (
                            "The date "
                            + str(date.year)
                            + "-"
                            + str(date.month)
                            + "-"
                            + str(date.day)
                            + " 00:00:00 is NOT available. The 'before' option is used while selecting netcdf time."
                        )
                        msg += "\n"
                    except Exception:
                        idx = nc.date2index(
                            date,
                            f.variables["time"],
                            calendar=f.variables["time"].calendar,
                            select="after",
                        )
                        msg = "\n"
                        msg += (
                            "WARNING related to the netcdf file: "
                            + str(ncFile)
                            + " ; variable: "
                            + str(varName)
                            + " !!!!!!"
                            + "\n"
                        )
                        msg += (
                            "The date "
                            + str(date.year)
                            + "-"
                            + str(date.month)
                            + "-"
                            + str(date.day)
                            + " 00:00:00 is NOT available. The 'after' option is used while selecting netcdf time."
                        )
                        msg += "\n"
                logger.warning(msg)
                date_string = nc.num2date(
                    f.variables["time"][int(idx)],
                    f.variables["time"].units,
                    f.variables["time"].calendar,
                )
                logger.warning("Using the datetime " + str(date_string))
                logger.warning(msg)

    idx = int(idx)
    logger.debug("Using the date index " + str(idx))

    date_string = nc.num2date(
        f.variables["time"][int(idx)],
        f.variables["time"].units,
        f.variables["time"].calendar,
    )
    logger.debug("Using the datetime " + str(date_string))

    sameClone = True
    # check whether clone and input maps have the same attributes:
    if cloneMapFileName is not None:
        # get the attributes of cloneMap
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone["cellsize"]
        rowsClone = attributeClone["rows"]
        colsClone = attributeClone["cols"]
        xULClone = attributeClone["xUL"]
        yULClone = attributeClone["yUL"]
        # get the attributes of input (netCDF)
        cellsizeInput = f.variables["lat"][0] - f.variables["lat"][1]
        cellsizeInput = float(cellsizeInput)
        rowsInput = len(f.variables["lat"])
        colsInput = len(f.variables["lon"])
        xULInput = f.variables["lon"][0] - 0.5 * cellsizeInput
        yULInput = f.variables["lat"][0] + 0.5 * cellsizeInput
        # check whether both maps have the same attributes
        if cellsizeClone != cellsizeInput:
            sameClone = False
        if rowsClone != rowsInput:
            sameClone = False
        if colsClone != colsInput:
            sameClone = False
        if xULClone != xULInput:
            sameClone = False
        if yULClone != yULInput:
            sameClone = False

    factor = 1
    yslice = slice(None)
    xslice = slice(None)
    if not sameClone:

        factor = int(round(float(cellsizeInput) / float(cellsizeClone)))
        if factor > 1:
            logger.debug(
                "Resample: input cell size = "
                + str(float(cellsizeInput))
                + " ; output/clone cell size = "
                + str(float(cellsizeClone))
            )

        diffX = np.abs(f.variables["lon"][:] - (xULClone + 0.5 * cellsizeInput))
        xIdxSta = np.argmin(diffX)
        xIdxEnd = math.ceil(xIdxSta + colsClone / factor)
        xslice = slice(xIdxSta, xIdxEnd)

        diffY = np.abs(f.variables["lat"][:] - (yULClone - 0.5 * cellsizeInput))
        yIdxSta = np.argmin(diffY)
        yIdxEnd = math.ceil(yIdxSta + rowsClone / factor)
        yslice = slice(yIdxSta, yIdxEnd)

    # retrieve data from netCDF for slice
    if f.variables[varName].ndim == 4:
        # not standard NC format
        logger.warning(
            "WARNING: the netCDF file %s has an additional dimension for variable %s ; the last two are read as latitude, longitude"
            % (ncFile, varName)
        )
        # -file with additional layer
        cropData = f.variables[varName][
            int(idx), 0, yslice, xslice
        ]  # selection of original data
    else:
        # standard nc file
        cropData = f.variables[varName][
            int(idx), yslice, xslice
        ]  # selection of original data

    # convert to PCR object and close f
    if specificFillValue is not None:
        outPCR = pcr.numpy2pcr(
            pcr.Scalar,
            regridData2FinerGrid(factor, cropData, float(specificFillValue)),
            float(specificFillValue),
        )
    else:
        try:
            outPCR = pcr.numpy2pcr(
                pcr.Scalar,
                regridData2FinerGrid(
                    factor, cropData, float(f.variables[varName]._FillValue)
                ),
                float(f.variables[varName]._FillValue),
            )
        except Exception:
            outPCR = pcr.numpy2pcr(
                pcr.Scalar,
                regridData2FinerGrid(
                    factor, cropData, float(f.variables[varName].missing_value)
                ),
                float(f.variables[varName].missing_value),
            )

    if useDoy == "daily_per_monthly_file":
        # close the file on the last day of the month
        tomorrow = date + datetime.timedelta(days=1)
        if tomorrow.day == 1:
            # close the file
            f.close()
            # remove from the cache
            del filecache[ncFile]

    # PCRaster object
    return outPCR


def netcdf2PCRobj(ncFile, varName, dateInput):
    # EHS (04 APR 2013): To convert netCDF (tss) file to PCR file.
    # The cloneMap is globally defined (outside this method).

    # Get netCDF file and variable name:
    f = nc.Dataset(ncFile)
    varName = str(varName)

    # date
    date = dateInput
    if isinstance(date, str):
        date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
    date = datetime.datetime(date.year, date.month, date.day)

    # time index (in the netCDF file)
    nctime = f.variables["time"]  # A netCDF time variable object.
    idx = nc.date2index(date, nctime, calendar=nctime.calendar, select="exact")

    # convert to PCR object and close f
    outPCR = pcr.numpy2pcr(
        pcr.Scalar,
        (f.variables[varName][idx].data),
        float(f.variables[varName]._FillValue),
    )
    f.close()
    # PCRaster object
    return outPCR


def writePCRmapToDir(v, outFileName, outDir):
    # v: inputMapFileName or floating values
    # cloneMapFileName: If the inputMap and cloneMap have different clones,
    #                   resampling will be done. Then,
    fullFileName = getFullPath(outFileName, outDir)
    logger.debug("Writing a pcraster map to : " + str(fullFileName))
    pcr.report(v, fullFileName)


def readPCRmapClone(
    v,
    cloneMapFileName,
    tmpDir,
    absolutePath=None,
    isLddMap=False,
    cover=None,
    isNomMap=False,
):

    iter_try = 0
    while iter_try < max_num_of_tries:
        try:
            return singleTryReadPCRmapClone(
                v, cloneMapFileName, tmpDir, absolutePath, isLddMap, cover, isNomMap
            )
            iter_try = max_num_of_tries + 100
        except Exception:
            iter_try = iter_try + 1
            logger.warning("Re-try to read file/value: " + str(v))

    if iter_try >= max_num_of_tries:
        logger.error("CANNOT READ file: " + str(v))
        return singleTryReadPCRmapClone(
            v, cloneMapFileName, tmpDir, absolutePath, isLddMap, cover, isNomMap
        )


def singleTryReadPCRmapClone(
    v,
    cloneMapFileName,
    tmpDir,
    absolutePath=None,
    isLddMap=False,
    cover=None,
    isNomMap=False,
):
    # v: inputMapFileName or floating values
    # cloneMapFileName: If the inputMap and cloneMap have different clones,
    #                   resampling will be done.
    logger.debug("read file/value: " + str(v))

    if v == "None":

        PCRmap = (
            None  # 29 July: I made an experiment by changing the type of this object.
        )

    elif not re.match(r"[0-9.-]*$", v):
        if absolutePath is not None:
            v = getFullPath(v, absolutePath)

        this_is_a_netcdf_file = False
        if v.endswith(".nc") or v.endswith(".nc4"):
            this_is_a_netcdf_file = True

        if this_is_a_netcdf_file:

            logger.debug("read netcdf file: " + str(v))

            try:
                # read netcdf file without time
                PCRmap = netcdf2PCRobjCloneWithoutTime(
                    ncFile=v, varName="automatic", cloneMapFileName=cloneMapFileName
                )
            except Exception:
                # read netcdf file with time
                PCRmap = netcdf2PCRobjClone(
                    ncFile=v,
                    varName="automatic",
                    dateInput=None,
                    useDoy=None,
                    cloneMapFileName=cloneMapFileName,
                )

        else:

            # pcraster format is assumed

            sameClone = isSameClone(v, cloneMapFileName)
            if sameClone:
                PCRmap = pcr.readmap(v)
            else:
                # resample using GDAL:
                output = tmpDir + "temp.map"
                _ = gdalwarpPCR(v, output, cloneMapFileName, tmpDir, isLddMap, isNomMap)
                # read from temporary file and delete the temporary file:
                PCRmap = pcr.readmap(output)
                if os.path.isdir(tmpDir):
                    shutil.rmtree(tmpDir)
                os.makedirs(tmpDir)
    else:
        PCRmap = pcr.spatial(pcr.scalar(float(v)))

    # make sure that values are in correct format
    if isLddMap:
        PCRmap = pcr.ifthen(pcr.scalar(PCRmap) < 10.0, PCRmap)
    if isLddMap:
        PCRmap = pcr.ifthen(pcr.scalar(PCRmap) > 0.0, PCRmap)
    if isLddMap:
        PCRmap = pcr.ldd(PCRmap)
    if isNomMap:
        PCRmap = pcr.ifthen(pcr.scalar(PCRmap) > 0.0, PCRmap)
    if isNomMap:
        PCRmap = pcr.nominal(PCRmap)

    if cover is not None:
        PCRmap = pcr.cover(PCRmap, cover)

    return PCRmap


def isSameClone(inputMapFileName, cloneMapFileName):
    # reading inputMap:
    attributeInput = getMapAttributesALL(inputMapFileName)
    cellsizeInput = attributeInput["cellsize"]
    rowsInput = attributeInput["rows"]
    colsInput = attributeInput["cols"]
    xULInput = attributeInput["xUL"]
    yULInput = attributeInput["yUL"]
    # reading cloneMap:
    attributeClone = getMapAttributesALL(cloneMapFileName)
    cellsizeClone = attributeClone["cellsize"]
    rowsClone = attributeClone["rows"]
    colsClone = attributeClone["cols"]
    xULClone = attributeClone["xUL"]
    yULClone = attributeClone["yUL"]
    # check whether both maps have the same attributes?
    sameClone = True
    if cellsizeClone != cellsizeInput:
        sameClone = False
    if rowsClone != rowsInput:
        sameClone = False
    if colsClone != colsInput:
        sameClone = False
    if xULClone != xULInput:
        sameClone = False
    if yULClone != yULInput:
        sameClone = False
    return sameClone


def gdalwarpPCR(input, output, cloneOut, tmpDir, isLddMap=False, isNominalMap=False):
    # 19 Mar 2013 created by Edwin H. Sutanudjaja
    # all input maps must be in PCRaster maps
    #
    # remove temporary files:
    co = "rm " + str(tmpDir) + "*.*"
    cOut, err = subprocess.Popen(
        co, stdout=subprocess.PIPE, stderr=open(os.devnull), shell=True
    ).communicate()
    #
    # converting files to tif:
    co = "gdal_translate -ot Float64 " + str(input) + " " + str(tmpDir) + "tmp_inp.tif"
    if isLddMap:
        co = (
            "gdal_translate -ot Int32 " + str(input) + " " + str(tmpDir) + "tmp_inp.tif"
        )
    if isNominalMap:
        co = (
            "gdal_translate -ot Int32 " + str(input) + " " + str(tmpDir) + "tmp_inp.tif"
        )
    cOut, err = subprocess.Popen(
        co, stdout=subprocess.PIPE, stderr=open(os.devnull), shell=True
    ).communicate()
    #
    # get the attributes of PCRaster map:
    cloneAtt = getMapAttributesALL(cloneOut)
    xmin = cloneAtt["xUL"]
    ymin = cloneAtt["yUL"] - cloneAtt["rows"] * cloneAtt["cellsize"]
    xmax = cloneAtt["xUL"] + cloneAtt["cols"] * cloneAtt["cellsize"]
    ymax = cloneAtt["yUL"]
    xres = cloneAtt["cellsize"]
    yres = cloneAtt["cellsize"]
    te = "-te " + str(xmin) + " " + str(ymin) + " " + str(xmax) + " " + str(ymax) + " "
    tr = "-tr " + str(xres) + " " + str(yres) + " "
    co = (
        "gdalwarp "
        + te
        + tr
        + " -srcnodata -3.4028234663852886e+38 -dstnodata mv "
        + str(tmpDir)
        + "tmp_inp.tif "
        + str(tmpDir)
        + "tmp_out.tif"
    )
    cOut, err = subprocess.Popen(
        co, stdout=subprocess.PIPE, stderr=open(os.devnull), shell=True
    ).communicate()
    #
    co = "gdal_translate -of PCRaster " + str(tmpDir) + "tmp_out.tif " + str(output)
    cOut, err = subprocess.Popen(
        co, stdout=subprocess.PIPE, stderr=open(os.devnull), shell=True
    ).communicate()
    #
    co = "mapattr -c " + str(cloneOut) + " " + str(output)
    cOut, err = subprocess.Popen(
        co, stdout=subprocess.PIPE, stderr=open(os.devnull), shell=True
    ).communicate()
    #

    #
    co = "rm " + str(tmpDir) + "tmp*.*"
    cOut, err = subprocess.Popen(
        co, stdout=subprocess.PIPE, stderr=open(os.devnull), shell=True
    ).communicate()


def getFullPath(inputPath, absolutePath, completeFileName=True):
    # 19 Mar 2013 created by Edwin H. Sutanudjaja
    # Function: to get the full absolute path of a folder or a file

    # replace all \ with /
    inputPath = str(inputPath).replace("\\", "/")
    absolutePath = str(absolutePath).replace("\\", "/")

    # tuple of suffixes (extensions) that can be used:
    suffix = (
        "/",
        "_",
        ".nc4",
        ".map",
        ".nc",
        ".dat",
        ".txt",
        ".asc",
        ".ldd",
        ".tbl",
        ".001",
        ".002",
        ".003",
        ".004",
        ".005",
        ".006",
        ".007",
        ".008",
        ".009",
        ".010",
        ".011",
        ".012",
    )

    if (
        inputPath.startswith("/")
        or str(inputPath)[1] == ":"
        or inputPath.startswith("http")
    ):
        fullPath = str(inputPath)
    else:
        if absolutePath.endswith("/"):
            absolutePath = str(absolutePath)
        else:
            absolutePath = str(absolutePath) + "/"
        fullPath = str(absolutePath) + str(inputPath)

    if completeFileName:
        if fullPath.endswith(suffix):
            fullPath = str(fullPath)
        else:
            fullPath = str(fullPath) + "/"

    return fullPath


def get_random_word(wordLen):
    word = ""
    for i in range(wordLen):
        word += random.choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        )
    return word


def isLastDayOfMonth(date):
    if (date + datetime.timedelta(days=1)).day == 1:
        return True
    else:
        return False


def getMapAttributesALL(cloneMap, arcDegree=True):
    cOut, err = subprocess.Popen(
        str("mapattr -p %s " % (cloneMap)),
        stdout=subprocess.PIPE,
        stderr=open(os.devnull),
        shell=True,
    ).communicate()

    if err is not None or cOut == []:
        print(
            "Something wrong with mattattr in virtualOS, maybe clone Map does not exist ? "
        )
        sys.exit()
    cellsize = float(cOut.split()[7])
    if arcDegree:
        cellsize = round(cellsize * 360000.0) / 360000.0
    mapAttr = {
        "cellsize": float(cellsize),
        "rows": float(cOut.split()[3]),
        "cols": float(cOut.split()[5]),
        "xUL": float(cOut.split()[17]),
        "yUL": float(cOut.split()[19]),
    }
    return mapAttr


def getMapAttributes(cloneMap, attribute, arcDegree=True):
    cOut, err = subprocess.Popen(
        str("mapattr -p %s " % (cloneMap)),
        stdout=subprocess.PIPE,
        stderr=open(os.devnull),
        shell=True,
    ).communicate()
    if err is not None or cOut == []:
        print(
            "Something wrong with mattattr in virtualOS, maybe clone Map does not exist ? "
        )
        sys.exit()
    if attribute == "cellsize":
        cellsize = float(cOut.split()[7])
        if arcDegree:
            cellsize = round(cellsize * 360000.0) / 360000.0
        return cellsize
    if attribute == "rows":
        return int(cOut.split()[3])
    if attribute == "cols":
        return int(cOut.split()[5])
    if attribute == "xUL":
        return float(cOut.split()[17])
    if attribute == "yUL":
        return float(cOut.split()[19])


def getMapTotal(mapFile):
    """outputs the sum of all values in a map file"""

    total, valid = pcr.cellvalue(pcr.maptotal(mapFile), 1)
    return total


def getMinMaxMean(mapFile, ignoreEmptyMap=False):
    mn = pcr.cellvalue(pcr.mapminimum(mapFile), 1)[0]
    mx = pcr.cellvalue(pcr.mapmaximum(mapFile), 1)[0]
    nrValues = pcr.cellvalue(pcr.maptotal(pcr.scalar(pcr.defined(mapFile))), 1)[
        0
    ]  # / getNumNonMissingValues(mapFile)
    if nrValues == 0.0 and ignoreEmptyMap:
        logger.warning("map is empty")
        return 0.0, 0.0, 0.0
    elif nrValues == 0.0 and not ignoreEmptyMap:
        logger.warning("map is empty")
        return 0.0, 0.0, 0.0
    else:
        return mn, mx, (getMapTotal(mapFile) / nrValues)


def getMapVolume(mapFile, cellareaFile):
    """returns the sum of all grid cell values"""
    volume = mapFile * cellareaFile
    return getMapTotal(volume) / 1


def secondsPerDay():
    return float(3600 * 24)


def getValDivZero(x, y, y_lim=smallNumber, z_def=0.0):
    # -returns the result of a division that possibly involves a zero
    # denominator; in which case, a default value is substituted:
    # x/y= z in case y > y_lim,
    # x/y= z_def in case y <= y_lim, where y_lim -> 0.
    # z_def is set to zero if not otherwise specified
    return pcr.ifthenelse(y > y_lim, x / pcr.max(y_lim, y), z_def)


def regridData2FinerGrid(rescaleFac, coarse, MV):
    if rescaleFac == 1:
        return coarse
    nr, nc = np.shape(coarse)

    fine = (
        np.zeros(nr * nc * rescaleFac * rescaleFac).reshape(
            nr * rescaleFac, nc * rescaleFac
        )
        + MV
    )

    ii = -1
    nrF, ncF = np.shape(fine)
    for i in range(0, nrF):
        if i % rescaleFac == 0:
            ii += 1
        fine[i, :] = coarse[ii, :].repeat(rescaleFac)

    return fine


def waterBalanceCheck(
    fluxesIn,
    fluxesOut,
    preStorages,
    endStorages,
    processName,
    PrintOnlyErrors,
    dateStr,
    threshold=1e-5,
    landmask=None,
):
    """Returns the water balance for a list of input, output, and storage map files"""
    # modified by Edwin (22 Apr 2013)

    inMap = pcr.spatial(pcr.scalar(0.0))
    outMap = pcr.spatial(pcr.scalar(0.0))
    dsMap = pcr.spatial(pcr.scalar(0.0))

    for fluxIn in fluxesIn:
        inMap += fluxIn
    for fluxOut in fluxesOut:
        outMap += fluxOut
    for preStorage in preStorages:
        dsMap += preStorage
    for endStorage in endStorages:
        dsMap -= endStorage

    a, b, c = getMinMaxMean(inMap + dsMap - outMap)
    if abs(a) > threshold or abs(b) > threshold:
        if PrintOnlyErrors:

            msg = "\n"
            msg += "\n"
            msg = "\n"
            msg += "\n"
            msg += "##############################################################################################################################################\n"
            msg += "WARNING !!!!!!!! Water Balance Error %s Min %f Max %f Mean %f" % (
                processName,
                a,
                b,
                c,
            )
            msg += "\n"
            msg += "##############################################################################################################################################\n"
            msg += "\n"
            msg += "\n"
            msg += "\n"

            logger.error(msg)


def waterBalance(
    fluxesIn,
    fluxesOut,
    deltaStorages,
    processName,
    PrintOnlyErrors,
    dateStr,
    threshold=1e-5,
):
    """Returns the water balance for a list of input, output, and storage map files and"""

    inMap = pcr.spatial(pcr.scalar(0.0))
    dsMap = pcr.spatial(pcr.scalar(0.0))
    outMap = pcr.spatial(pcr.scalar(0.0))
    inflow = 0
    outflow = 0
    deltaS = 0
    for fluxIn in fluxesIn:
        inflow += getMapTotal(fluxIn)
        inMap += fluxIn
    for fluxOut in fluxesOut:
        outflow += getMapTotal(fluxOut)
        outMap += fluxOut
    for deltaStorage in deltaStorages:
        deltaS += getMapTotal(deltaStorage)
        dsMap += deltaStorage

    a, b, c = getMinMaxMean(inMap + dsMap - outMap)
    if abs(a) > threshold or abs(b) > threshold:
        print("WBError %s Min %f Max %f Mean %f" % (processName, a, b, c))

    wb = inMap + dsMap - outMap
    _ = pcr.cellvalue(pcr.mapmaximum(pcr.abs(wb)), 1, 1)[0]

    return inMap + dsMap - outMap


def waterAbstractionAndAllocation(
    water_demand_volume,
    available_water_volume,
    allocation_zones,
    zone_area=None,
    high_volume_treshold=None,
    debug_water_balance=True,
    extra_info_for_water_balance_reporting="",
    landmask=None,
    ignore_small_values=False,
    prioritizing_local_source=True,
):

    logger.debug("Allocation of abstraction.")

    if landmask is not None:
        water_demand_volume = pcr.ifthen(landmask, pcr.cover(water_demand_volume, 0.0))
        available_water_volume = pcr.ifthen(
            landmask, pcr.cover(available_water_volume, 0.0)
        )
        allocation_zones = pcr.ifthen(landmask, allocation_zones)

    # satistify demand with local sources:
    localAllocation = pcr.scalar(0.0)
    localAbstraction = pcr.scalar(0.0)
    cellVolDemand = pcr.max(0.0, water_demand_volume)
    cellAvlWater = pcr.max(0.0, available_water_volume)
    if prioritizing_local_source:
        logger.debug(
            "Allocation of abstraction - first, satisfy demand with local source."
        )

        # demand volume in each cell (unit: m3)
        if landmask is not None:
            cellVolDemand = pcr.ifthen(landmask, pcr.cover(cellVolDemand, 0.0))

        # total available water volume in each cell
        if landmask is not None:
            cellAvlWater = pcr.ifthen(landmask, pcr.cover(cellAvlWater, 0.0))

        # first, satisfy demand with local source
        localAllocation = pcr.max(0.0, pcr.min(cellVolDemand, cellAvlWater))
        localAbstraction = localAllocation * 1.0

    logger.debug("Allocation of abstraction - satisfy demand with neighbour sources.")

    # the remaining demand and available water
    cellVolDemand = pcr.max(0.0, cellVolDemand - localAllocation)
    cellAvlWater = pcr.max(0.0, cellAvlWater - localAbstraction)

    # ignoring small values of water availability
    if ignore_small_values:
        available_water_volume = pcr.max(0.0, pcr.rounddown(available_water_volume))

    # demand volume in each cell (unit: m3)
    cellVolDemand = pcr.max(0.0, cellVolDemand)
    if landmask is not None:
        cellVolDemand = pcr.ifthen(landmask, pcr.cover(cellVolDemand, 0.0))

    # total demand volume in each zone/segment (unit: m3)
    zoneVolDemand = pcr.areatotal(cellVolDemand, allocation_zones)

    # avoid very high values of available water
    cellAvlWater = pcr.min(cellAvlWater, zoneVolDemand)

    # total available water volume in each cell
    cellAvlWater = pcr.max(0.0, cellAvlWater)
    if landmask is not None:
        cellAvlWater = pcr.ifthen(landmask, pcr.cover(cellAvlWater, 0.0))

    # total available water volume in each zone/segment (unit: m3)
    zoneAvlWater = pcr.areatotal(cellAvlWater, allocation_zones)

    # total actual water abstraction volume in each zone/segment (unit: m3)
    # - limited to available water
    zoneAbstraction = pcr.min(zoneAvlWater, zoneVolDemand)

    # actual water abstraction volume in each cell (unit: m3)
    cellAbstraction = (
        getValDivZero(cellAvlWater, zoneAvlWater, smallNumber) * zoneAbstraction
    )
    cellAbstraction = pcr.min(cellAbstraction, cellAvlWater)

    # to minimize numerical errors
    if high_volume_treshold is not None:
        # mask: 0 for small volumes ; 1 for large volumes (e.g. lakes and reservoirs)
        mask = pcr.cover(
            pcr.ifthen(cellAbstraction > high_volume_treshold, pcr.boolean(1)),
            pcr.boolean(0),
        )
        zoneAbstraction = pcr.areatotal(
            pcr.ifthenelse(mask, 0.0, cellAbstraction), allocation_zones
        )
        zoneAbstraction += pcr.areatotal(
            pcr.ifthenelse(mask, cellAbstraction, 0.0), allocation_zones
        )

    # allocation water to meet water demand (unit: m3)
    cellAllocation = (
        getValDivZero(cellVolDemand, zoneVolDemand, smallNumber) * zoneAbstraction
    )
    cellAllocation = pcr.min(cellAllocation, cellVolDemand)

    # adding local abstraction and local allocation
    cellAbstraction = cellAbstraction + localAbstraction
    cellAllocation = cellAllocation + localAllocation

    if debug_water_balance and zone_area is not None:

        waterBalanceCheck(
            [
                pcr.cover(
                    pcr.areatotal(cellAbstraction, allocation_zones) / zone_area, 0.0
                )
            ],
            [
                pcr.cover(
                    pcr.areatotal(cellAllocation, allocation_zones) / zone_area, 0.0
                )
            ],
            [pcr.scalar(0.0)],
            [pcr.scalar(0.0)],
            "abstraction - allocation per zone/segment (PS: Error here may be caused by rounding error.)",
            True,
            extra_info_for_water_balance_reporting,
            threshold=1e-4,
        )

    return cellAbstraction, cellAllocation


def findLastYearInNCTime(ncTimeVariable):

    # last datetime
    last_datetime = nc.num2date(
        ncTimeVariable[len(ncTimeVariable) - 1],
        ncTimeVariable.units,
        ncTimeVariable.calendar,
    )

    return last_datetime.year


def findFirstYearInNCTime(ncTimeVariable):

    # first datetime
    first_datetime = nc.num2date(
        ncTimeVariable[0], ncTimeVariable.units, ncTimeVariable.calendar
    )

    return first_datetime.year


def cmd_line(command_line, using_subprocess=True):

    msg = "Call: " + str(command_line)
    logger.debug(msg)

    co = command_line
    if using_subprocess:
        cOut, err = subprocess.Popen(
            co, stdout=subprocess.PIPE, stderr=open("/dev/null"), shell=True
        ).communicate()
    else:
        os.system(co)


def deg2rad(a):

    return a * pi / 180.0


def rad2deg(a):

    return a * 180.0 / pi
