#!/bin/bash 
#PBS -N PGB01-27
#PBS -q nf
#PBS -l EC_total_tasks=30
#PBS -l EC_hyperthreads=2
#PBS -l EC_memory_per_task=2GB
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -M hsutanudjajacchms99@yahoo.com



# load modules, etc
. load_miniconda_pcrglobwb-py3-env_pcraster430.sh


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# run the model for every clone
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  1 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  2 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  3 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  4 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  5 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  6 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  7 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  8 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  9 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 10 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 11 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 12 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 13 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 14 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 15 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 16 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 17 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 18 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 19 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 20 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 21 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 22 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 23 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 24 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 25 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 26 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 27 &

wait

