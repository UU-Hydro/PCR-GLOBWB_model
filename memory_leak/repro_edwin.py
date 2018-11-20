#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import psutil
#~ import netCDF4
import numpy as np
import pcraster as pcr

process = psutil.Process(os.getpid())
log_file = file("memory.col", "w")


def print_memory_usage():
    nr_mbytes = process.memory_info()[0] / 1048576.0
    log_file.write("{}\n".format(nr_mbytes))
    sys.stdout.write("{}\n".format(nr_mbytes))
    sys.stdout.flush()



print_memory_usage()

counter = 0
for i in xrange(500):
#~ while True: 
    counter = counter + 1
    print counter
    test_map = pcr.readmap("dummy.map")
    test_num = pcr.pcr2numpy(test_map, 0)[:]
    print_memory_usage()

log_file.close()
