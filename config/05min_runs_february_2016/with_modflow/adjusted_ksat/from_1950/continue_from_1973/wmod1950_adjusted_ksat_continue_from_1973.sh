#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_march_2016.py ../config/05min_runs_february_2016/with_modflow/adjusted_ksat/from_1950/continue_from_1973/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_adjusted_ksat_from_1950_continue_from_1973.ini

# NOTE: pcrglobwb modflow with adjusted_ksat - start from 1950
#                                              continue from 1973
