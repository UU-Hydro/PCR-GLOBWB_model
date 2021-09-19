#!/bin/bash 

#SBATCH -N 1
#SBATCH -n 96

#SBATCH -t 240:00:00

#SBATCH -J gswp3-w5e5_1959-2019

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com



set -x

# folder containing .ini file
# - with slurm (on eejit)
INI_FOLDER=${SLURM_SUBMIT_DIR}
#~ # - with bash
#~ INI_FOLDER=$(pwd)


# configuration (.ini) file
#~ # - historical
#~ INI_FILE=${INI_FOLDER}/"setup_05min_historical_version_2021-09-16.ini"
#~ # - ssp370
#~ INI_FILE=${INI_FOLDER}/"setup_05min_ssp370_version_2021-09-16.ini"

# - historical with max fossil gw
INI_FILE=${INI_FOLDER}/"setup_05min_historical_version_2021-09-16_with_maxfgw.ini"


# pcrglobwb output folder
MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-09-18/begin_from_1959/"

#~ MAIN_OUTPUT_DIR="/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-XX_ssp370_gfdl-esm4/continue_from_2051/"


# starting and end dates
STARTING_DATE="1959-01-01"
END_DATE="2019-12-31"


# meteorological forcing files

# - historical reference - gswp3-w5e5
RELATIVE_HUMIDITY_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_hurs_global_daily_1901_2019_version_2021-09-XX.nc"
PRECIPITATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX.nc"
PRESSURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_ps_global_daily_1901_2019_version_2021-09-XX.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc"
WIND_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc"
TEMPERATURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX.nc"

#~ (pcrglobwb_python3) sutan101@gpu038.cluster:/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged$ ls -lah
#~ total 477G
#~ drwxr-xr-x 2 sutan101 depfg   23 Sep 18 00:16 .
#~ drwxr-xr-x 3 sutan101 depfg  133 Sep 17 23:47 ..
#~ -r--r--r-- 1 sutan101 depfg 3.5K Sep 18 00:01 cdo_mergetime_and_monavg.sh
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:16 gswp3-w5e5_obsclim_hurs_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_huss_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:16 gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_prsn_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:16 gswp3-w5e5_obsclim_ps_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:16 gswp3-w5e5_obsclim_rlds_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_tasmax_global_daily_1901_2019_version_2021-09-XX.nc
#~ -r--r--r-- 1 sutan101 depfg  42G Sep 18 00:15 gswp3-w5e5_obsclim_tasmin_global_daily_1901_2019_version_2021-09-XX.nc

#~ # - ssp370
#~ RELATIVE_HUMIDITY_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_hurs_global_daily_2015_2100.nc"
#~ PRECIPITATION_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_pr_global_daily_2015_2100.nc"
#~ PRESSURE_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_ps_global_daily_2015_2100.nc"
#~ SHORTWAVE_RADIATION_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_rsds_global_daily_2015_2100.nc"
#~ WIND_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_sfcwind_global_daily_2015_2100.nc"
#~ TEMPERATURE_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_tas_global_daily_2015_2100.nc"


# initial conditions - example on eejit
MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-08-20c_gmd-paper-irrigated-areas/global/states/"
DATE_FOR_INITIAL_STATES="1999-12-31"


# number of spinup years
NUMBER_OF_SPINUP_YEARS="25"


# location of your pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER=~/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# load modules on eejit
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh

#~ # load modules on azure
#~ source activate pcrglobwb_python3


pcrcalc

#~ # - unset pcraster working threads
#~ unset PCRASTER_NR_WORKER_THREADS

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}
pwd


# run the model for all clones, from 1 to 53

#~ # - for testing
#~ for i in {2..2}
#~ for i in {2..3}

for i in {1..53}

do

CLONE_CODE=${i}
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} &



done


# merging process
python3 deterministic_runner_merging_with_arguments.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} &


wait

