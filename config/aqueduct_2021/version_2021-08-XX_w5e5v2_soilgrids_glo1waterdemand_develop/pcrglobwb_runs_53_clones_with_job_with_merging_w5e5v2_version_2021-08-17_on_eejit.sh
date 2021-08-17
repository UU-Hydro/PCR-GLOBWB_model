#!/bin/bash 

#!/bin/bash 
#SBATCH -N 1
#SBATCH -n 96

#~ #SBATCH -t 1:00

#SBATCH -J aqw5e5v2

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


set -x

#~ echo "Arg 0: $0"
#~ echo "Arg 1: $1"
#~ echo "Arg 2: $2"
#~ 
#~ for arg in "$@"
#~ do
    #~ echo "$arg"
#~ done

#~ # get the aguments
#~ INI_FILE=$1
#~ MAIN_OUTPUT_DIR=$2
#~ STARTING_DATE=$3
#~ END_DATE=$4
#~ MAIN_INITIAL_STATE_FOLDER=$5
#~ DATE_FOR_INITIAL_STATES=$6
#~ PRECIPITATION_FORCING_FILE=$7
#~ TEMPERATURE_FORCING_FILE=$8
#~ REF_POT_ET_FORCING_FILE=$9
#~ BASEFLOW_EXPONENT=${10}
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER=${11}


INI_FILE=${SLURM_SUBMIT_DIR}/"setup_05min_w5e5v2_version_2021-08-17.ini"

#~ # using bash
#~ INI_FILE=$(pwd)/"setup_05min_develop.ini"

#~ # using bash on azure
#~ INI_FILE=$(pwd)/"setup_05min_develop_on_azure.ini"


MAIN_OUTPUT_DIR="/scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/w5e5v2_version_2021-08-17/"

#~ # on azure
#~ MAIN_OUTPUT_DIR="/datadrive/pgb/pcrglobwb_aqueduct_2021/version_2021-06-23_w5e5v2_updated_gmd_parameters/"


STARTING_DATE="1978-01-01"
END_DATE="2019-12-31"


PRECIPITATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/pr_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
TEMPERATURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/tas_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
PRESSURE_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/ps_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
WIND_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/sfcWind_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
SHORTWAVE_RADIATION_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/rsds_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
RELATIVE_HUMIDITY_FORCING_FILE="/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/hurs_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"


#~ (pcrglobwb_python3) sutan101@gpu038.cluster:/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978$ pwd
#~ /scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978
#~ (pcrglobwb_python3) sutan101@gpu038.cluster:/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978$
#~ (pcrglobwb_python3) sutan101@gpu038.cluster:/scratch/depfg/sutan101/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978$ ls -lah *
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 hurs_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 huss_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg 5.5K Jun 10 14:23 merge_with_climatology_and_calculate_monthly.sh
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 pr_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 psl_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 ps_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 rlds_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 rsds_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 sfcWind_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 tasmax_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:24 tasmin_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc
#~ -rw-r--r-- 1 sutan101 depfg  15G Jun 10 14:25 tas_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc

#~ # on azure
#~ PRECIPITATION_FORCING_FILE="/datadrive/pgb/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/pr_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
#~ TEMPERATURE_FORCING_FILE="/datadrive/pgb/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/tas_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
#~ PRESSURE_FORCING_FILE="/datadrive/pgb/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/ps_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
#~ WIND_FORCING_FILE="/datadrive/pgb/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/sfcWind_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
#~ SHORTWAVE_RADIATION_FORCING_FILE="/datadrive/pgb/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/rsds_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"
#~ RELATIVE_HUMIDITY_FORCING_FILE="/datadrive/pgb/data/isimip_forcing/w5e5_version_2.0/downloaded_on_2021-06-09/merged/merged_1979-2019_with_climatology_on_1978/hurs_W5E5v2.0_19790101-20191231_with_climatology_on_1978.nc"


PCRGLOBWB_MODEL_SCRIPT_FOLDER="/quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"

#~ # on azure
#~ PCRGLOBWB_MODEL_SCRIPT_FOLDER="/home/pgb/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/"



# load modules on eejit
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh

#~ # load modules on azure
#~ source activate pcrglobwb_python3


pcrcalc

# - unset pcraster working threads
unset PCRASTER_NR_WORKER_THREADS

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# run the model for all clones, from 1 to 53

#~ # - for testing
#~ for i in {2..3}
for i in {2..2}

#~ for i in {1..53}

do

CLONE_CODE=${i}
python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} -pff ${PRECIPITATION_FORCING_FILE} -tff ${TEMPERATURE_FORCING_FILE} -presff ${PRESSURE_FORCING_FILE} -windff ${WIND_FORCING_FILE} -swradff ${SHORTWAVE_RADIATION_FORCING_FILE} -relhumff ${RELATIVE_HUMIDITY_FORCING_FILE} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} &

done


#~ # merging process
#~ python3 deterministic_runner_merging_with_arguments.py ${INI_FILE} parallel -mod ${MAIN_OUTPUT_DIR} -sd ${STARTING_DATE} -ed ${END_DATE} &


wait

