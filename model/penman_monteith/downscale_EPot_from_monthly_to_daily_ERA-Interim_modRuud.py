# downscaleEpot.py
# script to downscale monthly reference potential evaporation to daily values
# using Hamon's method

#-import modules
#-import modules
import os,sys
sys.path.insert(0,'/home/beek0120/PCRGLOBWB/ERA20C/processAnomalies')
import calendar, datetime
import numpy as np
import pcraster as pcr
import ncRecipes as ncR
import potentialET_Hamon as hamonET
import outputNetcdf
from types import NoneType

#-Initalization
MV= -999.9
numberRows= 360
numberCols= 720
latOrigin= 90.0
lonOrigin= -180.0
resolution= 0.5
startYear= 1979
endYear= 2016
cloneMapFileName = "/data/hydroworld/others/Global/Global_CloneMap_30min.map"
ncDailyTemperatureFileName= '/data/hydroworld/basedata/forcing/ERA-Interim-ECMWF/netcdfs/erai_tavg_1979_to_2016_daily.nc' # this data is in Kelvin, but hamonET.potentialETHamon requires Celsius, thus later this is converted to Celsius (line 78)
ncInputVariableName= 'temperature'
ncMonthlyReferencePotentialEvaporationFileName= '/scratch/ruud/ERA-Interim/ERA-Interim_monthly_epot_1979_to_2016.nc'
ncOutputVariableName= 'referencePotET'
ncOutputVariableUnit= 'metre per day (m.day**-1)'
ncDailyReferencePotentialEvaporationFileName= '/scratch/ruud/ERA-Interim/ERA-Interim_daily_epot_1979_to_2016.nc'
selectMode= 'after' #set for dates not centred on midnight
#-netcdf format and attributes for output files:
netcdf_attribute_dictionary = {}
netcdf_attribute_dictionary['institution']  = "Utrecht University, Department of Physical Geography / European Center for Medium-Range Weather Forecasts (RSMC) subcenter = 0"
netcdf_attribute_dictionary['title'      ]  = "Forcing dataset derived ERA-Interim dataset"
netcdf_attribute_dictionary['source'     ]  = "Global Ocean Forecast Model. Monthly temperature, dew-point temperature, net long-wave radiation, net short-wave radiation, wind speed."
netcdf_attribute_dictionary['history'    ]  = "http://www.ecmwf.int/products/data/archive/descriptions/ei/index.html"
netcdf_attribute_dictionary['references' ]  = "None"
netcdf_attribute_dictionary['description']  = "None"
netcdf_attribute_dictionary['comment'    ]  = "Prepared and calculated by Rens van Beek and Ruud van der Ent. "
netcdf_attribute_dictionary['comment'    ] += "The reference evaporation is computed according to FAO56 report, using the Penman-Monteith equation (albedo= 0.20, rs=70 m s-1, z_0m= 0.012 m). "
netcdf_attribute_dictionary['comment'    ] += "Note that the input meteorological variables are used conform FAO 56 with net radiation being scaled for cloudiness and to the reference grass surface "
netcdf_attribute_dictionary['comment'    ] += "and with the longwave radiation being computed from temperature."

#-Start
print ('###DOWNSCALING MONTHLY EVAPORATION TO DAILY VALUES###')
latitudes= np.ones((numberRows,numberCols))
for iCnt in xrange(numberCols):
	latitudes[:,iCnt]= latOrigin-(np.arange(numberRows)+0.5)*resolution
#-initialize netCDF file for output
output= outputNetcdf.OutputNetcdf(cloneMapFileName, netcdf_attribute_dictionary)
output.createNetCDF(ncDailyReferencePotentialEvaporationFileName,\
	ncOutputVariableName,ncOutputVariableUnit)

#-iterate over years and months
#-years
for year in xrange(startYear,endYear+1):
	#-length of year and start day
	yearLength= 365
	if calendar.isleap(year):
		yearLength+= 1
	startDay= 1
	#-months
	for month in xrange(1, 13):
		#-days: get number of days and iterate to compose dates
		# as array and initialize the array holding the daily evaporation
		numberDays= calendar.monthrange(year,month)[1]
		dates= np.zeros((numberDays), dtype= datetime.datetime)
		dailyValue= np.ones((numberDays,numberRows,numberCols))*MV
		ncFileFormat,ncAttributes, ncDimensions, ncVariables= ncR.getNCAttributes(ncDailyTemperatureFileName)
		ncDailyDates= ncR.getNCDates(ncDimensions['time'],ncVariables['time'])
		for dayCnt in xrange(0,numberDays):
			dates[dayCnt]= datetime.datetime(year, month, dayCnt+1)
			posCnt= ncR.getNCDateIndex(dates[dayCnt],ncDailyDates, select= selectMode)
			dailyValue[dayCnt,:,:]= ncR.readField(ncDailyTemperatureFileName,\
				ncInputVariableName,posCnt) - 273.15
			dailyValue[dayCnt,:,:]= hamonET.potentialETHamon(dailyValue[dayCnt,...],\
				startDay+dayCnt,yearLength,latitudes)
		#-get original monthly evaporation
		originalMonthlyValue= np.sum(dailyValue, axis= 0)
		#-get target value
		ncFileFormat, ncAttributes, ncDimensions, ncVariables= ncR.getNCAttributes(ncMonthlyReferencePotentialEvaporationFileName)
		ncMonthlyDates= ncR.getNCDates(ncDimensions['time'],ncVariables['time'], verbose= False)
		posCnt= ncR.getNCDateIndex(dates[0],ncMonthlyDates)
		if isinstance(posCnt,NoneType):
			print '***WARNING: target value not present!***'
			targetMonthlyValue= originalMonthlyValue.copy()
		else:
			targetMonthlyValue= ncR.readField(ncMonthlyReferencePotentialEvaporationFileName, ncOutputVariableName, posCnt)
			targetMonthlyValue*= numberDays
		#-correction factor: multiplicative if the monthly evaporation is larger than 10 mmselectMode
		mask= originalMonthlyValue > 0.01
		correctionFactor= np.ones(mask.shape)
		correctionFactor[mask]= targetMonthlyValue[mask]/originalMonthlyValue[mask]
		for dayCnt in xrange(0,numberDays):
			dailyValue[dayCnt,:,:][mask]*= correctionFactor[mask]
			dailyValue[dayCnt,:,:][mask == False]= targetMonthlyValue[mask == False]/numberDays
		print ' * %04d %02d: correction [-] %4.3f, Hamon ETP-daily [m/month] %6.4f, ERA ETP-monthly [m/month] %6.4f, Corrected ETP-daily [m/month] %6.4f' %\
			(year, month, correctionFactor.mean(), originalMonthlyValue.mean(),targetMonthlyValue.mean(),np.mean(np.sum(dailyValue, axis= 0)))

		#~ pcr.aguila(pcr.numpy2pcr(pcr.Scalar, targetMonthlyValue, -999.9), pcr.numpy2pcr(pcr.Scalar, originalMonthlyValue, -999.9),\
			#~ pcr.numpy2pcr(pcr.Scalar, correctionFactor, -999.9))
			
		#-write output
		for dayCnt in xrange(0,numberDays):
			output.data2NetCDF(ncDailyReferencePotentialEvaporationFileName,\
				ncOutputVariableName,dailyValue[dayCnt,...],dates[dayCnt])
		#-update startDay
		startDay+= numberDays
#-all done
print 'all done'		
		
