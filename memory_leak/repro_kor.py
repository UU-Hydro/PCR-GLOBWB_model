# -*- coding: utf-8 -*-
import os
import sys
import psutil
import netCDF4
import numpy


process = psutil.Process(os.getpid())
log_file = file("memory.col", "w")


def print_memory_usage():
    nr_mbytes = process.get_memory_info()[0] / 1048576.0
    log_file.write("{}\n".format(nr_mbytes))
    sys.stdout.write("{}\n".format(nr_mbytes))
    sys.stdout.flush()


# Attach to netcdf file.
filename = "http://motherlode.ucar.edu:8080/thredds/dodsC/" \
    "grib/FNMOC/NAVGEM/Global_0p5deg/best"
dataset = netCDF4.Dataset(filename)

# Get variable.
# variable is a netCDF4.Variable instance.
variable = dataset.variables["lon"]

# # variable is a numpy.ndarray instance.
# variable = dataset.variables["lon"][:]

print_memory_usage()

# Use variable in expression.
for i in xrange(100):
    result = variable * numpy.ones_like(variable)
    print_memory_usage()

dataset.close()
log_file.close()
