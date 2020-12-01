#!/bin/bash

#~ # Submit the first job and save the JobID as JOBONE
#~ JOBONE=$(qsub program1.pbs)
#~ # Submit the second job, use JOBONE as depend, save JobID
#~ JOBTWO=$(qsub -W depend=afterok:$JOBONE program2.pbs)
#~ # Submit last job using JOBTWO as depend, do not need to save the JobID
#~ qsub -W depend=afterok:$JOBTWO program3.pbs

set -x

SPINUP=$(qsub -N nwj_wmup -v INI_FILE="setup_6arcmin_new-jgw_uly-et0_uly-lcv_on_cca_for_spinup.ini",MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/_spinup/begin_from_1981/",STARTING_DATE="1981-01-01",END_DATE="1981-12-31",MAIN_INITIAL_STATE_FOLDER="NONE",DATE_FOR_INITIAL_STATES="NONE" job_script_pbs_pcrglobwb_template.sh)

FIRST=$(qsub -N nwj_8190 -W depend=afterany:${SPINUP} -v INI_FILE="setup_6arcmin_new-jgw_uly-et0_uly-lcv_on_cca_with_initial_states.ini",MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/begin_from_1981/",STARTING_DATE="1981-01-01",END_DATE="1990-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/_spinup/begin_from_1981/global/states/",DATE_FOR_INITIAL_STATES="1981-12-31" job_script_pbs_pcrglobwb_template.sh)

SECOND=$(qsub -N nwj_9100 -W depend=afterany:${FIRST} -v INI_FILE="setup_6arcmin_new-jgw_uly-et0_uly-lcv_on_cca_with_initial_states.ini",MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/continue_from_1991/",STARTING_DATE="1991-01-01",END_DATE="2000-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/begin_from_1981/global/states/",DATE_FOR_INITIAL_STATES="1990-12-31" job_script_pbs_pcrglobwb_template.sh)

THIRD=$(qsub -N nwj_0110 -W depend=afterany:${SECOND} -v INI_FILE="setup_6arcmin_new-jgw_uly-et0_uly-lcv_on_cca_with_initial_states.ini",MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/continue_from_2001/",STARTING_DATE="2001-01-01",END_DATE="2010-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/continue_from_1991/global/states/",DATE_FOR_INITIAL_STATES="2000-12-31" job_script_pbs_pcrglobwb_template.sh)

FOURTH=$(qsub -N nwj_1119 -W depend=afterany:${THIRD} -v INI_FILE="setup_6arcmin_new-jgw_uly-et0_uly-lcv_on_cca_with_initial_states.ini",MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/continue_from_2011/",STARTING_DATE="2011-01-01",END_DATE="2019-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/continue_from_2001/global/states/",DATE_FOR_INITIAL_STATES="2010-12-31" job_script_pbs_pcrglobwb_template.sh)

set +x
