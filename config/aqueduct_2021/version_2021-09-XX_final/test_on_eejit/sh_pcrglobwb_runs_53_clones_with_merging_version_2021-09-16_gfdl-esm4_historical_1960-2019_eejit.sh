#!/bin/bash 


set -x


# folder containing .ini file
# - with bash
INI_FOLDER=$(pwd)


# configuration (.ini) file
# - historical
INI_FILE=${INI_FOLDER}/"setup_05min_historical_version_2021-09-16_global_max_gw_on_eejit.ini"


# starting and end dates
# - historical
STARTING_DATE="1960-01-01"
END_DATE="2019-01-31"


# location/folder, where you will store output files of your 
# pcrglobwb output folder
MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-09-18/begin_from_1959/"


# meteorological forcing files

# - historical reference - gswp3-w5e5
RELATIVE_HUMIDITY_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_hurs_global_daily_1901_2019_version_2021-09-XX.nc"
PRECIPITATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX.nc"
PRESSURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_ps_global_daily_1901_2019_version_2021-09-XX.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc"
WIND_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc"
TEMPERATURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX.nc"


# initial conditions
MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-08-20c_gmd-paper-irrigated-areas/global/states/"
DATE_FOR_INITIAL_STATES="1999-12-31"


# number of spinup years
NUMBER_OF_SPINUP_YEARS="25"


# location of your pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER=~/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# load modules on eejit
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh


# test pcraster
pcrcalc


# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}
pwd


# a global run

python3 deterministic_runner_with_arguments.py ${INI_FILE} debug -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} 


echo "end of model runs (please check your results)"

