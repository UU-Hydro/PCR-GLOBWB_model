#!/bin/bash

set -x

MAIN_OUTPUT_DIR="/lustre1/0/einf1079/edwin/pcrglobwb_output_europe/europe_30sec/version_2021-04-20/"

python merge_netcdf_europe.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/global/netcdf outMonthTotNC 1981-01-01 1984-12-31 runoff,totalRunoff,precipitation,gwRecharge,surfaceWaterInf,referencePotET,totalEvaporation,totalPotentialEvaporation NETCDF4 False 12 Global &

python merge_netcdf_europe.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/global/netcdf outMonthAvgNC 1981-01-01 1984-12-31 discharge,temperature,snowCoverSWE,storUppTotal,storLowTotal,totalWaterStorageThickness,satDegUpp,satDegLow NETCDF4 False 12 Global &

wait

set +x
