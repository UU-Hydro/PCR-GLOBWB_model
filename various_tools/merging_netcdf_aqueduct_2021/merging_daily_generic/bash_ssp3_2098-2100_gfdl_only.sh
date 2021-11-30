
source activate pcrglobwb_python3

/gcm_disks/gfdl/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/gfdl-esm4/ssp370/begin_from_2015/global/netcdf_daily

GCM_CODE="gfdl-esm4" 
GCM_CODE_SHORT="gfdl"
python merging_daily_variables_only_2098-2100.py /gcm_disks/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/ssp370/ 2015 2100 /gcm_disks/${GCM_CODE_SHORT}/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/ssp370/begin_from_2015/global/netcdf_daily/ &

wait

