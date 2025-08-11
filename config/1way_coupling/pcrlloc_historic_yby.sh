#!/bin/bash
#SBATCH -N 1
#SBATCH -n 192
#SBATCH -p genoa
#SBATCH -t 15:00:00
#SBATCH -J 1wcoup
#SBATCH --mail-type=END
#SBATCH --mail-user=gcardenas1891@gmail.com

# setting input files and directories ...................................
# PCR-GLOBWB2 .....................
# folder containing .ini file
INI_FILE="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/config/1way_coupling/setup_05min_1way_coupling.ini"

# starting and end dates
YEAR=$1
START_DATE="${YEAR}-01-01"
END_DATE="${YEAR}-12-31"

# location/folder, where you will store output files of your 
OUTPUT_DIR="/gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_qualloc"

# initial conditions
# - PS: for continuing runs (including the transition from the historical to SSP runs), please use the output files from the previous period model runs.
PCRGLOBWB_INITIAL_STATE_FOLDER="/gpfs/work3/0/prjs1311/qualloc/data/initial/historic/pcrglobwb_1w"
DATE_FOR_INITIAL_STATES="$((YEAR - 1))-12-31"

# number of spinup years
# - PS: For continuing runs, please set it to zero
NUMBER_OF_SPINUP_YEARS="0"

# directory of pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/model/"

# PCR-GLOBWB2 and DynQual output variables' names
PCRGLOBWB_OUTPUT_NETCDFS=discharge,channelStorage,totalWaterStorageVolume

# QUAlloc .........................
# directory where QUAlloc base configuration file is stored
QUALLOC_CONFIG_FILE_FOLDER="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/model/water_management_qualloc/config/parallel"
QUALLOC_CONFIG_FILE_NAME="configuration_file_parallel_1w_coupled.cfg"

# directory where python script used to create configuration files per mask for parallel run is stored
SCRIPT_CONFIG_FILE_QUALLOC="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/model/water_management_qualloc/configuration_parallel.py"

# initial conditions
QUALLOC_INITIAL_STATE_FOLDER="/gpfs/work3/0/prjs1311/qualloc/data/initial/historic/qualloc_1w"

# water quality flag to consider sectoral water quality requirements (True or False)
WQ_FLAG=$2

# directory where grid description is stored
GRIDDES="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/model/water_management_qualloc/griddes_05arcmin_ldd.txt"

# QUAlloc output variables' names
QUALLOC_OUTPUT_NETCDFS=demand_domestic_allocated_to_renewable_surfacewater,demand_irrigation_allocated_to_renewable_surfacewater,demand_livestock_allocated_to_renewable_surfacewater,demand_manufacture_allocated_to_renewable_surfacewater,demand_thermoelectric_allocated_to_renewable_surfacewater,demand_domestic_allocated_to_renewable_groundwater,demand_irrigation_allocated_to_renewable_groundwater,demand_livestock_allocated_to_renewable_groundwater,demand_manufacture_allocated_to_renewable_groundwater,demand_thermoelectric_allocated_to_renewable_groundwater,demand_domestic_allocated_to_nonrenewable_groundwater,demand_irrigation_allocated_to_nonrenewable_groundwater,demand_livestock_allocated_to_nonrenewable_groundwater,demand_manufacture_allocated_to_nonrenewable_groundwater,demand_thermoelectric_allocated_to_nonrenewable_groundwater,withdrawal_domestic_allocated_to_renewable_surfacewater,withdrawal_irrigation_allocated_to_renewable_surfacewater,withdrawal_livestock_allocated_to_renewable_surfacewater,withdrawal_manufacture_allocated_to_renewable_surfacewater,withdrawal_thermoelectric_allocated_to_renewable_surfacewater,withdrawal_domestic_allocated_to_renewable_groundwater,withdrawal_irrigation_allocated_to_renewable_groundwater,withdrawal_livestock_allocated_to_renewable_groundwater,withdrawal_manufacture_allocated_to_renewable_groundwater,withdrawal_thermoelectric_allocated_to_renewable_groundwater,withdrawal_domestic_allocated_to_nonrenewable_groundwater,withdrawal_irrigation_allocated_to_nonrenewable_groundwater,withdrawal_livestock_allocated_to_nonrenewable_groundwater,withdrawal_manufacture_allocated_to_nonrenewable_groundwater,withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater,demand_domestic_allocated_to_desalinated_water,demand_irrigation_allocated_to_desalinated_water,demand_livestock_allocated_to_desalinated_water,demand_manufacture_allocated_to_desalinated_water,demand_thermoelectric_allocated_to_desalinated_water,withdrawal_domestic_allocated_to_desalinated_water,withdrawal_irrigation_allocated_to_desalinated_water,withdrawal_livestock_allocated_to_desalinated_water,withdrawal_manufacture_allocated_to_desalinated_water,withdrawal_thermoelectric_allocated_to_desalinated_water,domestic_gross_demand,irrigation_gross_demand,livestock_gross_demand,manufacture_gross_demand,thermoelectric_gross_demand,potential_withdrawal_renewable_surfacewater,potential_withdrawal_renewable_groundwater,potential_withdrawal_nonrenewable_groundwater


# running model ........................................................
# load the conda enviroment on snellius
source activate base
conda activate /gpfs/home6/gcardenas/.conda/envs/geo

# unset pcraster working threads and export the following option 
unset PCRASTER_NR_WORKER_THREADS
export OPENBLAS_NUM_THREADS=1

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# update directory where PCRGLOBWB2 outputs will be stored
MAIN_OUTPUT_DIR=${OUTPUT_DIR}_wq${WQ_FLAG}/${YEAR}

# update directory where PCRGLOBWB2 state variables will be stored
PCRGLOBWB_INITIAL_STATE_FOLDER=${PCRGLOBWB_INITIAL_STATE_FOLDER}_wq${WQ_FLAG}

# update directory where QUAlloc state variables will be stored
QUALLOC_INITIAL_STATE_FOLDER=${QUALLOC_INITIAL_STATE_FOLDER}_wq${WQ_FLAG}

# define starting and end year for QUAlloc
START_YEAR=${START_DATE:0:4}
END_YEAR=${END_DATE:0:4}

# directory where QUAlloc outputs will be stored
QUALLOC_OUTPUT_DIR=${MAIN_OUTPUT_DIR}/qualloc

# create folder to keep generated QUAlloc configuration files
CONFIG_FILE_OUTPUT_FOLDER=${QUALLOC_CONFIG_FILE_FOLDER}/${START_YEAR}_wq${WQ_FLAG}
mkdir ${CONFIG_FILE_OUTPUT_FOLDER}

# run the model for all clones, from 1 to 53
for i in {01..53}
  do
  # set the clone code
  CLONE_CODE=${i}
  
  # create qualloc configuration file
  python3 ${SCRIPT_CONFIG_FILE_QUALLOC} ${QUALLOC_CONFIG_FILE_FOLDER} ${QUALLOC_CONFIG_FILE_NAME} ${CLONE_CODE} -mod ${QUALLOC_OUTPUT_DIR} -sy ${START_YEAR} -ey ${END_YEAR} -qisd ${QUALLOC_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -wqf ${WQ_FLAG}
  QUALLOC_CONFIG_FILE=${CONFIG_FILE_OUTPUT_FOLDER}/${QUALLOC_CONFIG_FILE_NAME:0:-4}_M${CLONE_CODE}.cfg
  
  # run modelling framework
  python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE} -ed ${END_DATE} -misd ${PCRGLOBWB_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} -qcf ${QUALLOC_CONFIG_FILE} &
  done
wait

# removing temporary folder
rm -r ${CONFIG_FILE_OUTPUT_FOLDER}


# merging state variables ..............................................
# merging PCR-GLOBWB2 state variables
python3 merge_pcraster_maps.py ${END_DATE} ${MAIN_OUTPUT_DIR}/ ${PCRGLOBWB_INITIAL_STATE_FOLDER} states 8 Global &
wait

# merging QUAlloc state variables
# create folders
mkdir ${QUALLOC_INITIAL_STATE_FOLDER}/tmp
DATE_FOR_FINAL_STATES=${YEAR}-12-31

# state variables: long-term
LONGTERM_STATES=gross_demand_longterm_domestic_${DATE_FOR_FINAL_STATES},gross_demand_longterm_irrigation_${DATE_FOR_FINAL_STATES},gross_demand_longterm_livestock_${DATE_FOR_FINAL_STATES},gross_demand_longterm_manufacture_${DATE_FOR_FINAL_STATES},gross_demand_longterm_thermoelectric_${DATE_FOR_FINAL_STATES},groundwater_longterm_potential_withdrawal_${DATE_FOR_FINAL_STATES},groundwater_longterm_storage_${DATE_FOR_FINAL_STATES},surfacewater_longterm_discharge_${DATE_FOR_FINAL_STATES},surfacewater_longterm_runoff_${DATE_FOR_FINAL_STATES},surfacewater_longterm_organic_${DATE_FOR_FINAL_STATES},surfacewater_longterm_pathogen_${DATE_FOR_FINAL_STATES},surfacewater_longterm_salinity_${DATE_FOR_FINAL_STATES},surfacewater_longterm_temperature_${DATE_FOR_FINAL_STATES}
python merge_netcdf.py ${QUALLOC_OUTPUT_DIR} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp outStates ${END_YEAR}-01-01 ${END_YEAR}-12-01 ${LONGTERM_STATES} NETCDF4 True 53 53 all_lats True &
wait

# state variables: last-day
SHORTTERM_STATES=groundwater_storage_${DATE_FOR_FINAL_STATES},surfacewater_storage_${DATE_FOR_FINAL_STATES},total_base_flow_${DATE_FOR_FINAL_STATES},total_return_flow_${DATE_FOR_FINAL_STATES}
python merge_netcdf.py ${QUALLOC_OUTPUT_DIR} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp outStates ${END_YEAR}-12-31 ${END_YEAR}-12-31 ${SHORTTERM_STATES} NETCDF4 True 53 53 all_lats True &
wait

# regridding states
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/groundwater_longterm_storage_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/groundwater_longterm_storage_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_longterm_discharge_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_longterm_discharge_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_longterm_runoff_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_longterm_runoff_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/gross_demand_longterm_domestic_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/gross_demand_longterm_domestic_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/gross_demand_longterm_irrigation_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/gross_demand_longterm_irrigation_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/gross_demand_longterm_livestock_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/gross_demand_longterm_livestock_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/gross_demand_longterm_manufacture_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/gross_demand_longterm_manufacture_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/gross_demand_longterm_thermoelectric_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/gross_demand_longterm_thermoelectric_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/groundwater_longterm_potential_withdrawal_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/groundwater_longterm_potential_withdrawal_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_longterm_temperature_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_longterm_temperature_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_longterm_organic_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_longterm_organic_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_longterm_salinity_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_longterm_salinity_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_longterm_pathogen_${DATE_FOR_FINAL_STATES}_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_longterm_pathogen_${DATE_FOR_FINAL_STATES}.nc &

cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/total_base_flow_${DATE_FOR_FINAL_STATES}_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${QUALLOC_INITIAL_STATE_FOLDER}/total_base_flow_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/groundwater_storage_${DATE_FOR_FINAL_STATES}_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${QUALLOC_INITIAL_STATE_FOLDER}/groundwater_storage_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/surfacewater_storage_${DATE_FOR_FINAL_STATES}_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${QUALLOC_INITIAL_STATE_FOLDER}/surfacewater_storage_${DATE_FOR_FINAL_STATES}.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${QUALLOC_INITIAL_STATE_FOLDER}/tmp/total_return_flow_${DATE_FOR_FINAL_STATES}_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${QUALLOC_INITIAL_STATE_FOLDER}/total_return_flow_${DATE_FOR_FINAL_STATES}.nc &
wait

# remove temporary folder
rm -r ${QUALLOC_INITIAL_STATE_FOLDER}/tmp


# merge output netcdf ..................................................
# merging outputs to global extension
OUTPUT_NETCDF_DIR=${MAIN_OUTPUT_DIR}/global
mkdir ${OUTPUT_NETCDF_DIR}

# merging PCR-GLOBWB2 output netcdf files
# create folder
PCRGLOBWB_OUTPUT_NETCDF_DIR=${OUTPUT_NETCDF_DIR}/pcrglobwb
mkdir ${PCRGLOBWB_OUTPUT_NETCDF_DIR}

# merge outputs
MERGE_NETCDF_PY="/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/config/merge_outputs.sh"
sbatch ${MERGE_NETCDF_PY} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} ${MAIN_OUTPUT_DIR} ${PCRGLOBWB_OUTPUT_NETCDF_DIR} outMonthAvgNC ${START_YEAR}-01-01 ${END_YEAR}-12-01 ${PCRGLOBWB_OUTPUT_NETCDFS} False &

# merging QUAlloc output netcdf files
# create folder
QUALLOC_OUTPUT_NETCDF_DIR=${OUTPUT_NETCDF_DIR}/qualloc
mkdir ${QUALLOC_OUTPUT_NETCDF_DIR}

# merge outputs
sbatch ${MERGE_NETCDF_PY} ${PCRGLOBWB_MODEL_SCRIPT_FOLDER} ${QUALLOC_OUTPUT_DIR} ${QUALLOC_OUTPUT_NETCDF_DIR} out_month_avgNC ${START_YEAR}-01-01 ${END_YEAR}-12-01 ${QUALLOC_OUTPUT_NETCDFS} True &

echo -e "\n... Finished model runs for $YEAR." &
wait


# submit next year .....................................................
if [ "$YEAR" -le 2018 ]; then
  sbatch "/gpfs/home6/gcardenas/github/qualloc/PCR-GLOBWB_model/config/1way_coupling/pcrlloc_historic_yby.sh" "$((YEAR + 1))" "${WQ_FLAG}"
fi
