#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal
#SBATCH --constraint=haswell
#SBATCH -J 05min_non-natural_accutraveltime_part_two_using_a_consistent_pcraster_as_used_in_gmd_paper

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com                                                                                                                      

# load a special version of pcraster (version: Oct 27 2015) - this pcraster version used in the GMD paper
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

# check pcraster version
pcrcalc; mapattr

# go to the PCR-GLOBWB model folder
cd ~/github/edwinkost/PCR-GLOBWB/model/

# then execute your PCR-GLOBWB model run
python parallel_pcrglobwb_runner.py ../config/gmd_paper/05min/rerun/non-natural/begin_from_1958/setup_05min_non-natural_parallel_part_two.ini

# check pcraster version
pcrcalc; mapattr
