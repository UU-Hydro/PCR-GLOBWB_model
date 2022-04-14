#!/bin/bash 

#SBATCH -N 1
#SBATCH -t 119:59:00

#~ #SBATCH -t 59:59:00

#SBATCH -n 32

#SBATCH -p thin

#SBATCH -J e1k50kXX

#SBATCH --exclusive=user

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


#SBATCH --export CLONEMAP="clonemap"



set -x


# load software
. /home/edwin/load_pcrglobwb_python3_default.sh

#~ unset PCRASTER_NR_WORKER_THREADS
export PCRASTER_NR_WORKER_THREADS=32


# ini files
#~ # - with slurm
#~ INI_FILE=${SLURM_SUBMIT_DIR}"/setup_30sec_europe_with_30min_forcing_version_2021-06-XX_parallelization_with_clone_and_landmask_2000-2019.ini"
# - with bash
INI_FILE=$(pwd)"/setup_30sec_europe_with_30min_forcing_version_2021-06-XX_parallelization_with_clone_and_landmask_2000-2019.ini"


# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/edwin/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
# - go there
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} 


GENERAL_OUTPUT_DIR="/scratch-shared/edwin/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30min_forcing_all_europe/continue_from_2000/"



INITIAL_STATE_FOLDER="/scratch-shared/edwinari/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30min_forcing_all_europe/begin_from_1981/"
DATE_FOR_INITIAL_STATES="1999-12-31"


#~ CLONEMAP=${CLONEMAP}

# for clone 3 only
CLONEMAP=3

python deterministic_runner_with_arguments.py ${INI_FILE} -mod ${GENERAL_OUTPUT_DIR}/mask_${CLONEMAP}/ -clonemap ${CLONEMAP} -misd ${INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} &

wait

# wait for 5 sec 
sleep 5

set +x
