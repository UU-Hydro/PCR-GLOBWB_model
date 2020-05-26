#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

def main():
    
    local_source_folder = "/quanta1/home/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_11_beta/pcrglobwb2_input/"

    opendap_main_folder = "https://opendap.4tu.nl/thredds/dodsC/data2/pcrglobwb/version_2019_11_beta/pcrglobwb2_input/"
    
    txt_file_list = open("list_of_global_nc_opendap_files_version_2019_11_beta.txt", "w")
    
    for roots, dirs, files in os.walk(local_source_folder, followlinks = True):

        for file_name in files:
            
            print("\n\n")

            # local file name
            local_file_name = os.path.join(roots, file_name)
            
            # opendap file name
            opendap_filename = local_file_name.replace(local_source_folder, opendap_main_folder)

            # print only netcdf files and skip cloneMaps directories
            if (opendap_filename.endswith(".nc") or opendap_filename.endswith(".nc4")) and ("cloneMaps" not in opendap_filename):

                print(opendap_filename)
                
                # write it to the file
                txt_file_list.writelines(opendap_filename + "\n")

    txt_file_list.close()
    
    print("\n Done! \n")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
