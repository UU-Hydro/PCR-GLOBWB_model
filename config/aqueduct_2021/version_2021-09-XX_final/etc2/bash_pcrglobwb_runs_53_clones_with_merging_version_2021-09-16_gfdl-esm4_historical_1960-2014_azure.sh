#!/bin/bash 


set -x


# folder containing .ini file
# - with bash
INI_FOLDER=$(pwd)


# configuration (.ini) file
# - historical
INI_FILE=${INI_FOLDER}/"setup_05min_historical_version_2021-09-16.ini"
#~ # - ssp370
#~ INI_FILE=${INI_FOLDER}/"setup_05min_ssp370_version_2021-09-16.ini"


# starting and end dates
# - historical
STARTING_DATE="1960-01-01"
END_DATE="2014-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from previous model runs.


# location/folder, where you will store output files of your 
# - historical
MAIN_OUTPUT_DIR="/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/gfdl-esm4/historical/begin_from_1960/"
#~ # - ssp370
#~ MAIN_OUTPUT_DIR="/datadrive/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/gfdl-esm4/ssp370/continue_from_2015/"


# meteorological forcing files

# - historical reference - gswp3-w5e5
RELATIVE_HUMIDITY_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_hurs_global_daily_1901_2019_version_2021-09-XX.nc"
PRECIPITATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX.nc"
PRESSURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_ps_global_daily_1901_2019_version_2021-09-XX.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc"
WIND_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc"
TEMPERATURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX.nc"

#~ # - ssp370
#~ RELATIVE_HUMIDITY_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_hurs_global_daily_2015_2100.nc"
#~ PRECIPITATION_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_pr_global_daily_2015_2100.nc"
#~ PRESSURE_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_ps_global_daily_2015_2100.nc"
#~ SHORTWAVE_RADIATION_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_rsds_global_daily_2015_2100.nc"
#~ WIND_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_sfcwind_global_daily_2015_2100.nc"
#~ TEMPERATURE_FORCING_FILE="/mnt/pcrglobwb/pcrglobwb_input/forcing/gfdl-esm4_w5e5_ssp370_tas_global_daily_2015_2100.nc"


# initial conditions
MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-08-20c_gmd-paper-irrigated-areas/global/states/"
DATE_FOR_INITIAL_STATES="1999-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from previous model runs.


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

#~ # - loop through all clones
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

