
source activate pcrglobwb_python3

GCM_CODE="gfdl-esm4" 
GCM_CODE_SHORT="gfdl"
python merging_daily_variables_only_et0.py /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/ 1979 2014 /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/global/netcdf_daily_1979-2014/ &

GCM_CODE="ipsl-cm6a-lr"
GCM_CODE_SHORT="ipsl"
python merging_daily_variables_only_et0.py /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/ 1979 2014 /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/global/netcdf_daily_1979-2014/ &

GCM_CODE="mpi-esm1-2-hr"
GCM_CODE_SHORT="mpi"
python merging_daily_variables_only_et0.py /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/ 1979 2014 /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/global/netcdf_daily_1979-2014/ &

GCM_CODE="mri-esm2-0"
GCM_CODE_SHORT="mri"
python merging_daily_variables_only_et0.py /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/ 1979 2014 /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/global/netcdf_daily_1979-2014/ &

GCM_CODE="ukesm1-0-ll"
GCM_CODE_SHORT="ukesm"
python merging_daily_variables_only_et0.py /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/ 1979 2014 /ssp_disks/links_to_ssps_all/${GCM_CODE_SHORT}/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/begin_from_1960/global/netcdf_daily_1979-2014/ &

wait

#~ (base) pcrglobwb-azure@pcrglobwb-azure:/ssp_disks/links_to_ssps_all/gfdl/pcrglobwb/merged_daily/pcrglobwb_aqueduct_2021/version_2021-09-16/gfdl-esm4/historical/begin_from_1960/global/netcdf_daily_1979-2014$ ls -lah /ssp_disks/links_to_ssps_all/*/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/* -d
#~ drwxrwxr-x 3 pcrglobwb-azure pcrglobwb-azure 28 Oct  5 11:01 /ssp_disks/links_to_ssps_all/gfdl/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/ gfdl-esm4
#~ drwxrwxr-x 3 pcrglobwb-azure pcrglobwb-azure 28 Oct 29 23:46 /ssp_disks/links_to_ssps_all/ipsl/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/ ipsl-cm6a-lr
#~ drwxrwxr-x 3 pcrglobwb-azure pcrglobwb-azure 28 Oct  8 04:04 /ssp_disks/links_to_ssps_all/mpi/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/  mpi-esm1-2-hr
#~ drwxrwxr-x 3 pcrglobwb-azure pcrglobwb-azure 28 Oct  8 04:04 /ssp_disks/links_to_ssps_all/mri/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/  mri-esm2-0
#~ drwxrwxr-x 3 pcrglobwb-azure pcrglobwb-azure 28 Oct  8 04:02 /ssp_disks/links_to_ssps_all/ukesm/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/ukesm1-0-ll
