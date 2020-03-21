import os, time
import numpy as np
import pcraster as pcr
from pcrGlobalGeometry import getArcDistance

def getMappedLocations(mappedLocations,MV= -999.9):
	'''Returns an array holding per row entries of the row and column number as well of \
the mapped value itself from a map or array.'''
	#-determine whether the entry is a PCRaster map or an array
	if isinstance(mappedLocations,pcr._pcraster.Field):
		#-convert to array
		mappedLocations= pcr.pcr2numpy(mappedLocations, int(MV))
	#-process array
	if not isinstance(mappedLocations, np.ndarray) or mappedLocations.ndim != 2:
		sys.exit('%s cannot be processed'% type(mappedLocations))
	else:
		#-get rows and colums
		rows= np.ones((mappedLocations.shape))
		columns= np.ones((mappedLocations.shape))
		for column in xrange(columns.shape[1]):
			rows[:,column]*= np.arange(1,rows.shape[0]+1)
		for row in xrange(rows.shape[0]):
			columns[row,:]*= np.arange(1,columns.shape[1]+1)
		#-initialize locations
		locations= np.vstack([rows[mappedLocations > 0],\
			columns[mappedLocations > 0], mappedLocations[mappedLocations > 0]])
		locations= locations.transpose()
		#-return locations
		return locations

def main():
	#-MV
	MV= -999.9
	#-correlation decay distance for precipitation in m
	correlationDecayDistance= 450.#450.e3
	#-read in a map with station locations and get row, col, value from original PCRaster map
	stations= pcr.pcr2numpy(pcr.readmap('station_locations.map'),MV)
	stationLocations= getMappedLocations(stations, MV)
	#-get latitude and longitude
	latitude= pcr.pcr2numpy(pcr.ycoordinate(pcr.boolean(1)),MV).astype(np.float64)
	longitude= pcr.pcr2numpy(pcr.xcoordinate(pcr.boolean(1)),MV).astype(np.float64)
	#-iterate over all stations
	weight= np.zeros(latitude.shape)
	mask= np.zeros(latitude.shape, dtype= bool)
	print 'processing %d station locations' % stationLocations.shape[0]
	for station in stationLocations:
		row, col, value= tuple(station)
		latOrigin= latitude[row-1, col-1]
		lonOrigin= longitude[row-1, col-1]
		arcDistance= getArcDistance(latOrigin, lonOrigin, latitude, longitude)*1.e-3
		weight+= value*np.maximum(0.,correlationDecayDistance-arcDistance)/correlationDecayDistance
		mask[(arcDistance <= correlationDecayDistance) | mask]= True	
	weight= np.minimum(1,weight)
	pcr.report(pcr.numpy2pcr(pcr.Scalar,arcDistance,MV),'distance.map')
	pcr.report(pcr.numpy2pcr(pcr.Scalar,weight,MV),'weight.map')
	pcr.report(pcr.numpy2pcr(pcr.Boolean,mask,-1),'mask.map')
	
if __name__ == '__main__':
	main()


