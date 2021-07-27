#!/bin/bash
#SBATCH -N 1
#SBATCH -n 96
#~ #SBATCH -t 240:00:00
#SBATCH -p defq
#SBATCH -J runs_a_africa

#SBATCH --exclusive

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

set -x

cd $HOME
. load_my_miniconda_and_my_default_env.sh

export PCRASTER_NR_WORKER_THREADS=24

cd /quanta1/home/sutan101/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/

#~ # threads and clones
#~ # 32	3
#~ # 26	5
#~ # 26	7
#~ # 12	1

PCRASTER_NR_WORKER_THREADS=32 python deterministic_runner.py ../config/30sec_african_countries/africa_using_subdomains/version_2020-10-16/setup_30sec_africa_using_subdomains_clone_03.ini debug &
PCRASTER_NR_WORKER_THREADS=26 python deterministic_runner.py ../config/30sec_african_countries/africa_using_subdomains/version_2020-10-16/setup_30sec_africa_using_subdomains_clone_05.ini debug &
PCRASTER_NR_WORKER_THREADS=26 python deterministic_runner.py ../config/30sec_african_countries/africa_using_subdomains/version_2020-10-16/setup_30sec_africa_using_subdomains_clone_07.ini debug &
PCRASTER_NR_WORKER_THREADS=12 python deterministic_runner.py ../config/30sec_african_countries/africa_using_subdomains/version_2020-10-16/setup_30sec_africa_using_subdomains_clone_01.ini debug &

wait

set +x



