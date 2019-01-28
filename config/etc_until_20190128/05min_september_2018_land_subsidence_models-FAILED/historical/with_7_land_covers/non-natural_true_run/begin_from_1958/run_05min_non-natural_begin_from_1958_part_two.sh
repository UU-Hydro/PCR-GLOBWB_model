#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# go to the PCR-GLOBWB model folder
cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model/

# then execute your PCR-GLOBWB model run
python parallel_pcrglobwb_runner.py ../config/05min_september_2018_land_subsidence_models/historical/with_7_land_covers/non-natural_true_run/begin_from_1958/setup_05min_non-natural_begin_from_1958_part_two.ini

