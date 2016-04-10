#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal                                                                                                                                                                              

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_february_2016/6LCs/with_modflow/adjusted_ksat/from_1901/continue_from_1987/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_adjusted_ksat_from_1901_continue_from_1987_part_one.ini

# NOTE: pcrglobwb modflow with adjusted_ksat - start from 1901
#                                              continue from 1925
#                                              continue from 1942 (part_one)
#                                              continue from 1987 (part_one)

