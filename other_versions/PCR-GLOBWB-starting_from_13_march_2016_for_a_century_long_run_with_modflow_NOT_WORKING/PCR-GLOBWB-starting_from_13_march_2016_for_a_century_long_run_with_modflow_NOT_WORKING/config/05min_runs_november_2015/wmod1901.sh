#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python couplingPCR-GLOBWB-MODFLOW.py ../config/05min_runs_november_2015/setup_05min_pcrglobwb-modflow_cartesius.ini no_debug

# pcrglobwb modflow - start from 1901
