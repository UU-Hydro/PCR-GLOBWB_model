
set -x

OUT_FOLDER="/home/ms/copext/cyes/links/scratch_ulysses/data/edwin/river_network_adjusted_for_pcrglobwb/version_2020-07-21/final/"
mkdir -p ${OUT_FOLDER}
cd ${OUT_FOLDER}
rm -rf *

INP_FOLDER="/home/ms/copext/cyes/links/scratch_ulysses/data/edwin/ulysses_river_network_adjusted_for_pcrglobwb/source/river_network/"


# ldd - drainage direction

        #~ int flwdir(lat, lon) ;
                #~ flwdir:_FillValue = -9999 ;
                #~ flwdir:long_name = "flow direction (D8)" ;
                #~ flwdir:standard_name = "flow direction (D8)" ;
                #~ flwdir:units = "-" ;/home/ms/copext/cyes/links/scratch_ulysses/data/edwin/river_network_adjusted_for_pcrglobwb/source/river_network

rm flwdir*
cdo -L -sellonlatbox,-180,180,90,-90 -selname,flwdir ${INP_FOLDER}/d8map_06min.nc flwdir.nc
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
pcrcalc flwdir_pcraster_ldd_covered.map = "lddrepair(lddrepair(flwdir_pcraster_ldd_covered.map))"
 aguila flwdir_pcraster_ldd_covered.map


# cellarea (m2), using cdo
rm cdo_griddarea*
cdo -L -setname,cellarea -setunit,m2 -gridarea flwdir.nc cdo_griddarea.nc
gdalwarp -tr 0.1 0.1 -te -180 -90 180 90 cdo_griddarea.nc cdo_griddarea.tif
pcrcalc cdo_griddarea.map = "scalar(cdo_griddarea.tif)"
mapattr -s -P yb2t *.map
 aguila cdo_griddarea.map


# NEXT: put the ldd and cellarea map to derive channel properties

set +x
