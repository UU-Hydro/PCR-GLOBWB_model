#!/bin/bash 

#~ set -x 

# - using modules on cca
module load python3/3.6.10-01
module load pcraster/4.3.0
module load gdal/3.0.4

# go to the folder that contain PCR-GLOBWB scripts
cd /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
pwd

INI_FILE="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/ulysses/version_2020-08-14/continue_from_1996/setup_6arcmin_test_version_2020-08-14_continue_from_1996.ini"
#~ MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_output_version_2020-08-14_test_with_aprun/continue_from_1996/"

MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/test_aprun/"

# run the model for every clone
set -x
CLONE_CODE=`printf %d $ALPS_APP_PE`
python3 deterministic_runner_parallel_for_ulysses.py ${INI_FILE} debug_parallel ${CLONE_CODE} -mod ${MAIN_OUTPUT_DIR}
set +x

#~ set +x
