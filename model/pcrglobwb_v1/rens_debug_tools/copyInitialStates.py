import os, shutil

inputPath= '/scratch/rens/debug30min/RhineMeuse_2.0/initialStates'
outputPath= '/scratch/rens/debug30min/RhineMeuse_2.0/results'
initialFiles= {'ints_sv0.ini': 'interceptStor_grassland_2000-12-31.map',\
	'ints_tv0.ini': 'interceptStor_forest_2000-12-31.map',\
	'q2_sv000.ini': 'interflow_grassland_2000-12-31.map',\
	'q2_tv000.ini': 'interflow_forest_2000-12-31.map',\
	's1_sv000.ini': 'storUpp_grassland_2000-12-31.map',\
	's1_tv000.ini': 'storUpp_forest_2000-12-31.map',\
	's2_sv000.ini': 'storLow_grassland_2000-12-31.map',\
	's2_tv000.ini': 'storLow_forest_2000-12-31.map',\
	'scf_sv00.ini': 'snowFreeWater_grassland_2000-12-31.map',\
	'scf_tv00.ini': 'snowFreeWater_forest_2000-12-31.map',\
	'sc_sv000.ini': 'snowCoverSWE_grassland_2000-12-31.map',\
	'sc_tv000.ini': 'snowCoverSWE_forest_2000-12-31.map',\
	'stor3x00.ini': 'storGroundwater_2000-12-31.map'}

for oFile, iFile in initialFiles.iteritems():
	shutil.copy(os.path.join(inputPath,iFile),\
		os.path.join(outputPath,oFile))
	print '%s -> %s copied' % (iFile, oFile)
