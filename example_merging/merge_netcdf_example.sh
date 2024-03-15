#!/bin/bash

#SBATCH -N 1
#SBATCH -n 16

#~ #SBATCH -t 240:00:00

#SBATCH -p defq

#SBATCH -J merge_nc_1979-2019_naturalized

#~ #SBATCH --exclusive


# load my enviroment 
. /eejit/home/sutan101/load_anaconda_and_my_default_env.sh

# go to the folder where the python script is located
cd /eejit/home/sutan101/github/UU-Hydro/PCR-GLOBWB_model/model/

# merging monthly total files
python merge_netcdf_general.py /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_naturalized/version_2021-09-16_naturalized/gswp3-w5e5/historical-reference/continue_from_1965/ /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_naturalized/version_2021-09-16_naturalized/gswp3-w5e5/historical-reference/continue_from_1965/global/netcdf_1979-2019/ outMonthTotNC 1979-01-31 2019-12-31 referencePotET,gwRecharge,directRunoff,interflowTotal,baseflow NETCDF4 True 8 53 all_lats &

# merging monthly average files
python merge_netcdf_general.py /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_naturalized/version_2021-09-16_naturalized/gswp3-w5e5/historical-reference/continue_from_1965/ /scratch/depfg/sutan101/pcrglobwb_aqueduct_2021_naturalized/version_2021-09-16_naturalized/gswp3-w5e5/historical-reference/continue_from_1965/global/netcdf_1979-2019/ outMonthAvgNC 1979-01-31 2019-12-31 channelStorage,discharge,storGroundwater NETCDF4 True 8 53 all_lats &

wait




