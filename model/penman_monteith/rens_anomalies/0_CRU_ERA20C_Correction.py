#!/usr/bin/python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# EHS (23 June 2014): This is script for generating CRU-ERA Interim forcing time series 
#                     The method is inspired by Rens van Beek.
# RvB (01 October 2015): modified to process ERA20C

import os
import sys
import calendar
import datetime
import zipfile 
import zlib
import numpy as np
import logging

import pcraster as pcr
from pcraster.framework import generateNameT

# utility modules:
import virtualOS as vos
import computeAnomalies as rvb_ano
import ncRecipes as rvb_ncR
import potentialET_Hamon as hamonET
import outputNetcdf
import pcrGlobalGeometry as globGeo

from logger import Logger
# get name for the logger
logger = logging.getLogger("main_script")

# output folder
outputFolder = "/storagetemp/rens/ERA20C"
try:
    os.makedirs(outputFolder)
except:
    cleanOutpurDir = False
    if cleanOutpurDir: os.system("rm -r "+str(outputFolder)+"/*")
    pass
#
# 'front' file name for the output files:
front_filename = "cruts321_era20c"

# clone map file name (global with 0.50 degree cell size)
cloneMapFileName = "/data/hydroworld/others/Global/Global_CloneMap_30min.map"

# start year, end year: full ERA-Interim years (default)
startYear = 1901 # 2000 # 1979
endYear   = 1901 # 2000 # 2010
#
# try to read startYear and endYear from command line argurments (sys.argv) 
try:
    startYear = int(sys.argv[1]) 
    endYear   = int(sys.argv[2])
except:
    pass

# cru input
input_cru = {}
input_cru['folder'] = "/data/hydroworld/basedata/forcing/CRU-TS3.21"

# era interim input files for rainfall and temperature
# RvB: changed to netCDF input 
#~ input_ecmwf = {}
#~ input_ecmwf['files'] = {}
#~ input_ecmwf['files']['rainfall']           = "/projects/dfguu/data/hydroworld/basedata/forcing/ERA-Interim-GPCPCorrected/pcraster_maps/Precipitation/"  # daily resolution
#~ input_ecmwf['files']['rainfall']          +=  "Global_Precipitation_ERA-Interim-GPCPCorrected_%04d-%02d-%02d_30min.map"
#~ input_ecmwf['files']['temperature']        = "/projects/dfguu/data/hydroworld/basedata/forcing/ERA-Interim-ECMWF/pcraster_maps/MeanAirTemperature/"     # daily resolution
#~ input_ecmwf['files']['temperature']       +=  "Global_MeanAirTemperature_ERA-Interim-ECMWF_%04d-%02d-%02d_30min.map"
input_ecmwf = {}
input_ecmwf['files'] = {}
input_ecmwf['files']['rainfall']           = os.path.join('/data/hydroworld/forcing/ERA20C/RawData','totp%04d.nc')
input_ecmwf['files']['temperature']        = os.path.join('/data/hydroworld/forcing/ERA20C/RawData','tavg%04d.nc')

# era interim input files for monthly evaporation (derived based on the Penman-Monteith method using ERA Interim datasets) 
# RvB: changed to netCDF input 
#~ input_ecmwf['files']['evaporation_total']  = "/projects/dfguu/data/hydroworld/basedata/forcing/ERA-Interim/pcraster_maps/PotEvapotranspiration/"        # month resolution
#~ input_ecmwf['files']['evaporation_total'] +=  "Global_PotEvapotranspiration_ERA-Interim_%04d-%02d-00_30min.map"
input_ecmwf['files']['evaporation_total']  = os.path.join('/data/hydroworld/basedata/forcing/ERA20C','ERA20C_monthly_epot_1901_to_2010.nc')

ncVariableNames= {'temperature': 'var167', 'rainfall': 'var228', 'evaporation_total': 'potentialEvaporation'}

# snow correction input, derived by Rens van Beek, as proposed by Fiedler & Doell (2007)
input_snow_correction = {}
input_snow_correction['status'] = True     # True for including snow correction
input_snow_correction['folder'] = "/data/hydroworld/basedata/forcing/snowCorrection"

def main():

    # logger object
    loggger = Logger(outputFolder, "log_"+str(startYear)+"_to_"+str(endYear))
    testReport = False  # only for extra debugging (if True, it will report some maps to the current working directory)

    # set clone map
    pcr.setclone(cloneMapFileName)

    logger.info('Correcting daily ERA20C fields on the basis of CRU monthly values')
    logger.info('from the year '+str(startYear)+' to '+str(endYear))

    # CRU path and file root
    cruPath = input_cru['folder']
    cruInformation= {'data': 'dat', 'station': 'st0'}
    cruFileRoot= 'cru_ts3.21.%s.%s.nc'

    # snow correction
    snowCorrectionStatus   =  input_snow_correction['status']
    snowCorrectionPath     =  input_snow_correction['folder']
    snowCorrectionFileRoot = 'crsnow'

    # snow correction
    snowCorrectionStatus   =  input_snow_correction['status']
    snowCorrectionPath     =  input_snow_correction['folder']
    snowCorrectionFileRoot = 'crsnow'

    # correlation decay distance for CRU variables in kilometres
    correlationDecayDistance= {'tmp': 2000., \
                               'pre': 450., \
                               'wet': 450., \
                               'vap': 1000., \
                               'cld': 600.}

    # dictionary holding information on meteo data
    meteoVariables = {} 
      
    meteoVariables['rainfall'] = {}
    meteoVariables['rainfall']['ecmwf'] = 'ra'
    meteoVariables['rainfall']['sourceFileName'] = input_ecmwf['files']['rainfall']
    meteoVariables['rainfall']['cru'] =  'pre'
    meteoVariables['rainfall']['stn'] = ['pre']                                         # stn = station 
    meteoVariables['rainfall']['netcdf_variable_name'] = 'precipitation'
    meteoVariables['rainfall']['daily_unit'] = 'm.day-1'
    meteoVariables['rainfall']['month_unit'] = 'm.month-1'
    
    meteoVariables['temperature']= {}
    meteoVariables['temperature']['ecmwf']= 'ta'
    meteoVariables['temperature']['sourceFileName'] = input_ecmwf['files']['temperature']
    meteoVariables['temperature']['cru'] =  'tmp'
    meteoVariables['temperature']['stn'] = ['tmp']
    meteoVariables['temperature']['netcdf_variable_name'] = 'temperature'
    meteoVariables['temperature']['daily_unit'] = 'degrees Celcius'
    meteoVariables['temperature']['month_unit'] = 'degrees Celcius'
    
    meteoVariables['rainoccurrence'] = {}
    meteoVariables['rainoccurrence']['ecmwf'] = None                    # There is no information about rainoccurrence in ecmwf/era dataset
    meteoVariables['rainoccurrence']['cru'] = 'wet'
    meteoVariables['rainoccurrence']['stn']= ['wet']
    meteoVariables['rainoccurrence']['netcdf_variable_name'] = None
    meteoVariables['rainoccurrence']['daily_unit'] = None
    meteoVariables['rainoccurrence']['month_unit'] = 'day'
    
    # - added temporarily to exclude evaporation
    #~ meteoVariables['evaporation'] = {}
    #~ meteoVariables['evaporation']['ecmwf'] = 'etp'             
    #~ meteoVariables['evaporation']['ecmwf_total']    = input_ecmwf['files']['evaporation_total']  # monthly reference potential evaporation from ecmwf 
                                                                                                 #~ # will be used to cover areas with limited CRU stations 
    #~ meteoVariables['evaporation']['sourceFileName'] = input_ecmwf['files']['temperature']        # daily reference potential evaporation 
                                                                                                 #~ # will be estimated based on temperature (Hamon's method)
    #~ meteoVariables['evaporation']['cru'] = 'pet'               
    #~ meteoVariables['evaporation']['stn']= ['tmp','cld','vap']                                    # statin information will be on the basis of temperature, vapour pressure and cloudiness 
    #~ meteoVariables['evaporation']['netcdf_variable_name'] = 'referencePotET'
    #~ meteoVariables['evaporation']['daily_unit'] = 'm.day-1'
    #~ meteoVariables['evaporation']['month_unit'] = 'm.month-1'

    # netcdf format and attributes for output files:
    netcdf_attribute_dictionary = {}
    netcdf_attribute_dictionary['institution']  = "Utrecht University, Department of Physical Geography"
    netcdf_attribute_dictionary['title'      ]  = "Forcing dataset derived from CRU TS3.21 and ERA Interim datasets"
    netcdf_attribute_dictionary['source'     ]  = "None"
    netcdf_attribute_dictionary['history'    ]  = "None"
    netcdf_attribute_dictionary['references' ]  = "None"
    netcdf_attribute_dictionary['description']  = "None"
    netcdf_attribute_dictionary['comment'    ]  = "Prepared and calculated by Rens van Beek. "
    netcdf_attribute_dictionary['comment'    ] += "The main datasets used are CRU TS3.21 and ERA20C. "
    if snowCorrectionStatus: 
        netcdf_attribute_dictionary['comment'] += "Snow correction based on Fiedler and Doell is also included."

    # object for writing netcdf
    output = outputNetcdf.OutputNetcdf(cloneMapFileName, netcdf_attribute_dictionary)

    # preparing netcdf files for rainfall, temperature and referencePotET
    #
    # - exclude rain occurrence from the meteo variables to be processed
    meteoVariableKeys = meteoVariables.keys()
    meteoVariableKeys.remove('rainoccurrence')
    
    #
    for variable in meteoVariableKeys:
        #
        # preparing netcdf filenames for monthly and daily resolution:
        #
        # - daily file name:
        meteoVariables[variable]['daily_output_file']  =  outputFolder + "/"
        meteoVariables[variable]['daily_output_file'] += front_filename+"_daily_"
        meteoVariables[variable]['daily_output_file'] += meteoVariables[variable]['netcdf_variable_name']+"_"
        meteoVariables[variable]['daily_output_file'] += str(startYear)+'_to_'+str(endYear)+".nc"
        #
        output.createNetCDF(meteoVariables[variable]['daily_output_file'],\
                            meteoVariables[variable]['netcdf_variable_name'],\
                            meteoVariables[variable]['daily_unit'])

        # - monthly file name:
        meteoVariables[variable]['month_output_file']  =  outputFolder + "/"
        meteoVariables[variable]['month_output_file'] += front_filename+"_month_"
        meteoVariables[variable]['month_output_file'] += meteoVariables[variable]['netcdf_variable_name']+"_"
        meteoVariables[variable]['month_output_file'] += str(startYear)+'_to_'+str(endYear)+".nc"
        #
        output.createNetCDF(meteoVariables[variable]['month_output_file'],\
                            meteoVariables[variable]['netcdf_variable_name'],\
                            meteoVariables[variable]['month_unit'])
        #
        # - add variables anomaly, residual and anomaly type
        #   to monthly netcdf file
        output.addNewVariable(meteoVariables[variable]['month_output_file'],\
                              'anomaly_type',\
                              '-1: no correction; 0: additive; 1: multiplicative')
        output.addNewVariable(meteoVariables[variable]['month_output_file'],\
                              'anomaly',\
                              meteoVariables[variable]['month_unit'])
        output.addNewVariable(meteoVariables[variable]['month_output_file'],\
                              'residual',\
                              meteoVariables[variable]['month_unit'])

    # anomaly types
    anomalyTypeIDs = {-1: 'No correction on CRU data imposed', \
                       0: 'Additive correction / correction including rain days for precipitation', \
                       1: 'Multiplicative anomaly'}

    # rainfall threshold (m/day)
    generalRainfallThreshold= 1.e-3

    #-set scratch directory to the following directory :
    scratchDir = outputFolder+"/tmp_"+str(startYear)+"_"+str(endYear)
    os.system('rm -r '+scratchDir)
    os.makedirs(scratchDir)

    # set MV    
    MV = vos.MV   # use a consistent MV as defined in the vos module

    # get latitude and longitude
    latitude  = pcr.pcr2numpy(pcr.ycoordinate(pcr.boolean(1)),vos.MV).astype(np.float64)
    longitude = pcr.pcr2numpy(pcr.xcoordinate(pcr.boolean(1)),vos.MV).astype(np.float64)

    #-iterate over all years and months and variables
    for year in xrange(startYear, endYear+1):

        logger.info(str(year))

        # at the beginning of the year, reset the starting day to 1 
        startDay = 1

        # number of days within a year 
        yearLength = 365
        if calendar.isleap(year):
            yearLength += 1

        # loop for each month ==============================================================================================================
        #~ for month in xrange(1,2): # for debugging
        for month in xrange(1,12+1):

            msg = ' * %-10s %d:' % (calendar.month_name[month], year); logger.info(msg)

            # number of days within a month, last day/date of the month, and mid-month date 
            numberDays   = calendar.monthrange(year,month)[1]
            endDay       = startDay + numberDays
            midMonthDate = datetime.datetime(year,month,int(0.5*numberDays+0.5))

            # initialize dictionaries of monthly and daily values as well as the residual and iterate over all variables
            anomalyType = {}
            anomaly = {}
            originalMonthlyValue = {}
            originalTargetMonthlyValue = {}   # target without snow correction; this map is not spatially complete 
            cruTargetMonthlyValue = {}        # target with snow correction   ; this map is not spatially complete 
            targetMonthlyValue = {}           # target with snow correction   ; this is spatially-complete because it is `covered'
            updatedMonthlyValue = {}
            weight= {}
            residual = {}
            dailyValue = {}
            residual = {}

            for variable in meteoVariables.keys():        

                # initialize array with daily values, to be obtained from ERA-Interim and read in all values

                if variable in meteoVariableKeys:

                    logger.info('Reading daily ERA/ECMWF data: '+str(variable))
                    if variable == 'evaporation': 
                        logger.info("Potential ET is estimated based on temperature (Hamon's method).")

                    dailyValue[variable] = np.ones((numberDays,360,720))*vos.MV

################### RvB: disabled and replaced by netCDF file ############

                    #~ for dayCnt in xrange(numberDays):
                        #~ day= dayCnt+1
                        #~ fileName = (meteoVariables[variable]['sourceFileName'] % (year, month, day))
                        #~ dailyValue[variable][dayCnt,:,:] = pcr.pcr2numpy(pcr.readmap(fileName),vos.MV)
#~ 
                        #~ # daily potential evapotranspiration
                        #~ if variable == 'evaporation':
#~ 
                            #~ # set julianDay and compute daily evaporation; note that this is a full array without any missing values                                
                            #~ dailyValue[variable][dayCnt,...] = hamonET.potentialETHamon(dailyValue[variable][dayCnt,...],\
                                                               #~ startDay+dayCnt,yearLength,latitude)
                                                                                                                                
################### RvB: added ###########################################

                    for dayCnt in xrange(numberDays):
                        day= dayCnt+1
                        fileName = (meteoVariables[variable]['sourceFileName'] % year)
                        ncFileFormat,ncAttributes, ncDimensions, ncVariables= rvb_ncR.getNCAttributes(fileName)
                        ncDates= rvb_ncR.getNCDates(ncDimensions['time'],ncVariables['time'])
                        ncDate= datetime.datetime(year,month,day,9)
                        posCnt= rvb_ncR.getNCDateIndex(ncDate,ncDates)
                        dailyValue[variable][dayCnt,:,:] = rvb_ncR.readField(fileName,ncVariableNames[variable],posCnt)
                        if variable == 'temperature':
													dailyValue[variable][dayCnt,:,:] -= 273.15
												
##########################################################################


                logger.info('Calculating monthly ERA/ECMWF data (original data that will be corrected): '+str(variable))
                # - compute original monthly values from daily fields, note that the ERA-Interim output is spatially complete
                if variable == 'temperature':
                    originalMonthlyValue[variable] =  dailyValue[variable].mean(axis= 0)
                elif variable == 'rainoccurrence':
                    originalMonthlyValue[variable] = (dailyValue['rainfall'] >= generalRainfallThreshold).sum(axis= 0)
                    originalMonthlyValue[variable] = np.round(originalMonthlyValue[variable])
                    originalMonthlyValue[variable] = np.minimum(numberDays, originalMonthlyValue[variable])
                else: # rainfall and evaporation
                    originalMonthlyValue[variable] =  dailyValue[variable].sum(axis= 0)

                # get CRU variable name
                cruVarName = meteoVariables[variable]['cru']

                # - get target monthly value from CRU nc file	
                logger.info('Reading monthly CRU data (target data, reference for the correction): '+str(variable))
                dataKey    = 'data'    
                stationKey = 'station'
                ncFileName = os.path.join(cruPath,dataKey,cruVarName,cruFileRoot %(cruVarName,cruInformation[dataKey]))
                ncFileFormat, ncAttributes, ncDimensions, ncVariables = rvb_ncR.getNCAttributes(ncFileName)
                #
                # - get dates
                cruDates = rvb_ncR.getNCDates(ncDimensions['time'],ncVariables['time'], verbose= False)
                # - get corresponding match from cruDates
                posCnt = rvb_ncR.getNCDateIndex(midMonthDate,cruDates,'nearest')

                # - read field from CRU and set to MV
                cruTargetMonthlyValue[variable] = rvb_ncR.readField(ncFileName, cruVarName, posCnt)
                # -- the following 'swap' is needed while reading CRU-TS3.21
                cruTargetMonthlyValue[variable] = rvb_ncR.swapRows(cruTargetMonthlyValue[variable].filled([vos.MV]))

                # update units of variables from millimetres to metres,
                # apply optionally the snow fall correction
                # compute the mean monthly temperature
                if variable in['rainfall','evaporation']:
                    cruTargetMonthlyValue[variable][cruTargetMonthlyValue[variable] <> vos.MV] *= 0.001       # unit conversion from mm to m (CRU-TS3.21)
                if variable == 'evaporation':
                    cruTargetMonthlyValue[variable][cruTargetMonthlyValue[variable] <> vos.MV] *= numberDays  # conversion m/day to m/month  (CRU-TS3.21)
                #
                originalTargetMonthlyValue[variable] = cruTargetMonthlyValue[variable]

                if variable == 'rainfall' and snowCorrectionStatus:
                    logger.info('Correction in snow under catch areas for the variable '+str(variable))
                    snowCorrection = pcr.pcr2numpy(pcr.readmap(os.path.join(snowCorrectionPath,vos.generateNameT(snowCorrectionFileRoot,month))), vos.MV)
                    snowCorrection[snowCorrection == vos.MV]= 1.0
                    cruTargetMonthlyValue[variable][cruTargetMonthlyValue[variable] <> vos.MV] *= snowCorrection[cruTargetMonthlyValue[variable] <> vos.MV]

                ########################################################################################################     
                logger.info('Covering areas/cells with no or very limited CRU stations, for variables '+str(variable))
                ########################################################################################################     
                
                first_dataset = str(cruPath)
                if variable == 'evaporation':
                    cover_dataset = str(meteoVariables[variable]['ecmwf_total'])
                elif variable == 'rainoccurrence':
                    cover_dataset = str(meteoVariables['rainfall']['sourceFileName'])
                else: # rainfall and temperature
                    cover_dataset = str(meteoVariables[variable]['sourceFileName'])

                logger.info('The primary dataset used is taken from '+str(first_dataset))
                logger.info('The covering dataset used is from '+str(cover_dataset % year))

                logger.info('Calculating weights to combine both datasets (weights indicate the importance of the primary dataset).')

                #####################################################################################################################     
                # - get weight to compute the target value; initialized at zero, 
                #   with contributions of the different variables being added consecutively
                #
                weight[variable] = np.zeros(latitude.shape)

                # - read station info from file and add to weight
                for cruVarName in meteoVariables[variable]['stn']:

                    msg = 'processing station information for "%s" contributing to %-15s' % (cruVarName, variable)

                    weight_var = np.zeros(latitude.shape)

                    if cruVarName != 'cld': # for all variables with actual information on contributing stations

                        ncFileName = os.path.join(cruPath,stationKey,cruVarName,cruFileRoot %(cruVarName,cruInformation[stationKey]))

                        stations = rvb_ncR.readField(ncFileName, cruInformation[stationKey], posCnt)
                        stations = rvb_ncR.swapRows(stations.filled([vos.MV]))

                        stationLocations = globGeo.getMappedLocations(stations, vos.MV)

                        msg += ' containing %5d actual station locations' % stationLocations.shape[0]
                        logger.info(msg)

                        #-find for each station the distance to all points on the map and compute the weight
                        # as the ratio over the correlation decay distance
                        #
                        i_station = 0
                        for station in stationLocations:
                            #
                            i_station += 1 
                            msg = 'processing station: '+str(i_station)+' from '+str(stationLocations.shape[0])
                            logger.info(msg)
                            msg = station
                            logger.info(msg)
                            
                            row, col, value = tuple(station)
                            #
                            latOrigin    =  latitude[row-1, col-1]
                            lonOrigin    = longitude[row-1, col-1]
                            arcDistance  = globGeo.getArcDistance(latOrigin, lonOrigin, latitude, longitude)*1.e-3  # unit: km
                            #
                            weight_var   += value*np.maximum(0.0,\
                                correlationDecayDistance[cruVarName]-arcDistance)/correlationDecayDistance[cruVarName]

                        #-set weight to minimum of 1 for each variable
                        weight_var = np.minimum(1.,weight_var)

                    elif cruVarName == 'cld': # this variable (i.e. cloud cover) is without station info

                        # compute the ratio on the basis of the ratio of contributing stations, in this case
                        # at least 100 stations over the correlation decay distance

                        ncFileName =  os.path.join(cruPath,stationKey,cruVarName,cruFileRoot %\
                                                  (cruVarName,cruInformation[stationKey].replace('0','n')))
                        
                        stations = rvb_ncR.readField(ncFileName, cruInformation[stationKey].replace('0','n'), posCnt)
                        stations = rvb_ncR.swapRows(stations.filled([vos.MV]))

                        msg += 'containing %5d maximum stations within CCD' % stations[stations <> vos.MV].max()
                        logger.info(msg)
                        
                        # set weight (minimum 1)
                        weight_var[stations <> vos.MV] = np.minimum(1.,stations[stations <> vos.MV]/100.)

                    # add the weight for the current variable to the overall weight
                    weight[variable] += weight_var        

                # update weight to ratio between 0 and 1 once all stations are processed
                weight[variable] = np.minimum(len(meteoVariables[variable]['stn']),weight[variable])/\
                                   len(meteoVariables[variable]['stn'])

                # and reset the weight to zero outside the CRU landmask
                weight[variable][cruTargetMonthlyValue[variable] == vos.MV] = 0.

                logger.info('Weight factors have been calculated.')

                ########################################################################################################     

                logger.info('Combining two datasets (using weight factors): get target monthly values.')
                
                # - get target monthly value
                #   - this is the monthly total of the daily values with the exception
                #     of the evaporation, which has a monthly field specified; 
                #   - later, this value is then weighed with the CRU target value, 
                #     ensuring missing values outside the CRU lands mask

                targetMonthlyValue[variable] = np.zeros(originalMonthlyValue[variable].shape)
                #
                if variable == 'evaporation':
                    targetMonthlyValue[variable] = pcr.pcr2numpy(\
                                                   pcr.readmap((meteoVariables['evaporation']['ecmwf_total'] % (year, month))),vos.MV)
                    targetMonthlyValue[variable][targetMonthlyValue[variable] <> vos.MV] *= numberDays
                #
                elif variable == 'rainoccurrence':
                    targetMonthlyValue[variable][targetMonthlyValue['rainfall'] > 0.] = \
                                                   np.maximum(1.,originalMonthlyValue[variable][targetMonthlyValue['rainfall'] > 0.])
                    targetMonthlyValue[variable] = np.round(targetMonthlyValue[variable])
                    targetMonthlyValue[variable] = np.minimum(numberDays, targetMonthlyValue[variable])
                    targetMonthlyValue[variable][(targetMonthlyValue['rainfall'] > 0.) &\
                                                 (targetMonthlyValue[variable]  == 0.)] = 1.0
                #
                else: # rainfall and temperature
                    targetMonthlyValue[variable] = originalMonthlyValue[variable].copy()

                # update target values where CRU data are available
                #
                mask = (weight[variable] > 0)
                targetMonthlyValue[variable][mask] = \
                            weight[variable][mask] * cruTargetMonthlyValue[variable][mask] + \
                            np.maximum(0.,1.-weight[variable][mask])*\
                        targetMonthlyValue[variable][mask]
                
                # correcting rain occurrence after weights being applied
                #
                if variable == 'rainoccurrence':
                    targetMonthlyValue[variable][targetMonthlyValue['rainfall'] > 0.] = \
                                                   np.maximum(1.,originalMonthlyValue[variable][targetMonthlyValue['rainfall'] > 0.])
                    targetMonthlyValue[variable] = np.round(targetMonthlyValue[variable])
                    targetMonthlyValue[variable] = np.minimum(numberDays, targetMonthlyValue[variable])
                    targetMonthlyValue[variable][(targetMonthlyValue['rainfall'] > 0.) &\
                                                 (targetMonthlyValue[variable]  == 0.)] = 1.0

                #-write test maps of original and target monthly values optionally
                if testReport:
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,weight[variable]               ,vos.MV),'weight_%s.map'   % variable)                    
                    pcr.report(pcr.numpy2pcr(pcr.Scalar, originalMonthlyValue[variable],vos.MV),'original_%s.map' % variable)
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,cruTargetMonthlyValue[variable],vos.MV),'cru_%s.map'      % variable)
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,   targetMonthlyValue[variable],vos.MV),'target_%s.map'   % variable)

                # - reporting the statistics and differences between the 
                #   updated  targetMonthlyValue and 
                #   original originalTargetMonthlyValue (before snow correction and weight implemted)
                #
                # - calculating residual/bias map to the original target (cru)
                difference = targetMonthlyValue[variable] - \
                     originalTargetMonthlyValue[variable]
                #
                # reporting the statistics to the logger
                log_msg  = '\n'
                log_msg += '\n'
                log_msg += ' - Checking the differences between updated and \n'
                log_msg += '   original cru targets - %s - %s \n' % (variable, meteoVariables[variable]['month_unit'])
                log_msg += '=====================================================================================\n'
                dataNames =  ['update_cru','origin_cru','difference']
                dataFields = {'update_cru': targetMonthlyValue[variable][originalTargetMonthlyValue[variable] <> vos.MV],\
                              'origin_cru': originalTargetMonthlyValue[variable][originalTargetMonthlyValue[variable] <> vos.MV],\
                              'difference': difference[originalTargetMonthlyValue[variable] <> vos.MV]}
                for dataName in dataNames:
                	log_msg += '%-10s:' % dataName
                	#-get statistics
                	statistics = rvb_ano.getStatistics(dataFields[dataName][dataFields[dataName] <> vos.MV], vos.MV)
                	for stat in ['number', 'mean', 'std', 'min', 'max']:
                		log_msg += ' %6s: %12.6g' % (stat,statistics[stat]) 
                	log_msg += '\n'
                logger.info(log_msg)
 
                # - option for interpolation/extrapolation of target value
                targetExtrapolation = True
                if targetExtrapolation:
                    logger.info('Performing interpolation/extrapolation in order to avoid strange gradients: ' +str(variable))
                    values_within_cru_mask = targetMonthlyValue[variable]
                    values_within_cru_mask[cruTargetMonthlyValue[variable] == vos.MV] = vos.MV
                    #
                    target_filled_map = rvb_ano.mapFilling(\
                                        pcr.numpy2pcr(pcr.Scalar, values_within_cru_mask        , vos.MV),\
                                        pcr.numpy2pcr(pcr.Scalar, originalMonthlyValue[variable], vos.MV)) 
                    targetMonthlyValue[variable] = pcr.pcr2numpy(\
                                        target_filled_map, vos.MV)

                #-write test maps of original and target monthly values optionally
                if testReport:
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,   targetMonthlyValue[variable],vos.MV),'targ_int_%s.map'   % variable)

                # - reporting the statistics and differences between the 
                #   derived/updated target and original target values - This is an important check while interpolation/extrapolation is introduced.
                #
                # - calculating residual/bias map to the original target (cru)
                # - calculating residual/bias map to the original target (cru)
                difference = pcr.pcr2numpy(target_filled_map -\
                         pcr.numpy2pcr(pcr.Scalar,\
                         originalTargetMonthlyValue[variable], vos.MV),\
                         vos.MV)
                #
                # reporting the statistics to the logger
                log_msg  = '\n'
                log_msg += '\n'
                log_msg += " - Checking the differences between filled (edwin's interpolation/extrapolation method) and \n"
                log_msg += '   original cru targets - %s - %s \n' % (variable, meteoVariables[variable]['month_unit'])
                log_msg += '============================================================================================\n'
                dataNames = [ 'filled_cru','origin_cru','difference']
                dataFields = {'filled_cru': targetMonthlyValue[variable],\
                              'origin_cru': originalTargetMonthlyValue[variable],\
                              'difference': difference}
                for dataName in dataNames:
                	log_msg += '%-10s:' % dataName
                	#-get statistics
                	statistics = rvb_ano.getStatistics(dataFields[dataName][dataFields[dataName] <> vos.MV], vos.MV)
                	for stat in ['number', 'mean', 'std', 'min', 'max']:
                		log_msg += ' %6s: %12.6g' % (stat,statistics[stat]) 
                	log_msg += '\n'
                logger.info(log_msg)

            ##############################################################################################################
            logger.info('Start computing and applying anomalies for all variables.')
            logger.info('')
            ##############################################################################################################

            # - Iterate over all variables of interest to compute anomalies
            for variable in meteoVariables.keys():

                # - set mask for processing 
                mask = (targetMonthlyValue[variable] <> vos.MV)         # original Rens's line: mask= (weight[variable] > 0) & (cruTargetMonthlyValue[variable] <> MV)

                # - create noise to downscale rainfall: use daily temperature 
                noise = rvb_ano.deriveRelativeValues(dailyValue['temperature'], vos.MV, 0.1)


                anomaly[variable]     = np.ones((360,720))* vos.MV
                anomalyType[variable] = np.ones((360,720))*-1           # first, set anomaly to -1

                # - computing anomalies                
                #   first, additive anomalies are applied for all variables                
                logger.info('Computing anomalies: '+str(variable))
                anomaly[variable] = rvb_ano.deriveAnomaly(originalMonthlyValue[variable],\
                                                            targetMonthlyValue[variable],'additive', vos.MV)[0]

                # - anomaly will be handled per variable
                logger.info('Applying anomalies and obtain updated/downscaled values: '+str(variable))

                # -- temperature: additive anomaly
                if variable == 'temperature':
                    # - anomaly type is additive throughout
                    anomalyType[variable][mask] = 0

                    # - calculate anomaly and obtain updated variable
                    updated_value = rvb_ano.applyAnomaly(anomaly[variable],\
                                                         dailyValue[variable],\
                                                         targetMonthlyValue[variable],'additive',vos.MV)[0]

                    # - insert corrected values into daily values
                    for iCnt in xrange(noise.shape[0]):

                        offSet= ((datetime.datetime(int(year),int(month),1, 0)-\
													datetime.datetime(int(year),1,1, 0))).days+1

                        if testReport:
													pcr.report(pcr.numpy2pcr(pcr.Scalar,dailyValue[variable][iCnt,...],vos.MV),\
														os.path.join('scratch',generateNameT(variable[:4]+'_org',offSet+iCnt)))
											
                        dailyValue[variable][iCnt,...][anomalyType[variable] >= 0] = \
                               updated_value[iCnt,...][anomalyType[variable] >= 0]
                               
                        if testReport:
													pcr.report(pcr.numpy2pcr(pcr.Scalar,updated_value[iCnt,...],vos.MV),\
														os.path.join('scratch',generateNameT(variable[:4]+'_upd',offSet+iCnt)))

                # -- rainfall: multiplicative anomaly 
                if variable == 'rainfall':

                    # - get the integer number of rain days and dry days; if there is rain there is at least one rain day
                    targetRainDays = targetMonthlyValue['rainoccurrence']
                    targetRainDays[(targetMonthlyValue[variable] > 0.) &\
                        (targetRainDays == 0)] = 1
                    targetRainDays[mask == False] = originalMonthlyValue['rainoccurrence'][mask == False]
                    dryDays = numberDays - targetRainDays                                                
                                                                                                         
                    # - set daily values to zero on days with rain below the threshold specified
                    dailyValue[variable][dailyValue[variable] < generalRainfallThreshold] = 0.

                    # - and derive the anomaly type for the rainfall (and rain rainoccurrence)
                    #   this is one if the CRU value can be applied directly to the ERA/ECMWF data
                    #   otherwise zero (additive correction introduced if no rain found in either ERA/ECMWF or CRU data)
                    anomalyType[variable][mask] = (dailyValue[variable].sum(axis= 0)[mask] > 0) &\
                                                  (targetMonthlyValue[variable][mask] >= 0)
                    
                    # - create noise to downscale rainfall: use daily temperature: RvB Disabled, needed earlier for processing individual vars
                    #~ noise = rvb_ano.deriveRelativeValues(dailyValue['temperature'], vos.MV, 0.1)
                    for iCnt in xrange(noise.shape[0]):            
                        noise[iCnt,...][anomalyType[variable] <> 0]= 0
                    noise[noise <> vos.MV]  = 1. - noise[noise <> vos.MV]
                    noise[noise <> vos.MV] *= generalRainfallThreshold

                    # - set noise to zero in case no rain occurs using the threshold for rainfall occurrence
                    rainfallThreshold = rvb_ano.deriveOccurrenceThreshold(noise, dryDays, vos.MV)
                    noRainOccurrence  = rvb_ano.applyOccurrenceThreshold(noise, rainfallThreshold, vos.MV)
                    noise[noRainOccurrence] = 0.

                    # - add noise to update the daily rainfall
                    noise += dailyValue[variable]

                    # - remove values outside mask
                    for iCnt in xrange(noise.shape[0]):
                        noise[iCnt,...][mask == False] = vos.MV

                    # - remove any zeros where rain occurs the entire month,
                    #   scale values to unity and apply anomaly using the monthly rainfall total
                    noise = rvb_ano.removeZeros(noise, targetRainDays == numberDays, vos.MV)
                    noise = rvb_ano.deriveCumulativeValues(noise, vos.MV)
                    noise = rvb_ano.applyAnomaly(targetMonthlyValue[variable], noise, targetMonthlyValue[variable], 'multiplicative', vos.MV)[0]


                    # - insert corrected values into daily values
                    for iCnt in xrange(noise.shape[0]):                                   # original Rens's line: dailyValue[variable] = noise.copy()
                        dailyValue[variable][iCnt,...][anomalyType[variable] >= 0] = \
                                       noise[iCnt,...][anomalyType[variable] >= 0]

                # -- evaporation: multiplicative anomaly 
                if variable == 'evaporation':
                    
                    # - anomaly type is multiplicative throughout
                    anomalyType[variable][mask] = 1
                    
                    # - use daily evaporation preferably as noise, with a constant addition of 0.1 mm per day
                    #
                    noise = dailyValue[variable].copy() + 0.1/1000.           # The unit of dailyValue['evaporation'] is m.
                    noise = rvb_ano.deriveCumulativeValues(noise, vos.MV)
                    #
                    # - insert updated values
                    noise = rvb_ano.applyAnomaly(targetMonthlyValue[variable], noise, targetMonthlyValue[variable], 'multiplicative', vos.MV)[0]
                    for iCnt in xrange(noise.shape[0]):
                        dailyValue[variable][iCnt,...][anomalyType[variable] >= 0] = \
							           noise[iCnt,...][anomalyType[variable] >= 0]

                # - add anomaly type for rain occurrence
                if variable == 'rainoccurrence':
                    anomalyType[variable] = anomalyType['rainfall'].copy()

                # - compute monthly updated value
                logger.info('Computing monthly updated values: '+str(variable))
                #
                if variable == 'temperature':
                    updatedMonthlyValue[variable] = dailyValue[variable].mean(axis= 0)
                elif variable == 'rainoccurrence':
                    if targetExtrapolation: updatedMonthlyValue[variable] = \
                        ((dailyValue['rainfall'] > 0).sum(axis= 0))
                    updatedMonthlyValue[variable] = (dailyValue['rainfall'] >= generalRainfallThreshold).sum(axis= 0)
                    updatedMonthlyValue[variable][anomalyType[variable] == 0] = \
                        ((dailyValue['rainfall'] > 0).sum(axis= 0))[anomalyType[variable] == 0]
                else:
                    updatedMonthlyValue[variable] = dailyValue[variable].sum(axis= 0)


                # - compute residual value
                logger.info('Computing residual: target values - updated values: '+str(variable))
                #
                residual[variable] = targetMonthlyValue[variable] - updatedMonthlyValue[variable]
                residual[variable][mask == False] = vos.MV
                #
                #-report anomaly, anomaly type, residual and final value optionally
                if testReport:
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,anomaly[variable],vos.MV)            , 'anomaly%s.map'     % variable)
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,anomalyType[variable],vos.MV)        , 'anomalytype%s.map' % variable)
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,residual[variable],vos.MV)           , 'residual%s.map'    % variable)
                    pcr.report(pcr.numpy2pcr(pcr.Scalar,updatedMonthlyValue[variable],vos.MV), 'updated_%s.map'    % variable)
                    
                # - always report statistics per anomaly type per variable when processed
                wStr  = '\n'
                wStr += '\n'
                wStr += 'Report statistics per anomaly type - '+str(variable)+' '+str(meteoVariables[variable]['month_unit'])+'\n'
                wStr += '======================================================================================================\n'
                #
                anomalyTypes = np.unique(anomalyType[variable][anomalyType[variable] != vos.MV])
                #
                #
                for anomalyTypeID in anomalyTypes:
                    wStr += '\n'
                    wStr += '   %d: %s - %s\n' % (anomalyTypeID, variable.title(), anomalyTypeIDs[anomalyTypeID])
                    mask = anomalyType[variable] == anomalyTypeID
                    dataNames  = ['original','target','updated','anomaly','residual']
                    dataFields = {'original': originalMonthlyValue[variable], \
                                  'target': targetMonthlyValue[variable],
                                  'updated': updatedMonthlyValue[variable],\
                                  'anomaly': anomaly[variable],
                                  'residual': residual[variable]}
                    for dataName in dataNames:
                        wStr += '%-10s:' % dataName
                        #-get statistics
                        statistics = rvb_ano.getStatistics(dataFields[dataName][mask], vos.MV)
                        for stat in ['number', 'mean', 'std', 'min', 'max']:
                            wStr += ' %6s: %12.6g' % (stat,statistics[stat]) 
                        wStr += '\n'
                logger.info(wStr)

                # - writing data to netcdf files
                if variable in meteoVariableKeys:
                    
                    # writing daily data
                    for i_day in range(1, int(numberDays)+1):
                        log_msg  = "Writing daily "+str(variable)+" to "+meteoVariables[variable]['daily_output_file']
                        logger.info(log_msg)
                        output.data2NetCDF(meteoVariables[variable]['daily_output_file'],\
                                           meteoVariables[variable]['netcdf_variable_name'],\
                                           dailyValue[variable][i_day-1],\
                                           datetime.datetime(int(year),int(month),int(i_day), 0))
                    
                    # writing monthly data
                    log_msg  = "Writing monthly data to "+meteoVariables[variable]['month_output_file']
                    log_msg += "(including anomaly_type, anomaly and residual)" 
                    logger.info(log_msg)
                    varName = [ meteoVariables[variable]['netcdf_variable_name'],\
                               'anomaly_type',\
                               'anomaly',\
                               'residual']
                    varField = { meteoVariables[variable]['netcdf_variable_name']: updatedMonthlyValue[variable],\
                                'anomaly_type': anomalyType[variable],\
                                'anomaly': anomaly[variable],\
                                'residual': residual[variable]}           
                    output.dataList2NetCDF(meteoVariables[variable]['month_output_file'],\
                                           varName,\
                                           varField,\
                                           datetime.datetime(int(year),int(month),int(numberDays), 0))

            #-end of month, end line on screen and update startDay
            startDay = endDay
        
        # end of loop for each month =======================================================================================================

        # end of year
        logger.info('\n')
 
if __name__ == '__main__':    
    print 'Correcting ERA-Interim with CRU observations'
    main()
    
