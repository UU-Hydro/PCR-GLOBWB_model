#!/bin/bash

#~ # Submit the first job and save the JobID as JOBONE
#~ JOBONE=$(qsub program1.pbs)
#~ # Submit the second job, use JOBONE as depend, save JobID
#~ JOBTWO=$(qsub -W depend=afterok:$JOBONE program2.pbs)
#~ # Submit last job using JOBTWO as depend, do not need to save the JobID
#~ qsub -W depend=afterok:$JOBTWO program3.pbs

set -x


JOB_NAME="pgb_af_parl"
INI_FILE="setup_05min_africa_version_2021-06-01_kinemacticwave.ini"
GENERAL_MAIN_OUTPUT_DIR="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-06-01/africa_05min/africa_with_parallelization_kinematicwave/"
STARTING_YEAR=1981
END_YEAR=2019
NUMBER_OF_SPINUP_YEARS="5"
MAIN_INITIAL_STATE_FOLDER="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-05-31/africa_05min/africa_kinematicwave/states/"
DATE_FOR_INITIAL_STATES="1981-12-31"


# spinup
SUB_JOBNAME=${JOB_NAME}_spin-up
MAIN_OUTPUT_DIR=${GENERAL_MAIN_OUTPUT_DIR}/_spinup/
STARTING_DATE=${STARTING_YEAR}-01-01
END_DATE=${STARTING_YEAR}-12-31
SPIN_UP=$(qsub -N "${SUB_JOBNAME}" -v INI_FILE="${INI_FILE}",MAIN_OUTPUT_DIR="${MAIN_OUTPUT_DIR}",STARTING_DATE="${STARTING_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${MAIN_INITIAL_STATE_FOLDER}",DATE_FOR_INITIAL_STATES="${MAIN_INITIAL_STATE_FOLDER}",NUMBER_OF_SPINUP_YEARS="${NUMBER_OF_SPINUP_YEARS}" pbs_job_script_for_a_run.sh)

# save and use the following variables for the next run/job
PREVIOUS_JOB=${SPIN_UP}
MAIN_INITIAL_STATE_FOLDER=${MAIN_OUTPUT_DIR}/global/states/
DATE_FOR_INITIAL_STATES=${END_DATE}



# number of years
let NUM_OF_YEARS=${END_YEAR}-${STARTING_YEAR}+1

# the run for every year
for i in {1..${NUM_OF_YEARS}}

do

let YEAR=i+${STARTING_YEAR}-1

SUB_JOBNAME=${JOB_NAME}_${YEAR}
MAIN_OUTPUT_DIR=${GENERAL_MAIN_OUTPUT_DIR}/${YEAR}/
STARTING_DATE=${YEAR}-01-01
END_DATE=${YEAR}-12-31
CURRENT_JOB=$(qsub -N "${SUB_JOBNAME}" -W depend=afterany:${PREVIOUS_JOB} -v INI_FILE="${INI_FILE}",MAIN_OUTPUT_DIR="${MAIN_OUTPUT_DIR}",STARTING_DATE="${STARTING_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${MAIN_INITIAL_STATE_FOLDER}",DATE_FOR_INITIAL_STATES="${MAIN_INITIAL_STATE_FOLDER}",NUMBER_OF_SPINUP_YEARS="0" pbs_job_script_for_a_run.sh)

# save and use the following variables for the next run/job
PREVIOUS_JOB=${CURRENT_JOB}
MAIN_INITIAL_STATE_FOLDER=${MAIN_OUTPUT_DIR}/global/states/
DATE_FOR_INITIAL_STATES=${END_DATE}

done


set +x
