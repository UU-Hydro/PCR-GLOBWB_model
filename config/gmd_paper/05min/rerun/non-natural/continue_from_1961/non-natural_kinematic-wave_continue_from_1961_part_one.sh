#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 

#SBATCH -p normal

# go to the PCR-GLOBWB model folder
cd ~/github/edwinkost/PCR-GLOBWB/model/

# then execute your PCR-GLOBWB model run
python parallel_pcrglobwb_runner.py ../config/gmd_paper/05min/rerun/non-natural/continue_from_1961/setup_05min_non-natural_continue_from_1961_part_one.ini
