#!/bin/bash 
#PBS -N PGB19-36
#PBS -q nf
#PBS -l EC_total_tasks=29
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
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 19 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 20 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 21 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 22 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 23 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 24 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 25 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 26 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 27 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 28 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 29 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 30 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 31 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 32 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 33 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 34 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 35 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 36 &

wait

