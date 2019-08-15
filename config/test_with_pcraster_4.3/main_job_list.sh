#!/bin/bash

set -x

# set a working folder on a scratch disk (it will contains slurm output)
# - for tests on cartesius
WORK_FOLDER="/scratch/depfg/sutan101/pcrglobwb_pcraster4.3_test_on_eejit"
mkdir -p ${WORK_FOLDER}

# master job file
JOB_FILE=run_05min_test_on_eejit_natural.sh

# copy the master job file to the working folder
cp ${JOB_FILE} ${WORK_FOLDER}

# go to the working folder
cd ${WORK_FOLDER}

# submit the jobs
sbatch --export=NUMBER_OF_WORKING_THREADS=-1 -J pcrt_c-1 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=0  -J pcrt_c00 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=1  -J pcrt_c01 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=2  -J pcrt_c02 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=4  -J pcrt_c04 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=8  -J pcrt_c08 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=16 -J pcrt_c16 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=24 -J pcrt_c24 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=32 -J pcrt_c32 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=48 -J pcrt_c48 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=64 -J pcrt_c64 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=80 -J pcrt_c80 ${JOB_FILE}
sbatch --export=NUMBER_OF_WORKING_THREADS=96 -J pcrt_c96 ${JOB_FILE}

# go to the previous folder
cd -

set +x
