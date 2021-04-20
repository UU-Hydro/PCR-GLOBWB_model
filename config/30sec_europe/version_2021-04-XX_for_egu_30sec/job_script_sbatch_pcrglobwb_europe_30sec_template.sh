#!/bin/bash 
#SBATCH -N 1
#SBATCH -t 119:59:00

#SBATCH -J 30XXXXXX

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

#SBATCH --export PCRTHREADS="8",CLONE1="0",CLONE2="0",CLONE3="0"

set -x

CONFIG_INI_FILE=""

# load all required modules
. /home/edwinari/load_my_miniconda_and_my_default_env.sh

export PCRASTER_NR_WORKER_THREADS=${PCRTHREADS}

# go to the model folder
cd /home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model



python deterministic_runner_parallel_for_ulysses.py ../config/30sec_europe/setup_30sec_europe_develop.ini debug_parallel 3


wait

# sleep/wait for 5 sec 
sleep 5

set +x
