#!/bin/bash 
#PBS -N pgb-mnc
#PBS -q nf
#PBS -l EC_total_tasks=8
#PBS -l EC_hyperthreads=2
#PBS -l EC_memory_per_task=7.5GB
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -v MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/tmp_pbs_edwin/"

#PBS -M hsutanudjajacchms99@yahoo.com

# load modules, etc 
#
#~ # - using conda (NOT RECOMMENDED)
#~ . /home/ms/copext/cyes/load_miniconda_pcrglobwb-py3-env_pcraster430.sh
#
# - using modules on cca
module load python3/3.6.10-01
module load pcraster/4.3.0
module load gdal/3.0.4

set -x

# go to the folder that contain the script for merging
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_output_version_2020-08-10_example/first_test_54_clones/"

python3 merge_netcdf_6_arcmin_ulysses.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/global/netcdf outDailyTotNC 1981-01-01 1981-01-31 ulyssesP,ulyssesET,ulyssesSWE,ulyssesQsm,ulyssesSM,ulyssesQrRunoff,ulyssesDischarge NETCDF4 False 1 Global

set +x
