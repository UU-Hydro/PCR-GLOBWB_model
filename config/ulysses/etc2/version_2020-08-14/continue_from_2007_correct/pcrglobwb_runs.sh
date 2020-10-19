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
PCRGLOBWB_MODEL_SCRIPT_FOLDER=${10}

# load using modules on cca (or ccb)
module load python3/3.6.10-01
module load pcraster/4.3.0
module load gdal/3.0.4


# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# run the model for all clones, from 1 to 54
if [ $ALPS_APP_PE -gt 0 ]
then
if [ $ALPS_APP_PE -lt 55 ]
then
#~ set -x
CLONE_CODE=`printf %d $ALPS_APP_PE`
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
#~ set +x
fi
fi
