#-import modules
import os, sys, shutil, math, calendar, datetime, tarfile, zlib, zipfile
import numpy as np
import pcraster as pcr
from pcraster import pcr2numpy
import pcraster.framework as pcrm
from pcraster.framework import generateNameT
from pcrParameterization import pcrObject
from spatialDataSet2PCR import spatialAttributes
from convert2NetCDF import *

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
      
def copyIniFiles(pathIn,pathOut,IniExtList= [],SpecMapList= [],recur= 0):
	#copy files from in to out on the basis of the provided extension list; if empty all is copied
	#creating file inventory
	for Root, Dirs, Files in os.walk(pathIn):
		#Dstpath created if absent
		Dir= Root.find('/')+1
		if Dir > 0 and recur:
			DstPath= Root[Dir:len(Root)]
			DstPath= os.path.join(pathOut,DstPath)
		else:
			DstPath= pathOut
		#checking whether destination directory exist, if not it is created
		if not os.path.exists(DstPath):
			os.mkdir(DstPath)
		for File in Files:
			#check if File is a valid inital file
			if len(IniExtList) >0:
				CopyFile= False
			else:
				CopyFile=  True
			for ncnt in range(0,len(IniExtList)):
				Ext= File[len(File)-3:len(File)]
				if Ext == IniExtList[ncnt]:
					CopyFile=  True
			if CopyFile:
				SrcName = os.path.join(Root,File)
				DstName = os.path.join(DstPath,File)
				try:
					shutil.copy(SrcName,DstName)
					print '\tcopying %s => %s' %(SrcName,DstName)
				except:
					pass
		for File in SpecMapList:
			SrcName = os.path.join(pathIn,File)
			DstName = os.path.join(pathOut,File)
			try:
				shutil.copy(SrcName,DstName)
				print '\tcopying %s => %s' %(SrcName,DstName)
			except:
				pass

def testMapStack(fileRoot, fileName):
	from string import digits
	digitList= digits[:]
	digitList+= '.'
	'''Checks whether the file name entered corresponds with a map stack of the file root specified'''
	#-strip any path from file name
	fileRoot= os.path.split(fileRoot)[1]
	fileName= os.path.split(fileName)[1]
	#-set default match to false
	match= False
	#-get length of fileRoot
	posCnt= len(fileRoot)
	if fileName[:posCnt] == fileRoot:
		match= True
		fileName= fileName[posCnt:]
	if match and len(fileName) > 0:
		for char in fileName:
			if char not in digitList:
				match= False
	else:
		match= False
	return match

#-Simulates water temperature for the years specified (1958-2001)
# * initialization *
MV= -999.9
#-years and number of runs to initialize the model
startYear, endYear= (int(sys.argv[3]),2100)
yearRange= range(startYear, endYear)
nrRunsInitialization= int(sys.argv[4])
weightAvgT= 30.**-1
#-forcing dataset
forcingDataSet= sys.argv[1]
rcpName= sys.argv[2]
#-output locations
pathMaps= 'maps'
pathInitial= os.path.join('initialconditions','' % ((forcingDataSet.lower()).replace('-','_'),rcpName))
pathRes= '/scratch/rens/temp_%s_%s' % ((forcingDataSet.lower()).replace('-','_'),rcpName)
#-set up input data
#-input netCDF files
#-ncResultsPath
ncResultsPath= ('/scratch/rens/%s_historical/netcdf/' % (forcingDataSet.lower()).replace('-','_'),\
	'/scratch/rens/%s_%s/netcdf/' % ((forcingDataSet.lower()).replace('-','_'),rcpName),\
	'/scratch/rens/watertemperature%s_%s/netcdf/' % ((forcingDataSet.lower()).replace('-','_'),rcpName))
ncData= {}
# open water evap
variableName= 'openwaterEvaporation'
ncData[variableName]= {}
ncData[variableName]['fileName']= (os.path.join(ncResultsPath[0],'referencePotET_dailyTot_output.nc'),\
	os.path.join(ncResultsPath[1],'referencePotET_dailyTot_output.nc'))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'ewat')
# direct runoff
variableName= 'directRunoff'
ncData[variableName]= {}
ncData[variableName]['fileName']= (os.path.join(ncResultsPath[0],'directRunoff_dailyTot_output.nc'),\
	os.path.join(ncResultsPath[1],'directRunoff_dailyTot_output.nc'))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'q1x')
# interflow
variableName= 'interFlow'
ncData[variableName]= {}
ncData[variableName]['fileName']= (os.path.join(ncResultsPath[0],'interflowTotal_dailyTot_output.nc'),\
	os.path.join(ncResultsPath[1],'interflowTotal_dailyTot_output.nc'))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'q2x')
# base flow
variableName= 'baseFlow'
ncData[variableName]= {}
ncData[variableName]['fileName']= (os.path.join(ncResultsPath[0],'baseflow_dailyTot_output.nc'),\
	os.path.join(ncResultsPath[1],'baseflow_dailyTot_output.nc'))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'q3x')
# temperature
variableName= 'airTemperature'
ncData[variableName]= {}
ncData[variableName]['fileName']= ('/data/hydroworld/forcing/CMIP5/ISI-MIP-INPUT/%s/tas_bced_1960-1999_%s_historical_1951-2005.nc' % (forcingDataSet, forcingDataSet.lower()),\
	'/data/hydroworld/forcing/CMIP5/ISI-MIP-INPUT/%s/tas_bced_1960-1999_%s_%s_2006-2099.nc' % (forcingDataSet, forcingDataSet.lower(),rcpName))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'ta')
ncData[variableName]['conversionConstant']= -273.15
ncData[variableName]['conversionFactor']= 1.0
# precip
variableName= 'precipitation'
ncData[variableName]= {}
ncData[variableName]['fileName']= ('/data/hydroworld/forcing/CMIP5/ISI-MIP-INPUT/%s/pr_bced_1960-1999_%s_historical_1951-2005.nc' % (forcingDataSet, forcingDataSet.lower()),\
	'/data/hydroworld/forcing/CMIP5/ISI-MIP-INPUT/%s/pr_bced_1960-1999_%s_%s_2006-2099.nc' % (forcingDataSet, forcingDataSet.lower(),rcpName))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'prp')
ncData[variableName]['conversionConstant']= 0.0
ncData[variableName]['conversionFactor']= 86.4
# rel humidity
variableName= 'relativeHumidity'
ncData[variableName]= {}
ncData[variableName]['fileName']= []
for inputPath in ('/storagetemp/ISI-MIP_FT/%s/hist/' % forcingDataSet,\
	'/storagetemp/ISI-MIP_FT/%s/rcp%s/' % (forcingDataSet,rcpName):
		for fileName in os.listdir(inputPath):
			if 'rhs' in fileName:
				ncData[variableName]['fileName'].append(os.path.join(inputPath,fileName))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'relhum')
ncData[variableName]['conversionConstant']= 0.0
ncData[variableName]['conversionFactor']= 0.01
ncData[variableName]['maxValue']= 1.00
# short wave radiation
variableName= 'shortWaveRadiationIn'
ncData[variableName]= {}
ncData[variableName]['fileName']= []
for inputPath in ('/storagetemp/ISI-MIP_FT/%s/hist/' % forcingDataSet,\
	'/storagetemp/ISI-MIP_FT/%s/rcp%s/' % (forcingDataSet,rcpName)):
		for fileName in os.listdir(inputPath):
			if 'rsds' in fileName:
				ncData[variableName]['fileName'].append(os.path.join(inputPath,fileName))
ncData[variableName]['fileRoot']= os.path.join(pathRes,'rads')

#-input maps: roots for input and corresponding file
resStackList= ['q1x','q2x','q3x','ewat','ta','prp','relhum','rads','totd']
Q1FileName= os.path.join(pathRes,resStackList[0])
Q2FileName= os.path.join(pathRes,resStackList[1])
Q3FileName= os.path.join(pathRes,resStackList[2])
EWatFileName= os.path.join(pathRes,resStackList[3])
taFileName= os.path.join(pathRes,resStackList[4])
prpFileName= os.path.join(pathRes,resStackList[5])
relHumFileName= os.path.join(pathRes,resStackList[6])
radswFileName= os.path.join(pathRes,resStackList[7])
totdFileName= os.path.join(pathRes,resStackList[8])
#-channel characteristics
cloneMap= os.path.join(pathMaps,'wfd_mask.map')
cellAreaMap= os.path.join(pathMaps,'wfd_cellarea.map')
lddMap= os.path.join(pathMaps,'wfd_lddlake.map')
gradChannelMap= os.path.join(pathMaps,'wfd_gradchannel.map')
combChannelManNMap= os.path.join(pathMaps,'wfd_fldn.map')
combChannelWidthMap= os.path.join(pathMaps,'wfd_fldw.map')
combChannelLengthMap= os.path.join(pathMaps,'wfd_fldl.map')
#-lake characteristics
lakeIDMap=  os.path.join(pathMaps,'wfd_lakeid.map')
lakeAreaMap= os.path.join(pathMaps,'wfd_lakearea.map')
lakeVolumeMap= os.path.join(pathMaps,'wfd_lakevolume.map')
lakeFracMap= os.path.join(pathMaps,'wfd_lakefrac.map')
lakeOutletMap= os.path.join(pathMaps,'wfd_lakeoutlet.map')
#-limitation on ice growth
maxIceThicknessMap= os.path.join(pathMaps,'wfd_maxice.map')
#-points for water balance evaluation
basinOutletMap= os.path.join(pathMaps,'basinoutlet.map')
massBalEvalMap= os.path.join(pathMaps,'watballoc.map')
#-average annual temperature
avgTMap= os.path.join(pathMaps,'tavg_%s.map' % forcingDataSet)
#-input- & output: initial conditions:
# channel discharge, channel storage and lake storage
# and list of all initial maps to facilitate copying
qcIniMap= 'qc000000.ini'
storchIniMap= 'storch00.ini' 
storlakeIniMap= 'storlake.ini'
twIniMap= 'tw000000.ini'
wiIniMap= 'wi000000.ini'
iniFileList= [qcIniMap,storchIniMap,storlakeIniMap,twIniMap,wiIniMap]
iniQCFileName= os.path.join(pathRes,qcIniMap)
iniChannelStorFileName= os.path.join(pathRes,storchIniMap)
iniLakeStorFileName= os.path.join(pathRes,storlakeIniMap)
iniTWFileName= os.path.join(pathRes,twIniMap)
iniWIFileName= os.path.join(pathRes,wiIniMap)
#-output:
# maps of mass balance error
massBalanceErrorFileName= os.path.join(pathRes,'mbe_routing.map')
relmassBalanceErrorFileName= os.path.join(pathRes,'mberel_routing.map')
#-roots for output of map stacks
#-daily fields
taFileName= os.path.join(pathRes,'ta')
qcFileName= os.path.join(pathRes,'qc')
whFileName= os.path.join(pathRes,'wh')
twFileName= os.path.join(pathRes,'tw')
wiFileName= os.path.join(pathRes,'wi')
#-monthly fields statistics
qAvgFileName= os.path.join(pathRes,'qavg')
qSDFileName=  os.path.join(pathRes,'qsd_')
twAvgFileName= os.path.join(pathRes,'tavg')
twSDFileName=  os.path.join(pathRes,'tsd_')
dtAvgFileName= os.path.join(pathRes,'davg')
dtSDFileName=  os.path.join(pathRes,'dsd_')
#-output netCDF files
try:
	os.makedirs(ncResultsPath[2])
except:
	pass
ncAttributes= {'title': forcingDataSet}
ncOutput= {}
variableName= 'discharge'
shortName= 'qc'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath[2],('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, startYear, endYear)).lower())
ncOutput[variableName]['units']= 'm3/s'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)
variableName= 'waterTemperature'
shortName= 'tw'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath[2],('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, startYear, endYear)).lower())
ncOutput[variableName]['units']= 'K'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)
variableName= 'waterHeight'
shortName= 'wh'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath[2],('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, startYear, endYear)).lower())
ncOutput[variableName]['units']= 'm'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)
variableName= 'iceThickness'
shortName= 'wi'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath[2],('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, startYear, endYear)).lower())
ncOutput[variableName]['units']= 'm'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)

# * start *
#-echo
print ' * Simulating water temperature using the %s forcing data set' % forcingDataSet
#-set clone and obtain attributes
pcr.setclone(cloneMap)
cloneSpatialAttributes= spatialAttributes(cloneMap)
#-create path
if not os.path.exists(pathRes): os.makedirs(pathRes)
#-insert years for spin-up
numberYears= len(yearRange)
for runCnt in xrange(nrRunsInitialization):
	iCnt= runCnt % numberYears
	iCnt+= runCnt
	yearRange.insert(runCnt,yearRange[iCnt])
#-empty temporary directory
createOutputDirs([pathRes])
#-retrieve average temperature
tempNC= os.path.join(pathRes,'temp.nc')
variableName= 'airTemperature'
command= 'cdo timmean -seldate,%s,%s %s %s' % (datetime.date(startYear,1,1),\
	datetime.date(endYear,12,31),ncData[variableName]['fileName'][0],tempNC)
print command
os.system(command)
command= 'gdal_translate -of PCRaster -ot FLOAT32 -mo VALUESCALE=VS_SCALAR %s %s' % (tempNC, avgTMap)
os.system(command)
os.remove(tempNC)
#-post-processing
if 'conversionFactor' in ncData[variableName].keys():
	pcr.report(ncData[variableName]['conversionConstant']+\
		ncData[variableName]['conversionFactor']*pcr.readmap(avgTMap),avgTMap)						
#-set initial conditions if not set already
print ' - initializing run'
targetIniPath= os.path.join(pathInitial,str(startYear))
for fileName in iniFileList:
	if not os.path.exists(os.path.join(targetIniPath,fileName)):
		try:
			os.makedirs(targetIniPath)
		except:
			pass
		pcr.report(pcr.spatial(pcr.scalar(0.0)),os.path.join(targetIniPath,fileName))
		if fileName == twIniMap:
			pcr.report(pcr.max(0.1,pcr.readmap(avgTMap)),os.path.join(targetIniPath,fileName))
		print '   initial file %s created' % os.path.join(targetIniPath,fileName)	
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

#-iterate over years
for year in yearRange:
	#-echo year
	print ' - processing year %d' % year,
	runCnt+= 1
	#-decide on processing status
	if runCnt > nrRunsInitialization:
		initializeModel= False
		print
	else:
		initializeModel= True
		print '- spinup'
	#-set paths to process initial files and copy them to the temporary directory with results 
	if initializeModel:
		sourceIniPath= os.path.join(pathInitial,str(startYear))
		targetIniPath= sourceIniPath
	else:
		sourceIniPath= os.path.join(pathInitial,str(year))
		targetIniPath= os.path.join(pathInitial,str(year+1))
	if not os.path.exists(targetIniPath):
		os.makedirs(targetIniPath)
	copyIniFiles(sourceIniPath,pathRes,[''],iniFileList)
	#-process data and set time steps and increment
	startDate= datetime.datetime(year,1,1)
	endDate= datetime.datetime(year,12,31)
	timeSteps= endDate.toordinal()-startDate.toordinal()+1
	dynamicIncrement= 1
	#-retrieve input files
	for variableName in ncData.keys():
		print '   extracting %s' % variableName
		#-input from netCDF
		extracted= False
		for ncFileIn in ncData[variableName]['fileName']:
			if 'nc' in os.path.splitext(ncFileIn)[1]:
				print 'converting nc input'
				ncFileOut= os.path.split(ncFileIn)[1]
				ncFileOut= os.path.join(pathRes,os.path.splitext(ncFileOut)[0]+'.nc')
				command= 'cdo -f nc seldate,%s,%s %s %s' % (startDate.date(),endDate.date(),ncFileIn,ncFileOut)
				os.system(command)
				ncFileIn= ncFileOut
			#-process data
			if variableName == 'relativeHumidity': print ncData[variableName]['fileRoot']
			try:
				pcrDataSet= pcrObject(variableName, ncData[variableName]['fileRoot'],\
					ncFileIn,cloneSpatialAttributes, pcrVALUESCALE= pcr.Scalar, resamplingAllowed= True,\
						dynamic= True, dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= dynamicIncrement, ncDynamicDimension= 'time')
				validProcessInfo= pcrDataSet.initializeFileInfo()
				if validProcessInfo:
					pcrDataSet.processFileInfo()
					print '    - required input obtained from %s' % ncFileIn
					extracted= True
				elif not validProcessInfo and 'alias' in ncData[variableName].keys():
					pcrDataSet= pcrObject(ncData[variableName]['alias'], ncData[variableName]['fileRoot'],\
						ncFileIn,cloneSpatialAttributes, pcrVALUESCALE= pcr.Scalar, resamplingAllowed= True,\
							dynamic= True, dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= dynamicIncrement, ncDynamicDimension= 'time')
					validProcessInfo= pcrDataSet.initializeFileInfo()
					pcrDataSet.processFileInfo()
					print '    - required input obtained from %s' % ncFileIn
					extracted= True
				else:
					print '    - the required input is not contained by %s' % ncFileIn
				pcrDataSet= None
				del pcrDataSet
			except:
				pass
			if extracted: break
		#-post-processing
		if 'conversionFactor' in ncData[variableName].keys():
			for fileName in os.listdir(pathRes):
				if testMapStack(ncData[variableName]['fileRoot'],fileName):
					pcr.report(ncData[variableName]['conversionConstant']+\
						ncData[variableName]['conversionFactor']*pcr.readmap(os.path.join(pathRes,fileName)),\
						os.path.join(pathRes,fileName))
		if 'minValue' in ncData[variableName].keys():
			for fileName in os.listdir(pathRes):
				if testMapStack(ncData[variableName]['fileRoot'],fileName):
					pcr.report(pcr.max(ncData[variableName]['minValue'],pcr.readmap(os.path.join(pathRes,fileName))),\
						os.path.join(pathRes,fileName))
		if 'maxValue' in ncData[variableName].keys():
			for fileName in os.listdir(pathRes):
				if testMapStack(ncData[variableName]['fileRoot'],fileName):
					pcr.report(pcr.min(ncData[variableName]['maxValue'],pcr.readmap(os.path.join(pathRes,fileName))),\
						os.path.join(pathRes,fileName))
	#-total demand and obtain open water evaporation
	dayCnt= 0
	variableName= 'openwaterEvaporation'
	for day in xrange(startDate.toordinal(),endDate.toordinal()+1):
		dayCnt+= 1
		#-total demand
		pcr.report(pcr.scalar(0.),generateNameT(os.path.join(pathRes,'totd'),dayCnt))
		#-evaporation 
		try:
			kcWater= pcr.readmap(os.path.join(pathMaps,generateNameT('kc_wat',dayCnt)))
		except:
			pass
		pcr.report(kcWater*pcr.readmap(generateNameT(ncData[variableName]['fileRoot'],dayCnt)),\
			generateNameT(ncData[variableName]['fileRoot'],dayCnt))
	
	#-all input ready, invoke model
	execfile('pcrGlobTemperature.py')
	routingscheme= pcrglobRoutingScheme(startDate,endDate)
	dynRouting = pcrm.DynamicFramework(routingscheme,timeSteps)
	dynRouting.run()
	#-update average yearly temperature in case an actual year is run
	if not initializeModel:
		variableName= 'airTemperature'
		dayCnt= 0
		avgT= pcr.scalar(0)
		for day in xrange(startDate.toordinal(),endDate.toordinal()+1):
			dayCnt+= 1
			avgT+= pcr.readmap(generateNameT(ncData[variableName]['fileRoot'],dayCnt))
		avgT/= dayCnt
		avgT= weightAvgT*avgT+(1.-weightAvgT)*pcr.readmap(avgTMap)
		pcr.report(avgT,avgTMap)
		print '   average groundwater temperature updated for %d' % year
	#-archive netCDF files in case an actual year is run
	if not initializeModel:
		dayCnt= 0
		for day in xrange(startDate.toordinal(),endDate.toordinal()+1):
			date= startDate+datetime.timedelta(dayCnt)
			dayCnt+= 1
			for variableName in ncOutput.keys():
				variableArray= pcr2numpy(pcr.readmap(generateNameT(ncOutput[variableName]['fileRoot'],dayCnt)),MV)
				data2NetCDF(ncOutput[variableName]['fileName'],variableName,{'units': ncOutput[variableName]['units']},variableArray,posCnt,date,MV)
			posCnt+= 1
		print '   netCDF output written for %d' % year
	#-copy initial conditions to target directory
	copyIniFiles(pathRes,targetIniPath,[''],iniFileList)
	#-clean results directories
	createOutputDirs([pathRes])
#-finished
print 'all done'

#-note: old text to include longwave radiation
#~ variableName= 'longWaveRadiationIn'
#~ ncData[variableName]= {}
#~ ncData[variableName]['fileName']= '/scratch/yoshi/WATCH/rlds_watch_1958-2001.nc4'
#~ ncData[variableName]['fileRoot']= os.path.join(pathRes,'radl')

		#~ pcr.report(pcr.readmap(generateNameT(ncData['shortWaveRadiationIn']['fileRoot'],dayCnt))+\
			#~ pcr.readmap(generateNameT(ncData['longWaveRadiationIn']['fileRoot'],dayCnt)),\
				#~ generateNameT(ncData['shortWaveRadiationIn']['fileRoot'],dayCnt))
