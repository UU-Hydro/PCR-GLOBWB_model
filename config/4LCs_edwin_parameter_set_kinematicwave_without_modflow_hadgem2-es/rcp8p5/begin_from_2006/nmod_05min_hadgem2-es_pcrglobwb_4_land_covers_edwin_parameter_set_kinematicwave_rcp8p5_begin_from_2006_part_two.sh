#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# load a special version of pcraster that is optimized for pcraster-modflow (provided by Oliver)
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow


cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/4LCs_edwin_parameter_set_kinematicwave_without_modflow_hadgem2-es/rcp8p5/begin_from_2006/setup_05min_hadgem2-es_pcrglobwb_4_land_covers_edwin_parameter_set_kinematicwave_rcp8p5_begin_from_2006_part_two.ini
