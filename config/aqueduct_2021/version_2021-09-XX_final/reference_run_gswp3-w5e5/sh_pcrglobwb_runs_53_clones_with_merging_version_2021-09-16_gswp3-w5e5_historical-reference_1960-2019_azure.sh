#!/bin/bash 


set -x


# folder containing .ini file
# - with bash
INI_FOLDER=$(pwd)


# configuration (.ini) file
# - historical
INI_FILE=${INI_FOLDER}/"setup_05min_historical_version_2021-09-16_on_pcrglobwb-azure.ini"


# starting and end dates
# - historical
STARTING_DATE="1960-01-01"
END_DATE="2019-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from previous model runs.


# location/folder, where you will store output files of your 
# - historical
MAIN_OUTPUT_DIR="/datadrive/edwin/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/gswp3-w5e5_rerun/historical-reference/begin_from_1960/"


# meteorological forcing files

# - historical reference - gswp3-w5e5
RELATIVE_HUMIDITY_FORCING_FILE="/datadrive/pcrglobwb/isimip3a_forcing/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_hurs_global_daily_1901_2019_version_2021-09-XX.nc"
PRECIPITATION_FORCING_FILE="/datadrive/pcrglobwb/isimip3a_forcing/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX.nc"
PRESSURE_FORCING_FILE="/datadrive/pcrglobwb/isimip3a_forcing/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_ps_global_daily_1901_2019_version_2021-09-XX.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/datadrive/pcrglobwb/isimip3a_forcing/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc"
WIND_FORCING_FILE="/datadrive/pcrglobwb/isimip3a_forcing/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc"
TEMPERATURE_FORCING_FILE="/datadrive/pcrglobwb/isimip3a_forcing/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX.nc"

#~ sutan101@login01.cluster:/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged$ ls -lah
#~ total 477G
#~ drwxr-xr-x 2 sutan101 depfg   23 Sep 24 04:38 .
#~ drwxr-xr-x 3 sutan101 depfg  134 Sep 24 04:38 ..
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


# initial conditions
MAIN_INITIAL_STATE_FOLDER="/datadrive/pcrglobwb/pcrglobwb_input/version_2021-09-16/initial_conditions/"
DATE_FOR_INITIAL_STATES="2019-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from the previous period model runs.


# number of spinup years
NUMBER_OF_SPINUP_YEARS="25"
#~ # - PS: For continuing runs, please set it to zero
#~ NUMBER_OF_SPINUP_YEARS="0"


# location of your pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER=~/PCR-GLOBWB_model/model/


# load the conda enviroment on azure
source activate pcrglobwb_python3


# unset pcraster working threads (due to a limited number of cores on the Azure VM)
unset PCRASTER_NR_WORKER_THREADS


# test pcraster
pcrcalc


# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}
pwd


# run the model for all clones, from 1 to 53

#~ # - for testing
#~ for i in {2..2}

# - loop through all clones
for i in {1..53}

do

CLONE_CODE=${i}
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} &


done


# process for merging files at the global extent
python3 deterministic_runner_merging_with_arguments.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} &


# wait until process is finished
wait


echo "end of model runs (please check your results)"

