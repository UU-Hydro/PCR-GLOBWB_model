#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

python couplingPCR-GLOBWB-MODFLOW.py ../config/prepare_5min_run/setup_05min_pcrglobwb-modflow_cartesius_from_1990.ini no_debug
