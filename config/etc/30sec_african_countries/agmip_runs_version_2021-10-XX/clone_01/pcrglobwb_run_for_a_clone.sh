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

# get the aguments
INI_FILE=$1
MAIN_OUTPUT_DIR=$2
STARTING_DATE=$3
END_DATE=$4
MAIN_INITIAL_STATE_FOLDER=$5
DATE_FOR_INITIAL_STATES=$6
PRECIPITATION_FORCING_FILE=$7
TEMPERATURE_FORCING_FILE=$8
REF_POT_ET_FORCING_FILE=$9
BASEFLOW_EXPONENT=${10}
PCRGLOBWB_MODEL_SCRIPT_FOLDER=${11}
NUMBER_OF_SPINUP_YEARS=${12}

USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI=${13}
ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE=${14}
DAILY_GROUNDWATER_RECHARGE_INI=${15}

# load all software needed
cd /rds/general/user/esutanud/home/
. load_all_default.sh

# set number of threads for pcraster
export PCRASTER_NR_WORKER_THREADS=24

#~ # do not use workers/threads for pcraster
#~ unset PCRASTER_NR_WORKER_THREADS


# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


# run the model (for a specific clone)

python3 deterministic_runner_with_arguments.py ${INI_FILE} debug -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} -use_max_fossil_gw_ini ${USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI} -est_stor_gw_from_rch ${ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE} -day_gw_rch_ini ${DAILY_GROUNDWATER_RECHARGE_INI} 
