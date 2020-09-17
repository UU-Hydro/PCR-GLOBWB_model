#!/bin/bash

set -x

# chirps precipitation

#~ INP_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/source_icl_downloaded_2020-03-02/"
INP_FOLDER="/rds/general/user/ec407/ephemeral/Senegal/ForEdwin/CHIRPS/"

#~ (pcrglobwb_python3) esutanud@login-7:/rds/general/user/ec407/ephemeral/Senegal/ForEdwin/CHIRPS$ ls -lah *
#~ -rw-r-s--- 1 ec407 hpc-ec407 2.5G Sep  3 15:00 SNL_chirps-v2.0.1981-2020.days_p05.nc


#~ MAIN_OUT_FOLDER="/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-03-09/chirps_precipitation/"
MAIN_OUT_FOLDER="/rds/general/user/esutanud/ephemeral/meteo_arise/senegal/version_2020-09-XX/chirps_precipitation/"


mkdir -p ${MAIN_OUT_FOLDER}



# - 30 arcmin resolution
RESOLUTION=0.5
OUT_FOLDER=${MAIN_OUT_FOLDER}/half_arcdeg/
bash remapcon_arise.sh ${INP_FOLDER}/SNL_chirps-v2.0.1981-2020.days_p05.nc ${RESOLUTION} ${OUT_FOLDER} senegal_chirps-v2.0_1981-2020_p05_rempacon-30-arcmin monsum mm.month-1

# - 5 arcmin resolution
RESOLUTION=0.083333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333
OUT_FOLDER=${MAIN_OUT_FOLDER}/5_arcmin/
bash remapcon_arise.sh ${INP_FOLDER}/SNL_chirps-v2.0.1981-2020.days_p05.nc ${RESOLUTION} ${OUT_FOLDER} senegal_chirps-v2.0_1981-2020_p05_rempacon-5-arcmin monsum mm.month-1

# - 150 arcsec resolution
RESOLUTION=0.041666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666667
OUT_FOLDER=${MAIN_OUT_FOLDER}/150_arcsec/
bash remapcon_arise.sh ${INP_FOLDER}/SNL_chirps-v2.0.1981-2020.days_p05.nc ${RESOLUTION} ${OUT_FOLDER} senegal_chirps-v2.0_1981-2020_p05_rempacon-150-arcsec monsum mm.month-1

set +x
