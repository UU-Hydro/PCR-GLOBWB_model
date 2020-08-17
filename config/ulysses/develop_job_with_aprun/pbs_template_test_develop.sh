#!/bin/bash 
#PBS -N test-npd
#PBS -q np
#PBS -l EC_nodes=1
#PBS -l EC_total_tasks=72
#PBS -l EC_hyperthreads=2
#PBS -l EC_billing_account=c3s432l3

#~ #PBS -l walltime=48:00:00
#~ #PBS -l walltime=8:00
#PBS -l walltime=1:00:00

#PBS -M hsutanudjajacchms99@yahoo.com


set -x

# set the configuration file (*.ini) that will be used 
INI_FILE="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/ulysses/develop_job_with_aprun/setup_6arcmin_test_version_2020-08-XX_develop.ini"

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



# make the run for every clone
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/ulysses/develop_job_with_aprun/
aprun -N $EC_tasks_per_node -n $EC_total_tasks -j $EC_hyperthreads bash pcrglobwb_runs.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE}

cd ${MAIN_OUTPUT_DIR}
mkdir test 
cd test
pwd

set +x
