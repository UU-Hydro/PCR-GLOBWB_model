#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_may_2016/4LCs_edwin_parameter_set_with_modflow/no_correction/from_1901_extra_spin_up/natural/continue_from_2004/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_4LCs_edwin_parameter_set_natural_extra_spinup_from_1901_continue_from_2004_part_one.ini

# NOTE: pcrglobwb modflow - 4 LCs - edwin parameter set - no correction - NATURAL - with extra spin-up - part_one - start from 1901
#                                                                                                                 - continue from 1946
#                                                                                                                 - continue from 1958
#                                                                                                                 - continue from 2004

