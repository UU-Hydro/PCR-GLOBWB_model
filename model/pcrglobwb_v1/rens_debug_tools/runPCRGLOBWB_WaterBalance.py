import os

rootDir= '/scratch/rens/debug30min/RhineMeuse_2.0/'
modelFileName= '/home/beek0120/PCRGLOBWB/PCRGLOBWB_V1.0//pcr-glob_waterbalance_v1.0.txt'

command= 'oldcalc -d temp.map -f "%s"' % modelFileName

os.chdir(rootDir)

mapEntries= {}
for key in xrange(1,103):
	mapEntries['$%d' % key]= 'DUMMY'

mapEntries['$1']= '365'
mapEntries['$2']= '1'
mapEntries['$3']= 'maps/catclone.map'
mapEntries['$4']= 'maps/cellarea30.map'
mapEntries['$5']= 'maps/lddsound_30min.map'
mapEntries['$6']= 'maps/glwd130m_fracw.map'
mapEntries['$7']= 'maps/kc_wat'
mapEntries['$8']= 'maps/globalalpha.map'
mapEntries['$9']= 'maps/specificyield.map'
mapEntries['$10']= '5.0'

mapEntries['$11']= 'meteo/ra'
mapEntries['$12']= '0.0'
mapEntries['$13']= '1.0'

mapEntries['$14']= 'MULCONST.001'
mapEntries['$15']= '0.0'
mapEntries['$16']= '1.0'

mapEntries['$17']= 'meteo/ta'
mapEntries['$18']= '0.0'
mapEntries['$19']= '1.0'

mapEntries['$20']= 'ADDCONST.001'
mapEntries['$21']= '1.0'
mapEntries['$22']= '0.0'

mapEntries['$23']= 'meteo/epot'
mapEntries['$24']= '0.0'
mapEntries['$25']= '1.0'
mapEntries['$26']= 'MULCONST.001'
mapEntries['$27']= '0.0'
mapEntries['$28']= '1.0'

mapEntries['$31']= 'short'
mapEntries['$32']= 'tall'

mapEntries['$41']= 'sv'
mapEntries['$42']= 'tv'

mapEntries['$51']= 'maps/cv_t'
mapEntries['$52']= 'maps/cv_t'

mapEntries['$61']= 'maps/cv_t'
mapEntries['$62']= 'maps/cv_t'

mapEntries['$71']= 'maps/cv_t'
mapEntries['$72']= 'maps/cv_t'

mapEntries['$81']= 'maps/param_test.tbl'

mapEntries['$82']= 'results/stor3x00.ini'

mapEntries['$89']= 'results'

mapEntries['$91']= 'maps\hydro1k_dzrel0001.map'
mapEntries['$92']= 'maps\hydro1k_dzrel0005.map'
mapEntries['$93']= 'maps\hydro1k_dzrel0010.map'
mapEntries['$94']= 'maps\hydro1k_dzrel0020.map'
mapEntries['$95']= 'maps\hydro1k_dzrel0030.map'
mapEntries['$96']= 'maps\hydro1k_dzrel0040.map'
mapEntries['$97']= 'maps\hydro1k_dzrel0050.map'
mapEntries['$98']= 'maps\hydro1k_dzrel0060.map'
mapEntries['$99']= 'maps\hydro1k_dzrel0070.map'
mapEntries['$100']= 'maps\hydro1k_dzrel0080.map'
mapEntries['$101']= 'maps\hydro1k_dzrel0090.map'
mapEntries['$102']= 'maps\hydro1k_dzrel0100.map'

for key in xrange(1,len(mapEntries.keys())+1):
	mapEntry= mapEntries['$%d' % key]
	#-check if it is a float
	try:
		float(mapEntry)
	except:
		if '/'in mapEntry:
			mapEntry= os.path.join(rootDir,mapEntry)
			mapEntry= mapEntry.replace('/','\\')
		mapEntry= '"%s"' % mapEntry
	command+= ' %s' % mapEntry
print command
os.system(command)
