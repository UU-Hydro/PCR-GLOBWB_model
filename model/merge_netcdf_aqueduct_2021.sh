#!/bin/bash

set -x

python merge_netcdf_general.py /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-05-03_updated_gmd_parameters /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-05-03_updated_gmd_parameters/global/netcdf/ outMonthTotNC 1979-01-31 2016-12-31 actualET,runoff,totalRunoff,baseflow,directRunoff,interflowTotal,totalGroundwaterAbstraction,desalinationAbstraction,surfaceWaterAbstraction,nonFossilGroundwaterAbstraction,fossilGroundwaterAbstraction,precipitation,gwRecharge,surfaceWaterInf,totalEvaporation,totalPotentialEvaporation,referencePotET NETCDF4 True 48 53 all_lats &

python merge_netcdf_general.py /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-05-03_updated_gmd_parameters /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021/version_2021-05-03_updated_gmd_parameters/global/netcdf/ outMonthAvgNC 1979-01-31 2016-12-31 discharge,temperature,dynamicFracWat,surfaceWaterStorage,interceptStor,snowFreeWater,snowCoverSWE,topWaterLayer,storUppTotal,storLowTotal,storGroundwater,storGroundwaterFossil,totalActiveStorageThickness,totalWaterStorageThickness,satDegUpp,satDegLow,channelStorage,waterBodyStorage NETCDF4 True 48 53 all_lats &

wait

set +x



