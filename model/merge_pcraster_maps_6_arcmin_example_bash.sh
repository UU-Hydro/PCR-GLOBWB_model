#!/bin/bash

set -x

MAIN_OUTPUT_DIR="/scratch/ms/copext/cyes/pcrglobwb_output_version_2020-08-14/"

python merge_pcraster_maps_6_arcmin_ulysses.py 1995-12-31 ${MAIN_OUTPUT_DIR} states 8 Global 54 False

set +x
