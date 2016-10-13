#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# load a special version of pcraster that is optimized for pcraster-modflow (provided by Oliver)
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

# run using the account of "edwin":
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/4LCs_edwin_parameter_set_kinematicwave_without_modflow_noresm1-m/non-natural/continue_from_1971/setup_05min_noresm1-m_pcrglobwb_4_land_covers_edwin_parameter_set_kinematicwave_continue_from_1971_part_one.ini
