#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

import pcraster as pcr

# utility modules:
import virtualOS as vos
import outputNetcdf as out_nc

def convert_pcraster_to_netcdf(\
                               input_pcr_map_file,\
                               output_netcdf_file,\
                               variable_name = None,\
                               netcdf_global_attributes = None,\
                               netcdf_y_orientation_from_top_bottom = True,\
                               variable_unit = "unknown",\
                               netcdf_format = "NETCDF4",\
                               netcdf_zlib_option = False,\
                               time_input = None,\
                               ):
    
    # read the pcraster map
    pcr.setclone(input_pcr_map_file)
    input_pcr_map = pcr.readmap(input_pcr_map_file)
    
    if variable_name is None: 
        variable_name = os.path.basename(input_pcr_map_file)

        # Note variable, dimension and attribute names should begin with a letter and be composed of letters, digits, and underscores (see e.g. https://www.unidata.ucar.edu/support/help/MailArchives/netcdf/msg10684.html)

        # - replace "." with "_"
        variable_name = variable_name.replace(".", "_")
        
        # - replace "-" with "_"
        variable_name = variable_name.replace("-", "_")
    
    # converting it to a netcdf file
    # - initiate an object to write a netcdf file
    output_netcdf = out_nc.OutputNetcdf(inputMapFileName = input_pcr_map_file, \
                                        netcdf_format = netcdf_format,\
                                        netcdf_zlib = netcdf_zlib_option,\
                                        netcdf_attribute_dict = netcdf_global_attributes,\
                                        netcdf_attribute_description = None,\
                                        netcdf_y_orientation_from_top_bottom = netcdf_y_orientation_from_top_bottom)
    # - create the netcdf file
    output_netcdf.createNetCDF(ncFileName = output_netcdf_file, \
                               varName    = variable_name, \
                               varUnits   = variable_unit, \
                               date       = None
                               )                                    
    # - write to the netcdf file
    output_netcdf.data2NetCDF(ncFileName   = output_netcdf_file, \
                              shortVarName = variable_name, 
                              varField     = pcr.pcr2numpy(input_pcr_map, vos.MV), 
                              timeStamp    = None, 
                              posCnt       = None
                              )
    
    print("\n Done! \n")                          
                                        

def main():
    
    input_pcr_map_file = os.path.abspath(sys.argv[1])
    output_netcdf_file = os.path.abspath(sys.argv[2])
    
    convert_pcraster_to_netcdf(\
                               input_pcr_map_file,\
                               output_netcdf_file,\
                               variable_name = None,\
                               netcdf_global_attributes = None,\
                               netcdf_y_orientation_from_top_bottom = True,\
                               variable_unit = "unknown",\
                               netcdf_format = "NETCDF4",\
                               netcdf_zlib_option = False,\
                               time_input = None,\
                               )
    

if __name__ == '__main__':
    sys.exit(main())
