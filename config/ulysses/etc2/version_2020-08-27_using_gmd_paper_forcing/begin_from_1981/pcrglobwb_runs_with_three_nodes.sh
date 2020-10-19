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

# use at least 8 workers
export PCRASTER_NR_WORKER_THREADS=4

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


# run the model for all clones, from 1 to 54

# - splitted into two nodes

# - first node
if [ $ALPS_APP_PE -gt 0 ]
then
if [ $ALPS_APP_PE -lt 19 ]
then
#~ set -x
CLONENUMBER=$ALPS_APP_PE
CLONE_CODE=`printf %d $CLONENUMBER`
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
#~ set +x
fi
fi

# - second node
if [ $ALPS_APP_PE -gt 72 ]
then
CLONENUMBER=$((ALPS_APP_PE-72))
if [ $CLONENUMBER -gt 18 ]
then
if [ $CLONENUMBER -lt 37 ]
then
#~ set -x
CLONE_CODE=`printf %d ${CLONENUMBER}`
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
#~ set +x
fi
fi
fi

# - third node
if [ $ALPS_APP_PE -gt 144 ]
then
CLONENUMBER=$((ALPS_APP_PE-144))
if [ $CLONENUMBER -gt 36 ]
then
if [ $CLONENUMBER -lt 55 ]
#~ if [ $CLONENUMBER -lt 54 ] # for 5 arcmin gmd run (containing only 53 clones)
then
#~ set -x
CLONE_CODE=`printf %d ${CLONENUMBER}`
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
#~ set +x
fi
fi
fi
