#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

def main():
    
    target_local_folder = "/scratch/depfg/sutan101/test_crop_opendap_files/"
    
    ncea_lat_range = "-16.0,0.0"
    ncea_lon_range = "28.0,41.0"

    opendap_main_folder = "https://opendap.4tu.nl/thredds/dodsC/data2/pcrglobwb/version_2019_11_beta/pcrglobwb2_input/"
    file_list = "list_of_global_nc_opendap_files_version_2019_11_beta_test.txt"

    txt_file_list = open(file_list, "r")
    
    # opendap file names
    filenames = txt_file_list.readlines()
    
    for opendap_filename in filenames:

        # target file name
        target_file_name = opendap_filename.replace(opendap_main_folder, target_local_folder)
                
        # preparing directory 
        target_directory = os.path.dirname(target_file_name)
        if os.path.exists(target_directory) == False:
            os.makedirs(target_directory)
        
        # perform ncea for cropping
        cmd_line = "ncea -O -d latitude," + ncea_lat_range + " -d longitude," + ncea_lon_range + " " + opendap_filename + " " + target_file_name
        print(cmd_line)
        os.system(cmd_line)
        cmd_line = "ncea -O -d lat," + ncea_lat_range + " -d lon," + ncea_lon_range + " " + opendap_filename + " " + target_file_name
        print(cmd_line)
        os.system(cmd_line)

    txt_file_list.close()
    
    print("\n Done! \n")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
