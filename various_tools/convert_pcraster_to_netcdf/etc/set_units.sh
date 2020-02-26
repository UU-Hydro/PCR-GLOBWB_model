
MAINFOLDER="/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/"

set -x

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/groundwater/aquifer_thickness_estimate/thickness_05min.nc
VARNAME="thickness_05min_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/groundwater/confining_layer_parameters/confining_layer_thickness_version_2016.nc
VARNAME="confining_layer_thickness_version_2016_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/groundwater/properties/groundwaterProperties5ArcMin.nc
VARNAME="specificYield"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="recessionCoeff"
ncatted -O -h -a units,${VARNAME},o,c,"day-1" ${NCFILE}
VARNAME="kSatAquifer"
ncatted -O -h -a units,${VARNAME},o,c,"m day-1" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/irrNonPaddy/fractionNonPaddy.nc
VARNAME="fractionNonPaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/irrPaddy/fractionPaddy.nc
VARNAME="fractionPaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalShort/coverFractionInputGrassland.nc
VARNAME="coverFractionInput"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalShort/cropCoefficientGrassland.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalShort/interceptCapInputGrassland.nc
VARNAME="interceptCapInput"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalShort/rfrac1_short.nc
VARNAME="rfrac1_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalShort/rfrac2_short.nc
VARNAME="rfrac2_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalShort/vegf_short.nc
VARNAME="vegf_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalTall/coverFractionInputForest.nc
VARNAME="coverFractionInput"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalTall/cropCoefficientForest.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalTall/interceptCapInputForest.nc
VARNAME="interceptCapInput"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalTall/rfrac1_tall.nc
VARNAME="rfrac1_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalTall/rfrac2_tall.nc
VARNAME="rfrac2_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/landCover/naturalTall/vegf_tall.nc
VARNAME="vegf_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/landSurface/soil/soilProperties5ArcMin.nc 
VARNAME="firstStorDepth"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="secondStorDepth"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="soilWaterStorageCap1"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="soilWaterStorageCap2"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="airEntryValue1"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="airEntryValue2"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="poreSizeBeta1"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="poreSizeBeta2"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="resVolWC1"
ncatted -O -h -a units,${VARNAME},o,c,"m3 m-3" ${NCFILE}
VARNAME="resVolWC2"
ncatted -O -h -a units,${VARNAME},o,c,"m3 m-3" ${NCFILE}
VARNAME="satVolWC1"
ncatted -O -h -a units,${VARNAME},o,c,"m3 m-3" ${NCFILE}
VARNAME="satVolWC2"
ncatted -O -h -a units,${VARNAME},o,c,"m3 m-3" ${NCFILE}
VARNAME="KSat1"
ncatted -O -h -a units,${VARNAME},o,c,"m day-1" ${NCFILE}
VARNAME="KSat2"
ncatted -O -h -a units,${VARNAME},o,c,"m day-1" ${NCFILE}
VARNAME="percolationImp"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/meteo/downscaling_from_30min/gtopo05min.nc
VARNAME="gtopo05min_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/meteo/downscaling_from_30min/precipitation_correl.nc
VARNAME="precipitation"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/meteo/downscaling_from_30min/precipitation_slope.nc
VARNAME="precipitation"
ncatted -O -h -a units,${VARNAME},o,c,"mm m-1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/meteo/downscaling_from_30min/temperature_correl.nc
VARNAME="temperature"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/meteo/downscaling_from_30min/temperature_slope.nc
VARNAME="temperature"
ncatted -O -h -a units,${VARNAME},o,c,"degrees Celcius m-1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/meteo/downscaling_from_30min/uniqueIds_30min.nc
VARNAME="uniqueIds_30min_map"
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/bankfull_depth.nc
VARNAME="bankfull_depth_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/bankfull_width.nc
VARNAME="bankfull_width_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/channel_gradient.nc
VARNAME="channel_gradient_map"
ncatted -O -h -a units,${VARNAME},o,c,"m m-1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0000.nc
VARNAME="dzRel0000_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0010.nc
VARNAME="dzRel0010_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}
 
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0020.nc
VARNAME="dzRel0020_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}
 
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0030.nc
VARNAME="dzRel0030_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0040.nc
VARNAME="dzRel0040_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0050.nc
VARNAME="dzRel0050_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0060.nc
VARNAME="dzRel0060_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0070.nc
VARNAME="dzRel0070_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0080.nc
VARNAME="dzRel0080_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0090.nc
VARNAME="dzRel0090_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/channel_properties/dzRel0100.nc
VARNAME="dzRel0100_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}


cp ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/cellsize05min.correct.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/cellsize05min_correct.nc
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/cellsize05min.correct.nc
VARNAME="cellsize05min_correct_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2" ${NCFILE}
ncdump -h ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/cellsize05min_correct.nc
VARNAME="cellsize05min_correct_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2" ${NCFILE}
ncdump -h ${NCFILE}


cp ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/lddsound_05min.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/lddsound_05min_unmask.nc
cdo setmissval,0 ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/lddsound_05min_unmask.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/lddsound_05min.nc
VARNAME="lddsound_05min_map"
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/lddsound_05min.nc
ncatted -O -h -a units,${VARNAME},o,c,"pcraster_ldd" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/ldd_and_cell_area/lddsound_05min_unmask.nc
ncatted -O -h -a units,${VARNAME},o,c,"pcraster_ldd" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/surface_water_bodies/waterBodies5ArcMin.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/surface_water_bodies/waterBodies5ArcMin_1979-2010.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/surface_water_bodies/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/surface_water_bodies/waterBodies5ArcMin.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/routing/surface_water_bodies/complete_uncompressed/waterBodies5ArcMin.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.



cp ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_30min_05min.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_30min_05min_unmask.nc
cdo -L -setmissval,0 -setrtoc,-inf,0,0 ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_30min_05min_unmask.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_30min_05min.nc
VARNAME="abstraction_zones_30min_05min_map"
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_30min_05min.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_30min_05min_unmask.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


cp ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_60min_05min.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_60min_05min_unmask.nc
cdo -L -setmissval,0 -setrtoc,-inf,0,0 ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_60min_05min_unmask.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_60min_05min.nc
VARNAME="abstraction_zones_60min_05min_map"
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_60min_05min.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/abstraction_zones/abstraction_zones_60min_05min_unmask.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/desalination/desalination_water_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/desalination/desalination_water_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/desalination/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/desalination/desalination_water_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/desalination/complete_uncompressed/desalination_water_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


# TODO: /scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/pcrglobwb2_input/global_05min/waterUse/source_partitioning/surface_water_fraction_for_irrigation


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/domestic/domestic_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/domestic/domestic_water_demand_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/domestic/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/domestic/domestic_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/domestic/complete_uncompressed/domestic_water_demand_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/industry/industry_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/industry/industry_water_demand_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/industry/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/industry/industry_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/industry/complete_uncompressed/industry_water_demand_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/livestock/livestock_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/livestock/livestock_water_demand_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/livestock/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/livestock/livestock_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_05min/waterUse/waterDemand/livestock/complete_uncompressed/livestock_water_demand_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


set +x

