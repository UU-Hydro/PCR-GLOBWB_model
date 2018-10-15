#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal
#SBATCH --constraint=haswell

# mail alert at start, end and abortion of execution                                                                                            
#SBATCH --mail-type=ALL                                                                                                                         
                                                                                                                                                
# send mail to this address                                                                                                                     
#SBATCH --mail-user=edwinkost@gmail.com   

# load a special version of pcraster
. /home/edwin/bin-special/pcraster-4.1.0-beta-20151027_x86-64_gcc-4/bashrc_special_pcraster_modflow

cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_runner.py ../config/runs_2017_july_aug_finalizing_4LCs/05min_runs/05min_runs_with-modflow_4LCs_cru-forcing_1958-2015/natural_with-modlow_starting_from_1958/begin_from_1958/setup_05min_natural_with-modflow_starting_from_1958_part_two.ini
