#!/bin/bash

set -x

#~ INP_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/source_icl_downloaded_2020-04-07/era5-land/"
#~ INP_FOLDER="/rds/general/user/ec407/ephemeral/Senegal/ForEdwin/"
INP_FOLDER=/rds/general/project/arise/ephemeral/tmp_edwin/

#~ (pcrglobwb_python3) esutanud@login-7:/rds/general/project/arise/ephemeral/tmp_edwin$ ls -lah *
#~ -rw-r-x--- 1 ec407 rds-000549 2.4G Sep 18 12:59 TNZ-ERA5_daily_d2m_Max_1981-2020.nc
#~ -rw-r-x--- 1 ec407 rds-000549 2.4G Sep 18 13:00 TNZ-ERA5_daily_d2m_mean_1981-2020.nc
#~ -rw-r-x--- 1 ec407 rds-000549 2.4G Sep 18 13:00 TNZ-ERA5_daily_d2m_min_1981-2020.nc
#~ -rw-r-x--- 1 ec407 rds-000549 2.4G Sep 18 12:58 TNZ-ERA5_daily_t2m_Max_1981-2020.nc
#~ -rw-r-x--- 1 ec407 rds-000549 2.4G Sep 18 12:58 TNZ-ERA5_daily_t2m_mean_1981-2020.nc
#~ -rw-r-x--- 1 ec407 rds-000549 2.4G Sep 18 12:59 TNZ-ERA5_daily_t2m_min_1981-2020.nc

#~ OUT_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-04-07/era5-land/"
OUT_FOLDER="/rds/general/user/esutanud/ephemeral/meteo_arise/senegal/version_2020-09-XX/era5-land/"

bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_daily_d2m_Max_1981-2020.nc  ${OUT_FOLDER} senegal_era5-land_d2m-maximum_1981-2020 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_daily_d2m_mean_1981-2020.nc ${OUT_FOLDER} senegal_era5-land_d2m-average_1981-2020 monmean "K" &
bash remapcon_arise_era5.sh ${INP_FOLDER} TNZ-ERA5_daily_d2m_min_1981-2020.nc  ${OUT_FOLDER} senegal_era5-land_d2m-minimum_1981-2020 monmean "K" &

wait

set +x
