#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB_without_prefactors.py ../config/05min_runs_january_2016/setup_05min_pcrglobwb_only_cartesius_parallel_4LCs_edwin_parameter_set.ini no_debug

# pcrglobwb only (without modflow) - start

