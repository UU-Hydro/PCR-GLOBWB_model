#!/bin/bash
#SBATCH -N 1
#SBATCH -n 96
#~ #SBATCH -t 240:00:00
#SBATCH -p defq

#SBATCH -J naturalized_kinematic-wave_continue-from-2013_using-opendap-files

#SBATCH --exclusive

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com


# activate conda env with python3 that is compatible for running pcrglobwb (using pcraster >= 4.2.1)
source activate py3_pcrglobwb_edwin

# using pcraster 4.3 development version (NOTE: continuously developed/compiled by Oliver)
source /scratch/depfg/pcraster/pcraster-4.3.0.sh


export PCRASTER_NR_WORKER_THREADS=4

pcrcalc

cd ~
cd github/edwinkost/PCR-GLOBWB_model_edwin-private-development/model/
python parallel_pcrglobwb_runner.py ../config/opendap_development/05min_naturalized_with-parallelization_kinematic-wave/continue-from-2013/setup_05min_on_eejit_naturalized_with-parallelization_kinematic-wave_continue-from-2013_using-opendap-files.ini

pcrcalc

