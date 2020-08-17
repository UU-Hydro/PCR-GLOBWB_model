#!/bin/bash 
#PBS -N test-npd
#PBS -q np
#PBS -l EC_nodes=1
#PBS -l EC_total_tasks=72
#PBS -l EC_hyperthreads=2
#PBS -l EC_billing_account=c3s432l3

#PBS -l walltime=48:00:00
#~ #PBS -l walltime=8:00

#PBS -M hsutanudjajacchms99@yahoo.com


set -x

# make the run for every clone
aprun -N $EC_tasks_per_node -n $EC_total_tasks -j $EC_hyperthreads bash pcrglobwb_runs.sh 

MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/test_aprun_develop/"

cd ${MAIN_OUTPUT_DIR}
mkdir test 
cd test
pwd

set +x
