#-Collection of functions to process netCDF files
# including file creation, read and write
# and collation as well as PCRaster interoperability

#-modules
import os, sys, calendar, datetime, zlib
from types import NoneType, DictType, UnicodeType, BuiltinMethodType
import numpy as np
import netCDF4 as nc
import pcraster as pcr

#-functions to copy and create a netCDF file and add dimensions and data to it
# TODO: allow dimensions, variables and fields to be added to a netCDF dataset open for append
# rather than opening and closing files repeatedly
# TODO: add groups to getNCAttributes and dimension and variable creation

#-global variables: default netCDF type and variable attributes set
# createVariable functions called with all variables specified set to the following default values
# testVerbose flags output
defaultNCFormat= 'NETCDF3_CLASSIC'
default_zlib= False; default_complevel= 4; default_shuffle= True;
default_fletcher32= False; default_contiguous= False; default_chunksizes= None;
default_endian= 'native'; default_least_significant_digit= None; default_fill_value= None; 
testVerbose= True

def printDictionary(dObj,level= 0):
	'''iterates over all items in a dictionary and print key,value pairs'''
	for key, value in dObj.iteritems():
		if isinstance(value,list) or isinstance(value,np.ndarray):
			vals= value[:]
			value= [vals[0],'...',vals[-1]]
		print ' '*level*5,key,
		try:
			print value
		except:
			print

def getNCObjectAttributes(obj):
	'''Reads all information from the netCDF dataset object specified and returns a dictionary\
 of key, value pairs; should only be applied on copies of netCDF dataset objects\
 to avoid unwanted changes in the dataset'''
	#-create dictionary and iterate over output
	dObj= {}
	for item in dir(obj):
		#-check on allowable entries
		if not 'set' in item and not item[:2] == '__':
			if isinstance(getattr(obj,item),BuiltinMethodType):
				try:
					dObj[item]= getattr(obj,item)()
				except:
					pass
			else:
				dObj[item]= getattr(obj,item)
	return dObj

def getNCAttributes(ncFile):
	'''Reads netCDF file specified and returns dictionaries of\
 its format, attributes, dimensions, dimension values for reuse and the attributes of its variables.\
 Output variables include:
 - ncFormat:			netCDF file format
 - attributes:		netCDF dataset attributes
 - dimattrs:			a copy of the attributes of the netCDF dataset ordered dictionary of dimensions;
									includes information on whether it is unlimited and a copy of all values for each dimension
									from the netCDF dataset ordered dictionary of variables;
									stored as a dictionary with the dimension name as key
 - varattrs:			a copy of the attributes of each variable in the netCDF dataset ordered dictionary of
									variables; stored as a nested dictionary with the variable name as key and all attributes stored
									stored subsequently as a single key, value pair; this includes a copy of the numpy datatype and
									dimensions of each variable
 Keys specified in varattrs but not in dimvalues identify possible variables holding information'''
	# TODO: include groups
	# NOTE: information is passed partly as copies as netCDF dataset variables and dimensions cannot be accessed\
	# when file is closed
	#-local variables: specific keys for dimensions and variables to be added to their attributes and the function to extract them
	#-open netCDF file for read
	rootgrp= nc.Dataset(ncFile,'r',)
	#-retrieve file format, dimensions, atributes, variables, and missing value
	ncFormat= rootgrp.file_format
	dimensions = rootgrp.dimensions.copy()
	variables	= rootgrp.variables.copy()
	attributes = rootgrp.__dict__.copy()
	#-get the attributes of the dimensions as dictionary and the values of the dimensions as dictionary for reuse
	dimattrs= {}
	for key in dimensions.iterkeys():
		dimattrs[key]= getNCObjectAttributes(dimensions[key])
		if variables.has_key(key):
			dimattrs[key]['values']= variables[key][:]
			dimattrs[key]['size']= variables[key].size
	#-get all attributes for each variable for reuse
	varattrs= {}
	for key in variables.iterkeys():
		varattrs[key]= getNCObjectAttributes(variables[key])
	#-close file
	rootgrp.close()
	#-return output
	return ncFormat,attributes, dimattrs, varattrs

def selectNCVariableAttributes(ncVariable,verbose= testVerbose):
	'''Selects from the dictionary with information from a variable the\
 information that is required to initialize the variable.
 Output variables include:
 - name:					the name of the variable by which it is stored
 - datatype:			the data type, numpy datatype object or its dtype.str attribute\
									or any of the supported specifiers included: 'S1' or 'c' (NC_CHAR),\
									'i1' or 'b' or 'B' (NC_BYTE), 'u1' (NC_UBYTE), 'i2' or\
									'h' or 's' (NC_SHORT), 'u2' (NC_USHORT), 'i4' or 'i' or\
									'l' (NC_INT), 'u4' (NC_UINT), 'i8' (NC_INT64), 'u8' (NC_UINT64),\
									'f4' or 'f' (NC_FLOAT), 'f8' or 'd' (NC_DOUBLE).
 - dimensions:		the tuple with dimensions
 - attributes:		a dictionary copy of the ncattrs specified; ncattrs is included to\
									handle specific variable attribution in addVariableNCFile calls'''
	#-retrieves from the dictionary specified with variable info the name, datatype, dimensions and attributes
	#-initialize the output
	name= None
	datatype= None
	dimensions= ()
	attributes= {}
	#-check on entries
	if 'name' in ncVariable.keys():
		name= ncVariable['name']
	elif '_name' in ncVariable.keys():
		name= ncVariable['_name']
	if 'dtype' in ncVariable.keys():
		datatype= ncVariable['dtype']
	if 'dimensions' in ncVariable.keys():
		dimensions= ncVariable['dimensions']
	if 'ncattrs' in ncVariable.keys():
		for key in ncVariable['ncattrs']:
			if key in ncVariable.keys():
				if isinstance(key,UnicodeType): key= str(key)
				value= ncVariable[key]
				attributes[key]= value
		attributes['ncattrs']= ncVariable['ncattrs']
	#-return entries if valid name and datatype have been encountered, else exit with message
	if isinstance(name,NoneType) or isinstance(datatype,NoneType):
		sys.exit('no name or data type is specified in the dictionary with variable attributes')
	else:
		if verbose:
			print 'variable %s of type %s with dimensions %s holds the following attributes:'%\
				(name,datatype,dimensions)
			printDictionary(attributes,level= 1)
		return name,datatype,dimensions,attributes

def getNCDates(timeDimension,timeVariable,verbose= testVerbose):
	'''Returns the dates based on the information from the netCDF file\
 as specified by dictionaries hoding information on its time dimension\
 and corresponding variable; the variable should contain both units in 
 a format of "time units since reference time" and the calendar specified (e.g., "standard"),\
 if verbose is true, additional info is printed to screen'''
	dates= nc.num2date(timeDimension['values'],timeVariable['units'],\
		timeVariable['calendar'])
	if verbose:
		print 'Time expressed as %s for the %s calendar' %\
			(timeVariable['units'],timeVariable['calendar'])
		print 'Series contains %d timestamps between %s and %s inclusive' %\
			(dates.size,dates[0],dates[-1])
	return dates

def initializeNCFile(ncFile,ncFormat,ncAttributes= {}, verbose= testVerbose):
	'''Initializes the netCDF file with the name and format specified\
 and set its attributes'''
	rootgrp= nc.Dataset(ncFile,'w',format= ncFormat)
	#-set netCDF attributes
	for attribute,value in ncAttributes.iteritems():
		rootgrp.setncattr(attribute,value)
	if verbose:
		print 'New netCDF file %s created with the following attributes' % ncFile
		printDictionary(rootgrp.__dict__.copy(),level= 1)
	#-update and close
	rootgrp.sync()
	rootgrp.close()

def addVariableNCFile(ncFile,name,datatype,dimensions,verbose= testVerbose,**ncOptionalInfo):	
	'''Adds a variable to the netCDF file using netCDF4 createVariable function.\
 Input variables include the following required arguments:
 - ncFile:				the file name of the netCDF dataset in which the variable will be created
 - name:					the name of the variable by which it is stored
 - datatype:			the data type, numpy datatype object or its dtype.str attribute\
									or any of the supported specifiers included: 'S1' or 'c' (NC_CHAR),\
									'i1' or 'b' or 'B' (NC_BYTE), 'u1' (NC_UBYTE), 'i2' or\
									'h' or 's' (NC_SHORT), 'u2' (NC_USHORT), 'i4' or 'i' or\
									'l' (NC_INT), 'u4' (NC_UINT), 'i8' (NC_INT64), 'u8' (NC_UINT64),\
									'f4' or 'f' (NC_FLOAT), 'f8' or 'd' (NC_DOUBLE).
 - dimensions:		the tuple with dimensions
 Input variables include the following optional keyword arguments: 
 - Any or all of the following: zlib, complevel, shuffle,\
									fletcher32, contiguous, chunksizes, endian,\
									least_significant_digit, fill_value;
 - ncvarattrs:		a dictionary holding all netCDF variable attributes;\
									if this dictionary holds any of the above parameters but it is\
									specified explicitly, the latter is given precedence. Otherwise it is\
									set implicitly.'''
	#-local variables - process optional keywords and set defaults first
	ncvarattrs= {}
	ncVariableParameters= {}
	ncVariableParameters['varname']= name 
	ncVariableParameters['datatype']= datatype
	ncVariableParameters['dimensions']= dimensions
	ncVariableParameters['zlib']= default_zlib
	ncVariableParameters['complevel']= default_complevel
	ncVariableParameters['shuffle']= default_shuffle
	ncVariableParameters['fletcher32']= default_fletcher32
	ncVariableParameters['contiguous']= default_contiguous
	ncVariableParameters['chunksizes']= default_chunksizes
	ncVariableParameters['endian']= default_endian
	ncVariableParameters['least_significant_digit']= default_least_significant_digit
	ncVariableParameters['fill_value']= default_fill_value
	#-set any dictionary to attributes; test whether it is a wrapped keyword argument (e.g.,
	# when passed from addDimensionNCFile); in that case the arguments will contain a second dictionary
	for ncKeyWord, value in ncOptionalInfo.iteritems():
		if isinstance(value,DictType):
			ncvarattrs= value.copy()
	#-try and strip any key words
	for ncKeyWord in ncvarattrs.keys():
		if ncKeyWord in ncVariableParameters.keys():
			ncVariableParameters[ncKeyWord]= ncvarattrs[ncKeyWord]
			del ncvarattrs[ncKeyWord]
	#-try and open file to append variable
	try:
		assert(os.path.isfile(ncFile))
		rootgrp= nc.Dataset(ncFile,'a')
	except:
		sys.exit('netCDF file %s does not exist or could not be opened' % ncFile)	
	#-create variable in netCDF dataset
	ncVariable= rootgrp.createVariable(**ncVariableParameters)
	if 'ncattrs' in ncvarattrs.keys():
		keys= ncvarattrs['ncattrs']
	elif len(ncvarattrs.keys()) > 0:
		if testVerbose:	print 'Note: no variable attributes defined by ncattrs'
		keys= ncvarattrs.keys()
	#-try and assign keys; keys present in the list of ncattrs but not in the
	# ncVariableParameters dictionary are ignored
	for key in keys:
		try:
			ncVariable.setncattr(key,ncvarattrs[key])
		except:
			pass
	if verbose:
			print 'variable %s of type %s with dimensions %s set with the following attributes:'%\
				(name,datatype,dimensions)		
			for key in ncVariable.ncattrs():
				print ' ' * 5, key	
	#-synchronize and close
	rootgrp.sync()
	rootgrp.close()

def writeField(ncFile,variableArray,name,dimensionPos,\
		MV= default_fill_value,verbose= testVerbose):
	'''Writes a numpy array to the given variable in the netCDF dataset specified.\
 Input variables include:'''
	rootgrp= nc.Dataset(ncFile,'a')
	#- write data
	ncVariable= rootgrp.variables[name]
	ncVariable[:]= variableArray
	#-update file and close
	rootgrp.sync()
	rootgrp.close()
	
def addDimensionNCFile(ncFile,name,unlimited,datatype,values,verbose= testVerbose,**ncOptionalInfo):
	'''Adds a dimension to the netCDF file and creates the corresponding variable\
 by calling the addVariableNCFile command internally. It takes the following required arguments:
 - ncFile:				the file name of the netCDF dataset in which the dimension will be created
 - name:					the name of the variable by which it is stored
 - unlimited:			boolean specifying whether the dimension is unlimited or not
 - datatype:			the data type of the values, numpy datatype object or its dtype.str attribute\
									or any of the supported specifiers included: 'S1' or 'c' (NC_CHAR),\
									'i1' or 'b' or 'B' (NC_BYTE), 'u1' (NC_UBYTE), 'i2' or\
									'h' or 's' (NC_SHORT), 'u2' (NC_USHORT), 'i4' or 'i' or\
									'l' (NC_INT), 'u4' (NC_UINT), 'i8' (NC_INT64), 'u8' (NC_UINT64),\
									'f4' or 'f' (NC_FLOAT), 'f8' or 'd' (NC_DOUBLE).
 - values:				the dimension values as numpy array; if empty or not specified the dimension\
									is set to unlimited
 Input variables include the following optional keyword arguments: 
 - Any or all of the following: zlib, complevel, shuffle,\
									fletcher32, contiguous, chunksizes, endian,\
									least_significant_digit, fill_value;
 - ncvarattrs:		a dictionary holding all netCDF variable attributes;\
									if this dictionary holds any of the above parameters but it is\
									specified explicitly, the latter is given precedence. Otherwise it is\
									set implicitly.'''
	#-open file for append, if not possible, create it
	try:
		assert(os.path.isfile(ncFile))
		rootgrp= nc.Dataset(ncFile,'a')
	except:
		initializeNCFile(ncFile,defaultNCFormat)
		rootgrp= nc.Dataset(ncFile,'a')
	#-add dimension
	if unlimited:
		size= None
	else:
		if isinstance(values,np.ndarray):
			size= values.size
		else:
			try:
				size= len(values)
			except:
				size= None
				unlimited= True
	rootgrp.createDimension(name,size)
	#-synchronize and close
	rootgrp.sync()
	rootgrp.close()
	#-add variable
	#~ addVariableNCFile(ncFile,name,datatype,(name,),ncvarattrs= ncOptionalInfo['ncVariableAttributes'])
	addVariableNCFile(ncFile,name,datatype,(name,),**ncOptionalInfo)
	#-add values to variable unless it is set to unlimited
	if not unlimited:
		#~ writeField(ncFile,values,name)
		pass
	if verbose:
		print 'dimension %s created' % name
	
#~ def copyEmptyNCFile(inFile, outFile):
	#~ '''Creates outFile as an empty copy of inFile with the values for all\
 #~ dimensions initialized except those set to be unlimited'''
	#~ fileFormat,attributes, dimensions, dimensionValues, variableAttributes= getNCAttributes(inFile)
	#-initialize file
	#~ initializeNCFile(outFile,fileFormat)
	#-add dimensions
	#~ pass
	#~ for  in dimension.keys():
		#~ 
		#~ ncAddDimension
	
	
def main():
	#-tests on functions
	
	#-getNCAttributes: retrieve all info from a netCDF file
	testNCFile= '/home/beek0120/netData/hadisd.1.0.0.2011f.160330-99999.nc'
	#~ testNCFile= '/home/rens/netData/GlobalDataSets/NCC/ncc_mean_daily_2m_temp_climatology.nc'
	ncFileFormat,ncAttributes, ncDimensions, ncVariables= getNCAttributes(testNCFile)
	#-test attributes, dimensions and variables returned
	print ncFileFormat
	printDictionary(ncAttributes)
	for key in ncDimensions.keys():
		print key
		printDictionary(ncDimensions[key],level= 1)
	for key in ncVariables.keys():
		print key
		printDictionary(ncVariables[key],level= 1)
	print
	
	#-getNCDates: return an array of formatted dates
	getNCDates(ncDimensions['time'],ncVariables['time'])
	print
	
	#-addDimensionNCFile: add a dimension and its values to the netCDF file
	# create the file if it does not exist and do not set values if the dimension is unlimted
	tempNCFile= 'test.nc'
	try:
		os.remove(tempNCFile)
	except:
		pass
	initializeNCFile(tempNCFile,ncFileFormat,ncAttributes)
	#-selectNCVariableAttributes: return a selection of the attributes listed for a variable
	# here, iterate over all variables by dimensions first 
	variableNames= ncDimensions.keys()
	for key in ncVariables.keys():
		if key not in ncDimensions.keys():
			variableNames.append(key)
	#-add dimensons and variables
	for key in variableNames:
		if key in ncVariables.keys():
			if key in ncDimensions.keys():
				print 'dimension & variable %s' % key
			else:
				print 'variable %s' % key
		elif key in ncDimensions.keys():
			print 'dimension %s' % key
			
			#~ 
			#~ #-add dimension
			#~ if key != 'time':
				#~ addDimensionNCFile(tempNCFile,key,ncDimensions[key]['isunlimited'],\
					#~ variableDataType,ncDimensions[key]['values'],ncVariableAttributes= ncVariables[key])
			#~ else:
				#~ addDimensionNCFile(tempNCFile,key,ncDimensions[key]['isunlimited'],\
					#~ variableDataType,ncDimensions[key]['values'],ncVariableAttributes= ncVariables[key],fill_value= -999.0)
		#~ else:
			#~ #-add variable
			#~ variableName, variableDataType, variableDimensions, variableAttributes=\
				#~ selectNCVariableAttributes(ncVariables[key])
#~ 
			#~ addVariableNCFile(tempNCFile,key,variableDataType,variableDimensions,\
				#~ ncVariableAttributes= ncVariables[key])

	#~ #-test on variables
	#~ print
	#~ rootgrp= nc.Dataset(testNCFile,'r')
	#~ print rootgrp.dimensions.copy()
	#~ print rootgrp.variables.copy()
	#~ print
	#~ variables= rootgrp.variables.copy()
	#~ for key in variables.keys():
		#~ ncVariableAttributes= getNCObjectAttributes(variables[key])
		#~ print key,
		#~ printDictionary(ncVariableAttributes,level= 1)
		#~ pietje
	#~ rootgrp.close()
	
	
	#-copyEmptyNCFile: create an empty copy of an existing netCDF file
	# with the values for all dimensions initialized except those set to be unlimited
	#~ copyEmptyNCFile(testNCFile,'test.nc')	
	
	
		
if __name__ == '__main__':
	#-call main
	main()

