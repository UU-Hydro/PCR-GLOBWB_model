#!/bin/bash 


set -x


# configuration (.ini) file
INI_FILE=$(pwd)/"setup_05min_ssp370_version_2021-09-16.ini"


# pcrglobwb output folder
MAIN_OUTPUT_DIR="/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-XX_ssp370_gfdl-esm4/continue_from_2051/"


# starting and end dates
STARTING_DATE="2050-01-01"
END_DATE="2100-12-31"


# meteorological forcing files
RELATIVE_HUMIDITY_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_hurs_global_daily_2015_2100.nc"
PRECIPITATION_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_pr_global_daily_2015_2100.nc"
PRESSURE_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_ps_global_daily_2015_2100.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_rsds_global_daily_2015_2100.nc"
WIND_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_sfcwind_global_daily_2015_2100.nc"
TEMPERATURE_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_tas_global_daily_2015_2100.nc"


# initial conditions - example on eejit
MAIN_INITIAL_STATE_FOLDER="/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-XX_ssp370_gfdl-esm4/begin_from_2015/global/states/"
DATE_FOR_INITIAL_STATES="2050-12-31"


# number of spinup years
NUMBER_OF_SPINUP_YEARS="0"


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
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} &



done


# merging process
python3 deterministic_runner_merging_with_arguments.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} &


wait

