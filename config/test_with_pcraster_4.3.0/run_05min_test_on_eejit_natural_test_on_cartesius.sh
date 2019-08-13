#!/bin/bash

# test on cartesius
#SBATCH -N 1
#SBATCH -t 9:00
#SBATCH -p short
#SBATCH -J test-pcraster_4.3.0-test-edwinvua

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

# pcraster option
#SBATCH --export=NUMBER_OF_WORKING_THREADS=test

# output directory
#SBATCH --export=OUTPUT_DIR=/scratch-shared/edwinvua/test/

pcrcalc

echo $NUMBER_OF_WORKING_THREADS
echo $OUTPUT_DIR

cd /home/edwinvua/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
