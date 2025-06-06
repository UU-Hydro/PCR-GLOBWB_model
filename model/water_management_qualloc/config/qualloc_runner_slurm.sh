#!/bin/bash
#SBATCH -N 1
#SBATCH -n 53
#SBATCH -J hist_wqTrue
#SBATCH --mail-type=ALL
#SBATCH --mail-user=gcardenas1891@gmail.com

# load the conda enviroment on eejit
. /eejit/home/carde003/load_default.sh

# directory of QUAlloc model
MODEL_DIR_SCRIPTS="/eejit/home/carde003/github/QUAlloc_coupled/PCR-GLOBWB_model/model/water_management_qualloc"

# directory of configuration file (.cfg)
CFG_FILE="/eejit/home/carde003/github/QUAlloc_coupled/PCR-GLOBWB_model/model/water_management_qualloc/config/configuration_file_test_eejit_slurm.cfg"

# starting and end years
START_YEAR="1980"
END_YEAR="1980"

# sectoral water quality requirements
SWQ_FLAG="True"

# name of the simulation
SCENARIO_NAME="historic_wq=True"

# directory where input files are stored
MAIN_INPUT_DIR="/scratch/depfg/carde003/qualloc/data/"

# directory where output files will be stored 
MAIN_OUTPUT_DIR="/scratch/depfg/carde003/qualloc/outputs/historic/true"

# directory where maks fr parallel simulation are stored
MASK_DIR="maps/masks/mask_"

# directory where initial states are stored
INI_DIR="initial/historic"

# year for the initial states
YEAR_INITIAL_STATES="1979"

# directory where griddes file is stored
GRIDDES="/eejit/home/carde003/github/QUAlloc_coupled/PCR-GLOBWB_model/model/water_management_qualloc/griddes_05arcmin_ldd.txt"

# run QUAlloc
#for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
#  do
#  # adjusting general input data
#  OUTPUT_DIR=${MAIN_OUTPUT_DIR}/M${i}
#  CLONE_MAP=${MASK_DIR}M${i}.map
#  
#  # adjusting initial condition files
#  GW_BFL=${INI_DIR}/${YEAR_INITIAL_STATES}/total_base_flow.nc
#  GW_STO=${INI_DIR}/${YEAR_INITIAL_STATES}/groundwater_storage.nc
#  SW_STO=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_storage.nc
#  LT_STO=${INI_DIR}/${YEAR_INITIAL_STATES}/groundwater_longterm_storage.nc
#  LT_DIS=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_longterm_discharge.nc
#  LT_ROF=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_longterm_runoff.nc
#  LT_DOM=${INI_DIR}/${YEAR_INITIAL_STATES}/gross_demand_longterm_domestic.nc
#  LT_IRR=${INI_DIR}/${YEAR_INITIAL_STATES}/gross_demand_longterm_irrigation.nc
#  LT_LIV=${INI_DIR}/${YEAR_INITIAL_STATES}/gross_demand_longterm_livestock.nc
#  LT_MAN=${INI_DIR}/${YEAR_INITIAL_STATES}/gross_demand_longterm_manufacture.nc
#  LT_THR=${INI_DIR}/${YEAR_INITIAL_STATES}/gross_demand_longterm_thermoelectric.nc
#  LT_PGW=${INI_DIR}/${YEAR_INITIAL_STATES}/groundwater_longterm_potential_withdrawal.nc
#  LT_PSW=None
#  SW_RFL=${INI_DIR}/${YEAR_INITIAL_STATES}/total_return_flow.nc
#  LT_SWT=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_longterm_temperature.nc
#  LT_BOD=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_longterm_organic.nc
#  LT_TDS=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_longterm_salinity.nc
#  LT_FCL=${INI_DIR}/${YEAR_INITIAL_STATES}/surfacewater_longterm_pathogen.nc
#  
#  # running QUAlloc with arguments
#  python ${MODEL_DIR_SCRIPTS}/qualloc_runner.py ${CFG_FILE} ${SCENARIO_NAME} ${MAIN_INPUT_DIR} ${OUTPUT_DIR} ${CLONE_MAP} ${START_YEAR} ${END_YEAR} ${GW_BFL} ${GW_STO} ${SW_STO} ${LT_STO} ${LT_DIS} ${LT_ROF} ${LT_DOM} ${LT_IRR} ${LT_LIV} ${LT_MAN} ${LT_THR} ${LT_PGW} ${LT_PSW} ${SW_RFL} ${SWQ_FLAG} ${LT_SWT} ${LT_BOD} ${LT_TDS} ${LT_FCL} &
#  done
#wait

# merge state variables ................................................
# create folders
OUTPUT_STATE_DIR=${MAIN_INPUT_DIR}/${INI_DIR}/${END_YEAR}
mkdir ${OUTPUT_STATE_DIR}
mkdir ${OUTPUT_STATE_DIR}/tmp

# state variables: long-term
python ${MODEL_DIR_SCRIPTS}/merge_netcdf.py ${MAIN_OUTPUT_DIR} ${OUTPUT_STATE_DIR}/tmp outStates ${END_YEAR}-01-01 ${END_YEAR}-12-01 gross_demand_longterm_domestic,gross_demand_longterm_irrigation,gross_demand_longterm_livestock,gross_demand_longterm_manufacture,gross_demand_longterm_thermoelectric,groundwater_longterm_potential_withdrawal,groundwater_longterm_storage,surfacewater_longterm_discharge,surfacewater_longterm_runoff,surfacewater_longterm_organic,surfacewater_longterm_pathogen,surfacewater_longterm_salinity,surfacewater_longterm_temperature NETCDF4 True 53 53 all_lats True
wait

# state variables: initial conditions
python ${MODEL_DIR_SCRIPTS}/merge_netcdf.py ${MAIN_OUTPUT_DIR} ${OUTPUT_STATE_DIR}/tmp outStates ${END_YEAR}-12-01 ${END_YEAR}-12-01 groundwater_storage,surfacewater_storage,total_base_flow,total_return_flow NETCDF4 True 53 53 all_lats True
wait

# regridding states
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/groundwater_longterm_storage_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/groundwater_longterm_storage.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_discharge_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_discharge.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_runoff$_{END_YEAR}-01-01_to_.${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_runoff.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_domestic_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_domestic.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_irrigation_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_irrigation.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_livestock_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_livestock.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_manufacture_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_manufacture.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_thermoelectric_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_thermoelectric.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/groundwater_longterm_potential_withdrawal_storage_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/groundwater_longterm_potential_withdrawal.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_temperature_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_temperature.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_organic_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_organic.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_salinity_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_salinity.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_pathogen_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_pathogen.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/total_base_flow_${END_YEAR}-12-01_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/total_base_flow.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/groundwater_storage_${END_YEAR}-12-01_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/groundwater_storage.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_storage_${END_YEAR}-12-01_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_storage.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/total_return_flow_${END_YEAR}-12-01_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/total_return_flow.nc &
wait

echo "end of model runs (please check your results)"
