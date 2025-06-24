#!/bin/bash
#SBATCH -N 1
#SBATCH -n 16
#SBATCH -p rome
#SBATCH -t 24:00:00
#SBATCH -J full_couple
#SBATCH --mail-type=END
#SBATCH --mail-user=gcardenas1891@gmail.com

# setting input files and directories ...................................
# folder containing .ini file
INI_FILE="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/config/full_coupling/setup_05min_full_coupling.ini"

# starting and end dates
START_DATE="1980-01-01"
END_DATE="1980-12-31"

# location/folder, where you will store output files of your 
OUTPUT_DIR="/gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_dynqual_qualloc"

# initial conditions
# - PS: for continuing runs (including the transition from the historical to SSP runs), please use the output files from the previous period model runs.
INITIAL_STATE_FOLDER="/gpfs/work3/0/prjs1311/qualloc/data/initial/historic"
MAIN_INITIAL_STATE_FOLDER=${INITIAL_STATE_FOLDER}/pcrglobwb
DATE_FOR_INITIAL_STATES="1979-12-31"

# directory where python script to create configuration files per mask is stored
SCRIPT_CONFIG_FILE_QUALLOC="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/water_management_qualloc/configuration_parallel.py"

# directory where QUAlloc base configuration file is stored
MAIN_QUALLOC_CONFIG_FILE="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/water_management_qualloc/config/parallel/configuration_file_parallel_coupled.cfg"

# number of spinup years
# - PS: For continuing runs, please set it to zero
NUMBER_OF_SPINUP_YEARS="0"

# directory of pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/"

# running model ........................................................
# load the conda enviroment on snellius
source activate base
conda activate /gpfs/home6/gcardenas/.conda/envs/geo

# unset pcraster working threads and export the following option 
unset PCRASTER_NR_WORKER_THREADS
export OPENBLAS_NUM_THREADS=1

# starting, end and initial condition years
START_YEAR=${START_DATE:0:4}
END_YEAR=${END_DATE:0:4}
INI_STATE_YEAR=${DATE_FOR_INITIAL_STATES:0:4}

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# update directory where PCRGLOBWB2 outputs will be stored
MAIN_OUTPUT_DIR=${OUTPUT_DIR}/test

# directory where QUAlloc outputs will be stored
QUALLOC_OUTPUT_DIR=${MAIN_OUTPUT_DIR}/qualloc

# set the clone code
CLONE_CODE=01

# create qualloc configuration file
QUALLOC_CONFIG_FILE=${MAIN_QUALLOC_CONFIG_FILE:0:-4}_M01.cfg

# run modelling framework
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel 01 -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} -qcf ${QUALLOC_CONFIG_FILE} &
wait

echo "\n... End of model runs (please check your results)."

