
set -x

OUT_FOLDER="/home/ms/copext/cyes/links/scratch_ulysses/data/edwin/river_network_adjusted_for_pcrglobwb/version_2020-07-20/develop/"
mkdir -p ${OUT_FOLDER}
cd ${OUT_FOLDER}

INP_FOLDER="/home/ms/copext/cyes/links/scratch_ulysses/data/edwin/river_network_adjusted_for_pcrglobwb/source/river_network/"

        #~ float width(lat, lon) ;
                #~ width:_FillValue = -9999.f ;
                #~ width:long_name = "chanel width GWD-LR - satellite" ;
                #~ width:standard_name = "chanel width GWD-LR - satellite" ;
                #~ width:units = "m" ;

rm width.*
cdo selname,width ${INP_FOLDER}/d8map_06min.nc width.nc
gdalwarp -tr 0.1 0.1 -te -180 -90 180 90 width.nc width.tif
pcrcalc width.map = "if(scalar(width.tif) ge 0.00, scalar(width.tif))"
 aguila width.map

        #~ float grdare(lat, lon) ;
                #~ grdare:_FillValue = -9999.f ;
                #~ grdare:long_name = "rectangular grid area" ;
                #~ grdare:standard_name = "rectangular grid area" ;
                #~ grdare:units = "m2" ;

rm grdare.*
cdo selname,grdare ${INP_FOLDER}/d8map_06min.nc grdare.nc

        #~ float rivlen_grid(lat, lon) ;
                #~ rivlen_grid:_FillValue = -9999.f ;
                #~ rivlen_grid:long_name = "rectangular channel lenght" ;
                #~ rivlen_grid:standard_name = "rectangular channel lenght" ;
                #~ rivlen_grid:units = "m" ;

rm rivlen_grid.nc
cdo selname,rivlen_grid ../d8map_06min.nc rivlen_grid.nc /home/ms/copext/cyes/links/scratch_ulysses/data/edwin/river_network_adjusted_for_pcrglobwb/source/river_network

        #~ int flwdir(lat, lon) ;
                #~ flwdir:_FillValue = -9999 ;
                #~ flwdir:long_name = "flow direction (D8)" ;
                #~ flwdir:standard_name = "flow direction (D8)" ;
                #~ flwdir:units = "-" ;/home/ms/copext/cyes/links/scratch_ulysses/data/edwin/river_network_adjusted_for_pcrglobwb/source/river_network

rm flwdir*
cdo selname,flwdir ${INP_FOLDER}/d8map_06min.nc flwdir.nc
gdalwarp -tr 0.1 0.1 -te -180 -90 180 90 flwdir.nc flwdir.tif

# http://hydro.iis.u-tokyo.ac.jp/~yamadai/flow/tech.html
# http://pcraster.geo.uu.nl/pcraster/4.3.0/documentation/pcraster_manual/sphinx/secdatbase.html#ldd-data-type

pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq -1, ldd(5))"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  0, ldd(5), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  1, ldd(8), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  2, ldd(9), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  3, ldd(6), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  4, ldd(3), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  5, ldd(2), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  6, ldd(1), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  7, ldd(4), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.tif) eq  8, ldd(7), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "lddrepair(lddrepair(flwdir_pcraster_ldd.map))"
 aguila flwdir_pcraster_ldd.map

pcrcalc flwdir_pcraster_ldd_covered.map = "cover(flwdir_pcraster_ldd.map, ldd(5.0))"


# expand ldd - UNTIL THIS PART
# - landmask from Stephan
cp /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/various_tools/test_uly/land_mask_only.map .
# - forcing landmask version 1
cp /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/various_tools/test_uly/land_mask_only.map .
cp /home/ms/copext/cyes/github/edwinkost/PCR-GLOBWB_model_edwin-private-development/various_tools/test_uly/landmask_forcing_2020-06-XX/landmask_precipitation_daily_01_01_1981.map .



pcrcalc catchment_flwdir_pcraster_ldd.map        = "catchment(flwdir_pcraster_ldd.map, pit(flwdir_pcraster_ldd.map))"
pcrcalc scalar_catchment_flwdir_pcraster_ldd.map = "scalar(catchment_flwdir_pcraster_ldd.map)"

pcrcalc streamorder_flwdir_pcraster_ldd.map = "streamorder(flwdir_pcraster_ldd.map)"

aguila *.map *.nc

set +x
