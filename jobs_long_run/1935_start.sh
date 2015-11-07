#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

python ../model/couplingPCR-GLOBWB-MODFLOW.py ../config/prepare_5min_run/setup_05min_pcrglobwb-modflow_cartesius_from_1935.ini no_debug
