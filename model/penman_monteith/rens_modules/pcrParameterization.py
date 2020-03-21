################################################################################
# PCR-GLOBWB V1.0 - Utrecht University 2014, created by Rens van Beek          #
################################################################################
#-pcrParameterization: module containing classes and functions to process
# the parameterization of the pure PCRaster version of PCR-GLOBWB, Version 1.0
################################################################################

import os, sys, types
import datetime, calendar
import subprocess
import numpy as np
import pcraster as pcr
from pcraster.framework import generateNameT
import netCDF4 as nc
from spatialDataSet2PCR import compareSpatialAttributes, spatialAttributes, spatialDataSet
from basicFunctions import createListConstructor, constructListFromDictionary

def getNCDates(dates,units,calendar):
	'''Returns the dates based on the information from the netCDF file'''
	print 'this'
	print dates[:]
	print 'this'
	print units
	print calendar
	dates= nc.num2date(dates[:],units,calendar)
	return dates

def entry2index(ncEntries,value):
	#-returns first entry of the required value
	index= None
	ncEntries= ncEntries[:]
	index= np.arange(ncEntries.size)[ncEntries == value]
	if index.size == 0:
		index= None
	else:
		index= int(index[0])
	return index

def datetime2naive(dateStart,dateEntry):
	#-returns the naive equivalent of a date time format to a 
	return dateEntry.toordinal()-dateStart.toordinal()+1

def composeStackName(fileName,defaultStackEntry,stackEntry, separators= ['-','_']):
	#-uses some simple rules starting from the patterns in the output file name specified
	# to return a matching file name
	#-generate string of digital characters
	digitStr= ''
	for pCnt in xrange(0,10):
		digitStr+= str(pCnt)
	#-split path and file name
	path, fileName= os.path.split(fileName)
	#-try and substitute the argument, by a test string, this allows for multiple occurrences
	# and raises and error if arguments do not match
	if isinstance(defaultStackEntry,datetime.datetime):
		defaultStackEntry= defaultStackEntry.date()
		stackEntry= stackEntry.date()
	elif '%' not in fileName:
		try:
			defaultStackEntry= '%03d' % defaultStackEntry
		except:
			pass 
	testStr= str(defaultStackEntry)
	#-in case the fileName has no extension, testStr is not encountered,
	# and length less than 8 characters, the file follows the PCRaster map stack convention
	if testStr not in fileName and len(fileName) <= 8 and\
			os.path.splitext(fileName)[1] == '':
		#-PCRaster map stack
		try:
			fileName= generateNameT(fileName,stackEntry)
		except:
			fileName+= '.%s' % str(stackEntry)
		return os.path.join(path,fileName)
	else:
		#-single entry
		try:
			argumentList= [float(testStr)]
		except:
			argumentList= [testStr]
		#-multiple entries
		nrArguments= fileName.count('%')
		if nrArguments > 1:
			argumentList= []
			for separator in separators:
				if separator in testStr:
					for argument in testStr.split(separator):
						try:
							argumentList.append(float(argument))
						except:
							argumentList.append(argument)
		#-substitution
		if nrArguments > 0:
			try:
				fileName= fileName % tuple(argumentList)
			except:
				message= 'Error: %s cannot be substituted in file name %s' %\
					(testStr,fileName)
				sys.exit(message)
		if nrArguments > 1:	
			#-test entries
			for separator in separators:
				if separator in testStr:
					if len(testStr.split(separator)) != len(str(stackEntry).split(separator)):
						message= 'Error: formats of %s and %s cannot be substituted for file' %\
							(testStr,str(stackEntry,fileName))
						sys.exit(message)				
		#-check if the string of the defaultStackEntry is contained by the fileName;
		# matching starts from the rear
		#-try and find string of defaultStackEntry in case no argument substitution is found
		posCnt= len(fileName)
		posCnt= posCnt-len(testStr)
		match= False
		replaceStr= ''
		while match == False and posCnt >= 0:
			if fileName[posCnt:posCnt+len(testStr)] == testStr:
				#-set match and replacement string together with counter
				match= True
				replaceStr= testStr
				pCnt= posCnt-1
				while pCnt >= 0:
					if len(replaceStr) > 0 and (fileName[pCnt:pCnt+1] in digitStr and\
							replaceStr[:1] in separators) or fileName[pCnt:pCnt+1] in digitStr[1:]:
						replaceStr= ''
						match= False
					elif len(replaceStr) > 0 and fileName[pCnt:pCnt+1] in '0.' or\
							(fileName[pCnt:pCnt+1] in separators and not replaceStr[:1] in separators):
						replaceStr= fileName[pCnt:pCnt+1]+replaceStr
						if fileName[pCnt:pCnt+1] == '.':
							break
					else:
						#-escape if no separators, points or digital characters are found
						break
					#-update pCnt
					pCnt-= 1
			#-update posCnt	
			posCnt-= 1
		#-if a valid replaceStr is removed, replace this in the fileName
		# by a standard string argument substitution
		if len(replaceStr) > 0:
			#-remove any leading zeroes and points or separator charachters
			pCnt= replaceStr.find('.')
			if pCnt >= 0:
				replaceStr= replaceStr[pCnt+1:]
			for separator in separators:
				replaceStr= replaceStr.strip(separator)
			#-replace the string in the file name by a standard argument substitution		
			fileName= fileName.replace(replaceStr,'%s')
		#-try and subsitute the stack entry
		testStr= str(stackEntry)
		while len(testStr) < len(replaceStr):
			testStr= '0'+testStr
		try:
			fileName= fileName % testStr
		except:
			message= 'Error: %s cannot be substituted in file name %s' %\
				(testStr,fileName)
			sys.exit(message)
		#-return file name
		return os.path.join(path,fileName)

def getSplitPath(path):
	'''Splits the path into its entries, including drive and absolute path indicator'''
	absolutePath= os.path.isabs(path)
	pathEntries= []
	drive,path = os.path.splitdrive(path)
	if drive != '':
		pathEntries.insert(0,drive)
	iCnt= len(pathEntries)
	if absolutePath:
		absPathIndicator= os.path.join(' ',' ').strip()
		pathEntries.insert(iCnt,absPathIndicator)
		path= path.lstrip(absPathIndicator)
	iCnt= len(pathEntries)
	while len(path) > 0:
		path,tail= os.path.split(path)
		if len(tail) > 0:
			pathEntries.insert(iCnt,tail)
	return pathEntries, absolutePath

def matchList(testList,sampleList):
	'''Checks the sample list against the test list and returns the\
 index of the highest non-matching entry'''
	#-set length of lists and default index to return
	plen= len(testList)
	ilen= len(sampleList)
	ilist= sampleList[:]
	ix= ilen-1
	tx= -1
	#-match entries from the left onwards; if most right-hand entry in samplelist not found
	# there is no match, if there is a match at least all preceding elements should be true as well;
	# iteration continues until all elements are passed and the last true condition returned
	for px in xrange(plen): # (min(ilen,plen)):
		#-subsample the test and sample list and create a list to validate the entries
		ilist= sampleList[ix-px:ix+1]
		plist= testList[px-len(ilist)+1:px+1]
		valid= True
		#-iterate over ilist and plist
		for lx in xrange(len(ilist)):
			valid= valid and plist[lx] == ilist[lx]
		if valid:
			tx= px
	#-remove any redundant entries from the list to be sampled
	if tx >= 0:
		for px in xrange(0,tx+1):
			if len(sampleList) > 0:
				sampleList.pop()
	#-return reduced sample list
	return sampleList
	
def composeFileName(*paths):
	'''Composes a map name out of a list of paths placed in sequence, the first\
 holding any drive letters or absolute path indicator, the last one holding the file name'''
	#-initialize the list with path entries
	paths= list(paths)
	pathEntries= []
	#-remove any NoneType entries but the last entry by empty strings
	while None in paths[:-1]:
		paths.remove(None)
	#-get the path Entries from the last list
	absolutePath= False
	while len(paths) > 0 and not absolutePath:
		#-get current path from paths and split in list
		path= paths.pop()
		subDirs, absolutePath= getSplitPath(path)
		#-compare lists of directory entries
		subDirs= matchList(pathEntries,subDirs)
		for lCnt in xrange(len(subDirs)-1,-1,-1):
			pathEntries.insert(0,subDirs[lCnt])		
	#-path entries completed, fill out full fileName
	fileName= pathEntries.pop(0)
	while len(pathEntries) > 0:
		fileName= os.path.join(fileName,pathEntries.pop(0))
	return fileName

def optionalPathSubstitution(originalStr, substitutionArguments):
	'''Returns an updated string with any arguments substituted\
 and a boolean variable indicating whether the string was updated or not'''
	substitutedStr= originalStr
	if isinstance(originalStr,types.StringTypes):
		nrRequiredArguments= substitutedStr.count('%')
		nrArguments= len(substitutionArguments)
		arguments= ['']*nrRequiredArguments
		for iCnt in xrange(nrRequiredArguments):
			arguments[iCnt]= substitutionArguments[iCnt % nrArguments]
		if nrRequiredArguments >0:
			try:
				substitutedStr= substitutedStr % tuple(arguments)
			except:
				sys.exit('Warning: the arguments in the orignal string %s have not been updated' %\
					originalStr)
	return substitutedStr, not substitutedStr == originalStr
 
#-not used, superfluous
#~ def testValidDate(date1,date2,maxOffset= None,exact= True):
	#~ '''bolts if the absolute difference in dates measured in days exceeds the offset specified'\
 #~ or if the year, month and day are different in case of an exact match'''
	#~ if exact:
		#~ return date1.year == date2.year and date1.month == date2.month and date1.day ==  date2.day
	#~ else:
		#~ if maxOffset == types.NoneType: maxOffset= 0.5
		#~ 
		#~ return abs(d1-d2) < datetime.timedelta(days= maxOffset)

def convertStandardType(entryStr, typeInformation):
	'''Converts the string passed to a type specified within the types package'''
	#-check on data type
	assert isinstance(typeInformation,types.TypeType)
	#-boolean type
	if typeInformation == types.BooleanType:
		try:
			return bool(entryStr)
		except:
			sys.exit('variable %s cannot be converted to %s' % (entryStr,typeInformation))
	#-long type
	elif typeInformation == types.LongType:
		try:
			return long(float(entryStr))
		except:
			sys.exit('variable %s cannot be converted to %s' % (entryStr,typeInformation))
	#-integer type
	elif typeInformation == types.IntType:
		try:
			return int(float(entryStr))
		except:
			sys.exit('variable %s cannot be converted to %s' % (entryStr,typeInformation))		
	#-float type
	elif typeInformation == types.FloatType:
		try:
			return float(entryStr)
		except:
			sys.exit('variable %s cannot be converted to %s' % (entryStr,typeInformation))
	#-string type
	elif typeInformation in types.StringTypes:
		try:
			return str(entryStr)
		except:
			sys.exit('variable %s cannot be converted to %s' % (entryStr,typeInformation))
	#-None type
	elif typeInformation == types.NoneType:
		try:
			return None
		except:
			sys.exit('variable %s cannot be converted to %s' % (entryStr,typeInformation))
	#-type not encountered and not processed
	else:
		sys.exit('variable %s cannot be converted to %s; type not encountered' % (entryStr, typeInformation))
	# /* end of the function to convert standard types */

def convert2List(s, separators= [',',';']):
	#-converts a string (s) of entries separated by the listed default separators into a list and returns it
	#-create initial list from string
	resultList= []
	listConstructor= createListConstructor(s,separators)
	generatedList= constructListFromDictionary(listConstructor,resultList)
	for iCnt in xrange(len(generatedList)):
		generatedList[iCnt]= generatedList[iCnt].strip()
	return generatedList

def convert2Dictionary(keys, values, keywords= []):
	#-converts the arguments into a dictionary:
	# keys: list of keys to be used in the dictionary;
	# values: either a list of the same length as keys or a dictionary
	# that is ordered at its highest level by keys;
	# keywords: a single key or list of keys to be extracted from values if
	# this is a dictionary
	if isinstance(values,list):
		if len(keys) == len(values):
			return dict([(keys[iCnt],values[iCnt]) for iCnt in xrange(len(keys))])
		else:
				sys.exit('no dictionary could be created from the information specified')
	elif isinstance(values,dict):
		for key in keys:
			if not key in values.keys():
				sys.exit('keys do not match')
		if isinstance(values[keys[0]],dict):
			x= {}
			for key in keys:
				if isinstance(keywords,list):
					x[key]= {}
					for keyword in keywords:
						x[key][keyword]= values[key][keyword]
				elif isinstance(keywords,str):
					x[key]= values[key][keywords]
			return x
		else:
			return values
	else:
			sys.exit('no dictionary could be created from the information specified')

def convertSequence2Values(seq,f,typeInformation):
	#-translates a mutable sequence consisting of strings
	# into values
	if isinstance(seq,list):
		seq= seq[:]
		for index in xrange(len(seq)):
			if not isinstance(seq[index],list) and \
					 not isinstance(seq[index],dict):
				try:
					value= f(seq[index],typeInformation)
				except:
					value= seq[index]
				seq[index]= value
			else:
				seq[index]= self.convertSequence2Values(seq[index],f,typeInformation)
	elif isinstance(seq,dict):
		seq= seq.copy()
		for key in seq.keys():
			if not isinstance(seq[key],list) and \
					 not isinstance(seq[key],dict):
				try:
					value= f(seq[key],typeInformation)
				except:
					value= seq[key]
				seq[key]= value
			else:
				seq[key]= sequence2Values(seq[index],f,typeInformation)
	return seq

class pcrObject(object):
	'''Class of a pcraster object required as model input for PCR-GLOBWB V1.0'''
	#-It contains all information to process information including
	# variable name: a descriptive name
	# inputFileName, outputFileName: file names including full paths
	# targetSpatialAttributes: a class instance, derived from spatialAttributes,
	# defining the extent and resolution of the desired output PCRaster object
	# pcrVariableType: a PCRaster VALUESCALE object or its equivalent name as string
	# resamplingAllowed: boolean indicating whether the data set can be resampled or not
	# dynamic: boolean indicating whether the dataset is dynamic, mapping one entry to many PCR objects
	# ncDynamicDimension: the name of the dynamic dimension in a netCDF file
	# dynamicStart, dynamicEnd and dynamicIncrement: start, end and increment of the dynamic variable
	#-uses gdal for interoperability
	
	def __init__(self,variableName,outputFileName,inputFileName,targetSpatialAttributes,\
		pcrVALUESCALE= pcr.Scalar, resamplingAllowed= False,\
			dynamic= False, dynamicStart= None, dynamicEnd= None, dynamicIncrement= None,\
			ncDynamicDimension= None):
		#-local variables
		dataTypes= {'Boolean': ('BYTE', 'VS_BOOLEAN'),
			'Nominal': ('INT32','VS_NOMINAL'),\
			'Ordinal': ('INT32','VS_ORDINAL'),\
			'Scalar': ('FLOAT32', 'VS_SCALAR'),
			'Directional': ('FLOAT32', 'VS_DIRECTION'),\
			'Ldd': ('BYTE', 'VS_LDD')}
		resampleMethods= {}.fromkeys(dataTypes,'near')
		resampleMethods['Scalar']= 'bilinear'
		resampleMethods['Directional']= 'bilinear'
		timeIncrements= {'day': 1.0}
		#-assign values
		self.variableName= variableName
		self.inputFileName= inputFileName
		self.outputFileName= outputFileName
		#-test dynamic
		if dynamic:
			try:
				self.inputFileName= composeStackName(self.inputFileName,dynamicStart,dynamicStart)
				self.outputFileName= composeStackName(self.outputFileName,dynamicStart,dynamicStart)
			except:
				pass
			if (isinstance(dynamicStart,types.NoneType) or	isinstance(dynamicEnd,types.NoneType) or \
					isinstance(dynamicIncrement,types.NoneType)) or \
					(os.path.splitext(self.inputFileName)[1] == '.nc' and isinstance(ncDynamicDimension,types.NoneType)):
				message= 'Error: information for dynamic variable %s not set' % self.variableName
				sys.exit(message)
		#-get information on resampling and data type
		try: 
			self.variableType= pcrVALUESCALE.name
		except:
			self.variableType= pcrVALUESCALE
		self.variableType= self.variableType.capitalize()
		self.resampleMethod= resampleMethods[self.variableType]
		self.variableType, self.valueScale = dataTypes[self.variableType]
		self.resamplingAllowed= resamplingAllowed
		#-set targetSpatialAttributes and get the attributes of the present dataset
		self.targetSpatialAttributes= targetSpatialAttributes
		self.mapAttributes= spatialAttributes(self.inputFileName)
		#-get attributes defining dynamic dimension
		try:
			dynamicIncrement= dynamicIncrement.rstrip('s')
		except:
			pass
		self.dynamic= dynamic
		self.datetimeFormat= False
		self.dynamicStart= dynamicStart
		self.dynamicEnd= dynamicEnd
		self.dynamicIncrement= dynamicIncrement
		self.ncDynamicDimension= ncDynamicDimension
		if self.dynamic:
			if not isinstance(dynamicStart,type(dynamicEnd)):
				message('Error: start and end of dynamic variable are not the same')
				sys.exit(message)
			if isinstance(dynamicIncrement,types.StringTypes) and not\
				(isinstance(dynamicStart,datetime.datetime) and isinstance(dynamicEnd,datetime.datetime)):
					message= 'Error: timed variable expected but start or end is not in datetime format'
					sys.exit(message)					
			if isinstance(dynamicStart,datetime.datetime):
				self.datetimeFormat= True
				if dynamicIncrement not in timeIncrements.keys() and\
					dynamicIncrement not in  timeIncrements.values():
					message= 'time unit %s not defined; perhaps any of' % dynamicIncrement
					for key in timeIncrements.keys(): message+= ' %s,' % key
					message= message.rstrip(',')
					message+= '?'
					sys.exit(message)
				if dynamicIncrement in timeIncrements.keys():
					self.dynamicIncrement= timeIncrements[dynamicIncrement]
	
	def __str__(self):
		if self.dynamic:
			message= 'dynamic'
		else:
			message= 'static'
		message+= ' dataset for variable %s' % self.variableName
		return message
		
	def initializeFileInfo(self):
		'''initializes all in and output file names and any corresponding dates'''
		self.fileProcessInfo= {}
		valid= True
		if not self.dynamic:
			#-static variable, set default band
			band= 0
			self.fileProcessInfo[self.inputFileName]= []
			self.fileProcessInfo[self.inputFileName].append((band,self.outputFileName))
		else:
			#-dynamic variable: is it timed or not, if so, what are the bands associated with a particular time
			#-data structure allows linkage of one input to many output files
			#-get output file root and all desired entries of the dynamic variable with its output
			desiredDynamicEntries= {}
			if self.datetimeFormat:
				self.dynamicIncrement= datetime.timedelta(self.dynamicIncrement)
			dynamicEntry= self.dynamicStart
			while dynamicEntry <= self.dynamicEnd:
				if self.datetimeFormat:					
					outputFileName= composeStackName(self.outputFileName,\
						datetime2naive(self.dynamicStart,self.dynamicStart),datetime2naive(self.dynamicStart,dynamicEntry))
				else:
					outputFileName= composeStackName(self.outputFileName,self.dynamicStart,dynamicEntry)
				desiredDynamicEntries[dynamicEntry]= outputFileName
				dynamicEntry+= self.dynamicIncrement
			#-next, process
			if os.path.splitext(self.inputFileName)[1] == '.nc':
				#-process netCDF file: multiple bands
				self.fileProcessInfo[self.inputFileName]= []
				#-in case of netCDF file, open dataset and get its entries
				rootgrp= nc.Dataset(self.inputFileName)
				try:
					ncDynamicVariable= rootgrp.variables.copy()[self.ncDynamicDimension]
				except:
					rootgrp.close()
					message= 'Error: %s does not have the required dimension %s' % \
						(self.inputFileName, self.ncDynamicDimension)
					sys.exit(message)
				if self.datetimeFormat:
					availableEntries= getNCDates(ncDynamicVariable,ncDynamicVariable.getncattr('units'),\
						ncDynamicVariable.getncattr('calendar'))
				else:
					availableEntries= ncDynamicVar[:]
				#-get values
				for dynamicEntry, outputFileName in desiredDynamicEntries.iteritems():
					#-if date format, get index
					if self.datetimeFormat:
						try:
							band= nc.date2index(dynamicEntry,ncDynamicVariable,select= 'nearest')
							valid= dynamicEntry == availableEntries[band]
						except:
							band= 0
						 # *** NOTE: test superfluous
						#~ if testValidDate(date,dates[dateIndex]):
							#~ band= dateIndex+1
						#~ else:
							#~ band= None					 
						 # ***
					else:
						band= entry2index(ncDynamicVariable,dynamicEntry)
					if isinstance(band, types.NoneType):
						message= 'Warning: specific information for dynamic entry %s for variable %s not found' %\
							(dynamicEntry, self.variableName)
						print message
					else:
						band+= 1
						self.fileProcessInfo[self.inputFileName].append((band,outputFileName))
				rootgrp.close()
			else:
				#-different type pressumed, linked per file name assuming a naive file format
				# the band therefore remains 0
				band= 0
				#-iterate over all entries
				for dynamicEntry, outputFileName in desiredDynamicEntries.iteritems():
					#-find target strings to compose stack name
					if self.datetimeFormat:
						inputFileName= composeStackName(self.inputFileName,\
							datetime2naive(self.dynamicStart,self.dynamicStart),\
								datetime2naive(self.dynamicStart,dynamicEntry))
					else:
						inputFileName= composeStackName(self.inputFileName,self.dynamicStart,dynamicEntry)
					#-check if input file name exists
					if os.path.isfile(inputFileName):
						self.fileProcessInfo[inputFileName]= []
						self.fileProcessInfo[inputFileName].append((band,outputFileName))
					else:	
						message= 'Warning: specific information for dynamic entry %s for variable %s not found' %\
							(dynamicEntry,self.variableName)
						print message
		return valid

	def processFileInfo(self):
		'''Reads in entries from the fileProcessInfo dictionary and generates all maps accordingly'''
		for inputFileName, fileInfo in self.fileProcessInfo.iteritems():
			#-check for resampleRatio and whether it is allowed
			fitsExtent, sameResolution, self.xResampleRatio, self.yResampleRatio= \
				compareSpatialAttributes(self.mapAttributes, self.targetSpatialAttributes)
			if not self.resamplingAllowed and not sameResolution:
				message= 'Error: resamping of %s for %s is not allowed' % \
					(self.inputFileName,self.variableName)
				sys.exit(message)
			#-iterate over file information and extract data
			for band, outputFileName in fileInfo:
				if isinstance(band,types.NoneType):
					if self.dynamic:
						band= 1
					else:
						band= 0
					messsage= 'Warning: band not set, reverted to default value %d ' % band
					print(message)
				outputPath= os.path.split(outputFileName)[0]
				if outputPath != '' and not os.path.exists(outputPath):
					os.makedirs(outputPath)
				#-spatialDataSet called with appropriate variables
				spatialDataSet(self.variableName, inputFileName, self.variableType, self.valueScale,\
					self.targetSpatialAttributes.xLL,	self.targetSpatialAttributes.xUR,\
					self.targetSpatialAttributes.yLL,	self.targetSpatialAttributes.yUR,\
					self.targetSpatialAttributes.xResolution, self.targetSpatialAttributes.yResolution,\
					self.xResampleRatio, self.yResampleRatio, resampleMethod= self.resampleMethod,\
					outputFileName= outputFileName, band= band, warp= not(fitsExtent and sameResolution), test= False)
	# /* end of pcrObject class definition */

class pcrParameterization(object):
	'''Class to store and handle  model settings'''
	# This class is assigned a name and a dictionary with model settings
	# that contains (key, entries) pairs where the name corresponds to the
	# variable name and entries holds a string. Entries are checked against the 
	def __init__(self,name, parameterInput, parameterTypes,\
		parameterDefaultValues,**optionalArguments):
		'''Initialization: requires the name and corresponding parameter settings,\
 -returned as section name and dictionary from the modelConfiguration class-\
 and a similar dictionary specifying the parameter variable type and default values for 
 checking data presence and consistency and subsequent processing. Optional data types include\
 rootDirectory, the path to the root directory where data may be found or written.
 If not specified, the current directory is used'''
		#-assign name and parameterSettings and parameterTypes
		self.name= name
		self.parameterInput= parameterInput
		self.parameterTypes= parameterTypes
		#-get type definition
		if 'typeDefinition' in optionalArguments.keys():
			self.typeDefinition= optionalArguments['typeDefinition']
		#-class initialized, check values
		for parameterName, typeInformation in self.parameterTypes.iteritems():
			if parameterName in self.parameterInput.keys() and \
					self.parameterInput[parameterName].strip().capitalize() != 'None':
				self.parameterInput[parameterName]= self.parameterInput[parameterName].strip()
			elif parameterName in parameterDefaultValues:
				self.parameterInput[parameterName]= str(parameterDefaultValues[parameterName]).strip()
			else:
				sys.exit('Error: the required input for %s in section %s is not defined' %\
					(parameterName,self.name))

	def getValue(self, parameterName, **mapCreationArguments):
		'''Returns the value of a particular named parameter name.'''
		#-in case the value belongs to a standard type, return the value
		# with the optional conversion of sequence types;
		# in case it is a special type, it is processed accordingly and dynamicArguments passed
		#-set typeInformation, entryStr and initialize sequenceType
		typeInformation= self.parameterTypes[parameterName]
		entryStr= self.parameterInput[parameterName]
		#-process types, get sequence type, if any
		sequenceType= None
		if isinstance(typeInformation,tuple):
			sequenceType= typeInformation[0]
			typeInformation= typeInformation[1]
		#-standard type: return values
		if isinstance(typeInformation, types.TypeType):
			#-convert sequence types
			if sequenceType == types.ListType:
				entryStr= convert2List(entryStr,separators= [';',','])
			#-convert strings to values
			if not isinstance(sequenceType,types.NoneType):
				return convertSequence2Values(entryStr,convertStandardType,typeInformation)
			else:
				return convertStandardType(entryStr,typeInformation)
		#-non-standard type, as stored by optional type definition:
		# processing occurs along the line of the types defined
		else:
			#-convert sequence types
			if sequenceType == types.ListType:
				entryStr= convert2List(entryStr,separators= [';',','])
			#-convert strings to values
			if not isinstance(sequenceType,types.NoneType):
				sys.exit('Error: sequential type not implemented yet but invoked for %s' % parameterName)
			else:
				if not 'dummyName' in mapCreationArguments.keys():
					mapCreationArguments['dummyName']= parameterName
				return self.convertSpecialType(entryStr,typeInformation, **mapCreationArguments)

	def convertSpecialType(self,entryStr, typeInformation, verbose= False, **mapCreationArguments): 
		'''Converts the string passed to a type specified within the special types class; files are automatically\
 replenished with the path name using the optional arguments inputRootDirectory, and outputRootDirectory for
 input and output respectively; input automatically includes the localInputDirectory variable once specified.
 It allows for the dynamic creation of static and dynamic model variables by passing date information.\
 In case the year is specified any paths are automatically replenished with it.'''
		#-variables passed as dynamic arguments: year for substitution
		# in path names, dynamic start, dynamic end and dynamicIncrement
		dynamicProperties= ['cloneMapAttributes','currentWorkDirectory','inputRootDirectory','inputDirectory',\
			'outputRootDirectory','temporaryDirectory',\
			'year','dynamicStart','dynamicEnd','dynamicIncrement','ncDynamicDimension',\
			'dummyName','testCreation','forceCreation']
		for dynamicProperty in dynamicProperties:
			setattr(self,dynamicProperty,None)
		#-set optional arguments forcing file creation to False
		#-test creation is always set to false but is invoked in the case argument substitution in the input path name is 
		# detected and files may have to be updated, thus mimicking the time input sparse option
		self.forceCreation= False
		self.testCreation= False
		#-set optial map creation arguments as passed to this function
		for key, value in mapCreationArguments.iteritems():
			setattr(self,key, value)
		#-force creation is always True if the variable is dynamic else it depends on the argument passed
		self.forceCreation= self.forceCreation or typeInformation.dynamic
		#-set variableName
		variableName= 'dummy'
		if 'dummyName' in mapCreationArguments.keys():
			variableName= self.dummyName
			if len(variableName) == 0:
				variableName= os.path.split(entryStr)[1]
		#-test on variable entries, not used in script
		if verbose:
			for key, value in vars(self).iteritems():
				print key, value		
		#-check on data type and set default output to NoneType
		typeMatched= False
		#-iterate over special types
		for typeDefinition in vars(self.typeDefinition).keys():
			if typeInformation == getattr(self.typeDefinition,typeDefinition):
				typeMatched= True
				typeDefinitionMatched= typeDefinition
		#-entry found, and process
		if typeMatched:
			#-date time
			if typeInformation.allowableTypes[0] == datetime.date: 
				try:
					entryStr= datetime.date.fromordinal(float(entryStr))
				except:
					try:
						year, month, day= entryStr.split('-')[:3]
						entryStr= datetime.date(int(year),int(month),int(day))
					except:
						sys.exit('variable %s cannot be converted to %s; type not encountered' % (entryStr, typeDefinitionMatched))
			#-path type
			elif typeInformation.fileType == 'Path':
				#-allowable type can contain NoneType, check on this first, else return string
				if entryStr.capitalize() == 'None':
					entryStr= None
			#-file type linked to PCRaster map
			elif typeInformation.fileType == 'File' and typeInformation.dataType.name in pcr.Scalar.names.keys():
				#-check on multiple type entries and try to convert values
				value= None
				outputFileName= None
				if types.BooleanType in typeInformation.allowableTypes:
					try:
						value= int(bool(entryStr))
					except:
						pass
				if types.IntType in typeInformation.allowableTypes:
					try:
						value= int(float(entryStr))
					except:
						pass
				if types.FloatType in typeInformation.allowableTypes:
					try:
						value= float(entryStr)
					except:
						pass
				#-value returned, check on file name: in the case no value is returned,
				# an actual file is specified and the input file name is set accordingly
				#-start with any optional path components
				pathSubstArgs= []
				if not isinstance(self.year,types.NoneType):
					pathSubstArgs= [self.year]
				#-an actual file is specified if value is a NoneType;
				# update dummy name to file name and test any substitution in input paths
				if isinstance(value,types.NoneType):
					#-get actual file name from path specified
					fileDirectory, fileName= os.path.split(entryStr)
					if self.dummyName == '':
						self.dummyName= fileName
					#-check whether netCDF files are allowed
					if os.path.splitext(fileName)[1] == '.nc' and not typeInformation.ncAllowed:
						sys.exit('netCDF format not allowed for variable %s of type %s' % (entryStr, typeDefinition))
					#-subsitute any arguments in the input paths and test on possbile file creation thus mimicking the timeinputsparse option
					self.inputRootDirectory, t= optionalPathSubstitution(self.inputRootDirectory,pathSubstArgs)
					self.testCreation= self.testCreation or t
					self.inputDirectory, t= optionalPathSubstitution(self.inputDirectory,pathSubstArgs)
					self.testCreation= self.testCreation or t
					fileDirectory, t= optionalPathSubstitution(fileDirectory,pathSubstArgs)
					self.testCreation= self.testCreation or t
					#-obtain input file name
					inputFileName= composeFileName(self.currentWorkDirectory,self.inputRootDirectory,self.inputDirectory,\
						fileDirectory,fileName)
					#-output file name
					outputFileName= composeFileName(self.currentWorkDirectory,self.outputRootDirectory,self.temporaryDirectory,self.dummyName)
					#-use pcrObject to convert files: check whether the input map exists and creation is optional;
					# if it does not exist and forceCreation is set to true or cloneMapAttributes cannot be created,
					# exit with an error message; otherwise, create the file
					processFile= os.path.isfile(inputFileName) or self.testCreation
					if typeInformation.dynamic and not processFile:
						try:
							composeStackName(inputFileName,self.dynamicStart,self.dynamicEnd)
							processFile= True
						except:
							pass
					#-act on process file
					if not processFile:
						sys.exit('Error: input file name %s cannot be found, run halted' % inputFileName)
					if processFile:
						#-if test creation is true and input file exists, set force creation to true
						if self.testCreation and not typeInformation.dynamic:
							self.forceCreation= True
						#-create and copy file if required
						if self.forceCreation == True:
							#-check whether the output directory exists, else it is created
							try:
								os.makedirs(os.path.split(outputFileName)[0])
							except:
								pass
							#-set clone map attributes if not set
							if isinstance(self.cloneMapAttributes,types.NoneType):
								if typeInformation.resamplingAllowed:
									print 'Warning: no clone map attributes specified for rescalable %s' % inputFileName
								self.cloneMapAttributes= spatialAttributes(inputFileName)
							#-intialize spatial data set and copy
							pcrField= pcrObject(variableName, outputFileName, inputFileName, self.cloneMapAttributes,\
								pcrVALUESCALE= typeInformation.dataType, dynamic= typeInformation.dynamic,\
								dynamicStart= self.dynamicStart, dynamicEnd= self.dynamicEnd, dynamicIncrement= self.dynamicIncrement,\
								ncDynamicDimension= self.ncDynamicDimension, resamplingAllowed= typeInformation.resamplingAllowed)
							#-convert maps
							pcrField.initializeFileInfo()
							pcrField.processFileInfo()
							del pcrField
					else:
						print 'Warning: input file name %s cannot be found and is not updated' % inputFileName
					#-set entryStr to outputFileName
					entryStr= outputFileName						
				#-value is not of NoneType, actual value returned and a dummy output fileName has to be generated and the value reported
				else:
					#-compose the output file name, note that this is assigned to entryStr early on in order to ensure
					# that the root is passed on early in case of dynamic variables
					self.outputRootDirectory, t= optionalPathSubstitution(self.outputRootDirectory,pathSubstArgs)
					self.temporaryDirectory, t= optionalPathSubstitution(self.temporaryDirectory,pathSubstArgs)
					outputFileName= composeFileName(self.currentWorkDirectory,self.outputRootDirectory,self.temporaryDirectory,self.dummyName)
					entryStr= outputFileName
					try:
						os.makedirs(os.path.split(outputFileName)[0])
					except:
						pass
					if typeInformation.dynamic:
						outputFileName= composeStackName(outputFileName,1,1)
					if self.forceCreation:
						try:
							if typeInformation.dataType == pcr.Directional:
								pcrField= pcr.directional(value)
							elif typeInformation.dataType == pcr.Scalar:
								pcrField= pcr.scalar(value)
							elif typeInformation.dataType == pcr.Ordinal:
								pcrField= pcr.ordinal(value)
							elif typeInformation.dataType == pcr.Nominal:
								pcrField= pcr.nominal(value)
							elif typeInformation.dataType == pcr.Ldd:
								pcrField= pcr.ldd(value)
							elif typeInformation.dataType == pcr.Boolean:
								pcrField= pcr.boolean(value)
							pcr.report(pcrField,outputFileName)
							del pcrField
						except:
							sys.exit('Error: value %s for %s cannot be converted to %s' %\
								(value, variableName, typeInformation.dataType))
		#-delete any map creation attributes set
		#-set dynamic properties back to none and delete
		for dynamicProperty in dynamicProperties:
			setattr(self,dynamicProperty,None)
			delattr (self,dynamicProperty)
		#-check if type definition has been encountered, else halt with error
		if not typeMatched:
			#-entryStr set to NoneType
			entryStr= None
			#-raise error
			sys.exit('variable %s cannot be converted to %s; type not encountered' % (entryStr, typeInformation))
		#-entryStr returned
		return entryStr
	# /* end of pcrParameterization object */
	
class pcrParameterDefinition(object):
	'''Dummy class to set parameter types and default values'''
	
	def __init__(self):
		#-initialization
		pass

	def setParameterTypes(self,name,parameterInformation):
		#-creates the variable with the name specified and 
		# sets the dictionary with information passed
		setattr(self,name,parameterInformation)
		
	def setParameterEntries(self, **entries):
		#-creates entries from dictionary
		for key, entry in entries.iteritems():
			setattr(self,key,entry)
		
class pcrTypeDefinition(object):
	'''Class containing information on special data types'''
	#includes any specialTypes needed to manage the model
	
	def __init__(self, fileType= None, ncAllowed= False,\
		dataType= None, dynamic= False, resamplingAllowed= False,\
			allowableTypes= []):
		#-initialization
		self.fileType= fileType
		self.ncAllowed= ncAllowed
		self.dynamic= dynamic
		self.resamplingAllowed= resamplingAllowed		
		self.dataType= dataType
		self.allowableTypes= allowableTypes

def main():
	#-import time to test duration of conversion 
	import time
	#-test conversion
	entryStr= '0'
	for typeInformation in [types.BooleanType, types.FloatType,\
		types.IntType, types.LongType, types.NoneType, types.StringType, 'pipo koeie']:
		try:
			print convertStandardType(entryStr, typeInformation)
		except:
			pass
	#-test file name creation
	composeFileName('/home/rens/test/input/maps/','input/maps',None,'input/maps/test.map')

	outputFileName= '/scratch/rens/temp/results/s1_sv'
	print composeStackName(outputFileName,1,1)

	outputFileName= '/scratch/rens/temp/results/s2_sv'
	print composeStackName(outputFileName,1,1)

	outputFileName= '/home/beek0120/netData/LatinAmerica/Parameterization/LatinAmerica_Hydro1k_dzrel_%04d_05min.map'
	print composeStackName(outputFileName,1,100)


	#-test on a dynamic map for clipping and rescaling - netCDF format
	currentTime= time.time()
	inputFileName= '/home/rens/netData/LatinAmerica/testMasks/mask_M33.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/rens/netData/LatinAmerica/Parameterization/meteo/cruts321_era40_daily_temperature_1996_to_2001_05min.nc'
	variableName= 'airTemperature'
	outputFileName= 'test/%s' % variableName[:7].lower()
	startDate= datetime.datetime(2000,01,01)
	endDate= datetime.datetime(2000	,12,31)
	timeIncrement= 'days'
	dynamicMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, dynamic= True,\
		dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= timeIncrement, ncDynamicDimension=	'time',\
		resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(dynamicMap.mapAttributes)[key]	
	dynamicMap.initializeFileInfo()
	dynamicMap.processFileInfo()
	keys= dynamicMap.fileProcessInfo.keys()
	keys.sort()
	key= keys[0]
	outputFileName= dynamicMap.fileProcessInfo[key][0][1]
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)

	sys.exit()

	#-test on a dynamic map for clipping and rescaling - netCDF format
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/mask_M25map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/PCR-GLOBWB/PCR-GLOBWB_V1.0/states/soilwatercontent_bottomlayer_shortvegetation.nc'
	variableName= 'soilWaterContent_BottomLayer'
	outputFileName= 's2_sv'
	startDate= datetime.datetime(1999,12,31)
	endDate= datetime.datetime(1999,12,31)
	timeIncrement= 'days'
	dynamicMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, dynamic= True,\
		dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= timeIncrement, ncDynamicDimension=	'Time',\
		resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(dynamicMap.mapAttributes)[key]	
	dynamicMap.initializeFileInfo()
	dynamicMap.processFileInfo()
	keys= dynamicMap.fileProcessInfo.keys()
	keys.sort()
	key= keys[0]
	outputFileName= dynamicMap.fileProcessInfo[key][0][1]
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)


	sys.exit()


	#-test file name replacements
	testFileNames= ['test/airtemp', 'test/waterstorage-2000-01-01.map', 'test/waterstorage-%04d-%02d-%02d.map',\
		'test/LatinAmerica_Hydro1k_dzrel_0001_05min.map','test/LatinAmerica_Hydro1k_dzrel_%04d_05min.map',\
		'test/airtemp0.001', 'test/airtemp0.%03d','maps/Global_Hydro1k_RelativeElevation_30min.%03d']
	#-test on dates
	startDate= datetime.datetime(2000,01,01)
	testDate=  datetime.datetime(2000,12,31)
	for testFileName in testFileNames:
		try:
			print '\ntesting map stack style file substitution on %s with %s' % (testFileName, testDate)
			print composeStackName(testFileName,startDate,testDate)
		except:
			pass
		try:
			print '\ntesting map stack style file substitution on %s with %s' % (testFileName, 2)
			print composeStackName(testFileName,1,2)
		except:
			pass


	sys.exit()
			
	#-test on a dynamic map for clipping and rescaling - PCRaster format
	currentTime= time.time()
	inputFileName= '/home/beek0120/PCR-GLOBWB/PCR-GLOBWB_V1.0/input30min/maps/Global_Clone_30min.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/PCR-GLOBWB/PCR-GLOBWB_V1.0/input30min/maps/Global_Hydro1k_RelativeElevation_30min.%03d' % 1
	#~ inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/LatinAmerica_Hydro1k_dzrel_0001_05min.map'
	variableName= 'relativeElevation'
	outputFileName= 'test/test_%s' % variableName
	outputFileName+= '.%03d'
	dynamicMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes,\
		dynamic= True, dynamicStart= 1, dynamicEnd= 100, dynamicIncrement= 1, resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(dynamicMap.mapAttributes)[key]	
	dynamicMap.initializeFileInfo()
	dynamicMap.processFileInfo()
	keys= dynamicMap.fileProcessInfo.keys()
	keys.sort()
	key= keys[0]
	outputFileName= dynamicMap.fileProcessInfo[key][0][1]
	print '\n%s' % outputFileName
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)


	sys.exit()


	#-test on a dynamic map for clipping and rescaling - netCDF format
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/mask_M33.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/PCR-GLOBWB/PCR-GLOBWB_V1.0/input30min/meteo/ncep_ncar_1996_2000_prate.nc'
	variableName= 'prate'
	outputFileName= 'test/%s' % variableName[:7].lower()
	startDate= datetime.datetime(2010,01,01)
	endDate= datetime.datetime(2010,12,31)
	timeIncrement= 'days'
	dynamicMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, dynamic= True,\
		dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= timeIncrement, ncDynamicDimension=	'time',\
		resamplingAllowed= True)
	dynamicMap.initializeFileInfo()
	dynamicMap.processFileInfo()

			
	sys.exit()
 
	#-test functions for a particular mask:
	print '*** Test of PCR parameterization ***'
	#-test on a static map without rescaling
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/clone_latinamerica_5min.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/LatinAmerica_GLCC_TallVegetation_vegetationFraction_05min.map'
	variableName= 'veg_fraction'
	outputFileName= 'test/test_%s_LatinAmerica.map' % variableName
	staticMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(staticMap.mapAttributes)[key]	
	staticMap.initializeFileInfo()
	staticMap.processFileInfo()
	print '\n%s' % outputFileName
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)

	#-test on a static map with clipping
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/mask_M33.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/LatinAmerica_GLCC_TallVegetation_vegetationFraction_05min.map'
	variableName= 'veg_fraction'
	outputFileName= 'test/test_%s_mask33.map' % variableName
	staticMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(staticMap.mapAttributes)[key]	
	staticMap.initializeFileInfo()
	staticMap.processFileInfo()
	print '\n%s' % outputFileName
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)

	#-test on a static map with rescaling
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/clone_global_30min.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/LatinAmerica_GLCC_TallVegetation_vegetationFraction_05min.map'
	variableName= 'veg_fraction'
	outputFileName= 'test/test_%s_global.map' % variableName
	staticMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(staticMap.mapAttributes)[key]	
	staticMap.initializeFileInfo()
	staticMap.processFileInfo()
	print '\n%s' % outputFileName
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)

	#-test on a static map with clipping-nominal
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/mask_M33.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/LatinAmerica_GRAND_WaterBodiesID_05min.map'
	variableName= 'waterBodyID'
	outputFileName= 'test/test_%s_M33.map' % variableName
	staticMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes,\
		pcrVALUESCALE= pcr.Nominal, resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(staticMap.mapAttributes)[key]	
	staticMap.initializeFileInfo()
	staticMap.processFileInfo()
	print '\n%s' % outputFileName
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)

	#-test on a dynamic map for clipping and rescaling - PCRaster format
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/mask_M33.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/LatinAmerica_Hydro1k_dzrel_0001_05min.map'
	variableName= 'relativeElevation'
	outputFileName= 'test/test_%s_M33' % variableName
	outputFileName+= '.%03d'
	dynamicMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes,\
		dynamic= True, dynamicStart= 1, dynamicEnd= 100, dynamicIncrement= 1, resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(dynamicMap.mapAttributes)[key]	
	dynamicMap.initializeFileInfo()
	dynamicMap.processFileInfo()
	keys= dynamicMap.fileProcessInfo.keys()
	keys.sort()
	key= keys[0]
	outputFileName= dynamicMap.fileProcessInfo[key][0][1]
	print '\n%s' % outputFileName
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)

	#-test on a dynamic map for clipping and rescaling - netCDF format
	currentTime= time.time()
	inputFileName= '/home/beek0120/netData/LatinAmerica/testMasks/mask_M33.map'
	cloneMapAttributes= spatialAttributes(inputFileName)
	inputFileName= '../combinedforcing/crucorrected_era-combined_temperature.nc'
	variableName= 'airTemperature'
	outputFileName= 'test/%s' % variableName[:7].lower()
	startDate= datetime.datetime(2010,01,01)
	endDate= datetime.datetime(2010,12,31)
	timeIncrement= 'days'
	dynamicMap= pcrObject(variableName, outputFileName, inputFileName, cloneMapAttributes, dynamic= True,\
		dynamicStart= startDate, dynamicEnd= endDate, dynamicIncrement= timeIncrement, ncDynamicDimension=	'time',\
		resamplingAllowed= True)
	print 'Comparison between clone and source map'
	for key in vars(cloneMapAttributes).keys():
		print key, vars(cloneMapAttributes)[key], vars(dynamicMap.mapAttributes)[key]	
	dynamicMap.initializeFileInfo()
	dynamicMap.processFileInfo()
	keys= dynamicMap.fileProcessInfo.keys()
	keys.sort()
	key= keys[0]
	outputFileName= dynamicMap.fileProcessInfo[key][0][1]
	os.system('gdalinfo %s' % outputFileName)
	print 'processing required %.1f sec\n' % (time.time()-currentTime)
	
	#-tests done
	print '*** Tests done ***'

if __name__ == '__main__':
	main()

