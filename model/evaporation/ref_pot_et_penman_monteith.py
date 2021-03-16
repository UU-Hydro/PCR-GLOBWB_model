# functions and class to compute the potential evapotranspiration
# using the Penman-Monteith equation following the FAO guidelines
# from FAO irrigation report 56 (Allen et al.,1998)

#-modules
import os
import sys

import pcraster as pcr
import pcraster.framework as pcrm

#~ import shortwave_radiation

#~ from types import NoneType

#~ def get_extraterestrial_shortwave_radiation(\
                                            #~ latitude, solar_declination, \
                                            #~ eccentricity, day_length, solar_constant = 118.1):
#~ 
    #~ extraterestrial_shortwave_radiation = shortwave_radiation.compute_radsw_ext(latitude, solar_declination, \
                                                                                #~ eccentricity, day_length, solar_constant)
    #~ 
    #~ # Note: Unit must be consistent with the unit of solar_constant, if solar_constant = 118.1, the unit is MJ.day**-1.m**-2  
    #~ 
    #~ return extraterestrial_shortwave_radiation

def computeDefaultPressure(elevation):
	'''computeDefaultPressure: function that returns the \
default atmospheric pressure in [Pa] as a function of elevation \
in metres'''
	return 101300*((293-0.0065*elevation)/293)**5.26

def getLatentHeatVaporization(temperature):
	'''returns the latent heat of vaporization [J.kg**-1] \
as a function of temperature [degC]'''
	return 2.501E6-2370*temperature

def getSaturatedVapourPressure(temperature):
	'''returns the saturated vapour pressure [Pa] as \
as a function of temperature [degC]'''
	return 611.0*pcr.exp(17.27*temperature/(temperature+237.3))
	# see also https://www.weather.gov/media/epz/wxcalc/vaporPressure.pdf

def getSlopeVapourPressureCurve(temperature,satVapPres):
	'''returns the slope of the saturated vapour pressure curve [Pa.degC**-1]'''
	return (4098.0*satVapPres)/((temperature+237.3)**2)

def getPsychrometricConstant(atmosphericPressure,\
		cpAir,epsilon, latentHeatVaporization):
	'''returns the psychrometric constant [Pa.degC**-1]'''
	return (cpAir*atmosphericPressure)/(epsilon*latentHeatVaporization)

def getLongWaveRadiation(temperature, eAct, radFrac= 1.00, relativeHumidity = None):
	'''getLongWaveRadiation: returns the longwave radiation [W.m**-2] \
according to FAO guidelines.

	Input:
	temperature:          temperature [degC]
	eAct:                 actual vapour pressure [Pa]
	radFrac:              fraction incoming shortwave radiation [-]

	Output:
	longWaveRadiation:    longwave radiation [W.m**-2]

'''
	# Stefan-Boltzmann constant for emission of longwave radiaton [W.m**-2.K**-4]
	sigma= 5.67E-8
	# constants according to FAO to correct net longwave radiation for vapour pressure
	ea0= 0.34
	eaFactor= 4.43e-3
	#-constants, slope and range to convert radiation according to FAO
	radCon= 0.25
	radSlope= 0.50
	radDif= 0.35
	radCor= (1+radDif)/(radCon+radSlope)
	
	# estimate actual vapor pressure based on relativeHumidity
	if eAct is None:
		satVapPressure = getSaturatedVapourPressure(temperature)
		eAct = relativeHumidity * satVapPressure

	#-longwave radiation
	return sigma*(temperature+273.15)**4*pcr.max(0,ea0-eaFactor*eAct**0.5)*\
		pcr.max(0,(pcr.min(1+radDif,radCor*radFrac)-radDif))

def getShortWaveRadiationFraction(cloudiness):
	'''getShortWaveRadiationFraction: returns the fraction of \
shortwave radiation [-] that reaches the surface unimpeded by \
as a function of cloudiness according to FAO guidelines.

  Input:
  cloudiness:          cloud cover [-]

	Output:
  radiationFraction:   fraction shortwave radiation [-]
\n'''
	#-table with fraction sunshine hours as function of the cloudiness (Puit & Doornbos)
	sunFracTBL= {0: 0.95, 1: 0.85, 2: 0.80, 3: 0.75, 4: 0.65, 5: 0.55,\
		6: 0.50, 7: 0.40, 8: 0.30, 9: 0.15, 10: 0.05, 11: 0.00}
	#-constants, slope and range to convert radiation according to FAO
	radCon= 0.25
	radSlope= 0.50
	radDif= 0.35
	radCor= (1+radDif)/(radCon+radSlope)
	#-sunshine fraction
	cld1= pcr.roundoff(10.0*cloudiness+0.5)
	cld0= cld1-1
	sun0= pcr.scalar(0)
	deltaSun= pcr.scalar(0)
	keys= sunFracTBL.keys()
	keys.sort(reverse= True)
	for key in keys:
		sun0= pcr.ifthenelse(cld0 == key, sunFracTBL[key],sun0)
		deltaSun= pcr.ifthenelse(cld1 == key, sunFracTBL[key],deltaSun)
	deltaSun= (deltaSun-sun0)/(cld1-cld0)
	sunFrac= sun0+(10*cloudiness-cld0)*deltaSun
	#-fraction shortwave radiation
	return pcr.min(1.0,pcr.max(0.0,\
		radCon+radSlope*sunFrac))

def updateShortWaveRadiation(shortWaveRadiation, albedo= 0.00,\
	fraction= 1.00):
	'''returns the net shortwave radiation'''
	return (1-albedo)*fraction*shortWaveRadiation

class penmanMonteithET(pcrm.StaticModel):
	"""Class with the Penman-Monteith equation for potential evaporation. \
Constants are set in the init section and can override default values.

\n"""

	def __init__(self,\
		cpAir = 1004, epsilon = 0.622, rhoAir = 1.2047,\
		windHeight = 2.00, temperatureHeight= 2.00,\
		albedo= 0.23, canopyResistance = 70.0, vegetationHeight = 0.12):

		'''Initialization of the penmanMonteithET class with scalar constants \
that are used to calculate the potential evaporation. The following variables \
are included with the following default, constant values:

  cpAir = 1004;  					# specific heat of air at constant P [J/(kg*K)]
  epsilon = 0.622;				# ratio moleculair weight of water
	                        # vapour and dry air [-]
  rhoAir = 1.2047;				# air density [kg.m**-3]
  windHeight = 2.00;			# height open area windspeed [m] above ground
  temperatureHeight= 2.00;# height open area temperature measurements
	                        # [m] above ground
	albedo= 0.23;           # albedo [-] for FAO reference crop (grass)
	canopyResistance = 70.0;# canopy resistance [s.m**-1] for FAO reference crop
	vegetationHeight = 0.12;# vegetation height [m] for FAO reference crop

	'''
		pcrm.StaticModel.__init__(self)
		#-missing value
		self.MV= -999.9
		#-constants
		# Karman constant [-]
		self.karmanConst = 0.41
		self.cpAir= cpAir
		self.epsilon= epsilon
		self.rhoAir= rhoAir
		self.rhoWater= 1000.
		self.windHeight= windHeight
		self.temperatureHeight= temperatureHeight
		self.albedo= albedo
		self.canopyResistance= canopyResistance
		self.vegetationHeight= vegetationHeight

    #-initialize potential evapotranspiration
		self.potentialEvaporation= pcr.ifthen(pcr.scalar(0) == pcr.scalar(1),pcr.scalar(self.MV))

	def initial(self):
		pass

	def setDefaultAtmosphericPressure(self,elevation):
		'''sets the default atmospheric pressure as function of elevation [m]'''
		self.atmosphericPressure= computeDefaultPressure(pcr.cover(elevation,0))

	def updateSurfaceProperties(self,\
		albedo, vegetationHeight, canopyResistance):
		'''updates the surface properties: albedo, vegetation height and canopyResistance'''
		self.albedo= albedo
		self.canopyResistance= canopyResistance
		self.vegetationHeight= vegetationHeight

	def updatePotentialEvaporation(self,\
			netRadiation, airTemperature, windSpeed, atmosphericPressure,\
			unsatVapPressure= None, relativeHumidity= None,\
			timeStepLength= 86400):
		'''updates the potential evaporation on the basis of the meteorological \
variables provided (note: either relative humidity or the actual vapour pressure \
must be provided; the latter takes precedence):

	Input:
	netRadiation:         net incoming radiation [W.m**-2], incoming positive
	airTemperature:       air temperature [degC]
	windSpeed:            wind speed [m.s**-1]
	unsatVapPressure:     actual vapour pressure [Pa]
	relativeHumidity:     relative humidity [-]
	timeStepLength:       length of the time step [seconds], default one day (86400 sec)

	Output:
	potentialEvaporation: potential evaporation, returned in [m] waterslice over timestep length

\n'''

		#-set constants & properties
		latentHeatVaporization= getLatentHeatVaporization(airTemperature)
		satVapPressure= getSaturatedVapourPressure(airTemperature)
		# slope of sat vap pressure curve [Pa.degC**-1]
		delta= getSlopeVapourPressureCurve(airTemperature,satVapPressure)
		# psychrometric constant [Pa.degC**-1]
		gamma= getPsychrometricConstant(atmosphericPressure,self.cpAir,\
			self.epsilon,latentHeatVaporization)
		#-aerodynamic resistance
		# zero plane displacement, roughness height for momentum and heat and vapour transfer
		Zd= 2./3.*self.vegetationHeight
		Z0m= 0.123*self.vegetationHeight
		Z0h= 0.1*Z0m
		raTerm= pcr.ln((self.windHeight-Zd)/(Z0m))*\
			pcr.ln((self.temperatureHeight-Zd)/(Z0h))*(self.karmanConst)**-2

		# atmospheric resistance [s.m**-1]
		self.atmosphericResistance= raTerm/pcr.max(1.e-3,windSpeed)

		#-weighing of radiation and mass transfer term [Pa.J.degC**-1*kg**-1]
		dGLv = (delta+gamma*(1+self.canopyResistance/self.atmosphericResistance))*latentHeatVaporization

		#-decide on actual vapour pressure [Pa]
		#~ if not isinstance(unsatVapPressure, NoneType):
		if unsatVapPressure is not None:
			pass
		#~ elif not isinstance(relativeHumidity, NoneType):
		elif relativeHumidity is not None:
			unsatVapPressure= relativeHumidity*satVapPressure
		else:
			sys.exit(' * Halted: either relative humidity or actual vapour pressure should be defined')
		#-aerodynamic evaporation rate [m.s**-1]
		atmosphericContribution= self.rhoAir*self.cpAir*\
			(satVapPressure-unsatVapPressure)/(self.atmosphericResistance*self.rhoWater*dGLv)
		#-radiation contribution [m.s**-1]
		radiationContribution= delta*netRadiation/(dGLv*self.rhoWater)
		#-total potential evapotranspiration over time step length
		self.potentialEvaporation= pcr.max(0.,\
			atmosphericContribution+radiationContribution)*timeStepLength

##		pcr.report(raTerm,os.path.join('output','raterm.map'))
##		pcr.report(self.atmosphericResistance,os.path.join('output','ra.map'))
##		pcr.report(delta,os.path.join('output','delta.map'))
##		pcr.report(gamma,os.path.join('output','gamma.map'))
##		pcr.report(latentHeatVaporization,os.path.join('output','lv.map'))
##		pcr.report(dGLv,os.path.join('output','dglv.map'))

		#-return potential evaporation
		return self.potentialEvaporation

# /*** end of class definition ***/

def main():
	'''test of penman monteith potential evaporation'''
	#-init
	inputPath= 'input'
	outputPath= 'output'
	cloneMapFileName= os.path.join(inputPath,'globalclone.map')
	demFileName= os.path.join(inputPath,'globaldem.map')
	months= range(1,13)
	cloudinessFileRoot= os.path.join(inputPath,'ccldavg')
	temperatureFileRoot= os.path.join(inputPath,'ctmpavg')
	vapourPressureFileRoot= os.path.join(inputPath,'cvapavg')
	shortWaveRadiationFileRoot= os.path.join(inputPath,'maxrad')
	windSpeedFileRoot= os.path.join(inputPath,'cwndclm')

	#-start
	#-initialize clone map
	pcr.setclone(cloneMapFileName)
	#-set output map
	if not os.path.isdir(outputPath): os.makedirs(outputPath)
	#-set class
	penMonModel=penmanMonteithET(windHeight= 10.0)
	#-initialize atmospheric pressure
	penMonModel.setDefaultAtmosphericPressure(pcr.readmap(demFileName))
	pcr.report(penMonModel.atmosphericPressure,\
		os.path.join(outputPath,'atmosphericpressure.map'))
	#-iterate over months
	for month in months:
		msg = 'processing month %2d' % month
		print(msg)
		#-read files
		cloudiness= 0.001*pcr.readmap(pcrm.generateNameT(cloudinessFileRoot,month))
		temperature= 0.1*pcr.readmap(pcrm.generateNameT(temperatureFileRoot,month))
		vapourPressure= 10.*pcr.readmap(pcrm.generateNameT(vapourPressureFileRoot,month))
		shortWaveRadiation= pcr.readmap(pcrm.generateNameT(shortWaveRadiationFileRoot,month))
		windSpeed= pcr.readmap(pcrm.generateNameT(windSpeedFileRoot,month))
		#-compute fraction short- and longwave radiation
		fractionShortWaveRadiation= getShortWaveRadiationFraction(cloudiness)
		shortWaveRadiation= updateShortWaveRadiation(shortWaveRadiation,penMonModel.albedo,fractionShortWaveRadiation)
		longWaveRadiation= getLongWaveRadiation(temperature,vapourPressure,fractionShortWaveRadiation)
		pcr.report(shortWaveRadiation,os.path.join(outputPath,pcrm.generateNameT('rads',month)))
		pcr.report(longWaveRadiation, os.path.join(outputPath,pcrm.generateNameT('radl',month)))
		#-compute evaporation
		penMonModel.updatePotentialEvaporation(pcr.max(0,shortWaveRadiation-longWaveRadiation),\
			temperature,windSpeed,penMonModel.atmosphericPressure,\
			unsatVapPressure=vapourPressure)
		pcr.report(penMonModel.potentialEvaporation,\
			os.path.join(outputPath,pcrm.generateNameT('etpot',month)))

if __name__ == "__main__":
	print(main.__doc__)
	main()

