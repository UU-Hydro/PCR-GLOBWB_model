import os

modelSignature= 'ipsl_cm5a_lr_2p6' #'noresm1_m_2p6' #'miroc_esm_chem_2p6'
modelSignatureAlt= 'ipsl_cm5a_lr_2p6' #'noresm1_m_2p6'#'miroc-esm-chem_2p6'
inputFolder1= '/storagetemp/rens/%s/netcdf' % modelSignature
dates= ['2006-01-01','2086-12-31']
inputFolder2= '/scratch/rens/%s/netcdf'  % modelSignatureAlt
outputFolder= '/storagetemp/rens/%s'  % modelSignature
commandStr= 'cdo mergetime %s %s %s'
fileNames= ['baseflow_dailyTot_output.nc','interflowTotal_dailyTot_output.nc',\
	'referencePotET_dailyTot_output.nc','directRunoff_dailyTot_output.nc']
	
for fileName in fileNames:
	iFile1= os.path.join(inputFolder1,fileName)
	iFile2= os.path.join(inputFolder2,fileName)	
	oFile= os.path.join(outputFolder,fileName)
	command= commandStr % (iFile1,iFile2,oFile)
	print'\n%s\n' % command
	os.system(command)
command= 'cdo showdate %s'% oFile
os.system(command)
