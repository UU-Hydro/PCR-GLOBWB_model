
set -x

        #~ float width(lat, lon) ;
                #~ width:_FillValue = -9999.f ;
                #~ width:long_name = "chanel width GWD-LR - satellite" ;
                #~ width:standard_name = "chanel width GWD-LR - satellite" ;
                #~ width:units = "m" ;

rm width.nc
cdo selname,width ../d8map_06min.nc width.nc

        #~ float grdare(lat, lon) ;
                #~ grdare:_FillValue = -9999.f ;
                #~ grdare:long_name = "rectangular grid area" ;
                #~ grdare:standard_name = "rectangular grid area" ;
                #~ grdare:units = "m2" ;

rm grdare.nc
cdo selname,grdare ../d8map_06min.nc grdare.nc

        #~ float rivlen_grid(lat, lon) ;
                #~ rivlen_grid:_FillValue = -9999.f ;
                #~ rivlen_grid:long_name = "rectangular channel lenght" ;
                #~ rivlen_grid:standard_name = "rectangular channel lenght" ;
                #~ rivlen_grid:units = "m" ;

rm rivlen_grid.nc
cdo selname,rivlen_grid ../d8map_06min.nc rivlen_grid.nc 

        #~ int flwdir(lat, lon) ;
                #~ flwdir:_FillValue = -9999 ;
                #~ flwdir:long_name = "flow direction (D8)" ;
                #~ flwdir:standard_name = "flow direction (D8)" ;
                #~ flwdir:units = "-" ;

rm flwdir.nc
rm *.map

cdo selname,flwdir ../d8map_06min.nc flwdir.nc

# http://hydro.iis.u-tokyo.ac.jp/~yamadai/flow/tech.html
# http://pcraster.geo.uu.nl/pcraster/4.3.0/documentation/pcraster_manual/sphinx/secdatbase.html#ldd-data-type

pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq -1, ldd(5))"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  0, ldd(5), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  1, ldd(8), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  2, ldd(9), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  3, ldd(6), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  4, ldd(3), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  5, ldd(2), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  6, ldd(1), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  7, ldd(4), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "if(scalar(flwdir.nc) eq  8, ldd(7), flwdir_pcraster_ldd.map)"
pcrcalc flwdir_pcraster_ldd.map = "lddrepair(lddrepair(flwdir_pcraster_ldd.map))"
 aguila flwdir_pcraster_ldd.map flwdir.nc

pcrcalc catchment_flwdir_pcraster_ldd.map        = "catchment(flwdir_pcraster_ldd.map, pit(flwdir_pcraster_ldd.map))"
pcrcalc scalar_catchment_flwdir_pcraster_ldd.map = "scalar(catchment_flwdir_pcraster_ldd.map)"

pcrcalc streamorder_flwdir_pcraster_ldd.map = "streamorder(flwdir_pcraster_ldd.map)"

aguila *.map *.nc

set +x
