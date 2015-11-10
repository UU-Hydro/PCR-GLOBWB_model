#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p normal                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB.py ../config/05min_runs_november_2015/setup_05min_pcrglobwb_only_cartesius_parallel.ini no_debug

# pcrglobwb only (without modflow) - start from 1901
