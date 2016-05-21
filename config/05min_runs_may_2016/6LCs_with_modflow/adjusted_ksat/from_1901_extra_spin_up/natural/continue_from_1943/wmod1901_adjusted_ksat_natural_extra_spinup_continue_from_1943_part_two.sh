#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_may_2016/6LCs_with_modflow/adjusted_ksat/from_1901_extra_spin_up/natural/continue_from_1943/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_adjusted_ksat_natural_extra_spinup_from_1901_continue_from_1943_part_two.ini

# NOTE: pcrglobwb modflow with adjusted_ksat - with extra spin-up - natural - part_two - start from 1901
#                                                                                        continue from 1943
