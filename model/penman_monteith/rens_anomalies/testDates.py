import calendar, datetime
import ncRecipes as rvb_ncR

# - get dates

ncFileName = '/data/hydroworld/basedata/forcing/CRU-TS3.21/data/tmp/cru_ts3.21.tmp.dat.nc'
ncFileFormat, ncAttributes, ncDimensions, ncVariables = rvb_ncR.getNCAttributes(ncFileName)

cruDates = rvb_ncR.getNCDates(ncDimensions['time'],ncVariables['time'], verbose= False)
print cruDates
for year in xrange(1901,2000):
	for month in xrange(1,13):
		numberDays   = calendar.monthrange(year,month)[1]
		midMonthDate = datetime.datetime(year,month,int(0.5*numberDays+0.5))
		posCnt = rvb_ncR.getNCDateIndex(midMonthDate,cruDates,'nearest')
		print midMonthDate, posCnt, cruDates[posCnt]

#~ # - get corresponding match from cruDates
#~ 
