#!/bin/bash

#~ FIRST=`qsub first_job.sub`
#~ SECOND=`qsub -W depend=afterok:$FIRST second_job.sub`
#~ THIRD=`qsub -W depend=afterok:$SECOND third_job.sub`
#~ FOURTH=`qsub -W depend=afterok:$THIRD fourth_job.sub`

set -x

FIRST='qsub -N uet_gmd_1981-1990 -v MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/begin_from_1981/",STARTING_DATE="1981-01-01",END_DATE="1990-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/spinup/begin_from_1981/global/states/",DATE_FOR_INITIAL_STATES="1981-12-31" job_script_pbs_pcrglobwb_template.sh'

SECOND='qsub -N uet_gmd_1991-2000 -W depend=afterany:${FIRST} -v MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/continue_from_1991/",STARTING_DATE="1991-01-01",END_DATE="2000-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/begin_from_1981/global/states/",DATE_FOR_INITIAL_STATES="1990-12-31" job_script_pbs_pcrglobwb_template.sh'

THIRD='qsub -N uet_gmd_2001-2010 -W depend=afterany:${SECOND} -v MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/continue_from_2001/",STARTING_DATE="2001-01-01",END_DATE="2010-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/continue_from_1991/global/states/",DATE_FOR_INITIAL_STATES="2000-12-31" job_script_pbs_pcrglobwb_template.sh'

FOURTH='qsub -N uet_gmd_2011-2019 -W depend=afterany:${THIRD} -v MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/continue_from_2011/",STARTING_DATE="2011-01-01",END_DATE="2019-12-31",MAIN_INITIAL_STATE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-11-29/uly-et0_gmd-lcv/continue_from_2001/global/states/",DATE_FOR_INITIAL_STATES="2010-12-31" job_script_pbs_pcrglobwb_template.sh'

set +x
