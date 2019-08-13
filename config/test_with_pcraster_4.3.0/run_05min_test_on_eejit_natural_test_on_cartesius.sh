#!/bin/bash

# test on cartesius
#SBATCH -N 1
#SBATCH -t 59:00
#SBATCH -p short
#SBATCH -J test-pcraster_4.3.0-test-edwinvua

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

# pcraster option, -1 indicating that not defining 
#SBATCH --export=NUMBER_OF_WORKING_THREADS=-1

set -x

echo ${NUMBER_OF_WORKING_THREADS}

# using pcraster 4.3.0 dev
# - activate conda env with python3 that is compatible for running pcrglobwb (using pcraster >= 4.2.1)
source activate py3_pcrglobwb
# - using pcraster 4.3 development version (NOTE: continuously developed/compiled by Oliver)
source /scratch/depfg/pcraster/pcraster-4.3.0.sh

# test pcraster
pcrcalc

# set the number of working threads
if [ ((${NUMBER_OF_WORKING_THREADS})) -gt -1 ]
then
   export PCRASTER_NR_WORKER_THREADS=${NUMBER_OF_WORKING_THREADS}
   echo ${PCRASTER_NR_WORKER_THREADS}
fi

# set output directory based on the number of working threads
OUTPUT_DIR=/scratch-shared/edwinvua/test/using_${NUMBER_OF_WORKING_THREADS}

# go to the script directory and execute the run
cd /home/edwinvua/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
python deterministic_runner.py ../config/test_with_pcraster_4.3.0/setup_05min_test_on_eejit_natural.ini no-debug --output_dir ${OUTPUT_DIR}

# show pcraster version and number of working threads at the end of the calculation
pcrcalc
echo ${NUMBER_OF_WORKING_THREADS}

set +x
