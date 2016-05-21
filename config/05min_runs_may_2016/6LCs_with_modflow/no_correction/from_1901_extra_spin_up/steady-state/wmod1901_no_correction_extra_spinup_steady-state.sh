#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal            

# steady state run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model/
python deterministic_runner_for_monthly_merging_and_modflow_2016_03_29.py ../config/05min_runs_may_2016/6LCs_with_modflow/no_correction/from_1901_extra_spin_up/steady-state/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_no_correction_extra_spinup.STEADYSTATE_natural_1901to1925.ini

# NOTE: pcrglobwb modflow with 6LCs - no_correction - steady-state - natural
