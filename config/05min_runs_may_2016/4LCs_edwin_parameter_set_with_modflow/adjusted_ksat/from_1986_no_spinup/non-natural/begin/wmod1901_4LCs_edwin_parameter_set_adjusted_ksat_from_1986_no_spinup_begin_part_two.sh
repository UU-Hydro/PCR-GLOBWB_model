#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# transient run
cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/05min_runs_may_2016/4LCs_edwin_parameter_set_with_modflow/adjusted_ksat/from_1986_no_spinup/non-natural/begin/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_4LCs_edwin_parameter_set_adjusted_ksat_from_1986_no_spinup_begin_part_two.ini

# NOTE: pcrglobwb modflow - 4 LCs - edwin parameter set - adjusted_ksat - non-natural - from 1986 no spinup - part_two - start from 1986

