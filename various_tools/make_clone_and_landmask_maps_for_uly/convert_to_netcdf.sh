
mkdir -p

cd 

# get the mask code map for river and land
cp ../global_landmask_river_and_land_mask_all.map .
gdal_translate -of NETCDF global_landmask_river_and_land_mask_all.nc

# check
pcrcalc check_global_landmask_river_and_land_mask_all.map = "if(defined(land_mask.map), defined(global_landmask_river_and_land_mask_all.map))"
mapattr -p check_global_landmask_river_and_land_mask_all.map
aguila check_global_landmask_river_and_land_mask_all.map

# get the mask code map for land
pcrcalc global_landmask_land_mask_all.map = 


	pcrcalc check.map = "if(defined(global_landmask_land_mask_all.map), defined(global_landmask_river_and_land_mask_all.map))"



# merge original subdomian
pcrcalc check_original_subdomain.map = "scalar(subdomain_land_1.nc) +    scalar(subdomain_land_2.nc) +    scalar(subdomain_land_3.nc) +    scalar(subdomain_land_4.nc) +    scalar(subdomain_land_5.nc) +  scalar(subdomain_land_10.nc) +   scalar(subdomain_land_20.nc) +   scalar(subdomain_land_30.nc) +   scalar(subdomain_land_40.nc) +   scalar(subdomain_land_50.nc) + scalar(subdomain_land_11.nc) +   scalar(subdomain_land_21.nc) +   scalar(subdomain_land_31.nc) +   scalar(subdomain_land_41.nc) +   scalar(subdomain_land_51.nc) + scalar(subdomain_land_12.nc) +   scalar(subdomain_land_22.nc) +   scalar(subdomain_land_32.nc) +   scalar(subdomain_land_42.nc) +   scalar(subdomain_land_52.nc) + scalar(subdomain_land_13.nc) +   scalar(subdomain_land_23.nc) +   scalar(subdomain_land_33.nc) +   scalar(subdomain_land_43.nc) +   scalar(subdomain_land_53.nc) + scalar(subdomain_land_14.nc) +   scalar(subdomain_land_24.nc) +   scalar(subdomain_land_34.nc) +   scalar(subdomain_land_44.nc) +   scalar(subdomain_land_54.nc) + scalar(subdomain_land_15.nc) +   scalar(subdomain_land_25.nc) +   scalar(subdomain_land_35.nc) +   scalar(subdomain_land_45.nc) +   scalar(subdomain_land_6.nc) + scalar(subdomain_land_16.nc) +   scalar(subdomain_land_26.nc) +   scalar(subdomain_land_36.nc) +   scalar(subdomain_land_46.nc) +   scalar(subdomain_land_7.nc) + scalar(subdomain_land_17.nc) +   scalar(subdomain_land_27.nc) +   scalar(subdomain_land_37.nc) +   scalar(subdomain_land_47.nc) +   scalar(subdomain_land_8.nc) + scalar(subdomain_land_18.nc) +   scalar(subdomain_land_28.nc) +   scalar(subdomain_land_38.nc) +   scalar(subdomain_land_48.nc) +   scalar(subdomain_land_9.nc) + scalar(subdomain_land_19.nc) +   scalar(subdomain_land_29.nc) +   scalar(subdomain_land_39.nc) +   scalar(subdomain_land_49.nc)"

pcrcalc check_36.map =  "if(defined(land_mask.map), subdomain_land_36.map)"
