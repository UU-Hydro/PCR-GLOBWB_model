#! /usr/bin/python
#-function to compute the potential evapotranspiration according to Hamon (1963)

import math
import numpy as np
import pcraster as pcr


pcr.setglobaloption('radians')

def potentialETHamon(airT,julianDay,yearLength,latitudeDecimalDegrees,calibrationFactor= 1.0):
	#-returns Hamon potential evapotranspiration in m/day
	#-rhoSat: saturated vapor density (g/m3)
	#-satPressure returns the saturated vapour pressure in mb
	#-dayLength returns the fraction of daylight per 24 hours and is converted to multiples of 12 hours here
	# and tests whether a PCRaster map is passed on or not
	# note that latitude is defined in decimal degrees!
	rhoSat =  216.7 * satPressure (airT) / (airT + 273.15)
	return 1.e-3*0.1651*24./12.*dayLength(julianDay,yearLength,latitudeDecimalDegrees)* rhoSat*calibrationFactor

def dayLength(julianDay,yearLength,latitude,ratioLimitLatitude= 0.99999):
	#-retrurns the fraction of the day length (hours potential sunshine)
	#- convert decimal degrees to radians and compute radiation
	# note: sun stays above/below horizon if -tan(phi)xtan(decl) is less than -1, greater than 1
	thetaArg= -9.99*math.pi
	declination= -23.45*math.pi/180.*math.cos(2.*math.pi*(julianDay+10.)/yearLength)
	if isinstance(latitude,pcr._pcraster.Field):
		latitude*= math.pi/180.
		latitude= pcr.max(pcr.scalar(-0.5*ratioLimitLatitude*math.pi),\
			pcr.min(pcr.scalar(0.5*ratioLimitLatitude*math.pi),latitude))
		thetaArg= pcr.scalar(-pcr.tan(latitude)*pcr.tan(declination))
		thetaArg= pcr.ifthenelse(thetaArg <= -1.,pcr.scalar(math.pi),\
			pcr.ifthenelse(thetaArg >= 1.,pcr.scalar(0.),pcr.scalar(pcr.acos(thetaArg))))
	elif isinstance(latitude,np.ndarray):
		latitude= latitude.copy()
		latitude*= math.pi/180.
		latitude= np.maximum(-0.5*ratioLimitLatitude*math.pi,np.minimum(0.5*ratioLimitLatitude*math.pi,latitude))
		thetaArg= -np.tan(latitude)*np.tan(declination)
		valid= (thetaArg < 1) & (thetaArg > -1)
		mask= thetaArg >= 1
		thetaArg[mask]= 0
		mask= (thetaArg <= -1)
		thetaArg[mask]= math.pi
		thetaArg[valid]= np.arccos(thetaArg[valid])
	else:
		latitude*= math.pi/180.
		latitude= max(-0.5*ratioLimitLatitude*math.pi,min(0.5*ratioLimitLatitude*math.pi,latitude))
		thetaArg= -math.tan(latitude)*math.tan(declination)
		if thetaArg <= -1.:
			thetaArg= math.pi
		elif thetaArg >= 1.:
			thetaArg= 0.
		else:
			thetaArg= math.acos(thetaArg)
	return thetaArg/math.pi

def satPressure(airT):
	#" calculates saturated vapour pressure in mb from air temperature in degrees centigrade
	if isinstance(airT,pcr._pcraster.Field):
		return 6.108*pcr.exp(pcr.ifthenelse(airT>0,\
			17.26939*airT/(airT+237.3),21.87456*airT/(airT+265.5)))
	elif isinstance(airT,np.ndarray):
		eSat= 6.1079*np.exp(17.26939 * airT/(airT + 237.3))
		eSat[airT < 0]= 6.1078*np.exp(21.87456*airT[airT < 0]/(airT[airT < 0]+265.5))
		return eSat
	else:
		if airT >=0 :
				return 6.1078*math.exp(17.26939*airT/(airT+237.3))
		else:
				return 6.1078*math.exp(21.87456*airT/(airT+265.5))

def main():
	#tests Hamon for 50 degrees N, over a normal year, with a constant temperature of 10 degrees
	latitude= 50.0
	airTemperature= 10.0
	nrDays= 365
	for julianDay in xrange(1,nrDays+1):
		print 'day %d with temperature of %.f degrees has %.5f m/day of potential evapotranspiration' %\
			(julianDay,airTemperature,potentialETHamon(airTemperature,julianDay,nrDays,latitude))
			
	multA= np.ones((10,10))
	for julianDay in xrange(1,nrDays+1):
		print 'day %d with temperature of %.f degrees has %.5f m/day of potential evapotranspiration' %\
			(julianDay,airTemperature,potentialETHamon(multA*airTemperature,julianDay,nrDays,multA*latitude)[0,0])
			
			

if __name__ == '__main__':
	main()
