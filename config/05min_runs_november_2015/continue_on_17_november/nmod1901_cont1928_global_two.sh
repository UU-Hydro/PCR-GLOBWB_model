#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p normal                                                                                                                                                                              
#SBATCH --constraint=haswell

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB.py ../config/05min_runs_november_2015/continue_on_17_november/setup_05min_pcrglobwb_only_cartesius_parallel_from_2017_continue_global_two.ini no_debug

# pcrglobwb only (without modflow) - start from 1901 - continue from 1919 - continue from 1928 - but only for the clones: M23,M51,M04,M06,M10,M02,M45,M50,M47,M35,M24,M01,M36,M53,M33,M43,M34,M37,M31,M32,M28,M30,M29

