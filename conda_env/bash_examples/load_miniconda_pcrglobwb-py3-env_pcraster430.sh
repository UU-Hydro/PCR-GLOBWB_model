
set -x

# abandon any existing PYTHONPATH (recommended, if you want to use miniconda or anaconda)
unset PYTHONPATH

# load miniconda - RECOMMENDED
export PATH=$HOME/opt/miniconda3/bin:$PATH

# activate conda env
source activate pcrglobwb_python36_ulysses

# using pcraster 4.3.0
module load pcraster/4.3.0

# load gdal
module load gdal/3.0.4

# include PATH for for a working aguila
export PATH=$HOME/opt/aguila:$PATH

#~ # use at least 8 workers
#~ export PCRASTER_NR_WORKER_THREADS=8

set +x


