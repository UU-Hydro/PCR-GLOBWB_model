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
#from pcraster.numpy import pcr2numpy,numpy2pcr
from pcraster import pcr2numpy, numpy2pcr         # needed if we use PCRaster-4 (EHS, 7 May 2013)
import pcraster as pcr
import virtualOS as vos

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
        
        # netCDF format and attributes:
        self.format = 'NETCDF3_CLASSIC'
        self.attributeDictionary = {}
        self.attributeDictionary['institution'] = iniItems.globalOptions['institution']
        self.attributeDictionary['title'      ] = iniItems.globalOptions['title'      ]
        self.attributeDictionary['description'] = iniItems.globalOptions['description']

    def createNetCDF(self, ncFileName, varName, varUnits, \
                                      longName = None):

        rootgrp= nc.Dataset(ncFileName,'w',format= self.format)

        #-create dimensions - time is unlimited, others are fixed
        rootgrp.createDimension('time',None)
        rootgrp.createDimension('lat',len(self.latitudes))
        rootgrp.createDimension('lon',len(self.longitudes))

        date_time= rootgrp.createVariable('time','f4',('time',))
        date_time.standard_name= 'time'
        date_time.long_name= 'Days since 1901-01-01'

        date_time.units= 'Days since 1901-01-01' 
        date_time.calendar= 'standard'

        lat= rootgrp.createVariable('lat','f4',('lat',))
        lat.long_name= 'latitude'
        lat.units= 'degrees_north'
        lat.standard_name = 'latitude'

        lon= rootgrp.createVariable('lon','f4',('lon',))
        lon.standard_name= 'longitude'
        lon.long_name= 'longitude'
        lon.units= 'degrees_east'

        lat[:]= self.latitudes
        lon[:]= self.longitudes

        shortVarName = varName
        longVarName  = varName
        if longName != None: longVarName = longName
        
        var= rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',) ,fill_value=vos.MV,zlib=False)
        var.standard_name = varName
        var.long_name = longVarName
        var.units = varUnits

        attributeDictionary = self.attributeDictionary
        for k, v in attributeDictionary.items():
          setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def changeAtrribute(self,ncFileName,attributeDictionary):

        rootgrp= nc.Dataset(ncFileName,'a',format= self.format)

        for k, v in attributeDictionary.items():
          setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def addNewVariable(self, ncFileName, varName, varUnits,\
                                        longName = None):

        rootgrp= nc.Dataset(ncFileName,'a',format= self.format)

        shortVarName = varName
        longVarName  = varName
        if longName != None: longVarName = longName

        var= rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',) ,fill_value=vos.MV,zlib=False)
        var.standard_name = varName
        var.long_name = longVarName
        var.units = varUnits

        rootgrp.sync()
        rootgrp.close()

    def data2NetCDF(self,ncFile,varName,varField,timeStamp,posCnt = None):

        #-write data to netCDF
        rootgrp= nc.Dataset(ncFile,'a')    

        shortVarName= varName        

        date_time= rootgrp.variables['time']
        if posCnt == None: posCnt = len(date_time)
        date_time[posCnt]= nc.date2num(timeStamp,date_time.units,date_time.calendar)

        rootgrp.variables[shortVarName][posCnt,:,:]= (varField)

        rootgrp.sync()
        rootgrp.close()

    def dataList2NetCDF(self,ncFile,varNameList,varFieldList,timeStamp,posCnt = None):

        #-write data to netCDF
        rootgrp= nc.Dataset(ncFile,'a')    

        date_time = rootgrp.variables['time']
        if posCnt == None: posCnt = len(date_time)

        for varName in varNameList:
            shortVarName = varName        
            varField = varFieldList[varName]
            date_time[posCnt]= nc.date2num(timeStamp,date_time.units,date_time.calendar)
            rootgrp.variables[shortVarName][posCnt,:,:]= varField

        rootgrp.sync()
        rootgrp.close()
