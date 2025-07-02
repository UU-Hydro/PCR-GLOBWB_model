#!/bin/bash
#SBATCH -N 1
#SBATCH -n 52
#SBATCH -p rome
#SBATCH -t 24:00:00
#SBATCH -J merging
#SBATCH --mail-type=END
#SBATCH --mail-user=gcardenas1891@gmail.com

# merging output netcdf files
# defining system variables
MODEL_SCRIPT_FOLDER=$1
MAIN_OUTPUT_DIR=$2
OUTPUT_NETCDF_DIR=$3
FILE_TYPE=$4
START_DATE=$5
END_DATE=$6
OUTPUT_NETCDFS=$7
MV_DEFAULT=$8

# changing directory to folder where merge_netcdf.poy is located
cd ${MODEL_SCRIPT_FOLDER}

# merge outputs
python merge_netcdf.py ${MAIN_OUTPUT_DIR} ${OUTPUT_NETCDF_DIR} ${FILE_TYPE} ${START_DATE} ${END_DATE} ${OUTPUT_NETCDFS} NETCDF4 True 53 53 all_lats ${MV_DEFAULT} &
wait
