import os
import numpy as np
import pcraster as pcr
from math import pi as m_pi

pcr.setglobaloption('radians')
deg2Rad= m_pi/180.

def getEquivalentCellArea(arcResolution, radius= 6371221.3, testVerbose= False):
	'''Computes an array with the equivalent cell area in metres squared \
for a perfect sphere of given radius subdivided into geographic degrees. \
Input variables include:\n
- arcResolution: the resolution of the map in decimal degrees,\n
- radius: the radius of the sphere in metres, set by default to \
that of Earth (6371221.3 m).'''
	#-set local variables
	latOrigin= 90.0
	lonOrigin= -180.
	latExtent= 180.
	lonExtent= 360.
	#-set resolution and derive number of rows
	arcResolution= np.array([arcResolution], dtype= np.float64)
	#-set number of rows and columns
	nrRows= int(round(latExtent/arcResolution))
	nrCols= int(round(lonExtent/arcResolution))
	#-echo:
	if testVerbose:
		print ' * generating the cell area in the units of the radius specified over a geographic grid with \
%d, %d rows and columns with a resolution of %f decimal degrees' % (nrRows, nrCols, arcResolution)
	#-generate arrays with latitudes and longitudes at cell-centres
	latitude= np.ones((nrRows, nrCols))*latOrigin
	longitude= np.ones((nrRows, nrCols))*lonOrigin
	for colCnt in xrange(nrCols):
		latitude[:,colCnt]-= (np.arange(nrRows)+0.5)*arcResolution
	for rowCnt in xrange(nrRows):
		longitude[rowCnt,:]+= (np.arange(nrCols)+0.5)*arcResolution
	#-check on generated extent
	deltaLat= (latitude[-1,-1]/(latOrigin-(latExtent-0.5*arcResolution))-1.)*100.
	deltaLon= (longitude[-1,-1]/(lonOrigin+(lonExtent-0.5*arcResolution))-1.)*100.
	if testVerbose:
		print '   the differences between the generated latitude, longitude amount to \
 %.4f, %.4f %s' % (deltaLat, deltaLon,'%')
	#-compute cell area in units of radius
	cellArea= np.abs(np.sin((latitude+0.5*arcResolution)*deg2Rad)-np.sin((latitude-0.5*arcResolution)*deg2Rad))
	cellArea*= arcResolution*deg2Rad*radius**2
	if testVerbose:
			print '   the average, min and max cell areas in units of the radius of length %f are \
%.f, %.f, and %.f' % (radius,cellArea.mean(), cellArea.min(), cellArea.max()),
	totalArea= cellArea.sum()
	sphereArea= 4*m_pi*radius**2 
	deltaArea= (totalArea/sphereArea-1.)*100.
	if testVerbose:
			print 'equivalent to a total area of %f compared to %f for an ideal sphere, \
with a deviation of %f %s' % (totalArea, sphereArea, deltaArea, '%')	
	#-return cellArea and coordinates
	return cellArea, latitude, longitude
	
def getArcDistance(latA, lonA, latB, lonB, radius= 6371221.3, testVerbose= False):
	'''Computes the distance between two points, positioned by \
their geographic coordinates along the surface of a perfect sphere \
in units given by the radius used. Input variables include:\n
- latA, latB: the latitude of the points considered in decimal degrees,\n
- lonA, lonB: the longitude of the points considered in decimal degrees,\n
- radius: the radius of the sphere in metres, set by default to \
that of Earth (6371221.3 m).'''
	#-convert all coordinates to radians
	pA= latA*deg2Rad; pB= latB*deg2Rad
	lA= lonA*deg2Rad; lB= lonB*deg2Rad
	Z= np.sin(pA)*np.sin(pB)+\
		np.cos(pA)*np.cos(pB)*\
		np.cos(lA-lB)
	#-set arcDist default to zero and create mask of cells to be processed
	if Z.shape == ():
		Z= np.array([Z])
	mask= np.zeros(Z.shape)
	mask= (Z < 1) & (Z > -1)
	arcDist= np.zeros(Z.shape)
	arcDist[Z <= -1]= m_pi
	arcDist[mask]= np.arccos(Z[mask])
	arcDist*= radius
	if testVerbose:
		print ' * along an ideal sphere of radius %f, the distance between the points at lat, lon \
%f, %f and %f, %f respectively amounts to %f' % (radius, latA, lonA, latB, lonB, arcDist)
	#-return arcDist
	return arcDist

def getMappedLocations(mappedLocations,MV):
	'''Returns an array holding per row entries of the row and column number as well of \
       the mapped value itself from a map or array.'''
	#-determine whether the entry is a PCRaster map or an array
	if isinstance(mappedLocations,pcr._pcraster.Field):
		#-convert to array
		mappedLocations= pcr.pcr2numpy(mappedLocations, MV)
	#-process array
	if not isinstance(mappedLocations, np.ndarray) or mappedLocations.ndim != 2:
		sys.exit('%s cannot be processed'% type(mappedLocations))
	else:
		#-get rows and colums
		rows = np.ones((mappedLocations.shape))
		columns = np.ones((mappedLocations.shape))
		for column in xrange(columns.shape[1]):
			rows[:,column]*= np.arange(1,rows.shape[0]+1)
		for row in xrange(rows.shape[0]):
			columns[row,:]*= np.arange(1,columns.shape[1]+1)
		#-initialize locations
		locations = np.vstack([rows[(mappedLocations > 0) & (mappedLocations <> MV)],\
			                columns[(mappedLocations > 0) & (mappedLocations <> MV)], mappedLocations[(mappedLocations > 0) & (mappedLocations <> MV)]])
		locations= locations.transpose()
		#-return locations
		return locations

