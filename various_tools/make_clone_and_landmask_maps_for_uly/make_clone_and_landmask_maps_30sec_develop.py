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
    global_clone_map = "/scratch/depfg/sutan101/data/pcrglobwb_input_arise/develop/global_30sec/cloneMaps/global/global_clone_30sec.map"

    # number of initial subdomain masks (based on 5 arcmin model, gmd paper)
    num_of_masks = 53
    
    # subdomain file (land and inland water: rivers, lakes and reservoirs)
    # ~ # - using a netcdf file - still not working
    # ~ subdomain_nc = "/scratch/depfg/sutan101/making_subdomains/initial_subdomains/subdomain_30sec_areamajority_catchment_lddsound_30sec_version_202005XX_invertlat.nc"
    # - read from a pcraster map
    subdomain_map = "/scratch/depfg/sutan101/making_subdomains/initial_subdomains/subdomain_30sec_areamajority_catchment_lddsound_30sec_version_202005XX.map"

    # list of 5 arcmin pcrglobwb clone maps
    pcrglobwb_5min_clone_map = "/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_05min/cloneMaps/global_parallelization/clone_M%02d.map" 
    
    # output folder (and tmp folder)
    out_folder = "/scratch/depfg/sutan101/making_subdomains/refined_subdomains/pcraster_maps/"
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
    tmp_folder = os.path.join(out_folder, "tmp_clone_30sec") + "/"
    if os.path.exists(tmp_folder): shutil.rmtree(tmp_folder) 
    os.makedirs(tmp_folder)
    
    # read subdomain file - this is the input
    # - set to the global clone map
    pcr.setclone(global_clone_map)
    # ~ # - using a netcdf file - still not working
    # ~ mask_original = vos.netcdf2PCRobjCloneWithoutTime(ncFile = subdomain_nc, \
                                                               # ~ varName = "mask",\
                                                               # ~ cloneMapFileName  = global_clone_map,\
                                                               # ~ LatitudeLongitude = True,\
                                                               # ~ specificFillValue = -2147483647,\
                                                               # ~ absolutePath = None)
    # - using a pcraster map
    mask_original     = pcr.readmap(subdomain_map) 
    pcr.aguila(mask_original)                                                           

    # make initial landmask map at the global extent - this will be used as the output 
    # - set to the global clone map
    pcr.setclone(global_clone_map)
    # - for river and land
    landmask_all = pcr.ifthen(pcr.scalar(global_clone_map) > 10, pcr.nominal(0))
    # - file name (and save this initial map)
    filename_for_nominal_land_river_mask_at_global_extent = "global_landmask_all.map"
    pcr.report(landmask_all, filename_for_nominal_land_river_mask_at_global_extent)
    
    # clone code that will be assigned
    assigned_number = 0
    
    # ~ for nr in range(1, num_of_masks + 1, 1):

    # ~ # - for testing
    # ~ for nr in range(36, 40, 1):

    # ~ # - for testing
    # ~ for nr in range(1, 5 + 1, 1):

    # - for testing
    for nr in range(18, 23 + 1, 1):

        # kill all aguila processes if exist
        os.system('killall aguila')

        msg = "Processing the landmask %s" %(str(nr))
        msg = "\n\n" +str(msg) + "\n\n"
        print(msg)
        
        # set to the global clone map
        pcr.setclone(global_clone_map)
        
        # select the subdomain
        mask_selected = pcr.ifthen(pcr.scalar(mask_original) == float(nr), pcr.boolean(1.0))
        mask_selected_boolean = pcr.ifthen(pcr.scalar(mask_selected) > 0.0, pcr.boolean(1.0))
        mask_selected_boolean = pcr.ifthen(mask_selected_boolean, mask_selected_boolean)
        
        mask_selected_nominal = pcr.ifthen(mask_selected_boolean, pcr.nominal(nr)) 
        # ~ pcr.aguila(mask_selected_nominal)
        #
        # - save it in a global extent file for further processes
        filename_for_land_river_mask_at_global_extent = "global_landmask_%s_original.map" %(str(nr)) 
        filename_for_land_river_mask_at_global_extent = os.path.join(out_folder, filename_for_land_river_mask_at_global_extent)
        pcr.report(mask_selected_nominal, filename_for_land_river_mask_at_global_extent)
        
        # get the bounding box based on the landmask
        xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean)
        area_in_degree2 = (xmax - xmin) * (ymax - ymin)
        
        # check whether the size of bounding box is the same as the one based on the 5 arcmin PCR-GLOBWB clone maps
        # - initial check value
        check_ok = True
        # - no check for nr >= 54 as there are only 53 pcrglobwb clones
        if nr < 54:
        
            pcrglobwb_5min_clone_map_file = pcrglobwb_5min_clone_map %(nr) 
            reference_mapattr = vos.getMapAttributesALL(pcrglobwb_5min_clone_map_file)
            reference_xmin = reference_mapattr["xUL"]
            reference_xmax = reference_mapattr["cellsize"]*reference_mapattr["cols"] + reference_xmin
            reference_ymax = reference_mapattr["yUL"]
            reference_ymin = reference_ymax - reference_mapattr["cellsize"]*reference_mapattr["rows"]
            reference_area_in_degree2 = (reference_xmax - reference_xmin) * (reference_ymax - reference_ymin)
            
            if area_in_degree2 > 1.50 * reference_area_in_degree2: check_ok = False
        
        if check_ok == True:

            msg = "Clump is not needed."
            msg = "\n\n" +str(msg) + "\n\n"
            print(msg)

            # make sure that it is set to the global clone map
            pcr.setclone(global_clone_map)

            # assign the clone code
            assigned_number = assigned_number + 1

            # update global landmask for river and land
            mask_selected_nominal = pcr.ifthen(mask_selected_boolean, pcr.nominal(assigned_number))
            landmask_all = pcr.cover(landmask_all, mask_selected_nominal) 
            pcr.report(landmask_all, filename_for_nominal_land_river_mask_at_global_extent)
            pcr.aguila(landmask_all)

            
            # get the bounding box based on the landmask file
            xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean)
            
            # cellsize 
            cellsize = vos.getMapAttributes(global_clone_map, "cellsize")
            num_rows = int(round(ymax - ymin) / cellsize)
            num_cols = int(round(xmax - xmin) / cellsize)
            
            # make the clone map using mapattr 
            clonemap_mask_file = "clonemap_%s.map" %(str(assigned_number))
            cmd = "mapattr -s -R %s -C %s -B -P yb2t -x %s -y %s -l %s %s" %(str(num_rows), str(num_cols), str(xmin), str(ymax), str(cellsize), clonemap_mask_file)
            print(cmd); os.system(cmd)
            
            # make also a clone map with the file name using nr and assigned_number
            clonemap_mask_long_file_name = "clonemap_with_longname_mask_%s_%s.map" %(str(nr), str(assigned_number))
            cmd = "cp %s %s" %(str(clonemap_mask_file), str(clonemap_mask_long_file_name))
            print(cmd); os.system(cmd)
            
            # set the landmask
            pcr.setclone(clonemap_mask_file)
            landmask_river_and_land = vos.readPCRmapClone(v = filename_for_land_river_mask_at_global_extent, \
                                                          cloneMapFileName = clonemap_mask_file, 
                                                          tmpDir = tmp_folder, \
                                                          absolutePath = None, isLddMap = False, cover = None, isNomMap = True)
            landmask_river_and_land_boolean = pcr.ifthen(pcr.scalar(landmask_river_and_land) > 0.0, pcr.boolean(1.0))
            landmask_river_and_land_boolean = pcr.ifthen(landmask_river_and_land_boolean, landmask_river_and_land_boolean)
            landmask_river_and_land_file = "mask_%s.map" %(str(assigned_number))
            pcr.report(landmask_river_and_land_boolean, landmask_river_and_land_file) 

    
        if check_ok == False:
			
            msg = "Clump is needed."
            msg = "\n\n" +str(msg) + "\n\n"
            print(msg)

            # make clump
            clump_ids = pcr.nominal(pcr.clump(mask_selected_boolean))
            
            # merge clumps that are close together 
            # - not recommended for 30sec 
            merging_clumps = True
            
            if merging_clumps:
                
                print("Merging clumps that are close together.")
                
                print("Window majority operation.")
			    
                # ~ # - ideal for 6 arcmin, i.e. 25/0.1 = 250 cells
                # ~ clump_ids_window_majority = pcr.windowmajority(clump_ids, 25.0)
			    
                # - for 30sec, use 0.75deg, 0.75/(30/3600) = 90 cells
                clump_ids_window_majority = pcr.windowmajority(clump_ids, 0.75)
			    
                # ~ print("Area majority operation.")
                # ~ clump_ids = pcr.areamajority(clump_ids_window_majority, clump_ids) 
			    
                # - for 30arcsec, areaminimum is used as areamajority is too slow.
                print("Area maximum operation.")
                clump_ids = pcr.areamaximum(clump_ids_window_majority, clump_ids) 
			    
                pcr.aguila(clump_ids)
            
            # minimimum and maximum values
            min_clump_id = int(pcr.cellvalue(pcr.mapminimum(pcr.scalar(clump_ids)),1)[0])
            max_clump_id = int(pcr.cellvalue(pcr.mapmaximum(pcr.scalar(clump_ids)),1)[0])

            # ~ test
            
            for clump_id in range(min_clump_id, max_clump_id + 1, 1):
            
                msg = "Processing the clump %s of %s from the landmask %s" %(str(clump_id), str(max_clump_id), str(nr))
                msg = "\n\n" +str(msg) + "\n\n"
                print(msg)

                # make sure that it is set to the global clone map
                pcr.setclone(global_clone_map)

                # identify mask based on the clump
                mask_selected_boolean_from_clump = pcr.ifthen(clump_ids == pcr.nominal(clump_id), mask_selected_boolean)
                mask_selected_boolean_from_clump = pcr.ifthen(mask_selected_boolean_from_clump, mask_selected_boolean_from_clump)

                # check whether the clump is empty
                check_if_empty = float(pcr.cellvalue(pcr.mapmaximum(pcr.scalar(pcr.defined(check_mask_selected_boolean_from_clump))),1)[0])
                
                if check_if_empty == 0.0: 
                
                    msg = "Map is empty !"
                    msg = "\n\n" +str(msg) + "\n\n"
                    print(msg)

                else:
                
                    msg = "Map is NOT empty !"
                    msg = "\n\n" +str(msg) + "\n\n"
                    print(msg)

                    # assign the clone code
                    assigned_number = assigned_number + 1
                    
                    # update global landmask for river and land
                    mask_selected_nominal = pcr.ifthen(mask_selected_boolean_from_clump, pcr.nominal(assigned_number))
                    landmask_all = pcr.cover(landmask_all, mask_selected_nominal) 
                    pcr.report(landmask_all, filename_for_nominal_land_river_mask_at_global_extent)
                    pcr.aguila(landmask_all)
				    
                    # save mask_selected_nominal at the global extent
                    filename_for_mask_selected_nominal_at_global_extent = "global_mask_%s_clump_%s_selected_nominal.map" %(str(nr), str(assigned_number)) 
                    filename_for_mask_selected_nominal_at_global_extent = os.path.join(out_folder, filename_for_mask_selected_nominal_at_global_extent )
                    pcr.report(mask_selected_nominal, filename_for_mask_selected_nominal_at_global_extent )
				    
                    # get the bounding box based on the landmask file
                    xmin, ymin, xmax, ymax = boundingBox(mask_selected_boolean_from_clump)
                    
                    # cellsize 
                    cellsize = vos.getMapAttributes(global_clone_map, "cellsize")
                    num_rows = int(round(ymax - ymin) / cellsize)
                    num_cols = int(round(xmax - xmin) / cellsize)
                    
                    # make the clone map using mapattr 
                    clonemap_mask_file = "clonemap_%s.map" %(str(assigned_number))
                    cmd = "mapattr -s -R %s -C %s -B -P yb2t -x %s -y %s -l %s %s" %(str(num_rows), str(num_cols), str(xmin), str(ymax), str(cellsize), clonemap_mask_file)
                    print(cmd); os.system(cmd)
                    
                    # make also a clone map with the file name using nr and assigned_number
                    clonemap_mask_long_file_name = "clonemap_with_longname_mask_%s_%s.map" %(str(nr), str(assigned_number))
                    cmd = "cp %s %s" %(str(clonemap_mask_file), str(clonemap_mask_long_file_name))
                    print(cmd); os.system(cmd)
                    
                    # set the local landmask for the clump
                    pcr.setclone(clonemap_mask_file)
                    local_mask_selected_from_clump = vos.readPCRmapClone(v = filename_for_mask_selected_nominal_at_global_extent, \
                                                                         cloneMapFileName = clonemap_mask_file, 
                                                                         tmpDir = tmp_folder, \
                                                                         absolutePath = None, isLddMap = False, cover = None, isNomMap = True)
                    local_mask_selected_from_clump_boolean = pcr.ifthen(pcr.scalar(local_mask_selected_from_clump) > 0.0, pcr.boolean(1.0))
                    local_mask_selected_from_clump_boolean = pcr.ifthen(local_mask_selected_from_clump_boolean, local_mask_selected_from_clump_boolean)
				    
                    # set the landmask
                    landmask_river_and_land = vos.readPCRmapClone(v = filename_for_land_river_mask_at_global_extent, \
                                                                  cloneMapFileName = clonemap_mask_file, 
                                                                  tmpDir = tmp_folder, \
                                                                  absolutePath = None, isLddMap = False, cover = None, isNomMap = True)
                    landmask_river_and_land_boolean = pcr.ifthen(pcr.scalar(landmask_river_and_land) > 0.0, pcr.boolean(1.0))
                    landmask_river_and_land_boolean = pcr.ifthen(landmask_river_and_land_boolean, landmask_river_and_land_boolean)
                    landmask_river_and_land_boolean = pcr.ifthen(local_mask_selected_from_clump_boolean, landmask_river_and_land_boolean)
                    landmask_river_and_land_file = "mask_%s.map" %(str(assigned_number))
                    pcr.report(landmask_river_and_land_boolean, landmask_river_and_land_file) 
			    

    # kill all aguila processes if exist
    os.system('killall aguila')

    # report a global nominal map for river and and land
    pcr.setclone(global_clone_map)
    pcr.report(landmask_all, filename_for_nominal_land_river_mask_at_global_extent)
    pcr.aguila(landmask_all)
    
    print("\n\n Done \n\n")
    
        
if __name__ == '__main__':
    sys.exit(main())

