import os
import pcraster as pcr

pathMaps= 'maps'
lakeID= pcr.readmap(os.path.join(pathMaps,'wfd_lakeid.map'))
zones= pcr.nominal(pcr.ycoordinate(pcr.boolean(1))/pcr.celllength()+0.5)
for fileName in os.listdir(pathMaps):
	if 'kc_wat' in fileName:
		kc= pcr.readmap(os.path.join(pathMaps,fileName))
		kc1= pcr.ifthen(lakeID != 0, kc)
		kc=  pcr.ifthen(lakeID == 0, kc)
		kc= pcr.ifthen(pcr.defined(lakeID),pcr.cover(kc1,kc,pcr.areaaverage(kc,zones)))
		pcr.report(kc,os.path.join(pathMaps,fileName))
		


