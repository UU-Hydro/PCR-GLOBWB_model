#!/bin/bash 
#PBS -N pgb-set2
#PBS -q nf
#PBS -l EC_total_tasks=20
#PBS -l EC_hyperthreads=2
#PBS -l EC_memory_per_task=3GB
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
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel  5 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel  9 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 10 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 18 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 21 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 22 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 24 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 27 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 29 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 30 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 33 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 36 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 41 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 42 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 52 &
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel 53 &

wait

