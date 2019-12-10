#!/bin/bash

#SBATCH -N 1                                                                                                                     
#~ #SBATCH -t 240:00:00                                                                                                             

#~ #SBATCH -J test_brute-force                                                                                               

#SBATCH --exclusive
#SBATCH -n 96                                                                                                                    

#SBATCH -p defq                                                                                                                    

#~ # mail alert at start, end and abortion of execution
#~ #SBATCH --mail-type=ALL
#~ 
#~ # send mail to this address
#~ #SBATCH --mail-user=edwinkost@gmail.com

####################################################################################
# SET THE VARIABLES
####################################################################################
INI_FILE_FOR_SPINUP=/home/edwinhs/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/opendap_development/30min_for_jessica/setup_30min_RM_using-local-files_version_2019_10_beta_1_on_eejit_brute-force_spinup.ini


set -x

# using pcraster 4.3.0 dev
# - activate conda env with python3 that is compatible for running pcrglobwb (using pcraster >= 4.2.1)
source activate py3_pcrglobwb_fixing
# - using pcraster 4.3 development version (NOTE: continuously developed/compiled by Oliver)
source /scratch/depfg/pcraster/pcraster-4.3.0.sh

# test pcraster
pcrcalc

# go to the script directory
cd ~/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

# start the spin-up run
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 -0.5 -0.5 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 -0.5-0.5 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 -0.5 0 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 -0.5 0.5 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 -0.5 54 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 0 -0.5 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 0 0 1.0 0.5 1.0 0.5 Default &
python deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} spinup_test_1 0.5 0 0.5 1.0 0.5 1.0 0.5 Default &
wait

# get the initial storGroundwater based on the spin-up

# start the actual run



set +x
