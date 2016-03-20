#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors.py ../config/05min_runs_february_2016/continue_20_march_2016/non-natural/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_only_cartesius_parallel_6LCs_original_parameter_set_continue_from_1953.ini parallel 

# pcrglobwb only (with accutraveltime, without modflow) - start
#                                                         continue from 1922
#                                                         continue from 1953
