#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python couplingPCR-GLOBWB-MODFLOW.py ../config/05min_runs_november_2015/continue_on_27_november/with_modflow/setup_05min_pcrglobwb-modflow_cartesius_from_1991_continue.ini no_debug

# pcrglobwb modflow - start from 1925 - continue from 1947 - continue from 1975 - continue from 1991
