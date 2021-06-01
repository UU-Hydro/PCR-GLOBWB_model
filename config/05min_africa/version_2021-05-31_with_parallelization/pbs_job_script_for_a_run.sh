#!/bin/bash 

#~ #PBS -l select=1:ncpus=48:mem=124gb
#~ #PBS -l walltime=72:00:00

#PBS -l select=1:ncpus=256:mem=124gb
#PBS -l walltime=72:00:00

#PBS -q express -P exp-00044

#PBS -N pgb_af_parl_test

#PBS -v INI_FILE="setup.ini",MAIN_OUTPUT_DIR="/scratch/out/",STARTING_DATE="1982-01-01",END_DATE="2000-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/prev_out/states/",DATE_FOR_INITIAL_STATES="1981-12-31"


# for testing
INI_FILE="setup_05min_africa_version_develop.ini"

# set the output folder
MAIN_OUTPUT_DIR="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-05-31/africa_05min/africa_with_parallelization_accutraveltime_test/"

# set the starting and end simulation dates
STARTING_DATE="1981-01-01"
END_DATE="1981-12-31"

# set the initial conditions (folder and time stamp for the files)
MAIN_INITIAL_STATE_FOLDER="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-05-31/africa_05min/africa_kinematicwave/states/"
DATE_FOR_INITIAL_STATES="1981-12-31"


set -x

# set the folder that contain PCR-GLOBWB model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/rds/general/user/esutanud/home/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

# set the configuration file (*.ini) that will be used (assumption: the .ini file is located within the same directory as this job, i.e. ${PBS_O_WORKDIR})
INI_FILE=${PBS_O_WORKDIR}/${INI_FILE}

# set the output folder
MAIN_OUTPUT_DIR=${MAIN_OUTPUT_DIR}

# set the starting and end simulation dates
STARTING_DATE=${STARTING_DATE}
END_DATE=${END_DATE}

# set the initial conditions (folder and time stamp for the files)
MAIN_INITIAL_STATE_FOLDER=${MAIN_INITIAL_STATE_FOLDER}
DATE_FOR_INITIAL_STATES=${DATE_FOR_INITIAL_STATES}

# set the forcing files
PRECIPITATION_FORCING_FILE="NONE"
TEMPERATURE_FORCING_FILE="NONE"
REF_POT_ET_FORCING_FILE="NONE"

# baseflow exponent
BASEFLOW_EXPONENT="NONE"


# run the script
cd ${PBS_O_WORKDIR}
bash pcrglobwb_runs_africa_39_clones.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE} ${BASEFLOW_EXPONENT} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# wait for 30 sec 
sleep 30

set +x


