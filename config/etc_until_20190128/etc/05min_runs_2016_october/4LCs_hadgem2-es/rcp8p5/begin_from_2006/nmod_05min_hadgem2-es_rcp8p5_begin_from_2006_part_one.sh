#!/bin/bash
#SBATCH -N 1
#SBATCH -t 29:59:00 
#SBATCH -p normal

# load a special version of pcraster
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/05min_runs_2016_october/4LCs_hadgem2-es/rcp8p5/begin_from_2006/setup_05min_hadgem2-es_rcp8p5_begin_from_2006_part_one.ini
