#!/bin/bash

#~ # Submit the first job and save the JobID as JOBONE
#~ JOBONE=$(qsub program1.pbs)
#~ # Submit the second job, use JOBONE as depend, save JobID
#~ JOBTWO=$(qsub -W depend=afterok:$JOBONE program2.pbs)
#~ # Submit last job using JOBTWO as depend, do not need to save the JobID
#~ qsub -W depend=afterok:$JOBTWO program3.pbs

set -x


JOB_NAME="chrp_kw"
INI_FILE="setup_05min_africa_version_chirps_kinematicwave.ini"
GENERAL_MAIN_OUTPUT_DIR="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-07-XX/africa_05min/chirps_kinematicwave/"
STARTING_YEAR=2011
END_YEAR=2019
NUMBER_OF_SPINUP_YEARS="5"
MAIN_INITIAL_STATE_FOLDER="/rds/general/user/esutanud/projects/arise/live/HydroModelling/edwin/pcrglobwb_output_africa/version_2021-07-XX/africa_05min/chirps_accutraveltime/_spinup/with_1981/global/states/"
DATE_FOR_INITIAL_STATES="1981-12-31"


# spinup

SUB_JOBNAME=${JOB_NAME}_spinup_dummy
MAIN_OUTPUT_DIR=${GENERAL_MAIN_OUTPUT_DIR}/_spinup/with_${STARTING_YEAR}/
STARTING_DATE=${STARTING_YEAR}-01-01
END_DATE=${STARTING_YEAR}-12-31
SPIN_UP=$(qsub -N "${SUB_JOBNAME}" -v INI_FILE="${INI_FILE}",MAIN_OUTPUT_DIR="${MAIN_OUTPUT_DIR}",STARTING_DATE="${STARTING_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${MAIN_INITIAL_STATE_FOLDER}",DATE_FOR_INITIAL_STATES="${DATE_FOR_INITIAL_STATES}",NUMBER_OF_SPINUP_YEARS="${NUMBER_OF_SPINUP_YEARS}" pbs_job_script_for_a_run_dummy.sh)

# save and use the following variables for the next run/job
PREVIOUS_JOB=${SPIN_UP}
MAIN_INITIAL_STATE_FOLDER=${MAIN_OUTPUT_DIR}/global/states/
DATE_FOR_INITIAL_STATES=${END_DATE}



# number of years
let NUMOFYEARS=${END_YEAR}-${STARTING_YEAR}+1

# we will run for every 3-year period
let NUMOFSUBRUNS=${NUMOFYEARS}/3

# the run for every 3-year period
for i in $( eval echo {1..$NUMOFSUBRUNS} )

do

let STAYEAR=${STARTING_YEAR}+${i}*3-3
let ENDYEAR=${STAYEAR}+3-1

SUB_JOBNAME=${JOB_NAME}_${STAYEAR}-${ENDYEAR}
MAIN_OUTPUT_DIR=${GENERAL_MAIN_OUTPUT_DIR}/${STAYEAR}-${ENDYEAR}/
STARTING_DATE=${STAYEAR}-01-01
END_DATE=${ENDYEAR}-12-31

# dummy jobs/runs for the years before 2011
if [ ${STAYEAR} -lt 2011 ]
then
CURRENT_JOB=$(qsub -N "${SUB_JOBNAME}" -W depend=afterany:${PREVIOUS_JOB} -v INI_FILE="${INI_FILE}",MAIN_OUTPUT_DIR="${MAIN_OUTPUT_DIR}",STARTING_DATE="${STARTING_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${MAIN_INITIAL_STATE_FOLDER}",DATE_FOR_INITIAL_STATES="${DATE_FOR_INITIAL_STATES}",NUMBER_OF_SPINUP_YEARS="0" pbs_job_script_for_a_run_dummy.sh)
fi

# continue the runs for the years 2011 and so on
if [ ${STAYEAR} -gt 2010 ]
then
CURRENT_JOB=$(qsub -N "${SUB_JOBNAME}" -W depend=afterany:${PREVIOUS_JOB} -v INI_FILE="${INI_FILE}",MAIN_OUTPUT_DIR="${MAIN_OUTPUT_DIR}",STARTING_DATE="${STARTING_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${MAIN_INITIAL_STATE_FOLDER}",DATE_FOR_INITIAL_STATES="${DATE_FOR_INITIAL_STATES}",NUMBER_OF_SPINUP_YEARS="0" pbs_job_script_for_a_run.sh)
fi

# save and use the following variables for the next run/job
PREVIOUS_JOB=${CURRENT_JOB}
MAIN_INITIAL_STATE_FOLDER=${MAIN_OUTPUT_DIR}/global/states/
DATE_FOR_INITIAL_STATES=${END_DATE}

done


set +x
