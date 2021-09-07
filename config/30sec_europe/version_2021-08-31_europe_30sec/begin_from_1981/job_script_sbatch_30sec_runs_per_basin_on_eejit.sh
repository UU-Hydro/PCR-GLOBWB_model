#!/bin/bash 

#SBATCH -N 1
#SBATCH -n 96

#SBATCH -t 300:59:00

#SBATCH -J eu1k

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


#SBATCH --export STARTCLONE=0,ENDCLONE=0


set -x


# load software
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh

# unset PCRASTER_NR_WORKER_THREADS
export PCRASTER_NR_WORKER_THREADS=12

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
# - go there
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} 


STARTING_DATE="1981-01-01"
END_DATE="2019-12-31"

GENERAL_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30sec_forcing_all_europe/begin_from_1981/"

INI_FILE=${SLURM_SUBMIT_DIR}"/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX_parallelization_with_clone_and_landmask_1981-2019_on_eejit_with-limited-spinup.ini"

INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30sec_forcing_all_europe/_spinup/begin_from_1981_including_spinup/"
DATE_FOR_INITIAL_STATES="1981-12-31"


STA=${STARTCLONE}
END=${ENDCLONE}

for i in {STA..END}

do

CLONEMAP=${i}

python deterministic_runner_with_arguments.py ${INI_FILE} -mod ${GENERAL_OUTPUT_DIR}/mask_${CLONEMAP}/ -clonemap ${CLONEMAP} -sd ${STARTING_DATE} -ed ${END_DATE} -misd ${INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} &

wait

done

# wait for 5 sec 
sleep 5

set +x
