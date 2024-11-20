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

module load foss2023a
module load PCRaster/4.4.1-foss-2023a-Python-3.11.3
module load netcdf4-python
module load LUE/development-foss-2023a

# Run this script with LUE package in environment. This should work:
# python -c "import lue"

hostname=`hostname -s 2>/dev/null`

if [ ! "$hostname" ];
then
     echo "Could not figure out the hostname"
     exit 1
fi

hostname="${hostname,,}"  # Lower-case the hostname


scratch_prefix="/scratch/sutan101/"
input_prefix="/data"
libtcmalloc=$(find $EBROOTGPERFTOOLS -name libtcmalloc_minimal.so.4)


# Common
input_dir="$input_prefix/hydroworld/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input"
output_dir="$scratch_prefix/pcr_globwb/lue/30min_global"

ini_in="../config/lue/setup_30min_on_velocity_for_lue_with_lue.ini"
ini_out="$HOME/tmp/setup_30min_on_velocity_for_lue.ini"

rm -fr $output_dir

cat $ini_in \
     | sed -e "s|^outputDir .*|outputDir = $output_dir|" \
     | sed -e "s|^inputDir .*|inputDir = $input_dir|" \
     | sed -e "s|^cloneMap .*|cloneMap =
$input_dir/global_30min/cloneMaps/clone_global_30min.map|" \
     | sed -e "s|^correct_water_body_outlets
.*|correct_water_body_outlets =
$input_dir/global_30min/water_body/water_body_outlets_boolean.map|" \
     | sed -e "s|^correct_water_body_ids .*|correct_water_body_ids =
$input_dir/global_30min/water_body/water_body_ids_nominal.map|" \
     > $ini_out

LD_PRELOAD=$libtcmalloc \
LUE_PCRASTER_PROVIDER_NAME=lue \
LUE_PARTITION_SHAPE="360,720" \
     python ../model/deterministic_runner.py $ini_out \
         --hpx:threads=1





