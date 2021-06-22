#!/bin/bash 

#SBATCH -N 1
#~ #SBATCH -t 119:59:00
#~ #SBATCH -p normal
#~ #SBATCH --constraint=haswell

#SBATCH -t 59:00
#SBATCH -p short

#SBATCH -J eu1k_test

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


#~ #SBATCH --export CLONEMAP="clonemap"



set -x


# load software
. /home/edwinari/load_my_miniconda_and_my_default_env.sh
unset PCRASTER_NR_WORKER_THREADS

# set the folder that contain PCR-GLOBWB model scripts (note that this is not always the latest version)
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"
# - go there
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} 


#~ (pcrglobwb_python3) sutan101@gpu038.cluster:/scratch/depfg/sutan101/data/pcrglobwb_input_arise/develop/europe_30sec/cloneMaps/clonemaps_europe_countries$ ls -lah */*30sec.map

#~ -rw-r--r-- 1 sutan101 depfg 985K Jun 10 22:09 rhinemeuse/rhinemeuse_30sec.map
#~ -rw-r--r-- 1 sutan101 depfg 451K Jun 10 17:05 ebro/clone_ebro_30sec.map

#~ -rw-r--r-- 1 sutan101 depfg 985K Jun 10 22:01 vistula/clone_vistula_30sec.map
#~ -rw-r--r-- 1 sutan101 depfg 493K Jun 10 19:22 maritsa/clone_maritsa_30sec.map

#~ -rw-r--r-- 1 sutan101 depfg 887K Jun 10 17:16 elbe/clone_elbe_30sec.map
#~ -rw-r--r-- 1 sutan101 depfg 394K Jun 10 19:41 po/clone_po_30sec.map
#~ -rw-r--r-- 1 sutan101 depfg 352K Jun 10 21:07 severn/clone_severn_30sec.map


# run all runs

CLONEMAP="vistula"
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_05min_forcing_version_2021-06-XX.ini              -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30min_forcing_version_2021-06-XX.ini              -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX.ini              -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_alternative1_version_2021-06-XX.ini -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_alternative2_version_2021-06-XX.ini -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &

CLONEMAP="maritsa"
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_05min_forcing_version_2021-06-XX.ini              -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30min_forcing_version_2021-06-XX.ini              -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_version_2021-06-XX.ini              -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_alternative1_version_2021-06-XX.ini -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &
python deterministic_runner_with_arguments.py ${SLURM_SUBMIT_DIR}/setup_30sec_europe_with_30sec_forcing_alternative2_version_2021-06-XX.ini -mod ${CLONEMAP}_test -clonemap ${CLONEMAP}/clone_${CLONEMAP}_30sec.map &

wait

# wait for 5 sec 
sleep 5

set +x
