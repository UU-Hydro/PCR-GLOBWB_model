#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

def main():
    
    target_local_folder = "/scratch/depfg/sutan101/test_crop_opendap_files_rhine-meuse/"
    
    #~ ncea_lat_range = "-16.0,0.0"
    #~ ncea_lon_range = "28.0,41.0"

    ncea_lat_range    = "46.0,53.0"
    ncea_lon_range    = "3.00,13.0"

    opendap_main_folder = "https://opendap.4tu.nl/thredds/dodsC/data2/pcrglobwb/version_2019_11_beta/pcrglobwb2_input/"

    #~ file_list = "list_of_global_nc_opendap_files_version_2019_11_beta_test.txt"
    file_list    = "list_of_global_nc_opendap_files_version_2019_11_beta.txt"

    txt_file_list = open(file_list, "r")
    
    # opendap file names
    filenames = txt_file_list.readlines()
    
    for opendap_filename in filenames:

        # opendap file name
        opendap_filename = opendap_filename.replace("\n", "")
        
        # target file name
        target_file_name = opendap_filename.replace(opendap_main_folder, target_local_folder)
                
        # preparing directory 
        target_directory = os.path.dirname(target_file_name)
        if os.path.exists(target_directory) == False:
            os.makedirs(target_directory)
        
        print("\n\n")

        # perform ncea for cropping
        msg = 'Croping the file ' +  opendap_filename + "using one of the following commands: \n"
        print(msg) 

        # - using one of the following command lines, depending on variable names of lat/latitude and lon/longitude 
        cmd_line = "ncks -D 2 -O -d latitude," + ncea_lat_range + " -d longitude," + ncea_lon_range + " " + opendap_filename + " " + target_file_name
        print(cmd_line)
        os.system(cmd_line)
        cmd_line = "ncks -D 2 -O -d lat," + ncea_lat_range + " -d lon," + ncea_lon_range + " " + opendap_filename + " " + target_file_name
        print(cmd_line)
        os.system(cmd_line)
        
        # check if the file is produced
        msg = "\n"        
        if os.path.exists(target_file_name):
            msg += "The file " + target_file_name + " is succesfuly created. Please ignore any above-mentioned ERROR messages related to dimension names of lat/latitude."
        else: 
            msg += "ERROR: The file " + target_file_name + " can NOT BE created."
        msg += "\n"        
        print(msg)    

    txt_file_list.close()
    
    print("\n Done! \n")                          
                                        

if __name__ == '__main__':
    sys.exit(main())
