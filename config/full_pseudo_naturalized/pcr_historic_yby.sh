#!/bin/bash
#SBATCH -N 1
##SBATCH -n 192
##SBATCH -p genoa
#SBATCH -t 120:00:00
#SBATCH -n 52
#SBATCH -p rome
#SBATCH -J fullcoup
#SBATCH --mail-type=END
#SBATCH --mail-user=gcardenas1891@gmail.com

# setting input files and directories ...................................
# folder containing .ini file
INI_FILE="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/config/full_pseudo_naturalized/setup_05min_pseudo_naturalized.ini"

# starting and end dates
YEAR=$1
START_DATE="${YEAR}-01-01"
END_DATE="${YEAR}-12-31"

# location/folder, where you will store output files of your 
OUTPUT_DIR="/gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_pseudo_naturalized"

# initial conditions
# - PS: for continuing runs (including the transition from the historical to SSP runs), please use the output files from the previous period model runs.
PCRGLOBWB_INITIAL_STATE_FOLDER="/gpfs/work3/0/prjs1311/qualloc/data/initial/historic/pcrglobwb_natural"
DATE_FOR_INITIAL_STATES="$((YEAR - 1))-12-31"

# number of spinup years
# - PS: For continuing runs, please set it to zero
NUMBER_OF_SPINUP_YEARS="3"

# directory of pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/model/"

# PCR-GLOBWB2 and DynQual output variables' names
PCRGLOBWB_OUTPUT_NETCDFS=directRunoff,interflowTotal,baseflow,surfaceWaterInf,waterBodyActEvaporation,channelStorage,discharge,totalWaterStorageVolume,domesticWaterWithdrawal

# running model ........................................................
# load the conda enviroment on snellius
source activate base
conda activate /gpfs/home6/gcardenas/.conda/envs/geo

# unset pcraster working threads and export the following option 
unset PCRASTER_NR_WORKER_THREADS
export OPENBLAS_NUM_THREADS=1

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# update directory where PCRGLOBWB2 outputs will be stored
MAIN_OUTPUT_DIR=${OUTPUT_DIR}/${YEAR}

# update directory where PCRGLOBWB2 state variables will be stored
PCRGLOBWB_INITIAL_STATE_FOLDER=${PCRGLOBWB_INITIAL_STATE_FOLDER}

## run the model for all clones, from 1 to 53
##for i in {01..01}
#for i in {01..53}
  #do
  ## set the clone code
  #CLONE_CODE=${i}
  
  ## run modelling framework
  #python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE} -ed ${END_DATE} -misd ${PCRGLOBWB_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} &
  #done
#wait

## merging state variables ..............................................
## merging PCR-GLOBWB2 state variables
#python3 merge_pcraster_maps.py ${END_DATE} ${MAIN_OUTPUT_DIR}/ ${PCRGLOBWB_INITIAL_STATE_FOLDER} states 8 Global &
#wait

# merge output netcdf ..................................................
# create folder
PCRGLOBWB_OUTPUT_NETCDF_DIR=${MAIN_OUTPUT_DIR}/global
mkdir ${PCRGLOBWB_OUTPUT_NETCDF_DIR}

# merging outputs to global extension
python merge_netcdf.py ${MAIN_OUTPUT_DIR} ${PCRGLOBWB_OUTPUT_NETCDF_DIR} outMonthAvgNC ${START_DATE} ${END_DATE} ${PCRGLOBWB_OUTPUT_NETCDFS} NETCDF4 True 53 53 all_lats False &
wait

echo -e "\n... Finished model runs for $YEAR."


# submit next year .....................................................
#if [ "$YEAR" -le 2018 ]; then
#  sbatch "/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/config/full_pseudo_naturalized/pcr_historic_yby.sh" "$((YEAR + 1))"
#fi
