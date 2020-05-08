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

    source_path = "/quanta1/home/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/"
    source_path = "/scratch/depfg/sutan101/data/pcrglobwb2_input_arise/develop/pcrglobwb2_input/"
    
    target_path = "/scratch/depfg/sutan101/data/pcrglobwb2_input_arise/develop_tanzania_version_2019_12_11/pcrglobwb2_input/"

    if os.path.exists(target_path): shutil.rmtree(target_path)
    os.makedirs(target_path)
    print(target_path)
    
    # about os.walk, see https://www.tutorialspoint.com/python/os_walk.htm

    for roots, dirs, files in os.walk(source_path, followlinks = True):

        # preparing directories
        for directory in dirs:

            source_directory = os.path.join(roots, directory)
            target_directory = source_directory.replace(source_path, target_path)
            
            target_directory = target_directory.replace("global", "tanzania")

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

            target_file_name = target_file_name.replace("global", "tanzania")

            # make sure that the output directory is ready
            target_directory = os.path.dirname(target_file_name).replace(source_path, target_path)
            if os.path.exists(target_directory) == False: os.makedirs(target_directory)

            #~ # - go to the target directory - not necessary
            #~ os.chdir(target_directory)
            
            if target_file_name.endswith(".nc") or target_file_name.endswith(".nc4"):

                # for netcdf files

                # - rename ".nc4" to "nc" (the standard extension of netcdf file is ".nc")
                if target_file_name.endswith(".nc4"): target_file_name = target_file_name[:-1]

                if os.path.exists(target_file_name) == False:

                    # cropping
                    cmd_line = "ncea -O -d latitude,-16.0,0.0 -d longitude,28.0,41.0 " + source_file_name + " " + target_file_name
                    print(cmd_line)
                    os.system(cmd_line)
                    cmd_line = "ncea -O -d lat,-16.0,0.0 -d lon,28.0,41.0 " + source_file_name + " " + target_file_name
                    print(cmd_line)
                    os.system(cmd_line)

            elif target_file_name.endswith(".map"):  

                # for pcraster map files
                
                #~ # shall we also copy them?
                #~ shutil.copy(source_file_name, target_file_name)

                # convert them to netcdf
                target_file_name = target_file_name[:-4] + ".nc"
                print(target_file_name)
                
                if os.path.exists(target_file_name) == False:
                
                    msg = "converting " + source_file_name + " to " + target_file_name
                    print(msg)
                    netcdf_zlib_option = False
                    pcr2nc.convert_pcraster_to_netcdf(\
                                                      input_pcr_map_file = source_file_name,\
                                                      output_netcdf_file = target_file_name + ".tmp",\
                                                      variable_name = None,\
                                                      netcdf_global_attributes = None,\
                                                      netcdf_y_orientation_from_top_bottom = True,\
                                                      variable_unit = "unknown",\
                                                      netcdf_format = "NETCDF4",\
                                                      netcdf_zlib_option = False,\
                                                      time_input = None)
                    
                    
                    # cropping
                    source_file_name = target_file_name + ".tmp"
                    cmd_line = "ncea -O -d latitude,-16.0,0.0 -d longitude,28.0,41.0 " + source_file_name + " " + target_file_name
                    print(cmd_line)
                    os.system(cmd_line)
                    cmd_line = "ncea -O -d lat,-16.0,0.0 -d lon,28.0,41.0 " + source_file_name + " " + target_file_name
                    print(cmd_line)
                    os.system(cmd_line)
                    cmd_line = "rm " + source_file_name
                    print(cmd_line)
                    os.system(cmd_line)

            else:
                
                # for other files
                
                # just copy
                msg = "copying " + source_file_name + " to " + target_file_name
                print(msg)
                shutil.copy(source_file_name, target_file_name)


    print("\n Done! \n")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
