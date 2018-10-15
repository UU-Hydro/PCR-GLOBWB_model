#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Ludovicus P. H. (Rens) van Beek, Edwin H. Sutanudjaja, Yoshihide Wada,
# Joyce H. C. Bosmans, Niels Drost, Inge E. M. de Graaf, Kor de Jong, Patricia Lopez Lopez,
# Stefanie Pessenteiner, Oliver Schmitz, Menno W. Straatsma, Niko Wanders, Dominik Wisser,
# and Marc F. P. Bierkens,
# Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#-extracts data from partial netCDF output via arrays

#-modules
import os, sys
import time as tm
import numpy as np
import netCDF4 as nc
import datetime
import glob
from multiprocessing import Pool
import calendar
from dateutil.relativedelta import *

# file cache to minimize/reduce opening/closing files.  
filecache = dict()

def calculate_monthdelta(date1, date2):
    def is_last_day_of_the_month(date):
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        return date.day == days_in_month
    imaginary_day_2 = 31 if is_last_day_of_the_month(date2) else date2.day
    monthdelta = (
        (date2.month - date1.month) +
        (date2.year - date1.year) * 12 +
        (-1 if date1.day > imaginary_day_2 else 0)
        )
    return monthdelta

def getMax(x,a):
	m= float(a.max())
	if x == None:
		return m
	else:
		return max(m,x)
	
def getMin(x,a):
	m= float(a.min())
	if x == None:
		return m
	else:
		return min(m,x)

def netcdfList(inputDir):
	'''creates a dictionary of netcdf files'''
	netcdfList = glob.glob(os.path.join(inputDir, '*.nc'))
	print inputDir
	print os.path.join(inputDir, '*.nc')
	ll=[]
	for ncFile in netcdfList:
		ll.append(ncFile.split('/')[-1])
	return ll

def ncFileNameDict(inputDirRoot, areas, ncFileName):
	'''creates a dictionary of subdomains of pcrglob model outut'''
	netcdfInputDict = {}
	for key in range(1, len(areas)+1, 1):
		value = os.path.join(inputDirRoot, areas[key-1], 'netcdf', ncFileName)
		netcdfInputDict[key] = value
	return netcdfInputDict

def mergeNetCDF(inputTuple):
	
	ncName       = inputTuple[0]
	latMin       = inputTuple[1]
	latMax       = inputTuple[2]
	lonMin       = inputTuple[3]
	lonMax       = inputTuple[4]
	deltaLat     = inputTuple[5]
	deltaLon     = inputTuple[6]
	
	startDate    = inputTuple[7]
	endDate      = inputTuple[8] 
	
	print 'combining files for %s'%ncName
	scriptStartTime = tm.time()
	
	# - dictionary holding netCDFInput
	netCDFInput  = ncFileNameDict(inputDirRoot, areas, ncName)
	
	# - netDCF output file name
	netCDFOutput = outputDir + "/" + ncName.split(".")[0] + "_" + startDate + "_to_" + endDate + ".nc"
	
	print netCDFOutput
	
	#~ ncFormat = 'NETCDF3_CLASSIC'
	#~ ncFormat = 'NETCDF4'
	ncFormat = inputTuple[9]
	
	# option to use zlib compression:
	#~ using_zlib = True
	#~ using_zlib = False               # I decide not to compress (so that we can I analyze it quickly). 
	using_zlib = inputTuple[10]
	if using_zlib == "True": using_zlib = True

	#-set dimensions, attributes, and dimensions per netCDF input data set
	# and retrieve the resolution and definition of coordinates and calendar
	attributes= {}
	dimensions= {}
	variables= {}
	variableName = None
	
	calendar_used = {}
	uniqueTimes = np.array([])

	# defining time based on the given arguments 
	if startDate != None and endDate != None:

		# start time and end time
		sd = str(startDate).split('-')
		startTime = datetime.datetime(int(sd[0]), int(sd[1]), int(sd[2]), 0)
		ed = str(endDate).split('-')
		endTime   = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 0)
		
		print netCDFInput.values()[0]
		
		# open the first netcdf file to get time units and time calendar
		ncFile = netCDFInput.values()[0]
		print ncFile
		f = nc.Dataset(ncFile)
		time_units    = f.variables['time'].units
		time_calendar = f.variables['time'].calendar
		
		# temporal resolution
		timeStepType = "daily"
		if len(f.variables['time']) > 1:
			if (f.variables['time'][1] - f.variables['time'][0]) > 25.0: timeStepType = "monthly"
			if (f.variables['time'][1] - f.variables['time'][0]) > 305.0: timeStepType = "yearly"
		else:	
			timeStepType = "single"

		f.close() 

		if timeStepType == "daily":
			number_of_days = (endTime - startTime).days + 1
			datetime_range = [startTime + datetime.timedelta(days = x) for x in range(0, number_of_days)]
			
		if timeStepType == "monthly":
			number_of_months = calculate_monthdelta(startTime, endTime +  datetime.timedelta(days = 1)) + 1
			datetime_range = [startTime + relativedelta(months =+x) for x in range(0, number_of_months)]
			# make sure that datetime_range values always at the last day of the month:
			for i in range(0, len(datetime_range)):
				year_used  = datetime_range[i].year
				month_used = datetime_range[i].month
				day_used   = calendar.monthrange(year_used, month_used)[1]
				datetime_range[i] = datetime.datetime(int(year_used), int(month_used), int(day_used), 0)
				
		if timeStepType == "yearly":
			number_of_years = endTime.year - startTime.year + 1
			datetime_range = [startTime + relativedelta(years =+x) for x in range(0, number_of_years)]
			# make sure that datetime_range values always at the last day of the year:
			for i in range(0, len(datetime_range)):
				year_used  = datetime_range[i].year
				month_used = 12
				day_used   = 31
				datetime_range[i] = datetime.datetime(int(year_used), int(month_used), int(day_used), 0)

		if timeStepType == "single":
			datetime_range = [startTime]
		
		# time variables that will be used (using numerical values)
		uniqueTimes = nc.date2num(datetime_range, time_units, time_calendar)
		
		print timeStepType
		print datetime_range
		print uniqueTimes
	
	for ncFile in netCDFInput.values():

		# open netCDF file
		if ncFile in filecache.keys():
			rootgrp = filecache[ncFile]
			print "Cached: ", ncFile
		else:
			rootgrp = nc.Dataset(ncFile)
			filecache[ncFile] = rootgrp
			print "New: ", ncFile

		# and get index
		index = netCDFInput.keys()[netCDFInput.values().index(ncFile)]

		# retrieve dimensions,  atributes, variables, and missing value
		dimensions[index]= rootgrp.dimensions.copy()
		variables[index]=  rootgrp.variables.copy()
		attributes[index]= rootgrp.__dict__.copy()
	
		#-set new values
		for key in dimensions[index].keys():
			if 'lat' in key.lower():
				latVar= key
			if 'lon' in key.lower():
				lonVar= key
		latMin= getMin(latMin,variables[index][latVar][:])
		latMax= getMax(latMax,variables[index][latVar][:])
		lonMin= getMin(lonMin,variables[index][lonVar][:])
		lonMax= getMax(lonMax,variables[index][lonVar][:])
	
		#-assign calendar (used)
		if 'time' in  variables[index].keys():
			for name in variables[index]['time'].ncattrs():
				if name not in calendar_used.keys():
					calendar_used[name]= getattr(variables[index]['time'],name)
				else:
					if getattr(variables[index]['time'],name) != calendar_used[name]:
						rootgrp.close()
						sys.exit('calendars are incompatible')
			#-time
			if uniqueTimes.size == 0:
				uniqueTimes= variables[index]['time'][:]
			#~ else:
				#~ uniqueTimes= np.unique(np.c_[uniqueTimes[:],variables[index]['time'][:]])
			uniqueTimes.sort()
		keys= variables[index].keys()
		for key in dimensions[index].keys():
			if key in keys:
				keys.remove(key)
		key= keys[0]
		if variableName == None:
			variableName= key
		else:
			if key <> variableName:
				rootgrp.close()
				sys.exit('variables are incompatible')
		#-Missing Value
		MV = rootgrp.variables[key]._FillValue
		varUnits = rootgrp.variables[variableName].units
		#-close file 
		rootgrp.close()
	
	#-create output netCDF
	#~ longitudes= np.around(np.arange(lonMin,lonMax+deltaLon,deltaLon), decimals=4)
	#~ latitudes=  np.around(np.arange(latMax,latMin-deltaLat,-deltaLat), decimals=4)

	longitudes= np.arange(lonMin,lonMax+deltaLon,deltaLon)
	latitudes=  np.arange(latMax,latMin-deltaLat,-deltaLat)

	#~ longitudes= np.linspace(lonMin,lonMax+deltaLon, int(round((lonMax+deltaLon - lonMin)/deltaLon)))
	#~ latitudes=  np.linspace(latMax,latMin-deltaLat, int(round((latMax - latMin+deltaLat)/deltaLat)))

	uniqueTimes= uniqueTimes.tolist()
	#-open file
	rootgrp= nc.Dataset(netCDFOutput,'w',format= ncFormat)
	#-create dimensions for longitudes and latitudes
	rootgrp.createDimension('latitude',len(latitudes))
	rootgrp.createDimension('longitude',len(longitudes))
	lat= rootgrp.createVariable('latitude','f4',('latitude'))
	lat.standard_name= 'Latitude'
	lat.long_name= 'Latitude cell centres'
	lon= rootgrp.createVariable('longitude','f4',('longitude'))
	lon.standard_name= 'Longitude'
	lon.long_name= 'Longitude cell centres'
	#-assing latitudes and longitudes to variables
	lat[:]= latitudes
	lon[:]= longitudes  

	latitudes = np.around(latitudes, decimals=4)   # TODO: Improve this. We need this one for selecting rows and columns.
	longitudes = np.around(longitudes, decimals=4) # TODO: Improve this. We need this one for selecting rows and columns. 
    
	# - create time and set its attributes
	date_time=rootgrp.createDimension('time',len(uniqueTimes))
	#~ date_time=rootgrp.createDimension('time', None)
	date_time= rootgrp.createVariable('time','f8',('time',))
	for attr,value in calendar_used.iteritems():
		setattr(date_time,attr,str(value))
	date_time[:]= uniqueTimes

	# - setting variable
	if len(calendar_used) == 0:
		varStructure= ('latitude','longitude')  
	else:
		varStructure= ('time','latitude','longitude')  

	variable = rootgrp.createVariable(variableName, 'f4', varStructure, fill_value = MV, zlib = using_zlib)

	# - set variable attributes and overall values
	for index in attributes.keys():
		for name in variables[index][variableName].ncattrs():
			try:
				setattr(variable,name,str(getattr(variables[index][variableName],name)))
			except:
				pass
		for attr,value in attributes[index].iteritems():
			setattr(rootgrp,attr,str(value)) 
	
	#-write to file
	rootgrp.sync()
	rootgrp.close()
	
	#NOTE: this assumes it is a timed variable!
	#-iterate over time steps and retrieve values
	
	print 'nr of time steps = %s, nr of files = %s ' % (len(uniqueTimes), len(netCDFInput))
	i_time = 0
	for time in uniqueTimes[:]:

		
		#~ print 'processing %s for time index %.0d' %(ncName, 1+ time - min(uniqueTimes))
		#~ print 'processing %s for time %.0d' %(ncName, time)

		i_time = i_time + 1
		print 'processing %s %i from %i' %(ncName, i_time, len(uniqueTimes))
		
		#-create empty field to fill
		variableArray= np.ones((len(latitudes),len(longitudes)))*MV
		
		#-iterate over input netCDFs
		for ncFile in netCDFInput.values():
			#-open netCDF file and get dictionary index
			rootgrp= nc.Dataset(ncFile,'r',format= ncFormat)
			index= netCDFInput.keys()[netCDFInput.values().index(ncFile)]
			#-retrieve posCnt and process
			#-get row and column indices from lats and lons
			for key in dimensions[index].keys():
				if 'lat' in key.lower():
					latVar= key
				if 'lon' in key.lower():
					lonVar= key
			latMaxNcFile = round(getMax(latMin,variables[index][latVar][:]),4)
			latMinNcFile = round(getMin(latMax,variables[index][latVar][:]),4)
			lonMinNcFile = round(getMin(lonMax,variables[index][lonVar][:]),4)
			lonMaxNcFile = round(getMax(lonMin,variables[index][lonVar][:]),4)

			row0=  np.where(latitudes == min(latMax,latMaxNcFile))[0][0]
			row1=  np.where(latitudes == max(latMin,latMinNcFile))[0][0]+1
			col0= np.where(longitudes == max(lonMin,lonMinNcFile))[0][0]
			col1= np.where(longitudes == min(lonMax,lonMaxNcFile))[0][0]+1

			posCnt= None
			try:
				
				#~ # find the correct index (old method) - this is very slow
				#~ posCnt= variables[index]['time'][:].tolist().index(time)
				
				# find the correct index (new method)
				date_value = nc.num2date(time, rootgrp.variables['time'].units, rootgrp.variables['time'].calendar)
				posCnt = nc.date2index(date_value, rootgrp.variables['time'])
				
				sampleArray= rootgrp.variables[variableName][posCnt,:,:]
				sampleArray[sampleArray == variables[index][variableName]._FillValue]= MV
				variableArray[row0:row1,col0:col1][variableArray[row0:row1,col0:col1] == MV]= \
					sampleArray[variableArray[row0:row1,col0:col1] == MV]

				print 'time is present :' + str(date_value)

			except:
				if posCnt == None:
					print 'time not present'
				else:
					print 'error  in resampled'
			#-close
			rootgrp.close()
	
		#-write array to destination netCDF
		posCnt= uniqueTimes.index(time)
		rootgrp= nc.Dataset(netCDFOutput,'a',format= ncFormat)
		rootgrp.variables[variableName][posCnt,:,:]= variableArray
		variable.units = str(varUnits)
		rootgrp.sync()
		rootgrp.close()
	
	secs = int(tm.time() - scriptStartTime)
	print "Processing %s took %s hh:mm:ss\n" % (ncName, str(datetime.timedelta(seconds=secs)))


##################################
######## user input ##############
##################################

# latitudes and longitudes:
deltaLat        = 5.0/60.0
deltaLon        = 5.0/60.0
latMin          =  -90 + deltaLat / 2
latMax		    =   90 - deltaLat / 2
lonMin          = -180 + deltaLon / 2
lonMax          =  180 - deltaLon / 2

# input directory:
inputDirRoot = sys.argv[1] 

outputDir    = sys.argv[2]

# making outputDir
try:
	os.makedirs(outputDir)
except:
	pass	

# file_type, options are: outDailyTot, outMonthTot, outMonthAvg, outMonthEnd, outAnnuaTot, outAnnuaAvg, outAnnuaEnd
file_type  = str(sys.argv[3])

# starting and end dates
startDate  = str(sys.argv[4]) 
endDate    = str(sys.argv[5])

# list of netcdf files that will be merged:
netcdfList = str(sys.argv[6])
print netcdfList
netcdfList = list(set(netcdfList.split(",")))
if file_type == "outDailyTotNC": netcdfList = ['%s_dailyTot_output.nc'%var for var in netcdfList]
if file_type == "outMonthTotNC": netcdfList = ['%s_monthTot_output.nc'%var for var in netcdfList]
if file_type == "outMonthAvgNC": netcdfList = ['%s_monthAvg_output.nc'%var for var in netcdfList]
if file_type == "outMonthEndNC": netcdfList = ['%s_monthEnd_output.nc'%var for var in netcdfList]
if file_type == "outAnnuaTotNC": netcdfList = ['%s_annuaTot_output.nc'%var for var in netcdfList]
if file_type == "outAnnuaAvgNC": netcdfList = ['%s_annuaAvg_output.nc'%var for var in netcdfList]
if file_type == "outAnnuaEndNC": netcdfList = ['%s_annuaEnd_output.nc'%var for var in netcdfList]

if file_type == "outMonthMaxNC": netcdfList = ['%s_monthMax_output.nc'%var for var in netcdfList]
if file_type == "outAnnuaMaxNC": netcdfList = ['%s_annuaMax_output.nc'%var for var in netcdfList]

# netcdf format and zlib option:
ncFormat   = str(sys.argv[7])
using_zlib = str(sys.argv[8])

# maximum number of cores that will be used
max_number_of_cores = int(sys.argv[9])

# number of cores that will be used
ncores = min(len(netcdfList), max_number_of_cores)

# clone areas
areas = str(sys.argv[10])
if areas == "Global":
	areas = ['M%02d'%i for i in range(1,54,1)]
else:
    areas = list(set(areas.split(",")))


#~ # for testing, we use only a single core
#~ mergeNetCDF((netcdfList[0], latMin, latMax, lonMin, lonMax, deltaLat, deltaLon, startDate, endDate, ncFormat, using_zlib))

ll = []
for ncName in netcdfList:
	ll.append((ncName, latMin, latMax, lonMin, lonMax, deltaLat, deltaLon, startDate, endDate, ncFormat, using_zlib))
pool = Pool(processes = ncores)    # start "ncores" of worker processes
pool.map(mergeNetCDF, ll)          # multicore processing

