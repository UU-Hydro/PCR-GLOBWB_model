import os, sys
import datetime, calendar
import subprocess
import netCDF4 as nc
from types import NoneType

def getNCDates(dates,units,calendar):
	'''Returns the dates based on the information from the netCDF file'''
	dates= nc.num2date(dates,units,calendar)
	return dates

def testValidDate(date1,date2,maxOffset= None,exact= True):
	'''bolds if the absolute difference in dates measured in days exceeds the offset specified'\
 or if the year, month and day are different in case of an exact match'''
	if exact:
		return date1.year == date2.year and date1.month == date2.month and date1.day ==  date2.day
	else:
		if maxOffset == NoneType: maxOffset= 0.5
		return abs(d1-d2) < datetime.timedelta(days= maxOffset)

class pcrObject(object):
	#~ '''Class of a pcraster object required as model input for PCR-GLOBWB V1.0'''
	#-It contains all information to process information including
	# a descriptive variable name, output file , input file -both including  full paths and open for formatting-
	# the bounding box of the grid[(XLL,YLL),(XUR,YUR)], resolution as cellength and
	# the  start date and end date and time increment
	#-uses gdal_translate for any interoperability
	
	def __init__(self,variableName,outputFileName,inputFileName,boundingBox, cellLength,\
			startDate= None,endDate= None, timeIncrement= '', variablePCRType=  'scalar', dynamic= False):
		#-local variables
		outTypes= {'VS_BOOLEAN': 'BYTE', 'VS_NOMINAL': 'INT32',\
			'VS_ORDINAL': 'INT32', 'VS_SCALAR': 'FLOAT32',\
		'VS_DIRECTION': 'FLOAT32' , 'VS_LDD':  'BYTE'}
		timeIncrements= {'': 0., 'hours': 1./24,'days': 1.0}
		#-assign values
		self.variableName= variableName
		self.variablePCRType= 'VS_%s' % variablePCRType.upper()
		self.variableOutType= outTypes[self.variablePCRType]
		self.inputFileName= inputFileName
		self.outputFileName= outputFileName
		self.startDate= startDate
		self.endDate= endDate
		if timeIncrement in timeIncrements.keys():
			self.timeIncrement= timeIncrements[timeIncrement]
		else:
			message= 'time unit %s not defined; perhaps any of' % timeIncrement,
			for key in timeIncrements.keys(): message+= ' %s' % key
			message+= '?'
			sys.exit(message)
		#-test whether the dataset is dynamic or not
		self.dynamic= self.testDynamic(startDate,endDate,timeIncrement)
		self.dynamic= dynamic
		#-get coordinates and resolution
		self.XLL= boundingBox[0][0]
		self.YLL= boundingBox[0][1]
		self.XUR= boundingBox[1][0]
		self.YUR= boundingBox[1][1]
		self.cellLength= cellLength
		self.resampleRatio= 1.

	def __str__(self):
		if self.dynamic:
			message= 'dynamic'
		else:
			message= 'static'
		message+= ' dataset for variable %s' % self.variableName
		return message
		
	def testDynamic(self,*voidarguments):
		pass
	
	def initializeFileInfo(self):
		'''initializes all in and output file names and any corresponding dates'''
		self.fileProcessInfo= {}
		if self.dynamic:
			inputFileName= self.inputFileName
			self.fileProcessInfo[inputFileName]= []
			date= self.startDate
			if os.path.splitext(self.inputFileName)[1] == '.nc' and self.dynamic:
				#-temporal info, include bands
				rootgrp= nc.Dataset(self.inputFileName)
				ncTime= rootgrp.variables.copy()['time']
				dates= getNCDates(ncTime[:],ncTime.getncattr('units'),ncTime.getncattr('calendar'))
				while date <= self.endDate:
					julianDay= date.toordinal()-startDate.toordinal()+1
					dateIndex=nc.date2index(date,ncTime,select= 'nearest')
					if testValidDate(date,dates[dateIndex]):
						band= dateIndex+1
					else:
						band= None
						sys.exit('Input file %s does not contain valid information for %s' % (inputFileName,date))
					outputFileName= self.outputFileName.replace('%JULDAY','%03d' % julianDay)
					if '%YEAR' in outputFileName:
						outputFileName= outputFileName.replace('%YEAR','%04d' % date.year)
					self.fileProcessInfo[self.inputFileName].append((band,outputFileName))
					date+= datetime.timedelta(self.timeIncrement)
				rootgrp.close()			
		else:
			band= 0
			self.fileProcessInfo[self.inputFileName]= []
			self.fileProcessInfo[self.inputFileName].append((band,self.outputFileName))

	def processFileInfo(self):
		'''Reads in entries from the fileProcessInfo dictionary and generates all maps accordingly'''
		for inputFileName, fileInfo in self.fileProcessInfo.iteritems():
			for band, outputFileName in fileInfo:
				if isinstance(band,NoneType):
					sys.exit('')
				if not os.path.exists(os.path.split(outputFileName)[0]):  os.makedirs(os.path.split(outputFileName)[0])
				command= 'gdal_translate -ot %s -of PCRaster #band# -mo VALUE_SCALE=%s  -projwin %f %f %f %f -outsize %s %s %s %s ' %\
					(self.variableOutType,self.variablePCRType, self.XLL,self.YUR,self.XUR, self.YLL,\
						'%.3f%s' % (100.*self.resampleRatio,'%'),'%.3f%s' % (100.*self.resampleRatio,'%'),inputFileName,outputFileName)
				if band > 0:
					command= command.replace('#band#','-b %d' % band)
				else:
					command= command.replace('#band#','')
				subprocess.call(command,stdout= subprocess.PIPE,stderr= subprocess.PIPE,shell= True)

#-initialization
#-spatial attributes: bounding box and celllength
domainName= 'RhineMeuse_2.0'
boundingBox= [(3.5000000,  46.0000000), (  12.0000000,  52.5000000)]
#~ domainName=  'Columbia_2.0'
#~ boundingBox= [(-124.0000000,  41.0000000),(-109.0000000,  53.0000000)]
cellLength= 0.5

hydroworldPath = '/data/hydroworld/PCRGLOBWB20/input30min'

#~ initialPath = '/scratch/edwin/debug30min/global_2.0_initial_conditions/states'
#~ initialPath = ' /scratch/edwin/debug30min_after18Feb2014/python/global_2.0_initial_conditions/states'
initialPath = '/scratch/edwin/hyper_hydro_output/Rhine/RhineMeuse30min/states/'

#~ sourcePath= '/scratch/edwin/debug30min'
sourcePath = '/scratch/edwin/debug30min_after18Feb2014/python' # for forcing
targetPath = '/scratch/edwin/debug30min_after18Feb2014/oldcalc'

startDate = datetime.datetime(2000,1,1)
endDate   = datetime.datetime(2000,12,31)

#-land cover keys
landCoverKeys= {'forest': 'tall', 'grassland': 'short'}

#-dynamic datasets 
dynamicVariables = {}
dynamicDataSets= {}
dynamic= True
#-add temperature, rainfall and reference potential evapotranspiration
dynamicDataSets['temperature']= pcrObject('temperature',\
	os.path.join(targetPath,domainName,'meteo%YEAR','ta000000.%JULDAY'),\
	os.path.join(sourcePath,domainName,'netcdf','temperature_dailyTot.nc'),\
	boundingBox,cellLength,startDate,endDate,'days','scalar',dynamic)
dynamicDataSets['precipitation']= pcrObject('precipitation',\
	os.path.join(targetPath,domainName,'meteo%YEAR','ra000000.%JULDAY'),\
	os.path.join(sourcePath,domainName,'netcdf','precipitation_dailyTot.nc'),\
	boundingBox,cellLength,startDate,endDate,'days','scalar',dynamic)
dynamicDataSets['potentialEvapotranspiration']= pcrObject('potentialEvapotranspiration',\
	os.path.join(targetPath,domainName,'meteo%YEAR','epot0000.%JULDAY'),\
	os.path.join(sourcePath,domainName,'netcdf','referencePotET_dailyTot.nc'),\
	boundingBox,cellLength,startDate,endDate,'days','scalar',dynamic)
#-land cover
ncCropFiles= {'cropCoefficient': 'Global_CropCoefficientKc-%s_30min.nc',\
	'coverFraction': 'coverFractionInput%s366days.nc',\
	'interceptionCapacity':  'interceptCapInput%s366days.nc' }

for landCoverName, landCoverKey in landCoverKeys.iteritems():
	for landCoverProperty, landCoverPropertyMap in  {'cropCoefficient': 'kc_%s',\
			'coverFraction': 'cv_%s','interceptionCapacity': 'smax_%s'}.iteritems():
		key= '%s_%s' % (landCoverProperty,landCoverName)
		dynamicVariables[key]= os.path.join(hydroworldPath,'landCover',landCoverName,\
			ncCropFiles[landCoverProperty] % landCoverName.title()),\
			os.path.join(targetPath,domainName,'maps',(landCoverPropertyMap % landCoverKey[0]).ljust(8,'0')+'.%JULDAY')
#-populate dynamic datasets
for variableName, variableMaps in dynamicVariables.iteritems():
	dynamicDataSets[variableName]=  pcrObject(variableName,\
	variableMaps[1],variableMaps[0],boundingBox,cellLength,startDate,endDate,'days','scalar',dynamic)
#-process datasets
for value in dynamicDataSets.values():
	print 'processing %s' % value
	value.initializeFileInfo()
	value.processFileInfo()

#-static datasets
staticVariables= {}
staticDataSets= {}
dynamic= False
#-physiography: LDD and cell area
staticVariables['localDrainageDirection']= os.path.join(hydroworldPath,\
	'routing','reservoirs','fromRensJune2013','reservoirparameterization','lddsound_30min.map'),\
	os.path.join(targetPath,domainName,'maps','lddsound_30min.map')
staticVariables['cellArea']= os.path.join(hydroworldPath,'routing','cellarea30min.map'),\
	os.path.join(targetPath,domainName,'maps','cellarea30min.map')
#-topography: relative height
#-relative height
for dzRel in ('dzRel0001','dzRel0005','dzRel0010','dzRel0020','dzRel0030','dzRel0040',\
		'dzRel0050','dzRel0060','dzRel0070','dzRel0080','dzRel0090','dzRel0100'):
	staticVariables[dzRel]= os.path.join(hydroworldPath,'landSurface','topo','hydro1k_%s.map' % dzRel.lower()),\
		os.path.join(targetPath,domainName,'maps','hydro1k_%s.map' % dzRel.lower())
#-topography: slope characteristics
staticVariables['tanSlope']= os.path.join(hydroworldPath,'landSurface','topo','globalgradslope.map'),\
		os.path.join(targetPath,domainName,'maps','globalgradslope.map')
staticVariables['slopeLength']=  os.path.join(hydroworldPath,'landSurface','topo','globalbcat.map'),\
		os.path.join(targetPath,domainName,'maps','globalbcat.map')
staticVariables['orographyBeta']=  os.path.join(hydroworldPath,'landSurface','topo','globalboro.map'),\
		os.path.join(targetPath,domainName,'maps','globalboro.map')
#-soil properties
for soilProperty, soilPropertyMap in {'airEntryValue1': 'fao30_psis30.map', 'airEntryValue2': 'fao30_psis100.map', 'KSat1': 'fao30_ks30.map', \
		'KSat2': 'fao30_ks100.map', 'poreSizeBeta1': 'fao30_beta30.map', 'poreSizeBeta2': 'fao30_beta100.map', \
		'firstStorDepth': 'fao30_z1_permafrost.map', 'secondStorDepth': 'fao30_z2_permafrost.map', 'soilWaterStorageCap': 'fao30_sc_permafrost.map',\
		'soilWaterStorageCap1': 'fao30_sc1_permafrost.map', 'soilWaterStorageCap2': 'fao30_sc2_permafrost.map', \
		'resVolWC1': 'fao30_thr30.map', 'resVolWC2': 'fao30_thr100.map', 'satVolWC1': 'fao30_ths30.map', \
		'satVolWC2': 'fao30_ths100.map', 'percolationImp': 'fao30_p2imp_permafrost.map'}.iteritems():
	staticVariables[soilProperty]= os.path.join(hydroworldPath,'landSurface','soil',soilPropertyMap),\
		os.path.join(targetPath,domainName,'maps',soilPropertyMap)
#-land cover
for landCoverName, landCoverKey in landCoverKeys.iteritems():
	for landCoverProperty, landCoverPropertyMap in {'fracVegCover': 'vegf_%s.map',\
			'rootFraction1': 'rfrac1_%s.map', 'rootFraction2': 'rfrac2_%s.map', 'maxRootDepth': 'fao_root_%s.map',\
			'minSoilDepthFrac': 'minf_%s_permafrost.map', 'maxSoilDepthFrac': 'maxf_%s.map'}.iteritems():
		key= '%s_%s' % (landCoverProperty,landCoverName)
		staticVariables[key]= os.path.join(hydroworldPath,'landCover',landCoverName,landCoverPropertyMap % landCoverKey),\
			os.path.join(targetPath,domainName,'maps',landCoverPropertyMap % landCoverKey),
#-groundwater
staticVariables['recessionCoefficent']= os.path.join(hydroworldPath,'groundwater','globalalpha.map'),\
		os.path.join(targetPath,domainName,'maps','globalalpha.map')
staticVariables['specificYield']= os.path.join(hydroworldPath,'groundwater','specificyield.map'),\
		os.path.join(targetPath,domainName,'maps','specificyield.map')
#-populate static datasets
for variableName, variableMaps in staticVariables.iteritems():
	if variableName != 'localDrainageDirection':
		staticDataSets[variableName]=  pcrObject(variableName,\
			variableMaps[1],variableMaps[0],boundingBox,cellLength,startDate,endDate,'days','scalar',dynamic)
	else:
		staticDataSets[variableName]=  pcrObject(variableName,\
			variableMaps[1],variableMaps[0],boundingBox,cellLength,startDate,endDate,'days','ldd',dynamic)	
#-process static datasets
for value in staticDataSets.values():
	print 'processing %s' % value
	value.initializeFileInfo()
	value.processFileInfo()
	if value.variableName == 'localDrainageDirection':
		command= 'pcrcalc "%s= lddrepair(%s)"' % (value.outputFileName.replace('/', '\\'),value.outputFileName.replace('/', '\\'))
		os.system(command)
		command= 'pcrcalc catclone.map= "defined(%s)"' % value.outputFileName.replace('/', '\\')
		os.system(command)

#-initial data sets
initialVariables= {}
initialDataSets= {}
#-fixed
initialVariables['stor3x']= os.path.join(initialPath,'storGroundwaterIni_2000-12-31.map'),\
		os.path.join(targetPath,domainName,'results','stor3x00.ini')
#-land cover dependent
for landCoverName, landCoverKey in landCoverKeys.iteritems():
	for landCoverProperty, landCoverPropertyMap in {'ints': 'interceptStorIni_%s_2000-12-31.map','q2': 'interflowIni_%s_2000-12-31.map',\
			's1':  'storUppIni_%s_2000-12-31.map','s2': 'storLowIni_%s_2000-12-31.map',\
			'sc': 'snowCoverSWEIni_%s_2000-12-31.map','scf': 'snowFreeWaterIni_%s_2000-12-31.map' }.iteritems():
		key= '%s_%s' % (landCoverProperty,landCoverName)
		initialVariables[key]= os.path.join(initialPath,landCoverPropertyMap % landCoverName),\
			os.path.join(targetPath,domainName,'results',(landCoverProperty+'_%sv' % landCoverKey[0]).ljust(8,'0')+'.ini')
for variableName, variableMaps in initialVariables.iteritems():
	initialDataSets[variableName]=  pcrObject(variableName,\
		variableMaps[1],variableMaps[0],boundingBox,cellLength,startDate,endDate,'days','scalar',dynamic)
#-process static datasets
for value in initialDataSets.values():
	print 'processing %s' % value
	value.initializeFileInfo()
	value.processFileInfo()
