#!/bin/bash 

#~ #PBS -l select=1:ncpus=48:mem=124gb
#~ #PBS -l walltime=72:00:00

#~ #PBS -l select=1:ncpus=256:mem=620gb
#~ #PBS -l walltime=72:00:00

#~ Express queue exp_48_128_72:
  #~ Permitted job configurations:
   #~ -lselect=1-16:ncpus=24-48:mem=252gb -lwalltime=240:00:00

#~ #PBS -l select=1:ncpus=48:mem=252gb
#~ #PBS -l walltime=72:00:00

#PBS -l select=1:ncpus=48:mem=124gb
#PBS -l walltime=72:00:00

#PBS -q express -P exp-00044

#~ #PBS -l select=1:ncpus=8:mem=96gb
#~ #PBS -l walltime=29:00

#PBS -N pgb_af_parl_test

#PBS -v INI_FILE="setup.ini",MAIN_OUTPUT_DIR="/scratch/out/",STARTING_DATE="1982-01-01",END_DATE="2000-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/prev_out/states/",DATE_FOR_INITIAL_STATES="1981-12-31",NUMBER_OF_SPINUP_YEARS="0",USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI="False",ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE="False",DAILY_GROUNDWATER_RECHARGE_INI="NONE"


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

# NUMBER_OF_SPINUP_YEARS
NUMBER_OF_SPINUP_YEARS=${NUMBER_OF_SPINUP_YEARS}

# USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI
USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI=${USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI}

# ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE
ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE=${ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE}

# DAILY_GROUNDWATER_RECHARGE_INI
DAILY_GROUNDWATER_RECHARGE_INI=${DAILY_GROUNDWATER_RECHARGE_INI}


#~ # for testing with bash
#~ PBS_O_WORKDIR=$(pwd)
#~ echo ${PBS_O_WORKDIR}
#~ INI_FILE="setup_30sec_senegal-basin_version_develop.ini"
#~ INI_FILE=${PBS_O_WORKDIR}/${INI_FILE}
#~ MAIN_OUTPUT_DIR="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-07-XX/senegal_30sec/test/test_with_bash/"
#~ STARTING_DATE=1981-01-01
#~ END_DATE=1981-12-31
#~ MAIN_INITIAL_STATE_FOLDER="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-05-31/africa_05min/africa_accutraveltime/states/"
#~ DATE_FOR_INITIAL_STATES="1981-12-31"
#~ PRECIPITATION_FORCING_FILE="NONE"
#~ TEMPERATURE_FORCING_FILE="NONE"
#~ REF_POT_ET_FORCING_FILE="NONE"
#~ BASEFLOW_EXPONENT="NONE"
#~ NUMBER_OF_SPINUP_YEARS="5"
#~ USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI="True"
#~ ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE="False"
#~ DAILY_GROUNDWATER_RECHARGE_INI="NONE"


# run the script
cd ${PBS_O_WORKDIR}
pwd
bash pcrglobwb_run_for_a_clone.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE} ${BASEFLOW_EXPONENT} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} ${NUMBER_OF_SPINUP_YEARS} ${USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI} ${ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE} ${DAILY_GROUNDWATER_RECHARGE_INI}

#~ # wait for 30 sec 
#~ sleep 30

set +x


