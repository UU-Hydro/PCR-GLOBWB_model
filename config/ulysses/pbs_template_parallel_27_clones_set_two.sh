#!/bin/bash 
#PBS -N PGB28-54
#PBS -q nf
#PBS -l EC_total_tasks=32
#PBS -l EC_hyperthreads=2
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -M hsutanudjajacchms99@yahoo.com



# load modules, etc
. load_miniconda_pcrglobwb-py3-env_pcraster430.sh


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# run the model for every clone
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 28 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 29 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 30 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 31 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 32 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 33 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 34 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 35 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 36 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 37 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 38 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 39 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 40 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 41 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 42 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 43 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 44 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 45 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 46 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 47 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 48 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 49 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 50 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 51 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 52 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 53 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel 54 &

wait

