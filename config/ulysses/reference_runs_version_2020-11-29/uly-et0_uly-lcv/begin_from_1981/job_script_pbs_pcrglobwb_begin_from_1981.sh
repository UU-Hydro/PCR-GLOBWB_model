#!/bin/bash 
#PBS -q np
#PBS -l EC_nodes=4
#PBS -l EC_total_tasks=288
#PBS -l EC_hyperthreads=2
#PBS -l EC_billing_account=c3s432l3

#PBS -l walltime=48:00:00
#~ #PBS -l walltime=8:00
#~ #PBS -l walltime=1:00:00
#~ #PBS -l walltime=18:00:00

#PBS -M hsutanudjajacchms99@yahoo.com

#PBS -N uet_uly_1981-2000

set -x

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER="/perm/mo/nest/ulysses/src/edwin/ulysses_pgb_source/model/"
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

# set the configuration file (*.ini) that will be used (assumption: the .ini file is located within the same directory as this job, i.e. ${PBS_O_WORKDIR})
INI_FILE=${PBS_O_WORKDIR}/"setup_6arcmin_uly-et0_uly-lcv_on_cca_with_initial_states.ini"

# set the output folder
MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_uly-lcv/begin_from_1981/"

# set the starting and end simulation dates
STARTING_DATE=1981-01-01
END_DATE=2000-12-31

# set the initial conditions (folder and time stamp for the files)
#~ MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/data/pcrglobwb_input_ulysses/develop/global_06min/initialConditions/dummy_version_2020-10-19/global/states_1800_rows/"
#~ DATE_FOR_INITIAL_STATES=1981-12-31
#~ MAIN_INITIAL_STATE_FOLDER="NONE"
#~ DATE_FOR_INITIAL_STATES="NONE"
MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_uly-lcv/spinup/begin_from_1981/global/states/"
DATE_FOR_INITIAL_STATES="1981-12-31"

#~ # set the forcing files
#~ PRECIPITATION_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/precipitation_daily_01_2000.nc"
#~ TEMPERATURE_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/tavg_01_2000.nc"
#~ REF_POT_ET_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/pet_01_2000.nc"
PRECIPITATION_FORCING_FILE="NONE"
TEMPERATURE_FORCING_FILE="NONE"
REF_POT_ET_FORCING_FILE="NONE"


# go to the folder that contain the bash script that will be submitted using aprun
# - using the folder that contain this pbs job script 
cd ${PBS_O_WORKDIR}

# make the run for every clone using aprun
aprun -N $EC_tasks_per_node -n $EC_total_tasks -j $EC_hyperthreads bash pcrglobwb_runs_with_four_nodes.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


set +x
