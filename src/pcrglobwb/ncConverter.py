from __future__ import print_function

import datetime

import netCDF4 as nc
import numpy as np
import pcraster as pcr

from pcrglobwb.common import virtualOS as vos

# TODO: use a file cache (e.g. filecache = dict()) to avoid opening and closing files


class PCR2netCDF:

    def __init__(self, iniItems, specificAttributeDictionary=None):

        pcr.setclone(iniItems.cloneMap)
        cloneMap = pcr.boolean(1.0)

        # latitudes and longitudes
        self.latitudes = np.unique(pcr.pcr2numpy(pcr.ycoordinate(cloneMap), vos.MV))[
            ::-1
        ]
        self.longitudes = np.unique(pcr.pcr2numpy(pcr.xcoordinate(cloneMap), vos.MV))

        # let users decide the latitude order
        self.netcdf_y_orientation_follow_cf_convention = False
        if (
            "netcdf_y_orientation_follow_cf_convention"
            in list(iniItems.reportingOptions.keys())
            and iniItems.reportingOptions["netcdf_y_orientation_follow_cf_convention"]
            == "True"
        ):
            msg = "Latitude (y) orientation for output netcdf files start from the bottom to top."
            self.netcdf_y_orientation_follow_cf_convention = True
            self.latitudes = np.unique(pcr.pcr2numpy(pcr.ycoordinate(cloneMap), vos.MV))

        # general netCDF attributes from the ini file
        self.set_general_netcdf_attributes(iniItems, specificAttributeDictionary)

        self.format = "NETCDF3_CLASSIC"
        self.zlib = False
        if "formatNetCDF" in list(iniItems.reportingOptions.keys()):
            self.format = str(iniItems.reportingOptions["formatNetCDF"])
        if "zlib" in list(iniItems.reportingOptions.keys()):
            if iniItems.reportingOptions["zlib"] == "True":
                self.zlib = True

        # use the attributes given in the ini section 'specific_attributes_for_netcdf_output_files'
        if "specific_attributes_for_netcdf_output_files" in iniItems.allSections:
            for key in list(
                iniItems.specific_attributes_for_netcdf_output_files.keys()
            ):

                self.attributeDictionary[key] = (
                    iniItems.specific_attributes_for_netcdf_output_files[key]
                )

                if self.attributeDictionary[key] == "None":
                    self.attributeDictionary[key] = ""

                if key == "history" and self.attributeDictionary[key] == "Default":
                    self.attributeDictionary[key] = (
                        "created on " + datetime.datetime.today().isoformat(" ")
                    )
                if self.attributeDictionary[key] == "Default" and (
                    key == "date_created" or key == "date_issued"
                ):
                    self.attributeDictionary[key] = datetime.datetime.today().isoformat(
                        " "
                    )

    def set_general_netcdf_attributes(self, iniItems, specificAttributeDictionary=None):

        # netCDF attributes from the configuration file or specificAttributeDictionary
        self.attributeDictionary = {}
        if specificAttributeDictionary == None:
            self.attributeDictionary["institution"] = iniItems.globalOptions[
                "institution"
            ]
            self.attributeDictionary["title"] = iniItems.globalOptions["title"]
            self.attributeDictionary["description"] = iniItems.globalOptions[
                "description"
            ]
        else:
            for ncAttributeKey, ncAttribute in list(
                specificAttributeDictionary.items()
            ):
                print(ncAttributeKey, ncAttribute)
                self.attributeDictionary[ncAttributeKey] = ncAttribute

    def createNetCDF(
        self, ncFileName, varName, varUnits, longName=None, standardName=None
    ):

        rootgrp = nc.Dataset(ncFileName, "w", format=self.format)

        # time is unlimited, other dimensions are fixed
        rootgrp.createDimension("time", None)
        rootgrp.createDimension("lat", len(self.latitudes))
        rootgrp.createDimension("lon", len(self.longitudes))

        date_time = rootgrp.createVariable("time", "f4", ("time",))
        date_time.standard_name = "time"
        date_time.long_name = "Days since 1901-01-01"

        # fixed reference date for Ulysses
        date_time.units = "days since 1901-01-01"

        date_time.calendar = "standard"

        lat = rootgrp.createVariable("lat", "f4", ("lat",))
        lat.long_name = "latitude"
        lat.units = "degrees_north"
        lat.standard_name = "latitude"

        lon = rootgrp.createVariable("lon", "f4", ("lon",))
        lon.standard_name = "longitude"
        lon.long_name = "longitude"
        lon.units = "degrees_east"

        lat[:] = self.latitudes
        lon[:] = self.longitudes

        shortVarName = varName
        longVarName = varName
        standardVarName = varName
        if longName != None:
            longVarName = longName
        if standardName != None:
            standardVarName = standardName

        var = rootgrp.createVariable(
            shortVarName,
            "f4",
            (
                "time",
                "lat",
                "lon",
            ),
            fill_value=vos.MV,
            zlib=self.zlib,
        )
        var.standard_name = standardVarName
        var.long_name = longVarName
        var.units = varUnits

        attributeDictionary = self.attributeDictionary
        for k, v in list(attributeDictionary.items()):
            setattr(rootgrp, k, v)

        rootgrp.sync()
        rootgrp.close()

    def data2NetCDF(self, ncFileName, shortVarName, varField, timeStamp, posCnt=None):

        rootgrp = nc.Dataset(ncFileName, "a")

        date_time = rootgrp.variables["time"]
        if posCnt == None:
            posCnt = len(date_time)
        date_time[posCnt] = nc.date2num(timeStamp, date_time.units, date_time.calendar)

        # flip variable if necessary (to follow the CF convention)
        if self.netcdf_y_orientation_follow_cf_convention:
            varField = np.flipud(varField)

        rootgrp.variables[shortVarName][posCnt, :, :] = varField

        rootgrp.sync()
        rootgrp.close()

    def close(self, ncFileName):

        rootgrp = nc.Dataset(ncFileName, "w")

        rootgrp.close()
