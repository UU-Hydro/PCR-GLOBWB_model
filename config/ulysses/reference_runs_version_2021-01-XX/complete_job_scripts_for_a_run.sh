#!/bin/bash

#~ # Submit the first job and save the JobID as JOBONE
#~ JOBONE=$(qsub program1.pbs)
#~ # Submit the second job, use JOBONE as depend, save JobID
#~ JOBTWO=$(qsub -W depend=afterok:$JOBONE program2.pbs)
#~ # Submit last job using JOBTWO as depend, do not need to save the JobID
#~ qsub -W depend=afterok:$JOBTWO program3.pbs

#~ sutan101@login01.cluster:/quanta1/home/sutan101$ A="test"
#~ sutan101@login01.cluster:/quanta1/home/sutan101$ SPINUP=$(echo -v INI_FILE="${A}",MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/_spinup/begin_from_1981/",STARTING_DATE="1981-01-01",END_DATE="1981-12-31",MAIN_INITIAL_STATE_FOLDER="NONE",DATE_FOR_INITIAL_STATES="NONE" job_script_pbs_pcrglobwb_template.sh)
#~ sutan101@login01.cluster:/quanta1/home/sutan101$ echo $SPINUP
#~ -v INI_FILE=test,MAIN_OUTPUT_DIR=/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/new-jgw_uly-et0_uly-lcv/_spinup/begin_from_1981/,STARTING_DATE=1981-01-01,END_DATE=1981-12-31,MAIN_INITIAL_STATE_FOLDER=NONE,DATE_FOR_INITIAL_STATES=NONE job_script_pbs_pcrglobwb_template.sh
#~ sutan101@login01.cluster:/quanta1/home/sutan101$

JOBNAME="b1.0"
BFEXPON="1.0"
NODENMR="gpu030"

JOBNAME=$1
BFEXPON=$2
NODENMR=$3

SPINUP_RUN_INI="setup_6arcmin_ulysses_version_2021-01-03_for_spinup.ini"
WARMED_RUN_INI="setup_6arcmin_ulysses_version_2021-01-03_with_initial_states.ini" 

MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/"${JOBNAME}

set -x

# spin up run
SUB_JOBNAME=${JOBNAME}_spinup
SUB_INIFILE=${SPINUP_RUN_INI}
STA_DATE="1981-01-01"
END_DATE="1981-12-31"
INITIAL_FOLD="NONE"
INITIAL_DATE="NONE"
SUB_OUT_DIR=${MAIN_OUTPUT_DIR}/_spinup/with_1981/
# - start the run
SPINUP=$(sbatch --nodelist "${NODENMR}" -J "${SUB_JOBNAME}" --export INI_FILE="${SUB_INIFILE}",MAIN_OUTPUT_DIR="${SUB_OUT_DIR}",STARTING_DATE="${STA_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${INITIAL_FOLD}",DATE_FOR_INITIAL_STATES="${INITIAL_DATE}",BASEFLOW_EXPONENT="${BFEXPON}" job_script_sbatch_pcrglobwb_template.sh | sed 's/Submitted batch job //')


# run for the period 1981-90
SUB_JOBNAME=${JOBNAME}_81-90
SUB_INIFILE=${WARMED_RUN_INI}
STA_DATE="1981-01-01"
END_DATE="1990-12-31"
INITIAL_FOLD=${SUB_OUT_DIR}/global/states/
INITIAL_DATE="1981-12-31"
SUB_OUT_DIR=${MAIN_OUTPUT_DIR}/begin_from_1981/
# - start the run
FIRST=$(sbatch --nodelist "${NODENMR}" --dependency=afterany:${SPINUP} -J "${SUB_JOBNAME}" --export INI_FILE="${SUB_INIFILE}",MAIN_OUTPUT_DIR="${SUB_OUT_DIR}",STARTING_DATE="${STA_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${INITIAL_FOLD}",DATE_FOR_INITIAL_STATES="${INITIAL_DATE}",BASEFLOW_EXPONENT="${BFEXPON}" job_script_sbatch_pcrglobwb_template.sh | sed 's/Submitted batch job //')


# run for the period 1991-00
SUB_JOBNAME=${JOBNAME}_91-00
SUB_INIFILE=${WARMED_RUN_INI}
STA_DATE="1991-01-01"
END_DATE="2000-12-31"
INITIAL_FOLD=${SUB_OUT_DIR}/global/states/
INITIAL_DATE="1990-12-31"
SUB_OUT_DIR=${MAIN_OUTPUT_DIR}/continue_from_1991/
# - start the run
SECOND=$(sbatch --nodelist "${NODENMR}" --dependency=afterany:${FIRST} -J "${SUB_JOBNAME}" --export INI_FILE="${SUB_INIFILE}",MAIN_OUTPUT_DIR="${SUB_OUT_DIR}",STARTING_DATE="${STA_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${INITIAL_FOLD}",DATE_FOR_INITIAL_STATES="${INITIAL_DATE}",BASEFLOW_EXPONENT="${BFEXPON}" job_script_sbatch_pcrglobwb_template.sh | sed 's/Submitted batch job //')


# run for the period 2001-10
SUB_JOBNAME=${JOBNAME}_01-10
SUB_INIFILE=${WARMED_RUN_INI}
STA_DATE="2001-01-01"
END_DATE="2010-12-31"
INITIAL_FOLD=${SUB_OUT_DIR}/global/states/
INITIAL_DATE="2000-12-31"
SUB_OUT_DIR=${MAIN_OUTPUT_DIR}/continue_from_2001/
# - start the run
THIRD=$(sbatch --nodelist "${NODENMR}" --dependency=afterany:${SECOND} -J "${SUB_JOBNAME}" --export INI_FILE="${SUB_INIFILE}",MAIN_OUTPUT_DIR="${SUB_OUT_DIR}",STARTING_DATE="${STA_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${INITIAL_FOLD}",DATE_FOR_INITIAL_STATES="${INITIAL_DATE}",BASEFLOW_EXPONENT="${BFEXPON}" job_script_sbatch_pcrglobwb_template.sh | sed 's/Submitted batch job //')


# run for the period 2011-19
SUB_JOBNAME=${JOBNAME}_11-19
SUB_INIFILE=${WARMED_RUN_INI}
STA_DATE="2011-01-01"
END_DATE="2019-12-31"
INITIAL_FOLD=${SUB_OUT_DIR}/global/states/
INITIAL_DATE="2010-12-31"
SUB_OUT_DIR=${MAIN_OUTPUT_DIR}/continue_from_2011/
# - start the run
FOURTH=$(sbatch --nodelist "${NODENMR}" --dependency=afterany:${THIRD} -J "${SUB_JOBNAME}" --export INI_FILE="${SUB_INIFILE}",MAIN_OUTPUT_DIR="${SUB_OUT_DIR}",STARTING_DATE="${STA_DATE}",END_DATE="${END_DATE}",MAIN_INITIAL_STATE_FOLDER="${INITIAL_FOLD}",DATE_FOR_INITIAL_STATES="${INITIAL_DATE}",BASEFLOW_EXPONENT="${BFEXPON}" job_script_sbatch_pcrglobwb_template.sh | sed 's/Submitted batch job //')


set +x

echo $SPINUP
echo $FIRST
echo $SECOND
echo $THIRD
echo $FOURTH

squeue -u sutan101

