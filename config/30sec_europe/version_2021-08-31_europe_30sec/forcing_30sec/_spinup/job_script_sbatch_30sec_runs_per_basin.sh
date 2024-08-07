#!/bin/bash 

#SBATCH -N 1
#SBATCH -t 119:59:00
#SBATCH -p normal

#~ #SBATCH -p broadwell

#~ #SBATCH -t 59:00
#~ #SBATCH -p short

#~ #SBATCH -t 119:59:00
#~ #SBATCH -p fat

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


#~ edwinari@fcn24.bullx:/projects/0/einf1079/edwin/data/pcrglobwb_input_arise/develop/europe_30sec/cloneMaps/clonemaps_europe_countries$ ls -lah */clone*30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 451K Jun 21 12:48 ebro/clone_ebro_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 887K Jun 21 12:48 elbe/clone_elbe_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 493K Jun 21 12:48 maritsa/clone_maritsa_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 394K Jun 21 12:48 po/clone_po_30sec.map
#~ lrwxrwxrwx 1 edwinari einf1079   20 Jun 22 22:02 rhinemeuse/clone_rhinemeuse_30sec.map -> rhinemeuse_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 352K Jun 21 12:48 severn/clone_severn_30sec.map
#~ -rw-r--r-- 1 edwinari einf1079 985K Jun 21 12:48 vistula/clone_vistula_30sec.map

GENERAL_OUTPUT_DIR="/projects/0/einf1079/edwin/pcrglobwb_output_europe_version_2021-06-XX/europe_30sec_with_30sec_forcing_all_europe/begin_from_1981_including_spinup/"

# run all runs

CLONEMAP=${CLONEMAP}

python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX_parallelization_with_clone_and_landmask.ini -mod ${GENERAL_OUTPUT_DIR}/mask_${CLONEMAP}/ -clonemap ${CLONEMAP}

wait

# wait for 5 sec 
sleep 5

set +x
