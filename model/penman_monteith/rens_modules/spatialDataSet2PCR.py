import os, sys, types
import subprocess
import pcraster as pcr

def checkCoordinate(v1, v2, delta_v1, delta_v2):
	#-check coordinates on the basis of delta_v, the minimum resolution
	delta_v= min(abs(delta_v1),abs(delta_v2))
	return abs(v1-v2) < 0.5*delta_v

def compareSpatialAttributes(sourceSpatialDataSet,targetSpatialDataSet, resamplePrecision= 1.e-5):
	'''Compares the attributes of two spatial datasets defined by the spatialAttributes instance\
 taking the second input as target.\
 '''
	#-check if the maps have the same dimensions
	sameDimensions= sourceSpatialDataSet.numberCols == targetSpatialDataSet.numberCols and \
		sourceSpatialDataSet.numberRows == targetSpatialDataSet.numberRows
	#-compute resample ratios
	xResampleRatio= sourceSpatialDataSet.xResolution/targetSpatialDataSet.xResolution
	yResampleRatio= sourceSpatialDataSet.yResolution/targetSpatialDataSet.yResolution
	#-check the position of the corner coordinates and determine whether the target area fits
	# within the extent of the source data set
	sameCoordinates= {}
	fitsExtent= True
	for coordKey in ['xLL','xUR','yLL','yUR']:
		resolutionKey= '%sResolution' % coordKey[:1]
		sameCoordinates[coordKey]= checkCoordinate(getattr(sourceSpatialDataSet,coordKey),\
			getattr(targetSpatialDataSet,coordKey),getattr(sourceSpatialDataSet,resolutionKey),\
			getattr(targetSpatialDataSet,resolutionKey))
		fitsExtent &= sameCoordinates[coordKey]
	#-determine whether the maps fits the extent if the coordinates of the corners do not match
	if not fitsExtent:
		fitsExtent= targetSpatialDataSet.xLL >= sourceSpatialDataSet.xLL and \
			targetSpatialDataSet.xLL < sourceSpatialDataSet.xUR and \
			targetSpatialDataSet.xUR > sourceSpatialDataSet.xLL and \
			targetSpatialDataSet.xUR <= sourceSpatialDataSet.xUR and \
			targetSpatialDataSet.yLL >= sourceSpatialDataSet.yLL and \
			targetSpatialDataSet.yLL < sourceSpatialDataSet.yUR and \
			targetSpatialDataSet.yUR > sourceSpatialDataSet.yLL and \
			targetSpatialDataSet.yUR <= sourceSpatialDataSet.yUR
	#-same resolution
	sameResolution= abs(1-xResampleRatio) < resamplePrecision and\
			abs(1-yResampleRatio) < resamplePrecision
	#-decide on output: does the map to be clipped or warped, and whether it has
	# to be rescaled or not
	return fitsExtent, sameResolution, xResampleRatio, yResampleRatio
	# /* end of function */

class spatialAttributes:
  #-retrieves attributes of a spatial dataset

  def __init__(self, inputFileName, maxLength= -1):
		'''Returns the map attributes for the spatial file name specified'''
		#-max length specifies a cutoff to speed up processing of large datasets with multible bands
		#-set local variables: mapInformation holds identifier strings and offset for the variables of interest
		mapInformation={}
		mapInformation['dataFormat']= 'Driver', 0, types.StringTypes
		mapInformation['numberRows']= 'Size is', 1, types.IntType
		mapInformation['numberCols']= 'Size is', 0, types.IntType
		mapInformation['xResolution']= 'Pixel Size =', 0, types.FloatType
		mapInformation['yResolution']= 'Pixel Size =', 1, types.FloatType
		mapInformation['xLL']= 'Lower Left', 0, types.FloatType
		mapInformation['yLL']= 'Lower Left', 1, types.FloatType
		mapInformation['xUR']= 'Upper Right', 0, types.FloatType
		mapInformation['yUR']= 'Upper Right', 1, types.FloatType
		mapInformation['dataType']= 'Type=', 0, types.StringTypes
		mapInformation['minValue']= 'Min=', 0, types.FloatType
		mapInformation['maxValue']= 'Max=', 0, types.FloatType
		mapInformation['noDataValue']= 'NoData Value=', 0, types.FloatType
		#-set dictionary to hold relevant information
		mapAttributes={}
		#-get information with gdalinfo
		command= 'gdalinfo %s' % inputFileName
		cOut,err = subprocess.Popen(command, stdout= subprocess.PIPE,\
			stderr= subprocess.PIPE,shell=True).communicate()
		if err != '' and not err[:7].lower() == 'warning':
				sys.exit('Error: no information could be retrieved for the spatial dataset %s' % inputFileName)
		#-get map information
		for mapAttribute, info in mapInformation.iteritems():
			matched= False
			rawList= cOut.split('\n')[:maxLength]
			key= info[0]
			entryNumber= info[1]
			typeInfo= info[2]
			#-iterate until the entry is found or the list of entries is empty
			while not matched and len(rawList) > 0:
				#-pop first entry with white space, including \r removed
				entry= rawList.pop(0).strip()
				#-if found, set matched true and process
				if key in entry:
					matched= True
					posCnt= entry.find(key)
					#-if entry found, get actual value
					if posCnt >= 0:
						posCnt+= len(key)
						rawStr= entry[posCnt:].split(',')[entryNumber]
						rawStr= rawStr.strip('=:() \t')
						if typeInfo in [types.IntType,types.FloatType,types.LongType]:
							rawStr= rawStr.split()[0]
						#-rawStr of entry returned, process accordingly
						if typeInfo == types.IntType or typeInfo ==  types.LongType:
							try:
								mapAttributes[mapAttribute]= int(rawStr)
							except:
								sys.exit('Error: map attributes could not be processed for %s' % mapAttribute)
						elif typeInfo == types.FloatType:
							try:
								mapAttributes[mapAttribute]= float(rawStr)
							except:
								sys.exit('Error: map attributes could not be processed for %s' % mapAttribute)
						else:
							mapAttributes[mapAttribute]= rawStr
			if mapAttribute in ['xResolution','yResolution']:
				mapAttributes[mapAttribute]= abs(mapAttributes[mapAttribute])
			#-set class attributes
			if mapAttribute in mapAttributes.keys():
				setattr(self,mapAttribute,mapAttributes[mapAttribute])
			else:
				setattr(self,mapAttribute,None)
	# /* end of spatialAttributes class */

class spatialDataSet:
	#~ '''Handles the processing of spatial datasets using GDAL;\
 #~ it requires the specification of the bounding box and resolution
#~ stores data as numpy array in memory under the variable name specified'''

	def __init__(self, variableName, inputFileName, typeStr, valueScale,\
			xLL, xUR, yLL, yUR, xResolution, yResolution, xResampleRatio, yResampleRatio,\
			resampleMethod= 'near', outputFileName= None, band= None, attribute= None, warp= False, test= False):
		#-set root for temporary file names
		tempFileRoot= 'temp_%s' % variableName
		#-set the source and target file name
		if isinstance(outputFileName,types.NoneType):
			outputFileName= '%s.map' % tempFileRoot
		#-process particular situations such as shape files and information in bands
		if os.path.splitext(inputFileName)[1] == '.shp':
			#-process shape file
			command= 'gdal_rasterize -a %s -ot %s -tr %f %f -te %f %f %f %f  %s %s.tif -q' %\
				(attribute, typeStr, xResolution, yResolution, xLL, yLL, xUR, yUR,\
				inputFileName, tempFileRoot)
			if test: print command
			cOut,err = subprocess.Popen(command, stdout= subprocess.PIPE,\
				stderr= subprocess.PIPE,shell=True).communicate()
			if err != '' and not err[:7].lower() == 'warning':
					sys.exit('Error: no information could be retrieved from the spatial dataset %s' % inputFileName)
			inputFileName= '%s.tif' % tempFileRoot
		elif band != 0 and not isinstance(band,types.NoneType):
			#-process band
			command= 'gdal_translate -ot %s -of PCRaster -b %d -mo VALUE_SCALE=%s %s %s_%d.map -q' %\
				(typeStr, band, valueScale, inputFileName, tempFileRoot, band)
			if test: print command
			cOut,err = subprocess.Popen(command, stdout= subprocess.PIPE,\
				stderr= subprocess.PIPE,shell=True).communicate()
			if err != '' and not err[:7].lower() == 'warning':
					sys.exit('Error: no information could be retrieved from the spatial dataset %s' % inputFileName)
			inputFileName= '%s_%d.map' % (tempFileRoot, band)
		#-in case the input needs to be warped, process accordingly
		if warp:
			#-warp dataset and reset resolution
			command= 'gdalwarp -of GTiff -ot %s -te %f %f %f %f -tr %f %f -r %s %s %s2.tif -q -overwrite -nomd' %\
				(typeStr, xLL, yLL, xUR, yUR, xResolution, yResolution, resampleMethod, inputFileName, tempFileRoot)
			#~ command= 'gdalwarp -of GTiff -ot %s -te %f %f %f %f -tr %f %f -r %s %s %s2.tif -q -overwrite' %\
				#~ (typeStr, xLL, yLL, xUR, yUR, xResolution, yResolution, resampleMethod, inputFileName, tempFileRoot)			
			if test: print command
			cOut,err = subprocess.Popen(command, stdout= subprocess.PIPE,\
				stderr= subprocess.PIPE,shell=True).communicate()
			if err != '' and not err[:7].lower() == 'warning':		
				sys.exit('Error: no information could be retrieved from the spatial dataset %s' % inputFileName)
			inputFileName= '%s2.tif' % tempFileRoot
			xResampleRatio= 1.; yResampleRatio= 1.
		#-convert to PCRaster map of chosen extent
		command= 'gdal_translate -ot %s -of PCRaster -mo VALUE_SCALE=%s -projwin %f %f %f %f -outsize %s %s %s %s -q' %\
			(typeStr, valueScale, xLL, yUR, xUR, yLL, '%.3f%s' % (100.*xResampleRatio,'%'),'%.3f%s' % (100.*yResampleRatio,'%'),\
			inputFileName, outputFileName)
		if test: print command
		cOut,err = subprocess.Popen(command, stdout= subprocess.PIPE,\
			stderr= subprocess.PIPE,shell=True).communicate()
		if err != '' and not err[:7].lower() == 'warning':
				sys.exit('Error: no information could be retrieved from the spatial dataset %s' % inputFileName)
		#-read resulting map
		setattr(self,variableName,pcr.readmap(outputFileName))
		#-remove any temporary files
		for tempFileName in os.listdir(os.getcwd()):
			if os.path.splitext(tempFileName)[1] in ['.map','.tif','.xml']:
				if tempFileRoot in tempFileName:
					try:
						os.remove(tempFileName)
					except:
						pass
	# /* end of spatialAttributes class */
