#!/bin/bash
#SBATCH -N 1
#SBATCH -n 3
#SBATCH -J hist_wqTrue
#SBATCH --mail-type=ALL
#SBATCH --mail-user=gcardenas1891@gmail.com

# load the conda enviroment on eejit
. /eejit/home/carde003/load_default.sh

# directory of QUAlloc model
MODEL_DIR_SCRIPTS="/eejit/home/carde003/github/QUAlloc_coupled/PCR-GLOBWB_model/model/water_management_qualloc"

# directory of configuration file (.cfg)
CFG_FILE="/eejit/home/carde003/github/QUAlloc_coupled/PCR-GLOBWB_model/model/water_management_qualloc/config/configuration_file_test_eejit_slurm.cfg"

# starting and end years
START_YEAR="2000"
END_YEAR="2001"

# sectoral water quality requirements
SWQ_FLAG="True"

# name of the simulation
SCENARIO_NAME="historic_wq=True"

# directory where input files are stored
INPUT_DIR="/scratch/depfg/carde003/qualloc/data/"

# directory where output files will be stored 
MAIN_OUTPUT_DIR="/scratch/depfg/carde003/qualloc/outputs/historic/true"

# directory where maks fr parallel simulation are stored
MASK_DIR="maps/masks/mask_"

# date for the initial states
YEAR_INITIAL_STATES="1979"

# run QUAlloc
#python qualloc/model/qualloc_runner.py qualloc/model/configuration_file_test.cfg
#for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
for i in 01 02
  do
  # adjusting input data
  OUTPUT_DIR=${MAIN_OUTPUT_DIR}/M${i}
  CLONE_MAP=${MASK_DIR}M${i}.map
  
  # running QUAlloc with arguments
  python ${MODEL_DIR_SCRIPTS}/qualloc_runner.py ${CFG_FILE} ${SCENARIO_NAME} ${INPUT_DIR} ${OUTPUT_DIR} ${CLONE_MAP} ${START_YEAR} ${END_YEAR} ${YEAR_INITIAL_STATES} ${SWQ_FLAG} &
  done
wait

echo "end of model runs (please check your results)"
