#!/bin/bash

#PBS -N af5m_acc

#PBS -l select=1:ncpus=48:mem=124gb
#PBS -l walltime=48:00:00

#PBS -q express -P exp-00044

# load all software needed
cd /rds/general/user/esutanud/home/
. load_all_default.sh

# set number of threads for pcraster
export PCRASTER_NR_WORKER_THREADS=48

# set the folder that contain PCR-GLOBWB model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/rds/general/user/esutanud/home/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

# set the configuration file (*.ini) that will be used (assumption: the .ini file is located within the same directory as this job, i.e. ${PBS_O_WORKDIR})
INI_FILE=${PBS_O_WORKDIR}/"setup_05min_africa_version_2021-05-31.ini"

# execute the model
cd /rds/general/user/esutanud/home/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
python deterministic_runner.py ${INI_FILE}
