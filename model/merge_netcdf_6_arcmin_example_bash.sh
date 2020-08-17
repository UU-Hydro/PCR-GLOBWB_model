#!/bin/bash

set -x

MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_output_version_2020-08-10_example/first_test_54_clones/"

python merge_netcdf_6_arcmin_ulysses.py ${MAIN_OUTPUT_DIR} ${MAIN_OUTPUT_DIR}/global/netcdf outDailyTotNC 1981-01-01 1981-01-31 ulyssesP,ulyssesET,ulyssesSWE,ulyssesQsm,ulyssesSM,ulyssesQrRunoff,ulyssesDischarge NETCDF4 False 1 Global

set +x
