
set -eu

export MODULEPATH=/depfg/easybuild/foss2024a/modules/all/
module load PCRaster/development-foss-2024a
module load netcdf4-python
module load LUE/development-foss-2024a

# Run this script with LUE package in environment. This should work:
# python -c "import lue"

libtcmalloc=$(find $EBROOTGPERFTOOLS -name libtcmalloc_minimal.so.4)

pcrglobwb_runner="/eejit/home/sutan101/github/edwinkost/PCR-GLOBWB_model/model/deterministic_runner_lue.py"
pcrglobwb_ini="/eejit/home/sutan101/github/edwinkost/PCR-GLOBWB_model/config/lue/setup_30min_for_lue_experiment_v2025-05-15.ini"
pcrglobwb_debug_mode="nodebug"

output_dir="/scratch/depfg/sutan101/test_lue_experiment/"
clone_map="/scratch/depfg/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min.map"
ldd_map="/scratch/depfg/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min.map"

#~ # prepare the clone map
#~ rm /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map
#~ mapattr -s -P yb2t -R 360 -C 720 -B -x -180 -y 90 -l 0.5 /scratch/depfg/sutan101/clone_map_for_lue/clone_map_for_lue_test.map

#~ # prepare the ldd map
#~ cp /scratch/depfg/hydrowld/data/hydroworld/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min.map /scratch/depfg/sutan101/clone_map_for_lue/ldd_for_lue_test.map

# get the number of rows and column of the input dataset (required to determine the "centre")
gdalinfo ${ldd_map}

LD_PRELOAD=$libtcmalloc \
LUE_PCRASTER_PROVIDER_NAME=lue \
LUE_PARTITION_SHAPE="36,72" \
     python ${pcrglobwb_runner} ${pcrglobwb_ini} ${pcrglobwb_debug_mode} \
         --output_dir ${output_dir} \
         --clone_map ${clone_map} \
         --ldd_map ${ldd_map} \
         --hpx:threads=1 \
         --lue:count=1 \
         --lue:nr_workers=1 \
         --lue:array_shape="36,72" \
         --lue:partition_shape="36,72" \
         --lue:centre="180,360" \
         --lue:result="/scratch/depfg/sutan101/test_lue_experiment/test.txt" \
         --end
