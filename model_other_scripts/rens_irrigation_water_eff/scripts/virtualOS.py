#!/usr/bin/python
# -*- coding: utf-8 -*-

# EHS (20 March 2013): This is the list of general functions.
#                      The list is continuation from Rens's and Dominik's.

import subprocess
import datetime
import random
import os
import gc
import re
import math
import sys

import netCDF4 as nc
import numpy as np
import numpy.ma as ma
import pcraster as pcr

import logging
logger = logging.getLogger(__name__)

# Global variables:
MV = 1e20
smallNumber = 1E-39

# file cache to minimize/reduce opening/closing files.  
filecache = dict()

def getIndex(value, values):
  #-RvB 2014-07-28: returns the index of
  #  value in values
  #-set deviations and rank
  deviations= np.abs(values-value)
  rank= np.arange(values.size)
  #-find smallest deviation relative to value in values
  return rank[deviations == np.min(deviations)][0]

def getCroppedMap(xULClone, yULClone, colsClone, rowsClone, cellsizeClone,\
		xULInput, yULInput, colsInput, rowsInput, yPCROrder, cellsizeInput,\
		inputData, MV):
	
	#-RvB 2014-07-29: returns an array of the size equal to the clone map
	#-initialize clone cell-centre coordinates and resample factor
	resampleFactor= max(1,int(float(cellsizeInput)/float(cellsizeClone)))
	cloneXCoordinates= xULClone+(np.arange(colsClone)+0.5)*cellsizeClone
	cloneYCoordinates= yULClone-(np.arange(rowsClone)+0.5)*cellsizeClone
	xULClone= cloneXCoordinates[0]
	yULClone= cloneYCoordinates[0]
	xLRClone= cloneXCoordinates[-1]
	yLRClone= cloneYCoordinates[-1]
	#-get cell-corner coordinates from the input map
	inputXCoordinates= xULInput+(np.arange(colsInput)+0.5)*cellsizeInput
	if yPCROrder:
		inputYCoordinates= yULInput-(np.arange(rowsInput)+0.5)*cellsizeInput
	else:
		#-check!
		inputYCoordinates= yULInput+(np.arange(rowsInput)+0.5)*cellsizeInput
	xULInput= inputXCoordinates[0]
	yULInput= inputYCoordinates[0]
	xLRInput= inputXCoordinates[-1]
	yLRInput= inputYCoordinates[-1]
	#-get index
	xIdxSta= getIndex(xULClone, inputXCoordinates)
	xIdxEnd= getIndex(xLRClone, inputXCoordinates)
	yIdxSta= getIndex(yULClone, inputYCoordinates)
	yIdxEnd= getIndex(yLRClone, inputYCoordinates)
	
	#-set output array
	outputData= np.ones((rowsClone, colsClone))*MV

	#-check on options:
	# 1) coordinate sizes agree and resample factor equals 1: input data satisfies output requirements, return
	if resampleFactor == 1 and (xIdxEnd-xIdxSta+1) == colsClone and (yIdxEnd-yIdxSta+1) == rowsClone:
		outputData[:]= inputData[yIdxSta:yIdxEnd+1,xIdxSta:xIdxEnd+1]
	# 2) resample factor equals 1 but coordinates are not the same
	elif resampleFactor == 1:
		#-set output array and get bounding array
		xULOutput= max(cloneXCoordinates[0],inputXCoordinates[0])
		xLROutput= min(cloneXCoordinates[-1],inputXCoordinates[-1])
		yULOutput= min(cloneYCoordinates[0],inputYCoordinates[0])
		yLROutput= max(cloneYCoordinates[-1],inputYCoordinates[-1])
		xIdxSta= getIndex(xULOutput, inputXCoordinates)
		xIdxEnd= getIndex(xLROutput, inputXCoordinates)
		yIdxSta= getIndex(yULOutput, inputYCoordinates)
		yIdxEnd= getIndex(yLROutput, inputYCoordinates)
		xIdsSta= getIndex(xULOutput, cloneXCoordinates)
		xIdsEnd= getIndex(xLROutput, cloneXCoordinates)
		yIdsSta= getIndex(yULOutput, cloneYCoordinates)
		yIdsEnd= getIndex(yLROutput, cloneYCoordinates)
		
		#-debug
		debug= False
		if debug:
			print xULOutput, xULClone, xULInput
			print xIdxSta, inputXCoordinates[xIdxSta], xIdsSta, cloneXCoordinates[xIdsSta]
			print
			print yULOutput, yULClone, yULInput
			print yIdxSta, inputYCoordinates[yIdxSta], yIdsSta, cloneYCoordinates[yIdsSta]
			print
			print xLROutput, xLRClone, xLRInput
			print xIdxEnd, inputXCoordinates[xIdxEnd], xIdsSta, cloneXCoordinates[xIdsEnd]
			print
			print yLROutput, yLRClone, yLRInput
			print yIdxEnd, inputYCoordinates[yIdxEnd], yIdsEnd, cloneYCoordinates[yIdsEnd]
			print
			print xIdxSta, xIdxEnd, xIdxEnd-xIdxSta
			print
			print xIdsSta, xIdsEnd, xIdsEnd-xIdsSta
			print
			print yIdxSta, yIdxEnd, yIdxEnd-yIdxSta
			print
			print yIdsSta, yIdsEnd, yIdsEnd-yIdsSta
			print
			print cloneYCoordinates.size, cloneXCoordinates.size, cloneYCoordinates.size*cloneXCoordinates.size
	
		outputData[yIdsSta:yIdsEnd+1,xIdsSta:xIdsEnd+1]= inputData[yIdxSta:yIdxEnd+1,xIdxSta:xIdxEnd+1]
	# 3) information is resampled using a nearest neighbour approach and resample factor reset to zero
	else:
		#-set output data array and reset resample factor
		resampleFactor= 1.
		outputData= np.ones((cloneYCoordinates.size,cloneXCoordinates.size))*MV
		#-iterate over rows, columns and find index
		for rowCnt in xrange(cloneYCoordinates.size):
			yIdxSta= getIndex(cloneYCoordinates[rowCnt], inputYCoordinates)
			for colCnt in xrange(cloneXCoordinates.size):
				xIdxSta= getIndex(cloneXCoordinates[colCnt], inputXCoordinates)
				outputData[rowCnt,colCnt]= inputData[yIdxSta,xIdxSta]
	#-return output and resample factor
	return outputData, resampleFactor      

def netcdf2PCRobjCloneWithoutTime(ncFile,varName,
                                  cloneMapFileName  = None,\
                                  LatitudeLongitude = False,\
                                  specificFillValue = None):
    # 
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    # Get netCDF file and variable name:
    if ncFile in filecache.keys():
        f = filecache[ncFile]
        print "Cached: ", ncFile
    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f
        print "New: ", ncFile
    
    #print ncFile
    #f = nc.Dataset(ncFile)  
    varName = str(varName)
    
    if LatitudeLongitude == True:
        try:
            f.variables['lat'] = f.variables['latitude']
            f.variables['lon'] = f.variables['longitude']
        except:
            pass
    
    sameClone = True
    # check whether clone and input maps have the same attributes:
    if cloneMapFileName != None:
        # get the attributes of cloneMap
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone['cellsize']
        rowsClone = attributeClone['rows']
        colsClone = attributeClone['cols']
        xULClone = attributeClone['xUL']
        yULClone = attributeClone['yUL']
        # get the attributes of input (netCDF) 
        cellsizeInput = f.variables['lat'][0]- f.variables['lat'][1]
        cellsizeInput = float(cellsizeInput)
        rowsInput = len(f.variables['lat'])
        colsInput = len(f.variables['lon'])
        xULInput = f.variables['lon'][0]-0.5*cellsizeInput
        yULInput = f.variables['lat'][0]+0.5*cellsizeInput
        # check whether both maps have the same attributes 
        if cellsizeClone != cellsizeInput: sameClone = False
        if rowsClone != rowsInput: sameClone = False
        if colsClone != colsInput: sameClone = False
        if xULClone != xULInput: sameClone = False
        if yULClone != yULInput: sameClone = False

    cropData = f.variables[varName][:,:]       # still original data
    factor = 1                                 # needed in regridData2FinerGrid
    if sameClone == False:
        # crop to cloneMap:
        minX    = min(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput))) # ; print(minX)
        xIdxSta = int(np.where(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput)) == minX)[0])
        xIdxEnd = int(math.ceil(xIdxSta + colsClone /(cellsizeInput/cellsizeClone)))
        minY    = min(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput))) # ; print(minY)
        yIdxSta = int(np.where(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput)) == minY)[0])
        yIdxEnd = int(math.ceil(yIdxSta + rowsClone /(cellsizeInput/cellsizeClone)))
        cropData = f.variables[varName][yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
        factor = int(float(cellsizeInput)/float(cellsizeClone))
    
    # convert to PCR object and close f
    if specificFillValue != None:
        outPCR = pcr.numpy2pcr(pcr.Scalar, \
                  regridData2FinerGrid(factor,cropData,MV), \
                  float(specificFillValue))
    else:
        outPCR = pcr.numpy2pcr(pcr.Scalar, \
                  regridData2FinerGrid(factor,cropData,MV), \
                  float(f.variables[varName]._FillValue))
                  
    #~ # debug:
    #~ pcr.report(outPCR,"tmp.map")
    #~ print(varName)
    #~ os.system('aguila tmp.map')
    
    #f.close();
    f = None ; cropData = None 
    # PCRaster object
    return (outPCR)

def netcdf2PCRobjClone(ncFile,varName,dateInput,\
                       useDoy = None,
                       cloneMapFileName  = None,\
                       LatitudeLongitude = True,\
                       specificFillValue = None):
    # 
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    # Get netCDF file and variable name:
    
    print ncFile
    print LatitudeLongitude
    
    if ncFile in filecache.keys():
        f = filecache[ncFile]
        print "Cached: ", ncFile
    else:
        f = nc.Dataset(ncFile)
        filecache[ncFile] = f
        print "New: ", ncFile
    
    varName = str(varName)
    
    if LatitudeLongitude == True:
        try:
            f.variables['lat'] = f.variables['latitude']
            f.variables['lon'] = f.variables['longitude']
        except:
            pass
    
    if varName == "evapotranspiration":        
        try:
            f.variables['evapotranspiration'] = f.variables['referencePotET']
        except:
            pass

    # date
    date = dateInput
    if useDoy == "Yes": 
        idx = dateInput - 1
    else:
        if isinstance(date, str) == True: date = \
                        datetime.datetime.strptime(str(date),'%Y-%m-%d') 
        date = datetime.datetime(date.year,date.month,date.day)
        # time index (in the netCDF file)
        if useDoy == "month":
            idx = int(date.month) - 1
        else:
            nctime = f.variables['time']  # A netCDF time variable object.
            if useDoy == "yearly":\
                date = datetime.datetime(date.year,int(1),int(1))
            if useDoy == "monthly":\
                date = datetime.datetime(date.year,date.month,int(1))
            try:
                idx = nc.date2index(date, nctime, calendar = nctime.calendar, \
                                                  select='exact')
            except:                                  
                idx = nc.date2index(date, nctime, calendar = nctime.calendar, \
                                                  select='before')
                msg  = "\n"
                msg += "WARNING related to the netcdf file: "+str(ncFile)+" ; variable: "+str(varName)+" !!!!!!"+"\n"
                msg += "No "+str(dateInput)+" is available. The 'before' option is used while selecting netcdf time."
                logger.info(msg)                                   
                                                  
    idx = int(idx)                                                  

    sameClone = True
    # check whether clone and input maps have the same attributes:
    if cloneMapFileName != None:
        # get the attributes of cloneMap
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone['cellsize']
        rowsClone = attributeClone['rows']
        colsClone = attributeClone['cols']
        xULClone = attributeClone['xUL']
        yULClone = attributeClone['yUL']
        # get the attributes of input (netCDF)
        #-RvB 2014-07-28: mean resolution
        cellsizeInput = np.abs(np.max(f.variables['lon'][:-1] - f.variables['lon'][1:]))
        cellsizeInput = float(cellsizeInput)
        rowsInput = len(f.variables['lat'])
        colsInput = len(f.variables['lon'])
        
        #-RvB 2014-07-28: order of y input added: True if y-coordinates are sorted from high to low
        # and obtain lower right corners of clone and input maps
        yPCROrder= f.variables['lat'][:].max() == f.variables['lat'][0]
        xULInput = f.variables['lon'][0] - 0.5*cellsizeInput
        yULInput = f.variables['lat'][:].max() + 0.5*cellsizeInput
        #-lower right corners
        xLRClone= round(xULClone + colsClone * cellsizeClone,4)
        yLRClone= round(yULClone - rowsClone * cellsizeClone,4)
        xLRInput= f.variables['lon'][-1] + 0.5*cellsizeInput
        yLRInput= f.variables['lat'][:].min() - 0.5*cellsizeInput
        # check whether both maps have the same attributes 
        if cellsizeClone != cellsizeInput: sameClone = False
        if rowsClone != rowsInput: sameClone = False
        if colsClone != colsInput: sameClone = False
        if xULClone != xULInput: sameClone = False
        if yULClone != yULInput: sameClone = False
        
        debug= False
        if debug:
					print 'x input:',colsInput,xULInput, xLRInput, cellsizeInput
					print 'y input:',rowsInput,yULInput, yLRInput, cellsizeInput
					print 'x clone:',colsClone,xULClone, xLRClone, cellsizeClone
					print 'y clone:',rowsClone,yULClone, yLRClone, cellsizeClone				

    cropData = f.variables[varName][int(idx),:,:]       # still original data
    factor = 1                          # needed in regridData2FinerGrid
		#-RvB 2014-07-28: the following original lines were disabled and changed to return generic indices
    #~ if sameClone == False:
        #~ # crop to cloneMap:
        #~ #~xIdxSta = int(np.where(f.variables['lon'][:] == xULClone + 0.5*cellsizeInput)[0])
        #~ minX    = min(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput))) # ; print(minX)
        #~ xIdxSta = int(np.where(abs(f.variables['lon'][:] - (xULClone + 0.5*cellsizeInput)) == minX)[0])
        #~ xIdxEnd = int(math.ceil(xIdxSta + colsClone /(cellsizeInput/cellsizeClone)))
        #~ #~yIdxSta = int(np.where(f.variables['lat'][:] == yULClone - 0.5*cellsizeInput)[0])
        #~ minY    = min(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput))) # ; print(minY)
        #~ yIdxSta = int(np.where(abs(f.variables['lat'][:] - (yULClone - 0.5*cellsizeInput)) == minY)[0])
        #~ yIdxEnd = int(math.ceil(yIdxSta + rowsClone /(cellsizeInput/cellsizeClone)))
        #~ cropData = f.variables[varName][idx,yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
        #~ factor = int(float(cellsizeInput)/float(cellsizeClone))
		#-RvB:added
    if sameClone == False:
        # crop to cloneMap:
        cropData, factor= getCroppedMap(xULClone, yULClone, colsClone, rowsClone, cellsizeClone,\
					xULInput, yULInput, colsInput, rowsInput, yPCROrder, cellsizeInput,\
					cropData, MV)
        specificFillValue= MV
    if debug:
			print MV, specificFillValue, float(f.variables[varName]._FillValue)
    #-RvB: end
    
    # convert to PCR object and close f
    if specificFillValue != None:
        outPCR = pcr.numpy2pcr(pcr.Scalar, \
                  regridData2FinerGrid(factor,cropData,MV), \
                  float(specificFillValue))
    else:
        outPCR = pcr.numpy2pcr(pcr.Scalar, \
                  regridData2FinerGrid(factor,cropData,MV), \
                  float(f.variables[varName]._FillValue))

    if debug == True:
			pcr.report(pcr.numpy2pcr(pcr.Scalar,cropData,MV),'temp_%s.map' % os.path.split(cloneMapFileName)[1])
                  
    #f.close();
    f = None ; cropData = None 
    # PCRaster object
    return (outPCR)

def netcdf2PCRobjCloneWindDist(ncFile,varName,dateInput,useDoy = None,
                       cloneMapFileName=None):
    # EHS (02 SEP 2013): This is a special function made by Niko Wanders (for his DA framework).
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    
    # Get netCDF file and variable name:
    f = nc.Dataset(ncFile)
    varName = str(varName)

    # date
    date = dateInput
    if useDoy == "Yes": 
        idx = dateInput - 1
    else:
        if isinstance(date, str) == True: date = \
                        datetime.datetime.strptime(str(date),'%Y-%m-%d') 
        date = datetime.datetime(date.year,date.month,date.day)
        # time index (in the netCDF file)
        nctime = f.variables['time']  # A netCDF time variable object.
        idx = nc.date2index(date, nctime, calendar=nctime.calendar, \
                                                     select='exact')
    idx = int(idx)                                                  

    sameClone = True
    # check whether clone and input maps have the same attributes:
    if cloneMapFileName != None:
        # get the attributes of cloneMap
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone['cellsize']
        rowsClone = attributeClone['rows']
        colsClone = attributeClone['cols']
        xULClone = attributeClone['xUL']
        yULClone = attributeClone['yUL']
        # get the attributes of input (netCDF) 
        cellsizeInput = f.variables['lat'][0]- f.variables['lat'][1]
        cellsizeInput = float(cellsizeInput)
        rowsInput = len(f.variables['lat'])
        colsInput = len(f.variables['lon'])
        xULInput = f.variables['lon'][0]-0.5*cellsizeInput
        yULInput = f.variables['lat'][0]+0.5*cellsizeInput
        # check whether both maps have the same attributes 
        if cellsizeClone != cellsizeInput: sameClone = False
        if rowsClone != rowsInput: sameClone = False
        if colsClone != colsInput: sameClone = False
        if xULClone != xULInput: sameClone = False
        if yULClone != yULInput: sameClone = False

    cropData = f.variables[varName][int(idx),:,:]       # still original data
    factor = 1                          # needed in regridData2FinerGrid
    if sameClone == False:
        # crop to cloneMap:
        xIdxSta = int(np.where(f.variables['lon'][:] == xULClone + 0.5*cellsizeInput)[0])
        xIdxEnd = int(math.ceil(xIdxSta + colsClone /(cellsizeInput/cellsizeClone)))
        yIdxSta = int(np.where(f.variables['lat'][:] == yULClone - 0.5*cellsizeInput)[0])
        yIdxEnd = int(math.ceil(yIdxSta + rowsClone /(cellsizeInput/cellsizeClone)))
        cropData = f.variables[varName][idx,yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
        factor = int(float(cellsizeInput)/float(cellsizeClone))
    
    # convert to PCR object and close f
    outPCR = pcr.numpy2pcr(pcr.Scalar, \
               regridData2FinerGrid(factor,cropData,MV), \
                  float(0.0))
    f.close();
    f = None ; cropData = None 
    # PCRaster object
    return (outPCR)    
    
def netcdf2PCRobjCloneWind(ncFile,varName,dateInput,useDoy = None,
                       cloneMapFileName=None):
    # EHS (02 SEP 2013): This is a special function made by Niko Wanders (for his DA framework).
    # EHS (19 APR 2013): To convert netCDF (tss) file to PCR file.
    # --- with clone checking
    #     Only works if cells are 'square'.
    #     Only works if cellsizeClone <= cellsizeInput
    
    # Get netCDF file and variable name:
    f = nc.Dataset(ncFile)
    varName = str(varName)

    # date
    date = dateInput
    if useDoy == "Yes": 
        idx = dateInput - 1
    else:
        if isinstance(date, str) == True: date = \
                        datetime.datetime.strptime(str(date),'%Y-%m-%d') 
        date = datetime.datetime(date.year,date.month,date.day, 0, 0)
        # time index (in the netCDF file)
        nctime = f.variables['time']  # A netCDF time variable object.
        idx = nc.date2index(date, nctime, select="exact")
    idx = int(idx)                                                  

    sameClone = True
    # check whether clone and input maps have the same attributes:
    if cloneMapFileName != None:
        # get the attributes of cloneMap
        attributeClone = getMapAttributesALL(cloneMapFileName)
        cellsizeClone = attributeClone['cellsize']
        rowsClone = attributeClone['rows']
        colsClone = attributeClone['cols']
        xULClone = attributeClone['xUL']
        yULClone = attributeClone['yUL']
        # get the attributes of input (netCDF) 
        cellsizeInput = f.variables['lat'][0]- f.variables['lat'][1]
        cellsizeInput = float(cellsizeInput)
        rowsInput = len(f.variables['lat'])
        colsInput = len(f.variables['lon'])
        xULInput = f.variables['lon'][0]-0.5*cellsizeInput
        yULInput = f.variables['lat'][0]+0.5*cellsizeInput
        # check whether both maps have the same attributes 
        if cellsizeClone != cellsizeInput: sameClone = False
        if rowsClone != rowsInput: sameClone = False
        if colsClone != colsInput: sameClone = False
        if xULClone != xULInput: sameClone = False
        if yULClone != yULInput: sameClone = False

    cropData = f.variables[varName][int(idx),:,:]       # still original data
    factor = 1                          # needed in regridData2FinerGrid
    if sameClone == False:
        # crop to cloneMap:
        xIdxSta = int(np.where(f.variables['lon'][:] == xULClone + 0.5*cellsizeInput)[0])
        xIdxEnd = int(math.ceil(xIdxSta + colsClone /(cellsizeInput/cellsizeClone)))
        yIdxSta = int(np.where(f.variables['lat'][:] == yULClone - 0.5*cellsizeInput)[0])
        yIdxEnd = int(math.ceil(yIdxSta + rowsClone /(cellsizeInput/cellsizeClone)))
        cropData = f.variables[varName][idx,yIdxSta:yIdxEnd,xIdxSta:xIdxEnd]
        factor = int(float(cellsizeInput)/float(cellsizeClone))
    
    # convert to PCR object and close f
    outPCR = pcr.numpy2pcr(pcr.Scalar, \
               regridData2FinerGrid(factor,cropData,MV), \
                  float(f.variables[varName]._FillValue))
    f.close();
    f = None ; cropData = None 
    # PCRaster object
    return (outPCR)    
    
def netcdf2PCRobj(ncFile,varName,dateInput):
    # EHS (04 APR 2013): To convert netCDF (tss) file to PCR file.
    # The cloneMap is globally defined (outside this method).
    
    # Get netCDF file and variable name:
    f = nc.Dataset(ncFile)
    varName = str(varName)

    # date
    date = dateInput
    if isinstance(date, str) == True: date = \
                    datetime.datetime.strptime(str(date),'%Y-%m-%d') 
    date = datetime.datetime(date.year,date.month,date.day)
    
    # time index (in the netCDF file)
    nctime = f.variables['time']  # A netCDF time variable object.
    idx = nc.date2index(date, nctime, calendar=nctime.calendar, \
                                                 select='exact') 
    
    # convert to PCR object and close f
    outPCR = pcr.numpy2pcr(pcr.Scalar,(f.variables[varName][idx].data), \
                             float(f.variables[varName]._FillValue))
    f.close(); f = None ; del f
    # PCRaster object
    return (outPCR)

def makeDir(directoryName):
    try:
        os.makedirs(directoryName)
    except OSError:
        pass

def writePCRmapToDir(v,outFileName,outDir):
    # v: inputMapFileName or floating values
    # cloneMapFileName: If the inputMap and cloneMap have different clones,
    #                   resampling will be done. Then,   
    fullFileName = getFullPath(outFileName,outDir)
    pcr.report(v,fullFileName)

def readPCRmapClone(v,cloneMapFileName,tmpDir,absolutePath=None,isLddMap=False,cover=None,isNomMap=False):
	# v: inputMapFileName or floating values
	# cloneMapFileName: If the inputMap and cloneMap have different clones,
	#                   resampling will be done.   
    print(v)
    if v == "None":
        PCRmap = str("None")
    elif not re.match(r"[0-9.-]*$",v):
        if absolutePath != None: v = getFullPath(v,absolutePath)
        # print(v)
        sameClone = isSameClone(v,cloneMapFileName)
        if sameClone == True:
            PCRmap = pcr.readmap(v)
        else:
            # resample using GDAL:
            output = tmpDir+'temp.map'
            warp = gdalwarpPCR(v,output,cloneMapFileName,tmpDir,isLddMap,isNomMap)
            # read from temporary file and delete the temporary file:
            PCRmap = pcr.readmap(output)
            if isLddMap == True: PCRmap = pcr.ifthen(pcr.scalar(PCRmap) < 10., PCRmap)
            if isLddMap == True: PCRmap = pcr.ldd(PCRmap)
            if isNomMap == True: PCRmap = pcr.ifthen(pcr.scalar(PCRmap) >  0., PCRmap)
            if isNomMap == True: PCRmap = pcr.nominal(PCRmap)
            co = 'rm '+str(tmpDir)+'*.*'
            cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    else:
        PCRmap = pcr.scalar(float(v))
    if cover != None:
        PCRmap = pcr.cover(PCRmap, cover)
    co = None; cOut = None; err = None; warp = None
    del co; del cOut; del err; del warp
    stdout = None; del stdout
    stderr = None; del stderr
    return PCRmap    

def readPCRmap(v):
	# v : fileName or floating values
    if not re.match(r"[0-9.-]*$", v):
        PCRmap = pcr.readmap(v)
    else:
        PCRmap = pcr.scalar(float(v))
    return PCRmap    

def isSameClone(inputMapFileName,cloneMapFileName):    
    # reading inputMap:
    attributeInput = getMapAttributesALL(inputMapFileName)
    cellsizeInput = attributeInput['cellsize']
    rowsInput = attributeInput['rows']
    colsInput = attributeInput['cols']
    xULInput = attributeInput['xUL']
    yULInput = attributeInput['yUL']
    # reading cloneMap:
    attributeClone = getMapAttributesALL(cloneMapFileName)
    cellsizeClone = attributeClone['cellsize']
    rowsClone = attributeClone['rows']
    colsClone = attributeClone['cols']
    xULClone = attributeClone['xUL']
    yULClone = attributeClone['yUL']
    # check whether both maps have the same attributes? 
    sameClone = True
    if cellsizeClone != cellsizeInput: sameClone = False
    if rowsClone != rowsInput: sameClone = False
    if colsClone != colsInput: sameClone = False
    if xULClone != xULInput: sameClone = False
    if yULClone != yULInput: sameClone = False
    return sameClone

def gdalwarpPCR(input,output,cloneOut,tmpDir,isLddMap=False,isNominalMap=False):
    # 19 Mar 2013 created by Edwin H. Sutanudjaja
    # all input maps must be in PCRaster maps
    # 
    # remove temporary files:
    co = 'rm '+str(tmpDir)+'*.*'
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    # 
    # converting files to tif:
    co = 'gdal_translate -ot Float64 '+str(input)+' '+str(tmpDir)+'tmp_inp.tif'
    if isLddMap == True: co = 'gdal_translate -ot Int32 '+str(input)+' '+str(tmpDir)+'tmp_inp.tif'
    if isNominalMap == True: co = 'gdal_translate -ot Int32 '+str(input)+' '+str(tmpDir)+'tmp_inp.tif'
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    # 
    # get the attributes of PCRaster map:
    cloneAtt = getMapAttributesALL(cloneOut)
    xmin = cloneAtt['xUL']
    ymin = cloneAtt['yUL'] - cloneAtt['rows']*cloneAtt['cellsize']
    xmax = cloneAtt['xUL'] + cloneAtt['cols']*cloneAtt['cellsize']
    ymax = cloneAtt['yUL'] 
    xres = cloneAtt['cellsize']
    yres = cloneAtt['cellsize']
    te = '-te '+str(xmin)+' '+str(ymin)+' '+str(xmax)+' '+str(ymax)+' '
    tr = '-tr '+str(xres)+' '+str(yres)+' '
    co = 'gdalwarp '+te+tr+ \
         ' -srcnodata -3.4028234663852886e+38 -dstnodata mv '+ \
           str(tmpDir)+'tmp_inp.tif '+ \
           str(tmpDir)+'tmp_out.tif'
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    # 
    co = 'gdal_translate -of PCRaster '+ \
              str(tmpDir)+'tmp_out.tif '+str(output)
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    # 
    co = 'mapattr -c '+str(cloneOut)+' '+str(output)
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    # 
    #~ co = 'aguila '+str(output)
    #~ print(co)
    #~ cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    # 
    co = 'rm '+str(tmpDir)+'tmp*.*'
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    co = None; cOut = None; err = None
    del co; del cOut; del err
    stdout = None; del stdout
    stderr = None; del stderr
    n = gc.collect() ; del gc.garbage[:] ; n = None ; del n

def getFullPath(inputPath,absolutePath,completeFileName = True):
    # 19 Mar 2013 created by Edwin H. Sutanudjaja
    # Function: to get the full absolute path of a folder or a file
          
    # list of suffixes (extensions) that can be used:
    suffix = ('/','_','.nc4','.map','.nc','.dat','.txt','.asc','.ldd',\
              '.001','.002','.003','.004','.005','.006',\
              '.007','.008','.009','.010','.011','.012')
    
    if inputPath.startswith('/'):
        fullPath = str(inputPath)
    else:
        if absolutePath.endswith('/'): 
            absolutePath = str(absolutePath)
        else:
			absolutePath = str(absolutePath)+'/'    
        fullPath = str(absolutePath)+str(inputPath)
    
    if completeFileName:
        if fullPath.endswith(suffix): 
            fullPath = str(fullPath)
    	else:
            fullPath = str(fullPath)+'/'    

    return fullPath    		

def findISIFileName(year,model,rcp,prefix,var):
    histYears = [1951,1961,1971,1981,1991,2001]
    sYears = [2011,2021,2031,2041,2051,2061,2071,2081,2091]
    rcpStr = rcp
    if year >= sYears[0]:
        sYear = [i for i in range(len(sYears)) if year >= sYears[i]]
        sY  = sYears[sYear[-1]]
        
    elif year < histYears[-1]:
       
        sYear = [i for i in range(len(histYears)) if year >= histYears[i] ]
        sY  = histYears[sYear[-1]]
    
    if year >= histYears[-1] and year < sYears[0]:
         
        if model == 'HadGEM2-ES':
            if year < 2005:
                rcpStr = 'historical'               
                sY = 2001
                eY = 2004
            else:
                rcpStr = rcp
                sY = 2005
                eY = 2010
        if model == 'IPSL-CM5A-LR' or model == 'GFDL-ESM2M':
            if year < 2006:
                rcpStr = 'historical'
                sY = 2001
                eY = 2005
            else:
                rcpStr = rcp
                sY = 2006
                eY = 2010
            
    else:        
        eY = sY + 9
        if sY == 2091:
            eY  = 2099
    if model == 'HadGEM2-ES':
        if year < 2005:
            rcpStr = 'historical'
    if model == 'IPSL-CM5A-LR' or model == 'GFDL-ESM2M':
        if year < 2006:
            rcpStr = 'historical'
    #print year,sY,eY
    return "%s_%s_%s_%s_%i-%i.nc" %(var,prefix,model.lower(),rcpStr,sY,eY)

 
def get_random_word(wordLen):
    word = ''
    for i in range(wordLen):
        word += random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
    return word
    
def isLastDayOfMonth(date):
    if (date + datetime.timedelta(days=1 )).day == 1:
        return True
    else:
        return False

def getMapAttributesALL(cloneMap):
    co = ['mapattr -p %s ' %(cloneMap)]
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    if err !=None or cOut == []:
        print "Something wrong with mattattr in virtualOS, maybe clone Map does not exist ? "
        sys.exit()
    mapAttr = {'cellsize': float(cOut.split()[7]) ,\
               'rows'    : float(cOut.split()[3]) ,\
               'cols'    : float(cOut.split()[5]) ,\
               'xUL'     : float(cOut.split()[17]),\
               'yUL'     : float(cOut.split()[19])}
    co = None; cOut = None; err = None
    del co; del cOut; del err
    n = gc.collect() ; del gc.garbage[:] ; n = None ; del n
    return mapAttr 

def getMapAttributes(cloneMap,attribute):
    co = ['mapattr -p %s ' %(cloneMap)]
    cOut,err = subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
    #print cOut
    if err !=None or cOut == []:
        print "Something wrong with mattattr in virtualOS, maybe clone Map does not exist ? "
        sys.exit()
    #print cOut.split()
    co = None; err = None
    del co; del err
    n = gc.collect() ; del gc.garbage[:] ; n = None ; del n
    if attribute == 'cellsize':
        return float(cOut.split()[7])
    if attribute == 'rows':
        return int(cOut.split()[3])
        #return float(cOut.split()[3])
    if attribute == 'cols':
        return int(cOut.split()[5])
        #return float(cOut.split()[5])
    if attribute == 'xUL':
        return float(cOut.split()[17])
    if attribute == 'yUL':
        return float(cOut.split()[19])
    
def getMapTotal(mapFile):
    ''' outputs the sum of all values in a map file '''

    total, valid= pcr.cellvalue(pcr.maptotal(mapFile),1)
    return total



def get_rowColAboveThreshold(map, threshold):
    npMap = pcr.pcr2numpy(map, -9999)
    (nr, nc) = np.shape(npMap)
    for r in range(0, nr):
        for c in range(0, nc):
            if npMap[r, c] != -9999:
                if np.abs(npMap[r, c]) > threshold:


                    return (r, c)


def getLastDayOfMonth(date):
    ''' returns the last day of the month for a given date '''

    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)

def getMinMaxMean(mapFile,ignoreEmptyMap=False):
    mn = pcr.cellvalue(pcr.mapminimum(mapFile),1)[0]
    mx = pcr.cellvalue(pcr.mapmaximum(mapFile),1)[0]
    nrValues = pcr.cellvalue(pcr.maptotal(pcr.scalar(pcr.defined(mapFile))), 1 ) [0] #/ getNumNonMissingValues(mapFile)
    if nrValues == 0.0 and ignoreEmptyMap: 
        return 0.0,0.0,0.0
    else:
        return mn,mx,(getMapTotal(mapFile) / nrValues)
#~ 
#~ def getMinMaxMean(mapFile):
    #~ mn = pcr.cellvalue(pcr.mapminimum(mapFile),1)[0]
    #~ mx = pcr.cellvalue(pcr.mapmaximum(mapFile),1)[0]
    #~ nrValues  = pcr.cellvalue(pcr.maptotal(pcr.scalar(pcr.defined(mapFile))), 1 ) [0] #/ getNumNonMissingValues(mapFile)
    #~ return mn,mx,(getMapTotal(mapFile) / nrValues)

def getMapVolume(mapFile,cellareaFile):
    ''' returns the sum of all grid cell values '''
    volume = mapFile * cellareaFile
    return (getMapTotal(volume) / 1)

def secondsPerDay():
    return float(3600 * 24)
    
def getValDivZero(x,y,y_lim,z_def= 0.):
  #-returns the result of a division that possibly involves a zero
  # denominator; in which case, a default value is substituted:
  # x/y= z in case y > y_lim,
  # x/y= z_def in case y <= y_lim, where y_lim -> 0.
  # z_def is set to zero if not otherwise specified
  return pcr.ifthenelse(y > y_lim,x/pcr.max(y_lim,y),z_def)

def getValFloatDivZero(x,y,y_lim,z_def= 0.):
  #-returns the result of a division that possibly involves a zero
  # denominator; in which case, a default value is substituted:
  # x/y= z in case y > y_lim,
  # x/y= z_def in case y <= y_lim, where y_lim -> 0.
  # z_def is set to zero if not otherwise specified
  if y > y_lim:
    return x / max(y_lim,y)
  else:
    return z_def


def retrieveMapValue(pcrX,coordinates):
    #-retrieves values from a map and returns an array conform the IDs stored in properties
    nrRows= coordinates.shape[0]
    x= np.ones((nrRows))* MV
    tmpIDArray= pcr.pcr2numpy(pcrX,MV)
    for iCnt in xrange(nrRows):
      row,col= coordinates[iCnt,:]
      if row != MV and col != MV:
        x[iCnt]= tmpIDArray[row,col]
    return x

def returnMapValue(pcrX,x,coord):
    #-retrieves value from an array and update values in the map
    if x.ndim == 1:
      nrRows= 1

    tempIDArray= pcr.pcr2numpy(pcrX,MV)
    #print tempIDArray
    temporary= tempIDArray
    nrRows= coord.shape[0]
    for iCnt in xrange(nrRows):
      row,col= coord[iCnt,:]
      if row != MV and col != MV:
        tempIDArray[row,col]= (x[iCnt])
       # print iCnt,row,col,x[iCnt]
    pcrX= pcr.numpy2pcr(pcr.Scalar,tempIDArray,MV)
    return pcrX
    
def getQAtBasinMouths(discharge, basinMouth):
    temp = pcr.ifthenelse(basinMouth != 0 , discharge * secondsPerDay(),0.)
    pcr.report(temp,"temp.map")
    return (getMapTotal(temp)  / 1e9)

def regridMapFile2FinerGrid (rescaleFac,coarse):
    if rescaleFac ==1:
        return coarse
    return pcr.numpy2pcr(pcr.Scalar, regridData2FinerGrid(rescaleFac,pcr.pcr2numpy(coarse,MV),MV),MV)
    
def regridData2FinerGrid(rescaleFac,coarse,MV):
    if rescaleFac ==1:
        return coarse
    nr,nc = np.shape(coarse)
    
    fine= np.zeros(nr*nc*rescaleFac*rescaleFac).reshape(nr*rescaleFac,nc*rescaleFac) + MV
    
 
    ii = -1
    nrF,ncF = np.shape(fine)
    for i in range(0 , nrF):
            if i % rescaleFac == 0:
                ii += 1
            fine [i,:] = coarse[ii,:].repeat(rescaleFac)

    nr = None; nc = None
    del nr; del nc
    nrF = None; ncF = None
    del nrF; del ncF
    n = gc.collect() ; del gc.garbage[:] ; n = None ; del n
    return fine

def regridToCoarse(fine,fac,mode,missValue):
    nr,nc = np.shape(fine)
    coarse = np.zeros(nr/fac * nc / fac).reshape(nr/fac,nc/fac) + MV
    nr,nc = np.shape(coarse)
    for r in range(0,nr):
        for c in range(0,nc):
            ar = fine[r * fac : fac * (r+1),c * fac: fac * (c+1)]
            m = np.ma.masked_values(ar,missValue)
            if ma.count(m) == 0:
                coarse[r,c] = MV
            else:
                if mode == 'average':
                    coarse [r,c] = ma.average(m)
                elif mode == 'median': 
                    coarse [r,c] = ma.median(m)
                elif mode == 'sum':
                    coarse [r,c] = ma.sum(m)
                elif mode =='min':
                    coarse [r,c] = ma.min(m)
                elif mode == 'max':
                    coarse [r,c] = ma.max(m)
    return coarse    
        
    
def waterBalanceCheck(fluxesIn,fluxesOut,preStorages,endStorages,processName,PrintOnlyErrors,dateStr,threshold=1e-5,landmask=None):
    """ Returns the water balance for a list of input, output, and storage map files  """
    # modified by Edwin (22 Apr 2013)

    inMap   = pcr.spatial(pcr.scalar(0.0))
    outMap  = pcr.spatial(pcr.scalar(0.0))
    dsMap   = pcr.spatial(pcr.scalar(0.0))
    
    for fluxIn in fluxesIn:
        inMap   += fluxIn
    for fluxOut in fluxesOut:
        outMap  += fluxOut
    for preStorage in preStorages:
        dsMap   += preStorage
    for endStorage in endStorages:
        dsMap   -= endStorage

    a,b,c = getMinMaxMean(inMap + dsMap- outMap)
    if abs(a) > threshold or abs(b) > threshold:
        if PrintOnlyErrors: 
            print "WBError %s Min %f Max %f Mean %f" %(processName,a,b,c)
            print ""
            
            #~ # for debugging:
            #~ error = inMap + dsMap- outMap
            #~ os.system('rm error.map')
            #~ pcr.report(error,"error.map")
            #~ os.system('aguila error.map')
            #~ os.system('rm error.map')
            
    #~ wb = inMap + dsMap - outMap
    #~ maxWBError = pcr.cellvalue(pcr.mapmaximum(pcr.abs(wb)), 1, 1)[0]
    #~ #return wb


def waterBalance(  fluxesIn,  fluxesOut,  deltaStorages,  processName,   PrintOnlyErrors,  dateStr,threshold=1e-5):
    """ Returns the water balance for a list of input, output, and storage map files and """

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

    #if PrintOnlyErrors:
    a,b,c = getMinMaxMean(inMap + dsMap- outMap)
    # if abs(a) > 1e-5 or abs(b) > 1e-5:
    # if abs(a) > 1e-4 or abs(b) > 1e-4:
    if abs(a) > threshold or abs(b) > threshold:
        print "WBError %s Min %f Max %f Mean %f" %(processName,a,b,c)
    #    if abs(inflow + deltaS - outflow) > 1e-5:
    #        print "Water balance Error for %s on %s: in = %f\tout=%f\tdeltaS=%f\tBalance=%f" \
    #        %(processName,dateStr,inflow,outflow,deltaS,inflow + deltaS - outflow)
    #else:
    #   print "Water balance for %s: on %s in = %f\tout=%f\tdeltaS=%f\tBalance=%f" \
    #        %(processName,dateStr,inflow,outflow,deltaS,inflow + deltaS - outflow)

    wb = inMap + dsMap - outMap
    maxWBError = pcr.cellvalue(pcr.mapmaximum(pcr.abs(wb)), 1, 1)[0]

    #if maxWBError > 0.001 / 1000:
        #row = 0
        #col = 0
        #cellID = 1
        #troubleCell = 0

        #print "Water balance for %s on %s: %f mm !!! " %(processName,dateStr,maxWBError * 1000)
        #pcr.report(wb,"%s-WaterBalanceError-%s" %(processName,dateStr))

        #npWBMError = pcr2numpy(wb, -9999)
        #(nr, nc) = np.shape(npWBMError)
        #for r in range(0, nr):
            #for c in range(0, nc):

                ## print r,c

                #if npWBMError[r, c] != -9999.0:
                    #val = npWBMError[r, c]
                    #if math.fabs(val) > 0.0001 / 1000:

                        ## print npWBMError[r,c]

                        #row = r
                        #col = c
                        #troubleCell = cellID
                #cellID += 1
        #print 'Water balance for %s on %s: %f mm row %i col %i cellID %i!!! ' % (
            #processName,
            #dateStr,
            #maxWBError * 1000,
            #row,
            #col,
            #troubleCell,
            #)

    return inMap + dsMap - outMap

