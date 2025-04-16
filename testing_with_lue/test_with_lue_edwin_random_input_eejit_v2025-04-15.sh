#~ Hi Edwin,

#~ Here are the two scripts I use to run the model with either PCRaster or
#~ LUE. You can use them as inspiration for your own runs.

#~ Setting LD_PRELOAD is required, otherwise a LUE model will likely crash
#~ upon exit. I asked Oliver to see whether loading the LUE EasyBuild
#~ module could set the variable as a side-effect. Once that is done, we
#~ don't have to set it anymore. You can test this by "echo $LD_PRELOAD".

#~ Here's what I would do if I where you:
#~ 1. Look at the changes which I made so you know what the differences are
#~ 2. Run the model with PCRaster. Store the results in a directory.
#~ 3. Run the model with LUE. Store the results in another directory.
#~ 4. Look at the differences between the LUE and PCRaster outputs. Figure
#~ out why some rasters are different. I will fix any issue with LUE of course.

#~ I will send you a script which I used to compare results between
#~ PCRaster and LUE outputs.

#~ Let me know if things don't work and I will fix 'm.

#~ Kor



set -eu

export MODULEPATH=/depfg/easybuild/foss2024a/modules/all/
module load PCRaster/development-foss-2024a
module load netcdf4-python
module load LUE/development-foss-2024a

# Run this script with LUE package in environment. This should work:
# python -c "import lue"

libtcmalloc=$(find $EBROOTGPERFTOOLS -name libtcmalloc_minimal.so.4)

pcrglobwbrunner="/eejit/home/sutan101/github/edwinkost/PCR-GLOBWB_model/model/deterministic_runner_lue.py"
pcrglobwbini="/eejit/home/sutan101/github/edwinkost/PCR-GLOBWB_model/config/lue/setup_for_lue_experiment_v2025-04-15.ini"
pcrglobwbdebugmode="debug"

#~ # prepare the clone map
#~ rm /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map
#~ mapattr -s -P yb2t -R 10000 -C 20000 -B -x -18 -y 38 -l 0.000833333 /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map

# prepare the clone map
rm /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map
mapattr -s -P yb2t -R 360 -C 720 -B -x -180 -y 90 -l 0.5 /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map

# prepare the ldd map - now everything just a pit/sink
cd /scratch/depfg/sutan101/clone_map_for_lue/
pcrcalc --clone clone_map_for_lue_test.map ldd_for_lue_test.map = "ldd(5.0)"
cd -

LD_PRELOAD=$libtcmalloc \
LUE_PCRASTER_PROVIDER_NAME=lue \
LUE_PARTITION_SHAPE="360,720" \
     python ${pcrglobwbrunner} ${pcrglobwbini} ${pcrglobwbdebugmode} \
         --hpx:threads=1 \
         --lue:count=1 \
         --lue:nr_workers=1 \
         --lue:array_shape="360,720" \
         --lue:partition_shape="360,720" \
         --lue:result="/scratch/depfg/sutan101/test_lue_experiment/test.txt" \
         --end
