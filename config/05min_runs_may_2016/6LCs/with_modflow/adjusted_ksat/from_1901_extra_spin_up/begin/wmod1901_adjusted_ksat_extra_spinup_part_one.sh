#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p normal

# transient run
cd /home/edwinhs/github/edwinkost/PCR-GLOBWB/model
python parallel_pcrglobwb_with_prefactors_2016_03_29.py ../config/6LCs/with_modflow/adjusted_ksat/from_1901_extra_spin_up/begin/setup_05min_CRU-TS3.23_ERA20C_pcrglobwb_with_modflow_6LCs_original_parameter_set_adjusted_ksat_extra_spinup_from_1901_begin_part_one.ini

# NOTE: pcrglobwb modflow with adjusted_ksat - with extra spin-up - part_one - start from 1901
