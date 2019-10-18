#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

import pcraster_to_netcdf as pcr2nc

def main():
    
    source_path = "/quanta1/home/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_10_beta_1/"
    
    target_path = "/scratch/depfg/sutan101/data/pcrglobwb2_input_release/develop_complete_set_for_opendap/"
    
    # about os.walk, see https://www.tutorialspoint.com/python/os_walk.htm

    for roots, dirs, files in os.walk(source_path):

        # preparing directories
        for directory in dirs:
            source_directory = os.path.join(roots, directory)
            target_directory = source_directory.replace(source_path, target_path)
            if os.path.exists(target_directory): shutil.rmtree(target_directory)
            os.makedirs(target_directory)
            print(target_directory)

        print(" ")

        for file_name in files:
            
            # get the full path of source
            source_file_name = os.path.join(roots, file_name)
            print(source_file_name)
            
            # get target file_name
            target_file_name = source_file_name.replace(source_path, target_path)
            if target_file_name.endswith(".nc4"): target_file_name = target_file_name[:-1]

            if target_file_name.endswith(".nc"):
                # for netcdf files, just copy
                shutil.copy(source_file_name, target_file_name)
            
            elif target_file_name.endswith(".map"):  
                # for pcraster map files, convert them to netcdf 
                target_file_name = target_file_name[:-4] + ".nc"
                pcr2nc.convert_pcraster_to_netcdf(input_pcr_map_file = source_file_name,\
                                                  output_netcdf_file = target_file_name)
            
            else:
                # for other files, just copy
                shutil.copy(source_file_name, target_file_name)

            print(target_file_name)


            print(" ")

    print("Done!")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
