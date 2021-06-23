#!/bin/bash 

#SBATCH -N 1
#SBATCH -t 119:59:00
#SBATCH -p broadwell

#~ #SBATCH -p normal

#~ #SBATCH -p normal
#~ #SBATCH --constraint=haswell

#~ #SBATCH -t 59:00
#~ #SBATCH -p short

#~ #SBATCH -t 119:59:00
#~ #SBATCH -p fat

#SBATCH -J eu1k_rm

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


#~ #SBATCH --export CLONEMAP="clonemap"



set -x


# load software
. /home/edwinari/load_my_miniconda_and_my_default_env.sh

#~ unset PCRASTER_NR_WORKER_THREADS
export PCRASTER_NR_WORKER_THREADS=12

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
# - go there
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} 


#~ edwinari@fcn24.bullx:/projects/0/einf1079/edwin/data/pcrglobwb_input_arise/develop/europe_30sec/cloneMaps/clonemaps_europe_countries$ ls -lah */clone*30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 451K Jun 21 12:48 ebro/clone_ebro_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 887K Jun 21 12:48 elbe/clone_elbe_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 493K Jun 21 12:48 maritsa/clone_maritsa_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 394K Jun 21 12:48 po/clone_po_30sec.map
#~ lrwxrwxrwx 1 edwinari einf1079   20 Jun 22 22:02 rhinemeuse/clone_rhinemeuse_30sec.map -> rhinemeuse_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 352K Jun 21 12:48 severn/clone_severn_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 985K Jun 21 12:48 vistula/clone_vistula_30sec.map


# run all runs

CLONEMAP="rhinemeuse"
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_05min_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30min_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &

#~ CLONEMAP="vistula"
#~ python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_05min_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
#~ python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30min_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
#~ python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX.ini -mod ${CLONEMAP} -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &

wait

# wait for 5 sec 
sleep 5

set +x
