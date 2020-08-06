
# load modules, etc
. load_miniconda_pcrglobwb-py3-env_pcraster430.sh


# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/


# run the model for every clone
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  1 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  2 &
python deterministic_runner_parallel_for_ulysses.py ../config/ulysses/setup_6arcmin_mask_xxxx.ini debug_parallel  3 &

wait

