#!/bin/bash 
#PBS -N pgb-set4
#PBS -q nf
#PBS -l EC_total_tasks=15
#PBS -l EC_hyperthreads=2
#PBS -l EC_memory_per_task=4GB
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -v INI_FILE=None

#PBS -M hsutanudjajacchms99@yahoo.com


# load modules, etc 
#
#~ # - using conda (NOT RECOMMENDED)
#~ . /home/ms/copext/cyes/load_miniconda_pcrglobwb-py3-env_pcraster430.sh
#
# - using modules on cca
module load python3/3.6.10-01
module load pcraster/4.3.0
module load gdal/3.0.4

# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

INI_FILE="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/ulysses/version_2020-08-12/setup_6arcmin_test_version_2020-08-12.ini"

# run the model for every clone
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel  4 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel  6 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel  7 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel  8 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 14 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 19 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 20 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 34 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 38 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 45 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 47 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 49 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 50 &

wait

