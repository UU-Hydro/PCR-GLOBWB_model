#!/bin/bash

echo "Arg 0: $0"
echo "Arg 1: $1"
echo "Arg 2: $2"

for arg in "$@"
do
    echo "$arg"
done

set -x

MAIN_PCR_OUTPUT_DIR=$1
SUB_PCR_OUTPUT_DIR=$2

# go to the netcdf output folder
cd ${MAIN_PCR_OUTPUT_DIR}
cd ${SUB_PCR_OUTPUT_DIR}
cd netcdf

# copy the reccession coefficient used
cp ${MAIN_PCR_OUTPUT_DIR}/${SUB_PCR_OUTPUT_DIR}/maps/globalalpha.map .

# convert nc to map
gdal_translate -of PCRaster gwRecharge_annuaAvg_output.nc gwRecharge_annuaAvg_output.map
mapattr -c globalalpha.map gwRecharge_annuaAvg_output.map

# calculate the initial storGroundwater
pcrcalc estimate_of_initial_storGroundwater.map = "gwRecharge_annuaAvg_output.map/globalalpha.map"
