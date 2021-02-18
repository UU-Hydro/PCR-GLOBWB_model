#!/bin/bash

#PBS -l walltime=72:00:00
#PBS -l select=1:ncpus=32:mem=62gb

#~ #PBS -q express -P exp-0032

cd /rds/general/user/esutanud/home/
. load_all_default.sh

cd /rds/general/user/esutanud/home/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
python deterministic_runner.py ../config/30sec_african_countries/tanzania/version_20191211/setup_30sec_tanzania-basin_test_version_2019_12_11_rerun.ini debug

