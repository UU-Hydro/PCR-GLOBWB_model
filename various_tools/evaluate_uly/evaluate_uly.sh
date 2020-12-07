
SOURCE_FOLDER="/scratch/ms/copext/cyes/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv/"

cdo gridarea ${SOURCE_FOLDER}/begin_from_1981/global/netcdf/precipitation_annuaTot_output_1981-12-31_to_1981-12-31.nc gridarea.nc

cdo -L -mergetime ${SOURCE_FOLDER}/*/global/netcdf/precipitation_annuaTot_*.nc merged_precipitation.nc ; cdo -L -fldsum -mul merged_precipitation.nc gridarea.nc global_precipitation.nc ; ncdump global_precipitation.nc

cdo -L -mergetime ${SOURCE_FOLDER}/*/global/netcdf/totalRunoff_annuaTot_*.nc merged_totalRunoff.nc ; cdo -L -fldsum -mul merged_totalRunoff.nc gridarea.nc global_totalRunoff.nc ; ncdump global_totalRunoff.nc

cdo -L -mergetime ${SOURCE_FOLDER}/*/global/netcdf/totalEvaporation_annuaTot_*.nc merged_totalEvaporation.nc ; cdo -L -fldsum -mul merged_totalEvaporation.nc gridarea.nc global_totalEvaporation.nc ; ncdump global_totalEvaporation.nc


edwinhs@int1.bullx:/scratch-shared/edwinhs/discharge_evaluation_ulysses_2020-12-01$ ls -lah old-jgw_uly-et0_uly-lcv/merged_1981-1998/edwin_monthly_discharge_evaluation_with_job/*/chart/*BRATIS*.pdf
-r--r--r-- 1 edwinhs edwinhs 7.1K Dec  4 00:56 old-jgw_uly-et0_uly-lcv/merged_1981-1998/edwin_monthly_discharge_evaluation_with_job/15/chart/SK_DANUBERIVER_6142200_BRATISLAVA_chart.pdf


CHART_FILE=$1

CHART_FILE="SK_DANUBERIVER_6142200_BRATISLAVA_chart.pdf"

display old-jgw_uly-et0_uly-lcv/merged_1981-1998/edwin_monthly_discharge_evaluation_with_job/*/chart/${CHART_FILE} & display new-jgw_uly-et0_uly-lcv/merged_1981-1998/edwin_monthly_discharge_evaluation_with_job/*/chart/${CHART_FILE} & display gmd_paper/merged_1981-1998/edwin_monthly_discharge_evaluation_with_job/*/chart/${CHART_FILE} & wait
