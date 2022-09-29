#!/bin/bash 
#PBS -N test
#PBS -q nf
#PBS -l EC_total_tasks=5
#PBS -l EC_hyperthreads=2
#PBS -l EC_memory_per_task=11GB
#PBS -l EC_billing_account=c3s432l3
#PBS -l walltime=48:00:00

#PBS -M hsutanudjajacchms99@yahoo.com



# load modules, etc
. /home/ms/copext/cyes/load_miniconda_pcrglobwb-py3-env_pcraster430.sh


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

python deterministic_runner_parallel_for_ulysses.py \
          ../config/ulysses/setup_6arcmin_develop.ini debug_parallel 2 \
          -mod /scratch/ms/copext/cyes/develop_parallel \
          -sd 1982-01-01 -ed 1982-01-31 \
          -misd /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones/global/states \
          -dfis 1981-12-31 \
          -pff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/precipitation_daily_01_1982.nc \
          -tff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/tavg_01_1982.nc \
          -rpetff /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/pet_01_1982.nc \
          end_of_arguments &

python deterministic_runner_parallel_for_ulysses.py \
          ../config/ulysses/setup_6arcmin_develop.ini debug_parallel 15 \
          -mod /scratch/ms/copext/cyes/develop_parallel \
          -sd 1982-01-01 -ed 1982-01-31 \
          -misd /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones/global/states \
          -dfis 1981-12-31 \
          -pff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/precipitation_daily_01_1982.nc \
          -tff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/tavg_01_1982.nc \
          -rpetff /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/pet_01_1982.nc \
          end_of_arguments &

python deterministic_runner_parallel_for_ulysses.py \
          ../config/ulysses/setup_6arcmin_develop.ini debug_parallel 37 \
          -mod /scratch/ms/copext/cyes/develop_parallel \
          -sd 1982-01-01 -ed 1982-01-31 \
          -misd /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones/global/states \
          -dfis 1981-12-31 \
          -pff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/precipitation_daily_01_1982.nc \
          -tff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/tavg_01_1982.nc \
          -rpetff /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/pet_01_1982.nc \
          end_of_arguments &

python deterministic_runner_parallel_for_ulysses.py \
          ../config/ulysses/setup_6arcmin_develop.ini debug_parallel 52 \
          -mod /scratch/ms/copext/cyes/develop_parallel \
          -sd 1982-01-01 -ed 1982-01-31 \
          -misd /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones/global/states \
          -dfis 1981-12-31 \
          -pff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/precipitation_daily_01_1982.nc \
          -tff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/tavg_01_1982.nc \
          -rpetff /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/pet_01_1982.nc \
          end_of_arguments &
          
wait

