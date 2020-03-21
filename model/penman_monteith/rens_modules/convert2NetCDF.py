#-reads in monthly snow cover and extracts fractional monthly snow occurrence

import numpy as np
import netCDF4 as nc

def createNetCDF(ncFile,longitudes,latitudes,timedData= False,attributes= {}):
	#-creates a netCDF file, including its projection attributes.
	#-open nc dataset
	rootgrp= nc.Dataset(ncFile,'w',format= 'NETCDF3_CLASSIC')
	#-create dimensions - time if present is unlimited, others are fixed
	rootgrp.createDimension('latitude',len(latitudes))
	rootgrp.createDimension('longitude',len(longitudes))
	#-create variables
	if timedData:
		rootgrp.createDimension('time',0)
		date_time= rootgrp.createVariable('time','f8',('time',))
		date_time.standard_name= 'time'
		date_time.long_name= 'Hours since 1901-01-01 00:00:00.0'
		date_time.units= 'Hours since 1901-01-01 00:00:00.0'
		date_time.calendar= 'gregorian'
	lat= rootgrp.createVariable('latitude','f4',('latitude'))
	lat.standard_name= 'Latitude'
	lat.long_name= 'Latitude cell centres'
	lon= rootgrp.createVariable('longitude','f4',('longitude'))
	lon.standard_name= 'Longitude'
	lon.long_name= 'Longitude cell centres'
	#-assing latitudes and longitudes to variables
	lat[:]= latitudes
	lon[:]= longitudes  
	#-set attributes
	for attribute,value in attributes.iteritems():
		setattr(rootgrp,attribute,value) 
	#-write to file
	rootgrp.sync()
	rootgrp.close()

def data2NetCDF(ncFile,variableName,variableAttributes,variableArray,posCnt= None,timeStamp= None,MV= -999.9,compress= True):
	#-default variable format and structure
	varFormat= 'f4'
	if isinstance(timeStamp,type(None)):
		varStructure= ('latitude','longitude')  
	else:
		varStructure= ('time','latitude','longitude')  
	#-open file to append information
	rootgrp= nc.Dataset(ncFile,'a')
	#-check if variable is already mapped, if not create
	try:
		mappedVariables= rootgrp.variables
	except:
		mappedVariables= {}
	if variableName not in mappedVariables:
		mappedVariables[variableName]= rootgrp.createVariable(variableName,varFormat,varStructure,fill_value= MV,zlib=compress)
		mappedVariables[variableName].standard_name= variableName
		for attribute,value in variableAttributes.iteritems():
			if attribute == 'long_name' and len(value) == 0:
				value= variableName
			if attribute != 'filename' and attribute != 'interval':
				setattr(mappedVariables[variableName],attribute,value) 
	#-initialize time and posCnt
	# then write timeStamp and variable
	if isinstance(timeStamp,type(None)):
		rootgrp.variables[variableName][:,:]= variableArray
	else:
		date_time= rootgrp.variables['time']
		date_time[posCnt]= nc.date2num(timeStamp,\
				date_time.units,date_time.calendar)
		rootgrp.variables[variableName][posCnt,:,:]= variableArray
	#-update file and close 
	rootgrp.sync()
	rootgrp.close()

def timeseries2NetCDF(ncFile,variableName,variableAttributes,resultsDir,pcrVariableName,startDay,startDate,endDate,
		posCnt,MV= -999.9,compress= True):
	#-default variable format and structure
	varFormat= 'f4'
	varStructure= ('time','latitude','longitude')  
	#-open file to append information
	rootgrp= nc.Dataset(ncFile,'a')
	#-check if variable is already mapped, if not create
	try:
		mappedVariables= rootgrp.variables
	except:
		mappedVariables= {}
	if variableName not in mappedVariables:
		mappedVariables[variableName]= rootgrp.createVariable(variableName,varFormat,varStructure,fill_value= MV,zlib=compress)
		mappedVariables[variableName].standard_name= variableName
		for attribute,value in variableAttributes.iteritems():
			if attribute == 'long_name' and len(value) == 0:
				value= variableName
			if attribute != 'filename' and attribute != 'interval':
				setattr(mappedVariables[variableName],attribute,value) 
	#-initialize time and posCnt
	# then write timeStamp and variable
	date_time= rootgrp.variables['time']
	day= startDay
	for dayCnt in xrange(startDate.toordinal(),endDate.toordinal()):
		date_time[posCnt]= nc.date2num(datetime.datetime.fromordinal(dayCnt),\
				date_time.units,date_time.calendar)
		rootgrp.variables[variableName][posCnt,:,:]= \
			pcr2numpy(pcr.readmap(os.path.join(resultsDir,generateNameT(pcrVariableName,day))),MV)
		os.remove(os.path.join(resultsDir,generateNameT(pcrVariableName,day)))
		day+= 1
		posCnt+= 1
	#-update file and close 
	rootgrp.sync()
	rootgrp.close()
	
def readField(ncFile, variableName, posCnt, MV):
	rootgrp= nc.Dataset(ncFile,'r')
	#- read data
	ncVariable = rootgrp.variables[variableName]
	varArray	 = ncVariable[posCnt,:,:]
	rootgrp.close()
	return varArray
