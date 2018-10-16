#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# go to the PCR-GLOBWB model folder
cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model/

# then execute your PCR-GLOBWB model run
python parallel_pcrglobwb_runner.py ../config/05min_october_2018_land_subsidence_models/historical/with_7_land_covers/natural_only_spinup/begin_from_1955/setup_05min_natural_spinup_begin_from_1955_part_one.ini

