
git pull; python deterministic_runner_parallel_for_ulysses.py \
          ../config/ulysses/setup_6arcmin_develop.ini debug_parallel 29 \
          -mod /scratch/ms/copext/cyes/develop_parallel \
          -sd 1982-01-01 -ed 1982-01-31 \
          -misd /scratch/ms/copext/cyes/pcrglobwb_output_version_2020-10-08_example/first_test_54_clones/global/states \
          -dfis 1981-12-31 \
          -pff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/precipitation_daily_01_1981.nc \
          -tff    /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/tavg_01_1981.nc \
          -rpetff /scratch/mo/nest/ulysses/data/meteo/era5land/1982/01/pet_01_1981.nc \
          end_of_arguments
