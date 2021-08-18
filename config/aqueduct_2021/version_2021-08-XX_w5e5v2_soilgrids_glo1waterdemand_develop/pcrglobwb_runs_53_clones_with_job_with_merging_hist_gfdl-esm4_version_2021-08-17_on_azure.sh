#!/bin/bash 


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


# configuration (.ini) file
INI_FILE=$(pwd)/"setup_05min_historical_version_2021-08-17.ini"


# pcrglobwb output folder
MAIN_OUTPUT_DIR="/datadrive/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-08-17_hist_gfdl-esm4/"


# starting and end dates
STARTING_DATE="1978-01-01"
END_DATE="2014-12-31"


# meteorological forcing files
RELATIVE_HUMIDITY_FORCING_FILE="/datadrive/pcrglobwb_input/data/isimip_forcing/isimip3b_version_2021-05-XX/gfdl-esm4_w5e5_historical_hurs_global_daily_1850_2014.nc"
PRECIPITATION_FORCING_FILE="/datadrive/pcrglobwb_input/data/isimip_forcing/isimip3b_version_2021-05-XX/gfdl-esm4_w5e5_historical_pr_global_daily_1850_2014.nc"
PRESSURE_FORCING_FILE="/datadrive/pcrglobwb_input/data/isimip_forcing/isimip3b_version_2021-05-XX/gfdl-esm4_w5e5_historical_ps_global_daily_1850_2014.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/datadrive/pcrglobwb_input/data/isimip_forcing/isimip3b_version_2021-05-XX/gfdl-esm4_w5e5_historical_rsds_global_daily_1850_2014.nc"
WIND_FORCING_FILE="/datadrive/pcrglobwb_input/data/isimip_forcing/isimip3b_version_2021-05-XX/gfdl-esm4_w5e5_historical_sfcwind_global_daily_1850_2014.nc"
TEMPERATURE_FORCING_FILE="/datadrive/pcrglobwb_input/data/isimip_forcing/isimip3b_version_2021-05-XX/gfdl-esm4_w5e5_historical_tas_global_daily_1850_2014.nc"


PCRGLOBWB_MODEL_SCRIPT_FOLDER=~/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# load modules on azure
source activate pcrglobwb_python3


pcrcalc

# - unset pcraster working threads
unset PCRASTER_NR_WORKER_THREADS

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}
pwd


# run the model for all clones, from 1 to 53

#~ # - for testing
#~ for i in {2..2}
#~ for i in {2..3}

for i in {1..53}

do

CLONE_CODE=${i}
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} &

done


# merging process
python3 deterministic_runner_merging_with_arguments.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} &


wait

