import os
import pcraster as pcr

#-init
inputPath= '/data/hydroworld/forcing/ERA20C/RawData'
outputPath= '/scratch/rens/era20c'
keepMaps= False
meteoVariables= {'precipitation': 'totp%04d.nc'}
years= range(1900,2011)
resampleRatio= 0.5/(5./60.)
resampleRatioStr= '%f' % (resampleRatio*100)+'%'
tmpFile= 'temp.nc'
cellArea= pcr.readmap('/data/hydroworld/PCRGLOBWB20/input5min/routing/cellsize05min.correct.map')
cellArea= pcr.ifthenelse(pcr.defined(pcr.readmap('/data/hydroworld/PCRGLOBWB20/input5min/routing/lddsound_05min.map')),cellArea,0)

#-start
if not os.path.isdir(outputPath):
	os.makedirs(outputPath)

tmpFile= 'temp.nc'

for meteoVariable, fileRoot in meteoVariables.iteritems():
	txtFile= open(os.path.join(outputPath,'%s.txt' % meteoVariable),'w')
	txtFile.write('Annual total for %s in km3' % meteoVariable)
	for year in years:
		iFile= fileRoot % year
		oFile= iFile.replace('.nc','.map')
		iFile= os.path.join(inputPath,iFile)
		oFile= os.path.join(outputPath,oFile)
		command= 'cdo yearsum %s %s' % (iFile, tmpFile)
		os.system(command)
		command= 'gdal_translate -of PCRaster -ot FLOAT32 -mo VALUESCALE=VS_SCALAR -outsize %s %s %s %s' % (resampleRatioStr,resampleRatioStr,tmpFile,oFile)
		os.system(command)
		annualTotal= pcr.cellvalue(pcr.maptotal(1.e-9*cellArea*pcr.max(0,pcr.readmap(oFile))),1)[0]
		wStr= '%04d, %.1f' % (year,annualTotal)
		txtFile.write('%s\n' % wStr)
		print wStr
		if not keepMaps:
			os.remove(oFile)
			os.remove(tmpFile)
			os.remove(oFile+'.aux.xml')
	txtFile.close()
