#!/bin/bash

set -x

JOB_NAME="pgb_af_parl_ac"
INI_FILE="setup_05min_africa_version_2021-06-02_accutraveltime.ini"

GENERAL_MAIN_OUTPUT_DIR="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-06-02/africa_05min/africa_with_parallelization_accutraveltime/"

MAIN_INITIAL_STATE_FOLDER=/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-06-02/africa_05min/africa_with_parallelization_accutraveltime/2017/global/states/
DATE_FOR_INITIAL_STATES="2017-12-31"

SUB_JOBNAME=${JOB_NAME}_2018-2019
MAIN_OUTPUT_DIR=${GENERAL_MAIN_OUTPUT_DIR}/2018-2019/
STARTING_DATE=2018-01-01
END_DATE=2019-12-31
CURRENT_JOB=$(qsub -N "${SUB_JOBNAME}" -v INI_FILE="${INI_FILE}",MAIN_OUTPUT_DIR="${MAIN_OUTPUT_DIR}",STARTING_DATE="${STARTING_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${MAIN_INITIAL_STATE_FOLDER}",DATE_FOR_INITIAL_STATES="${DATE_FOR_INITIAL_STATES}",NUMBER_OF_SPINUP_YEARS="0" pbs_job_script_for_a_run.sh)

set +x
