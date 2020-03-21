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
    
    def __init__(self,cloneMapFileName, attributeDictionary = None):
        		
        # cloneMap
        cloneMap = pcr.boolean(pcr.readmap(cloneMapFileName))
        cloneMap = pcr.boolean(pcr.scalar(1.0))
        
        # latitudes and longitudes
        self.latitudes  = np.unique(pcr.pcr2numpy(pcr.ycoordinate(cloneMap), vos.MV))[::-1]
        self.longitudes = np.unique(pcr.pcr2numpy(pcr.xcoordinate(cloneMap), vos.MV))

        # netcdf format:
        self.format = 'NETCDF3_CLASSIC'
        
        self.attributeDictionary = {}
        if attributeDictionary == None:
            self.attributeDictionary['institution'] = "None"
            self.attributeDictionary['title'      ] = "None"
            self.attributeDictionary['source'     ] = "None"
            self.attributeDictionary['history'    ] = "None"
            self.attributeDictionary['references' ] = "None"
            self.attributeDictionary['description'] = "None"
            self.attributeDictionary['comment'    ] = "None"
        else:
            self.attributeDictionary = attributeDictionary
        
    def changeAtrribute(self,ncFileName,attributeDictionary):

        rootgrp= nc.Dataset(ncFileName,'a',format= self.format)

        for k, v in attributeDictionary.items():
          setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def createNetCDF(self,ncFileName,varName,varUnits):

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

        var= rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',) ,fill_value=vos.MV,zlib=False)
        var.standard_name= varName
        var.long_name= varName
        var.units= varUnits

        attributeDictionary = self.attributeDictionary
        for k, v in attributeDictionary.items(): setattr(rootgrp,k,v)

        rootgrp.sync()
        rootgrp.close()

    def addNewVariable(self,ncFileName,varName,varUnits):

        #~ print ncFileName
        rootgrp= nc.Dataset(ncFileName,'a',format= self.format)

        shortVarName = varName

        var= rootgrp.createVariable(shortVarName,'f4',('time','lat','lon',) ,fill_value=vos.MV,zlib=False)
        var.standard_name= varName
        var.long_name= varName
        var.units= varUnits

        rootgrp.sync()
        rootgrp.close()

    def data2NetCDF(self,ncFile,varName,varField,timeStamp,posCnt = None):

        #-write data to netCDF
        rootgrp= nc.Dataset(ncFile,'a')    

        shortVarName = varName

        date_time = rootgrp.variables['time']
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
