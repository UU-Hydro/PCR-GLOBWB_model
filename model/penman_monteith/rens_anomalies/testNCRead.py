import datetime
import zlib
import numpy as np
import logging

import ncRecipes as rvb_ncR

ncFile= '/data/hydroworld/forcing/ERA20C/RawData/tavg1900.nc' 

ncFileFormat,ncAttributes, ncDimensions, ncVariables= rvb_ncR.getNCAttributes(ncFile)
ncDates= rvb_ncR.getNCDates(ncDimensions['time'],ncVariables['time'])

for dayCnt in xrange(365):
		date= datetime.datetime(1900,1,1,9)+datetime.timedelta(dayCnt)
		posCnt= rvb_ncR.getNCDateIndex(date,ncDates)
		print date, posCnt, np.mean(rvb_ncR.readField(ncFile,'var167',posCnt))
	
