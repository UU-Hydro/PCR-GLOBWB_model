#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import time
import re
import glob
import subprocess
import netCDF4 as nc
import numpy as np
import pcraster as pcr
import virtualOS as vos

# the following dictionary is needed to avoid open and closing files
filecache = dict()


class PCR2netCDF():
    
    def __init__(self,iniItems):
        		
        # cloneMap
        pcr.setclone(iniItems.cloneMap)
        cloneMap = pcr.boolean(1.0)
        
        # latitudes and longitudes
        self.latitudes  = np.unique(pcr2numpy(pcr.ycoordinate(cloneMap), vos.MV))[::-1]
        self.longitudes = np.unique(pcr2numpy(pcr.xcoordinate(cloneMap), vos.MV))
        
        # TODO: Let users decide what their preference regarding latitude order. 
        #       Consult with Stefanie regarding CF convention. 
        
        # set the general netcdf attributes (based on the information given in the ini/configuration file) 
        self.set_general_netcdf_attributes(iniItems)
        
        # netcdf format and zlib setup 
        self.format = 'NETCDF3_CLASSIC'
        self.zlib = False
        if "formatNetCDF" in iniItems.reportingOptions.keys():
            self.format = str(iniItems.reportingOptions['formatNetCDF'])
        if "zlib" in iniItems.reportingOptions.keys():
            if iniItems.reportingOptions['zlib'] == "True": self.zlib = True 
            
    def set_general_netcdf_attributes(self,iniItems):

        # netCDF attributes:
        self.attributeDictionary = {}
        self.attributeDictionary['institution'] = iniItems.globalOptions['institution']
        self.attributeDictionary['title'      ] = iniItems.globalOptions['title'      ]
        self.attributeDictionary['description'] = iniItems.globalOptions['description']


    def createNetCDF(self, ncFileName, varName, varUnits, longName = None):

        rootgrp = nc.Dataset(ncFileName,'w',format= self.format)

        #-create dimensions - time is unlimited, others are fixed
        rootgrp.createDimension('time',None)
        rootgrp.createDimension('lat',len(self.latitudes))
        rootgrp.createDimension('lon',len(self.longitudes))

        date_time = rootgrp.createVariable('time','f4',('time',))
        date_time.standard_name = 'time'
        date_time.long_name = 'Days since 1901-01-01'

        date_time.units = 'Days since 1901-01-01' 
        date_time.calendar = 'standard'

        lat= rootgrp.createVariable('lat','f4',('lat',))
        lat.long_name = 'latitude'
        lat.units = 'degrees_north'
        lat.standard_name = 'latitude'

        lon= rootgrp.createVariable('lon','f4',('lon',))
        lon.standard_name = 'longitude'
        lon.long_name = 'longitude'
        lon.units = 'degrees_east'

        lat[:]= self.latitudes
        lon[:]= self.longitudes

        shortVarName = varName
        longVarName  = varName
        if longName != None: longVarName = longName

        var = rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',) ,fill_value=vos.MV,zlib=self.zlib)
        var.standard_name = varName
        var.long_name = longVarName
        var.units = varUnits

        attributeDictionary = self.attributeDictionary
        for k, v in attributeDictionary.items(): setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def changeAtrribute(self, ncFileName, attributeDictionary, closeFile = False):

        if ncFileName in filecache.keys():
            #~ print "Cached: ", ncFileName
            rootgrp = filecache[ncFileName]
        else:
            #~ print "New: ", ncFileName
            rootgrp = nc.Dataset(ncFileName,'a')
            filecache[ncFileName] = rootgrp

        for k, v in attributeDictionary.items(): setattr(rootgrp,k,v)

        rootgrp.sync()
        if closeFile == True: rootgrp.close()

    def addNewVariable(self, ncFileName, varName, varUnits, longName = None, closeFile = False):

        if ncFileName in filecache.keys():
            #~ print "Cached: ", ncFileName
            rootgrp = filecache[ncFileName]
        else:
            #~ print "New: ", ncFileName
            rootgrp = nc.Dataset(ncFileName,'a')
            filecache[ncFileName] = rootgrp

        shortVarName = varName
        longVarName  = varName
        if longName != None: longVarName = longName

        var = rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',) ,fill_value=vos.MV,zlib=self.zlib)
        var.standard_name = varName
        var.long_name = longVarName
        var.units = varUnits

        rootgrp.sync()
        if closeFile == True: rootgrp.close()

    def data2NetCDF(self, ncFileName, shortVarName, varField, timeStamp, posCnt = None, closeFile = False):

        if ncFileName in filecache.keys():
            #~ print "Cached: ", ncFileName
            rootgrp = filecache[ncFileName]
        else:
            #~ print "New: ", ncFileName
            rootgrp = nc.Dataset(ncFileName,'a')
            filecache[ncFileName] = rootgrp

        date_time = rootgrp.variables['time']
        if posCnt == None: posCnt = len(date_time)
        date_time[posCnt] = nc.date2num(timeStamp,date_time.units,date_time.calendar)

        rootgrp.variables[shortVarName][posCnt,:,:] = varField

        rootgrp.sync()
        if closeFile == True: rootgrp.close()

    def dataList2NetCDF(self, ncFileName, shortVarNameList, varFieldList, timeStamp, posCnt = None, closeFile = False):

        if ncFileName in filecache.keys():
            #~ print "Cached: ", ncFileName
            rootgrp = filecache[ncFileName]
        else:
            #~ print "New: ", ncFileName
            rootgrp = nc.Dataset(ncFileName,'a')
            filecache[ncFileName] = rootgrp

        date_time = rootgrp.variables['time']
        if posCnt == None: posCnt = len(date_time)

        for shortVarName in shortVarNameList:
            date_time[posCnt] = nc.date2num(timeStamp,date_time.units,date_time.calendar)
            rootgrp.variables[shortVarName][posCnt,:,:] = varFieldList[shortVarName]

        rootgrp.sync()
        if closeFile == True: rootgrp.close()

    def close(self, ncFileName):

        if ncFileName in filecache.keys():
            #~ print "Cached: ", ncFileName
            rootgrp = filecache[ncFileName]
        else:
            #~ print "New: ", ncFileName
            rootgrp = nc.Dataset(ncFileName,'a')
            filecache[ncFileName] = rootgrp

        # closing the file 
        rootgrp.close()

        # remove ncFilename from filecache
        if ncFileName in filecache.keys(): filecache.pop(ncFileName, None)
