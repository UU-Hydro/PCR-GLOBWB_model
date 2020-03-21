# pcrglob_ClimateAnomalies - corrects a stack of fields to a mean specified
# main is implemented to test this using the CRU long-term means to correct the ERA-40 database

#-modules used
import sys
import datetime
import numpy as np
import pcraster as pcr

import virtualOS as vos

from types import NoneType, BooleanType

import logging

# logger object
logger = logging.getLogger(__name__)

#-functions

def mapFilling(map_with_MV, map_without_MV, method = "window_average"):

    # ----- method 1: inverse distance method (but too slow)
    if method == "inverse_distance":
        logger.info('Extrapolation using "inverse distance" in progress!')
        #
        # - interpolation mask for cells without values
        interpolatedMask = pcr.ifthenelse(\
                           pcr.defined(map_with_MV),\
                           pcr.boolean(0),\
                           pcr.boolean(1),)
        map_with_MV_intrpl = pcr.inversedistance(interpolatedMask, \
                                               map_with_MV, 2, 1.50, 25)
    #
    else: # method 2: using window average
        logger.info('Extrapolation using "modified window average" in progress!')
        #
        map_with_MV_intrpl = 0.70 * pcr.windowaverage(map_with_MV, 1.50) + \
                             0.25 * pcr.windowaverage(map_with_MV, 2.00) + \
                             0.05 * pcr.windowaverage(map_with_MV, 2.50) + \
                             pcr.scalar(0.0)
    #
    # - interpolated values are only introduced in cells with MV 
    map_with_MV_intrpl = pcr.cover(map_with_MV, map_with_MV_intrpl)
    #
    # - calculating weight factor:
    weight_factor = pcr.scalar(pcr.defined(map_with_MV))
    weight_factor = pcr.windowaverage(0.70*weight_factor, 1.50) +\
                    pcr.windowaverage(0.25*weight_factor, 2.00) +\
                    pcr.windowaverage(0.05*weight_factor, 2.50)
    weight_factor = pcr.min(1.0, weight_factor)
    weight_factor = pcr.max(0.0, weight_factor)
    weight_factor = pcr.cover(weight_factor, 0.0)
    #
    # merge with weight factor
    merged_map = weight_factor  * map_with_MV_intrpl + \
          (1.0 - weight_factor) * map_without_MV
    #
    # retain the original values and make sure that all values are covered
    #~ filled_map = pcr.cover(map_with_MV, merged_map, map_without_MV)
    filled_map = pcr.cover(map_with_MV, merged_map)

    logger.info('Extrapolation is done!')
    return filled_map

def getRank(x,MV= None):
    """Returns the rank order of vector x\
 with missing values optionally left out."""
    if x.ndim == 1:
        m= np.ones((x.size), dtype= bool)
        if not isinstance(MV,type(None)):
            m= x <> MV
        s= x[m]
        s.sort(kind= 'mergesort')
        n= np.arange(s.size,dtype= int)
        r= np.zeros(x.size, dtype= int)-1
        for i in s:
            r[x == i]= n[s == i]
        return r
    else:
        sys.exit('array to be sorted is not a vector')

def rankArray(x,MV= None):
    """Returns the rank order of x for the first axis \
 with missing values optionally left out."""
    shape= x.shape
    if len(shape) > 1:
        x.shape= (shape[0],-1)
        r= np.zeros(x.shape, dtype= int)-1
        for sCnt in xrange(x.shape[1]):
            s= x[:,sCnt]
            r[:,sCnt]= getRank(s,MV)
    else:
        r= getRank(x,MV)
    r.shape= shape
    return r

def getStatistics(x, MV):
    """Reads in an array and returns the mean, standard deviation, minimum and maximum\
 being masked by the specified missing value identifier"""
    if (x <> MV).sum() > 0:
        return {'mean': x[x <> MV].mean(),'std': x[x <> MV].std(),\
            'min': x[x <> MV].min(), 'max': x[x <> MV].max(), 'number': (x <> MV).sum()}
    else:
        return {'mean': MV,'std': MV, 'min': MV, 'max': MV, 'number': 0}

def checkDimensions(x,v,dimMax= 1):
    """Checks the dimensions of v against x in the sense that\
 v has the same shape as x or is a multiple thereof"""
    offSet= v.ndim-x.ndim
    if offSet <= dimMax:
        if v.shape[offSet:] != x.shape:
            sys.exit('shapes %s and %s of arrays are mismatched' % (v.shape,x.shape))
    else:
        sys.exit('shapes %s and %s of arrays are mismatched' % (v.shape,x.shape))    

def deriveAnomaly(originalValues,targetValue,anomalyType,MV,verbose= False):
    """Retrieves the field specifying the anomaly of the specified type between\
 the original values and the target values as array, having equal shapes\
 and being masked by a common missing value (MV) identifier.\
 Verbose output returns an additional dictionary with statistics on original and\
 target value and the resulting anomaly"""
    if anomalyType not in ['additive','multiplicative'] :
        sys.exit(' %s anomaly type is not defined' % anomalyType)
    #-check dimensions of values
    checkDimensions(targetValue,originalValues)
    multiDimensional= originalValues.shape != targetValue.shape
    #-get original value
    originalValue= np.ones(targetValue.shape)*MV
    if multiDimensional:
        mask= np.all(originalValues <> MV, axis= 0)
        originalValue[mask]= originalValues.mean(axis= 0)[mask]
    else:
        originalValue= originalValues
  #-create mask and compute anomaly dependent on type
    anomaly= np.ones(targetValue.shape)*MV
    mask= (targetValue <> MV) & (originalValue <> MV)
    if anomalyType == 'additive':
        anomaly[mask]= targetValue[mask]-originalValue[mask]
    elif anomalyType == 'multiplicative':
        mask= mask & (originalValue <> 0)
        anomaly[mask]= targetValue[mask]/originalValue[mask]
    #-compute statistics in case of verbose output
    stats= {}
    stats['target'] = getStatistics(targetValue,MV)
    stats['original'] = getStatistics(originalValue,MV)
    stats['anomaly'] = getStatistics(anomaly,MV)
    if verbose:
        print ' *** verbose output ***'
        for varName in stats.keys():
            wStr= '%-12s ' % varName
            for key, value in stats[varName].iteritems():
                wStr+= '%s: %10f; ' % (key,value)
            print wStr
    #-return output
    return anomaly, stats

def applyAnomaly(anomaly,values,targetValue,anomalyType,MV,verbose= False):
    """Updates an array of variables to a mean specified by addition\
 values are listed by time on the first dimension, with rows and columns on the second and third axis\
 Verbose output returns an additional dictionary with statistics on original and\
 target value and the resulting anomaly"""
    values= values.copy()
    if anomalyType not in ['additive','multiplicative'] :
        sys.exit(' %s anomaly type is not defined' % anomalyType)
    #-check dimensions of values
    checkDimensions(targetValue,values)
    multiDimensional= values.shape != targetValue.shape
    #-get mean from values, create mask and compute anomaly    
    anomalyMask= (anomaly <> MV)
    if multiDimensional:
        anomalyMask= anomalyMask & np.all(values <> MV,axis= 0)
    else:
        anomalyMask= anomalyMask & (values <> MV)
    selectionMask= anomalyMask & (targetValue <> MV)
    #-apply anomalies
    if multiDimensional:
        for value in values[:,]:
            if anomalyType == 'additive':
                value[anomalyMask]+= anomaly[anomalyMask]
            elif anomalyType == 'multiplicative':
                value[anomalyMask]*= anomaly[anomalyMask]
            value[anomalyMask == False]= MV
    else:
        if anomalyType == 'additive':
            values[anomalyMask]+= anomaly[anomalyMask]
        elif anomalyType == 'multiplicative':
            values[anomalyMask]*= anomaly[anomalyMask]
        values[anomalyMask == False]= MV
    #-compute mean value and residual
    value= np.ones(targetValue.shape)*MV
    residual= np.ones(targetValue.shape)*MV
    if multiDimensional:
        value[selectionMask]= values.mean(axis= 0)[selectionMask]
    else:
        value[selectionMask]= values[selectionMask]
    residual[selectionMask]= value[selectionMask]-targetValue[selectionMask]
    #~ #-mask target to get comparable statistics
    #~ targetValue[selectionMask == False]= MV
    stats= {}
    stats['target']= dict({'min': 0, 'mean': 0, 'max': 0, 'std': 0,'number': 0})
    stats['value']= dict({'min': 0, 'mean': 0, 'max': 0, 'std': 0,'number': 0})
    stats['residual']= dict({'min': 0, 'mean': 0, 'max': 0, 'std': 0,'number': 0})
    stats['target']['mean'],stats['target']['std'],\
        stats['target']['min'],stats['target']['max'], stats['value']['number']= \
            getStatistics(targetValue,MV)    
    stats['value']['mean'],stats['value']['std'],\
        stats['value']['min'],stats['value']['max'], stats['value']['number'] = \
            getStatistics(value,MV)
    stats['residual']['mean'],stats['residual']['std'],\
        stats['residual']['min'],stats['residual']['max'], stats['value']['number']= \
            getStatistics(residual,MV)
    if verbose:
        print ' *** verbose output ***'
        for varName in stats.keys():
            wStr= '%-12s ' % varName
            for key, value in stats[varName].iteritems():
                wStr+= '%s: %10f; ' % (key,value)
            print wStr
    #-return output
    return values, stats

def deriveOccurrenceThreshold(originalValues,targetOccurrence,MV, verbose= False):
    """Reads in an array of original values with the time dimension being defined by the zero axis\
 and the number target occurrences for the field described by the higher dimensions.\
 It returns the threshold that approximates the number of days the best for days with\
 values <= threshold."""
    #-initialize threshold with missing values
    threshold= np.ones(targetOccurrence.shape,dtype= float)*MV
    mask= (targetOccurrence <> MV) & np.all(originalValues <> MV,axis= 0)
    #~ maxValue= (10.*originalValues.max()).round()
    #~ ranks= rankArray(originalValues)
    #-iterate over rows and columns in target mask
    nrRows,nrCols= targetOccurrence.shape
    for rowCnt in xrange(nrRows):
       for colCnt in xrange(nrCols):
           if mask[rowCnt,colCnt]:
               #-create rank and selection vector
               rank= 0
               threshold[rowCnt,colCnt]= 0.
               ranks= rankArray(originalValues[:,rowCnt,colCnt])+1
               vsel= ranks == targetOccurrence[rowCnt,colCnt]
               if np.any(vsel):    
                   rank= ranks[vsel]
                   threshold[rowCnt,colCnt]= originalValues[:,rowCnt,colCnt][vsel]
               #-output
               if verbose:
                   print 'row, col: %4d,%4d; occurrence, rank: %3d, %3d; threshold: %f' %\
                       (rowCnt,colCnt,targetOccurrence[rowCnt,colCnt],\
                           rank,threshold[rowCnt,colCnt])
    #-return threshold array
    return threshold

def applyOccurrenceThreshold(originalValues,threshold,MV):
    """Reads in an array of original values with the time dimension being defined by the zero axis\
       and the threshold and returns an updated array with all occurrences set to true."""
    #-initialize occurrence with missing values
    mask= (threshold <> MV) & np.all(originalValues <> MV,axis= 0)
    occurrence= np.zeros(originalValues.shape,dtype= bool)
    #-iterate over rows and columns in target mask
    nrRows,nrCols= threshold.shape
    for rowCnt in xrange(nrRows):
       for colCnt in xrange(nrCols):
           if threshold[rowCnt,colCnt] <> MV:
               occurrence[:,rowCnt,colCnt]= originalValues[:,rowCnt,colCnt] <= threshold[rowCnt,colCnt]
    return occurrence

def removeZeros(values,nonZero, MV):
    """removes zeroes from an array recast to 2-d"""
    #-recast values and nonZero if necessary
    originalShape= values.shape
    values.shape= (originalShape[0],-1)
    if isinstance(nonZero,BooleanType):
        nonZero= np.array([nonZero] * values.shape[1])
    else:
        nonZero= nonZero.ravel()
    #-iterate over all values
    for iCnt in xrange(values.shape[1]):
        v= values[:,iCnt]
        m= v <> MV
        s= v[m].sum()
        validEntries= np.size(v[m])
        if validEntries > 0 and v[m].min() == 0 and nonZero[iCnt]:
            #-get offSet and fill value
            if np.any(v[m] > 0):
                offSet= np.min(v[(v > 0) & (v <> MV)])
                v[v == 0]= (v[v == 0]+0.5)/(offSet+0.5)
                #-ensure values are conservative
                v[m]*= s/(v[m].sum())
            else:
                offSet= float(validEntries)
                v[v == 0]= 1.0/offSet
        values[:,iCnt]= v
    #-all values set, return values
    values.shape= originalShape
    return values

def deriveRelativeValues(values, MV, additionalNoise= 0., nonZero= None):
    """Reads in an array and derives the relative values ranging between 0\
 and 1 for min and max respectively over the zeroth order axis"""
    #-copy values and set noise
    values= values.copy()
    mask= np.all(values <>  MV, axis= 0)
    noise= np.random.random(size= values.size)*additionalNoise
    noise.shape= values.shape    
    for iCnt in xrange(values.shape[0]):
        values[iCnt,...][mask]+= noise[iCnt,...][mask]
        values[mask == False]= MV
    #-get scaling
    scaleFactor= values.max(axis= 0)-values.min(axis= 0)
    offSet= -values.min(axis= 0)
    scaleFactor[mask == False]= MV
    offSet[mask == False]= MV
    for iCnt in xrange(values.shape[0]):
        values[iCnt,...][mask & (scaleFactor > 0)]+= offSet[mask & (scaleFactor > 0)]
        values[iCnt,...][mask & (scaleFactor > 0)]/= scaleFactor[mask & (scaleFactor > 0)]
        values[iCnt,...][scaleFactor == 0]*= 0
    #-check whether zero values are allowed or not
    if not isinstance(nonZero,NoneType):    
        removeZeros(values,nonZero,MV)
    #-all values set, return values
    return values

def deriveCumulativeValues(values, MV, nonZero= None):
    """Reads in an array and derives the cumulative distribution 
 ranging between 0 and 1 over the zeroth order axis"""
    #-copy values and set noise
    values= values.copy()
    mask= np.all(values <>  MV, axis= 0)
    #-check whether zero values are allowed or not
    if not isinstance(nonZero,NoneType):    
        removeZeros(values,nonZero,MV)
    #-get scaling
    scaleFactor= values.sum(axis= 0)
    scaleFactor[mask == False]= MV
    for iCnt in xrange(values.shape[0]):
        values[iCnt,...][mask & (scaleFactor > 0)]/= scaleFactor[mask & (scaleFactor > 0)]
        values[iCnt,...][scaleFactor == 0]*= 0
    #-all values set, return values
    return values

def main():
    #-default function: test
    #-modules
    import os,calendar, zipfile, zlib
    import PCRaster as pcr
    from PCRaster.Framework import generateNameT
    from PCRaster.NumPy import numpy2pcr, pcr2numpy
    #-test
    MV= -999.9
    #-test on  arrays
    #-rank order on vector
    a= np.arange(27)
    a[15:]-= 27
    r= rankArray(a)
    print a,r
    #-rank order on array
    a.shape= (3,3,3)
    r= rankArray(a)
    print r
    #-anomalies
    t= np.arange(9.)
    v= np.flipud(t.copy())
    t[t == 4.]= MV
    #-test 
    print 't',t
    print 'v',v
    print 'test verbose\n',
    a= deriveAnomaly(v,t,'additive',MV,True)[0]
    print 'v*', applyAnomaly(a,v,t,'additive',MV,True)[0]
    print 'test verbose multiplicative\n'
    a= deriveAnomaly(v,t,'multiplicative',MV,True)[0]
    print 'v*', applyAnomaly(a,v,t,'multiplicative',MV,True)[0]
    #-test stacked, verbose
    t.shape= (3,3)
    v.shape= (-1,3,3)
    v= np.vstack((v.copy(),v.copy(),v.copy()))
    v[0,0,2]= MV
    v[2,2,0]= MV
    print
    print 't',t
    print 'v',v
    print 'test stacked verbose\n', 
    a= deriveAnomaly(v,t,'additive',MV,True)[0]
    print 'v*', applyAnomaly(a,v,t,'additive',MV,True)[0]
    print 'test stacked multiplicative verbose\n',
    a= deriveAnomaly(v,t,'multiplicative',MV,True)[0]
    print 'v*', applyAnomaly(a,v,t,'multiplicative',MV,True)[0]

    #-test on rainfall and temperature
    #-year to evaluate
    year= 1960          
    nrMonths= 1 #12
    #-paths
    pathCRUArchive= '/home/rens/archive/crutss'
    pathMeteo= '/home/rens/NoBackup/pcrglobwb_test/era40'
    #-cru zip files
    cruZipFileName= 'cru_%s.zip'
    #-dictionary holding meteo data
    meteoVariables= {}
    meteoVariables['rainfall']= {}
    meteoVariables['rainfall']['era40']= 'ra'
    meteoVariables['rainfall']['cru']= 'pre'
    meteoVariables['rainfall']['cruConversion']= 1.e-4
    meteoVariables['temperature']= {}
    meteoVariables['temperature']['era40']= 'ta'
    meteoVariables['temperature']['cru']= 'tmp'
    meteoVariables['temperature']['cruConversion']= 0.1
    meteoVariables['rainoccurrence']= {}
    meteoVariables['rainoccurrence']['era40']= None
    meteoVariables['rainoccurrence']['cru']= 'wet'
    meteoVariables['rainoccurrence']['cruConversion']= 0.01
    #-rainfall threshold (m/day)
    generalRainfallThreshold= 1.e-3
    #-clone map
    cloneMap= '/home/rens/archive/globalmaps/globalclone.map' 
    clone= pcr.readmap(cloneMap)
    nrRows, nrCols= pcr2numpy(clone,int(MV)).shape
    #-iterate over variables and months and fill array holding monthly targets
    cruMonthlyData= {}
    for variable,meteoVariable in meteoVariables.iteritems():
        #-initialize monthly data
        cruMonthlyData[variable]= np.ones((nrMonths,nrRows,nrCols))*MV
        #-open zip with CRU data (target)
        cruTSSZip= zipfile.ZipFile(os.path.join(pathCRUArchive,\
            cruZipFileName % meteoVariable['cru']),'r',zipfile.ZIP_DEFLATED)
        #-fill array
        for month in xrange(1,nrMonths+1):
            #-set month counter
            mCnt= month-1
            print 'processing CRU %s for month %d' % (variable,month)
            #-read in cru data
            fileName= 'c%s%04d.%03d' % (meteoVariable['cru'],year,month)
            if fileName in cruTSSZip.namelist():
                arcName= fileName
                cf= open(fileName,'wb')
                cf.write(cruTSSZip.read(arcName))
                cf.close()
                cruMonthlyData[variable][mCnt,:,:]=\
                    pcr2numpy(pcr.readmap(fileName),MV)
                MV= cruMonthlyData[variable][mCnt,0,0]
                mask= cruMonthlyData[variable][mCnt,:,:] <> MV
                cruMonthlyData[variable][mCnt,:,:][mask]*= meteoVariable['cruConversion']
                os.remove(fileName)
            else:
                sys.exit('%s not found' % fileName)            
        #-close zip
        cruTSSZip.close()    

    #-remove wet days from dictionary
    del meteoVariables['rainoccurrence']

    #-anomalies
    #-read in temperature and rainfall
    #-initialize start day
    startDay= 1
    #-iterate over months
    for month in xrange(1,nrMonths+1):
        #-set month counter end day
        mCnt= month-1
        endDay= startDay+calendar.monthrange(year,month)[1]
        #-get mask
        mask= cruMonthlyData[variable][mCnt,:,:] <> MV
        #-create empty array of daily values
        dailyValues= {}
        for variable,meteoVariable in meteoVariables.iteritems():
            dailyValues[variable]= np.ones((endDay-startDay,nrRows,nrCols))*MV            
            #-iterate over days
            for day in xrange(startDay,endDay):
                #-read in daily data
                iCnt= day-startDay
                fileName= os.path.join(pathMeteo,generateNameT(meteoVariable['era40'],day))
                dailyValues[variable][iCnt,:,:]= pcr2numpy(pcr.readmap(fileName),MV)
                dailyValues[variable][iCnt,:,:][mask == False]= MV
        #-anomaly: temperature
        # use an additive anomaly to change daily temperatures to conform reported monthly mean from CRU
        variable= 'temperature'
        print 'apply temperature anomaly verbose'
        anomaly= deriveAnomaly(dailyValues[variable],\
            cruMonthlyData[variable][mCnt,:,:],'additive',MV,True)[0]
        dailyValues[variable]= applyAnomaly(anomaly,\
            dailyValues[variable],cruMonthlyData[variable][mCnt,:,:],'additive',MV,True)[0]
        #-set mask and report
        mask= (cruMonthlyData[variable][mCnt,:,:] <> MV) &\
            np.all(dailyValues[variable] <> MV, axis= 0)
        cruMonthlyData[variable][mCnt,:,:][mask == False]= MV
        pcr.report(numpy2pcr(pcr.Scalar,cruMonthlyData[variable][mCnt,:,:],MV),'target%s.map' % variable)
        pcr.report(numpy2pcr(pcr.Scalar,anomaly,MV),'anomaly%s.map' % variable)
        value= dailyValues[variable].mean(axis= 0)
        value[mask == False]= MV
        pcr.report(numpy2pcr(pcr.Scalar,value,MV),'modified%s.map' % variable)
        #-anomaly: precipitation
        # use a multiplicative anomaly to change daily rainfall to conform reported monthly sum from CRU
        # to select the correct number of days, a noise series is generated in which rainfall depths
        # are proportional to decreasing temperature in the month and the simulated daily total
        # this noise is then used to select the days with the largest rainfall depths that conform in number with
        # the reported number of rain days from the CRU; note that this is done by taking the inverse of dry days
        # as noise levels are sorted in ascending order
        variable= 'rainfall'
        #-get the original rain sum
        mask= np.all(dailyValues[variable] == MV, axis= 0)
        originalRainSum= dailyValues[variable].sum(axis= 0)
        originalRainSum[mask]= MV
        #-get the integer number of rain days and dry days; if there is rain there is at least one rain day
        nrDays= endDay-startDay
        mask= cruMonthlyData['rainoccurrence'][mCnt,:,:] <> MV
        rainDays= cruMonthlyData['rainoccurrence'][mCnt,:,:].round()
        rainDays[(cruMonthlyData['rainfall'][mCnt,:,:] > 0.) &\
            (rainDays == 0)]= 1
        rainDays[mask == False]= MV
        dryDays= nrDays-rainDays
        dryDays[mask == False]= MV
        #-create noise from daily temperature and rainfall values 
        # to select days with precipitation on the basis of reported occurrence
        #-note that this can be done on daily values directly, thus reducing memory use
        mask= dailyValues['temperature'] <> MV
        noise= dailyValues['temperature']
        scaleFactor= np.maximum(1.e-3,noise.max(axis= 0)-noise.min(axis= 0)) 
        noise-= noise.min(axis= 0)
        noise/= scaleFactor
        noise= (1.-noise)*1.e-3
        seed=np.random.random(size= noise.size)*1.e-4
        seed.shape= noise.shape
        noise+= seed
        noise+= dailyValues[variable]
        noise[mask == False]= 0.
        #~ for iCnt in xrange(noise.shape[0]):
            #~ pcr.report(numpy2pcr(pcr.Scalar,noise[iCnt,:,:],MV),\
                #~ generateNameT('noise',iCnt+1))
        #-find threshold for rainfall occurrence
        rainfallThreshold= deriveOccurrenceThreshold(noise,dryDays,MV)
        noRainOccurrence= applyOccurrenceThreshold(noise,rainfallThreshold,MV)
        #-set noise levels to zero on non-raindays        
        mask= dailyValues[variable] <> MV
        noise[noRainOccurrence]= 0.
        noise[mask == False]= MV
        #-test rain depths to agree with the overall sum
        # note that the test on the values is done separately by means of an
        # additive anomaly as the correction is done on the sums and the number
        # of raindays is different; note that the noise levels are not updated as
        # they hold seeds for possible occurrence
        print 'test rainfall totals after selecting raindays to original values with zero values masked out'
        #-target value -original ERA-40 month sum- with zero rain occurrences in CRU masked out as
        # these have been set to no rain occurrence in the seeds 
        targetValue= originalRainSum.copy()
        targetValue[(targetValue > 0) & (cruMonthlyData[variable][mCnt,:,:] == 0)]= MV
        #-rainfall sum from the seeds
        mask= np.all(dailyValues[variable] <> MV, axis= 0)
        originalValue= noise.sum(axis= 0)
        originalValue[mask == False]= MV
        #-multiplicative anomaly, where divisions by zero occur, zeroes are substituted
        anomaly= deriveAnomaly(originalValue,targetValue,'multiplicative',MV,True)[0]
        anomaly[(targetValue <> MV) & (anomaly == MV)]= 0.
        #-apply anomaly on the basis of noise and add to daily values (noise is kept as it holds possible seeds)
        # sums of the daily values are masked out to avoid mismatch
        dailyValues[variable]= applyAnomaly(anomaly,\
            noise,targetValue,'multiplicative',MV)[0]
        originalValue= dailyValues[variable].sum(axis= 0)
        originalValue[targetValue == MV]= MV
        anomaly= deriveAnomaly(originalValue,targetValue,'additive',MV)[0]
        applyAnomaly(anomaly,originalValue,targetValue,'additive',MV,True)
        #-check on number of rain days
        print 'check number of rain days'
        mask= np.all(noise <> MV, axis= 0)
        originalValue = (noise > 0).astype(float).sum(axis= 0)
        originalValue[mask == False]= MV
        targetValue= rainDays
        anomaly= deriveAnomaly(originalValue,targetValue,'additive',MV,True)[0]
        pcr.report(numpy2pcr(pcr.Scalar,anomaly,MV),'anomaly%s.map' % 'rainoccurrence')        
        pcr.report(numpy2pcr(pcr.Scalar,targetValue,MV),'target%s.map' % 'rainoccurrence')
        pcr.report(numpy2pcr(pcr.Scalar,originalValue,MV),'modified%s.map' % 'rainoccurrence')
        #-correct rainfall depths using a multiplicative anomaly to the target value (CRU)
        print 'correct rainfall depths'
        dailyValues[variable]= noise.copy()
        del noise
        mask= (cruMonthlyData[variable][mCnt,:,:] <> MV) &\
            np.all(dailyValues[variable] <> MV, axis= 0)
        originalValue= dailyValues[variable].sum(axis= 0)
        originalValue[mask == False]= MV
        pcr.report(numpy2pcr(pcr.Scalar,originalValue,MV),'original%s.map' % variable)
        anomaly= deriveAnomaly(originalValue,\
            cruMonthlyData[variable][mCnt,:,:],'multiplicative',MV,True)[0]
        anomaly[(cruMonthlyData[variable][mCnt,:,:] <> MV) & (anomaly == MV)]= 0.
        dailyValues[variable]= applyAnomaly(anomaly,\
            dailyValues[variable],cruMonthlyData[variable][mCnt,:,:],'multiplicative',MV)[0]
        #-set mask and report
        mask= (cruMonthlyData[variable][mCnt,:,:] <> MV) &\
            np.all(dailyValues[variable] <> MV, axis= 0)
        pcr.report(numpy2pcr(pcr.Scalar,anomaly,MV),'anomaly%s.map' % variable)
        pcr.report(numpy2pcr(pcr.Scalar,cruMonthlyData[variable][mCnt,:,:],MV),'target%s.map' % variable)
        originalValue= dailyValues[variable].sum(axis= 0)
        originalValue[mask == False]= MV
        anomaly= deriveAnomaly(originalValue,cruMonthlyData[variable][mCnt,:,:],'additive',MV)[0]
        applyAnomaly(anomaly,originalValue,cruMonthlyData[variable][mCnt,:,:],'additive',MV,True)
        pcr.report(numpy2pcr(pcr.Scalar,originalValue,MV),'modified%s.map' % variable)
        #-update start day
        startDay= endDay        
        
if __name__ == '__main__':
    #-execute default function
    main()
