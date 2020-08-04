#!/bin/bash 
#PBS -N test-PCR-GLOBWB-serial
#PBS -q ns
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -M hsutanudjajacchms99@yahoo.com

#PBS -l EC_memory_per_task=64000MB

#PBS -v CLONE_CODE=99

# load modules, etc
. /home/ms/copext/cyes/load_miniconda_pcrglobwb-py3-env_pcraster421.sh


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# run the model for every clone
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx_serial.ini debug_parallel ${CLONE_CODE}

