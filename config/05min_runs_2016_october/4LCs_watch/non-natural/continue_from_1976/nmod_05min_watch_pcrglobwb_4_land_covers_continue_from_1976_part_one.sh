#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

cd /home/edwinsut/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/05min_runs_2016_october/4LCs_watch/non-natural/continue_from_1976/setup_05min_watch_pcrglobwb_4_land_covers_continue_from_1976_part_one.ini
