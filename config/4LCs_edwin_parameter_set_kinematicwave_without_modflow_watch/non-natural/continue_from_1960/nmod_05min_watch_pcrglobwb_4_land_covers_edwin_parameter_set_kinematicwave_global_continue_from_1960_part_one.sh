#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normmal

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/4LCs_edwin_parameter_set_kinematicwave_without_modflow_watch/non-natural/continue_from_1960/setup_05min_watch_pcrglobwb_4_land_covers_edwin_parameter_set_kinematicwave_global_continue_from_1960_part_one.ini

