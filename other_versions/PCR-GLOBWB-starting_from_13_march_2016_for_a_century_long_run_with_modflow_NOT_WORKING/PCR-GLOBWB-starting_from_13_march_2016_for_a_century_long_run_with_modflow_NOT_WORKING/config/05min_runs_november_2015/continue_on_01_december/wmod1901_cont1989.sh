#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python couplingPCR-GLOBWB-MODFLOW.py ../config/05min_runs_november_2015/continue_on_01_december/setup_05min_pcrglobwb-modflow_cartesius_from_1989_continue.ini no_debug

# pcrglobwb modflow - start from 1901 - continue from 1920 - continue from 1933 - continue from 1955 - continue from 1969 - continue from 1989

