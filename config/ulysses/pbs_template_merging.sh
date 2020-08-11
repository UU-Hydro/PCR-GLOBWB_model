#!/bin/bash 
#PBS -N merging_netcdf
#PBS -q nf
#PBS -l EC_total_tasks=9
#PBS -l EC_hyperthreads=2
#PBS -l EC_memory_per_task=6.5GB
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -M hsutanudjajacchms99@yahoo.com



# load modules, etc
. /home/ms/copext/cyes/load_miniconda_pcrglobwb-py3-env_pcraster430.sh


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# merging process
python merge_netcdf_6_arcmin.py /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones/global/netcdf/ outDailyTotNC 1981-01-01 1981-01-31 ulyssesET,ulyssesQrRunoff,ulyssesSM,ulyssesDischarge,ulyssesP,ulyssesQsm,ulyssesSWE NETCDF4 True 8 Global
