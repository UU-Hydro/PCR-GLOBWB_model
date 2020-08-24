#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function

import os
import sys
import glob
import subprocess
import time
import datetime
import shutil

import numpy as np
import math

import pcraster as pcr
import virtualOS as vos

def boundingBox(pcrmap):
    ''' derive the bounding box for a map, return xmin,ymin,xmax,ymax '''
    bb = []
    xcoor = pcr.xcoordinate(pcrmap)
    ycoor = pcr.ycoordinate(pcrmap)
    xmin  = pcr.cellvalue(pcr.mapminimum(xcoor), 1, 1)[0]
    xmax  = pcr.cellvalue(pcr.mapmaximum(xcoor), 1, 1)[0]
    ymin  = pcr.cellvalue(pcr.mapminimum(ycoor), 1, 1)[0]
    ymax  = pcr.cellvalue(pcr.mapmaximum(ycoor), 1, 1)[0]
    return [math.floor(xmin), math.floor(ymin), math.ceil(xmax), math.ceil(ymax)]
    
def main():

    # global map of subdomain masks
    global_clone_map = "/scratch/mo/nest/ulysses/data/edwin/clone_maps/version_2020-08-04/clone_all_maps/clone_ulysses_06min_global.map"

    # number of subdomain masks
    num_of_masks = 54

    # list of subdomain mask files for land (all in nc files)
    subdomain_land_nc  = "/scratch/mo/nest/ulysses/data/subdomain_masks/subdomain_land_%s.nc"

    # lisk of subdomain maks files for touring (all in nc files)
    subdomain_river_nc = "/scratch/mo/nest/ulysses/data/subdomain_river_masks/subdomain_river_%s.nc"	
    
    # output folder (and tmp folder)
    out_folder   = "/scratch/mo/nest/ulysses/data/edwin/clone_maps/version_2020-08-04/pcraster_maps/"
    clean_out_folder = True
    if os.path.exists(out_folder): 
        if clean_out_folder:
            shutil.rmtree(out_folder)
            os.makedirs(out_folder)
    else:
        os.makedirs(out_folder)
    os.chdir(out_folder)    
    os.system("pwd")
    
    # make tmp folder
    tmp_folder = os.path.join(out_folder, "tmp_clone_uly") + "/"
    if os.path.exists(tmp_folder): shutil.rmtree(tmp_folder) 
    os.makedirs(tmp_folder)
    
    # make initial landmask maps at the global extent
    # - set to the global clone map
    pcr.setclone(global_clone_map)
    # - for land
    landmask_land_all = pcr.ifthen(pcr.scalar(global_clone_map) > 10, pcr.nominal(0))
    # - for river
    landmask_river_and_land_all = pcr.ifthen(pcr.scalar(global_clone_map) > 10, pcr.nominal(0))
    
    for nr in range(1, num_of_masks + 1, 1):
        
        msg = "Processing the landmask %s" %(str(nr))
        msg = "\n\n" +str(msg) + "\n\n"
        print(msg)
        
        # set to the global clone map
        pcr.setclone(global_clone_map)
        
        # read land nc file (and convert it to pcraster)
        subdomain_land_nc_file = subdomain_land_nc %(str(nr))
        mask_land_selected = vos.netcdf2PCRobjCloneWithoutTime(ncFile  = subdomain_land_nc_file, \
                                                               varName = "mask",\
                                                               cloneMapFileName  = global_clone_map,\
                                                               LatitudeLongitude = True,\
                                                               specificFillValue = "NaN",\
                                                               absolutePath = None)
        mask_land_selected_boolean = pcr.ifthen(pcr.scalar(mask_land_selected) > 0.0, pcr.boolean(1.0))
        mask_land_selected_boolean = pcr.ifthen(mask_land_selected_boolean, mask_land_selected_boolean)
        
        # update global landmask for land
        mask_land_selected_nominal = pcr.ifthen(mask_land_selected_boolean, pcr.nominal(nr))
        landmask_land_all = pcr.cover(landmask_land_all, mask_land_selected_nominal)
        # ~ pcr.aguila(landmask_land_all)

        # read river nc file (and convert it to pcraster)
        subdomain_river_nc_file = subdomain_river_nc %(str(nr))
        mask_river_selected = vos.netcdf2PCRobjCloneWithoutTime(ncFile  = subdomain_river_nc_file, \
                                                                varName = "mask",\
                                                                cloneMapFileName  = global_clone_map,\
                                                                LatitudeLongitude = True,\
                                                                specificFillValue = "NaN",\
                                                                absolutePath = None)
        mask_river_selected_boolean = pcr.ifthen(pcr.scalar(mask_river_selected) > 0.0, pcr.boolean(1.0))
        mask_river_selected_boolean = pcr.ifthen(mask_river_selected_boolean, mask_river_selected_boolean)
        
        
        # merge land and river landmask
        mask_selected_boolean = pcr.cover(mask_land_selected_boolean, mask_river_selected_boolean)
        mask_selected_nominal = pcr.ifthen(mask_selected_boolean, pcr.nominal(nr)) 
        # ~ pcr.aguila(mask_selected_nominal)
        filename_for_land_river_mask_at_global_extent = "global_landmask_river_and_land_mask_%s.map" %(str(nr)) 
        filename_for_land_river_mask_at_global_extent = os.path.join(out_folder, filename_for_land_river_mask_at_global_extent)
        pcr.report(mask_selected_nominal, filename_for_land_river_mask_at_global_extent)
        
        # update global landmask for land and river
        landmask_river_and_land_all = pcr.cover(landmask_river_and_land_all, mask_selected_nominal)
        # ~ pcr.aguila(landmask_river_and_land_all)

        # get the bounding box based on the landmask file
        xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean)
        
        # cellsize 
        cellsize = vos.getMapAttributes(global_clone_map, "cellsize")
        num_rows = int(round(ymax - ymin) / cellsize)
        num_cols = int(round(xmax - xmin) / cellsize)
        
        # make the clone map using mapattr 
        clonemap_mask_file = "clonemap_mask_%s.map" %(str(nr))
        # - example: mapattr -s -R 19 -C 68 -B -P yb2t -x 12 -y -14.02 -l 0.8 mask2.map
        cmd = "mapattr -s -R %s -C %s -B -P yb2t -x %s -y %s -l %s %s" %(str(num_rows), str(num_cols), str(xmin), str(ymax), str(cellsize), clonemap_mask_file)
        print(cmd)
        os.system(cmd)
        
        # set the landmask for land
        pcr.setclone(clonemap_mask_file)
        landmask_land = vos.netcdf2PCRobjCloneWithoutTime(ncFile  = subdomain_land_nc_file, \
                                                          varName = "mask",\
                                                          cloneMapFileName  = clonemap_mask_file,\
                                                          LatitudeLongitude = True,\
                                                          specificFillValue = "NaN",\
                                                          absolutePath = None)
        landmask_land_boolean = pcr.ifthen(pcr.scalar(landmask_land) > 0.0, pcr.boolean(1.0))
        landmask_land_boolean = pcr.ifthen(landmask_land_boolean, landmask_land_boolean)
        # - save the landmask for land (used for PCR-GLOBWB reporting)
        landmask_land_file = "landmask_land_mask_%s.map" %(str(nr))
        pcr.report(landmask_land_boolean, landmask_land_file)
        
        # set the landmask for river and land
        landmask_river_and_land = vos.readPCRmapClone(v = filename_for_land_river_mask_at_global_extent, \
                                                      cloneMapFileName = clonemap_mask_file, 
                                                      tmpDir = tmp_folder, \
                                                      absolutePath = None, isLddMap = False, cover = None, isNomMap = True)
        landmask_river_and_land_boolean = pcr.ifthen(pcr.scalar(landmask_river_and_land) > 0.0, pcr.boolean(1.0))
        landmask_river_and_land_boolean = pcr.ifthen(landmask_river_and_land_boolean, landmask_river_and_land_boolean)
        landmask_river_and_land_file = "landmask_river_and_land_mask_%s.map" %(str(nr))
        pcr.report(landmask_river_and_land_boolean, landmask_river_and_land_file) 

    
    # kill all aguila processes if exist
    os.system('killall aguila')


    # report a global nominal map for land
    pcr.setclone(global_clone_map)
    filename_for_nominal_land_mask_at_global_extent = "global_landmask_land_mask_all.map"
    pcr.report(landmask_land_all, filename_for_nominal_land_mask_at_global_extent)
    pcr.aguila(landmask_land_all)

    # report a global nominal map for river and and land
    pcr.setclone(global_clone_map)
    filename_for_nominal_land_river_mask_at_global_extent = "global_landmask_river_and_land_mask_all.map"
    pcr.report(landmask_river_and_land_all, filename_for_nominal_land_river_mask_at_global_extent)
    pcr.aguila(landmask_river_and_land_all)
    
    print("\n\n Done \n\n")
    
        
if __name__ == '__main__':
    sys.exit(main())

