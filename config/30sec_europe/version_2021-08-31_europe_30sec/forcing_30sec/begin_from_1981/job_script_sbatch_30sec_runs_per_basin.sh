#!/bin/bash 

#SBATCH -N 1
#SBATCH -t 119:59:00

#~ #SBATCH -p normal

#~ #SBATCH -p broadwell

#SBATCH -J eu1k_mXX

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


#SBATCH --export CLONEMAP="clonemap"


set -x


# load software
. /home/edwinari/load_my_miniconda_and_my_default_env.sh

#~ unset PCRASTER_NR_WORKER_THREADS
export PCRASTER_NR_WORKER_THREADS=12

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
# - go there
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} 


CLONEMAP=${CLONEMAP}

STARTING_DATE="1981-01-01"
END_DATE="2000-12-31"

GENERAL_OUTPUT_DIR="/projects/0/einf1079/edwin/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30sec_forcing_all_europe/begin_from_1981/"

INITIAL_STATE_FOLDER="/home/edwinari/project_dirs/einf1079/edwin/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30sec_forcing_all_europe/_spinup/begin_from_1981_including_spinup/"

DATE_FOR_INITIAL_STATES="1981-12-31"

python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX_parallelization_with_clone_and_landmask_1981-2000_no-spinup_but_maximum_fossil_gw.ini -mod ${GENERAL_OUTPUT_DIR}/mask_${CLONEMAP}/ -clonemap ${CLONEMAP} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} 

wait

# wait for 5 sec 
sleep 5

set +x
