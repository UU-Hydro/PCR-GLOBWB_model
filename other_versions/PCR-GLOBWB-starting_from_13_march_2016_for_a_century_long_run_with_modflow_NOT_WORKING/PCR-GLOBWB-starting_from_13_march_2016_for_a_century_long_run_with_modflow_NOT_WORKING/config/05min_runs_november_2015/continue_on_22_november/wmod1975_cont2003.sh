#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python couplingPCR-GLOBWB-MODFLOW.py ../config/05min_runs_november_2015/continue_on_22_november/setup_05min_pcrglobwb-modflow_cartesius_from_2003_continue.ini no_debug

# pcrglobwb modflow - start from 1975 - continue from 1997 - continue from 2003

