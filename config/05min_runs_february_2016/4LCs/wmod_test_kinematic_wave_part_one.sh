#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal                                                                                                                                                                              
# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_february_2016/4LCs/setup_05min_pcrglobwb_modflow_cartesius_parallel_4LCs_edwin_parameter_set_test_part_one.ini

# NOTE: pcrglobwb modflow with kinematic wave - test
