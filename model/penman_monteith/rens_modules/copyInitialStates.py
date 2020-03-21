import os, shutil

sourceIniPath= '/scratch/rens/hadgem2_es_historical/states/'
targetIniPath= '/home/beek0120/PCR-GLOBWB/WaterTemperature/initialconditions/hadgem2_es_historical/states/warmstates_2005'

sourceStr= '2005-12-31'
targetStr= 'ini'

for fileName in os.listdir(sourceIniPath):
	if sourceStr in fileName:
		sourceFileName= os.path.join(sourceIniPath,fileName)
		try:
			fileName= fileName.replace(sourceStr,targetStr)
		except:
			pass
		targetFileName= os.path.join(targetIniPath,fileName)
		try:
			shutil.copy(sourceFileName, targetFileName)
			print 'copied: %s => %s' % (sourceFileName, targetFileName)
		except:
			sys.exit('cannot copy: %s => %s' % (sourceFileName, targetFileName))
