#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

import pcraster_to_netcdf as pcr2nc

def main():
    
    #~ source_path = "/scratch/depfg/sutan101/test_ldd/input/"
    #~ 
    #~ target_path = "/scratch/depfg/sutan101/test_ldd/output_2/"

    source_path = "/quanta1/home/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_10_beta_1_extended/"
    
    target_path = "/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta"

    without_compression = True

    if without_compression:
        target_path = target_path + "_without_compression"
    else:
        target_path = target_path + "_with_compression"
    
    target_path = target_path + "/"
    
    if os.path.exists(target_path): shutil.rmtree(target_path)
    os.makedirs(target_path)
    print(target_path)
    
    # about os.walk, see https://www.tutorialspoint.com/python/os_walk.htm

    for roots, dirs, files in os.walk(source_path):

        # preparing directories
        for directory in dirs:
            source_directory = os.path.join(roots, directory)
            target_directory = source_directory.replace(source_path, target_path)
            if os.path.exists(target_directory): shutil.rmtree(target_directory)
            os.makedirs(target_directory)
            print(target_directory)

        for file_name in files:
            
            print("\n\n")

            # get the full path of source
            source_file_name = os.path.join(roots, file_name)
            print(source_file_name)
            
            # get target file_name
            target_file_name = source_file_name.replace(source_path, target_path)

            # make sure that the output directory is ready
            target_directory = os.path.dirname(source_file_name).replace(source_path, target_path)
            if os.path.exists(target_directory) == False: os.makedirs(target_directory)

            #~ # - go to the target directory - not necessary
            #~ os.chdir(target_directory)
            
            if target_file_name.endswith(".nc") or target_file_name.endswith(".nc4"):

                # for netcdf files

                # - rename ".nc4" to "nc" (the standard extension of netcdf file is ".nc")
                if target_file_name.endswith(".nc4"): target_file_name = target_file_name[:-1]

                #~ if without_compression == False: target_file_name = target_file_name.replace(".nc", "_zip.nc")
                
                # - if compression is used, use only level 1
                cmd_line = 'cdo -L -z zip_1 -f nc4 -copy ' + source_file_name + " " + target_file_name

                # - turn off compression, but we make sure that the format is nc4
                if without_compression:
                    cmd_line = 'cdo -L -f nc4 -copy ' + source_file_name + " " + target_file_name

                #~ # - alternative: using nco
                #~ cmd_line = 'nccopy -k netCDF-4 -d1 -u ' + source_file_name + " " + target_file_name

                print(cmd_line)
                os.system(cmd_line)
            
                # add/replace the 'comment' attribute to netcdf files
                comment_line = 'This file is part of the input files for the PCR-GLOBWB model runs underlying the publication "PCR-GLOBWB 2: a 5 arcmin global hydrological and water resources model" (Sutanudjaja et al., 2018, https://doi.org/10.5194/gmd-11-2429-2018).'
                cmd = "ncatted -O -h -a comment,global,o,c,'" + comment_line + "' " + target_file_name
                print(cmd)
                os.system(cmd)

            elif target_file_name.endswith(".map"):  

                # for pcraster map files
                
                # shall we also copy them?
                shutil.copy(source_file_name, target_file_name)

                # convert them to netcdf
                target_file_name = target_file_name[:-4] + ".nc"
                #~ if without_compression == False: target_file_name = target_file_name.replace(".nc", "_zip.nc")
                
                msg = "converting " + source_file_name + " to " + target_file_name
                print(msg)
                netcdf_zlib_option = True
                if without_compression: netcdf_zlib_option = False
                pcr2nc.convert_pcraster_to_netcdf(\
                                                  input_pcr_map_file = source_file_name,\
                                                  output_netcdf_file = target_file_name,\
                                                  variable_name = None,\
                                                  netcdf_global_attributes = None,\
                                                  netcdf_y_orientation_from_top_bottom = True,\
                                                  variable_unit = "unknown",\
                                                  netcdf_format = "NETCDF4",\
                                                  netcdf_zlib_option = False,\
                                                  time_input = None)
            
                # add/replace the 'comment' attribute to netcdf files
                comment_line = 'This file is part of the input files for the PCR-GLOBWB model runs underlying the publication "PCR-GLOBWB 2: a 5 arcmin global hydrological and water resources model" (Sutanudjaja et al., 2018, https://doi.org/10.5194/gmd-11-2429-2018).'
                cmd = "ncatted -O -h -a comment,global,o,c,'" + comment_line + "' " + target_file_name
                print(cmd)
                os.system(cmd)
            
            else:
                
                # for other files
                
                # just copy
                msg = "copying " + source_file_name + " to " + target_file_name
                print(msg)
                shutil.copy(source_file_name, target_file_name)

                #~ # skip
                #~ pass

    print("\n Done! \n")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
