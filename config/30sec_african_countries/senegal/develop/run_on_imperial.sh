#!/bin/bash 
#PBS -l walltime=900:00:00
#PBS -l select=1:ncpus=8:mem=96gb
#PBS -N ARISE-PCR-GLOBWB_model

echo "Allocated nodes:"
cat $PBS_NODEFILE

cd $HOME

. load_all_default.sh

module list

cd github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
python deterministic_runner.py ../config/30sec_african_countries/senegal/develop/setup_30sec_senegal_develop_on_imperial.ini debug

