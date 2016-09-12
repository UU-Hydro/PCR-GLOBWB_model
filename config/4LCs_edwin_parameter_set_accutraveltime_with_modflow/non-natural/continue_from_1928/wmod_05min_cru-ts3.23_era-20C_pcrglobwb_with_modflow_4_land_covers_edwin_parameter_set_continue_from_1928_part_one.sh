#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal


# load a special version of pcraster that is optimized for pcraster-modflow (provided by Oliver)
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

# transient run
cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/4LCs_edwin_parameter_set_accutraveltime_with_modflow/non-natural/continue_from_1928/setup_05min_cru-ts3.23_era-20C_pcrglobwb_with_modflow_4_land_covers_edwin_parameter_set_continue_from_1928_part_one.ini
