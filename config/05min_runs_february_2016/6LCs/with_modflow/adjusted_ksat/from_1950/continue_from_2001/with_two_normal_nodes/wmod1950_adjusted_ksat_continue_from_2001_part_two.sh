#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal                                                                                                                                                                              

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_february_2016/with_modflow/adjusted_ksat/from_1950/continue_from_2001/with_two_normal_nodes/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_adjusted_ksat_from_1950_continue_from_2001_part_two.ini

# NOTE: pcrglobwb modflow with adjusted_ksat - start from 1950
#                                              continue from 1974 (part_two)
#                                              continue from 2001 (part_two)
