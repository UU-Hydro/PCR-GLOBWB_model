#!/bin/bash 
#PBS -l walltime=12:00:00
#PBS -N test-PCR-GLOBWB
#PBS -q np

# load modules, etc
. /home/ms/copext/cyes/load_miniconda_pcrglobwb-py3-env_pcraster421.sh

# set number of working threads
export PCRASTER_NR_WORKER_THREADS=36

# run the model
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
python deterministic_runner.py ../config/ulysses/setup_6arcmin_dummy_with_input.ini debug


