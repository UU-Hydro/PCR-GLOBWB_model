#!/bin/bash
#SBATCH -N 1
#SBATCH -t 59:00 
#SBATCH -p normal

# load a special version of pcraster
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/05min_example_with_modflow/online_coupling/setup_05min_cru-ts3.23_era-20C_pcrglobwb_with_modflow_4_land_covers_test_part_two.ini
