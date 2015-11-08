#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

python parallelPCR-GLOBWB.py ../config/prepare_5min_run/setup_05min_pcrglobwb_only.ini no_debug
