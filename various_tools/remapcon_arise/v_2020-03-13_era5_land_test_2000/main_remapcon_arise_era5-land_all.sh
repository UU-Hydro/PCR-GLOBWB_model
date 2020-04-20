#!/bin/bash

set -x

INP_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/source_test-edwin-only-2000_downloaded_2020-03-12/daily/"

#~ edwinhs@fcn13.bullx:/scratch-shared/edwinhs/meteo_arise/tanzania/source_test-edwin-only-2000_downloaded_2020-03-12/daily$ ls -lah *
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:05 tanzania_era5-land_daily_d2m-average_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:05 tanzania_era5-land_daily_d2m-maximum_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:05 tanzania_era5-land_daily_d2m-minimum_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:03 tanzania_era5-land_daily_fal-average_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:02 tanzania_era5-land_daily_spressu-avg_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:05 tanzania_era5-land_daily_t2m-average_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:05 tanzania_era5-land_daily_t2m-maximum_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:05 tanzania_era5-land_daily_t2m-minimum_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:03 tanzania_era5-land_daily_total-preci_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:04 tanzania_era5-land_daily_total-ssrad_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:04 tanzania_era5-land_daily_u10-average_2000-2000.nc
#~ -r--r--r-- 1 edwinhs edwinhs 234M Mar 12 02:04 tanzania_era5-land_daily_v10-average_2000-2000.nc

OUT_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-03-12_test-edwin-only-2000/era5-land/"

bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_d2m-average_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_d2m-average_2000-2000 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_d2m-maximum_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_d2m-maximum_2000-2000 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_d2m-minimum_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_d2m-minimum_2000-2000 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_fal-average_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_fal-average_2000-2000 monmean "1" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_spressu-avg_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_spressu-avg_2000-2000 monmean "Pa" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_t2m-average_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_t2m-average_2000-2000 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_t2m-maximum_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_t2m-maximum_2000-2000 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_t2m-minimum_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_t2m-minimum_2000-2000 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_total-preci_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_total-preci_2000-2000 monsum  "m.month-1" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_total-ssrad_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_ssr-average_2000-2000 monmean "J.m-2.day-1" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_u10-average_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_u10-average_2000-2000 monmean "m.s-1" &
bash remapcon_arise_era5.sh ${INP_FOLDER} tanzania_era5-land_daily_v10-average_2000-2000.nc ${OUT_FOLDER} tanzania_era5-land_v10-average_2000-2000 monmean "m.s-1" &

wait

set +x
