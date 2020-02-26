#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import time
import re
import subprocess
import netCDF4 as nc
import numpy as np
import pcraster as pcr
import virtualOS as vos

class OutputNetcdf():
    
    def __init__(self, inputMapFileName,\
                       netcdf_format = "NETCDF3_CLASSIC",\
                       netcdf_zlib = False,\
                       netcdf_attribute_dict = None,\
                       netcdf_attribute_description = None, \
                       netcdf_y_orientation_from_top_bottom = True,
                       ):
        		
        # netcdf format and zlib setup
        self.format = netcdf_format
        self.zlib   = netcdf_zlib 

        # netcdf latitude orientation
        self.netcdf_y_orientation_from_top_bottom = netcdf_y_orientation_from_top_bottom

        # longitudes and latitudes
        self.longitudes, self.latitudes, self.cellSizeInArcMin = self.set_latlon_based_on_cloneMapFileName(inputMapFileName, \
                                                                                                           self.netcdf_y_orientation_from_top_bottom)
        # necdf global attributes
        self.attributeDictionary = {}
        if netcdf_attribute_description == None:
            # default netCDF attributes
            self.attributeDictionary['institution'] = ""
            self.attributeDictionary['title'      ] = os.path.basename(inputMapFileName)
            self.attributeDictionary['source'     ] = inputMapFileName
            self.attributeDictionary['references' ] = inputMapFileName
            self.attributeDictionary['history'    ] = ""
            self.attributeDictionary['comment'    ] = "" 
        else:
            # using a specific defined set of netCDF attributes
            self.attributeDictionary['institution'] = netcdf_attribute_dict['institution']
            self.attributeDictionary['title'      ] = netcdf_attribute_dict['title'      ]
            self.attributeDictionary['source'     ] = netcdf_attribute_dict['source'     ]
            self.attributeDictionary['references' ] = netcdf_attribute_dict['references' ]
            self.attributeDictionary['history'    ] = netcdf_attribute_dict['history'    ]
            self.attributeDictionary['comment'    ] = netcdf_attribute_dict['comment'    ]
            self.attributeDictionary['description'] = netcdf_attribute_dict['description']
        
        # add a history
        current_time = str(datetime.datetime.now())
        self.attributeDictionary['history']  = "This netcdf file was converted from a pcraster file " + inputMapFileName + " on " + current_time + "."

        # extra netcdf attribute ('description')
        if netcdf_attribute_description != None: self.attributeDictionary['description']  = netcdf_attribute_description

        
    def set_latlon_based_on_cloneMapFileName(self, cloneMapFileName, netcdf_y_orientation_from_top_bottom = True):

        # cloneMap
        cloneMap = pcr.boolean(pcr.readmap(cloneMapFileName))
        cloneMap = pcr.boolean(pcr.scalar(1.0))
        
        # properties of the clone maps
        # - numbers of rows and colums
        rows = pcr.clone().nrRows() 
        cols = pcr.clone().nrCols()
        # - cell size in arc minutes rounded to one value behind the decimal
        cellSizeInArcMin = round(pcr.clone().cellSize() * 60.0, 1) 
        # - cell sizes in ar degrees for longitude and langitude direction 
        deltaLon = cellSizeInArcMin / 60.
        deltaLat = deltaLon
        # - coordinates of the upper left corner - rounded to two values behind the decimal in order to avoid rounding errors during (future) resampling process
        x_min = round(pcr.clone().west(), 2)
        y_max = round(pcr.clone().north(), 2)
        # - coordinates of the lower right corner - rounded to two values behind the decimal in order to avoid rounding errors during (future) resampling process
        x_max = round(x_min + cols*deltaLon, 2) 
        y_min = round(y_max - rows*deltaLat, 2) 
        
        # cell centres coordinates
        longitudes = np.arange(x_min + deltaLon/2., x_max, deltaLon)
        latitudes  = np.arange(y_max - deltaLat/2., y_min,-deltaLat)

        if netcdf_y_orientation_from_top_bottom == False:
            latitudes  = latitudes[::-1]
            
        return longitudes, latitudes, cellSizeInArcMin  


    def createNetCDF(self, ncFileName, varName, varUnits, date, longName = None):

        rootgrp = nc.Dataset(ncFileName,'w',format= self.format)

        # if required, create time dimension - time is unlimited (others are fixed)
        if date != None:
           rootgrp.createDimension('time', None)

        # create lat and lon dimensions
        rootgrp.createDimension('lat', len(self.latitudes))
        rootgrp.createDimension('lon', len(self.longitudes))
        
        if date != None:
            date_time = rootgrp.createVariable('time','f4',('time',))
            date_time.standard_name = 'time'
            date_time.long_name = 'Days since 1901-01-01'
            date_time.units = 'Days since 1901-01-01' 
            date_time.calendar = 'standard'

        lat = rootgrp.createVariable('lat','f4',('lat',))
        lat.long_name = 'latitude'
        lat.units = 'degrees_north'
        lat.standard_name = 'latitude'

        lon = rootgrp.createVariable('lon','f4',('lon',))
        lon.standard_name = 'longitude'
        lon.long_name = 'longitude'
        lon.units = 'degrees_east'

        lat[:] = self.latitudes
        lon[:] = self.longitudes

        shortVarName = varName
        longVarName  = varName
        if longName != None: longVarName = longName

        # create variable
        if date != None:
            var = rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',),fill_value = vos.MV, zlib = self.zlib)
        else:
            var = rootgrp.createVariable(shortVarName,'f4',('lat','lon',),fill_value = vos.MV, zlib = self.zlib)
        
        var.standard_name = varName
        var.long_name = longVarName
        var.units = varUnits

        attributeDictionary = self.attributeDictionary
        for k, v in attributeDictionary.items(): setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def data2NetCDF(self, ncFileName, shortVarName, varField, timeStamp, posCnt = None):

        rootgrp = nc.Dataset(ncFileName,'a')
        
        # flip variable if necessary
        if self.netcdf_y_orientation_from_top_bottom == False: varField = np.flipud(varField)

        if timeStamp != None:
            date_time = rootgrp.variables['time']
            if posCnt == None: posCnt = len(date_time)
            date_time[posCnt] = nc.date2num(timeStamp,date_time.units,date_time.calendar)
            rootgrp.variables[shortVarName][posCnt,:,:] = varField
        else:
            rootgrp.variables[shortVarName][:,:] = varField
        
        rootgrp.sync()
        rootgrp.close()


