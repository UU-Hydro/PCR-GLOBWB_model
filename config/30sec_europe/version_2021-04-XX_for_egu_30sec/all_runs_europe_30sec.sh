#!/bin/bash

set -x

sbatch -J eu113235 --export PCRTHREADS="12",CLONE1="11",CLONE2="32",CLONE3="35" job_script_sbatch_pcrglobwb_europe_30sec_template.sh


set +x
