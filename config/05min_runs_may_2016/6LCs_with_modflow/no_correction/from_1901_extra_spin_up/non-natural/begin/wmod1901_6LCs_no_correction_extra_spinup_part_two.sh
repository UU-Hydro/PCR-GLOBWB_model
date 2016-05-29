#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_may_2016/6LCs_with_modflow/no_correction/from_1901_extra_spin_up/non-natural/begin/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_no_correction_extra_spinup_from_1901_begin_part_two.ini

# NOTE: pcrglobwb modflow - 6LCs no correction - with extra spin-up - part_two - start from 1901
