#!/bin/bash
#SBATCH -N 1
#SBATCH -t 100:59:00 
#SBATCH -p normal

# load a special version of pcraster
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/05min_runs_2016_october/4LCs_cru-ts3.23_era-20c/non-natural/begin_from_1958/setup_05min_cru-ts3.23_era-20c_kinematicwave_begin_from_1958_part_two.ini
