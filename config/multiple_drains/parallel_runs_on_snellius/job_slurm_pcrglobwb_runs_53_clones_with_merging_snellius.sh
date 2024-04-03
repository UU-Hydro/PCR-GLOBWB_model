#!/bin/bash

# using the genoa computational node
#SBATCH -p genoa

# we will use 96 cores within one node
#SBATCH -N 1
## you reserve one node
#SBATCH -n 96
## 96 cores

# wall clock time, 
#SBATCH -t 119:59:00
## this is the time, maximum 120:00:00 hours

# job name
#SBATCH -J pgb_test
## this is the job name


#~ # mail alert at start, end and abortion of execution
#~ #SBATCH --mail-type=ALL
#~
#~ # send mail to this address
#~ #SBATCH --mail-user=XXX@gmail.com



set -x


# configuration (.ini) file
INI_FILE="/home/edwindql/github/UU-Hydro/PCR-GLOBWB_model/config/multiple_drains/parallel_runs_on_snellius/setup_05min_non-linear-gw_based-on_aqueduct-2021.ini"


# starting and end dates
# - historical
STARTING_DATE="1978-01-01"
END_DATE="2019-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from previous model runs.


# location/folder, where you will store output files of your 
# - historical
MAIN_OUTPUT_DIR="/scrcatch-shared/edwindql/pcrglobwb_test_parallel/"


# meteorological forcing files

#~ # - historical reference - gswp3-w5e5
#~ edwin@int5:/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978$
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_hurs_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_huss_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_pr_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_prsn_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_ps_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_rlds_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_rsds_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_sfcwind_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_tas_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_tasmax_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 edwin dfguu  15G Apr 18  2022 gswp3-w5e5_obsclim_tasmin_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc


RELATIVE_HUMIDITY_FORCING_FILE="/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978/gswp3-w5e5_obsclim_hurs_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc"
PRECIPITATION_FORCING_FILE="/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978/gswp3-w5e5_obsclim_pr_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc"
PRESSURE_FORCING_FILE="/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978/gswp3-w5e5_obsclim_ps_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978/gswp3-w5e5_obsclim_rsds_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc"
WIND_FORCING_FILE="/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978/gswp3-w5e5_obsclim_rsds_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc"
TEMPERATURE_FORCING_FILE="/projects/0/dfguu/users/edwin/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/w5e5_1979-2019_with_climatology_on_1978/gswp3-w5e5_obsclim_tas_global_daily_1979-2019_version_2021-09-XX_with_climatology_on_1978.nc"


# initial conditions
MAIN_INITIAL_STATE_FOLDER="/projects/0/dfguu/users/edwin/data/pcrglobwb_input_aqueduct/version_2021-09-16/initial_conditions/"
DATE_FOR_INITIAL_STATES="2019-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from the previous period model runs.


# number of spinup years
NUMBER_OF_SPINUP_YEARS="25"
#~ # - PS: For continuing runs, please set it to zero
#~ NUMBER_OF_SPINUP_YEARS="0"


# location of your pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER=~/PCR-GLOBWB_model/model/


# load the conda enviroment 
# - using the one from /home/edwin/
. /home/edwin/load_all_default.sh


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

