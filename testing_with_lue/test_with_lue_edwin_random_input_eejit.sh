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
pcrglobwbini="/eejit/home/sutan101/github/edwinkost/PCR-GLOBWB_model/config/lue/setup_30min_on_velocity_for_lue_random_field_develop_eejit.ini"
pcrglobwbdebugmode="debug"

#~ # prepare the clone map
#~ rm /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map
#~ mapattr -s -P yb2t -R 10000 -C 20000 -B -x -18 -y 38 -l 0.000833333 /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map

#~ # prepare the clone map
#~ rm /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map
#~ mapattr -s -P yb2t -R 360 -C 720 -B -x -180 -y 90 -l 0.5 /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map

# prepare the clone map
rm /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map
cp /scratch/depfg/sutan101/ldd_for_lue/ldd_test_repaired.map /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map

#~ # prepare the ldd map - now everything just a pit/sink
#~ cd /scratch/depfg/sutan101/clone_map_for_lue/
#~ pcrcalc --clone clone_map_for_lue_test.map ldd_for_lue_test.map = "ldd(5.0)"
#~ cd -

# prepare the ldd map - now everything just a pit/sink
rm /scratch/depfg/sutan101/clone_map_for_lue/ldd_for_lue_test.map
cp /scratch/depfg/sutan101/ldd_for_lue/ldd_test_repaired.map /scratch/depfg/sutan101/clone_map_for_lue/ldd_for_lue_test.map

#~ LD_PRELOAD=$libtcmalloc \
#~ LUE_PCRASTER_PROVIDER_NAME=lue \
#~ LUE_PARTITION_SHAPE="360,720" \
     #~ python ${pcrglobwbrunner} ${pcrglobwbini} ${pcrglobwbdebugmode} \
         #~ --hpx:threads=1 \
         #~ --lue:count=1 \
         #~ --lue:nr_workers=1 \
         #~ --lue:array_shape="360,720" \
         #~ --lue:partition_shape="360,720" \
         #~ --lue:result="/scratch/depfg/sutan101/test_lue_experiment/test.txt" \
         #~ --end

LD_PRELOAD=$libtcmalloc \
LUE_PCRASTER_PROVIDER_NAME=lue \
LUE_PARTITION_SHAPE="1200,1200" \
     python ${pcrglobwbrunner} ${pcrglobwbini} ${pcrglobwbdebugmode} \
         --hpx:threads=1 \
         --lue:count=1 \
         --lue:nr_workers=1 \
         --lue:array_shape="1200,1200" \
         --lue:partition_shape="1200,1200" \
         --lue:result="/scratch/depfg/sutan101/test_lue_experiment/test.txt" \
         --end


#~ sutan101@node026.cluster:/scratch/depfg/pcraster/lue_pycatch_input$ ls -lah
#~ total 9.2G
#~ drwxr-xr-x  2 schmi109 depfg    7 Mar 31 15:45 .
#~ drwxr-xr-x 15 schmi109 depfg   19 Mar 31 15:44 ..
#~ -rwxr-xr-x  1 schmi109 depfg 115K Mar 31 15:44 airTemperatureArnaJulAugSep0506.tss
#~ -rw-r--r--  1 schmi109 depfg 8.0G Mar 31 15:45 elv.tiff
#~ -rwxr-xr-x  1 schmi109 depfg 128K Mar 31 15:44 incomingShortwaveRadiationArnasJulAugSep0506.tss
#~ -rw-r--r--  1 schmi109 depfg 1.3G Mar 31 15:44 ldd.tiff
#~ -rw-r--r--  1 schmi109 depfg 215K Mar 31 15:44 rainfallFluxTwoCatchsJulAugSep0506.tss
#~ -rwxr-xr-x  1 schmi109 depfg 118K Mar 31 15:44 relativeHumidityArnasJulAugSep0506.tss
#~ -rwxr-xr-x  1 schmi109 depfg 118K Mar 31 15:44 windVelocityArnasJulAugSep0506.tss
#~ (pcrglobwb_python3_pcraster44_v2025-01-16b)
#~ sutan101@node026.cluster:/scratch/depfg/pcraster/lue_pycatch_input$ gdalinfo ldd.tiff
#~ Driver: GTiff/GeoTIFF
#~ Files: ldd.tiff
#~ Size is 84000, 87600
#~ Origin = (-18.000000000000000,38.000000000000000)
#~ Pixel Size = (0.000833333333333,-0.000833333333333)
#~ Metadata:
  #~ PCRASTER_VALUESCALE=VS_LDD
#~ Image Structure Metadata:
  #~ COMPRESSION=ZSTD
  #~ INTERLEAVE=BAND
#~ Corner Coordinates:
#~ Upper Left  ( -18.0000000,  38.0000000)
#~ Lower Left  ( -18.0000000, -35.0000000)
#~ Upper Right (  52.0000000,  38.0000000)
#~ Lower Right (  52.0000000, -35.0000000)
#~ Center      (  17.0000000,   1.5000000)
#~ Band 1 Block=84000x1 Type=Byte, ColorInterp=Gray
  #~ NoData Value=255
#~ (pcrglobwb_python3_pcraster44_v2025-01-16b)
#~ sutan101@node026.cluster:/scratch/depfg/pcraster/lue_pycatch_input$
