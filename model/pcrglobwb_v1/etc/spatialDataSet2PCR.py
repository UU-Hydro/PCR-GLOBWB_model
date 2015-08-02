import os, sys, tempfile, shutil
import subprocess
import PCRaster as pcr

class spatialDataSet:

  def __init__(self,sourceFileName,variable,x0,y0,x1,y1,dx,dy,\
		resampleRatio= 1.0, attribute= None)
	'''Initializes the information on a spatial dataset and\
 stores the spatial extent and resolution for a regular grid of interest.\
 The dataset can return a numpy object or convert it to an output file. '''
  
  
  #~ variable,typeStr,outputFormat,\
        #~ x0,y0,x1,y1,dx,dy,resampleRatio= 1.,attribute= None):
			#~ 
			
			
    #-requires as input ...
    #-read in the source file name and decide on processing
    tempFileName= os.path.split(fileName)[1].lower()
    tempFileName= 'temp_%s' % os.path.splitext(tempFileName)[0]
    #-set output format
    outputFormat= 'PCRASTER_VALUESCALE=VS_%s' % outputFormat.upper()
    if '.shp' in fileName:
      #-shape file: create empty geotiff and rasterize prior to further processing
      shutil.copy('empty.tif','%s.tif' % tempFileName)
      co= 'gdal_rasterize -a %s -l %s %s %s.tif' %\
          (attribute,os.path.split(fileName)[1].replace('.shp',''),fileName,tempFileName)
      subprocess.call(co,stdout= subprocess.PIPE,stderr= subprocess.PIPE,shell= True)
      fileName= '%s.tif' % tempFileName
    #-process grid
    co= 'gdal_translate -ot %s -of PCRaster -mo %s %s %s.map -projwin %f %f %f %f -outsize %s %s -quiet' %\
        (typeStr,outputFormat,fileName,tempFileName,\
          x0,y1,x1,y0,'%.3f%s' % (100.*resampleRatio,'%'),'%.3f%s' % (100.*resampleRatio,'%'))
    subprocess.call(co,stdout= subprocess.PIPE,stderr= subprocess.PIPE,shell= True)
    #-read resulting map
    setattr(self,variable,pcr.readmap('%s.map' % tempFileName))
    for suffix in ['map','tif']:
      try:
        os.remove('%s.%s' %(tempFileName,suffix))
        os.remove('%s.%s.aux.xml' %(tempFileName,suffix))
      except:
          pass
