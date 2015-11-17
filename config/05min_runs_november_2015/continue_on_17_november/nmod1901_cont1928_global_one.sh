#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:00:00 
#SBATCH -p fat                                                                                                                                                                              

cd /home/edwin/github/edwinkost/PCR-GLOBWB/model
python parallelPCR-GLOBWB.py ../config/05min_runs_november_2015/continue_on_17_november/setup_05min_pcrglobwb_only_cartesius_parallel_from_2017_continue_global_one.ini no_debug

# pcrglobwb only (without modflow) - start from 1901 - continue from 1919 - continue from 1928 - but only for the clones: M17,M19,M26,M13,M18,M20,M05,M03,M46,M21,M27,M49,M16,M44,M52,M25,M09,M08,M11,M42,M12,M39,M07,M15,M38,M48,M40,M41,M22,M14

