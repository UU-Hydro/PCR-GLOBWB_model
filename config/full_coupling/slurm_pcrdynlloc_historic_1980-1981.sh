#!/bin/bash
#SBATCH -N 1
#SBATCH -n 96
#SBATCH -J full_couple
#SBATCH --mail-type=ALL
#SBATCH --mail-user=gcardenas1891@gmail.com

# folder containing .ini file
INI_FILE="/home/gcardenas/github/PCR-GLOBWB_model/config/full_coupling/setup_05min.ini"

# starting and end dates
START_DATE="1980-01-01"
END_DATE="1980-12-31"

# location/folder, where you will store output files of your 
MAIN_OUTPUT_DIR=/gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_dynqual_qualloc/${START_DATE:0:4}-${END_DATE:0:4}

# initial conditions
INITIAL_STATE_FOLDER="/projects/0/prjs1311/qualloc/data/initial/historic"
MAIN_INITIAL_STATE_FOLDER=${INITIAL_STATE_FOLDER}/pcrglobwb
DATE_FOR_INITIAL_STATES="1979-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), please use the output files from the previous period model runs.

# directory where python script to create configuration files per mask is stored
SCRIPT_CONFIG_FILE_QUALLOC=""

# directory where QUAlloc base configuration file is stored
MAIN_QUALLOC_CONFIG_FILE="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/water_management_qualloc/config/parallel/configuration_file_parallel_coupled.cfg"

# number of spinup years
NUMBER_OF_SPINUP_YEARS="1"
# - PS: For continuing runs, please set it to zero
#NUMBER_OF_SPINUP_YEARS="0"

# location of your pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/"

# load the conda enviroment on snellius
source activate base
conda activate /gpfs/home6/gcardenas/.conda/envs/geo

# unset pcraster working threads 
unset PCRASTER_NR_WORKER_THREADS

# - you may have to activate the following
export OPENBLAS_NUM_THREADS=1

# test pcraster
pcrcalc

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# run the model for all clones, from 1 to 53
#for i in {01..53}
for i in {01..02}
  do
  # set the clone code
  CLONE_CODE=${i}
  # create qualloc configuration file
  python3 ${SCRIPT_CONFIG_FILE_QUALLOC} ${MAIN_QUALLOC_CONFIG_FILE} ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE:0:4} -ed ${END_DATE:0:4} -isd ${INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES:0:4} 
  QUALLOC_CONFIG_FILE=${MAIN_QUALLOC_CONFIG_FILE:0:-4}_M${CLONE_CODE}.cfg
  # run modelling framework
  python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} -qcf ${QUALLOC_CONFIG_FILE} &
  done


# process for merging files at the global extent
python3 deterministic_runner_merging_with_arguments.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE} -ed ${END_DATE} &

# wait until process is finished
wait

echo "end of model runs (please check your results)"

