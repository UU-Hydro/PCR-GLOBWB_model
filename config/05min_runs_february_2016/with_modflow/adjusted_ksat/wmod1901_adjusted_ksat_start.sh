#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

# steady state run (this has been performed)
#~ cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
#~ python deterministic_runner_for_monthly_merging_and_modflow.py ../config/05min_runs_february_2016/with_modflow/adjusted_ksat/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_only_cartesius_parallel_6LCs_original_parameter_set_adjusted_ksat_with_modflow.STEADYSTATE.ini debug steady-state-only

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_march_2016.py ../config/05min_runs_february_2016/with_modflow/adjusted_ksat/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_only_cartesius_parallel_6LCs_original_parameter_set_adjusted_ksat_with_modflow.ini


# pcrglobwb modflow with adjusted_ksat - start from 1901
