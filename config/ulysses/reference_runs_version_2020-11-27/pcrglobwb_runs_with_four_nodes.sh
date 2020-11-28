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

# use 4 working threads
export PCRASTER_NR_WORKER_THREADS=4


# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


#~ # - for testing, run only clone 3
#~ if [ $ALPS_APP_PE -gt 2 ]
#~ then
#~ if [ $ALPS_APP_PE -lt 4 ]
#~ then
#~ set -x
#~ CLONENUMBER=$ALPS_APP_PE
#~ CLONE_CODE=`printf %d $CLONENUMBER`
#~ python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
#~ echo $CLONENUMBER
#~ echo ${CLONE_CODE}
#~ set +x
#~ fi
#~ fi



# run the model for all clones, from 1 to 71
# - splitted into four nodes

# - first node: 1 to 18
if [ $ALPS_APP_PE -gt 0 ]
then
if [ $ALPS_APP_PE -lt 19 ]
then
CLONENUMBER=$ALPS_APP_PE
CLONE_CODE=`printf %d $CLONENUMBER`
# - without forcing
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} 
#~ # - with forcing
#~ python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
fi
fi

# - second node: 19 to 36
if [ $ALPS_APP_PE -gt 72 ]
then
CLONENUMBER=$((ALPS_APP_PE-72))
if [ $CLONENUMBER -gt 18 ]
then
if [ $CLONENUMBER -lt 37 ]
then
CLONE_CODE=`printf %d ${CLONENUMBER}`
# - without forcing
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} 
#~ # - with forcing
#~ python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
fi
fi
fi

# - third node: 37 to 54
if [ $ALPS_APP_PE -gt 144 ]
then
CLONENUMBER=$((ALPS_APP_PE-144))
if [ $CLONENUMBER -gt 36 ]
then
if [ $CLONENUMBER -lt 55 ]
then
CLONE_CODE=`printf %d ${CLONENUMBER}`
# - without forcing
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} 
#~ # - with forcing
#~ python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
fi
fi
fi

# - fourth node: 55 to 71, 72 for merging
if [ $ALPS_APP_PE -gt 216 ]-
then
CLONENUMBER=$((ALPS_APP_PE-216))
if [ $CLONENUMBER -gt 54 ]
then
if [ $CLONENUMBER -lt 72 ]
then
CLONE_CODE=`printf %d ${CLONENUMBER}`
# - without forcing
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} 
#~ # - with forcing
#~ python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -rpetff ${REF_POT_ET_FORCING_FILE}
echo $CLONENUMBER
echo ${CLONE_CODE}
fi
fi
if [ $CLONENUMBER -eq 72 ]
then
# merging process
python3 deterministic_runner_merging_ulysses.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES}
fi
fi
