#!/bin/bash
#SBATCH -N 1
#SBATCH -n 192
#SBATCH -p genoa
#SBATCH -t 24:00:00
#SBATCH -J full_couple
#SBATCH --mail-type=END
#SBATCH --mail-user=gcardenas1891@gmail.com

# setting input files and directories ...................................
# folder containing .ini file
INI_FILE="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/config/full_coupling/setup_05min_full_coupling.ini"

# starting and end dates
START_DATE="1980-01-01"
END_DATE="1982-12-31"

# location/folder, where you will store output files of your 
OUTPUT_DIR="/gpfs/work3/0/prjs1311/qualloc/outputs/historic/pcrglobwb_dynqual_qualloc"

# initial conditions
# - PS: for continuing runs (including the transition from the historical to SSP runs), please use the output files from the previous period model runs.
INITIAL_STATE_FOLDER="/gpfs/work3/0/prjs1311/qualloc/data/initial/historic"
MAIN_INITIAL_STATE_FOLDER=${INITIAL_STATE_FOLDER}/pcrglobwb
DATE_FOR_INITIAL_STATES="1979-12-31"

# directory where python script to create configuration files per mask is stored
SCRIPT_CONFIG_FILE_QUALLOC="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/water_management_qualloc/configuration_parallel.py"

# directory where QUAlloc base configuration file is stored
MAIN_QUALLOC_CONFIG_FILE="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/water_management_qualloc/config/parallel/configuration_file_parallel_coupled.cfg"

# number of spinup years
# - PS: For continuing runs, please set it to zero
NUMBER_OF_SPINUP_YEARS="0"

# directory of pcrglobwb model scripts
PCRGLOBWB_MODEL_SCRIPT_FOLDER="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/"

# directory where grid description is stored
GRIDDES="/gpfs/home6/gcardenas/github/PCR-GLOBWB_model/model/water_management_qualloc/griddes_05arcmin_ldd.txt"

# PCR-GLOBWB2 and DynQual output variables' names
PCRGLOBWB_OUTPUT_NETCDFS=baseflow,interflowTotal,directRunoff,discharge,channelStorage,waterTemp,TDSload,BODload,FCload,routedTDS,routedBOD,routedFC,salinity,organic,dissolved_oxygen,pathogen

# QUAlloc output variables' names
QUALLOC_OUTPUT_NETCDFS=demand_domestic_allocated_to_renewable_surfacewater,demand_irrigation_allocated_to_renewable_surfacewater,demand_livestock_allocated_to_renewable_surfacewater,demand_manufacture_allocated_to_renewable_surfacewater,demand_thermoelectric_allocated_to_renewable_surfacewater,demand_domestic_allocated_to_renewable_groundwater,demand_irrigation_allocated_to_renewable_groundwater,demand_livestock_allocated_to_renewable_groundwater,demand_manufacture_allocated_to_renewable_groundwater,demand_thermoelectric_allocated_to_renewable_groundwater,demand_domestic_allocated_to_nonrenewable_groundwater,demand_irrigation_allocated_to_nonrenewable_groundwater,demand_livestock_allocated_to_nonrenewable_groundwater,demand_manufacture_allocated_to_nonrenewable_groundwater,demand_thermoelectric_allocated_to_nonrenewable_groundwater,withdrawal_domestic_allocated_to_renewable_surfacewater,withdrawal_irrigation_allocated_to_renewable_surfacewater,withdrawal_livestock_allocated_to_renewable_surfacewater,withdrawal_manufacture_allocated_to_renewable_surfacewater,withdrawal_thermoelectric_allocated_to_renewable_surfacewater,withdrawal_domestic_allocated_to_renewable_groundwater,withdrawal_irrigation_allocated_to_renewable_groundwater,withdrawal_livestock_allocated_to_renewable_groundwater,withdrawal_manufacture_allocated_to_renewable_groundwater,withdrawal_thermoelectric_allocated_to_renewable_groundwater,withdrawal_domestic_allocated_to_nonrenewable_groundwater,withdrawal_irrigation_allocated_to_nonrenewable_groundwater,withdrawal_livestock_allocated_to_nonrenewable_groundwater,withdrawal_manufacture_allocated_to_nonrenewable_groundwater,withdrawal_thermoelectric_allocated_to_nonrenewable_groundwater,demand_domestic_allocated_to_desalinated_water,demand_irrigation_allocated_to_desalinated_water,demand_livestock_allocated_to_desalinated_water,demand_manufacture_allocated_to_desalinated_water,demand_thermoelectric_allocated_to_desalinated_water,withdrawal_domestic_allocated_to_desalinated_water,withdrawal_irrigation_allocated_to_desalinated_water,withdrawal_livestock_allocated_to_desalinated_water,withdrawal_manufacture_allocated_to_desalinated_water,withdrawal_thermoelectric_allocated_to_desalinated_water,domestic_gross_demand,irrigation_gross_demand,livestock_gross_demand,manufacture_gross_demand,thermoelectric_gross_demand,potential_withdrawal_renewable_surfacewater,potential_withdrawal_renewable_groundwater,potential_withdrawal_nonrenewable_groundwater

# running model ........................................................
# load the conda enviroment on snellius
source activate base
conda activate /gpfs/home6/gcardenas/.conda/envs/geo

# unset pcraster working threads and export the following option 
unset PCRASTER_NR_WORKER_THREADS
export OPENBLAS_NUM_THREADS=1

# starting, end and initial condition years
START_YEAR=${START_DATE:0:4}
END_YEAR=${END_DATE:0:4}
INI_STATE_YEAR=${DATE_FOR_INITIAL_STATES:0:4}

# go to the folder that contain PCR-GLOBWB scripts
cd ${PCRGLOBWB_MODEL_SCRIPT_FOLDER}

# update directory where PCRGLOBWB2 outputs will be stored
MAIN_OUTPUT_DIR=${OUTPUT_DIR}/${START_YEAR}_${END_YEAR}

# directory where QUAlloc outputs will be stored
QUALLOC_OUTPUT_DIR=${MAIN_OUTPUT_DIR}/qualloc

# run the model for all clones, from 1 to 53
for i in {01..53}
  do
  # set the clone code
  CLONE_CODE=${i}
  
  # create qualloc configuration file
  python3 ${SCRIPT_CONFIG_FILE_QUALLOC} ${MAIN_QUALLOC_CONFIG_FILE} ${CLONE_CODE} -mod ${QUALLOC_OUTPUT_DIR} -sd ${START_YEAR} -ed ${END_YEAR} -isd ${INITIAL_STATE_FOLDER} -dfis ${INI_STATE_YEAR}
  QUALLOC_CONFIG_FILE=${MAIN_QUALLOC_CONFIG_FILE:0:-4}_M${CLONE_CODE}.cfg
  
  # run modelling framework
  python3 deterministic_runner_with_arguments.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR} -sd ${START_DATE} -ed ${END_DATE} -misd ${MAIN_INITIAL_STATE_FOLDER} -dfis ${DATE_FOR_INITIAL_STATES} -num_of_sp_years ${NUMBER_OF_SPINUP_YEARS} -qcf ${QUALLOC_CONFIG_FILE} &
  done
wait

# merging state variables ..............................................
# merging PCR-GLOBWB2 state variables
python3 merge_pcraster_maps.py ${END_DATE} ${MAIN_OUTPUT_DIR}/ ${MAIN_INITIAL_STATE_FOLDER} states 8 Global &
wait

# merging QUAlloc state variables
# create folders
OUTPUT_STATE_DIR=${INITIAL_STATE_FOLDER}/${END_YEAR}
mkdir ${OUTPUT_STATE_DIR}
mkdir ${OUTPUT_STATE_DIR}/tmp

# state variables: long-term
python merge_netcdf.py ${QUALLOC_OUTPUT_DIR} ${OUTPUT_STATE_DIR}/tmp outStates ${END_YEAR}-01-01 ${END_YEAR}-12-01 gross_demand_longterm_domestic,gross_demand_longterm_irrigation,gross_demand_longterm_livestock,gross_demand_longterm_manufacture,gross_demand_longterm_thermoelectric,groundwater_longterm_potential_withdrawal,groundwater_longterm_storage,surfacewater_longterm_discharge,surfacewater_longterm_runoff,surfacewater_longterm_organic,surfacewater_longterm_pathogen,surfacewater_longterm_salinity,surfacewater_longterm_temperature NETCDF4 True 53 53 all_lats True &
wait

# state variables: last-day
python merge_netcdf.py ${QUALLOC_OUTPUT_DIR} ${OUTPUT_STATE_DIR}/tmp outStates ${END_YEAR}-12-31 ${END_YEAR}-12-31 groundwater_storage,surfacewater_storage,total_base_flow,total_return_flow NETCDF4 True 53 53 all_lats True &
wait

# regridding states
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/groundwater_longterm_storage_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/groundwater_longterm_storage.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_discharge_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_discharge.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_runoff_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_runoff.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_domestic_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_domestic.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_irrigation_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_irrigation.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_livestock_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_livestock.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_manufacture_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_manufacture.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/gross_demand_longterm_thermoelectric_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/gross_demand_longterm_thermoelectric.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/groundwater_longterm_potential_withdrawal_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/groundwater_longterm_potential_withdrawal.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_temperature_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_temperature.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_organic_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_organic.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_salinity_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_salinity.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} ${OUTPUT_STATE_DIR}/tmp/surfacewater_longterm_pathogen_${END_YEAR}-01-01_to_${END_YEAR}-12-01.nc ${OUTPUT_STATE_DIR}/surfacewater_longterm_pathogen.nc &

cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${OUTPUT_STATE_DIR}/tmp/total_base_flow_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${OUTPUT_STATE_DIR}/total_base_flow.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${OUTPUT_STATE_DIR}/tmp/groundwater_storage_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${OUTPUT_STATE_DIR}/groundwater_storage.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${OUTPUT_STATE_DIR}/tmp/surfacewater_storage_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${OUTPUT_STATE_DIR}/surfacewater_storage.nc &
cdo -v -z zip_9 -setgrid,${GRIDDES} -setday,31 ${OUTPUT_STATE_DIR}/tmp/total_return_flow_${END_YEAR}-12-31_to_${END_YEAR}-12-31.nc ${OUTPUT_STATE_DIR}/total_return_flow.nc &
wait

# merge output netcdf ..................................................
# merging PCR-GLOBWB2 output netcdf files
# create folder
PCRGLOBWB_OUTPUT_NETCDF_DIR=${MAIN_OUTPUT_DIR}/global
mkdir ${PCRGLOBWB_OUTPUT_NETCDF_DIR}

# merge outputs
python merge_netcdf.py ${MAIN_OUTPUT_DIR} ${PCRGLOBWB_OUTPUT_NETCDF_DIR} outMonthAvgNC ${START_DATE} ${END_DATE} ${PCRGLOBWB_OUTPUT_NETCDFS} NETCDF4 True 53 53 all_lats True &
wait

# merging QUAlloc state variables
# create folder
QUALLOC_OUTPUT_NETCDF_DIR=${QUALLOC_OUTPUT_DIR}/global
mkdir ${QUALLOC_OUTPUT_NETCDF_DIR}

# merge outputs
python merge_netcdf.py ${QUALLOC_OUTPUT_DIR} ${QUALLOC_OUTPUT_NETCDF_DIR} out_month_avgNC ${START_YEAR}-01-01 ${END_YEAR}-12-01 ${QUALLOC_OUTPUT_NETCDFS} NETCDF4 True 53 53 all_lats True &
wait

echo "\n... End of model runs (please check your results)."

