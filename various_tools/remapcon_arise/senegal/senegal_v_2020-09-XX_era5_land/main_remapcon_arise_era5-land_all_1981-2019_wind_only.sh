#!/bin/bash

set -x

#~ INP_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/source_icl_downloaded_2020-04-07/era5-land/"
INP_FOLDER="/rds/general/user/ec407/ephemeral/Senegal/ForEdwin/"

#~ esutanud@login-7:/rds/general/user/ec407/ephemeral/Senegal/ForEdwin$ ls -lah
#~ total 24K
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 8.0K Sep  8 23:21 ..
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Sep  3 15:21 CHIRPS
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:05 Variable_Falb
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:05 Variable_Snsr
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:05 Variable_Spre
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Sep  9 00:43 Variable_Temp
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:08 Variable_Tpre
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:28 Variable_Wind


#~ OUT_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-04-07/era5-land/"
OUT_FOLDER="/rds/general/user/esutanud/ephemeral/meteo_arise/senegal/version_2020-09-XX/era5-land/"


#~ Variable_Temp:
#~ total 15G
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Sep  9 00:43 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 ..
#~ -rw------- 1 ec407 hpc-ec407 2.4G Sep  9 00:42 TNZ-ERA5_daily_d2m_Max_1981-2020.nc
#~ -rw------- 1 ec407 hpc-ec407 2.4G Sep  9 00:43 TNZ-ERA5_daily_d2m_mean_1981-2020.nc
#~ -rw------- 1 ec407 hpc-ec407 2.4G Sep  9 00:43 TNZ-ERA5_daily_d2m_min_1981-2020.nc

#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Temp/TNZ-ERA5_daily_d2m_Max_1981-2020.nc  ${OUT_FOLDER} senegal_era5-land_d2m-maximum_1981-2020 monmean "K" &
#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Temp/TNZ-ERA5_daily_d2m_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_d2m-average_1981-2020 monmean "K" &
#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Temp/TNZ-ERA5_daily_d2m_min_1981-2020.nc  ${OUT_FOLDER} senegal_era5-land_d2m-minimum_1981-2020 monmean "K" &

#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 23:02 TNZ-ERA5_daily_t2m_Max_1981-2020.nc
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 22:59 TNZ-ERA5_daily_t2m_mean_1981-2020.nc
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 22:54 TNZ-ERA5_daily_t2m_min_1981-2020.nc

#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Temp/TNZ-ERA5_daily_t2m_Max_1981-2020.nc  ${OUT_FOLDER} senegal_era5-land_t2m-maximum_1981-2020 monmean "K" &
#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Temp/TNZ-ERA5_daily_t2m_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_t2m-average_1981-2020 monmean "K" &
#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Temp/TNZ-ERA5_daily_t2m_min_1981-2020.nc  ${OUT_FOLDER} senegal_era5-land_t2m-minimum_1981-2020 monmean "K" &

#~ Variable_Falb:
#~ total 2.4G
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:05 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 ..
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 22:42 TNZ-ERA5_daily_Fa_mean_1981-2020.nc

#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Falb/TNZ-ERA5_daily_Fa_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_fal-average_1981-2020 monmean "1" &

#~ Variable_Spre:
#~ total 2.4G
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:05 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 ..
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 22:51 TNZ-ERA5_daily_Sp_mean_1981-2020.nc

#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Spre/TNZ-ERA5_daily_Sp_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_spressu-avg_1981-2020 monmean "Pa" &

#~ Variable_Tpre:
#~ total 2.4G
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:08 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 ..
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 23:08 TNZ-ERA5_daily_Tp_daysum_1981-2020.nc

#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Tpre/TNZ-ERA5_daily_Tp_daysum_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_total-preci_1981-2020 monsum  "m.month-1" &

#~ Variable_Snsr:
#~ total 2.4G
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:05 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 ..
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 22:45 TNZ-ERA5_daily_Ssr_mean_1981-2020.nc

#~ bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Snsr/TNZ-ERA5_daily_Ssr_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_ssr-average_1981-2020 monmean "J.m-2.day-1" &

#~ Variable_Wind:
#~ total 9.4G
#~ drwxr-sr-x 2 ec407 hpc-ec407 4.0K Aug 30 23:28 .
#~ drwxr-sr-x 9 ec407 hpc-ec407 4.0K Sep  3 15:21 ..
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 23:25 TNZ-ERA5_daily_u10_mean_1981-2020.nc
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 23:11 TNZ-ERA5_daily_v10_mean_1981-2020.nc
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 23:16 TNZ-ERA5_daily_WSPEED10m_1981-2020.nc
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.4G Aug 30 23:20 TNZ-ERA5_daily_WSPEED2m_1981-2020.nc

bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Wind/TNZ-ERA5_daily_u10_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_u10-average_1981-2020 monmean "m.s-1" &
bash remapcon_arise_era5.sh ${INP_FOLDER} Variable_Wind/TNZ-ERA5_daily_u10_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_v10-average_1981-2020 monmean "m.s-1" &

wait

set +x
