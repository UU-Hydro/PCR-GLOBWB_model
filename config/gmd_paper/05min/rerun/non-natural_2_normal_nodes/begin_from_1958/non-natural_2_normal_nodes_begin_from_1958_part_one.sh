#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal
#SBATCH --constraint=haswell
#SBATCH -J 05min_non-natural_accutraveltime_part_one

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com                                                                                                                      

# go to the PCR-GLOBWB model folder
cd ~/github/edwinkost/PCR-GLOBWB/model/

# then execute your PCR-GLOBWB model run
python parallel_pcrglobwb_runner.py ../config/gmd_paper/05min/rerun/non-natural_2_normal_nodes/begin_from_1958/setup_05min_non-natural_parallel_part_one.ini
