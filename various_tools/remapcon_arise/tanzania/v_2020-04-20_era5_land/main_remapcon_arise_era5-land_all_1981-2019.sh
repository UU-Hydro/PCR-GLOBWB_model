#!/bin/bash

set -x

INP_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/source_icl_downloaded_2020-04-07/era5-land/"

#~ edwinhs@fcn8.bullx:/scratch-shared/edwinhs/meteo_arise/tanzania/source_icl_downloaded_2020-04-07/era5-land$ ls -lah *

#~ -r--r--r-- 1 edwinhs edwinhs 125G Apr 18 18:28 TNZ-ERA5-Land-variables.tar
#~ -r--r----- 1 edwinhs edwinhs  72G Apr 18 18:28 TNZ-ERA5-Land-variables.tbz

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_d2m-mean_1981-2019.nc
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_d2m-max_1981-2019.nc
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_d2m-min_1981-2019.nc

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5_Land_daily_fal_mean_1981-2019.nc

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5_Land_daily_sp_1981-2019.nc

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_t2m-mean_1981-2019.nc
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_t2m-max_1981-2019.nc
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_t2m-min_1981-2019.nc

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5_Land_daily_tp_1981-2019.nc

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5_daily_Ssr_mean_1981-2019.nc

#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_u10-mean_1981-2019.nc
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5-Land_daily_v10-mean_1981-2019.nc

# - NOT PROCESSED:
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5_Land_daily_WSPEED10m_1981-2019.nc
#~ -r--r--r-- 1 edwinhs edwinhs 8.9G Apr 18 18:28 TNZ-ERA5_Land_daily_WSPEED2m_1981-2019.nc


OUT_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-04-07/era5-land/"


bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_d2m-mean_1981-2019.nc ${OUT_FOLDER} tanzania_era5-land_d2m-average_1981-2019 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_d2m-max_1981-2019.nc  ${OUT_FOLDER} tanzania_era5-land_d2m-maximum_1981-2019 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_d2m-min_1981-2019.nc  ${OUT_FOLDER} tanzania_era5-land_d2m-minimum_1981-2019 monmean "K" &

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_Land_daily_fal_mean_1981-2019.nc ${OUT_FOLDER} tanzania_era5-land_fal-average_1981-2019 monmean "1" &

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_Land_daily_sp_1981-2019.nc       ${OUT_FOLDER} tanzania_era5-land_spressu-avg_1981-2019 monmean "Pa" &

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_t2m-mean_1981-2019.nc ${OUT_FOLDER} tanzania_era5-land_t2m-average_1981-2019 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_t2m-max_1981-2019.nc  ${OUT_FOLDER} tanzania_era5-land_t2m-maximum_1981-2019 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_t2m-min_1981-2019.nc  ${OUT_FOLDER} tanzania_era5-land_t2m-minimum_1981-2019 monmean "K" &

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_Land_daily_tp_1981-2019.nc       ${OUT_FOLDER} tanzania_era5-land_total-preci_1981-2019 monsum  "m.month-1" &

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_daily_Ssr_mean_1981-2019.nc      ${OUT_FOLDER} tanzania_era5-land_ssr-average_1981-2019 monmean "J.m-2.day-1" &

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_u10-mean_1981-2019.nc ${OUT_FOLDER} tanzania_era5-land_u10-average_1981-2019 monmean "m.s-1" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5-Land_daily_v10-mean_1981-2019.nc ${OUT_FOLDER} tanzania_era5-land_v10-average_1981-2019 monmean "m.s-1" &

wait

set +x
