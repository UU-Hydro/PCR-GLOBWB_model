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
# Edwin Husni Sutanudjaja (24 June 2014): This script is to integrate several pcraster maps into one global map.
#                                         - Used mainly for making a set of initial conditions for 5 arc min runs. 

#-modules
import os
import sys
import subprocess
import time as tm
import numpy as np
import datetime
import glob
from multiprocessing import Pool
from pcraster import setclone, Scalar, readmap, report, pcr2numpy, numpy2pcr

def getMax(x,a):
	if not isinstance(a,np.ndarray):
		a= np.array(a)		
	m= float(a.max())
	if x == None:
		return m
	else:
		return max(m,x)
	
def getMin(x,a):
	if not isinstance(a,np.ndarray):
		a= np.array(a)		
	m= float(a.min())
	if x == None:
		return m
	else:
		return min(m,x)

def getFileList(inputDir, filePattern):
	'''creates a dictionary of	files meeting the pattern specified'''
	fileNameList = glob.glob(os.path.join(inputDir, filePattern))
	ll= {}
	for fileName in fileNameList:
		ll[os.path.split(fileName)[-1]]= fileName
	return ll

def getMapAttributesALL(cloneMap):
		co= ['mapattr -p %s ' %(cloneMap)]
		cOut,err= subprocess.Popen(co, stdout=subprocess.PIPE,stderr=open('/dev/null'),shell=True).communicate()
		if err !=None or cOut == []:
				print "Something wrong with mattattr in virtualOS, maybe clone Map does not exist ? "
				sys.exit()
		mapAttr = {'cellsize': float(cOut.split()[7]) ,\
							 'rows'		: float(cOut.split()[3]) ,\
							 'cols'		: float(cOut.split()[5]) ,\
							 'xUL'		 : float(cOut.split()[17]),\
							 'yUL'		 : float(cOut.split()[19])}
		return mapAttr

def checkResolution(c1,c2):
	'''Check resolution'''
	s1= str(c1)
	s2= str(c2)
	if len(s1) < len(s2):
		s= s1
	else:
		s= s2
	p= s.find('.')
	if p <> -1:
		nd= len(s)-(p+1)
	else:
		nd= 0
	c1= round(c1,nd)
	c2= round(c2,nd)
	if c1 <> c2: print 'resolutions %s, %s differ' % (s1,s2)
	return c1 == c2, nd
	
def getPosition(x,values,nd):
	'''Returns the position of value x in the array of values with the number of digits specified '''
	values= np.abs(values[:]-x)
	x= values.min()
	pos= np.where(values == x)
	if pos[0].size > 0 and x <= 1./nd:		
		return pos[0][0]
	else:
		return None

def checkRowPosition(r0,r1):
	'''' Returns the sorted row positions'''
	if r0 > r1:
		return r1, r0
	else:
		return r0, r1

def joinMaps(inputTuple):
	'''Merges maps starting from an input tuple that specifies the output map name, the number of rows\
 and the number rows, columns, ULL X and Y coordinates, cell length and the missing value identifer and a list of input maps'''
	outputFileName= inputTuple[0]
	nrRows= inputTuple[1]
	nrCols= inputTuple[2]
	xMin= inputTuple[3]
	yMax= inputTuple[4]
	cellLength= inputTuple[5]
	MV= inputTuple[6]
	fileNames= inputTuple[7]
	cloneFileName= inputTuple[8]
	#-echo to screen
	print 'combining files for %s' % outputFileName,
	#-get extent
	xMax= xMin+nrCols*cellLength
	yMin= yMax-nrRows*cellLength
	xCoordinates= xMin+np.arange(nrCols+1)*cellLength
	yCoordinates= yMin+np.arange(nrRows+1)*cellLength
	yCoordinates= np.flipud(yCoordinates)
	print 'between %.2f, %.2f and %.2f, %.2f' % (xMin,yMin,xMax,yMax)
	#-set output array
	variableArray= np.ones((nrRows,nrCols))*MV
	#-iterate over maps
	for fileName in fileNames:
		print fileName
		attributeClone= getMapAttributesALL(fileName)
		cellLengthClone= attributeClone['cellsize']
		rowsClone= attributeClone['rows']
		colsClone= attributeClone['cols']
		xULClone= attributeClone['xUL']
		yULClone= attributeClone['yUL']
		# check whether both maps have the same attributes and process
		process, nd= checkResolution(cellLength,cellLengthClone)
		if process:
			#-get coordinates and locations
			sampleXMin= xULClone
			sampleXMax= xULClone+colsClone*cellLengthClone
			sampleYMin= yULClone-rowsClone*cellLengthClone
			sampleYMax= yULClone
			sampleXCoordinates= sampleXMin+np.arange(colsClone+1)*cellLengthClone
			sampleYCoordinates= sampleYMin+np.arange(rowsClone+1)*cellLengthClone
			sampleYCoordinates= np.flipud(sampleYCoordinates)
			sampleXMin= getMax(xMin,sampleXMin)
			sampleXMax= getMin(xMax,sampleXMax)
			sampleYMin= getMax(yMin,sampleYMin)
			sampleYMax= getMin(yMax,sampleYMax)
			sampleRow0= getPosition(sampleYMin,sampleYCoordinates,nd)
			sampleRow1= getPosition(sampleYMax,sampleYCoordinates,nd)			
			sampleCol0= getPosition(sampleXMin,sampleXCoordinates,nd)
			sampleCol1= getPosition(sampleXMax,sampleXCoordinates,nd)
			sampleRow0, sampleRow1= checkRowPosition(sampleRow0,sampleRow1)
			variableRow0= getPosition(sampleYMin,yCoordinates,nd)
			variableRow1= getPosition(sampleYMax,yCoordinates,nd)
			variableCol0= getPosition(sampleXMin,xCoordinates,nd)
			variableCol1= getPosition(sampleXMax,xCoordinates,nd)
			variableRow0,variableRow1= checkRowPosition(variableRow0,variableRow1)
			#-read sample array
			setclone(fileName)
			sampleArray= pcr2numpy(readmap(fileName),MV)
			sampleNrRows, sampleNrCols= sampleArray.shape
			#-create mask
			mask= (variableArray[variableRow0:variableRow1,variableCol0:variableCol1] == MV) &\
				(sampleArray[sampleRow0:sampleRow1,sampleCol0:sampleCol1] <> MV)
			#-add values
			print ' adding values in %d, %d rows, columns from (x, y) %.3f, %.3f and %.3f, %.3f to position (row, col) %d, %d and %d, %d' %\
				(sampleNrRows, sampleNrCols,sampleXMin,sampleYMin,sampleXMax,sampleYMax,variableRow0,variableCol0,variableRow1,variableCol1)
			variableArray[variableRow0:variableRow1,variableCol0:variableCol1][mask]= \
				sampleArray[sampleRow0:sampleRow1,sampleCol0:sampleCol1][mask]
		else:
			print '%s does not match resolution and is not processed' % fileName
	#-report output map
	setclone(cloneFileName)
	report(numpy2pcr(Scalar,variableArray,MV),outputFileName)

##################################
######## user input ##############
##################################

MV = 1e20

# chosen date
year = 1960
chosenDate = datetime.date(int(year),12,31) # datetime.date(1979,12,31)
try:
    chosenDate = str(sys.argv[1])
except:
    pass

# map coordinates and resolution 
deltaLat= 5.0/60.0
deltaLon= 5.0/60.0
latMin= -90.
latMax= 90.0
lonMin= -180.
lonMax= 180.0

inputDirRoot = ''  
try:
    inputDirRoot = str(sys.argv[2])
except:
    pass

outputDir = inputDirRoot+"/global/maps/"
try:
	outputDir = sys.argv[3]
	if sys.argv[3] == "default": outputDir = inputDirRoot + "/global/maps/"
	if sys.argv[3] == "maps"   : outputDir = inputDirRoot + "/global/maps/"
	if sys.argv[3] == "states" : outputDir = inputDirRoot + "/global/states/"
except:
	outputDir = str(sys.argv[3])
try:
	os.makedirs(outputDir)
except:
	pass

ncores = 8
try:
    ncores = int(sys.argv[4])
except:
    pass

number_of_clone_maps = 53
try:
    number_of_clone_maps = int(sys.argv[5])
except:
    pass
areas = ['M%02d'%i for i in range(1,number_of_clone_maps+1,1)]

# set clone maps based on the system argument
#~ areas = ["M47","M48"]   ### only fot TEST CASE
try:
    areas = str(sys.argv[5])
    areas = list(set(areas.split(",")))
    if areas[0] == "Global": areas = ['M%02d'%i for i in range(1,number_of_clone_maps+1,1)] 
except:
    pass

#-main script
#-get clone
nrRows= int((latMax-latMin)/deltaLat)
nrCols= int((lonMax-lonMin)/deltaLon)

tempCloneMap = outputDir+'/temp_clone.map'
command= 'mapattr -s -R %d -C %d -P "yb2t"	-B -x %f -y %f -l %f %s' %\
	(nrRows,nrCols,lonMin,latMax,deltaLat,tempCloneMap)
os.system(command)
setclone(tempCloneMap)

#~ print areas
#~ print areas[0]

# input files where unmerged maps are saved
inputDir = os.path.join(inputDirRoot,areas[0], 'maps')
if sys.argv[3] == "default": inputDir = os.path.join(inputDirRoot,areas[0], 'maps')
if sys.argv[3] == "maps"   : inputDir = os.path.join(inputDirRoot,areas[0], 'maps')
if sys.argv[3] == "states" : inputDir = os.path.join(inputDirRoot,areas[0], 'states')
files = getFileList(inputDir, '*%s.map' % chosenDate)


ncores = min(len(files), ncores)
print
print
print 'Using %d cores to process' % ncores,
print
print

for fileName in files.keys():
	#~ print fileName,
	files[fileName]= {}
	ll= []
	outputFileName= os.path.join(outputDir,fileName)
	for area in areas:
		#~ print area
		inputFileName= os.path.join(inputDirRoot, area, 'maps', fileName)
		if sys.argv[3] == "default": inputFileName = os.path.join(inputDirRoot, area, 'maps',   fileName)
		if sys.argv[3] == "maps"   : inputFileName = os.path.join(inputDirRoot, area, 'maps',   fileName)
		if sys.argv[3] == "states" : inputFileName = os.path.join(inputDirRoot, area, 'states', fileName)
		ll.append(inputFileName)
	files[fileName]= tuple((outputFileName,nrRows,nrCols,lonMin,latMax,deltaLat,MV,ll[:],tempCloneMap))

#~ # this is for testing
#~ joinMaps(files[fileName])

print
print
pool = Pool(processes=ncores)		# start "ncores" of worker processes
pool.map(joinMaps,files.values())
print
print

#-remove temporary file
os.remove(tempCloneMap)
print ' all done'
print
print
