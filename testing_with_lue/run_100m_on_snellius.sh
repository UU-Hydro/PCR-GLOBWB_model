
set -eu

module load 2024
module load PCRaster/4.4.2-foss-2024a
module load netcdf4-python/1.7.1.post2-foss-2024a
module load LUE/development-foss-2024a


# Run this script with LUE package in environment. This should work:
# python -c "import lue"

libtcmalloc=$(find $EBROOTGPERFTOOLS -name libtcmalloc_minimal.so.4)

pcrglobwb_runner="../model/deterministic_runner_lue.py"
pcrglobwb_ini="../config/lue/setup_100m_for_lue_experiment_v2025-05-15.ini"
pcrglobwb_debug_mode="nodebug"

#~ output_dir="/scratch/depfg/sutan101/test_lue_experiment/100m_final_test/"
#~ clone_map="/scratch/depfg/sutan101/clone_map_for_lue/ldd_africa_3sec.map"
#~ ldd_map="/scratch/depfg/sutan101/clone_map_for_lue/ldd_africa_3sec.map"

#~ output_dir="/scratch-shared/edwin/test_lue_experiment/100m_final_test/"
#~ clone_map="/scratch-shared/edwin/ldd_map_for_lue/ldd_africa_3sec.map"
#~ ldd_map="/scratch-shared/edwin/ldd_map_for_lue/ldd_africa_3sec.map"

output_dir="/scratch-shared/edwin/test_lue_experiment/100m_small_test/"
clone_map="/scratch-shared/edwin/ldd_map_for_lue/lue_used_for_a_small_test.map"
ldd_map="/scratch-shared/edwin/ldd_map_for_lue/lue_used_for_a_small_test.map"


#~ sutan101@node011.cluster:/scratch/depfg/sutan101/clone_map_for_lue$ mapattr -p ldd_africa_3sec.map
#~ mapattr version: 4.4.1 (linux/x86_64)
#~ attributes  ldd_africa_3sec.map
#~ rows        87600
#~ columns     84000
#~ cell_length 0.000833333
#~ data_type   ldd
#~ cell_repr   small
#~ projection  yb2t
#~ angle(deg)  0
#~ xUL         -18
#~ yUL         38
#~ min_val     1
#~ max_val     9
#~ version     2
#~ file_id     0
#~ native      y
#~ attr_tab    n
#~ (pcrglobwb_python3_pcraster44_v2025-01-16b)


#~ LD_PRELOAD=$libtcmalloc \
#~ LUE_PCRASTER_PROVIDER_NAME=lue \
#~ LUE_PARTITION_SHAPE="100,200" \
     #~ python ${pcrglobwb_runner} ${pcrglobwb_ini} ${pcrglobwb_debug_mode} \
         #~ --output_dir ${output_dir} \
         #~ --clone_map ${clone_map} \
         #~ --ldd_map ${ldd_map} \
         #~ --hpx:threads=1 \
         #~ --lue:count=1 \
         #~ --lue:nr_workers=1 \
         #~ --lue:array_shape="100,200" \
         #~ --lue:partition_shape="100,200" \
         #~ --lue:centre="43800,42000" \
         #~ --lue:result=${output_dir}/"lue_experiment.txt" \
         #~ --end

LD_PRELOAD=$libtcmalloc \
LUE_PCRASTER_PROVIDER_NAME=lue \
LUE_PARTITION_SHAPE="100,200" \
     python ${pcrglobwb_runner} ${pcrglobwb_ini} ${pcrglobwb_debug_mode} \
         --output_dir ${output_dir} \
         --clone_map ${clone_map} \
         --ldd_map ${ldd_map} \
         --hpx:threads=1 \
         --lue:count=1 \
         --lue:nr_workers=1 \
         --lue:array_shape="100,200" \
         --lue:partition_shape="100,200" \
         --lue:centre="51,101" \
         --lue:result=${output_dir}/"lue_experiment.txt" \
         --end
