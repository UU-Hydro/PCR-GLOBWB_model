# copying the script and tbl
cp ../pcrglobwb_v1/pcrglobwb_v1.2_fullforcing_edwinVersion.txt /scratch/edwin/test_RhineMeuse30min_EFAS_test/maps
cp ../pcrglobwb_v1/param_permafrost_edwinVersion.tbl /scratch/edwin/test_RhineMeuse30min_EFAS_test/maps

# go to the maps directory and make the results directory
cd /scratch/edwin/test_RhineMeuse30min_EFAS_test/maps
mkdir results

# execute the script
oldcalc -f pcrglobwb_v1.2_fullforcing_edwinVersion.txt 366



