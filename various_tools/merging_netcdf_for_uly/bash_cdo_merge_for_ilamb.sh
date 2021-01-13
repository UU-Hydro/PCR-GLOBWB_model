
set -x

#~ sutan101@gpu040.cluster:/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/merged_monthly_files_for_ilamb/b1p50$ ls 1981/*
#~ 1981/interceptStor_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/snowCoverSWE_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/snowFreeWater_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/storGroundwater_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/surfaceWaterStorage_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/totalWaterStorageThickness_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesET_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesP_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesQrRunoff_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesQsm_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesSMUpp_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesSM_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesSWE_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssesSnowFraction_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssessCropPET_monthAvg_output_1981-01-31_to_1981-12-31.nc
#~ 1981/ulyssessRefPET_monthAvg_output_1981-01-31_to_1981-12-31.nc

MAIN_FOLDER="/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/merged_monthly_files_for_ilamb/b1p50/"

set -x

cd ${MAIN_FOLDER}

cdo -L -f nc4 -mergetime  */totalWaterStorageThickness_monthAvg_output* totalWaterStorageThickness_monthAvg_output_1981-2019.nc &
cdo -L -f nc4 -mergetime  */ulyssesET_monthAvg_output*                  ulyssesET_monthAvg_output_1981-2019.nc                  &
cdo -L -f nc4 -mergetime  */ulyssesQrRunoff_monthAvg_output*            ulyssesQrRunoff_monthAvg_output_1981-2019.nc            &
cdo -L -f nc4 -mergetime  */ulyssesSMUpp_monthAvg_output*               ulyssesSMUpp_monthAvg_output_1981-2019.nc               &
cdo -L -f nc4 -mergetime  */ulyssesSMUpp_monthAvg_output*               ulyssesSM_monthAvg_output_1981-2019.nc                  &
cdo -L -f nc4 -mergetime  */ulyssesSWE_monthAvg_output*                 ulyssesSWE_monthAvg_output_1981-2019.nc                 &
cdo -L -f nc4 -mergetime  */ulyssesSnowFraction_monthAvg_output*        ulyssesSnowFraction_monthAvg_output_1981-2019.nc        &

wait

set +x

