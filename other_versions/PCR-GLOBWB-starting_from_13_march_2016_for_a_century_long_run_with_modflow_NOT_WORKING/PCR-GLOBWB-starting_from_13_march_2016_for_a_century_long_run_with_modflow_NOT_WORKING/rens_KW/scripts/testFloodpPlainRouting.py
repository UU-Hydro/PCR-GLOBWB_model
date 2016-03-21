import os, sys
import logging

import virtualOS as vos
from routing import Routing
from configuration import Configuration
import pcraster as pcr
from pcraster.framework import generateNameT

def main():
	#-get configuration from file
	configuration = Configuration()
	tempDir= os.path.join(configuration.globalOptions['outputDir'],'test')
	if not os.path.isdir(tempDir): os.makedirs(tempDir)
	#-obtain ldd map and cell area
	lddMap = vos.readPCRmapClone(\
		configuration.routingOptions['lddMap'],
		configuration.cloneMap,configuration.tmpDir,configuration.globalOptions['inputDir'],True)
	#-initialize routing module
	routing= Routing(configuration,None,lddMap)
	
	routing.wMean= routing.constantChannelWidth
	
	#-iterate over channel storage capacity
	channelStorageFractions= [0.,1.,2.,3.,5.,10.,5.,3.,2.,1.,0.]
	for iCnt in xrange(len(channelStorageFractions)):
		#-invoke for each storage the function kinAlphaDynamic and 
		# return floodFrac,floodZ,alphaQ, dischargeInitial
		print '%3d %6.3f' % (iCnt, channelStorageFractions[iCnt])
		channelStorage= channelStorageFractions[iCnt]*routing.channelStorageCapacity
		#-return values
		floodFrac,floodZ,alphaQ, dischargeInitial= routing.kinAlphaDynamic(channelStorage)
		if channelStorageFractions[iCnt] > 0:
			floodVolume= floodFrac*routing.cellArea*floodZ+routing.channelStorageCapacity
		else:
			floodVolume= pcr.scalar(0)
		#-report
		pcr.report(channelStorage,os.path.join(tempDir,generateNameT('chanstor',iCnt+1)))
		pcr.report(floodFrac,os.path.join(tempDir,generateNameT('fldfrac',iCnt+1)))
		pcr.report(floodZ,os.path.join(tempDir,generateNameT('flddepth',iCnt+1)))
		pcr.report(floodVolume,os.path.join(tempDir,generateNameT('fldvol',iCnt+1)))
		pcr.report(dischargeInitial,os.path.join(tempDir,generateNameT('qini',iCnt+1)))

if __name__ == '__main__':
	sys.exit(main())
