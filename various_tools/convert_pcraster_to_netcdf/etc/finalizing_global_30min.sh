
MAINFOLDER="/scratch/depfg/sutan101/data/pcrglobwb2_input_release/version_2019_11_beta_extended/"

set -x

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/groundwater/aquifer_thickness_estimate/thickness_30min.nc
VARNAME="thickness_30min_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/groundwater/properties/groundwaterProperties.nc
VARNAME="specificYield"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="recessionCoeff"
ncatted -O -h -a units,${VARNAME},o,c,"day-1" ${NCFILE}
VARNAME="kSatAquifer"
ncatted -O -h -a units,${VARNAME},o,c,"m day-1" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/fao_root_nonpaddy.nc
VARNAME="fao_root_nonpaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/Global_CropCoefficientKc-IrrNonPaddy_30min.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/maxf_nonpaddy.nc
VARNAME="maxf_nonpaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/minf_nonpaddy_permafrost.nc
VARNAME="minf_nonpaddy_permafrost_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/nonPaddyProperties.nc
VARNAME="fracVegCover"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
VARNAME="rootFraction1"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="rootFraction2"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxRootDepth"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="minSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/rfrac1_nonpaddy.nc
VARNAME="rfrac1_nonpaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/rfrac2_nonpaddy.nc
VARNAME="rfrac2_nonpaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrNonPaddy/vegf_nonpaddy.nc
VARNAME="vegf_nonpaddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/fao_root_paddy.nc
VARNAME="fao_root_paddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/Global_CropCoefficientKc-IrrPaddy_30min.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/maxf_paddy.nc
VARNAME="maxf_paddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/minf_paddy_permafrost.nc
VARNAME="minf_paddy_permafrost_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/paddyProperties.nc
VARNAME="fracVegCover"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
VARNAME="rootFraction1"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="rootFraction2"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxRootDepth"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="minSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/rfrac1_paddy.nc
VARNAME="rfrac1_paddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/rfrac2_paddy.nc
VARNAME="rfrac2_paddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/irrPaddy/vegf_paddy.nc
VARNAME="vegf_paddy_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/coverFractionInputGrassland366days.nc
VARNAME="coverFractionInput"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/Global_CropCoefficientKc-Grassland_30min.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/interceptCapInputGrassland366days.nc
VARNAME="interceptCapInput"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/rfrac1_short.nc
VARNAME="rfrac1_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/rfrac2_short.nc
VARNAME="rfrac2_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/vegf_short.nc
VARNAME="vegf_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/fao_root_short.nc
VARNAME="fao_root_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/maxf_short.nc
VARNAME="maxf_short_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/minf_short_permafrost.nc
VARNAME="minf_short_permafrost_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalShort/grasslandProperties.nc
VARNAME="fracVegCover"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
VARNAME="rootFraction1"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="rootFraction2"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxRootDepth"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="minSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/coverFractionInputForest366days.nc
VARNAME="coverFractionInput"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/Global_CropCoefficientKc-Forest_30min.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/interceptCapInputForest366days.nc
VARNAME="interceptCapInput"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/rfrac1_tall.nc
VARNAME="rfrac1_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/rfrac2_tall.nc
VARNAME="rfrac2_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/vegf_tall.nc
VARNAME="vegf_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/fao_root_tall.nc
VARNAME="fao_root_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/maxf_tall.nc
VARNAME="maxf_tall_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/minf_tall_permafrost.nc
VARNAME="minf_tall_permafrost_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/landCover/naturalTall/forestProperties.nc
VARNAME="fracVegCover"
ncatted -O -h -a units,${VARNAME},o,c,"m2 m-2" ${NCFILE}
VARNAME="rootFraction1"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="rootFraction2"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxRootDepth"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
VARNAME="minSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
VARNAME="maxSoilDepthFrac"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/landSurface/soil/soilProperties.nc 
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


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_30min/meteo/forcing/daily_precipitation_cruts321_era-40_era-interim_1958-2010_cruts324_era-interim_2011_to_2015.nc  ${MAINFOLDER}/pcrglobwb2_input/global_30min/meteo/forcing/daily_precipitation_cru_era-interim_1979_to_2010.nc  &
cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_30min/meteo/forcing/daily_referencePotET_cruts321_era-40_era-interim_1958-2010_cruts324_era-interim_2011_to_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/meteo/forcing/daily_referencePotET_cru_era-interim_1979_to_2010.nc &
cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_30min/meteo/forcing/daily_temperature_cruts321_era-40_era-interim_1958-2010_cruts324_era-interim_2011_to_2015.nc    ${MAINFOLDER}/pcrglobwb2_input/global_30min/meteo/forcing/daily_temperature_cru_era-interim_1979_to_2010.nc    &
wait


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/bankfull_depth.nc
VARNAME="bankfull_depth_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/bankfull_width.nc
VARNAME="bankfull_width_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/channel_gradient.nc
VARNAME="channel_gradient_map"
ncatted -O -h -a units,${VARNAME},o,c,"m m-1" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0000.nc
VARNAME="dzRel0000_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0001.nc
VARNAME="dzRel0001_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0005.nc
VARNAME="dzRel0005_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0010.nc
VARNAME="dzRel0010_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}
 
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0020.nc
VARNAME="dzRel0020_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}
 
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0030.nc
VARNAME="dzRel0030_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0040.nc
VARNAME="dzRel0040_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0050.nc
VARNAME="dzRel0050_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0060.nc
VARNAME="dzRel0060_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0070.nc
VARNAME="dzRel0070_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0080.nc
VARNAME="dzRel0080_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0090.nc
VARNAME="dzRel0090_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/channel_properties/dzRel0100.nc
VARNAME="dzRel0100_map"
ncatted -O -h -a units,${VARNAME},o,c,"m" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/kc_surface_water/cropCoefficientForOpenWater.nc
VARNAME="kc"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/cellarea30min.nc
VARNAME="cellarea30min_map"
ncatted -O -h -a units,${VARNAME},o,c,"m2" ${NCFILE}
ncdump -h ${NCFILE}


cp ${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min_unmask.nc
cdo setmissval,0.0 ${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min_unmask.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min.nc
VARNAME="lddsound_30min_map"
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min.nc
ncatted -O -h -a units,${VARNAME},o,c,"pcraster_ldd" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/routing/ldd_and_cell_area/lddsound_30min_unmask.nc
ncatted -O -h -a units,${VARNAME},o,c,"pcraster_ldd" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


cp ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_30min_30min.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_30min_30min_unmask.nc
cdo -L -setmissval,0 -setrtoc,-inf,0,0 ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_30min_30min_unmask.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_30min_30min.nc
VARNAME="abstraction_zones_30min_30min_map"
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_30min_30min.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}
cdo info ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_30min_30min_unmask.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


cp ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_60min_30min.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_60min_30min_unmask.nc
cdo -L -setmissval,0 -setrtoc,-inf,0,0 ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_60min_30min_unmask.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_60min_30min.nc
VARNAME="abstraction_zones_60min_30min_map"
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_60min_30min.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}
cdo info ${NCFILE}
NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/abstraction_zones/abstraction_zones_60min_30min_unmask.nc
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/irrigation/irrigation_efficiency/efficiency.nc
VARNAME="efficiency_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}


NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/source_partitioning/surface_water_fraction_for_irrigation/AEI_QUAL.nc
VARNAME="AEI_QUAL_map"
ncatted -O -h -a units,${VARNAME},o,c,"-" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}

NCFILE=${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/source_partitioning/surface_water_fraction_for_irrigation/AEI_SWFRAC.nc
VARNAME="AEI_SWFRAC_map"
ncatted -O -h -a units,${VARNAME},o,c,"1" ${NCFILE}
ncdump -h ${NCFILE}
ncview ${NCFILE}





cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/domestic/domestic_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/domestic/domestic_water_demand_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/domestic/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/domestic/domestic_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/domestic/complete_uncompressed/domestic_water_demand_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/industry/industry_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/industry/industry_water_demand_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/industry/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/industry/industry_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/industry/complete_uncompressed/industry_water_demand_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


cdo -L -f nc4 -selyear,1979/2010 ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/livestock/livestock_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/livestock/livestock_water_demand_1979-2010_version_april_2015.nc
mkdir ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/livestock/complete_uncompressed
cp -r ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/livestock/livestock_water_demand_version_april_2015.nc ${MAINFOLDER}/pcrglobwb2_input/global_30min/waterUse/waterDemand/livestock/complete_uncompressed/livestock_water_demand_version_april_2015.nc
# YOU ALSO HAVE TO COPY THE COMPRESSED FILE.


set +x

