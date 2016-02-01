#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB_without_prefactors.py ../config/05min_runs_january_2016/setup_05min_pcrglobwb_only_cartesius_parallel_4LCs_edwin_parameter_set_kinematic_wave_continue_from_1971.ini no_debug

# pcrglobwb only (with kinematic wave, but without modflow) - start
#                                                           - continue from 1958
#                                                           - continue from 1971
