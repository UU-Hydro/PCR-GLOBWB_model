#!/bin/bash 

#~ echo "Arg 0: $0"
#~ echo "Arg 1: $1"
#~ echo "Arg 2: $2"
#~ 
#~ for arg in "$@"
#~ do
    #~ echo "$arg"
#~ done


set -x

#~ # get the aguments
#~ INI_FILE=$1
#~ MAIN_OUTPUT_DIR=$2
#~ STARTING_DATE=$3
#~ END_DATE=$4
#~ MAIN_INITIAL_STATE_FOLDER=$5
#~ DATE_FOR_INITIAL_STATES=$6
#~ PRECIPITATION_FORCING_FILE=$7
#~ TEMPERATURE_FORCING_FILE=$8
#~ REF_POT_ET_FORCING_FILE=$9
#~ BASEFLOW_EXPONENT=${10}
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER=${11}

INI_FILE="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/aqueduct_2021/version_2021-04-30/setup_05min_gmd_isimip_3a_forcing_update_parameters_develop.ini"
MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_develop/test/"
STARTING_DATE="1979-01-01"
END_DATE="1980-12-31"
PRECIPITATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5/gswp3-w5e5_obsclim_pr_global_daily_1971_1980.nc"
TEMPERATURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5/gswp3-w5e5_obsclim_tas_global_daily_1971_1980.nc"
PRESSURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5/gswp3-w5e5_obsclim_tasmax_global_daily_1971_1980.nc"
WIND_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5/gswp3-w5e5_obsclim_sfcwind_global_daily_1971_1980.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5/gswp3-w5e5_obsclim_rsds_global_daily_1971_1980.nc"
RELATIVE_HUMIDITY_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5/gswp3-w5e5_obsclim_hurs_global_daily_1971_1980.nc"
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

#~ sutan101@gpu038.cluster:/scratch/depfg/sutan101/data/isimip_forcing/isimip3a/copied_on_2020-12-XX/GSWP3-W5E5$ ls -lah *1980*
#~ -rw-r--r-- 1 sutan101 depfg 2.4G Dec  7 05:58 gswp3-w5e5_obsclim_hurs_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.6G Dec  7 06:03 gswp3-w5e5_obsclim_huss_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.1G Dec  7 06:08 gswp3-w5e5_obsclim_pr_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.0G Dec  7 06:13 gswp3-w5e5_obsclim_ps_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.4G Dec  7 06:19 gswp3-w5e5_obsclim_rlds_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.4G Dec  7 06:25 gswp3-w5e5_obsclim_rsds_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.7G Dec  7 06:32 gswp3-w5e5_obsclim_sfcwind_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.0G Dec  7 06:39 gswp3-w5e5_obsclim_tas_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.0G Dec  7 06:44 gswp3-w5e5_obsclim_tasmax_global_daily_1971_1980.nc
#~ -rw-r--r-- 1 sutan101 depfg 2.0G Dec  7 06:49 gswp3-w5e5_obsclim_tasmin_global_daily_1971_1980.nc


# load modules on eejit
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh

#~ # - unset pcraster working threads
#~ unset PCRASTER_NR_WORKER_THREADS

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# run the model for all clones, from 1 to 53

# - for testing
#~ for i in {2..3}
#~ for i in {2..2}

for i in {1..53}

do

CLONE_CODE=${i}
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

done


#~ # merging process
#~ python3 deterministic_runner_merging_ulysses.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} &

wait

