#!/bin/bash 

set -x 

INI_FILE="/home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/config/ulysses/version_2020-08-14/continue_from_1996/setup_6arcmin_test_version_2020-08-14_continue_from_1996.ini"
MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/test_aprun_3/"

TEST=inputfile_`printf %03d $ALPS_APP_PE`

mkdir -p ${MAIN_OUTPUT_DIR}/${TEST}


set +x
