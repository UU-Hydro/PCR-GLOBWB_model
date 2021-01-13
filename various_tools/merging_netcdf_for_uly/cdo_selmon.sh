set -x

YEAR=$1

INP_FOLDER="/scratch/ms/copext/cynw/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv_merged_1981-2019/runoff/"
INP_FOLDER="/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/merged_runoff_1981-2019/b1p50/"
INP_FOLDER=$2

OUT_FOLDER="/scratch/ms/copext/cynw/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv_merged_1981-2019/daily_runoff_in_monthly_files/"
OUT_FOLDER="/scratch/depfg/sutan101/pcrglobwb_ulysses_reference_runs_version_2021-01-XX_b/merged_runoff_1981-2019/b1p50/daily_runoff_in_monthly_files/"
OUT_FOLDER=$3

mkdir -p ${OUT_FOLDER}
cd ${OUT_FOLDER}

mkdir ${YEAR}

cdo -L -f nc4 -selmon,1  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01.nc &
cdo -L -f nc4 -selmon,2  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-02.nc &
cdo -L -f nc4 -selmon,3  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-03.nc &
cdo -L -f nc4 -selmon,4  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-04.nc &
cdo -L -f nc4 -selmon,5  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-05.nc &
cdo -L -f nc4 -selmon,6  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-06.nc &
cdo -L -f nc4 -selmon,7  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-07.nc &
cdo -L -f nc4 -selmon,8  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-08.nc &
cdo -L -f nc4 -selmon,9  ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-09.nc &
cdo -L -f nc4 -selmon,10 ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-10.nc &
cdo -L -f nc4 -selmon,11 ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-11.nc &
cdo -L -f nc4 -selmon,12 ${INP_FOLDER}/${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-01-01_to_${YEAR}-12-31.nc ${YEAR}/ulyssesQrRunoff_dailyTot_output_${YEAR}-12.nc &

wait

set +x
