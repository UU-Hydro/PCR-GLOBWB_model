#!/bin/bash

set -x

MAIN_OUTPUT_DIR="/lustre1/0/einf1079/edwin/pcrglobwb_output_europe/europe_30sec/version_2021-04-20/"

python merge_netcdf_europe.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/europe_30sec/netcdf outMonthTotNC 1981-01-31 1984-12-31 runoff,totalRunoff,precipitation,gwRecharge,surfaceWaterInf,referencePotET,totalEvaporation,totalPotentialEvaporation,baseflow NETCDF4 False 12 europe_30sec europe_30sec &

python merge_netcdf_europe.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/europe_30sec/netcdf outMonthAvgNC 1981-01-31 1984-12-31 discharge,temperature,snowCoverSWE,storUppTotal,storLowTotal,totalWaterStorageThickness,satDegUpp,satDegLow NETCDF4 False 12 europe_30sec europe_30sec &

python merge_netcdf_europe.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/europe_30sec/netcdf outAnnuaTotNC 1981-12-31 1984-12-31 runoff,totalRunoff,precipitation,gwRecharge,surfaceWaterInf,referencePotET,totalEvaporation,totalPotentialEvaporation,baseflow NETCDF4 False 12 europe_30sec europe_30sec &

wait

#~ # for testing
#~ python merge_netcdf_europe.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/europe_30sec/netcdf outMonthAvgNC 1981-01-31 1981-03-31 discharge NETCDF4 False 12 europe_30sec europe_30sec 

set +x
