
import os, sys, shutil, math, calendar, datetime, tarfile, zlib, zipfile

import numpy as np
import pcraster as pcr
from pcraster import pcr2numpy
import pcraster.framework as pcrm
from pcraster.framework import generateNameT

import rens_modules 
from rens_modules.pcrParameterization import pcrObject
from rens_modules.spatialDataSet2PCR import spatialAttributes
from rens_modules.convert2NetCDF import *
# TODO: replace/remove all of rens modules

from potentialET_PenmanMonteith import *
import virtualOS as vos


#-functions
def createOutputDirs(DirList):
	#creates empty output directories
	for DirOut in DirList:
		if os.path.exists(DirOut):
			for Root, Dirs, Files in os.walk(DirOut):
				for File in Files:
					FileName= os.path.join(Root,File)
					try:
						os.remove(FileName)
					except:
						pass
		else:
			os.mkdir(DirOut)

# Computes the potential reference potential evaporation from information from the ERA-Interim
# * initialization *
MV= -999.9

#-maps

#~ cloneMap = '/data/hydroworld/PCRGLOBWB20/input30min/global/Global_CloneMap_30min.map'
cloneMap    = 'clone_tanzania_30min/clone.map'


#-years and number of runs to initialize the model
startDate  = datetime.datetime(2000, 1,1)
endDate    = datetime.datetime(2000,12,1)


scratchDir = 'scratch'
scratchDir = '/scratch-shared/edwinhs/process_pm/tmp/'


ncData= {}

#~ edwinhs@tcn1072.bullx:/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-03-12_test-edwin-only-2000/era5-land/half_arcdeg$ ls -lah */*month*
#~ -rw-r--r-- 1 edwinhs edwinhs 83K Mar 18 23:21 tanzania_era5-land_10winds-avg_2000-2000/tanzania_era5-land_10winds-avg_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_d2m-average_2000-2000/tanzania_era5-land_d2m-average_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_d2m-maximum_2000-2000/tanzania_era5-land_d2m-maximum_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_d2m-minimum_2000-2000/tanzania_era5-land_d2m-minimum_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_fal-average_2000-2000/tanzania_era5-land_fal-average_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_spressu-avg_2000-2000/tanzania_era5-land_spressu-avg_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_ssr-average_2000-2000/tanzania_era5-land_ssr-average_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_t2m-average_2000-2000/tanzania_era5-land_t2m-average_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_t2m-maximum_2000-2000/tanzania_era5-land_t2m-maximum_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_t2m-minimum_2000-2000/tanzania_era5-land_t2m-minimum_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_total-preci_2000-2000/tanzania_era5-land_total-preci_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_u10-average_2000-2000/tanzania_era5-land_u10-average_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -r--r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_v10-average_2000-2000/tanzania_era5-land_v10-average_2000-2000_rempacon-30-arcmin_monthly.nc

main_input_netcdf_dir = '/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-03-12_test-edwin-only-2000/era5-land/half_arcdeg/input_to_pm_model'

# - 2 metre air temperature, unit: K
variableName = 'tavg'    # 2 metre temperature var167
ncData[variableName] = {}
ncData[variableName]['varCode']     = 't2m' # 'var167'
ncData[variableName]['fileName']    = os.path.join(main_input_netcdf_dir, "tanzania_era5-land_t2m-average_2000-2000_rempacon-30-arcmin_monthly.nc") 
ncData[variableName]['fileRoot']    = os.path.join(scratchDir, 'tavg')

# - 2 metre dew temperature, unit: K
variableName = 'tdew'   # dewpoint temperature var168
ncData[variableName] = {}
ncData[variableName]['varCode']     = 'd2m' # 'var168'
ncData[variableName]['fileName']    = os.path.join(main_input_netcdf_dir, "tanzania_era5-land_d2m-average_2000-2000_rempacon-30-arcmin_monthly.nc")
ncData[variableName]['fileRoot']= os.path.join(scratchDir, 'tdew')

# - 10 m wind speed, unit: m.s-1
variableName = 'si10'                 # 10 m wind speed var207
ncData[variableName] = {}
ncData[variableName]['varCode']     = '10m-wind-speed' 'var207'
ncData[variableName]['fileName']    = os.path.join(main_input_netcdf_dir, "tanzania_era5-land_10winds-avg_2000-2000_rempacon-30-arcmin_monthly.nc")
ncData[variableName]['fileRoot']    = os.path.join(scratchDir, 'wind')

# - surface solar radiation, unit: J.m-2.day-1
variableName= 'ssr'  # surface solar radiation var176
ncData[variableName] = {}
ncData[variableName]['varCode']     = 'ssr' # 'var176'
ncData[variableName]['fileName']    = os.path.join(main_input_netcdf_dir, "tanzania_era5-land_ssr-average_2000-2000_rempacon-30-arcmin_monthly.nc")
ncData[variableName]['fileRoot']    = os.path.join(scratchDir, 'rads')

# - surface pressure, unit: Pa
variableName = 'sp'        # surface pressure var134
ncData[variableName] = {}
ncData[variableName]['varCode']     = 'sp'  # 'var134'
ncData[variableName]['fileName']    = os.path.join(main_input_netcdf_dir, "tanzania_era5-land_spressu-avg_2000-2000_rempacon-30-arcmin_monthly.nc")
ncData[variableName]['fileRoot']    = os.path.join(scratchDir, 'patm')

# - albedo, unit: dimensionless
variableName = 'al' # forecast albedo var243
ncData[variableName] = {}
ncData[variableName]['varCode']     = 'fal' # 'var243'
ncData[variableName]['fileName']    = os.path.join(main_input_netcdf_dir, "tanzania_era5-land_fal-average_2000-2000_rempacon-30-arcmin_monthly.nc")
ncData[variableName]['fileRoot']    = os.path.join(scratchDir, 'albedo')

# - fraction maximum incoming radiation
#~ maxRadFileRoot = '/home/beek0120/PCRGLOBWB/ERA_I/ProcessEpot/maxrad/maxrad'
maxRadFileRoot    = 'maxrad/maxrad'


ncAttributes = {'title': 'Monthly_potential_reference_evaporation_computed_from_ERA-Interim_according_to_FAO_guidelines_over_the_period_1979-1979'}
ncAttributes = {'title': 'Monthly_potential_reference_evaporation'}
ncOutput = {}
variableName = 'potentialEvaporation'
shortName = 'epot'
ncOutput[variableName] = {}
ncOutput[variableName]['fileName'] = '/scratch-shared/edwinhs/process_pm/out/test.nc'
ncOutput[variableName]['units']    = 'm*day**-1'
ncOutput[variableName]['fileRoot'] = os.path.join(scratchDir, shortName)


# start

# set clone and obtain attributes
pcr.setclone(cloneMap)
cloneSpatialAttributes = spatialAttributes(cloneMap)

#-create scratch
if not os.path.isdir(scratchDir): os.makedirs(scratchDir)

#-initialize output netCDF files
#-get coordinates
latitudes=  pcr2numpy(pcr.ycoordinate(pcr.boolean(1)),MV)[:,0].ravel()
longitudes= pcr2numpy(pcr.xcoordinate(pcr.boolean(1)),MV)[0,:].ravel()
#-start simulation, set posCnt for netCDF generation and run counter
posCnt= 0
runCnt= 0
#-initialize files
for variableName in ncOutput.keys():
	createNetCDF(ncOutput[variableName]['fileName'],longitudes,latitudes,timedData= True,attributes= ncAttributes)
posCnt= 0

#-set class
penMonModel=penmanMonteithET(windHeight= 10.0)

#-iterate over dates
date= startDate
while date <= endDate:
	print 'computing monthly potential evaporation for %s' % date
	#-update time
	numberDays= calendar.monthrange(date.year,date.month)[1]
	dynamicIncrement= 1
	#-retrieve input files
	for variableName in ncData.keys():
		print '   extracting %s' % variableName
		pcrDataSet= pcrObject(ncData[variableName]['varCode'], ncData[variableName]['fileRoot'],\
			ncData[variableName]['fileName'],cloneSpatialAttributes, pcrVALUESCALE= pcr.Scalar, resamplingAllowed= True,\
				dynamic= True, dynamicStart= date, dynamicEnd= date, dynamicIncrement= dynamicIncrement, ncDynamicDimension= 'time')
		validProcessInfo= pcrDataSet.initializeFileInfo()
		pcrDataSet.processFileInfo()

	#-read information and process

	# obtain shortwave radiation [J.day**-1.m**-2 => W.m**-2]
	albedo= pcr.readmap(generateNameT(ncData['al']['fileRoot'],1))
	shortWaveRadiation= pcr.readmap(generateNameT(ncData['ssr']['fileRoot'],1))/(1-albedo)
	shortWaveRadiation/= 86400*2

	#~ maxRad = pcr.readmap(generateNameT(maxRadFileRoot,date.month))
	maxRad_file_name = generateNameT(maxRadFileRoot, date.month)
	maxRad = vos.readPCRmapClone(v = maxRad_file_name, 
	                             cloneMapFileName = cloneMap, 
	                             tmpDir = os.path.join(scratchDir, 'maxrad'))

	fractionShortWaveRadiation= pcr.cover(pcr.min(1,shortWaveRadiation/maxRad),0)

	# obtain average temperature [degC]
	airTemperature= pcr.readmap(generateNameT(ncData['tavg']['fileRoot'],1)) -273.15

	# compute vapour pressure
	dewPointTemperature= pcr.readmap(generateNameT(ncData['tdew']['fileRoot'],1)) -273.15
	vapourPressure= getSaturatedVapourPressure(dewPointTemperature)

	# longwave radiation [W.m**-2]
	longWaveRadiation= getLongWaveRadiation(airTemperature,vapourPressure,fractionShortWaveRadiation)

	# atmospheric pressure [Pa]
	atmosphericPressure= pcr.readmap(generateNameT(ncData['sp']['fileRoot'],1))

	# wind speed [m.s*-1]
	windSpeed= pcr.readmap(generateNameT(ncData['si10']['fileRoot'],1))

	# potential evaporation [m.day**-1]
	variableName= 'potentialEvaporation'
	penMonModel.updatePotentialEvaporation(pcr.max(0,shortWaveRadiation-longWaveRadiation),\
		airTemperature,windSpeed,atmosphericPressure,\
		unsatVapPressure=vapourPressure)

	oFile= generateNameT(ncOutput[variableName]['fileRoot'],date.month)
	pcr.report(penMonModel.potentialEvaporation,oFile)
	variableArray= pcr2numpy(penMonModel.potentialEvaporation,MV)
	for variableName in ncOutput.keys():
		data2NetCDF(ncOutput[variableName]['fileName'],variableName,{'units': ncOutput[variableName]['units']},variableArray,posCnt,date,MV)
	posCnt+= 1
	date+= datetime.timedelta(numberDays)

#-all done
print 'all done!'	
