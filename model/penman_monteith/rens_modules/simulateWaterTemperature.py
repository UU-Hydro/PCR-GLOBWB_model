#-import modules
import os, sys, shutil, math, calendar, datetime, tarfile, zlib, zipfile
import numpy as np
import pcraster as pcr
from pcraster import pcr2numpy
import pcraster.framework as pcrm
from pcraster.framework import generateNameT

sys.path.insert(0,'/home/beek0120/PCR-GLOBWB/PCR-GLOBWB_V1.0/')
sys.path.insert(1,'/home/beek0120/PCR-GLOBWB/SoilParameterization')
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
years= range(1958,2002)
forcingDataSet= 'wfd'
#-output locations
pathMaps= 'maps'
pathInitial= 'initialconditions'
pathRes= 'results'
#-set up input data
#-input netCDF files
#-ncResultsPath	
ncResultsPath= '/scratch/rens/%s/netcdf/' % forcingDataSet
ncData= {}
variableName= 'openwaterEvaporation'
ncData[variableName]= {}
ncData[variableName]['fileName']= os.path.join(ncResultsPath,'referencePotET_dailyTot_output.nc')
ncData[variableName]['fileRoot']= os.path.join(pathRes,'ewat')
variableName= 'directRunoff'
ncData[variableName]= {}
ncData[variableName]['fileName']= os.path.join(ncResultsPath,'directRunoff_dailyTot_output.nc')
ncData[variableName]['fileRoot']= os.path.join(pathRes,'q1x')
variableName= 'interFlow'
ncData[variableName]= {}
ncData[variableName]['fileName']= os.path.join(ncResultsPath,'interflowTotal_dailyTot_output.nc')
ncData[variableName]['fileRoot']= os.path.join(pathRes,'q2x')
variableName= 'baseFlow'
ncData[variableName]= {}
ncData[variableName]['fileName']= os.path.join(ncResultsPath,'baseflow_dailyTot_output.nc')
ncData[variableName]['fileRoot']= os.path.join(pathRes,'q3x')
variableName= 'airTemperature'
ncData[variableName]= {}
ncData[variableName]['fileName']= '/scratch/yoshi/WATCH/tas_watch_1958-2001.nc4'
ncData[variableName]['fileRoot']= os.path.join(pathRes,'ta')
ncData[variableName]['conversionConstant']= -273.15
ncData[variableName]['conversionFactor']= 1.0
variableName= 'precipitation'
ncData[variableName]= {}
ncData[variableName]['fileName']= '/scratch/yoshi/WATCH//pr_total_gpcc_watch_1958-2001.nc4'
ncData[variableName]['fileRoot']= os.path.join(pathRes,'prp')
ncData[variableName]['conversionConstant']= 0.0
ncData[variableName]['conversionFactor']= 86.4
variableName= 'relativeHumidity'
ncData[variableName]= {}
ncData[variableName]['fileName']= '/scratch/yoshi/WATCH//hur_watch_1958-2001.nc4'
ncData[variableName]['fileRoot']= os.path.join(pathRes,'relhum')
ncData[variableName]['conversionConstant']= 0.0
ncData[variableName]['conversionFactor']= 0.01
variableName= 'shortWaveRadiationIn'
ncData[variableName]= {}
ncData[variableName]['fileName']= '/scratch/yoshi/WATCH/rsds_watch_1958-2001.nc4'
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
ncAttributes= {'title': forcingDataSet}
ncOutput= {}
variableName= 'discharge'
shortName= 'qc'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath,('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, years[0], years[-1])).lower())
ncOutput[variableName]['units']= 'm3/s'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)
variableName= 'waterTemperature'
shortName= 'tw'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath,('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, years[0], years[-1])).lower())
ncOutput[variableName]['units']= 'K'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)
variableName= 'waterHeight'
shortName= 'wh'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath,('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, years[0], years[-1])).lower())
ncOutput[variableName]['units']= 'm'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)
variableName= 'iceThickness'
shortName= 'wi'
ncOutput[variableName]= {}
ncOutput[variableName]['fileName']= os.path.join(ncResultsPath,('%s_%s_%d-%d.nc' % (variableName, forcingDataSet, years[0], years[-1])).lower())
ncOutput[variableName]['units']= 'm'
ncOutput[variableName]['fileRoot']= os.path.join(pathRes,shortName)

# * start *
#-echo
print ' * Simulating water temperature using the %s forcing data set' % forcingDataSet
#-set clone and obtain attributes
pcr.setclone(cloneMap)
cloneSpatialAttributes= spatialAttributes(cloneMap)
#-empty temporary directory
createOutputDirs([pathRes])
#-retrieve average temperature
variableName= 'airTemperature'
command= 'cdo timmean -seldate,%s,%s %s %s' % (datetime.date(years[0],1,1),\
	datetime.date(years[-1],12,31),ncData[variableName]['fileName'],'temp.nc')
os.system(command)
command= 'gdal_translate -of PCRaster -ot FLOAT32 -mo VALUESCALE=VS_SCALAR temp.nc %s' % avgTMap
os.system(command)
os.remove('temp.nc')
#-post-processing
if 'conversionFactor' in ncData[variableName].keys():
	pcr.report(ncData[variableName]['conversionConstant']+\
		ncData[variableName]['conversionFactor']*pcr.readmap(avgTMap),avgTMap)						
#-set initial conditions if not set already
print ' - initializing run'
targetIniPath= os.path.join(pathInitial,forcingDataSet,str(years[0]))
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
#-initialize posCnt
posCnt= 0
#-initialize files
for variableName in ncOutput.keys():
	createNetCDF(ncOutput[variableName]['fileName'],longitudes,latitudes,timedData= True,attributes= ncAttributes)

#-iterate over years
for year in years:
	#-echo year
	print ' - processing year %d' % year
	#-set paths to process initial files and copy them to the temporary directory with results 
	sourceIniPath= os.path.join(pathInitial,forcingDataSet,str(year))
	targetIniPath= os.path.join(pathInitial,forcingDataSet,str(year+1))
	createOutputDirs([targetIniPath])
	copyIniFiles(sourceIniPath,pathRes,[''],iniFileList)
	#-process data and set time steps and increment
	startDate= datetime.datetime(year,1,1)
	endDate= datetime.datetime(year,12,31)
	timeSteps= endDate.toordinal()-startDate.toordinal()+1
	dynamicIncrement= 1
	for variableName in ncData.keys():
		print '   extracting %s' % variableName,
		ncFileIn= ncData[variableName]['fileName']
		if 'nc4' in os.path.splitext(ncData[variableName]['fileName'])[1]:
			print 'converting nc4 input'
			ncFileOut= os.path.split(ncData[variableName]['fileName'])[1]
			ncFileOut= os.path.join(pathRes,os.path.splitext(ncFileOut)[0]+'.nc')
			command= 'cdo -f nc seldate,%s,%s %s %s' % (startDate.date(),endDate.date(),ncFileIn,ncFileOut)
			os.system(command)
			ncFileIn= ncFileOut			
		else:
			ncFileIn= ncData[variableName]['fileName']
			print
		#~ #-process data
		pcrDataSet= pcrObject(variableName, ncData[variableName]['fileRoot'],\
			ncFileIn,cloneSpatialAttributes, pcrVALUESCALE= pcr.Scalar, resamplingAllowed= True,\
			dynamic= True, dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= dynamicIncrement, ncDynamicDimension= 'time')
		pcrDataSet.initializeFileInfo()
		pcrDataSet.processFileInfo()
		#-post-processing
		if 'conversionFactor' in ncData[variableName].keys():
			for fileName in os.listdir(pathRes):
				if testMapStack(ncData[variableName]['fileRoot'],fileName):
					pcr.report(ncData[variableName]['conversionConstant']+\
						ncData[variableName]['conversionFactor']*pcr.readmap(os.path.join(pathRes,fileName)),\
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
	#-archive netCDF files
	dayCnt= 0
	for day in xrange(startDate.toordinal(),endDate.toordinal()+1):
		date= startDate+datetime.timedelta(dayCnt)
		dayCnt+= 1
		for variableName in ncOutput.keys():
			variableArray= pcr2numpy(pcr.readmap(generateNameT(ncOutput[variableName]['fileRoot'],dayCnt)),MV)
			data2NetCDF(ncOutput[variableName]['fileName'],variableName,{'units': ncOutput[variableName]['units']},variableArray,posCnt,date,MV)
		posCnt+= 1
	
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
