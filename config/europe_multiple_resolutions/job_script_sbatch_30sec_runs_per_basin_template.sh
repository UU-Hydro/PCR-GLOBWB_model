#!/bin/bash 

#SBATCH -N 1
#SBATCH -t 119:59:00
#SBATCH -p normal
#SBATCH --constraint=haswell

#SBATCH -J 1km_multf

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


#SBATCH --export CLONEMAP="clonemap"



set -x


# load software
. /home/edwinari/load_my_miniconda_and_my_default_env.sh


# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
# - go there
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} 


# run all runs
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_05min_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30min_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/${CLONEMAP}_30sec.map &

wait

# wait for 5 sec 
sleep 5

set +x
