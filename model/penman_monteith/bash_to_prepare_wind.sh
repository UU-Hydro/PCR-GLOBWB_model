
cd /scratch-shared/edwinhs/meteo_arise/tanzania/version_2020-03-12_test-edwin-only-2000/era5-land/half_arcdeg/


# calculate wind speed

#~ -rw-r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_u10-average_2000-2000/tanzania_era5-land_u10-average_2000-2000_rempacon-30-arcmin_monthly.nc
#~ -rw-r--r-- 1 edwinhs edwinhs 82K Mar 14 17:12 tanzania_era5-land_v10-average_2000-2000/tanzania_era5-land_v10-average_2000-2000_rempacon-30-arcmin_monthly.nc

mkdir tanzania_era5-land_10winds-avg_2000-2000
   cd tanzania_era5-land_10winds-avg_2000-2000

rm *.nc

cdo -L -setunit,m2.s-2 -sqr ../tanzania_era5-land_u10-average_2000-2000/tanzania_era5-land_u10-average_2000-2000_rempacon-30-arcmin_monthly.nc tmp_square_u10.nc
cdo -L -setunit,m2.s-2 -sqr ../tanzania_era5-land_v10-average_2000-2000/tanzania_era5-land_v10-average_2000-2000_rempacon-30-arcmin_monthly.nc tmp_square_v10.nc
cdo -L -add tmp_square_v10.nc tmp_square_u10.nc tmp_square_w10.nc
cdo -L -setname,10m-wind-speed -setunit,m.s-1 -sqrt tmp_square_w10.nc w10.nc

cdo -L -setname,10m-wind-speed -sqrt -add -sqr ../tanzania_era5-land_u10-average_2000-2000/tanzania_era5-land_u10-average_2000-2000_rempacon-30-arcmin_monthly.nc -sqr ../tanzania_era5-land_v10-average_2000-2000/tanzania_era5-land_v10-average_2000-2000_rempacon-30-arcmin_monthly.nc tanzania_era5-land_10winds-avg_2000-2000_rempacon-30-arcmin_monthly.nc

cdo -L -sub w10.nc tanzania_era5-land_10winds-avg_2000-2000_rempacon-30-arcmin_monthly.nc check.nc
