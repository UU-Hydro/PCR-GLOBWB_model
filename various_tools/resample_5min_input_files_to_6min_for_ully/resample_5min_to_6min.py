#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

def main():
    
    target_local_folder = "/scratch/depfg/sutan101/test_resample_to_06min/"
    
    source_local_folder = "/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta/pcrglobwb2_input/"
    opendap_main_folder =  "https://opendap.4tu.nl/thredds/dodsC/data2/pcrglobwb/version_2019_11_beta/pcrglobwb2_input/"

    file_list    = "list_of_global_nc_5min_version_2019_11_beta_without_routing_and_meteo_test.txt"

    txt_file_list = open(file_list, "r")
    
    # file names
    filenames = txt_file_list.readlines()
    
    for opendap_filename in filenames:

        # opendap file name
        opendap_filename = opendap_filename.replace("\n", "")
        
        # local file name
        local_file_name  = opendap_filename.replace(opendap_main_folder, source_local_folder)
        
        # target file name
        target_file_name = opendap_filename.replace(opendap_main_folder, target_local_folder)
                
        # target file name
        target_file_name = target_file_name.replace("global_05min", "global_06min")

        # preparing directory 
        target_directory = os.path.dirname(target_file_name)
        if os.path.exists(target_directory) == False:
            os.makedirs(target_directory)
        
        print("\n\n")

        # perform cdo remapcon

        cmd_line = "cdo -L -remapcon,griddes_land_mask_only.nc.txt " + " " + local_file_name + " " + target_file_name
        print(cmd_line)
        os.system(cmd_line)
        
        # check if the file is produced
        msg = "\n"        
        if os.path.exists(target_file_name):
            msg += "The file " + target_file_name + " is succesfuly created."
        else: 
            msg += "ERROR: The file " + target_file_name + " can NOT BE created."
        msg += "\n"        
        print(msg)    

    txt_file_list.close()
    
    print("\n Done! \n")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
