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
INI_FILE="/eejit/home/carde003/github/QUAlloc_coupled/PCR-GLOBWB_model/model/water_management_qualloc/config/configuration_file_test_eejit_slurm.cfg"

# starting and end years
START_YEAR="2000"
END_YEAR="2001"

# sectoral water quality requirements
SWQ_FLAG=True

# name of the simulation
SCENARIO_NAME="historic_wq=True"

# directory where input files are stored
MAIN_INPUT_DIR="/scratch/depfg/carde003/qualloc/data/"

# directory where output files will be stored 
MAIN_OUTPUT_DIR="/scratch/depfg/carde003/qualloc/outputs/historic/true"

# date for the initial states
YEAR_INITIAL_STATES="1979"

# run QUAlloc
#python qualloc/model/qualloc_runner.py qualloc/model/configuration_file_test.cfg
for i in {1..3}
do
CLONE_CODE=${i}
python ${MODEL_DIR_SCRIPTS}/qualloc_runner_parallel.py ${INI_FILE} &
done
wait

echo "end of model runs (please check your results)"