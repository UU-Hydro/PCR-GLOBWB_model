#!/bin/bash

printf "$0"
for arg in "$@"
do 
    printf " $arg"
done
echo

echo "Arg 0: $0"
echo "Arg 1: $1"
echo "Arg 2: $2"
echo "Arg 3: $3"
echo "Arg 4: $4"
echo "Arg 5: $5"
echo "Arg 6: $6"

set -x 

INPUT_FILE="/scratch-shared/edwinhs/meteo_arise/tanzania/source_icl_downloaded_2020-03-02/chirps_rainfall/TNZ_chirps-v2.0.1981-2019.days_p05.nc"
INPUT_FILE=$1

RESOLUTION=0.041666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666667
RESOLUTION=$2

OUTPUT_DIR="/scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-03-06/chirps/150_arcsec/"
OUTPUT_DIR=$3

OUTPUTFILE="tanzania_chirps-v2.0_1981-2019_p05_rempacon-150-arcsec"
OUTPUTFILE=$4
OUTPUT_DAILY_FILE=${OUTPUTFILE}_daily.nc
OUTPUT_MONTH_FILE=${OUTPUTFILE}_monthly.nc

CDOMON_OPERA="monsum"
CDOMON_OPERA=$5
MONTHLY_UNIT="mm.month-1"
MONTHLY_UNIT=$6

CLONE30SEC="/scratch-shared/edwinswt/data/pcrglobwb2_input_arise/tanzania_version_2019_12_11/pcrglobwb2_input/tanzania_30sec/cloneMaps/ghana_tanzania_uganda_zimbabwe/clone_tanzania_194_basin.map"

mkdir -p ${OUTPUT_DIR}
cd ${OUTPUT_DIR}
rm *.nc
rm *.txt
rm *.tif

# creating griddes file
gdalwarp -tr ${RESOLUTION} ${RESOLUTION} ${CLONE30SEC} clone.tif
gdal_translate -of NETCDF clone.tif clone.nc
cdo -L -griddes -invertlat clone.nc > griddes_invertlat_clone.txt

# remapcon
cdo -L -setrtoc,-inf,0,0 -settime,00:00:00 -remapcon,griddes_invertlat_clone.txt -setrtoc,-inf,0,0 ${INPUT_FILE} ${OUTPUT_DAILY_FILE}

# calculate monthly values
CDO_TIMESTAT_DATE='last' cdo -L -settime,00:00:00 -setunit,${MONTHLY_UNIT} -${CDOMON_OPERA} ${OUTPUT_DAILY_FILE} ${OUTPUT_MONTH_FILE}

set +x
