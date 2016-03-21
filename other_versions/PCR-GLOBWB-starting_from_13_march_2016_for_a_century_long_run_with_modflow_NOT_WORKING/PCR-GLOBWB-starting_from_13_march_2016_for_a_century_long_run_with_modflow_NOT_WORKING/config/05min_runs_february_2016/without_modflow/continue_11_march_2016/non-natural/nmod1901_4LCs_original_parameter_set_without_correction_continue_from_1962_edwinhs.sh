#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal                                                                                                                                                                              

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors.py ../config/05min_runs_february_2016/continue_11_march_2016/non-natural/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_only_cartesius_parallel_4LCs_original_parameter_set_continue_from_1962.ini parallel 

# pcrglobwb only (with accutraveltime, without modflow) - start
# pcrglobwb only (with accutraveltime, without modflow) - continue from 1962 (using a normal node)
