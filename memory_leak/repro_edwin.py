#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

#~ import netCDF4
import numpy as np
import pcraster as pcr


def print_memory_usage():
    import psutil
    p = psutil.Process(os.getpid())
    print p  
    nr_mbytes = p.get_memory_info()[0] / 1048576.0
    log_file.write("{}\n".format(nr_mbytes))
    sys.stdout.write("{}\n".format(nr_mbytes))
    sys.stdout.flush()


log_file = file("memory.col", "w")

print_memory_usage()

# Use variable in expression.
for i in xrange(100):
    test_map = pcr.readmap("dummy.map")
    test_num = pcr.pcr2numpy(test_map, 0)
    result = variable * numpy.ones_like(variable)
    print_memory_usage()

log_file.close()
