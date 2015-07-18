import os, sys, calendar
from types import NoneType
from pcrBasicFunctions import stackAverage
import pcraster as pcr
from pcraster.framework import generateNameT

def main():

	stores=  ['snowcov', 'stor2x', 'stor3x',  'intstor', 'stor1x', 'snowliq', 'wact', 'satf', 'efrac']
	MV= -999
	
	if len(sys.argv) > 2:
		inputDirectory= sys.argv[1]
		year= int(sys.argv[2])
		numberDays= 365
		if calendar.isleap(year): numberDays= 366
		extensionDays= '.%03d' % numberDays
		print extensionDays
		print 'processing data from %s'  % inputDirectory
		#-obtain roots
		fileRoots= []
		for fileName in os.listdir(inputDirectory):
			fileRoot, extension= os.path.splitext(fileName)
			fileRoot= fileRoot.rstrip('0')
			if extension ==  extensionDays:
				fileRoots.append(fileRoot)
		pcr.setclone(os.path.join(inputDirectory,generateNameT(fileRoots[0],numberDays)))
		#-process roots
		for fileRoot in fileRoots:
			fileName= os.path.join(inputDirectory,generateNameT(fileRoot,1))
			if os.path.isfile(fileName):
				print ' processing %s' % fileRoot,
				startDay= 1
				for month in xrange(1,13):
					endDay= startDay+ calendar.monthrange(year,month)[1]
					monthlyField= stackAverage(inputDirectory,fileRoot,startDay,endDay)
					if fileRoot not in stores:
						if month == 1: print 'as total'
						monthlyField*=  pcr.ifthen(monthlyField <> MV,pcr.scalar(endDay-startDay))
						fileName= fileRoot[:5]+'tot'
					else:
						if month == 1: print 'as average'
						monthlyField*=  pcr.ifthen(monthlyField <> MV,pcr.scalar(1.0))
						fileName= fileRoot[:5]+'avg'
					pcr.report(monthlyField,os.path.join(inputDirectory,generateNameT(fileName,month)))
					#-update days
					startDay= endDay
	else:
		sys.exit('command line input not defined')

if __name__ == '__main__':
	main()

