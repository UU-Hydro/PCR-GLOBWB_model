import os, sys
import numpy as np
import pcraster as pcr
from pcraster.framework import generateNameT

def extractTSSList(fileRoot, initialStep, finalStep, stepIncrement, cellID):
	timeSteps= range(initialStep,finalStep+1,stepIncrement)
	tssList= [0.]*len(timeSteps)
	for timeStep in timeSteps:
		fileName= generateNameT(fileRoot,timeStep)
		tssList[timeSteps.index(timeStep)]= pcr.cellvalue(pcr.readmap(fileName),cellID)[0]
	return timeSteps,tssList

def writeTSS(tssFileName,timeSteps,timeValues,idList= [],timeFormat= '%4d', valueFormat= '%12.3e',\
	header= ''):
	#-open file 
	if not os.path.exists(os.path.split(tssFileName)[0]):
		os.makedirs(os.path.split(tssFileName)[0])
	tssFile= open(tssFileName,'w')
	#-dimensions timeValues
	if timeValues.ndim == 1:
		timeValues.shape= (-1,1)
	timeSteps= timeSteps.ravel()
	#-header
	if header == '': header= 'timeseries scalar'
	numberEntries= timeValues.shape[1]
	hStr= '%s\n%d\ntimesteps\n' % (header,numberEntries)
	for iCnt in xrange(numberEntries):
		if len(idList) > 0:
			hStr+= '%d: %s\n' % (iCnt+1,idList[iCnt])
		else:
			hStr+= '%d\n' % (iCnt+1)
	tssFile.write(hStr)
	#-entries
	for nCnt in xrange(timeSteps.size):
		wStr= timeFormat % timeSteps[nCnt]
		for iCnt in xrange(numberEntries):
			wStr+= '\t'+valueFormat % timeValues[nCnt,iCnt]
		wStr+='\n'
		tssFile.write(wStr)
	tssFile.close()

def main():
	#-init
	cloneMap= '/scratch/rens/debug30min/RhineMeuse_2.0/maps/catclone.map'
	outputPath= '/scratch/rens/debug30min/RhineMeuse_2.0/defaultRun'
	fileRoots= ['/scratch/rens/debug30min/RhineMeuse_2.0/results/q1x',\
	'/scratch/rens/debug30min/RhineMeuse_2.0/results/q2x',\
	'/scratch/rens/debug30min/RhineMeuse_2.0/results/q3x']
	latitude= 49.75
	longitude= 9.75
	#-get id
	pcr.setclone(cloneMap)
	cellID= pcr.cellvalue(pcr.mapmaximum(\
		pcr.ifthen((pcr.ycoordinate(pcr.boolean(1)) == latitude) &\
			(pcr.xcoordinate(pcr.boolean(1)) == longitude),\
				pcr.uniqueid(pcr.boolean(1)))),1)[0]
	cellID= int(cellID)
	#-get values and write
	for fileRoot in fileRoots:
		varName= os.path.split(fileRoot)[1]
		tssFileName= os.path.join(outputPath,'%s.tss' % varName)
		timeSteps, timeValues= extractTSSList(fileRoot,1,365,1,cellID)
		writeTSS(tssFileName,np.array(timeSteps),np.array(timeValues),\
			header= '%s at ID %d, lat. %.2f, lon %.2f' % (varName, cellID, latitude, longitude))
		
		
	
		
if __name__ == '__main__':
	sys.exit(main())
