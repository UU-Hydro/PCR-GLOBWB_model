#-renames the catchment map
import numpy as np
import pcraster as pcr

originalCatchments= 'catchments.map'
rescaledCatchmentsTBL= 'catchments.tbl'
rescaledCatchments= 'catchments_scalar.map'


catchments= pcr.readmap(originalCatchments)
catchmentIDs= np.unique(pcr.pcr2numpy(catchments,-999))
catchmentIDs= catchmentIDs[catchmentIDs != -999]
copyIDs= catchmentIDs.copy()
np.random.shuffle(copyIDs)

txtFile= open(rescaledCatchmentsTBL,'w')
for iCnt in xrange(catchmentIDs.size):
	txtFile.write('%d %d\n' % (catchmentIDs[iCnt],copyIDs[iCnt]))
txtFile.close()

pcr.setglobaloption('large')

copyCatchments= pcr.lookupscalar(rescaledCatchmentsTBL,catchments)
pcr.report(copyCatchments,rescaledCatchments)
