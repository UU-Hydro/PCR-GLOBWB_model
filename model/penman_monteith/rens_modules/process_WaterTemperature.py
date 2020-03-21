#-reads in information from netCDF files and convert it accordingly

import os, sys, datetime, calendar
import numpy as np
import netCDF4 as nc
from pcraster import setclone, readmap, pcr2numpy

#-Initialization
cloneMap= '/home/beek0120/PCRGLOBWB/WaterTemperature/Watch/wfd_cellarea.map'
setclone(cloneMap)
mask= pcr2numpy(readmap(cloneMap),0) != 0
MV= -999.9
simulationName= sys.argv[1]
startYear= int(sys.argv[2])
endYear= int(sys.argv[3])
inputDirRoot=  sys.argv[4]
outputDirRoot= sys.argv[5]
#-file names related to discharge and water temperature
ncFileRoot= '%s_%s_%s_1958-2001.nc'
txtFileRoot= '%s_%s_%04d%04d_%s_pcr-globwb.txt'
variableNames= {}
variableNames['Flow']= 'discharge'
variableNames['Tw']= 'waterTemperature'
fileExtension= {}
fileExtension['monthly']= 'monthly'
fileExtension['yearly']= 'yearly'
headerEntries= ['cell_lat', 'cell_lon','cell_nr']
headerFormats= {}
headerFormats['default']= '%12s'
headerFormats['cell_lat']= '%12s'
headerFormats['cell_lon']= '%12s'
headerFormats['cell_nr']= '%12s'
entryFormats= {}
entryFormats['default']= '%12.3f'
entryFormats['cell_lat']= '%12.2f'
entryFormats['cell_lon']= '%12.2f'
entryFormats['cell_nr']= '%12d'

#-Start
#-iterate over variables and temporal resolution
for variableName, variableID in variableNames.iteritems():
	for tempName, tempID in fileExtension.iteritems():
		#-create input file name
		ncFileName= os.path.join(inputDirRoot,(ncFileRoot % (variableID,tempID,simulationName)).lower())
		#-create output file name
		txtFileName= os.path.join(outputDirRoot,txtFileRoot % (tempName,variableName,startYear,endYear,simulationName))
		#-echo to screen
		print ' * processing %s, writing output to %s' % (os.path.split(ncFileName)[1],os.path.split(txtFileName)[1])
		#-open txt file for output
		txtFile= open(txtFileName,'w')		
		#-open nc file for input
		rootgrp= nc.Dataset(ncFileName)	
		#-process entries
		latitudes= rootgrp.variables['latitude'][:]
		longitudes= rootgrp.variables['longitude'][:]
		dates= nc.num2date(rootgrp.variables['time'][:],rootgrp.variables['time'].units,rootgrp.variables['time'].calendar)
		dateEntries= []
		if tempName == 'monthly':
			for date in dates:
				dateEntries.append('mean_%s' % calendar.month_abbr[date.month])
		elif tempName == 'yearly':
			for date in dates:
				dateEntries.append(date.year)		
		else:
			dateEntries= dates[:]
		#-write header
		hStr= ''
		for entry in headerEntries:
			hStr+= headerFormats[entry] % entry
		for entry in dateEntries:
			hStr+= headerFormats['default'] % str(entry)
		hStr+= '\n'
		txtFile.write(hStr)
		#-set couter to zero
		cellNumber= 0
		for rowCnt in xrange(latitudes.size):
			for colCnt in xrange(longitudes.size):
				data= rootgrp.variables[variableID][:,rowCnt,colCnt]
				#-try to fill in any masked array entries
				try:
					data= data.filled(MV)
				except:
					pass		
				if mask[rowCnt,colCnt]:
					#-process
					latitude= latitudes[rowCnt]
					longitude= longitudes[colCnt]
					cellNumber+= 1
					if variableID == 'tw':
						data+= -273.15
					#-write entries
					wStr= ''
					entry= 'cell_lat'
					wStr+= entryFormats[entry] % latitude
					entry= 'cell_lon'
					wStr+= entryFormats[entry] % longitude
					entry= 'cell_nr'
					wStr+= entryFormats[entry] % cellNumber
					entry= 'default'
					for value in data:
						wStr+= entryFormats[entry] % value				
					wStr+= '\n'
					txtFile.write(wStr)
		#-processed
		print '   %d entries written' % cellNumber
		#-close nc file
		rootgrp.close()
		#-close txt file
		txtFile.close()
#-all done
print 'all done!'
