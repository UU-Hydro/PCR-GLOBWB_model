#!/bin/bash

#SBATCH -N 1                                                                                                                     
#~ #SBATCH -t 240:00:00                                                                                                             

#~ #SBATCH -J test_brute-force                                                                                               

#SBATCH --exclusive
#SBATCH -n 96                                                                                                                    

#SBATCH -p defq                                                                                                                    

#~ # mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL
#~ 
#~ # send mail to this address
#SBATCH --mail-user=j.ruijsch@uu.nl


####################################################################################
# SET THE VARIABLES
####################################################################################
PCRGLOBWB_SCRIPTDIR="/quanta1/home/5627591/pcrglobwb_brute-force/model/"
MAIN_PCR_OUTPUT_DIR="/scratch/depfg/Jessica/brute-force2/"
INI_FILE_FOR_SPINUP="/quanta1/home/5627591/pcrglobwb_brute-force/config/opendap_development/30min_for_jessica/setup_30min_RM_using-local-files_version_2019_10_beta_1_on_eejit_brute-force2_spinup.ini"
INI_FILE_FOR_ACTUAL="/quanta1/home/5627591/pcrglobwb_brute-force/config/opendap_development/30min_for_jessica/setup_30min_RM_using-local-files_version_2019_10_beta_1_on_eejit_brute-force2.ini"

#~ set -x

# using pcraster 4.3.0 dev
# - activate conda env with python3 that is compatible for running pcrglobwb (using pcraster >= 4.2.1)
#~ source activate py3_pcrglobwb
# - using pcraster 4.3 development version (NOTE: continuously developed/compiled by Oliver)
#~ source /scratch/depfg/pcraster/pcraster-4.3.0.sh

# activate edwins conda env that includes pcraster
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh

# test pcraster
pcrcalc

# go to the script directory
cd ${PCRGLOBWB_SCRIPTDIR}
pwd

# start the spin-up run
echo "START SPINUP RUNS"
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_70 0.5 0.0 0.0 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_166 1.0 -0.5 0.0 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_198 1.0 0.0 -0.5 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_210 1.0 0.0 0.0 1.0 0.5 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_213 1.0 0.0 0.0 1.0 1.0 1.0 0.5 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_214 1.0 0.0 0.0 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_215 1.0 0.0 0.0 1.0 1.0 1.0 2.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_216 1.0 0.0 0.0 1.0 1.0 1.0 3.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_218 1.0 0.0 0.0 1.0 2.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_222 1.0 0.0 0.0 1.0 3.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_230 1.0 0.0 0.5 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_262 1.0 0.5 0.0 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_358 2.0 0.0 0.0 1.0 1.0 1.0 1.0 Default &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_SPINUP} no_debug spinup_502 3.0 0.0 0.0 1.0 1.0 1.0 1.0 Default &
wait

# get the initial storGroundwater based on the spin-up
echo "CALCULATE GROUNDWATER STORAGE INITIAL"
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_70 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_166 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_198 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_210 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_213 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_214 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_215 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_216 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_218 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_222 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_230 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_262 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_358 &
bash calculate_initial_storGroundwater.sh ${MAIN_PCR_OUTPUT_DIR} spinup_502 &
wait

# start the actual run
echo "START ACTUAL RUNS"
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run70 0.5 0.0 0.0 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_70/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run166 1.0 -0.5 0.0 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_166/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run198 1.0 0.0 -0.5 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_198/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run210 1.0 0.0 0.0 1.0 0.5 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_210/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run213 1.0 0.0 0.0 1.0 1.0 1.0 0.5 ${MAIN_PCR_OUTPUT_DIR}/spinup_213/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run214 1.0 0.0 0.0 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_214/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run215 1.0 0.0 0.0 1.0 1.0 1.0 2.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_215/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run216 1.0 0.0 0.0 1.0 1.0 1.0 3.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_216/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run218 1.0 0.0 0.0 1.0 2.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_218/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run222 1.0 0.0 0.0 1.0 3.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_222/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run230 1.0 0.0 0.5 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_230/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run262 1.0 0.5 0.0 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_262/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run358 2.0 0.0 0.0 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_358/netcdf/estimate_of_initial_storGroundwater.map &
python3 deterministic_runner_glue_with_parallel_and_modflow_options_for_jessica.py ${INI_FILE_FOR_ACTUAL} no_debug actual_run502 3.0 0.0 0.0 1.0 1.0 1.0 1.0 ${MAIN_PCR_OUTPUT_DIR}/spinup_502/netcdf/estimate_of_initial_storGroundwater.map &
wait

#~ set +x
