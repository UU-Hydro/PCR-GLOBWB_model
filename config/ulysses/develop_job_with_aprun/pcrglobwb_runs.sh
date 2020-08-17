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

# set the configuration file (*.ini) that will be used 
INI_FILE="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/setup_6arcmin_test_version_2020-08-XX_develop.ini"

# set the output folder
MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/test_aprun_develop/"

#~ # - clear the output folder
#~ rm -rf ${MAIN_OUTPUT_DIR}

# set the starting and end simulation dates
STARTING_DATE=1996-01-01
END_DATE=1996-01-31

# set the initial conditions (folder and time stamp for the files)
MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_output_version_2020-08-14/begin_from_1981/global/states/"
DATE_FOR_INITIAL_STATES=1995-12-31

# set the forcing files
PRECIPITATION_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/precipitation_daily_01_1996.nc"
TEMPERATURE_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/tavg_01_1996.nc"
REF_POT_ET_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/pet_01_1996.nc"



# load using modules on cca (or ccb)
module load python3/3.6.10-01
module load pcraster/4.3.0
module load gdal/3.0.4


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

# run the model for all clone, from 1 to 54
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
