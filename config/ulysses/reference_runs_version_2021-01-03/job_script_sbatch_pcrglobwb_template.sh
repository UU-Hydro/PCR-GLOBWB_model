#!/bin/bash 
#SBATCH -N 1
#SBATCH -n 96
#SBATCH -p gpu

#~ #SBATCH -t 1:00

#SBATCH -J pgb_uly_spinup_and_actual_runs

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

#SBATCH --export INI_FILE=setup_6arcmin.ini,MAIN_OUTPUT_DIR="/scratch/pcrglobwb_ulysses_reference_runs/test/",STARTING_DATE="1981-01-01",END_DATE="2000-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/spinup/global/states/",DATE_FOR_INITIAL_STATES="1981-12-31",BASEFLOW_EXPONENT="1.0"

set -x

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER="/perm/mo/nest/ulysses/src/edwin/ulysses_pgb_source/model/"
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

# set the configuration file (*.ini) that will be used (assumption: the .ini file is located within the same directory as this job, i.e. ${PBS_O_WORKDIR})
#~ INI_FILE=${PBS_O_WORKDIR}/"setup_6arcmin_uly-et0_gmd-lcv_on_cca_with_initial_states.ini"
#~ INI_FILE=${PBS_O_WORKDIR}/${INI_FILE}
INI_FILE=${SLURM_SUBMIT_DIR}/${INI_FILE}

# set the output folder
MAIN_OUTPUT_DIR=${MAIN_OUTPUT_DIR}

# set the starting and end simulation dates
STARTING_DATE=${STARTING_DATE}
END_DATE=${END_DATE}

# set the initial conditions (folder and time stamp for the files)
MAIN_INITIAL_STATE_FOLDER=${MAIN_INITIAL_STATE_FOLDER}
DATE_FOR_INITIAL_STATES=${DATE_FOR_INITIAL_STATES}

# set the forcing files
#~ PRECIPITATION_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/precipitation_daily_01_2000.nc"
#~ TEMPERATURE_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/tavg_01_2000.nc"
#~ REF_POT_ET_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/pet_01_2000.nc"
PRECIPITATION_FORCING_FILE="NONE"
TEMPERATURE_FORCING_FILE="NONE"
REF_POT_ET_FORCING_FILE="NONE"

# baseflow exponent
BASEFLOW_EXPONENT=${BASEFLOW_EXPONENT}


# go to the folder that contain the bash script that will be submitted using aprun
# - using the folder that contain this job script 
#~ cd ${PBS_O_WORKDIR}
cd ${SLURM_SUBMIT_DIR}

# make the run for every clone using aprun
bash pcrglobwb_runs_71_clones.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE} ${BASEFLOW_EXPONENT} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# wait for 30 sec 
sleep 30

set +x
