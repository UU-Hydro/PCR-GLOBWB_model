from __future__ import print_function

import calendar
import datetime
import glob
import os
import sys
import time as tm
from multiprocessing import Pool

import netCDF4 as nc
import numpy as np
from dateutil.relativedelta import *

# file cache to reduce opening and closing files
filecache = dict()


def calculate_monthdelta(date1, date2):
    def is_last_day_of_the_month(date):
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        return date.day == days_in_month

    imaginary_day_2 = 31 if is_last_day_of_the_month(date2) else date2.day
    monthdelta = (
        (date2.month - date1.month)
        + (date2.year - date1.year) * 12
        + (-1 if date1.day > imaginary_day_2 else 0)
    )
    return monthdelta


def calculate_weekdelta(start, end):
    # always start 7 Jan
    start = datetime.datetime(start.year, 1, 7)
    # force the end to 31 December of the last year
    end = datetime.datetime(end.year, 12, 31)
    # always 53 weeks/year
    return ((end - start).days // 7) + 1


def getMax(x, a):
    m = float(a.max())
    if x == None:
        return m
    else:
        return max(m, x)


def getMin(x, a):
    m = float(a.min())
    if x == None:
        return m
    else:
        return min(m, x)


def netcdfList(inputDir):
    """creates a dictionary of netcdf files"""
    netcdfList = glob.glob(os.path.join(inputDir, "*.nc"))
    print(inputDir)
    print(os.path.join(inputDir, "*.nc"))
    ll = []
    for ncFile in netcdfList:
        ll.append(ncFile.split("/")[-1])
    return ll


def ncFileNameDict(inputDirRoot, areas, ncFileName, fileType):
    """creates a dictionary of subdomains of pcrglob model outut"""
    netcdfInputDict = {}
    folder = "states" if fileType == "outStates" else "netcdf"
    for key in range(1, len(areas) + 1, 1):
        value = os.path.join(inputDirRoot, areas[key - 1], folder, ncFileName)
        netcdfInputDict[key] = value
    return netcdfInputDict


def mergeNetCDF(inputTuple):

    ncName = inputTuple[0]
    latMin = inputTuple[1]
    latMax = inputTuple[2]
    lonMin = inputTuple[3]
    lonMax = inputTuple[4]
    deltaLat = inputTuple[5]
    deltaLon = inputTuple[6]

    startDate = inputTuple[7]
    endDate = inputTuple[8]

    print("combining files for %s" % ncName)
    scriptStartTime = tm.time()

    # whether the files are outputs or states
    fileType = inputTuple[12]

    netCDFInput = ncFileNameDict(inputDirRoot, areas, ncName, fileType)

    # netCDF output file name
    netCDFOutput = (
        outputDir
        + "/"
        + ncName.split(".")[0]
        + "_"
        + startDate
        + "_to_"
        + endDate
        + ".nc"
    )
    print(netCDFOutput)

    ncFormat = inputTuple[9]

    # option to use zlib compression
    using_zlib = inputTuple[10]
    if using_zlib == "True":
        using_zlib = True

    # set dimensions and attributes per netCDF input data set, and retrieve the
    # resolution and definition of the coordinates and calendar
    attributes = {}
    dimensions = {}
    variables = {}
    variableName = None

    calendar_used = {}
    uniqueTimes = np.array([])

    # define the time from the given arguments
    if startDate != None and endDate != None:
        sd = str(startDate).split("-")
        startTime = datetime.datetime(int(sd[0]), int(sd[1]), int(sd[2]), 0)
        ed = str(endDate).split("-")
        endTime = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 0)

        print(list(netCDFInput.values())[0])

        # open the first netCDF file to get the time units and calendar
        ncFile = list(netCDFInput.values())[0]
        print(ncFile)
        f = nc.Dataset(ncFile)
        time_units = f.variables["time"].units
        time_calendar = f.variables["time"].calendar

        timeStepType = "daily"
        if len(f.variables["time"]) > 1:
            if (f.variables["time"][1] - f.variables["time"][0]) > 5.0:
                timeStepType = "weekly"
            if (f.variables["time"][1] - f.variables["time"][0]) > 25.0:
                timeStepType = "monthly"
            if (f.variables["time"][1] - f.variables["time"][0]) > 305.0:
                timeStepType = "yearly"
        else:
            timeStepType = "single"

        f.close()

        if timeStepType == "daily":
            number_of_days = (endTime - startTime).days + 1
            datetime_range = [
                startTime + datetime.timedelta(days=x) for x in range(0, number_of_days)
            ]

        if timeStepType == "weekly":
            datetime_range = []
            for year in range(startTime.year, endTime.year + 1):
                current = datetime.datetime(year, 1, 7)
                end_of_year = datetime.datetime(year, 12, 31)
                while current <= end_of_year:
                    datetime_range.append(current)
                    current += datetime.timedelta(weeks=1)
                if datetime_range[-1] != end_of_year:
                    datetime_range.append(end_of_year)

        if timeStepType == "monthly":
            number_of_months = calculate_monthdelta(startTime, endTime) + 1
            datetime_range = [
                startTime + relativedelta(months=+x) for x in range(0, number_of_months)
            ]
            # make sure the dates are at the last day of the month
            for i in range(0, len(datetime_range)):
                year_used = datetime_range[i].year
                month_used = datetime_range[i].month
                day_used = calendar.monthrange(year_used, month_used)[1]
                if file_type != "outStates":
                    datetime_range[i] = datetime.datetime(
                        int(year_used), int(month_used), int(day_used), 0
                    )
                else:
                    datetime_range[i] = datetime.datetime(
                        int(year_used), int(month_used), int(1), 0
                    )

        if timeStepType == "yearly":
            number_of_years = endTime.year - startTime.year + 1
            datetime_range = [
                startTime + relativedelta(years=+x) for x in range(0, number_of_years)
            ]
            # make sure the dates are at the last day of the year
            for i in range(0, len(datetime_range)):
                year_used = datetime_range[i].year
                month_used = 12
                day_used = 31
                datetime_range[i] = datetime.datetime(
                    int(year_used), int(month_used), int(day_used), 0
                )

        if timeStepType == "single":
            datetime_range = [startTime]

        # numerical time values
        uniqueTimes = nc.date2num(datetime_range, time_units, time_calendar)

        print(timeStepType)
        print(datetime_range)
        print(uniqueTimes)

    for ncFile in list(netCDFInput.values()):
        if ncFile in list(filecache.keys()):
            rootgrp = filecache[ncFile]
            print("Cached: ", ncFile)
        else:
            rootgrp = nc.Dataset(ncFile)
            filecache[ncFile] = rootgrp
            print("New: ", ncFile)

        index = list(netCDFInput.keys())[list(netCDFInput.values()).index(ncFile)]

        # retrieve dimensions, attributes, variables and missing value
        dimensions[index] = rootgrp.dimensions.copy()
        variables[index] = rootgrp.variables.copy()
        attributes[index] = rootgrp.__dict__.copy()

        for key in list(dimensions[index].keys()):
            if "lat" in key.lower():
                latVar = key
            if "lon" in key.lower():
                lonVar = key
        latMin = getMin(latMin, variables[index][latVar][:])
        latMax = getMax(latMax, variables[index][latVar][:])
        lonMin = getMin(lonMin, variables[index][lonVar][:])
        lonMax = getMax(lonMax, variables[index][lonVar][:])

        if "time" in list(variables[index].keys()):
            for name in variables[index]["time"].ncattrs():
                if name not in list(calendar_used.keys()):
                    calendar_used[name] = getattr(variables[index]["time"], name)
                else:
                    if getattr(variables[index]["time"], name) != calendar_used[name]:
                        rootgrp.close()
                        sys.exit("calendars are incompatible")
            if uniqueTimes.size == 0:
                uniqueTimes = variables[index]["time"][:]
            uniqueTimes.sort()
        keys = list(variables[index].keys())
        for key in list(dimensions[index].keys()):
            if key in keys:
                keys.remove(key)
        key = keys[0]
        if variableName == None:
            variableName = key
        else:
            if key != variableName:
                rootgrp.close()
                sys.exit("variables are incompatible")
        using_MV = inputTuple[11]
        if using_MV == "True":
            using_MV = True
        if using_MV == True:
            MV = -999.9000244140625
        else:
            MV = rootgrp.variables[key]._FillValue
        varUnits = rootgrp.variables[variableName].units
        rootgrp.close()

    longitudes = np.around(np.arange(lonMin, lonMax + deltaLon, deltaLon), decimals=3)
    latitudes = np.around(np.arange(latMax, latMin - deltaLat, -deltaLat), decimals=3)
    uniqueTimes = uniqueTimes.tolist()

    rootgrp = nc.Dataset(netCDFOutput, "w", format=ncFormat)

    date_time = rootgrp.createDimension("time", len(uniqueTimes))
    date_time = rootgrp.createVariable("time", "f8", ("time",))

    for attr, value in list(calendar_used.items()):
        if attr != "_FillValue":
            setattr(date_time, attr, str(value))
    date_time[:] = uniqueTimes

    rootgrp.createDimension("latitude", len(latitudes))
    rootgrp.createDimension("longitude", len(longitudes))
    lat = rootgrp.createVariable("latitude", "f4", ("latitude"))
    lat.standard_name = "Latitude"
    lat.long_name = "Latitude cell centres"
    lon = rootgrp.createVariable("longitude", "f4", ("longitude"))
    lon.standard_name = "Longitude"
    lon.long_name = "Longitude cell centres"

    lat[:] = latitudes
    lon[:] = longitudes

    # TODO: improve this; needed for selecting rows and columns
    latitudes = np.around(latitudes, decimals=3)
    # TODO: improve this; needed for selecting rows and columns
    longitudes = np.around(longitudes, decimals=3)

    if len(calendar_used) == 0:
        varStructure = ("latitude", "longitude")
    else:
        varStructure = ("time", "latitude", "longitude")
    variable = rootgrp.createVariable(
        variableName, "f4", varStructure, fill_value=MV, zlib=using_zlib
    )

    for index in list(attributes.keys()):
        for name in variables[index][variableName].ncattrs():
            try:
                setattr(
                    variable, name, str(getattr(variables[index][variableName], name))
                )
            except:
                pass
        for attr, value in list(attributes[index].items()):
            setattr(rootgrp, attr, str(value))

    rootgrp.sync()
    rootgrp.close()

    # note: this assumes a timed variable
    # iterate over the time steps and retrieve the values

    print(
        "nr of time steps = %s, nr of files = %s "
        % (len(uniqueTimes), len(netCDFInput))
    )
    i_time = 0
    for time in uniqueTimes[:]:
        i_time = i_time + 1
        print("processing %s %i from %i" % (ncName, i_time, len(uniqueTimes)))

        variableArray = np.ones((len(latitudes), len(longitudes))) * MV

        for ncFile in list(netCDFInput.values()):
            rootgrp = nc.Dataset(ncFile, "r", format=ncFormat)
            index = list(netCDFInput.keys())[list(netCDFInput.values()).index(ncFile)]
            # get the row and column indices from the latitudes and longitudes
            for key in list(dimensions[index].keys()):
                if "lat" in key.lower():
                    latVar = key
                if "lon" in key.lower():
                    lonVar = key
            latMaxNcFile = round(getMax(latMin, variables[index][latVar][:]), 3)
            latMinNcFile = round(getMin(latMax, variables[index][latVar][:]), 3)
            lonMinNcFile = round(getMin(lonMax, variables[index][lonVar][:]), 3)
            lonMaxNcFile = round(getMax(lonMin, variables[index][lonVar][:]), 3)

            row0 = int(np.where(latitudes == min(latMax, latMaxNcFile))[0][0])
            row1 = int(np.where(latitudes == max(latMin, latMinNcFile))[0][0] + 1)
            col0 = int(np.where(longitudes == max(lonMin, lonMinNcFile))[0][0])
            col1 = int(np.where(longitudes == min(lonMax, lonMaxNcFile))[0][0] + 1)

            posCnt = None

            try:
                # find the correct time index
                date_value = nc.num2date(
                    time,
                    rootgrp.variables["time"].units,
                    rootgrp.variables["time"].calendar,
                )
                posCnt = nc.date2index(date_value, rootgrp.variables["time"])

                print(date_value)
                print(posCnt)

                sampleArray = rootgrp.variables[variableName][posCnt, :, :]

                print(sampleArray)

                sampleArray[
                    sampleArray == variables[index][variableName]._FillValue
                ] = MV
                variableArray[row0:row1, col0:col1][
                    variableArray[row0:row1, col0:col1] == MV
                ] = sampleArray[variableArray[row0:row1, col0:col1] == MV]

                print("time is present :" + str(date_value))

            except:
                if posCnt == None:
                    print("time not present")
                else:
                    print("error  in resampled")
            rootgrp.close()

        posCnt = uniqueTimes.index(time)
        rootgrp = nc.Dataset(netCDFOutput, "a", format=ncFormat)
        rootgrp.variables[variableName][posCnt, :, :] = variableArray
        variable.units = str(varUnits)
        rootgrp.sync()
        rootgrp.close()

    secs = int(tm.time() - scriptStartTime)
    print(
        "Processing %s took %s hh:mm:ss\n"
        % (ncName, str(datetime.timedelta(seconds=secs)))
    )


# latitudes and longitudes (5 arcmin)
deltaLat = 5.0 / 60.0
deltaLon = 5.0 / 60.0

latMin = -90 + deltaLat / 2
latMax = 90 - deltaLat / 2
lonMin = -180 + deltaLon / 2
lonMax = 180 - deltaLon / 2

inputDirRoot = sys.argv[1]

outputDir = sys.argv[2]

try:
    os.makedirs(outputDir)
except:
    pass

# file_type: outDailyTot, outMonthTot, outMonthAvg, outMonthEnd, outAnnuaTot, outAnnuaAvg or outAnnuaEnd
file_type = str(sys.argv[3])

startDate = str(sys.argv[4])
endDate = str(sys.argv[5])

# netCDF files to merge
netcdfList = str(sys.argv[6])
print(netcdfList)
netcdfList = list(set(netcdfList.split(",")))
if file_type == "outDailyTotNC":
    netcdfList = ["%s_dailyTot_output.nc" % var for var in netcdfList]
if file_type == "outWeekTotNC":
    netcdfList = ["%s_weekTot_output.nc" % var for var in netcdfList]
if file_type == "outWeekAvgNC":
    netcdfList = ["%s_weekAvg_output.nc" % var for var in netcdfList]
if file_type == "outMonthTotNC":
    netcdfList = ["%s_monthTot_output.nc" % var for var in netcdfList]
if file_type == "outMonthAvgNC":
    netcdfList = ["%s_monthAvg_output.nc" % var for var in netcdfList]
if file_type == "outMonthEndNC":
    netcdfList = ["%s_monthEnd_output.nc" % var for var in netcdfList]
if file_type == "outAnnuaTotNC":
    netcdfList = ["%s_annuaTot_output.nc" % var for var in netcdfList]
if file_type == "outAnnuaAvgNC":
    netcdfList = ["%s_annuaAvg_output.nc" % var for var in netcdfList]
if file_type == "outAnnuaEndNC":
    netcdfList = ["%s_annuaEnd_output.nc" % var for var in netcdfList]
if file_type == "outMonthMaxNC":
    netcdfList = ["%s_monthMax_output.nc" % var for var in netcdfList]
if file_type == "outAnnuaMaxNC":
    netcdfList = ["%s_annuaMax_output.nc" % var for var in netcdfList]

if file_type == "out_month_totNC":
    netcdfList = ["%s_monthly_tot.nc" % var for var in netcdfList]
if file_type == "out_month_avgNC":
    netcdfList = ["%s_monthly_avg.nc" % var for var in netcdfList]
if file_type == "outStates":
    netcdfList = ["%s.nc" % var for var in netcdfList]

# netCDF format and zlib option
ncFormat = str(sys.argv[7])
using_zlib = str(sys.argv[8])

# maximum number of cores to use
max_number_of_cores = int(sys.argv[9])

ncores = min(len(netcdfList), max_number_of_cores)

number_of_clones = int(sys.argv[10])
areas = ["M%02d" % i for i in range(1, number_of_clones + 1, 1)]

if sys.argv[11] == "all_lats":
    latMin = -90 + deltaLat / 2
    latMax = 90 - deltaLat / 2

# clone map defined by the command-line arguments
if sys.argv[11] == "defined":
    cellsize_in_arcsec = float(sys.argv[12])
    xmin = float(sys.argv[13])
    ymin = float(sys.argv[14])
    xmax = float(sys.argv[15])
    ymax = float(sys.argv[16])
    lonMin = xmin + float(sys.argv[12]) / (2.0 * 3600.0)
    latMin = ymin + float(sys.argv[12]) / (2.0 * 3600.0)
    lonMax = xmax - float(sys.argv[12]) / (2.0 * 3600.0)
    latMax = ymax - float(sys.argv[12]) / (2.0 * 3600.0)

using_MV = str(sys.argv[12])


ll = []
for ncName in netcdfList:
    ll.append(
        (
            ncName,
            latMin,
            latMax,
            lonMin,
            lonMax,
            deltaLat,
            deltaLon,
            startDate,
            endDate,
            ncFormat,
            using_zlib,
            using_MV,
            file_type,
        )
    )
# start ncores worker processes
pool = Pool(processes=ncores)
pool.map(mergeNetCDF, ll)

pool.terminate()
pool.join()

sys.exit()
