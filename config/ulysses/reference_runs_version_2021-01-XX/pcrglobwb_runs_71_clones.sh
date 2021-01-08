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


#~ # load using modules on cca (or ccb)
#~ module load python3/3.6.10-01
#~ module load pcraster/4.3.0
#~ module load gdal/3.0.4
#~ # - use 4 working threads
#~ export PCRASTER_NR_WORKER_THREADS=4


# load modules on eejit
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh
# - unset pcraster working threads
unset PCRASTER_NR_WORKER_THREADS




# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


# run the model for all clones, from 1 to 71

#~ # - for testing
#~ for i in {2..3}

for i in {1..71}

do

CLONE_CODE=${i}
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -bfexp ${BASEFLOW_EXPONENT} &


done


# merging process
python3 deterministic_runner_merging_ulysses.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} &

wait

