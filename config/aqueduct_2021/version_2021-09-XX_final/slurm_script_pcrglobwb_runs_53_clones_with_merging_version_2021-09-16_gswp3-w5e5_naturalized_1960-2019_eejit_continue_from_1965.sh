#!/bin/bash
#SBATCH -N 1
#SBATCH -n 96

#~ #SBATCH -t 240:00:00

#~ #SBATCH -p defq

#SBATCH -J natr-pgb_continue_from_1965

#~ #SBATCH --exclusive

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


# folder containing .ini file
#~ INI_FOLDER=$(pwd)
INI_FOLDER=~/github/UU-Hydro/PCR-GLOBWB_model/config/aqueduct_2021/version_2021-09-XX_final/


# configuration (.ini) file
INI_FILE=${INI_FOLDER}/"setup_05min_historical_version_2021-09-16_naturalized_no-water_no-reservoirs_two-natural-landcovers.ini"


# starting and end dates
STARTING_DATE="1965-01-01"
END_DATE="2019-12-31"


# location/folder, where you will store output files of your 
MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_naturalized/version_2021-09-16_naturalized/gswp3-w5e5/historical-reference/continue_from_1965/"


# meteorological forcing files

# - historical reference - gswp3-w5e5
RELATIVE_HUMIDITY_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_hurs_global_daily_1901_2019_version_2021-09-XX.nc"
PRECIPITATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_pr_global_daily_1901_2019_version_2021-09-XX.nc"
PRESSURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_ps_global_daily_1901_2019_version_2021-09-XX.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_rsds_global_daily_1901_2019_version_2021-09-XX.nc"
WIND_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_sfcwind_global_daily_1901_2019_version_2021-09-XX.nc"
TEMPERATURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/isimip3a_version_2021-09-XX/copied_on_2021-09-XX/GSWP3-W5E5/merged/gswp3-w5e5_obsclim_tas_global_daily_1901_2019_version_2021-09-XX.nc"



# initial conditions
#~ MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/data/pcrglobwb_input_aqueduct/version_2021-09-16/initial_conditions/"
#~ DATE_FOR_INITIAL_STATES="2019-12-31"
# - PS: for continuing runs (including the transition from the historical to SSP runs), plese use the output files from the previous period model runs.

MAIN_INITIAL_STATE_FOLDER="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_naturalized/version_2021-09-16_naturalized/gswp3-w5e5/historical-reference/begin_from_1960/global/states/"
DATE_FOR_INITIAL_STATES="1964-12-31"


# number of spinup years
#~ NUMBER_OF_SPINUP_YEARS="25"
# - PS: For continuing runs, please set it to zero
NUMBER_OF_SPINUP_YEARS="0"


# location of your pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER=~/github/UU-Hydro/PCR-GLOBWB_model/model/


# load the conda enviroment on eejit
. /eejit/home/sutan101/load_anaconda_and_my_default_env.sh

# - using the old conda environment (to test whether pcraster 4.3.0 is faster than 4.4.1)
conda activate /quanta1/home/sutan101/opt/miniconda3/envs/pcrglobwb_python3


# unset pcraster working threads 
unset PCRASTER_NR_WORKER_THREADS

# - you may have to activate the following
export OPENBLAS_NUM_THREADS=1

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

