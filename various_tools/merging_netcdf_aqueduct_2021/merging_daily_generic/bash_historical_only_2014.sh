
source activate pcrglobwb_python3

GCM_CODE="gfdl-esm4" 
GCM_CODE_SHORT="gfdl"
python merging_daily_variables_only_2014.py /gcm_disks_hist_and_ssp585/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/ 1960 2014 /gcm_disks_hist_and_ssp585/edwin_2014/${GCM_CODE}/ &

GCM_CODE="ipsl-cm6a-lr"
GCM_CODE_SHORT="ipsl"
python merging_daily_variables_only_2014.py /gcm_disks_hist_and_ssp585/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/ 1960 2014 /gcm_disks_hist_and_ssp585/edwin_2014/${GCM_CODE}/ &

GCM_CODE="mpi-esm1-2-hr"
GCM_CODE_SHORT="mpi"
python merging_daily_variables_only_2014.py /gcm_disks_hist_and_ssp585/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/ 1960 2014 /gcm_disks_hist_and_ssp585/edwin_2014/${GCM_CODE}/ &

GCM_CODE="mri-esm2-0"
GCM_CODE_SHORT="mri"
python merging_daily_variables_only_2014.py /gcm_disks_hist_and_ssp585/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/ 1960 2014 /gcm_disks_hist_and_ssp585/edwin_2014/${GCM_CODE}/ &

GCM_CODE="ukesm1-0-ll"
GCM_CODE_SHORT="ukesm"
python merging_daily_variables_only_2014.py /gcm_disks_hist_and_ssp585/${GCM_CODE_SHORT}/pcrglobwb/pcrglobwb_output/pcrglobwb_aqueduct_2021/version_2021-09-16/${GCM_CODE}/historical/ 1960 2014 /gcm_disks_hist_and_ssp585/edwin_2014/${GCM_CODE}/ &

wait

