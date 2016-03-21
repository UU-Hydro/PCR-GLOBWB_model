#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python couplingPCR-GLOBWB-MODFLOW.py ../config/05min_runs_november_2015/continue_on_23_november/setup_05min_pcrglobwb-modflow_cartesius_from_2000_continue.ini no_debug

# pcrglobwb modflow - start from 1950 - continue from 1972 - continue from 1984 - continue from 2000
