#!/bin/bash 
#PBS -N nametest
#PBS -q ns
#~ #PBS -l EC_nodes=1
#~ #PBS -l EC_total_tasks=72
#~ #PBS -l EC_hyperthreads=2
#PBS -l EC_billing_account=c3s432l3

#~ #PBS -l walltime=48:00:00
#~ #PBS -l walltime=8:00
#~ #PBS -l walltime=1:00:00
#PBS -l walltime=12:00:00

#PBS -M hsutanudjajacchms99@yahoo.com

#PBS -o %N.out.%j
#PBS -e %N.err.%j

set -x

echo ${PBS_JOBNAME}
echo ${PBS_JOBID}
echo ${HOSTNAME}

set +x
