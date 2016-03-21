#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00
#SBATCH -p fat

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB_without_prefactors.py ../config/05min_runs_january_2016/setup_05min_pcrglobwb_only_cartesius_parallel_natural_kinematic_wave_continue_from_2000.ini no_debug

# pcrglobwb only (natural, kinematic wave, without modflow) - start
# pcrglobwb only (natural, kinematic wave, without modflow) - continue from 1958
# pcrglobwb only (natural, kinematic wave, without modflow) - continue from 1966
# pcrglobwb only (natural, kinematic wave, without modflow) - continue from 1972
# pcrglobwb only (natural, kinematic wave, without modflow) - continue from 1979
# pcrglobwb only (natural, kinematic wave, without modflow) - continue from 1993
# pcrglobwb only (natural, kinematic wave, without modflow) - continue from 2000

