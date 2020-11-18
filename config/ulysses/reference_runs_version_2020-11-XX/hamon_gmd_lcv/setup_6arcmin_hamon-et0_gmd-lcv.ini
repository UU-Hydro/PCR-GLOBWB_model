#!/bin/bash
#SBATCH -N 1
#SBATCH -n 71
#~ #SBATCH -t 240:00:00

#SBATCH -p defq
#SBATCH -J ham_gmd

#~ #SBATCH --exclusive

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


set -x

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER="/perm/mo/nest/ulysses/src/edwin/ulysses_pgb_source/model/"
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

# set the configuration file (*.ini) that will be used (assumption: the .ini file is located within the same directory as this job, i.e. ${PBS_O_WORKDIR})
#~ INI_FILE="setup_6arcmin_test_version_2020-08-XX_develop.ini"
#~ INI_FILE=${PBS_O_WORKDIR}/"setup_6arcmin_version_develop.ini"
#~ INI_FILE="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/ulysses/reference_runs_version_2020-11-XX/hamon_gmd_lcv/setup_6arcmin_hamon_gmd_lcv_develop.ini"
INI_FILE=${SLURM_SUBMIT_DIR}/"setup_6arcmin_hamon-et0_gmd-lcv.ini"

# set the output folder
#~ MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/test_monthly_runs_develop/"
MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2020-11-18/hamon-et0_gmd-lcv/begin_from_1980/"

# set the starting and end simulation dates
STARTING_DATE=1980-01-01
END_DATE=2019-12-31

# set the initial conditions (folder and time stamp for the files)
MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/data/pcrglobwb_input_ulysses/develop/global_06min/initialConditions/dummy_version_2020-10-19/global/states_1800_rows/"
DATE_FOR_INITIAL_STATES=1981-12-31


#~ # set the forcing files
#~ PRECIPITATION_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/precipitation_daily_01_2000.nc"
#~ TEMPERATURE_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/tavg_01_2000.nc"
#~ REF_POT_ET_FORCING_FILE="/scratch/mo/nest/ulysses/data/meteo/era5land/2000/01/pet_01_2000.nc"
PRECIPITATION_FORCING_FILE="NONE"
TEMPERATURE_FORCING_FILE="NONE"
REF_POT_ET_FORCING_FILE="NONE"


# for runs with sbatch (on eejit)
# - go to the folder that contain the bash script that will be used
# - using the folder that contain this pbs job script 
cd ${SLURM_SUBMIT_DIR}
# - make the run for every clone using aprun
bash pcrglobwb_runs_71_clones.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


#~ # for runs with pbs and aprun
#~ # - go to the folder that contain the bash script that will be submitted using aprun
#~ # - using the folder that contain this pbs job script 
#~ cd ${PBS_O_WORKDIR}
#~ # - make the run for every clone using aprun
#~ aprun -N $EC_tasks_per_node -n $EC_total_tasks -j $EC_hyperthreads bash pcrglobwb_runs.sh ${INI_FILE} ${MAIN_OUTPUT_DIR} ${STARTING_DATE} ${END_DATE} ${MAIN_INITIAL_STATE_FOLDER} ${DATE_FOR_INITIAL_STATES} ${PRECIPITATION_FORCING_FILE} ${TEMPERATURE_FORCING_FILE} ${REF_POT_ET_FORCING_FILE} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}


set +x
