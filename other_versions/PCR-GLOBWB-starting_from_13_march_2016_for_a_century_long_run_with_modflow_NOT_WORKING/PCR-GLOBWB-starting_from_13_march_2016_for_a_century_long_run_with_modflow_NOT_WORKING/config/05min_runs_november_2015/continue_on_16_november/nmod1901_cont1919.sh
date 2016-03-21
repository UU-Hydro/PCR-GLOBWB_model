#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB.py ../config/05min_runs_november_2015/continue_on_16_november/setup_05min_pcrglobwb_only_cartesius_parallel_from_1919_continue.ini no_debug

# pcrglobwb only (without modflow) - start from 1901 - continue from 1919

