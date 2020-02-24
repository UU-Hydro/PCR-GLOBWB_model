#!/bin/bash
#SBATCH -N 1
#SBATCH -n 96
#~ #SBATCH -t 240:00:00
#SBATCH -p defq
#SBATCH -J 30sec_africa_version_20200218

#SBATCH --exclusive

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


set -x

source activate pcrglobwb_py3_env_v20200128

pcrcalc

#~ export PCRASTER_NR_WORKER_THREADS=88

cd /quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

python deterministic_runner.py ../config/opendap_development/30sec_african_countries/whole_africa/setup_30sec_africa.ini debug

pcrcalc

set +x
