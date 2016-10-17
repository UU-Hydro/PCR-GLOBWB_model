#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/05min_runs_2016_october/4LCs_edwin_parameter_set_kinematicwave_without_modflow_watch/non-natural/begin_from_1958/setup_05min_watch_pcrglobwb_4_land_covers_edwin_parameter_set_kinematicwave_begin_from_1958_part_one.ini
