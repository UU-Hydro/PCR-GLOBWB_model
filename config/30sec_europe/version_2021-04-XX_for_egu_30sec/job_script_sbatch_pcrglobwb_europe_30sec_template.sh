#!/bin/bash 
#SBATCH -N 1
#SBATCH -t 119:59:00

#SBATCH -J 30XXXXXX

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

#SBATCH --export PCRTHREADS="8",CLONE1="0",CLONE2="0",CLONE3="0"

#~ edwinari@tcn757.bullx:/home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/30sec_europe/version_2021-04-XX_for_egu_30sec$ ls -lah *
#~ -rw-r--r-- 1 edwinari edwinari 728 Apr 20 13:47 job_script_sbatch_pcrglobwb_europe_30sec_template.sh
#~ -rw-r--r-- 1 edwinari edwinari 37K Apr 20 13:47 setup_30sec_europe_version_2021-04-XX.ini

CONFIG_INI_FILE="/home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/30sec_europe/version_2021-04-XX_for_egu_30sec/setup_30sec_europe_version_2021-04-XX.ini"

set -x

# load all required modules
. /home/edwinari/load_my_miniconda_and_my_default_env.sh

export PCRASTER_NR_WORKER_THREADS=${PCRTHREADS}

# go to the model folder
cd /home/edwinari/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model

# run the model(s)
python deterministic_runner_parallel_for_ulysses.py ${CONFIG_INI_FILE} parallel ${CLONE1} &
python deterministic_runner_parallel_for_ulysses.py ${CONFIG_INI_FILE} parallel ${CLONE2} &
python deterministic_runner_parallel_for_ulysses.py ${CONFIG_INI_FILE} parallel ${CLONE3} &

wait

# sleep/wait for 5 sec 
sleep 5

set +x
