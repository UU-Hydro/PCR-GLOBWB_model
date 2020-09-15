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
    # - using the clone with 1400 rows
    global_clone_map = "/scratch/mo/nest/ulysses/data/edwin/clone_maps/version_2020-09-XX/clone_all_maps/clone_ulysses_06min_global_with_1400_rows.map"
    # ~ # - using the clone with 1800 rows
    # ~ global_clone_map = "/scratch/mo/nest/ulysses/data/edwin/clone_maps/version_2020-09-XX/clone_all_maps/clone_ulysses_06min_global_with_1800_rows.map"

    # number of subdomain masks
    num_of_masks = 54

    # list of subdomain mask files for land (all in nc files)
    subdomain_land_nc        = "/scratch/mo/nest/ulysses/data/subdomain_masks/subdomain_land_%s.nc"

    # list of subdomain maks files for routing (all in nc files)
    subdomain_river_nc       = "/scratch/mo/nest/ulysses/data/subdomain_river_masks/subdomain_river_network_%s.nc"	
    
    # list of 5 arcmin pcrglobwb clone maps
    pcrglobwb_5min_clone_map = "/scratch/mo/nest/ulysses/data/edwin/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_05min/cloneMaps/global_parallelization/clone_M%02d.map" 
    
    # output folder (and tmp folder)
    out_folder   = "/scratch/mo/nest/ulysses/data/edwin/clone_maps/version_2020-09-XX/pcraster_maps/"
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
    
    # clone code that will be assigned
    assigned_number = 0
    
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
        
        # read river nc file (and convert it to pcraster)
        subdomain_river_nc_file = subdomain_river_nc %(str(nr))
        mask_river_selected = vos.netcdf2PCRobjCloneWithoutTime(ncFile  = subdomain_river_nc_file, \
                                                                varName = "lsmask",\
                                                                cloneMapFileName  = global_clone_map,\
                                                                LatitudeLongitude = True,\
                                                                specificFillValue = "NaN",\
                                                                absolutePath = None)
        mask_river_selected_boolean = pcr.ifthen(pcr.scalar(mask_river_selected) > 0.0, pcr.boolean(1.0))
        mask_river_selected_boolean = pcr.ifthen(mask_river_selected_boolean, mask_river_selected_boolean)
        
        # merge land and river landmask
        mask_selected_boolean = pcr.cover(mask_land_selected_boolean, mask_river_selected_boolean)
        
        # get the bounding box based on the landmask
        xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean)
        area_in_degree2 = (xmax - xmin) * (ymax - ymin)
        
        # check whether the size of bounding box is the same as the one based on the 5 arcmin PCR-GLOBWB clone maps
        # - initial check value
        check_ok = True
        # - no check for nr 54 as there is no pcrglobwb clone nr 53
        if nr < 54:
        
            pcrglobwb_5min_clone_map_file = pcrglobwb_5min_clone_map %(nr) 
            reference_mapattr = vos.getMapAttributesALL(pcrglobwb_5min_clone_map_file)
            reference_xmin = reference_mapattr["xUL"]
            reference_xmax = reference_mapattr["cellsize"]*reference_mapattr["cols"] + reference_xmin
            reference_ymax = reference_mapattr["yUL"]
            reference_ymin = reference_ymax - reference_mapattr["cellsize"]*reference_mapattr["rows"]
            reference_area_in_degree2 = (xmax - xmin) * (ymax - ymin)
            
            if size > 1.50 * reference_size: check_ok = False
        
        if check_ok == True:
        
            # make sure that it is set to the global clone map
            pcr.setclone(global_clone_map)

            # get the bounding box based on the landmask file
            xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean)
            
            # cellsize 
            cellsize = vos.getMapAttributes(global_clone_map, "cellsize")
            num_rows = int(round(ymax - ymin) / cellsize)
            num_cols = int(round(xmax - xmin) / cellsize)
            
            # assign the clone code
            assigned_number = assigned_number + 1

            # make the clone map using mapattr 
            clonemap_mask_file = "clonemap_mask_%s.map" %(str(nr))
            cmd = "mapattr -s -R %s -C %s -B -P yb2t -x %s -y %s -l %s %s" %(str(num_rows), str(num_cols), str(xmin), str(ymax), str(cellsize), clonemap_mask_file)
            print(cmd); os.system(cmd)
            
            # make also a clone map with the file name using nr and assigned_number
            clonemap_mask_long_file_name = "clonemap_with_longname_mask_%s_%s.map" %(str(nr), str(assigned_number))
            cmd = "cp %s %s" %(str(clonemap_mask_file), str(clonemap_mask_long_file_name))
            
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

            # update global landmasks
            pcr.setclone(global_clone_map)
            # - for land
            landmask_land_all = pcr.cover(landmask_land_all, landmask_land)
            # - for river and land
            landmask_river_and_land_all = pcr.cover(landmask_river_and_land_all, landmask_river_and_land)
            pcr.aguila(landmask_river_and_land_all)
    
        if check_ok == False:
			
            # make clump
            clump_ids    = pcr.nominal(pcr.clump(mask_selected_boolean))
            
            # minimimum and maximum values
            min_clump_id = pcr.cellvalue(pcr.mapminimum(mapFile),1)[0]
            max_clump_id = pcr.cellvalue(pcr.mapmaximum(mapFile),1)[0]
           
            for clump_id in range(min_clump_id, max_clump_id, 1):
            
                msg = "Processing the clump %s of %s from the ulysses landmask %s" %(str(clump_id), str(max_clump_id), str(nr))
                msg = "\n\n" +str(msg) + "\n\n"
                print(msg)

                mask_selected_boolean_from_clump = pcr.ifthen(clump_ids == pcr.nominal(clump_id), mask_selected_boolean)
                
                # get the bounding box based on the landmask file
                xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean_from_clump)
                
                # cellsize 
                cellsize = vos.getMapAttributes(global_clone_map, "cellsize")
                num_rows = int(round(ymax - ymin) / cellsize)
                num_cols = int(round(xmax - xmin) / cellsize)
                
                # assign the clone code
                assigned_number = assigned_number + 1
			    
                # make the clone map using mapattr 
                clonemap_mask_file = "clonemap_mask_%s.map" %(str(nr))
                cmd = "mapattr -s -R %s -C %s -B -P yb2t -x %s -y %s -l %s %s" %(str(num_rows), str(num_cols), str(xmin), str(ymax), str(cellsize), clonemap_mask_file)
                print(cmd); os.system(cmd)
                
                # make also a clone map with the file name using nr and assigned_number
                clonemap_mask_long_file_name = "clonemap_with_longname_mask_%s_%s.map" %(str(nr), str(assigned_number))
                cmd = "cp %s %s" %(str(clonemap_mask_file), str(clonemap_mask_long_file_name))
                
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
			    
                # update global landmasks
                pcr.setclone(global_clone_map)
                # - for land
                landmask_land_all = pcr.cover(landmask_land_all, landmask_land)
                # - for river and land
                landmask_river_and_land_all = pcr.cover(landmask_river_and_land_all, landmask_river_and_land)
                pcr.aguila(landmask_river_and_land_all)

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

